"""
Management command to delete a user by email for testing purposes.

Usage:
    python manage.py delete_user email@example.com
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Delete a user by email (for testing purposes)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the user to delete')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        
        try:
            user = User.objects.get(username=email)
            user_email = user.email
            user.delete()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully deleted user: {user_email}')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ User with email "{email}" not found')
            )
