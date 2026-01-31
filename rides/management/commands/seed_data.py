from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from rides.models import Ride


class Command(BaseCommand):
    help = 'Seeds the database with sample data'

    def handle(self, *args, **options):
        if User.objects.filter(username='alice@eco.com').exists():
            self.stdout.write(self.style.WARNING('Database already has data; skipping seed.'))
            return

        # Create users
        alice = User.objects.create_user(username='alice@eco.com', email='alice@eco.com', password='password')
        bob = User.objects.create_user(username='bob@eco.com', email='bob@eco.com', password='password')
        carol = User.objects.create_user(username='carol@eco.com', email='carol@eco.com', password='password')

        self.stdout.write(self.style.SUCCESS(f'Created users: {alice.email}, {bob.email}, {carol.email}'))

        # Create rides
        tomorrow = datetime.now().date() + timedelta(days=1)
        in_two_days = datetime.now().date() + timedelta(days=2)

        ride1 = Ride.objects.create(
            from_location='Campus',
            to_location='Downtown',
            ride_date=tomorrow,
            ride_time=datetime.strptime('08:30', '%H:%M').time(),
            vehicle_type='car_petrol',
            distance_km=12,
            total_seats=4,
            seats_available=2,
            creator=alice
        )

        ride2 = Ride.objects.create(
            from_location='Station',
            to_location='Office Park',
            ride_date=in_two_days,
            ride_time=datetime.strptime('09:00', '%H:%M').time(),
            vehicle_type='car_petrol',
            distance_km=20,
            total_seats=3,
            seats_available=1,
            creator=bob
        )

        self.stdout.write(self.style.SUCCESS(f'Created rides: {ride1}, {ride2}'))
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
