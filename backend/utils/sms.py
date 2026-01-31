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
        
        if not account_sid or not auth_token:
             print("Twilio credentials missing")
             return False

        client = Client(account_sid, auth_token)
        
        # Ensure mobile number has country code, default to +91 if missing
        # Clean the number first
        clean_mobile = ''.join(filter(str.isdigit, str(mobile)))
        
        if len(clean_mobile) == 10:
             mobile = '+91' + clean_mobile
        elif len(clean_mobile) == 12 and clean_mobile.startswith('91'):
             mobile = '+' + clean_mobile
        elif not mobile.startswith('+'):
             # If it has some other format but no +, add +?
             # Let's hope for the best or leave as is if we can't determine
             pass

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
        print(f"Failed to send SMS: {e}")
        return False
