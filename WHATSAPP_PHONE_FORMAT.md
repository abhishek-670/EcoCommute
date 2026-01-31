# 📱 WhatsApp Phone Number Format

## ⚠️ CRITICAL: Phone Number Storage Requirements

### **Format Rules (MANDATORY)**

Phone numbers MUST be stored in **international format** with:
- ✅ Country code included (e.g., 91 for India)
- ✅ Digits only (no special characters)
- ❌ NO plus sign (+)
- ❌ NO spaces
- ❌ NO hyphens (-)
- ❌ NO parentheses ()

### **Correct Examples**

| Country | Format | Example |
|---------|--------|---------|
| India 🇮🇳 | `91XXXXXXXXXX` | `919876543210` |
| USA 🇺🇸 | `1XXXXXXXXXX` | `14155551234` |
| UK 🇬🇧 | `44XXXXXXXXXX` | `447700900123` |
| UAE 🇦🇪 | `971XXXXXXXXX` | `971501234567` |

### **Incorrect Examples**

❌ `+919876543210` (has + sign)
❌ `+91 9876543210` (has + and space)
❌ `91-9876543210` (has hyphen)
❌ `9876543210` (missing country code)
❌ `(91) 9876543210` (has parentheses)

---

## 🔧 Database Field: UserProfile.phone_number

The `phone_number` field in `UserProfile` model stores phone numbers for WhatsApp integration.

### **Current Storage**
```python
# rides/models.py
class UserProfile(models.Model):
    phone_number = models.CharField(max_length=15, blank=True)
```

### **Validation Needed**

To ensure proper format, add validation in the registration form:

```python
# rides/views.py - register() function
def register(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        
        # Remove any non-digit characters
        phone_number = ''.join(filter(str.isdigit, phone_number))
        
        # Validate length (10-15 digits)
        if not (10 <= len(phone_number) <= 15):
            messages.error(request, 'Phone number must be 10-15 digits.')
            return redirect('register')
        
        # If starts with 0, remove it (common in India)
        if phone_number.startswith('0'):
            phone_number = phone_number[1:]
        
        # If doesn't start with country code, add 91 (India)
        if len(phone_number) == 10:
            phone_number = '91' + phone_number
        
        # Save to database
        profile.phone_number = phone_number
```

---

## 📲 WhatsApp Integration

### **How It Works**

The system uses WhatsApp's `wa.me` API:

```
https://wa.me/{phone_number}?text={message}
```

### **Implementation in ride_detail.html**

```html
<!-- Start Ride Button -->
<a href="https://wa.me/{{ passenger.whatsapp_phone }}?text={{ passenger.start_ride_message|urlencode }}" 
   target="_blank">
    Start Ride – Notify
</a>
```

### **Implementation in views.py**

```python
# Get phone number from user profile
passenger.whatsapp_phone = passenger.user.profile.phone_number

# Example: "919876543210"
```

---

## 🧪 Testing

### **Test Phone Numbers**

For testing, you can use your own WhatsApp number:

1. **Find your number in international format:**
   - India: Remove leading 0, add 91
   - Example: `9876543210` → `919876543210`

2. **Update your profile:**
   ```python
   python manage.py shell
   ```
   ```python
   from django.contrib.auth.models import User
   
   user = User.objects.get(email='your@email.com')
   user.profile.phone_number = '919876543210'  # Your number
   user.profile.save()
   ```

3. **Test the button:**
   - Create a ride
   - Have someone join
   - Click "Start Ride – Notify"
   - WhatsApp should open with your number

---

## 🚀 Current Features

### **Two WhatsApp Buttons**

1. **Start Ride – Notify Passenger** (Gradient Green)
   - Opens WhatsApp to passenger's number
   - Prefills: "🚗 RIDE STARTED! 🚗"
   - Includes pickup point and ETA
   - Creator must manually send

2. **Send Details** (Solid Green)
   - Opens WhatsApp to passenger's number
   - Prefills: Complete ride details
   - Includes route, date, time, pickup
   - Creator must manually send

### **Security & Privacy**

- ✅ Buttons visible only to ride creator
- ✅ Phone numbers stored in backend only
- ✅ No auto-sending (user-initiated)
- ✅ WhatsApp handles actual message delivery
- ✅ No WhatsApp API required (uses wa.me links)

---

## 📝 User Instructions

### **For Users Registering:**

When you register, enter your phone number in one of these formats:
- With country code: `919876543210`
- Without country code: `9876543210` (system adds 91)
- With spaces: `91 9876 543210` (system removes spaces)

The system will automatically convert it to the correct format.

### **For Ride Creators:**

1. Go to ride details page
2. See list of passengers who joined
3. Each passenger has two buttons:
   - **"Start Ride – Notify"** - Use when starting the ride
   - **"Send Details"** - Use to send general ride info
4. Click button → WhatsApp opens
5. Review/edit message if needed
6. Click WhatsApp's Send button

---

## 🔍 Troubleshooting

### **Problem: WhatsApp opens but no number**

**Cause:** Phone number not in correct format

**Solution:** Update user's phone number:
```python
user.profile.phone_number = '919876543210'  # Correct format
user.profile.save()
```

### **Problem: WhatsApp says "Invalid number"**

**Cause:** Incorrect country code or missing digits

**Solution:** Verify:
- India: Must be 12 digits (91 + 10 digits)
- USA: Must be 11 digits (1 + 10 digits)
- Check country code is correct

### **Problem: Button doesn't open WhatsApp**

**Cause:** Browser or WhatsApp not installed

**Solution:**
- Desktop: Install WhatsApp Desktop or use WhatsApp Web
- Mobile: Install WhatsApp app
- Check browser allows opening external apps

---

## 📊 Summary

✅ **Phone Format:** Digits only, with country code (e.g., `919876543210`)
✅ **Two Buttons:** Start Ride notification + General details
✅ **Creator Only:** Buttons visible only to ride creator
✅ **Manual Send:** User must click send in WhatsApp
✅ **No API Needed:** Uses free wa.me links

**Status:** ✅ Feature fully implemented and ready to use!
