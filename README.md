# EcoCommute 🚗🌱

**EcoCommute** - Smarter rides for a greener planet

A Django-based carpooling and ride-sharing platform with Aadhaar verification, real-time location tracking, and admin management features.

---

## 🌟 Features

- **User Authentication**: Secure registration and login system
- **Aadhaar Verification**: Integration with Aadhaar API for user verification
- **Ride Creation & Management**: Create and manage carpool rides
- **Real-time Location Tracking**: Live location sharing during active rides
- **Two-way Confirmation System**: Driver and passenger confirmation workflow
- **Admin Dashboard**: Comprehensive admin panel for managing users, rides, and trips
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **WhatsApp Integration**: Phone number formatting for WhatsApp communication

---

## 📁 Project Structure

```
ecocommut/
├── ecocommute/              # Django project settings
│   ├── settings.py          # Project configuration
│   ├── urls.py              # Main URL routing
│   └── wsgi.py              # WSGI configuration
├── rides/                   # Main application
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── admin.py             # Admin configuration
│   ├── aadhaar_service.py   # Aadhaar verification service
│   ├── templates/           # HTML templates
│   └── management/          # Custom management commands
├── static/                  # Static files (CSS, JS)
├── templates/               # Base templates
├── db.sqlite3               # SQLite database
├── manage.py                # Django management script
└── requirements.txt         # Python dependencies
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

1. **Clone the repository or navigate to the project directory**
   ```bash
   cd "C:\Users\Admin\Desktop\ride ecocommut"
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (admin)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Seed sample data (optional)**
   ```bash
   python manage.py seed_data
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main app: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

---

## 📊 Database Models

### User
Django's built-in User model extended with:

### UserProfile
- `user` - OneToOne relationship with User
- `phone_number` - Contact number (WhatsApp enabled)
- `aadhaar_number` - Aadhaar ID (encrypted)
- `aadhaar_verified` - Verification status
- `aadhaar_consent_given` - User consent flag

### Ride
- `driver` - ForeignKey to User
- `from_location` - Starting point
- `to_location` - Destination
- `ride_date` - Date of ride
- `ride_time` - Time of ride
- `vehicle_type` - Type of vehicle
- `vehicle_number` - Registration number
- `total_seats` - Total available seats
- `seats_available` - Current available seats
- `distance_km` - Distance in kilometers
- `driver_started` - Ride start status
- `driver_ended_ride` - Ride completion status

### RidePassenger
- `user` - ForeignKey to User
- `ride` - ForeignKey to Ride
- `status` - (pending/confirmed/cancelled)
- `joined_at` - Timestamp
- `pickup_location` - Custom pickup point
- `pickup_notes` - Additional notes

### LiveLocation
- `user` - ForeignKey to User
- `ride` - ForeignKey to Ride
- `latitude` - GPS latitude
- `longitude` - GPS longitude
- `timestamp` - Last update time

---

## 🛠️ Management Commands

### Create Missing Profiles
```bash
python manage.py create_missing_profiles
```
Creates UserProfile instances for existing users.

### Delete User
```bash
python manage.py delete_user <username>
```
Safely delete a user and their related data.

### Seed Sample Data
```bash
python manage.py seed_data
```
Populate the database with sample users and rides.

---

## 🔐 Admin Features

The custom admin panel includes:
- **Dashboard**: Overview of users, rides, and trips
- **User Management**: View and manage all registered users
- **Ride Management**: Monitor all rides with filtering options
- **Ongoing Trips**: Track active rides in real-time
- **Completed Trips**: View ride history and statistics

Access admin at: `/rides/admin/`

---

## 📱 Key Features Documentation

### Aadhaar Verification
See [AADHAAR_IMPLEMENTATION_GUIDE.md](AADHAAR_IMPLEMENTATION_GUIDE.md) for complete integration details.

### Location Tracking
See [LOCATION_TRACKING_GUIDE.md](LOCATION_TRACKING_GUIDE.md) for real-time tracking implementation.

### Two-way Confirmation
See [TWO_SIDE_CONFIRMATION.md](TWO_SIDE_CONFIRMATION.md) for confirmation workflow.

### Admin Architecture
See [ADMIN_ARCHITECTURE.md](ADMIN_ARCHITECTURE.md) for admin system details.

---

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Test Admin Functionality
```bash
python test_admin.py
```

### Testing Checklist
See [ADMIN_TESTING_CHECKLIST.md](ADMIN_TESTING_CHECKLIST.md)

---

## 📝 Configuration

### Environment Variables (Optional)
Create a `.env` file for sensitive settings:
```
SECRET_KEY=your-secret-key
DEBUG=True
AADHAAR_API_KEY=your-aadhaar-api-key
```

### Settings
Key settings in `ecocommute/settings.py`:
- `DEBUG`: Development mode
- `ALLOWED_HOSTS`: Allowed domains
- `DATABASES`: Database configuration
- `STATIC_URL`: Static files path

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 License

This project is developed for educational and demonstration purposes.

---

## 📞 Support

For issues and questions:
- Check the documentation files in the project root
- Review the implementation guides
- Contact the development team

---

## 🎯 Future Enhancements

- [ ] Payment integration
- [ ] Rating and review system
- [ ] SMS notifications
- [ ] Mobile app (React Native)
- [ ] Advanced analytics
- [ ] Multi-language support

---

**Built with Django 🎸 | Making commutes greener, one ride at a time 🌍**
