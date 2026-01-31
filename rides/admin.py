from django.contrib import admin
from .models import Ride, RidePassenger, UserProfile, LiveLocation


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'aadhaar_verified', 'aadhaar_masked', 'created_at']
    search_fields = ['user__email', 'phone_number', 'aadhaar_last_4_digits']
    list_filter = ['aadhaar_verified', 'aadhaar_consent_given', 'created_at']
    readonly_fields = ['aadhaar_verified_at', 'aadhaar_consent_timestamp', 'created_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'phone_number', 'created_at')
        }),
        ('Aadhaar Verification', {
            'fields': (
                'aadhaar_verified',
                'aadhaar_last_4_digits',
                'aadhaar_verified_at',
            ),
            'description': 'Aadhaar verification status. Full Aadhaar number is NEVER stored.'
        }),
        ('Consent & Compliance', {
            'fields': (
                'aadhaar_consent_given',
                'aadhaar_consent_timestamp',
            ),
            'description': 'User consent for Aadhaar verification (required for DPDP Act compliance)'
        }),
        ('Legacy Fields', {
            'fields': ('id_proof_number',),
            'classes': ('collapse',),
            'description': 'DEPRECATED - Do not use for Aadhaar storage'
        }),
    )


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ['from_location', 'to_location', 'ride_date', 'ride_time', 'creator', 'ride_status', 'seats_available', 'total_seats']
    list_filter = ['ride_date', 'vehicle_type', 'ride_status', 'driver_started', 'passenger_started', 'driver_ended', 'passenger_ended']
    search_fields = ['from_location', 'to_location', 'creator__email']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Route Information', {
            'fields': ('from_location', 'to_location', 'ride_date', 'ride_time', 'distance_km')
        }),
        ('Ride Details', {
            'fields': ('vehicle_type', 'total_seats', 'seats_available', 'creator', 'created_at')
        }),
        ('Ride Status', {
            'fields': ('ride_status',),
            'description': 'Current status of the ride'
        }),
        ('Start Confirmations', {
            'fields': ('driver_started', 'passenger_started'),
            'description': 'Both must confirm for ride to start'
        }),
        ('End Confirmations', {
            'fields': ('driver_ended', 'passenger_ended'),
            'description': 'Both must confirm for ride to complete'
        }),
    )


@admin.register(RidePassenger)
class RidePassengerAdmin(admin.ModelAdmin):
    list_display = ['user', 'ride', 'joined_at']
    list_filter = ['joined_at']
    search_fields = ['user__email', 'ride__from_location', 'ride__to_location']


@admin.register(LiveLocation)
class LiveLocationAdmin(admin.ModelAdmin):
    list_display = ['user', 'ride', 'latitude', 'longitude', 'is_sharing', 'updated_at']
    list_filter = ['is_sharing', 'updated_at']
    search_fields = ['user__email', 'ride__from_location', 'ride__to_location']
    readonly_fields = ['updated_at']
