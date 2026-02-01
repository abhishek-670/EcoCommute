<<<<<<< HEAD
# EcoCommute (Flask + SQLite)

A beginner-friendly carpool app that tracks CO₂ savings from shared rides.

## Folder Structure
```
.
├─ app.py              # Flask app, models, routes, CO₂ logic
├─ seed_data.py        # Sample users and rides
├─ requirements.txt    # Python dependencies
├─ templates/          # HTML pages (Bootstrap)
│  ├─ base.html
│  ├─ login.html
│  ├─ register.html
│  ├─ dashboard.html
│  ├─ rides.html
│  └─ create_ride.html
└─ static/
   └─ css/
      └─ style.css
```

## Database Schema (SQLite via SQLAlchemy)
- `user`: id, email (unique), password_hash, created_at
- `ride`: id, from_location, to_location, ride_date, ride_time, vehicle_type, distance_km, total_seats, seats_available, creator_id (FK user), created_at
- `ride_passenger`: id, user_id (FK user), ride_id (FK ride), joined_at, unique(user_id, ride_id)

## CO₂ Calculation
- Emission factors: Car (petrol) = 120 g/km, Bike = 0 g/km
- Formula per ride: `solo_kg = distance_km * factor / 1000`
- Shared: `shared_kg = solo_kg / occupants` (driver counts as one occupant)
- Savings per user: `saved_per_user = solo_kg - shared_kg`

## How to Run Locally
1) Create a virtual env (recommended)
```
python -m venv .venv
.venv\Scripts\activate
```
2) Install dependencies
```
pip install -r requirements.txt
```
3) Initialize database (first run creates ecocommute.db)
```
python app.py
```
4) Seed sample data (optional)
```
python seed_data.py
```
5) Start the server
```
set FLASK_APP=app.py
flask run
```
Then open http://127.0.0.1:5000

Demo logins (after seeding):
- alice@eco.com / password
- bob@eco.com / password
- carol@eco.com / password

## Notes
- Seats include the driver seat. Available seats start at `total_seats - 1`.
- Joining a ride decreases `seats_available` by one and prevents double joins.
- Eco badge appears when your total saved CO₂ exceeds 5 kg.
=======
# EcoCommute
EcoCommute - smarter rides for a greener planet
>>>>>>> bec6b1c9924a0348ff9db1494e9d7762ba541a8a
