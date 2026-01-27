from datetime import datetime, date, time
from functools import wraps
from typing import Tuple

from flask import Flask, render_template, request, redirect, url_for, session, g, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ecocommute.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "change-me"  # Replace in production


db = SQLAlchemy(app)


EMISSION_FACTORS = {
    "car_petrol": 120,  # g CO2 per km
    "bike": 0,
}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_location = db.Column(db.String(120), nullable=False)
    to_location = db.Column(db.String(120), nullable=False)
    ride_date = db.Column(db.Date, nullable=False)
    ride_time = db.Column(db.Time, nullable=False)
    vehicle_type = db.Column(db.String(20), nullable=False)
    distance_km = db.Column(db.Float, nullable=False)
    total_seats = db.Column(db.Integer, nullable=False)
    seats_available = db.Column(db.Integer, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", backref=db.backref("rides_created", lazy=True))
    passengers = db.relationship(
        "RidePassenger",
        back_populates="ride",
        cascade="all, delete-orphan",
        lazy=True,
    )

    @property
    def occupant_count(self) -> int:
        # Driver counts as one occupant; each filled seat removes one available slot.
        used_seats = self.total_seats - self.seats_available
        return max(used_seats, 1)


class RidePassenger(db.Model):
    __tablename__ = "ride_passenger"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey("ride.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("rides_joined", lazy=True))
    ride = db.relationship("Ride", back_populates="passengers")

    __table_args__ = (db.UniqueConstraint("user_id", "ride_id", name="unique_join"),)


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view_func(**kwargs)

    return wrapped_view


@app.before_request
def load_user() -> None:
    user_id = session.get("user_id")
    g.user = User.query.get(user_id) if user_id else None


def calculate_co2(distance_km: float, vehicle_type: str, occupants: int) -> Tuple[float, float, float]:
    factor = EMISSION_FACTORS.get(vehicle_type, EMISSION_FACTORS["car_petrol"])
    solo_kg = (distance_km * factor) / 1000
    occupants = max(occupants, 1)
    shared_kg = solo_kg / occupants
    saved_per_user = solo_kg - shared_kg
    return solo_kg, shared_kg, saved_per_user


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return redirect(url_for("register"))

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        flash("Welcome to EcoCommute!", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid credentials.", "danger")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        flash("Logged in successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    created_rides = (
        Ride.query.filter_by(creator_id=g.user.id)
        .order_by(Ride.ride_date.asc(), Ride.ride_time.asc())
        .all()
    )
    joined_rides = (
        Ride.query.join(RidePassenger)
        .filter(RidePassenger.user_id == g.user.id)
        .order_by(Ride.ride_date.asc(), Ride.ride_time.asc())
        .all()
    )

    total_saved = 0.0
    ride_summaries = []

    for ride in created_rides:
        solo, shared, saved = calculate_co2(ride.distance_km, ride.vehicle_type, ride.occupant_count)
        total_saved += saved
        ride_summaries.append({"ride": ride, "solo": solo, "shared": shared, "saved": saved, "role": "Driver"})

    for ride in joined_rides:
        solo, shared, saved = calculate_co2(ride.distance_km, ride.vehicle_type, ride.occupant_count)
        total_saved += saved
        ride_summaries.append({"ride": ride, "solo": solo, "shared": shared, "saved": saved, "role": "Passenger"})

    badge_earned = total_saved > 5

    return render_template(
        "dashboard.html",
        created_rides=created_rides,
        joined_rides=joined_rides,
        total_saved=total_saved,
        ride_summaries=ride_summaries,
        badge_earned=badge_earned,
    )


@app.route("/rides")
@login_required
def rides():
    rides_list = (
        Ride.query.order_by(Ride.ride_date.asc(), Ride.ride_time.asc()).all()
    )
    joined_ids = {rp.ride_id for rp in RidePassenger.query.filter_by(user_id=g.user.id).all()}
    return render_template("rides.html", rides=rides_list, joined_ids=joined_ids)


@app.route("/rides/create", methods=["GET", "POST"])
@login_required
def create_ride():
    if request.method == "POST":
        try:
            ride_date = datetime.strptime(request.form["ride_date"], "%Y-%m-%d").date()
            ride_time = datetime.strptime(request.form["ride_time"], "%H:%M").time()
            distance_km = float(request.form["distance_km"])
            total_seats = int(request.form["total_seats"])
        except (KeyError, ValueError):
            flash("Please provide valid ride details.", "danger")
            return redirect(url_for("create_ride"))

        vehicle_type = request.form.get("vehicle_type", "car_petrol")
        from_location = request.form.get("from_location", "").strip()
        to_location = request.form.get("to_location", "").strip()

        if total_seats < 1:
            flash("Total seats must be at least 1.", "warning")
            return redirect(url_for("create_ride"))

        seats_available = max(total_seats - 1, 0)  # Driver uses one seat.

        ride = Ride(
            from_location=from_location,
            to_location=to_location,
            ride_date=ride_date,
            ride_time=ride_time,
            vehicle_type=vehicle_type,
            distance_km=distance_km,
            total_seats=total_seats,
            seats_available=seats_available,
            creator_id=g.user.id,
        )
        db.session.add(ride)
        db.session.commit()
        flash("Ride created.", "success")
        return redirect(url_for("rides"))

    return render_template("create_ride.html")


@app.route("/rides/join/<int:ride_id>", methods=["POST"])
@login_required
def join_ride(ride_id: int):
    ride = Ride.query.get_or_404(ride_id)

    if ride.creator_id == g.user.id:
        flash("You are the driver for this ride.", "info")
        return redirect(url_for("rides"))

    if ride.seats_available <= 0:
        flash("No seats available.", "warning")
        return redirect(url_for("rides"))

    already_joined = RidePassenger.query.filter_by(ride_id=ride_id, user_id=g.user.id).first()
    if already_joined:
        flash("You have already joined this ride.", "info")
        return redirect(url_for("rides"))

    ride.seats_available -= 1
    join_entry = RidePassenger(user_id=g.user.id, ride_id=ride_id)
    db.session.add(join_entry)
    db.session.commit()
    flash("Joined ride!", "success")
    return redirect(url_for("rides"))


def ensure_database() -> None:
    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    ensure_database()
    app.run(debug=True)
