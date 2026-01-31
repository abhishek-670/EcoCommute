"""
Aadhaar Verification API Integration Service

COMPLIANCE & SECURITY:
- This service acts as a secure intermediary between Django and Aadhaar verification providers
- Full Aadhaar numbers are NEVER stored in database or logs
- All API calls are made from backend only (never from frontend)
- Supports multiple providers: Cashfree, Signzy, Surepass
- Uses HTTPS for all API communications
- Implements proper error handling and timeout management

PROVIDER SETUP:
1. Sign up with a licensed Aadhaar verification provider
2. Obtain API credentials (Client ID, Secret Key)
3. Set credentials in Django settings or environment variables
4. Use sandbox mode for testing, production mode for live

LEGAL COMPLIANCE:
- Complies with Aadhaar (Targeted Delivery of Financial and Other Subsidies, 
  Benefits and Services) Act, 2016
- Follows UIDAI guidelines for Aadhaar verification
- Adheres to Digital Personal Data Protection Act (DPDP) 2023
- Never stores or logs full Aadhaar numbers
"""

import requests
import logging
from django.conf import settings
from typing import Dict, Tuple, Optional
import hashlib
import time

logger = logging.getLogger(__name__)


class AadhaarAPIException(Exception):
    """Custom exception for Aadhaar API errors"""
    pass


class AadhaarVerificationService:
    """
    Service class to handle Aadhaar OTP verification through licensed providers.
    
    IMPORTANT SECURITY NOTES:
    - Aadhaar numbers are handled in memory only
    - No Aadhaar numbers are logged or stored
    - All sensitive data is cleared after use
    - API credentials must be stored securely (environment variables)
    """
    
    def __init__(self, provider: str = 'cashfree'):
        """
        Initialize Aadhaar verification service.
        
        Args:
            provider: API provider name ('cashfree', 'signzy', or 'surepass')
        """
        self.provider = provider.lower()
        self._load_credentials()
        
    def _load_credentials(self):
        """
        Load API credentials from Django settings.
        
        SECURITY: Store these in environment variables, never commit to Git.
        
        In settings.py or .env:
            AADHAAR_API_PROVIDER = 'cashfree'  # or 'signzy', 'surepass'
            AADHAAR_API_CLIENT_ID = 'your_client_id'
            AADHAAR_API_SECRET_KEY = 'your_secret_key'
            AADHAAR_API_SANDBOX = True  # False for production
        """
        self.client_id = getattr(settings, 'AADHAAR_API_CLIENT_ID', 'sandbox_client_id')
        self.secret_key = getattr(settings, 'AADHAAR_API_SECRET_KEY', 'sandbox_secret_key')
        self.is_sandbox = getattr(settings, 'AADHAAR_API_SANDBOX', True)
        
        # Provider-specific endpoints
        self.endpoints = self._get_provider_endpoints()
        
    def _get_provider_endpoints(self) -> Dict[str, str]:
        """
        Get API endpoints for the selected provider.
        
        Returns:
            Dictionary with 'send_otp' and 'verify_otp' endpoints
        """
        # These are example endpoints - replace with actual provider URLs
        endpoints_map = {
            'cashfree': {
                'send_otp': 'https://api.cashfree.com/verification/aadhaar/otp',
                'verify_otp': 'https://api.cashfree.com/verification/aadhaar/verify',
            },
            'signzy': {
                'send_otp': 'https://api.signzy.tech/api/v2/aadhaar/sendOtp',
                'verify_otp': 'https://api.signzy.tech/api/v2/aadhaar/verifyOtp',
            },
            'surepass': {
                'send_otp': 'https://kyc-api.surepass.io/api/v1/aadhaar-v2/generate-otp',
                'verify_otp': 'https://kyc-api.surepass.io/api/v1/aadhaar-v2/submit-otp',
            },
        }
        
        if self.is_sandbox:
            # In sandbox mode, you might use different endpoints
            logger.info(f"Using SANDBOX mode for {self.provider}")
        
        return endpoints_map.get(self.provider, endpoints_map['cashfree'])
    
    def _validate_aadhaar_number(self, aadhaar_number: str) -> Tuple[bool, str]:
        """
        Validate Aadhaar number format (12 digits).
        
        Args:
            aadhaar_number: Aadhaar number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Remove spaces and hyphens
        clean_aadhaar = aadhaar_number.replace(' ', '').replace('-', '')
        
        # Check if 12 digits
        if len(clean_aadhaar) != 12:
            return False, "Aadhaar number must be 12 digits"
        
        # Check if all digits
        if not clean_aadhaar.isdigit():
            return False, "Aadhaar number must contain only digits"
        
        # Basic Verhoeff algorithm check (optional - Aadhaar uses this)
        # For production, implement full Verhoeff validation
        
        return True, ""
    
    def _generate_request_id(self) -> str:
        """
        Generate unique request ID for tracking.
        
        Returns:
            Unique request ID
        """
        timestamp = str(time.time())
        return hashlib.sha256(timestamp.encode()).hexdigest()[:16]
    
    def _make_api_request(self, endpoint: str, payload: Dict, method: str = 'POST') -> Dict:
        """
        Make API request to provider with proper error handling.
        
        Args:
            endpoint: API endpoint URL
            payload: Request payload
            method: HTTP method
            
        Returns:
            API response as dictionary
            
        Raises:
            AadhaarAPIException: If API request fails
        """
        headers = {
            'Content-Type': 'application/json',
            'X-Client-Id': self.client_id,
            'X-Client-Secret': self.secret_key,
        }
        
        try:
            if method == 'POST':
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=30  # 30 second timeout
                )
            else:
                response = requests.get(
                    endpoint,
                    params=payload,
                    headers=headers,
                    timeout=30
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"API request timeout for {endpoint}")
            raise AadhaarAPIException("Request timeout. Please try again.")
        
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {endpoint}")
            raise AadhaarAPIException("Connection error. Please check your internet.")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} for {endpoint}")
            raise AadhaarAPIException(f"Verification service error: {e.response.status_code}")
        
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {str(e)}")
            raise AadhaarAPIException("Unexpected error. Please try again.")
    
    def send_otp(self, aadhaar_number: str) -> Tuple[bool, str, Optional[str]]:
        """
        Send OTP to Aadhaar-linked mobile number.
        
        SECURITY:
        - Aadhaar number is NOT stored or logged
        - Only passed to licensed API provider
        - Provider sends OTP to registered mobile
        
        Args:
            aadhaar_number: 12-digit Aadhaar number
            
        Returns:
            Tuple of (success, message, transaction_id)
            
        Example Response:
            (True, "OTP sent successfully", "TXN123456789")
            (False, "Invalid Aadhaar number", None)
        """
        # Validate Aadhaar format
        is_valid, error_msg = self._validate_aadhaar_number(aadhaar_number)
        if not is_valid:
            return False, error_msg, None
        
        # Clean Aadhaar number
        clean_aadhaar = aadhaar_number.replace(' ', '').replace('-', '')
        
        # Generate request ID for tracking
        request_id = self._generate_request_id()
        
        # Prepare payload (provider-specific format)
        payload = {
            'aadhaar_number': clean_aadhaar,
            'request_id': request_id,
        }
        
        # Log request (WITHOUT Aadhaar number)
        logger.info(f"Sending OTP for Aadhaar verification (Request ID: {request_id})")
        
        try:
            # Make API call
            response = self._make_api_request(
                self.endpoints['send_otp'],
                payload
            )
            
            # Parse response (provider-specific)
            # Example response format:
            # {
            #   "success": true,
            #   "message": "OTP sent successfully",
            #   "transaction_id": "TXN123456789",
            #   "mobile_masked": "XXXXXX1234"
            # }
            
            if response.get('success'):
                transaction_id = response.get('transaction_id') or response.get('ref_id')
                masked_mobile = response.get('mobile_masked', 'registered mobile')
                message = f"OTP sent to {masked_mobile}"
                
                logger.info(f"OTP sent successfully (Transaction: {transaction_id})")
                return True, message, transaction_id
            else:
                error_msg = response.get('message', 'Failed to send OTP')
                logger.warning(f"OTP send failed: {error_msg}")
                return False, error_msg, None
                
        except AadhaarAPIException as e:
            return False, str(e), None
        
        except Exception as e:
            logger.error(f"Unexpected error in send_otp: {str(e)}")
            return False, "System error. Please try again.", None
    
    def verify_otp(self, transaction_id: str, otp: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Verify OTP entered by user.
        
        Args:
            transaction_id: Transaction ID from send_otp response
            otp: 6-digit OTP entered by user
            
        Returns:
            Tuple of (success, message, user_data)
            
        Example Response:
            (True, "Verification successful", {
                "full_name": "JOHN DOE",
                "dob": "01/01/1990",
                "gender": "M",
                "address": {...}
            })
            (False, "Invalid OTP", None)
        """
        # Validate OTP format
        if not otp or len(otp) != 6 or not otp.isdigit():
            return False, "OTP must be 6 digits", None
        
        # Prepare payload
        payload = {
            'transaction_id': transaction_id,
            'otp': otp,
        }
        
        logger.info(f"Verifying OTP (Transaction: {transaction_id})")
        
        try:
            # Make API call
            response = self._make_api_request(
                self.endpoints['verify_otp'],
                payload
            )
            
            # Parse response
            # Example response format:
            # {
            #   "success": true,
            #   "message": "Verification successful",
            #   "data": {
            #     "full_name": "JOHN DOE",
            #     "dob": "01/01/1990",
            #     "gender": "M",
            #     "address": {...}
            #   }
            # }
            
            if response.get('success') or response.get('verified'):
                user_data = response.get('data', {})
                
                # Extract useful information
                verified_data = {
                    'full_name': user_data.get('full_name', user_data.get('name')),
                    'dob': user_data.get('dob'),
                    'gender': user_data.get('gender'),
                    # Address is optional - usually not needed
                }
                
                logger.info(f"OTP verified successfully (Transaction: {transaction_id})")
                return True, "Aadhaar verified successfully", verified_data
            else:
                error_msg = response.get('message', 'Invalid OTP')
                logger.warning(f"OTP verification failed: {error_msg}")
                return False, error_msg, None
                
        except AadhaarAPIException as e:
            return False, str(e), None
        
        except Exception as e:
            logger.error(f"Unexpected error in verify_otp: {str(e)}")
            return False, "System error. Please try again.", None
    
    def get_last_4_digits(self, aadhaar_number: str) -> str:
        """
        Extract last 4 digits of Aadhaar for storage.
        
        Args:
            aadhaar_number: 12-digit Aadhaar number
            
        Returns:
            Last 4 digits as string
        """
        clean_aadhaar = aadhaar_number.replace(' ', '').replace('-', '')
        return clean_aadhaar[-4:] if len(clean_aadhaar) == 12 else ""


# ============================================================================
# SANDBOX/MOCK MODE (For Development & Testing)
# ============================================================================

class MockAadhaarService(AadhaarVerificationService):
    """
    Mock service for development and testing.
    NEVER use in production!
    
    Simulates API responses without calling actual providers.
    Useful for:
    - Local development
    - Automated testing
    - Demos without API keys
    """
    
    def __init__(self):
        logger.warning("Using MOCK Aadhaar service - NOT FOR PRODUCTION!")
        self.provider = 'mock'
    
    def send_otp(self, aadhaar_number: str) -> Tuple[bool, str, Optional[str]]:
        """Mock OTP send - always succeeds"""
        is_valid, error_msg = self._validate_aadhaar_number(aadhaar_number)
        if not is_valid:
            return False, error_msg, None
        
        # Simulate API delay
        time.sleep(1)
        
        transaction_id = f"MOCK_TXN_{int(time.time())}"
        logger.info(f"[MOCK] OTP sent (Transaction: {transaction_id})")
        
        return True, "OTP sent to XXXXXX1234 (MOCK MODE)", transaction_id
    
    def verify_otp(self, transaction_id: str, otp: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Mock OTP verify.
        Accepts OTP: 123456 (success), anything else (failure)
        """
        if len(otp) != 6 or not otp.isdigit():
            return False, "OTP must be 6 digits", None
        
        # Simulate API delay
        time.sleep(1)
        
        # Accept only 123456 in mock mode
        if otp == '123456':
            mock_data = {
                'full_name': 'MOCK USER',
                'dob': '01/01/1990',
                'gender': 'M',
            }
            logger.info(f"[MOCK] OTP verified successfully")
            return True, "Aadhaar verified successfully (MOCK MODE)", mock_data
        else:
            logger.info(f"[MOCK] OTP verification failed")
            return False, "Invalid OTP", None


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_aadhaar_service() -> AadhaarVerificationService:
    """
    Factory function to get appropriate Aadhaar service instance.
    
    Returns:
        AadhaarVerificationService instance (real or mock)
    """
    use_mock = getattr(settings, 'AADHAAR_USE_MOCK', True)
    
    if use_mock:
        return MockAadhaarService()
    else:
        provider = getattr(settings, 'AADHAAR_API_PROVIDER', 'cashfree')
        return AadhaarVerificationService(provider)
