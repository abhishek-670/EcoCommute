from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('rides/', views.rides_list, name='rides_list'),
    path('rides/create/', views.create_ride, name='create_ride'),
    path('rides/<int:ride_id>/', views.ride_detail, name='ride_detail'),
    path('rides/join/<int:ride_id>/', views.join_ride, name='join_ride'),
    path('rides/cancel/<int:ride_id>/', views.cancel_ride, name='cancel_ride'),
    path('rides/leave/<int:ride_id>/', views.leave_ride, name='leave_ride'),
    path('rides/delete/<int:ride_id>/', views.delete_ride, name='delete_ride'),
    
    # Two-Side Confirmation URLs
    path('rides/<int:ride_id>/driver-start/', views.driver_start_ride, name='driver_start_ride'),
    path('rides/<int:ride_id>/passenger-confirm-start/', views.passenger_confirm_start, name='passenger_confirm_start'),
    path('rides/<int:ride_id>/driver-end/', views.driver_end_ride, name='driver_end_ride'),
    path('rides/<int:ride_id>/passenger-confirm-arrival/', views.passenger_confirm_arrival, name='passenger_confirm_arrival'),
    
    # Live Location Tracking URLs
    path('location/update/', views.update_location, name='update_location'),
    path('location/get/<int:user_id>/<int:ride_id>/', views.get_location, name='get_location'),
    path('location/stop/', views.stop_location_sharing, name='stop_location_sharing'),
    path('rides/<int:ride_id>/track/', views.track_ride, name='track_ride'),
    path('rides/<int:ride_id>/share-location/', views.share_location_view, name='share_location_view'),
    
    # Aadhaar Verification URLs
    path('aadhaar/verify/', views.aadhaar_verification_start, name='aadhaar_verification_start'),
    path('aadhaar/send-otp/', views.aadhaar_send_otp, name='aadhaar_send_otp'),
    path('aadhaar/verify-otp/', views.aadhaar_verify_otp, name='aadhaar_verify_otp'),
    path('aadhaar/submit-otp/', views.aadhaar_submit_otp, name='aadhaar_submit_otp'),
    path('aadhaar/resend-otp/', views.aadhaar_resend_otp, name='aadhaar_resend_otp'),
    
    # Custom Admin Dashboard URLs (NOT Django default admin)
    path('custom-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('custom-admin/users/', views.admin_users_list, name='admin_users_list'),
    path('custom-admin/users/<int:user_id>/toggle-status/', views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('custom-admin/rides/', views.admin_rides_list, name='admin_rides_list'),
    path('custom-admin/rides/<int:ride_id>/', views.admin_ride_detail, name='admin_ride_detail'),
    path('custom-admin/rides/<int:ride_id>/cancel/', views.admin_cancel_ride, name='admin_cancel_ride'),
    path('custom-admin/trips/ongoing/', views.admin_trips_ongoing, name='admin_trips_ongoing'),
    path('custom-admin/trips/completed/', views.admin_trips_completed, name='admin_trips_completed'),
]
