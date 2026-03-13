-- EcoCommute core schema for ER diagram generation
-- Note: This includes a minimal auth_user table because rides_* tables reference it.
-- If you already use Django's built-in auth tables, keep your existing auth_user and skip recreating it.

-- Optional cleanup for re-runs
DROP TABLE IF EXISTS rides_livelocation;
DROP TABLE IF EXISTS rides_ridepassenger;
DROP TABLE IF EXISTS rides_userprofile;
DROP TABLE IF EXISTS rides_ride;
DROP TABLE IF EXISTS auth_user;

-- Minimal Django auth user entity (ERD anchor)
CREATE TABLE auth_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL,
    password VARCHAR(128) NOT NULL,
    is_staff BOOLEAN NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    date_joined DATETIME NOT NULL
);

CREATE TABLE rides_userprofile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    phone_number VARCHAR(12) NOT NULL,
    id_proof_number VARCHAR(50) NOT NULL DEFAULT '',
    aadhaar_verified BOOLEAN NOT NULL DEFAULT 0,
    aadhaar_last_4_digits VARCHAR(4) NULL,
    aadhaar_consent_given BOOLEAN NOT NULL DEFAULT 0,
    aadhaar_consent_timestamp DATETIME NULL,
    aadhaar_verified_at DATETIME NULL,
    email_verified BOOLEAN NOT NULL DEFAULT 0,
    email_verified_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    CONSTRAINT fk_userprofile_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id)
        ON DELETE CASCADE
);

CREATE TABLE rides_ride (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_location VARCHAR(120) NOT NULL,
    to_location VARCHAR(120) NOT NULL,
    ride_date DATE NOT NULL,
    ride_time TIME NOT NULL,
    vehicle_type VARCHAR(20) NOT NULL DEFAULT 'car_petrol',
    vehicle_number VARCHAR(15) NOT NULL DEFAULT 'UNKNOWN',
    distance_km REAL NOT NULL,
    total_seats INTEGER NOT NULL,
    seats_available INTEGER NOT NULL,
    creator_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    driver_started BOOLEAN NOT NULL DEFAULT 0,
    passenger_started BOOLEAN NOT NULL DEFAULT 0,
    driver_ended BOOLEAN NOT NULL DEFAULT 0,
    passenger_ended BOOLEAN NOT NULL DEFAULT 0,
    ride_status VARCHAR(20) NOT NULL DEFAULT 'created',
    CONSTRAINT fk_ride_creator
        FOREIGN KEY (creator_id) REFERENCES auth_user(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_ride_status
        CHECK (ride_status IN ('created', 'started', 'completed')),
    CONSTRAINT chk_vehicle_type
        CHECK (vehicle_type IN ('car_petrol', 'bike')),
    CONSTRAINT chk_seat_bounds
        CHECK (seats_available >= 0 AND seats_available <= total_seats)
);

CREATE TABLE rides_ridepassenger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ride_id INTEGER NOT NULL,
    pickup_point VARCHAR(200) NOT NULL DEFAULT '',
    pickup_notes TEXT NOT NULL DEFAULT '',
    joined_at DATETIME NOT NULL,
    CONSTRAINT fk_ridepassenger_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ridepassenger_ride
        FOREIGN KEY (ride_id) REFERENCES rides_ride(id)
        ON DELETE CASCADE,
    CONSTRAINT uq_ridepassenger_user_ride UNIQUE (user_id, ride_id)
);

CREATE TABLE rides_livelocation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    ride_id INTEGER NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    updated_at DATETIME NOT NULL,
    is_sharing BOOLEAN NOT NULL DEFAULT 0,
    CONSTRAINT fk_livelocation_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_livelocation_ride
        FOREIGN KEY (ride_id) REFERENCES rides_ride(id)
        ON DELETE CASCADE
);

-- Helpful relationship indexes
CREATE INDEX idx_rides_ride_creator_id ON rides_ride (creator_id);
CREATE INDEX idx_rides_ridepassenger_user_id ON rides_ridepassenger (user_id);
CREATE INDEX idx_rides_ridepassenger_ride_id ON rides_ridepassenger (ride_id);
CREATE INDEX idx_rides_livelocation_ride_id ON rides_livelocation (ride_id);
