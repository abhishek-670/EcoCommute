from datetime import datetime, timedelta

from app import app, db, User, Ride, RidePassenger, ensure_database


def seed() -> None:
    with app.app_context():
        ensure_database()

        if User.query.first():
            print("Database already has data; skipping seed.")
            return

        alice = User(email="alice@eco.com")
        alice.set_password("password")
        bob = User(email="bob@eco.com")
        bob.set_password("password")
        carol = User(email="carol@eco.com")
        carol.set_password("password")
        db.session.add_all([alice, bob, carol])
        db.session.commit()

        tomorrow = datetime.utcnow().date() + timedelta(days=1)
        in_two_days = datetime.utcnow().date() + timedelta(days=2)

        ride1 = Ride(
            from_location="Campus",
            to_location="Downtown",
            ride_date=tomorrow,
            ride_time=datetime.strptime("08:30", "%H:%M").time(),
            vehicle_type="car_petrol",
            distance_km=12,
            total_seats=4,
            seats_available=2,
            creator_id=alice.id,
        )

        ride2 = Ride(
            from_location="Station",
            to_location="Office Park",
            ride_date=in_two_days,
            ride_time=datetime.strptime("09:00", "%H:%M").time(),
            vehicle_type="car_petrol",
            distance_km=20,
            total_seats=3,
            seats_available=1,
            creator_id=bob.id,
        )

        db.session.add_all([ride1, ride2])
        db.session.commit()

        join1 = RidePassenger(user_id=bob.id, ride_id=ride1.id)
        ride1.seats_available -= 1
        join2 = RidePassenger(user_id=carol.id, ride_id=ride2.id)
        ride2.seats_available -= 1

        db.session.add_all([join1, join2])
        db.session.commit()

        print("Seed data created: 3 users, 2 rides.")


if __name__ == "__main__":
    seed()
