from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime
from .models import Ride, RidePassenger, EMISSION_FACTORS, UserProfile, LiveLocation
from .aadhaar_service import get_aadhaar_service


def landing(request):
    """Landing page view."""
    return render(request, 'rides/landing.html')


def calculate_co2(distance_km, vehicle_type, occupants):
    """Calculate CO2 emissions for a ride."""
    factor = EMISSION_FACTORS.get(vehicle_type, EMISSION_FACTORS["car_petrol"])
    solo_kg = (distance_km * factor) / 1000
    occupants = max(occupants, 1)
    shared_kg = solo_kg / occupants
    saved_per_user = solo_kg - shared_kg
    return solo_kg, shared_kg, saved_per_user


def register(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        phone_number = request.POST.get('phone_number', '').strip()
        id_proof_number = request.POST.get('id_proof_number', '').strip()
        
        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return redirect('register')
        
        if not phone_number:
            messages.error(request, 'Phone number is required.')
            return redirect('register')
        
        # Validate phone number format
        import re
        cleaned_phone = ''.join(filter(str.isdigit, phone_number))
        if not re.match(r'^91\d{10}$', cleaned_phone):
            messages.error(request, 'Phone number must start with 91 and contain exactly 12 digits (e.g., 919876543210)')
            return redirect('register')
        
        if not id_proof_number:
            messages.error(request, 'ID proof number is required.')
            return redirect('register')
        
        if User.objects.filter(username=email).exists():
            messages.warning(request, 'Email already registered.')
            return redirect('register')
        
        # Create user (signal automatically creates UserProfile)
        user = User.objects.create_user(username=email, email=email, password=password)
        
        # Update the auto-created profile with user data
        profile = user.profile
        profile.phone_number = cleaned_phone
        profile.id_proof_number = id_proof_number
        profile.save()
        
        auth_login(request, user)
        messages.success(request, 'Welcome to EcoCommute!')
        return redirect('dashboard')
    
    return render(request, 'rides/register.html')


def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=email, password=password)
        if not user:
            messages.error(request, 'Invalid credentials.')
            return redirect('login')
        
        auth_login(request, user)
        messages.success(request, 'Logged in successfully.')
        
        # Redirect staff users to admin dashboard, regular users to normal dashboard
        if user.is_staff:
            return redirect('admin_dashboard')
        else:
            return redirect('dashboard')
    
    return render(request, 'rides/login.html')


@login_required
def user_logout(request):
    auth_logout(request)
    messages.info(request, 'Logged out.')
    return redirect('login')


@login_required
def dashboard(request):
    created_rides = Ride.objects.filter(creator=request.user).prefetch_related('passengers').order_by('ride_date', 'ride_time')
    joined_ride_passengers = RidePassenger.objects.filter(user=request.user).select_related('ride').order_by('ride__ride_date', 'ride__ride_time')
    
    total_saved = 0.0
    ride_summaries = []
    
    for ride in created_rides:
        solo, shared, saved = calculate_co2(ride.distance_km, ride.vehicle_type, ride.occupant_count)
        total_saved += saved
        ride_summaries.append({
            'ride': ride,
            'solo': solo,
            'shared': shared,
            'saved': saved,
            'role': 'Driver'
        })
    
    for rp in joined_ride_passengers:
        ride = rp.ride
        solo, shared, saved = calculate_co2(ride.distance_km, ride.vehicle_type, ride.occupant_count)
        total_saved += saved
        ride_summaries.append({
            'ride': ride,
            'solo': solo,
            'shared': shared,
            'saved': saved,
            'role': 'Passenger'
        })
    
    badge_earned = total_saved > 5
    
    context = {
        'created_rides': created_rides,
        'joined_ride_passengers': joined_ride_passengers,
        'total_saved': total_saved,
        'ride_summaries': ride_summaries,
        'badge_earned': badge_earned,
    }
    return render(request, 'rides/dashboard.html', context)


@login_required
def rides_list(request):
    # Start with all rides, sorted by newest first
    rides = Ride.objects.all().order_by('-created_at', 'ride_date', 'ride_time')
    
    # Get filter parameters from GET request
    from_location = request.GET.get('from_location', '').strip()
    to_location = request.GET.get('to_location', '').strip()
    
    # Apply filters if provided
    if from_location:
        rides = rides.filter(from_location__icontains=from_location)
    
    if to_location:
        rides = rides.filter(to_location__icontains=to_location)
    
    # Get joined ride IDs for current user
    joined_ids = set(RidePassenger.objects.filter(user=request.user).values_list('ride_id', flat=True))
    
    context = {
        'rides': rides,
        'joined_ids': joined_ids,
        'from_location': from_location,
        'to_location': to_location,
    }
    return render(request, 'rides/rides.html', context)


@login_required
def ride_detail(request, ride_id):
    """View ride details with passenger information."""
    ride = get_object_or_404(Ride, id=ride_id)
    passengers = ride.passengers.select_related('user', 'user__profile').all()
    is_creator = ride.creator == request.user
    has_joined = RidePassenger.objects.filter(ride=ride, user=request.user).exists()
    
    # Add WhatsApp messages and phone number for each passenger (for creator notifications)
    for passenger in passengers:
        # Get phone number from user profile (international format: 919876543210)
        # Clean phone number: remove all non-digit characters (spaces, dashes, brackets, etc.)
        phone = passenger.user.profile.phone_number if passenger.user.profile.phone_number else None
        if phone:
            # Remove all non-digit characters
            cleaned_phone = ''.join(filter(str.isdigit, phone))
            passenger.whatsapp_phone = cleaned_phone if cleaned_phone else None
        else:
            passenger.whatsapp_phone = None
        
        # Message 1: Start Ride Notification
        passenger.start_ride_message = (
            f"🚗 RIDE STARTED! 🚗\n\n"
            f"Hi {passenger.user.email}!\n\n"
            f"Your ride from {ride.from_location} to {ride.to_location} has started.\n\n"
            f"📌 Pickup Point: {passenger.pickup_point}\n"
            f"🕐 Expected Time: {ride.ride_time.strftime('%H:%M')}\n\n"
            f"I'm on my way to pick you up!\n\n"
            f"- {ride.creator.email}"
        )
        
        # Message 2: General Ride Details
        passenger.whatsapp_message = (
            f"Hi {passenger.user.email}! 🚗\n\n"
            f"Ride Details:\n"
            f"📍 Route: {ride.from_location} → {ride.to_location}\n"
            f"📅 Date: {ride.ride_date.strftime('%B %d, %Y')}\n"
            f"🕐 Time: {ride.ride_time.strftime('%H:%M')}\n"
            f"📌 Your Pickup Point: {passenger.pickup_point}\n\n"
            f"See you soon!\n"
            f"- {ride.creator.email}"
        )
    
    context = {
        'ride': ride,
        'passengers': passengers,
        'is_creator': is_creator,
        'has_joined': has_joined,
    }
    return render(request, 'rides/ride_detail.html', context)


@login_required
def create_ride(request):
    # AADHAAR VERIFICATION CHECK: Required to create rides
    if not request.user.profile.aadhaar_verified:
        messages.warning(request, 'Please verify your Aadhaar to create rides.')
        return redirect('aadhaar_verification_start')
    
    if request.method == 'POST':
        try:
            ride_date = datetime.strptime(request.POST['ride_date'], '%Y-%m-%d').date()
            ride_time = datetime.strptime(request.POST['ride_time'], '%H:%M').time()
            distance_km = float(request.POST['distance_km'])
            total_seats = int(request.POST['total_seats'])
        except (KeyError, ValueError):
            messages.error(request, 'Please provide valid ride details.')
            return redirect('create_ride')
        
        vehicle_type = request.POST.get('vehicle_type', 'car_petrol')
        from_location = request.POST.get('from_location', '').strip()
        to_location = request.POST.get('to_location', '').strip()
        vehicle_number = request.POST.get('vehicle_number', '').strip()
        
        if not vehicle_number:
            messages.error(request, 'Vehicle number is required.')
            return redirect('create_ride')
        
        if total_seats < 1:
            messages.warning(request, 'Total seats must be at least 1.')
            return redirect('create_ride')
        
        seats_available = max(total_seats - 1, 0)  # Driver uses one seat
        
        ride = Ride.objects.create(
            from_location=from_location,
            to_location=to_location,
            ride_date=ride_date,
            ride_time=ride_time,
            vehicle_type=vehicle_type,
            vehicle_number=vehicle_number,
            distance_km=distance_km,
            total_seats=total_seats,
            seats_available=seats_available,
            creator=request.user
        )
        messages.success(request, 'Ride created.')
        return redirect('rides_list')
    
    return render(request, 'rides/create_ride.html')


@login_required
def join_ride(request, ride_id):
    # AADHAAR VERIFICATION CHECK: Required to join rides
    if not request.user.profile.aadhaar_verified:
        messages.warning(request, 'Please verify your Aadhaar to join rides.')
        return redirect('aadhaar_verification_start')
    
    ride = get_object_or_404(Ride, id=ride_id)
    
    if request.method == 'POST':
        if ride.creator == request.user:
            messages.info(request, 'You are the driver for this ride.')
            return redirect('rides_list')
        
        if ride.seats_available <= 0:
            messages.warning(request, 'No seats available.')
            return redirect('rides_list')
        
        if RidePassenger.objects.filter(ride=ride, user=request.user).exists():
            messages.info(request, 'You have already joined this ride.')
            return redirect('rides_list')
        
        # Get pickup point data
        pickup_point = request.POST.get('pickup_point', '').strip()
        pickup_notes = request.POST.get('pickup_notes', '').strip()
        
        if not pickup_point:
            messages.error(request, 'Please enter a pickup point.')
            return render(request, 'rides/join_ride.html', {'ride': ride})
        
        ride.seats_available -= 1
        ride.save()
        
        RidePassenger.objects.create(
            user=request.user, 
            ride=ride,
            pickup_point=pickup_point,
            pickup_notes=pickup_notes
        )
        
        # Send email notification to ride creator
        try:
            email_subject = f"New Passenger Joined Your Ride - {ride.from_location} to {ride.to_location}"
            
            email_message = f"""Hello {ride.creator.email},

Great news! A passenger has joined your ride.

🚗 Ride Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Route: {ride.from_location} → {ride.to_location}
Date: {ride.ride_date}
Time: {ride.ride_time.strftime('%H:%M')}

👤 Passenger Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name/Email: {request.user.email}
Pickup Point: {pickup_point}
{f'Notes: {pickup_notes}' if pickup_notes else ''}

📊 Current Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Seats Available: {ride.seats_available}/{ride.total_seats}

Please check your dashboard for complete details:
http://127.0.0.1:8000/dashboard/

Thank you for choosing EcoCommute!
🌱 Together, we're making commuting more sustainable.

---
EcoCommute Team
"""
            
            send_mail(
                subject=email_subject,
                message=email_message,
                from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
                recipient_list=[ride.creator.email],
                fail_silently=True  # Don't break the join flow if email fails
            )
        except Exception as e:
            # Log error but don't fail the ride join
            pass
        
        messages.success(request, 'Joined ride successfully!')
        return redirect('rides_list')
    
    # GET request - show join form
    return render(request, 'rides/join_ride.html', {'ride': ride})


@login_required
def cancel_ride(request, ride_id):
    """Leave a joined ride from dashboard."""
    if request.method == 'POST':
        ride = get_object_or_404(Ride, id=ride_id)
        
        passenger = RidePassenger.objects.filter(ride=ride, user=request.user).first()
        if not passenger:
            messages.warning(request, 'You have not joined this ride.')
            return redirect('dashboard')
        
        passenger.delete()
        ride.seats_available += 1
        ride.save()
        
        messages.success(request, 'You have left the ride.')
        return redirect('dashboard')
    
    return redirect('dashboard')


@login_required
def leave_ride(request, ride_id):
    """Leave a joined ride from rides list."""
    if request.method == 'POST':
        ride = get_object_or_404(Ride, id=ride_id)
        
        passenger = RidePassenger.objects.filter(ride=ride, user=request.user).first()
        if not passenger:
            messages.warning(request, 'You have not joined this ride.')
            return redirect('rides_list')
        
        passenger.delete()
        ride.seats_available += 1
        ride.save()
        
        messages.success(request, 'You have left the ride.')
        return redirect('rides_list')
    
    return redirect('rides_list')


@login_required
def delete_ride(request, ride_id):
    """Delete a created ride."""
    if request.method == 'POST':
        ride = get_object_or_404(Ride, id=ride_id)
        
        # Only the creator can delete the ride
        if ride.creator != request.user:
            messages.error(request, 'You can only delete your own rides.')
            return redirect('dashboard')
        
        # Check if there are any passengers
        passenger_count = ride.passengers.count()
        if passenger_count > 0:
            messages.warning(request, f'Cannot delete ride. {passenger_count} passenger(s) have already joined.')
            return redirect('dashboard')
        
        ride.delete()
        messages.success(request, 'Ride deleted successfully.')
        return redirect('dashboard')
    
    return redirect('dashboard')


# ==================== TWO-SIDE CONFIRMATION VIEWS ====================

@login_required
@require_http_methods(["POST"])
def driver_start_ride(request, ride_id):
    """Driver confirms ride start."""
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Only the driver can start
    if ride.creator != request.user:
        return JsonResponse({'error': 'Only the driver can start the ride'}, status=403)
    
    # Can't start if already started or completed
    if ride.ride_status != 'created':
        return JsonResponse({'error': 'Ride has already been started or completed'}, status=400)
    
    # Can't start if already confirmed
    if ride.driver_started:
        return JsonResponse({'error': 'You have already confirmed the start'}, status=400)
    
    # Set driver confirmation
    ride.driver_started = True
    ride.save()
    
    # Check and update status
    status_changed = ride.check_and_update_status()
    
    if status_changed == 'started':
        messages.success(request, '🚗 Ride started! Location sharing is now enabled.')
    else:
        messages.info(request, '✅ You confirmed the start. Waiting for passenger confirmation.')
    
    return redirect('ride_detail', ride_id=ride.id)


@login_required
@require_http_methods(["POST"])
def passenger_confirm_start(request, ride_id):
    """Passenger confirms ride start."""
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Check if user is a passenger
    passenger = RidePassenger.objects.filter(ride=ride, user=request.user).first()
    if not passenger:
        return JsonResponse({'error': 'Only passengers can confirm the start'}, status=403)
    
    # Can't start if already started or completed
    if ride.ride_status != 'created':
        return JsonResponse({'error': 'Ride has already been started or completed'}, status=400)
    
    # Can't start if already confirmed
    if ride.passenger_started:
        return JsonResponse({'error': 'You have already confirmed the start'}, status=400)
    
    # Set passenger confirmation
    ride.passenger_started = True
    ride.save()
    
    # Check and update status
    status_changed = ride.check_and_update_status()
    
    if status_changed == 'started':
        messages.success(request, '🚗 Ride started! You can now share your location.')
    else:
        messages.info(request, '✅ You confirmed the start. Waiting for driver confirmation.')
    
    return redirect('ride_detail', ride_id=ride.id)


@login_required
@require_http_methods(["POST"])
def driver_end_ride(request, ride_id):
    """Driver confirms ride end."""
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Only the driver can end
    if ride.creator != request.user:
        return JsonResponse({'error': 'Only the driver can end the ride'}, status=403)
    
    # Can only end started rides
    if ride.ride_status != 'started':
        return JsonResponse({'error': 'Ride must be started before it can be ended'}, status=400)
    
    # Can't end if already confirmed
    if ride.driver_ended:
        return JsonResponse({'error': 'You have already confirmed the end'}, status=400)
    
    # Set driver confirmation
    ride.driver_ended = True
    ride.save()
    
    # Check and update status
    status_changed = ride.check_and_update_status()
    
    if status_changed == 'completed':
        messages.success(request, '🏁 Ride completed! Thank you for carpooling.')
    else:
        messages.info(request, '✅ You confirmed arrival. Waiting for passenger confirmation.')
    
    return redirect('ride_detail', ride_id=ride.id)


@login_required
@require_http_methods(["POST"])
def passenger_confirm_arrival(request, ride_id):
    """Passenger confirms arrival (ride end)."""
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Check if user is a passenger
    passenger = RidePassenger.objects.filter(ride=ride, user=request.user).first()
    if not passenger:
        return JsonResponse({'error': 'Only passengers can confirm arrival'}, status=403)
    
    # Can only end started rides
    if ride.ride_status != 'started':
        return JsonResponse({'error': 'Ride must be started before it can be ended'}, status=400)
    
    # Can't end if already confirmed
    if ride.passenger_ended:
        return JsonResponse({'error': 'You have already confirmed arrival'}, status=400)
    
    # Set passenger confirmation
    ride.passenger_ended = True
    ride.save()
    
    # Check and update status
    status_changed = ride.check_and_update_status()
    
    if status_changed == 'completed':
        messages.success(request, '🏁 Ride completed! Thank you for carpooling.')
    else:
        messages.info(request, '✅ You confirmed arrival. Waiting for driver confirmation.')
    
    return redirect('ride_detail', ride_id=ride.id)


# ==================== LIVE LOCATION TRACKING VIEWS ====================

@login_required
@require_http_methods(["POST"])
def update_location(request):
    """
    Update or create live location for the authenticated user.
    User must be a passenger in an active ride to share location.
    IMPORTANT: Location sharing requires explicit user consent.
    """
    try:
        # Get location data from POST request
        ride_id = request.POST.get('ride_id')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        is_sharing = request.POST.get('is_sharing', 'false').lower() == 'true'
        
        # Validate input
        if not all([ride_id, latitude, longitude]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return JsonResponse({'error': 'Invalid coordinates'}, status=400)
        
        # Verify ride exists and user is a passenger
        ride = get_object_or_404(Ride, id=ride_id)
        if not RidePassenger.objects.filter(ride=ride, user=request.user).exists():
            return JsonResponse({'error': 'User is not a passenger in this ride'}, status=403)
        
        # Update or create location (OneToOne ensures only one record per user)
        location, created = LiveLocation.objects.update_or_create(
            user=request.user,
            defaults={
                'ride': ride,
                'latitude': latitude,
                'longitude': longitude,
                'is_sharing': is_sharing,
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Location updated successfully',
            'latitude': location.latitude,
            'longitude': location.longitude,
            'updated_at': location.updated_at.isoformat(),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_location(request, user_id, ride_id):
    """
    Get live location of a specific user in a ride.
    Only the ride creator can view passenger locations.
    Returns 404 if location sharing is disabled or location doesn't exist.
    """
    try:
        # Verify the ride exists and requester is the creator
        ride = get_object_or_404(Ride, id=ride_id)
        if ride.creator != request.user:
            return JsonResponse({'error': 'Only ride creator can view locations'}, status=403)
        
        # Verify the target user is a passenger in this ride
        passenger_user = get_object_or_404(User, id=user_id)
        if not RidePassenger.objects.filter(ride=ride, user=passenger_user).exists():
            return JsonResponse({'error': 'User is not a passenger in this ride'}, status=404)
        
        # Get live location if sharing is enabled
        try:
            location = LiveLocation.objects.get(
                user=passenger_user,
                ride=ride,
                is_sharing=True  # Only return if user has consented to share
            )
            
            return JsonResponse({
                'success': True,
                'user_id': user_id,
                'user_email': passenger_user.email,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'updated_at': location.updated_at.isoformat(),
            })
            
        except LiveLocation.DoesNotExist:
            return JsonResponse({
                'error': 'Location not available or sharing disabled'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def stop_location_sharing(request):
    """
    Stop location sharing for the authenticated user.
    Deletes the live location record.
    """
    try:
        # Delete the user's live location
        deleted_count, _ = LiveLocation.objects.filter(user=request.user).delete()
        
        if deleted_count > 0:
            return JsonResponse({
                'success': True,
                'message': 'Location sharing stopped'
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'No active location sharing'
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def track_ride(request, ride_id):
    """
    View for ride creator to track live locations of all passengers.
    Displays a map with real-time location updates.
    """
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Only ride creator can access tracking
    if ride.creator != request.user:
        messages.error(request, 'Only ride creator can track passengers')
        return redirect('ride_detail', ride_id=ride_id)
    
    # Get all passengers in this ride
    passengers = RidePassenger.objects.filter(ride=ride).select_related('user')
    
    context = {
        'ride': ride,
        'passengers': passengers,
    }
    return render(request, 'rides/track_ride.html', context)


@login_required
def share_location_view(request, ride_id):
    """
    View for passengers to share their live location during a ride.
    Provides UI to start/stop location sharing.
    """
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Verify user is a passenger in this ride
    if not RidePassenger.objects.filter(ride=ride, user=request.user).exists():
        messages.error(request, 'You are not a passenger in this ride')
        return redirect('ride_detail', ride_id=ride_id)
    
    # Check if user is already sharing location
    is_currently_sharing = LiveLocation.objects.filter(
        user=request.user,
        ride=ride,
        is_sharing=True
    ).exists()
    
    context = {
        'ride': ride,
        'is_currently_sharing': is_currently_sharing,
    }
    return render(request, 'rides/share_location.html', context)


# ==================== AADHAAR VERIFICATION VIEWS ====================

@login_required
def aadhaar_verification_start(request):
    """
    Initial Aadhaar verification page.
    User enters Aadhaar number and gives consent.
    
    COMPLIANCE:
    - Explicit consent checkbox required
    - Clear privacy notice displayed
    - Aadhaar number submitted only to backend (HTTPS)
    - No client-side storage or logging
    """
    # Get or create profile (safety check for existing users)
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Redirect if already verified
    if profile.aadhaar_verified:
        messages.info(request, 'Your Aadhaar is already verified.')
        return redirect('dashboard')
    
    context = {
        'aadhaar_masked': profile.aadhaar_masked,
        'already_verified': profile.aadhaar_verified,
    }
    return render(request, 'rides/aadhaar_verify_start.html', context)


@login_required
@require_http_methods(["POST"])
def aadhaar_send_otp(request):
    """
    Send OTP to Aadhaar-linked mobile number.
    
    SECURITY & COMPLIANCE:
    - Backend-only processing (never expose Aadhaar to frontend)
    - Aadhaar number NOT stored in database
    - Aadhaar number NOT logged anywhere
    - Only last 4 digits stored after verification
    - Explicit consent required before processing
    
    Flow:
    1. Validate consent checkbox
    2. Validate Aadhaar format
    3. Call licensed API provider
    4. Store transaction ID in session (not database)
    5. Return success/failure to user
    """
    try:
        # Get form data
        aadhaar_number = request.POST.get('aadhaar_number', '').strip()
        consent_given = request.POST.get('consent') == 'on'
        
        # MANDATORY: Check explicit consent
        if not consent_given:
            messages.error(request, 'You must give consent to verify your Aadhaar.')
            return redirect('aadhaar_verification_start')
        
        # Validate Aadhaar number format
        if not aadhaar_number:
            messages.error(request, 'Please enter your Aadhaar number.')
            return redirect('aadhaar_verification_start')
        
        # Record consent
        profile = request.user.profile
        profile.aadhaar_consent_given = True
        profile.aadhaar_consent_timestamp = timezone.now()
        profile.save()
        
        # Get Aadhaar verification service
        aadhaar_service = get_aadhaar_service()
        
        # Send OTP via licensed provider
        # NOTE: Aadhaar number is passed to provider, NEVER stored locally
        success, message, transaction_id = aadhaar_service.send_otp(aadhaar_number)
        
        if success:
            # Store transaction ID in session (NOT database)
            # Also store last 4 digits temporarily for OTP verification
            request.session['aadhaar_transaction_id'] = transaction_id
            request.session['aadhaar_last_4'] = aadhaar_service.get_last_4_digits(aadhaar_number)
            request.session['aadhaar_otp_sent_at'] = timezone.now().isoformat()
            
            # Clear the Aadhaar number from memory immediately
            aadhaar_number = None
            
            messages.success(request, message)
            return redirect('aadhaar_verify_otp')
        else:
            # Clear the Aadhaar number from memory
            aadhaar_number = None
            
            messages.error(request, f'Failed to send OTP: {message}')
            return redirect('aadhaar_verification_start')
            
    except Exception as e:
        # Log error without sensitive data
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in aadhaar_send_otp: {str(e)}")
        
        messages.error(request, 'System error. Please try again later.')
        return redirect('aadhaar_verification_start')


@login_required
def aadhaar_verify_otp(request):
    """
    OTP verification page.
    User enters 6-digit OTP received on their mobile.
    
    SECURITY:
    - Transaction ID stored in session (not exposed to user)
    - OTP validated on backend only
    - Rate limiting recommended (prevent brute force)
    - Session timeout after 10 minutes
    """
    # Check if OTP was sent
    transaction_id = request.session.get('aadhaar_transaction_id')
    if not transaction_id:
        messages.warning(request, 'Please start Aadhaar verification first.')
        return redirect('aadhaar_verification_start')
    
    # Check session timeout (10 minutes)
    otp_sent_at = request.session.get('aadhaar_otp_sent_at')
    if otp_sent_at:
        from datetime import timedelta
        sent_time = datetime.fromisoformat(otp_sent_at)
        if timezone.now() - sent_time > timedelta(minutes=10):
            # Clear session
            request.session.pop('aadhaar_transaction_id', None)
            request.session.pop('aadhaar_last_4', None)
            request.session.pop('aadhaar_otp_sent_at', None)
            
            messages.warning(request, 'OTP expired. Please request a new OTP.')
            return redirect('aadhaar_verification_start')
    
    context = {
        'transaction_id': transaction_id,  # For display only (masked)
    }
    return render(request, 'rides/aadhaar_verify_otp.html', context)


@login_required
@require_http_methods(["POST"])
def aadhaar_submit_otp(request):
    """
    Submit and verify OTP.
    
    COMPLIANCE:
    - OTP verified with licensed provider
    - On success: Mark user as verified, store last 4 digits
    - On failure: Show error, allow retry
    - Full Aadhaar number NEVER stored
    
    Flow:
    1. Get OTP from form
    2. Get transaction ID from session
    3. Call provider's verify_otp API
    4. Update UserProfile with verification status
    5. Clear session data
    6. Grant access to ride features
    """
    try:
        # Get OTP from form
        otp = request.POST.get('otp', '').strip()
        
        if not otp:
            messages.error(request, 'Please enter the OTP.')
            return redirect('aadhaar_verify_otp')
        
        # Get transaction ID from session
        transaction_id = request.session.get('aadhaar_transaction_id')
        if not transaction_id:
            messages.warning(request, 'Session expired. Please start again.')
            return redirect('aadhaar_verification_start')
        
        # Get last 4 digits from session
        last_4_digits = request.session.get('aadhaar_last_4')
        
        # Get Aadhaar verification service
        aadhaar_service = get_aadhaar_service()
        
        # Verify OTP with provider
        success, message, verified_data = aadhaar_service.verify_otp(transaction_id, otp)
        
        if success:
            # Update UserProfile - Mark as verified
            profile = request.user.profile
            profile.aadhaar_verified = True
            profile.aadhaar_verified_at = timezone.now()
            profile.aadhaar_last_4_digits = last_4_digits
            profile.save()
            
            # Clear session data (security best practice)
            request.session.pop('aadhaar_transaction_id', None)
            request.session.pop('aadhaar_last_4', None)
            request.session.pop('aadhaar_otp_sent_at', None)
            
            # Show success message with verified name (optional)
            if verified_data and verified_data.get('full_name'):
                messages.success(
                    request,
                    f'Aadhaar verified successfully! Welcome, {verified_data["full_name"]}. '
                    f'You can now create and join rides.'
                )
            else:
                messages.success(
                    request,
                    'Aadhaar verified successfully! You can now create and join rides.'
                )
            
            return redirect('dashboard')
        else:
            # Verification failed
            messages.error(request, f'Verification failed: {message}')
            return redirect('aadhaar_verify_otp')
            
    except Exception as e:
        # Log error without sensitive data
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in aadhaar_submit_otp: {str(e)}")
        
        messages.error(request, 'System error. Please try again later.')
        return redirect('aadhaar_verify_otp')


@login_required
def aadhaar_resend_otp(request):
    """
    Resend OTP if user didn't receive it.
    
    SECURITY:
    - Rate limiting recommended (max 3 attempts per 10 minutes)
    - Clears old transaction ID
    - Creates new transaction
    """
    # Clear old session data
    request.session.pop('aadhaar_transaction_id', None)
    request.session.pop('aadhaar_otp_sent_at', None)
    
    messages.info(request, 'Please enter your Aadhaar number again to resend OTP.')
    return redirect('aadhaar_verification_start')


# ============================================================================
# CUSTOM ADMIN DASHBOARD VIEWS
# ============================================================================

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q


@staff_member_required
def admin_dashboard(request):
    """
    Main admin dashboard showing key statistics.
    Accessible only to staff users (is_staff=True).
    """
    # Get statistics
    total_users = User.objects.count()
    total_rides = Ride.objects.count()
    active_rides = Ride.objects.filter(
        ride_status__in=['created', 'started']
    ).count()
    completed_rides = Ride.objects.filter(ride_status='completed').count()
    
    # Get recent activities
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_rides = Ride.objects.select_related('creator').order_by('-created_at')[:5]
    
    context = {
        'total_users': total_users,
        'total_rides': total_rides,
        'active_rides': active_rides,
        'completed_rides': completed_rides,
        'recent_users': recent_users,
        'recent_rides': recent_rides,
    }
    
    return render(request, 'rides/admin/dashboard.html', context)


@staff_member_required
def admin_users_list(request):
    """
    List all users with search and filter capabilities.
    """
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    users = User.objects.select_related('profile').all()
    
    # Apply search
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(profile__phone_number__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'staff':
        users = users.filter(is_staff=True)
    elif status_filter == 'verified':
        users = users.filter(profile__aadhaar_verified=True)
    
    users = users.order_by('-date_joined')
    
    context = {
        'users': users,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'rides/admin/users_list.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_toggle_user_status(request, user_id):
    """
    Activate or deactivate a user account.
    """
    user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deactivation
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('admin_users_list')
    
    # Toggle status
    user.is_active = not user.is_active
    user.save()
    
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.email} has been {status}.')
    
    return redirect('admin_users_list')


@staff_member_required
def admin_rides_list(request):
    """
    List all rides with search and filter capabilities.
    """
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    rides = Ride.objects.select_related('creator').prefetch_related('passengers').all()
    
    # Apply search
    if search_query:
        rides = rides.filter(
            Q(from_location__icontains=search_query) |
            Q(to_location__icontains=search_query) |
            Q(vehicle_number__icontains=search_query) |
            Q(creator__email__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        rides = rides.filter(ride_status=status_filter)
    
    rides = rides.order_by('-created_at')
    
    context = {
        'rides': rides,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'rides/admin/rides_list.html', context)


@staff_member_required
def admin_ride_detail(request, ride_id):
    """
    View detailed information about a specific ride.
    """
    ride = get_object_or_404(
        Ride.objects.select_related('creator').prefetch_related(
            'passengers__user__profile'
        ),
        id=ride_id
    )
    
    passengers = RidePassenger.objects.filter(ride=ride).select_related('user__profile')
    
    context = {
        'ride': ride,
        'passengers': passengers,
    }
    
    return render(request, 'rides/admin/ride_detail.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_cancel_ride(request, ride_id):
    """
    Cancel an active ride (admin only).
    Only cancels if ride is not completed.
    """
    ride = get_object_or_404(Ride, id=ride_id)
    
    if ride.ride_status == 'completed':
        messages.error(request, 'Cannot cancel a completed ride.')
    else:
        # Set ride status to a cancelled state
        # Since the model doesn't have 'cancelled' status, we'll delete it
        # Or you can add a 'cancelled' status to the model
        ride_info = f"{ride.from_location} to {ride.to_location}"
        ride.delete()
        messages.success(request, f'Ride "{ride_info}" has been cancelled.')
    
    return redirect('admin_rides_list')


@staff_member_required
def admin_trips_ongoing(request):
    """
    Monitor ongoing rides (created or started status).
    """
    ongoing_rides = Ride.objects.filter(
        ride_status__in=['created', 'started']
    ).select_related('creator').prefetch_related('passengers').order_by('ride_date', 'ride_time')
    
    context = {
        'rides': ongoing_rides,
    }
    
    return render(request, 'rides/admin/trips_ongoing.html', context)


@staff_member_required
def admin_trips_completed(request):
    """
    View completed rides (read-only).
    """
    completed_rides = Ride.objects.filter(
        ride_status='completed'
    ).select_related('creator').prefetch_related('passengers').order_by('-created_at')
    
    context = {
        'rides': completed_rides,
    }
    
    return render(request, 'rides/admin/trips_completed.html', context)
