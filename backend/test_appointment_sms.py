import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv(r"c:\Users\lavan\OneDrive\Desktop\Hospital-Appointment\.env")

# Add backend to path
sys.path.append(r"c:\Users\lavan\OneDrive\Desktop\Hospital-Appointment\backend")

# Import the send_sms function
from utils.sms import send_sms

print("=" * 60)
print("TESTING APPOINTMENT SMS FUNCTIONALITY")
print("=" * 60)

# Simulate the exact message format used in patient.py
date = "2026-02-02"
time = "10:00:00"
message = f"Thank you for booking appointment on {date} at {time} for your health issue. Please arrive at the hospital at least 30 minutes before the appointment time."

print(f"\nMessage to send:\n{message}\n")
print("Attempting to send SMS...")
print("-" * 60)

# This should mimic what happens in routes/patient.py line 103
success = send_sms("9999999999", message)  # Phone number will be overridden to 9014806135

print("-" * 60)
if success:
    print("✅ SMS Send Function Returned: SUCCESS (TRUE)")
else:
    print("❌ SMS Send Function Returned: FAILURE (FALSE)")
print("=" * 60)
