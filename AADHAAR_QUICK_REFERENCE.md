# Aadhaar OTP Authentication - Quick Reference

## 🚀 Quick Start (5 Minutes)

### For Development (Mock Mode)

```bash
# 1. Already done - migrations applied
# 2. Settings already configured for mock mode

# 3. Start server
python manage.py runserver

# 4. Test Flow
# - Login/Register
# - Dashboard will show "Verify Aadhaar" banner
# - Click "Verify Aadhaar Now"
# - Enter: 1234-5678-9012 (any 12 digits)
# - Check consent checkbox
# - Click "Send OTP"
# - Enter OTP: 123456 (mock OTP)
# - Click "Verify OTP"
# - Success! Dashboard shows verified status
```

---

## 📋 API Reference

### Send OTP

```python
from rides.aadhaar_service import get_aadhaar_service

service = get_aadhaar_service()
success, message, transaction_id = service.send_otp("123456789012")

# Returns:
# (True, "OTP sent to XXXXXX1234", "TXN123456789")
```

### Verify OTP

```python
success, message, user_data = service.verify_otp("TXN123456789", "123456")

# Returns:
# (True, "Verified successfully", {"full_name": "JOHN DOE", "dob": "01/01/1990"})
```

---

## 🔗 URLs

| Page | URL |
|------|-----|
| Start Verification | `/aadhaar/verify/` |
| Send OTP | `/aadhaar/send-otp/` (POST) |
| Enter OTP | `/aadhaar/verify-otp/` |
| Submit OTP | `/aadhaar/submit-otp/` (POST) |
| Resend OTP | `/aadhaar/resend-otp/` |

---

## 🗄️ Database Fields

| Field | Type | Example | Stored? |
|-------|------|---------|---------|
| `aadhaar_verified` | Boolean | `True` | ✅ |
| `aadhaar_last_4_digits` | String | `"9012"` | ✅ |
| `aadhaar_consent_given` | Boolean | `True` | ✅ |
| `aadhaar_verified_at` | DateTime | `2026-01-30 10:30` | ✅ |
| Full Aadhaar | String | `"123456789012"` | ❌ NEVER |
| OTP | String | `"123456"` | ❌ NEVER |

---

## ⚙️ Configuration

### Mock Mode (Development)
```python
# settings.py or .env
AADHAAR_USE_MOCK = True
# Mock OTP: 123456
```

### Production Mode
```python
AADHAAR_USE_MOCK = False
AADHAAR_API_PROVIDER = 'cashfree'  # or 'signzy', 'surepass'
AADHAAR_API_CLIENT_ID = 'your_client_id'
AADHAAR_API_SECRET_KEY = 'your_secret_key'
AADHAAR_API_SANDBOX = False
```

---

## 🧪 Testing

### Mock Mode OTP
Always use: **123456**

### Test Aadhaar Numbers
Any 12-digit number works in mock mode:
- 1234-5678-9012 ✅
- 9876-5432-1098 ✅
- 1111-2222-3333 ✅

---

## 🔒 Security Checklist

- [x] Full Aadhaar NEVER stored
- [x] Only last 4 digits stored
- [x] Explicit consent required
- [x] HTTPS only (production)
- [x] Session-based transaction IDs
- [x] 10-minute OTP timeout
- [x] CSRF protection enabled
- [x] Backend-only API calls

---

## 🐛 Common Issues

| Problem | Solution |
|---------|----------|
| "Consent required" | Check consent checkbox |
| "Invalid Aadhaar" | Must be 12 digits |
| "Invalid OTP" | Use 123456 in mock mode |
| "Session expired" | Request new OTP (>10 min) |
| "Already verified" | User already verified |

---

## 📱 User Flow

```
1. Dashboard → See "Verify Aadhaar" banner
2. Click "Verify Aadhaar Now"
3. Enter Aadhaar number (12 digits)
4. Check consent checkbox
5. Click "Send OTP"
6. Enter 6-digit OTP
7. Click "Verify OTP"
8. Success! Can now create/join rides
```

---

## 🛑 Restrictions

**Users WITHOUT Aadhaar verification:**
- ❌ Cannot create rides
- ❌ Cannot join rides
- ✅ Can browse rides
- ✅ Can view profile

**Users WITH Aadhaar verification:**
- ✅ Can create rides
- ✅ Can join rides
- ✅ Full platform access

---

## 🎯 Provider Setup (Production)

### Cashfree
1. Visit: https://www.cashfree.com/verification-api
2. Sign up & verify business
3. Get API credentials
4. Set in .env file

### Signzy
1. Visit: https://signzy.com/
2. Sign up & KYC
3. Enable Aadhaar verification
4. Get API key

### Surepass
1. Visit: https://surepass.io/
2. Create account
3. Subscribe to Aadhaar API
4. Get credentials

---

## 💰 Cost Estimate

| Provider | Cost per Verification |
|----------|----------------------|
| Cashfree | ₹3-5 |
| Signzy | ₹4-6 |
| Surepass | ₹2-4 |

**Estimated Monthly Cost (1000 users):**
- First month: ₹2,000 - ₹6,000
- Ongoing: ~₹500/month (new users only)

---

## 📊 Admin Panel

### View Verified Users

```python
# In Django Admin
http://localhost:8000/admin/rides/userprofile/

# Filter by:
- aadhaar_verified = True/False
- aadhaar_consent_given
- aadhaar_verified_at (date)
```

### Export Verification Stats

```python
# In Django shell
from rides.models import UserProfile

total_users = UserProfile.objects.count()
verified_users = UserProfile.objects.filter(aadhaar_verified=True).count()
verification_rate = (verified_users / total_users * 100) if total_users > 0 else 0

print(f"Total Users: {total_users}")
print(f"Verified: {verified_users}")
print(f"Rate: {verification_rate:.1f}%")
```

---

## 📝 Logging

### Check Logs

```bash
# Verification attempts
grep "Sending OTP" logs/django.log

# Successful verifications
grep "OTP verified successfully" logs/django.log

# Failed attempts
grep "verification failed" logs/django.log
```

---

## 🔧 Maintenance

### Clear Old Sessions
```bash
python manage.py clearsessions
```

### Reset User Verification (Admin Only)
```python
# Django shell
from rides.models import UserProfile

profile = UserProfile.objects.get(user__email='user@example.com')
profile.aadhaar_verified = False
profile.aadhaar_last_4_digits = None
profile.save()
```

---

## 📞 Support Contacts

**For Users:**
- Help: /aadhaar/verify/ → "Need Help?" section
- Email: support@ecocommute.com

**For Developers:**
- Docs: `AADHAAR_IMPLEMENTATION_GUIDE.md`
- Code: Inline comments in `aadhaar_service.py`

---

## ✅ Production Checklist

Before going live:

- [ ] API credentials obtained
- [ ] Environment variables set
- [ ] AADHAAR_USE_MOCK = False
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Error monitoring setup
- [ ] Backup strategy in place
- [ ] User privacy policy updated
- [ ] Terms of service updated
- [ ] Test with real Aadhaar (your own)

---

**Version:** 1.0.0  
**Last Updated:** January 30, 2026  
**Status:** Production-Ready ✅
