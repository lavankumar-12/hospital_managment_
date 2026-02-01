
import os
import sys

# Mock setting env vars if they aren't picked up automatically (though python-dotenv in utils might handle it)
# We will rely on sms.py to load them or we load them here.
from dotenv import load_dotenv
load_dotenv(r"c:\Users\lavan\OneDrive\Desktop\Hospital-Appointment\.env")

# Now import the sms function
sys.path.append(r"c:\Users\lavan\OneDrive\Desktop\Hospital-Appointment\backend")
from utils.sms import send_sms

print("Testing SMS...")
# Random number, it should be overridden by the hardcoded one in sms.py
success = send_sms("+919999999999", "Test message from System Check")

if success:
    print("SMS Send returned TRUE")
else:
    print("SMS Send returned FALSE")
