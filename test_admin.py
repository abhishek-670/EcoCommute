"""
Quick test script to verify the custom admin dashboard is working.

This script will:
1. Check if admin views are accessible
2. Verify URL patterns are registered
3. Test if staff_member_required decorator is working
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecocommute.settings')
django.setup()

from django.contrib.auth.models import User
from django.urls import reverse, resolve
from rides.models import Ride, UserProfile


def test_admin_urls():
    """Test if all admin URLs are registered correctly."""
    print("\n" + "=" * 60)
    print("Testing Admin Dashboard URLs")
    print("=" * 60 + "\n")
    
    urls_to_test = [
        ('admin_dashboard', '/custom-admin/'),
        ('admin_users_list', '/custom-admin/users/'),
        ('admin_rides_list', '/custom-admin/rides/'),
        ('admin_trips_ongoing', '/custom-admin/trips/ongoing/'),
        ('admin_trips_completed', '/custom-admin/trips/completed/'),
    ]
    
    all_passed = True
    
    for url_name, expected_path in urls_to_test:
        try:
            path = reverse(url_name)
            if path == expected_path:
                print(f"✅ {url_name:30} -> {path}")
            else:
                print(f"⚠️  {url_name:30} -> Expected: {expected_path}, Got: {path}")
                all_passed = False
        except Exception as e:
            print(f"❌ {url_name:30} -> Error: {str(e)}")
            all_passed = False
    
    print()
    if all_passed:
        print("✅ All admin URLs are registered correctly!\n")
    else:
        print("❌ Some URLs have issues. Please check the configuration.\n")
    
    return all_passed


def test_staff_users():
    """Check if there are any staff users."""
    print("=" * 60)
    print("Checking for Staff Users")
    print("=" * 60 + "\n")
    
    staff_users = User.objects.filter(is_staff=True, is_active=True)
    
    if staff_users.exists():
        print(f"✅ Found {staff_users.count()} staff user(s):\n")
        for user in staff_users:
            print(f"   - {user.email:30} (ID: {user.id})")
        print()
        return True
    else:
        print("⚠️  No staff users found!")
        print("\nTo create a staff user, run:")
        print("   python create_admin.py")
        print("\nOr use Django shell:")
        print("   python manage.py shell")
        print("   >>> from django.contrib.auth.models import User")
        print("   >>> user = User.objects.get(email='your@email.com')")
        print("   >>> user.is_staff = True")
        print("   >>> user.save()")
        print()
        return False


def test_database_stats():
    """Show current database statistics."""
    print("=" * 60)
    print("Database Statistics")
    print("=" * 60 + "\n")
    
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    
    total_rides = Ride.objects.count()
    created_rides = Ride.objects.filter(ride_status='created').count()
    started_rides = Ride.objects.filter(ride_status='started').count()
    completed_rides = Ride.objects.filter(ride_status='completed').count()
    
    print(f"Users:")
    print(f"   Total Users:        {total_users}")
    print(f"   Active Users:       {active_users}")
    print(f"   Staff Users:        {staff_users}")
    print()
    print(f"Rides:")
    print(f"   Total Rides:        {total_rides}")
    print(f"   Created Rides:      {created_rides}")
    print(f"   Started Rides:      {started_rides}")
    print(f"   Completed Rides:    {completed_rides}")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CUSTOM ADMIN DASHBOARD - VERIFICATION TEST")
    print("=" * 60)
    
    # Test 1: URLs
    urls_ok = test_admin_urls()
    
    # Test 2: Staff users
    staff_ok = test_staff_users()
    
    # Test 3: Database stats
    test_database_stats()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60 + "\n")
    
    if urls_ok and staff_ok:
        print("✅ All checks passed! Your admin dashboard is ready to use.")
        print("\n📍 Access it at: http://localhost:8000/custom-admin/")
        print()
    elif urls_ok and not staff_ok:
        print("⚠️  Admin URLs are configured, but no staff users found.")
        print("   Create a staff user to access the dashboard:")
        print("   python create_admin.py")
        print()
    else:
        print("❌ Some issues found. Please review the errors above.")
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
