# EcoCommute - Django Carpooling Platform

## 🚀 This is a Django Application

Your application is **fully Django-based** and working correctly.

## 📁 Active Django Files (Keep These)

### Django Project: `ecocommute/`
- `settings.py` - Configuration
- `urls.py` - Main URL routing
- `wsgi.py` / `asgi.py` - Server files

### Django App: `rides/`
- `models.py` - Database models (Ride, RidePassenger)
- `views.py` - Business logic and views
- `urls.py` - App URL routing
- `templates/rides/` - HTML templates
- `admin.py` - Django admin configuration

### Other Important Files
- `manage.py` - Django command-line tool
- `db.sqlite3` - Your Django database
- `requirements.txt` - Python dependencies
- `static/css/style.css` - Stylesheets

## ❌ Old Flask Files (Can Be Deleted)

These files are from the original Flask version and are NOT being used:

- `app.py` - Old Flask application
- `instance/` - Old Flask database folder
- `*.html` files in root (dashboard.html, login.html, etc.) - Old Flask templates

**Note:** The active templates are in `rides/templates/rides/`

## 🏃 How to Run

```bash
# Start Django development server
python manage.py runserver

# Access at: http://127.0.0.1:8000/
```

## 🗄️ Database Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Seed sample data
python manage.py seed_data
```

## ✨ Features

- User registration and authentication
- Create and browse rides
- Join rides as passenger
- Cancel joined rides
- CO₂ emissions tracking
- Gamification (Eco Champion Badge)
- Modern Tailwind CSS UI

## 🎨 Tech Stack

- **Backend:** Django 6.0.1
- **Frontend:** Django Templates + Tailwind CSS
- **Database:** SQLite
- **Authentication:** Django Auth System
