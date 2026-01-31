# Aadhaar OTP Authentication - Complete Implementation Guide

## 🔐 Overview

This implementation provides **compliant, secure, and production-ready Aadhaar OTP authentication** for the EcoCommute Django application using licensed third-party API providers (Cashfree, Signzy, or Surepass).

### ✅ Key Features

- ✅ Two-step OTP verification flow (Send OTP → Verify OTP)
- ✅ **Full Aadhaar number NEVER stored** (compliant with Aadhaar Act)
- ✅ Only stores verification status + last 4 digits (masked)
- ✅ Explicit user consent required (DPDP Act compliant)
- ✅ Backend-only API calls (no frontend exposure)
- ✅ HTTPS encrypted transmission
- ✅ Comprehensive error handling
- ✅ Mock/Sandbox mode for development
- ✅ Production-ready with security best practices

---

## 📋 Table of Contents

1. [Legal & Compliance](#legal--compliance)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Database Models](#database-models)
5. [API Integration Service](#api-integration-service)
6. [Views & URLs](#views--urls)
7. [Frontend Templates](#frontend-templates)
8. [Configuration](#configuration)
9. [Testing](#testing)
10. [Production Deployment](#production-deployment)
11. [Security Best Practices](#security-best-practices)
12. [Troubleshooting](#troubleshooting)

---

## 🏛️ Legal & Compliance

### Aadhaar Act 2016

This implementation complies with:
- **Section 8**: No Aadhaar number storage except as permitted
- **Section 29**: No disclosure of Aadhaar number
- **Section 57**: Use only for verification purposes

**Compliance Measures:**
- ✅ Full Aadhaar number NEVER stored in database
- ✅ Only verification status + last 4 digits retained
- ✅ Explicit consent obtained before verification
- ✅ Clear privacy notice displayed to users
- ✅ Data minimization principle followed

### Digital Personal Data Protection Act (DPDP) 2023

**Compliance Measures:**
- ✅ Explicit consent with checkbox (not pre-checked)
- ✅ Clear purpose specification (identity verification)
- ✅ Data minimization (only essential data stored)
- ✅ Right to erasure supported
- ✅ Consent timestamp recorded for audit trail

### UIDAI Guidelines

- ✅ Licensed API provider used (Cashfree/Signzy/Surepass)
- ✅ No direct UIDAI scraping or unauthorized access
- ✅ Secure transmission (HTTPS only)
- ✅ Backend-only processing

---

## 🏗️ Architecture

### Data Flow

```
User → Frontend (HTTPS) → Django Backend → Licensed API Provider → UIDAI
                              ↓
                         Database (only verification status + last 4 digits)
```

### Components

1. **Frontend (HTML/JS)**
   - Aadhaar input form with consent
   - OTP entry form
   - User-friendly error messages

2. **Backend (Django)**
   - `AadhaarVerificationService` - API integration
   - Views for send_otp, verify_otp
   - UserProfile model with verification fields

3. **External (API Provider)**
   - Cashfree / Signzy / Surepass
   - Handles actual Aadhaar verification via UIDAI

---

## 📦 Installation & Setup

### Step 1: Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the following fields in `UserProfile`:
- `aadhaar_verified` (boolean)
- `aadhaar_last_4_digits` (string, 4 chars)
- `aadhaar_consent_given` (boolean)
- `aadhaar_consent_timestamp` (datetime)
- `aadhaar_verified_at` (datetime)

### Step 2: Install Dependencies

```bash
pip install requests  # For API calls (should already be installed)
```

### Step 3: Configure Settings

Add to `settings.py`:

```python
# Aadhaar Verification Settings
AADHAAR_API_PROVIDER = os.environ.get('AADHAAR_API_PROVIDER', 'cashfree')
AADHAAR_API_CLIENT_ID = os.environ.get('AADHAAR_API_CLIENT_ID', 'sandbox_client_id')
AADHAAR_API_SECRET_KEY = os.environ.get('AADHAAR_API_SECRET_KEY', 'sandbox_secret_key')
AADHAAR_API_SANDBOX = os.environ.get('AADHAAR_API_SANDBOX', 'True') == 'True'
AADHAAR_USE_MOCK = os.environ.get('AADHAAR_USE_MOCK', 'True') == 'True'
```

### Step 4: Set Environment Variables

Create `.env` file:

```env
# Development (Mock Mode)
AADHAAR_USE_MOCK=True

# Production (Real API)
AADHAAR_USE_MOCK=False
AADHAAR_API_PROVIDER=cashfree
AADHAAR_API_CLIENT_ID=your_actual_client_id
AADHAAR_API_SECRET_KEY=your_actual_secret_key
AADHAAR_API_SANDBOX=False
```

**IMPORTANT:** Never commit `.env` file to Git! Add to `.gitignore`.

---

## 🗄️ Database Models

### UserProfile Model

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Aadhaar Verification Fields (Compliant)
    aadhaar_verified = models.BooleanField(default=False)
    aadhaar_last_4_digits = models.CharField(max_length=4, blank=True, null=True)
    aadhaar_consent_given = models.BooleanField(default=False)
    aadhaar_consent_timestamp = models.DateTimeField(null=True, blank=True)
    aadhaar_verified_at = models.DateTimeField(null=True, blank=True)
    
    @property
    def aadhaar_masked(self):
        """Returns XXXX-XXXX-1234 format"""
        if self.aadhaar_last_4_digits:
            return f"XXXX-XXXX-{self.aadhaar_last_4_digits}"
        return None
    
    def can_create_or_join_rides(self):
        """Check if user can create/join rides"""
        return self.aadhaar_verified
```

### What is Stored?

| Field | Example | Purpose |
|-------|---------|---------|
| `aadhaar_verified` | `True` | Verification status |
| `aadhaar_last_4_digits` | `"1234"` | Display only (XXXX-XXXX-1234) |
| `aadhaar_consent_given` | `True` | User gave consent |
| `aadhaar_consent_timestamp` | `2026-01-30T10:30:00Z` | When consent was given |
| `aadhaar_verified_at` | `2026-01-30T10:35:00Z` | When verification completed |

### What is NOT Stored?

- ❌ Full Aadhaar number (1234-5678-9012)
- ❌ OTP codes
- ❌ Transaction IDs (only in session)
- ❌ Personal details from Aadhaar (name, DOB, address)

---

## 🔌 API Integration Service

### File: `rides/aadhaar_service.py`

### AadhaarVerificationService Class

```python
from rides.aadhaar_service import get_aadhaar_service

# In your view
service = get_aadhaar_service()
success, message, transaction_id = service.send_otp(aadhaar_number)
```

### Methods

#### 1. `send_otp(aadhaar_number)`

**Purpose:** Send OTP to Aadhaar-linked mobile number

**Parameters:**
- `aadhaar_number` (str): 12-digit Aadhaar number

**Returns:**
```python
(success, message, transaction_id)
# Example: (True, "OTP sent to XXXXXX1234", "TXN123456789")
```

**API Request Example (Cashfree):**
```json
POST https://api.cashfree.com/verification/aadhaar/otp
Headers: {
  "Content-Type": "application/json",
  "X-Client-Id": "your_client_id",
  "X-Client-Secret": "your_secret_key"
}
Body: {
  "aadhaar_number": "123456789012",
  "request_id": "unique_request_id"
}
```

**API Response Example:**
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "transaction_id": "TXN123456789",
  "mobile_masked": "XXXXXX1234"
}
```

#### 2. `verify_otp(transaction_id, otp)`

**Purpose:** Verify OTP entered by user

**Parameters:**
- `transaction_id` (str): From send_otp response
- `otp` (str): 6-digit OTP

**Returns:**
```python
(success, message, user_data)
# Example: (True, "Verified successfully", {"full_name": "JOHN DOE", "dob": "01/01/1990"})
```

**API Request Example:**
```json
POST https://api.cashfree.com/verification/aadhaar/verify
Headers: { ... }
Body: {
  "transaction_id": "TXN123456789",
  "otp": "123456"
}
```

**API Response Example:**
```json
{
  "success": true,
  "message": "Verification successful",
  "data": {
    "full_name": "JOHN DOE",
    "dob": "01/01/1990",
    "gender": "M",
    "address": { ... }
  }
}
```

### Mock Mode (Development)

For testing without real API:

```python
# In settings.py
AADHAAR_USE_MOCK = True

# Mock OTP is always: 123456
# Any valid Aadhaar format will work
```

---

## 🔀 Views & URLs

### View Flow

```
1. aadhaar_verification_start → Display Aadhaar input form
2. aadhaar_send_otp → Send OTP via API
3. aadhaar_verify_otp → Display OTP input form
4. aadhaar_submit_otp → Verify OTP via API
5. aadhaar_resend_otp → Resend OTP
```

### URL Routes

```python
# In rides/urls.py
path('aadhaar/verify/', views.aadhaar_verification_start, name='aadhaar_verification_start'),
path('aadhaar/send-otp/', views.aadhaar_send_otp, name='aadhaar_send_otp'),
path('aadhaar/verify-otp/', views.aadhaar_verify_otp, name='aadhaar_verify_otp'),
path('aadhaar/submit-otp/', views.aadhaar_submit_otp, name='aadhaar_submit_otp'),
path('aadhaar/resend-otp/', views.aadhaar_resend_otp, name='aadhaar_resend_otp'),
```

### Key Views

#### 1. `aadhaar_send_otp` (POST)

**Security Checks:**
- ✅ Explicit consent checkbox required
- ✅ Aadhaar format validation
- ✅ CSRF protection
- ✅ Authentication required

**Process:**
1. Validate consent checkbox
2. Validate Aadhaar format (12 digits)
3. Record consent timestamp
4. Call API provider's send_otp
5. Store transaction_id in session (NOT database)
6. Redirect to OTP entry page

#### 2. `aadhaar_submit_otp` (POST)

**Security Checks:**
- ✅ Session timeout (10 minutes)
- ✅ Transaction ID validation
- ✅ OTP format validation

**Process:**
1. Get OTP from form
2. Get transaction_id from session
3. Call API provider's verify_otp
4. On success:
   - Update UserProfile (aadhaar_verified = True)
   - Store last 4 digits only
   - Clear session data
   - Redirect to dashboard
5. On failure:
   - Show error message
   - Allow retry

### Session Data

**What's Stored in Session (Temporary):**
```python
request.session['aadhaar_transaction_id'] = "TXN123456789"
request.session['aadhaar_last_4'] = "1234"
request.session['aadhaar_otp_sent_at'] = "2026-01-30T10:30:00Z"
```

**Why Session and Not Database?**
- Session data expires automatically
- More secure (not persisted)
- Prevents transaction ID leakage
- Automatically cleared after verification

---

## 🎨 Frontend Templates

### 1. `aadhaar_verify_start.html`

**Features:**
- Aadhaar number input with auto-formatting
- Mandatory consent checkbox
- Privacy & security notice
- Clear explanation of data handling
- Legal compliance notice

**JavaScript:**
- Auto-formats Aadhaar (1234-5678-9012)
- Validates consent before submit
- Only allows digits

### 2. `aadhaar_verify_otp.html`

**Features:**
- 6-digit OTP input
- 10-minute countdown timer
- Resend OTP option
- Security tips
- Auto-focus on OTP field

**JavaScript:**
- Countdown timer (10 minutes)
- Auto-submit option
- Prevents double submission
- Session timeout warning

---

## ⚙️ Configuration

### Environment Variables

```env
# Required for Production
AADHAAR_API_PROVIDER=cashfree  # or signzy, surepass
AADHAAR_API_CLIENT_ID=your_client_id_here
AADHAAR_API_SECRET_KEY=your_secret_key_here
AADHAAR_API_SANDBOX=False
AADHAAR_USE_MOCK=False
```

### API Provider Setup

#### Option 1: Cashfree
1. Sign up: https://www.cashfree.com/verification-api
2. Get API credentials from dashboard
3. Set `AADHAAR_API_PROVIDER=cashfree`

#### Option 2: Signzy
1. Sign up: https://signzy.com/
2. Enable Aadhaar verification
3. Set `AADHAAR_API_PROVIDER=signzy`

#### Option 3: Surepass
1. Sign up: https://surepass.io/
2. Subscribe to Aadhaar verification API
3. Set `AADHAAR_API_PROVIDER=surepass`

### Provider Comparison

| Provider | Sandbox | Pricing | Support |
|----------|---------|---------|---------|
| Cashfree | ✅ Free | ₹3-5 per verification | Good |
| Signzy | ✅ Free | ₹4-6 per verification | Excellent |
| Surepass | ✅ Free | ₹2-4 per verification | Good |

---

## 🧪 Testing

### Manual Testing (Mock Mode)

```bash
# 1. Set mock mode
AADHAAR_USE_MOCK=True

# 2. Start server
python manage.py runserver

# 3. Test flow
# - Register/Login
# - Go to dashboard
# - Click "Verify Aadhaar Now"
# - Enter any valid 12-digit Aadhaar (e.g., 1234-5678-9012)
# - Check consent checkbox
# - Click "Send OTP"
# - Enter OTP: 123456 (mock OTP)
# - Click "Verify OTP"
# - Should show success and redirect to dashboard
```

### Test Cases

#### Test 1: Valid Aadhaar + Valid OTP
- **Aadhaar:** 123456789012
- **OTP:** 123456 (mock mode)
- **Expected:** Success, user marked as verified

#### Test 2: Invalid Aadhaar Format
- **Aadhaar:** 12345 (too short)
- **Expected:** Error "Aadhaar must be 12 digits"

#### Test 3: No Consent
- **Aadhaar:** 123456789012
- **Consent:** Unchecked
- **Expected:** Error "You must give consent"

#### Test 4: Invalid OTP
- **OTP:** 000000 (mock mode)
- **Expected:** Error "Invalid OTP"

#### Test 5: Expired OTP
- Wait 11 minutes after sending OTP
- **Expected:** Session timeout, redirect to start

### Automated Testing

```python
# tests.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rides.models import UserProfile
from rides.aadhaar_service import MockAadhaarService

class AadhaarVerificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('test@example.com', password='test123')
        self.client.login(username='test@example.com', password='test123')
    
    def test_send_otp_without_consent(self):
        response = self.client.post('/aadhaar/send-otp/', {
            'aadhaar_number': '123456789012',
            # No consent checkbox
        })
        self.assertRedirects(response, '/aadhaar/verify/')
        messages = list(response.wsgi_request._messages)
        self.assertIn('consent', str(messages[0]))
    
    def test_send_otp_with_consent(self):
        response = self.client.post('/aadhaar/send-otp/', {
            'aadhaar_number': '123456789012',
            'consent': 'on'
        })
        self.assertRedirects(response, '/aadhaar/verify-otp/')
    
    def test_verify_otp_success(self):
        # First send OTP
        self.client.post('/aadhaar/send-otp/', {
            'aadhaar_number': '123456789012',
            'consent': 'on'
        })
        
        # Then verify
        response = self.client.post('/aadhaar/submit-otp/', {
            'otp': '123456'
        })
        
        # Check user is verified
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.aadhaar_verified)
        self.assertEqual(self.user.profile.aadhaar_last_4_digits, '9012')
```

---

## 🚀 Production Deployment

### Pre-Deployment Checklist

- [ ] API credentials obtained from provider
- [ ] Environment variables set correctly
- [ ] `AADHAAR_USE_MOCK=False`
- [ ] `AADHAAR_API_SANDBOX=False` (for live API)
- [ ] HTTPS enabled (mandatory)
- [ ] Database backed up
- [ ] Error logging configured
- [ ] Rate limiting configured

### Deployment Steps

1. **Set Production Environment Variables**
```bash
export AADHAAR_USE_MOCK=False
export AADHAAR_API_PROVIDER=cashfree
export AADHAAR_API_CLIENT_ID=prod_client_id
export AADHAAR_API_SECRET_KEY=prod_secret_key
export AADHAAR_API_SANDBOX=False
```

2. **Migrate Database**
```bash
python manage.py migrate
```

3. **Collect Static Files**
```bash
python manage.py collectstatic
```

4. **Test API Connection**
```bash
python manage.py shell
>>> from rides.aadhaar_service import get_aadhaar_service
>>> service = get_aadhaar_service()
>>> # Test with a real Aadhaar (your own)
```

5. **Deploy Application**
```bash
# Using Gunicorn
gunicorn ecocommute.wsgi:application --bind 0.0.0.0:8000

# Or using uWSGI
uwsgi --http :8000 --module ecocommute.wsgi
```

### Monitoring

**Key Metrics to Monitor:**
- API success rate
- Average verification time
- Failed verification reasons
- Session timeout rate
- API cost per verification

---

## 🔒 Security Best Practices

### 1. Never Store Full Aadhaar
```python
# ❌ WRONG
user.profile.aadhaar_number = "123456789012"  # NEVER DO THIS!

# ✅ CORRECT
user.profile.aadhaar_last_4_digits = "9012"
user.profile.aadhaar_verified = True
```

### 2. Always Use HTTPS
```python
# In settings.py (production)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 3. Implement Rate Limiting
```python
# Using django-ratelimit
from ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='3/10m')
@login_required
def aadhaar_send_otp(request):
    # ... 
```

### 4. Log Without Sensitive Data
```python
# ❌ WRONG
logger.info(f"OTP sent for Aadhaar: {aadhaar_number}")

# ✅ CORRECT
logger.info(f"OTP sent (Transaction: {transaction_id})")
```

### 5. Clear Sensitive Data
```python
# Clear Aadhaar from memory
aadhaar_number = None

# Clear session after verification
request.session.pop('aadhaar_transaction_id', None)
```

### 6. Validate All Inputs
```python
# Always validate
if not aadhaar_number or len(aadhaar_number) != 12:
    return error()

if not otp or len(otp) != 6:
    return error()
```

---

## 🐛 Troubleshooting

### Issue 1: "Module 'requests' not found"
**Solution:** `pip install requests`

### Issue 2: "Invalid API credentials"
**Solution:** 
- Check environment variables
- Verify credentials in provider dashboard
- Ensure no extra spaces in credentials

### Issue 3: "OTP not received"
**Cause:** Mobile number not linked to Aadhaar
**Solution:** User must update mobile with UIDAI first

### Issue 4: "Session expired"
**Cause:** More than 10 minutes passed
**Solution:** User should request new OTP

### Issue 5: "Transaction ID not found"
**Cause:** Session cleared or lost
**Solution:** User should start verification again

### Issue 6: High API costs
**Solution:**
- Implement rate limiting
- Cache verification status
- Add OTP resend cooldown

---

## 📞 Support

### For Users
- Email: support@ecocommute.com
- Help: In-app help section
- FAQ: /aadhaar/faq

### For Developers
- Code: See inline comments
- API Docs: Provider-specific documentation
- Issues: GitHub issues / Internal ticketing

---

## 📄 License & Compliance

This implementation:
- ✅ Complies with Aadhaar Act 2016
- ✅ Complies with DPDP Act 2023
- ✅ Follows UIDAI guidelines
- ✅ Uses licensed API providers
- ✅ Implements data minimization
- ✅ Records user consent

**Last Updated:** January 30, 2026
**Version:** 1.0.0
**Status:** Production-Ready

---

*For questions or concerns, contact your compliance officer or legal team.*
