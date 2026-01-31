"""
Management command to create UserProfile for all users without one.
Run this once after adding the signal to fix existing users.

Usage:
    python manage.py create_missing_profiles
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rides.models import UserProfile


class Command(BaseCommand):
    help = 'Create UserProfile for all users who do not have one'

    def handle(self, *args, **options):
        users_without_profile = []
        
        for user in User.objects.all():
            if not hasattr(user, 'profile'):
                users_without_profile.append(user)
        
        if not users_without_profile:
            self.stdout.write(
                self.style.SUCCESS('✅ All users already have profiles!')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(
                f'Found {len(users_without_profile)} users without profiles'
            )
        )
        
        created_count = 0
        for user in users_without_profile:
            try:
                UserProfile.objects.create(user=user)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created profile for: {user.email}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create profile for {user.email}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully created {created_count} profiles!'
            )
        )
