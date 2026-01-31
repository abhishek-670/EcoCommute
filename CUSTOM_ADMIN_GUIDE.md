# Custom Admin Dashboard - User Guide

## Overview
A custom admin dashboard for managing your Django ride-sharing application, completely separate from Django's default `/admin/` interface.

## Access
- **URL:** `http://localhost:8000/custom-admin/`
- **Requirement:** User account must have `is_staff=True`
- **Security:** Protected by `@staff_member_required` decorator

## Features

### 1. Dashboard (`/custom-admin/`)
Main overview page displaying:
- Total users count
- Total rides count
- Active rides count (created + started)
- Completed rides count
- Recent users (last 5)
- Recent rides (last 5)
- Quick action buttons

### 2. User Management (`/custom-admin/users/`)
**Features:**
- List all registered users
- Search by email, name, or phone number
- Filter by:
  - Active/Inactive status
  - Staff members
  - Aadhaar verified users
- View user details:
  - Email and phone number
  - Join date
  - Aadhaar verification status
  - Account active/inactive status
  - Staff status
- Activate/Deactivate user accounts
  - Deactivated users cannot log in
  - No data is deleted (no hard deletes)
  - Admins cannot deactivate themselves

### 3. Ride Management (`/custom-admin/rides/`)
**Features:**
- List all rides (past, present, future)
- Search by location, vehicle number, or driver email
- Filter by status:
  - Created
  - Started
  - Completed
- View ride details:
  - Route (from/to locations)
  - Date, time, and distance
  - Driver information
  - Vehicle type and number
  - Available/total seats
  - Passenger count
  - Two-side confirmation flags (start/end)
- Cancel active rides
  - Only non-completed rides can be cancelled
  - Cancellation permanently deletes the ride
  - Confirmation dialog required

### 4. Ride Detail View (`/custom-admin/rides/<id>/`)
**Features:**
- Comprehensive ride information
- Driver details with contact information
- Two-side confirmation status display:
  - Driver/Passenger start confirmations
  - Driver/Passenger end confirmations
- Complete passenger list with:
  - Email and phone numbers
  - Pickup points and notes
  - Join timestamps
  - Aadhaar verification status
- Admin actions (cancel if not completed)

### 5. Trip Monitoring - Ongoing (`/custom-admin/trips/ongoing/`)
**Features:**
- Real-time monitoring of active rides
- Shows rides with status "Created" or "Started"
- Progress indicators showing:
  - Start confirmation progress
  - End confirmation progress
- Visual indicators for each confirmation
- Auto-refresh every 30 seconds
- Quick access to view details or cancel

### 6. Trip Monitoring - Completed (`/custom-admin/trips/completed/`)
**Features:**
- Historical view of completed rides (read-only)
- Confirmation status overview:
  - Fully confirmed (all 4 confirmations)
  - Partially confirmed (missing some confirmations)
- Statistics:
  - Fully confirmed rides count
  - Total distance covered
  - Total passengers served
- No modification or cancellation allowed

## Security Features

### Authentication & Authorization
- All views protected with `@staff_member_required`
- Only users with `is_staff=True` can access
- Automatic redirect to login if not authenticated
- Admins cannot deactivate their own accounts

### CSRF Protection
- All POST requests require CSRF tokens
- Included automatically in all forms

### No Hard Deletes
- User deactivation doesn't delete data
- Only ride cancellation performs deletion
- Completed rides cannot be deleted

### Confirmation Dialogs
- Cancel ride: Requires JavaScript confirmation
- Toggle user status: Requires JavaScript confirmation
- Prevents accidental deletions

## UI/UX Features

### Layout
- Fixed sidebar navigation
- Responsive design (Bootstrap 5)
- Clean, modern interface
- Color-coded status badges

### Navigation
- Dashboard
- Users
- All Rides
- Ongoing Trips
- Completed Trips
- Back to Main Site
- Logout

### Status Indicators
**User Status:**
- 🟢 Green badge: Active
- ⚫ Gray badge: Inactive
- 🔵 Blue badge: Staff member
- ✅ Green badge: Aadhaar verified

**Ride Status:**
- 🔵 Blue badge: Created
- 🟡 Yellow badge: Started
- 🟢 Green badge: Completed

**Confirmations:**
- ✅ Green checkmark: Confirmed
- ⭕ Gray circle: Not confirmed
- ❌ Red X: Missing (completed rides only)

### Search & Filter
- Real-time search across multiple fields
- Status filters for quick access
- Clear filters option when active

## Setting Up an Admin User

### Method 1: Django Shell
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User

# Create a new staff user
user = User.objects.create_user(
    username='admin',
    email='admin@example.com',
    password='your_secure_password'
)
user.is_staff = True
user.save()
```

### Method 2: Update Existing User
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User

# Make existing user a staff member
user = User.objects.get(email='user@example.com')
user.is_staff = True
user.save()
```

### Method 3: Django Admin (if enabled)
1. Access `/admin/`
2. Log in as superuser
3. Find user in Users list
4. Check "Staff status" checkbox
5. Save

## URLs Summary

| URL | View | Purpose |
|-----|------|---------|
| `/custom-admin/` | Dashboard | Overview statistics |
| `/custom-admin/users/` | User list | Manage users |
| `/custom-admin/users/<id>/toggle-status/` | Toggle status | Activate/deactivate |
| `/custom-admin/rides/` | Ride list | Manage rides |
| `/custom-admin/rides/<id>/` | Ride detail | View ride details |
| `/custom-admin/rides/<id>/cancel/` | Cancel ride | Delete ride |
| `/custom-admin/trips/ongoing/` | Ongoing trips | Monitor active rides |
| `/custom-admin/trips/completed/` | Completed trips | View history |

## Best Practices

### For Administrators
1. **User Management:**
   - Deactivate suspicious accounts instead of deleting
   - Verify Aadhaar status before handling disputes
   - Contact users via phone before deactivation

2. **Ride Management:**
   - Monitor ongoing trips regularly
   - Only cancel rides when absolutely necessary
   - Check both confirmations before intervening

3. **Security:**
   - Don't share staff credentials
   - Use strong passwords
   - Log out after each session
   - Regularly review user activity

4. **Data Integrity:**
   - Avoid unnecessary cancellations
   - Let rides complete naturally
   - Only intervene in case of reports

## Troubleshooting

### Cannot Access Admin Dashboard
- Check if user has `is_staff=True`
- Verify user is logged in
- Clear browser cache
- Check URL is `/custom-admin/` not `/admin/`

### Permission Denied
- Ensure user account is active (`is_active=True`)
- Verify staff status in database
- Try logging out and back in

### Changes Not Saving
- Check for JavaScript errors in console
- Verify CSRF token is present
- Check server logs for errors
- Ensure database is not read-only

## Technical Details

### Technologies Used
- **Backend:** Django views with decorators
- **Frontend:** Bootstrap 5, Bootstrap Icons
- **Security:** Django CSRF, staff_member_required
- **Database:** Django ORM (works with any DB)

### Code Structure
```
rides/
├── views.py              # Admin views (bottom of file)
├── urls.py               # URL patterns
└── templates/
    └── rides/
        └── admin/
            ├── base.html              # Base template with sidebar
            ├── dashboard.html         # Main dashboard
            ├── users_list.html        # User management
            ├── rides_list.html        # Ride list
            ├── ride_detail.html       # Ride details
            ├── trips_ongoing.html     # Ongoing monitoring
            └── trips_completed.html   # Completed history
```

### Database Models Used
- `User` (Django built-in)
- `UserProfile` (custom)
- `Ride` (custom)
- `RidePassenger` (custom)

## Future Enhancements (Optional)

Possible additions:
- Export data to CSV/Excel
- Advanced analytics and charts
- Email notifications to users
- Bulk actions (multiple users/rides)
- Activity logs/audit trail
- Advanced filtering (date ranges, etc.)
- Pagination for large datasets
- User communication (send messages)
- Report generation (PDF reports)

## Support

If you encounter issues:
1. Check Django logs for errors
2. Verify database migrations are applied
3. Ensure all dependencies are installed
4. Check browser console for JS errors
5. Review this documentation

---

**Note:** This is a custom admin interface separate from Django's default admin. Both can coexist without conflicts.
