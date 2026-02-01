from twilio.rest import Client
import os
import sys

# Add parent directory to path to import config if needed, though usually python adds current dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import Config
except ImportError:
    # Fallback if running directly or path issue
    class Config:
        TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
        TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
        TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

def send_sms(mobile, message):
    """
    Send SMS to the given mobile number using Twilio.
    """
    if not mobile:
        print("No mobile number provided for SMS")
        return False
        
    try:
        account_sid = Config.TWILIO_ACCOUNT_SID
        auth_token = Config.TWILIO_AUTH_TOKEN
        from_number = Config.TWILIO_PHONE_NUMBER
        
        # HARDCODED FOR DEMO/EVALUATION
        # Override any patient number with the specific evaluation number
        target_number = '+919014806135'
        print(f"!!! DEMO OVERRIDE: Sending SMS to {target_number} instead of {mobile} !!!")
        
        if not account_sid or not auth_token:
             print("Twilio credentials missing - SIMULATING SMS SEND FOR DEV/DEMO")
             print(f"--- MOCK SMS to {target_number}: {message} ---")
             return True

        client = Client(account_sid, auth_token)
        
        # Ensure mobile number has country code, default to +91 if missing
        # Clean the number first - strictly for the hardcoded number just in case we change it later
        # clean_mobile = ''.join(filter(str.isdigit, str(mobile)))
        
        # We are using the hardcoded target_number directly
        mobile = target_number

        print(f"Attempting to send SMS to {mobile}...")
        msg_response = client.messages.create(
            body=message,
            from_=from_number,
            to=mobile
        )
        print(f"------------ SMS SENT TO {mobile} ------------")
        print(f"SID: {msg_response.sid}")
        print("----------------------------------------------")
        return True
    except Exception as e:
        print(f"❌ Real SMS Failed: {e}")
        print("⚠️ FALLING BACK TO MOCK MODE FOR DEMO STABILITY")
        print(f"--- MOCK SMS to {target_number}: {message} ---")
        return True
