from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime


EMISSION_FACTORS = {
    "car_petrol": 120,  # g CO2 per km
    "bike": 0,
}


class UserProfile(models.Model):
    """
    User profile with Aadhaar verification support.
    
    COMPLIANCE NOTES:
    - Full Aadhaar number is NEVER stored (violates Aadhaar Act)
    - Only last 4 digits stored (masked format: XXXX-XXXX-1234)
    - Verification status stored as boolean flag
    - Consent timestamp recorded for audit trail
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(
        max_length=12,
        help_text="Phone number must start with 91 and be exactly 12 digits (e.g., 919876543210)"
    )
    
    # DEPRECATED: Legacy field for backward compatibility
    # DO NOT use this for Aadhaar storage
    id_proof_number = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="DEPRECATED - Use aadhaar fields instead"
    )
    
    # Aadhaar Verification Fields (Compliant with Aadhaar Act)
    aadhaar_verified = models.BooleanField(
        default=False,
        help_text="Whether Aadhaar has been verified via OTP"
    )
    aadhaar_last_4_digits = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        help_text="Last 4 digits of Aadhaar (for display only, e.g., XXXX-XXXX-1234)"
    )
    aadhaar_consent_given = models.BooleanField(
        default=False,
        help_text="User gave explicit consent to verify Aadhaar"
    )
    aadhaar_consent_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user gave consent for Aadhaar verification"
    )
    aadhaar_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When Aadhaar was successfully verified"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - Profile"
    
    @property
    def aadhaar_masked(self):
        """Return masked Aadhaar for display (XXXX-XXXX-1234)"""
        if self.aadhaar_last_4_digits:
            return f"XXXX-XXXX-{self.aadhaar_last_4_digits}"
        return None
    
    def can_create_or_join_rides(self):
        """Check if user can create or join rides (requires Aadhaar verification)"""
        return self.aadhaar_verified
    
    def clean(self):
        """Validate phone number format"""
        import re
        from django.core.exceptions import ValidationError
        
        if self.phone_number:
            # Remove any non-digit characters
            cleaned = ''.join(filter(str.isdigit, self.phone_number))
            
            # Validate format: must start with 91 and be exactly 12 digits
            if not re.match(r'^91\d{10}$', cleaned):
                raise ValidationError({
                    'phone_number': 'Phone number must start with 91 and contain exactly 12 digits (e.g., 919876543210)'
                })
            
            # Store the cleaned version
            self.phone_number = cleaned
    
    def save(self, *args, **kwargs):
        """Override save to call clean before saving"""
        # Only validate if phone number is being changed (not on every save)
        if self.pk:  # If this is an update (not a new record)
            try:
                old_instance = UserProfile.objects.get(pk=self.pk)
                # Only validate if phone number has changed
                if old_instance.phone_number != self.phone_number:
                    self.clean()
            except UserProfile.DoesNotExist:
                self.clean()
        else:  # New record
            self.clean()
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    # Use get_or_create to handle cases where profile doesn't exist
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)


class Ride(models.Model):
    VEHICLE_CHOICES = [
        ('car_petrol', 'Petrol Car'),
        ('bike', 'Bike'),
    ]
    
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('started', 'Started'),
        ('completed', 'Completed'),
    ]
    
    from_location = models.CharField(max_length=120)
    to_location = models.CharField(max_length=120)
    ride_date = models.DateField()
    ride_time = models.TimeField()
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_CHOICES, default='car_petrol')
    vehicle_number = models.CharField(max_length=15, default='UNKNOWN', help_text='Vehicle registration number (e.g., KL07AB1234)')
    distance_km = models.FloatField()
    total_seats = models.IntegerField()
    seats_available = models.IntegerField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides_created')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Two-side confirmation fields for ride start
    driver_started = models.BooleanField(default=False)
    passenger_started = models.BooleanField(default=False)
    
    # Two-side confirmation fields for ride end
    driver_ended = models.BooleanField(default=False)
    passenger_ended = models.BooleanField(default=False)
    
    # Ride status
    ride_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created'
    )

    class Meta:
        ordering = ['ride_date', 'ride_time']

    def __str__(self):
        return f"{self.from_location} to {self.to_location} on {self.ride_date}"

    def save(self, *args, **kwargs):
        """Override save to convert vehicle_number to uppercase"""
        if self.vehicle_number:
            self.vehicle_number = self.vehicle_number.upper()
        super().save(*args, **kwargs)
    
    @property
    def occupant_count(self):
        """Driver counts as one occupant; each filled seat removes one available slot."""
        used_seats = self.total_seats - self.seats_available
        return max(used_seats, 1)
    
    def check_and_update_status(self):
        """Check confirmations and update ride status automatically."""
        # Check if ride should be started
        if self.driver_started and self.passenger_started and self.ride_status == 'created':
            self.ride_status = 'started'
            self.save()
            return 'started'
        
        # Check if ride should be completed
        if self.driver_ended and self.passenger_ended and self.ride_status == 'started':
            self.ride_status = 'completed'
            self.save()
            return 'completed'
        
        return None


class RidePassenger(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides_joined')
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='passengers')
    pickup_point = models.CharField(max_length=200, blank=True, help_text="Pickup location")
    pickup_notes = models.TextField(blank=True, help_text="Landmark, timing, or other notes")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'ride']
        verbose_name_plural = 'Ride Passengers'

    def __str__(self):
        return f"{self.user.email} joined {self.ride}"


class LiveLocation(models.Model):
    """
    Stores ONLY the latest location for a user during an active ride.
    Location sharing is opt-in and only active during the ride.
    Data is automatically deleted when ride ends.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='live_location')
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='live_locations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)
    is_sharing = models.BooleanField(default=False)  # User consent flag

    class Meta:
        verbose_name = 'Live Location'
        verbose_name_plural = 'Live Locations'

    def __str__(self):
        return f"{self.user.email} - {self.ride} (Last update: {self.updated_at})"
