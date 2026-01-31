# 🚀 Live Location Tracking - Quick Reference Card

## For Passengers

### Share Your Location
1. Join a ride
2. Go to ride detail page
3. Click **"Share My Location"** (orange button)
4. Click **"Start Sharing Location"**
5. Allow browser location permission

**To Stop**: Click "Stop Sharing" button

---

## For Ride Creators

### Track Passengers
1. Create a ride
2. Go to ride detail page
3. Click **"Track Passenger Locations"** (blue button)
4. View live map with passenger markers

**Features**: 
- Map auto-refreshes every 4 seconds
- Click markers for details
- Use "Locate" to center on passenger

---

## URLs

| Page | URL Pattern |
|------|-------------|
| Share Location (Passenger) | `/rides/{ride_id}/share-location/` |
| Track Ride (Creator) | `/rides/{ride_id}/track/` |
| Update Location API | `/location/update/` (POST) |
| Get Location API | `/location/get/{user_id}/{ride_id}/` (GET) |
| Stop Sharing API | `/location/stop/` (POST) |

---

## API Quick Reference

### Update Location (POST)
```javascript
POST /location/update/
Body: {
  ride_id: 123,
  latitude: 12.9716,
  longitude: 77.5946,
  is_sharing: "true"
}
```

### Get Location (GET)
```javascript
GET /location/get/5/123/
Response: {
  user_id: 5,
  latitude: 12.9716,
  longitude: 77.5946,
  updated_at: "2026-01-30T10:30:45Z"
}
```

---

## Database Model

```python
class LiveLocation(models.Model):
    user = OneToOneField(User)      # One per user
    ride = ForeignKey(Ride)          # Associated ride
    latitude = FloatField()          # Current lat
    longitude = FloatField()         # Current lng
    updated_at = DateTimeField()     # Auto timestamp
    is_sharing = BooleanField()      # Consent flag
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Django |
| Frontend | Vanilla JavaScript + Tailwind CSS |
| Map | Leaflet.js + OpenStreetMap |
| Location API | Browser Geolocation API |
| Updates | HTTP Polling (3-5 seconds) |
| Cost | $0 (completely free) |

---

## Key Features

✅ Real-time tracking (3-5 second updates)  
✅ No location history stored  
✅ Explicit user consent required  
✅ Only creator can view  
✅ Free (no API costs)  
✅ Privacy-first design  
✅ Works on mobile and desktop  

---

## Security Checklist

- [x] Authentication required
- [x] CSRF protection enabled
- [x] Passenger verification
- [x] Creator-only access
- [x] Input validation
- [x] No location history
- [x] User-controlled sharing

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Permission denied | Check browser location settings |
| Map not loading | Check internet, disable ad blockers |
| Location not updating | Refresh page, check WiFi/GPS |
| High battery drain | Plug in device, stop sharing when not needed |

---

## Testing Commands

```bash
# Check for errors
python manage.py check

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start server
python manage.py runserver

# Create superuser
python manage.py createsuperuser
```

---

## File Locations

### Backend
- Models: `rides/models.py`
- Views: `rides/views.py`
- URLs: `rides/urls.py`
- Admin: `rides/admin.py`

### Frontend
- Share Location: `rides/templates/rides/share_location.html`
- Track Map: `rides/templates/rides/track_ride.html`
- Ride Detail: `rides/templates/rides/ride_detail.html`

### Documentation
- Technical Guide: `LOCATION_TRACKING_GUIDE.md`
- User Guide: `LOCATION_TRACKING_USER_GUIDE.md`
- Summary: `LOCATION_TRACKING_SUMMARY.md`

---

## Demo Script (30 seconds)

1. "This uses browser Geolocation API with user consent"
2. "Passenger clicks Start Sharing, browser asks permission"
3. "Location sent to server every 3-5 seconds via POST"
4. "Creator's map polls server every 4 seconds via GET"
5. "Only latest position stored - no history"
6. "Free OpenStreetMap tiles, no billing"

---

## Privacy Promise

🔒 **We collect**: Current lat/lng, timestamp  
🚫 **We DON'T collect**: History, patterns, addresses  
👁️ **Who can see**: Only the ride creator  
⏱️ **How long**: Until you stop sharing or ride ends  
✋ **Your control**: Start/stop anytime  

---

## Browser Compatibility

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | 50+ | ✅ |
| Firefox | 55+ | ✅ |
| Safari | 10+ | ✅ |
| Edge | 79+ | ✅ |
| iOS Safari | 10+ | ✅ |
| Android Chrome | 50+ | ✅ |

---

## Performance

| Metric | Value |
|--------|-------|
| Update Frequency | 3-5 seconds |
| Data per Update | ~1 KB |
| Data per Hour | ~720 KB |
| Battery Impact | Moderate (GPS) |
| Server Load | Minimal |

---

## Contact & Support

📖 **Documentation**: See `LOCATION_TRACKING_*.md` files  
🔧 **Troubleshooting**: Check user guide  
💻 **Code Comments**: Inline in all files  
🎓 **Workshop**: Follow demo script  

---

*Quick Reference v1.0 - EcoCommute*  
*Last Updated: January 30, 2026*
