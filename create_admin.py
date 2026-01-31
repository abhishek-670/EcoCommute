"""
Script to create or promote a user to staff status for accessing the custom admin dashboard.

Usage:
    python create_admin.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecocommute.settings')
django.setup()

from django.contrib.auth.models import User
from rides.models import UserProfile


def create_admin_user():
    """Create a new staff user or promote an existing user."""
    
    print("=" * 60)
    print("Custom Admin Dashboard - User Setup")
    print("=" * 60)
    print()
    
    # Check if user wants to create new or promote existing
    print("Choose an option:")
    print("1. Create a new admin user")
    print("2. Promote an existing user to admin")
    print()
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        create_new_admin()
    elif choice == "2":
        promote_existing_user()
    else:
        print("Invalid choice. Please run the script again.")
        sys.exit(1)


def create_new_admin():
    """Create a new staff user."""
    print("\n--- Create New Admin User ---\n")
    
    email = input("Email address: ").strip().lower()
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        print(f"Error: User with email '{email}' already exists.")
        print("Please use option 2 to promote an existing user.")
        sys.exit(1)
    
    password = input("Password: ").strip()
    if len(password) < 6:
        print("Error: Password must be at least 6 characters long.")
        sys.exit(1)
    
    phone = input("Phone number (91XXXXXXXXXX format): ").strip()
    
    # Validate phone number
    import re
    cleaned_phone = ''.join(filter(str.isdigit, phone))
    if not re.match(r'^91\d{10}$', cleaned_phone):
        print("Error: Phone number must start with 91 and be exactly 12 digits.")
        print("Example: 919876543210")
        sys.exit(1)
    
    # Create user
    try:
        user = User.objects.create_user(
            username=email,  # Use email as username
            email=email,
            password=password
        )
        user.is_staff = True
        user.is_active = True
        user.save()
        
        # Update profile with phone number
        profile = user.profile
        profile.phone_number = cleaned_phone
        profile.save()
        
        print("\n✅ Success! Admin user created successfully.")
        print(f"   Email: {email}")
        print(f"   Phone: +{cleaned_phone}")
        print(f"   Staff Status: Yes")
        print(f"\nYou can now login at: http://localhost:8000/custom-admin/")
        
    except Exception as e:
        print(f"\n❌ Error creating user: {str(e)}")
        sys.exit(1)


def promote_existing_user():
    """Promote an existing user to staff status."""
    print("\n--- Promote Existing User ---\n")
    
    # List all users
    users = User.objects.all().order_by('email')
    
    if not users.exists():
        print("No users found in the database.")
        print("Please create a user first by registering on the website.")
        sys.exit(1)
    
    print("Existing users:")
    print("-" * 60)
    for idx, user in enumerate(users, 1):
        staff_status = "✓ Staff" if user.is_staff else "✗ Not Staff"
        active_status = "Active" if user.is_active else "Inactive"
        print(f"{idx}. {user.email:30} | {staff_status:12} | {active_status}")
    print("-" * 60)
    print()
    
    # Get user choice
    try:
        choice = int(input("Enter the number of the user to promote: ").strip())
        if choice < 1 or choice > users.count():
            print("Error: Invalid choice.")
            sys.exit(1)
        
        user = list(users)[choice - 1]
        
        # Check if already staff
        if user.is_staff:
            print(f"\nUser '{user.email}' is already a staff member.")
            update = input("Do you want to ensure they can access admin? (y/n): ").strip().lower()
            if update != 'y':
                print("No changes made.")
                sys.exit(0)
        
        # Promote to staff
        user.is_staff = True
        user.is_active = True
        user.save()
        
        print("\n✅ Success! User promoted to staff.")
        print(f"   Email: {user.email}")
        print(f"   Staff Status: Yes")
        print(f"   Active Status: Yes")
        print(f"\nThey can now login at: http://localhost:8000/custom-admin/")
        
    except ValueError:
        print("Error: Please enter a valid number.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error promoting user: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        create_admin_user()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
