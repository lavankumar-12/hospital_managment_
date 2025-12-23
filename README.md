# Hospital Appointment and Real-Time Queue Management System

## Prerequisites
- Python 3.8+
- MySQL Server

## Setup

1. **Database Setup**
   - Ensure MySQL is running on localhost:3306
   - User: `root`, Password: `9885` (Update `backend/config.py` & `backend/init_db.py` if different)
   - Initialize Database:
     ```sh
     cd backend
     python init_db.py
     ```

2. **Backend Setup**
   - Install dependencies:
     ```sh
     pip install -r backend/requirements.txt
     ```
   - Run the server:
     ```sh
     python backend/app.py
     ```
   - Server runs on `http://localhost:5000`

3. **Frontend**
   - No build required. Open `frontend/index.html` in your browser.
   - For better experience (avoid CORS if opening as file), use a live server extension or python simple http server:
     ```sh
     cd frontend
     python -m http.server 8000
     ```
     Then go to `http://localhost:8000`.

## Credentials
- **Admin**: `admin@hospital.com` / `admin123`
- **Doctor**: `doctor@hospital.com` / `doctor123`
- **Pharmacist**: `pharmacist@hospital.com` / `pharmacy123`
- **Patient**: Register a new account.

## Features

### Patient
- **Appointment Booking**: Book appointments with specific doctors or departments.
- **Emergency Booking**: "SOS" feature to immediately book the next available doctor.
- **Queue Management**: View live queue status and current serving token.
- **Records**: View appointment history and download Prescription PDFs.
- **Pharmacy**: 
  - Browse medicines by department or search.
  - Add to cart with quantity adjustment (+/-).
  - Secure checkout.

### Doctor
- **Dashboard**: View daily appointments and stats.
- **Queue Control**: "Call Next Patient" functionality to update the live queue.
- **Profile**: View and manage profile details.

### Pharmacist
- **Inventory Management**: 
  - Add new medicines.
  - **Edit Medicine**: Update price and stock quantity seamlessly.
  - Real-time inventory tracking.
- **Dashboard**: Overview of available stock and low-stock alerts.

### Admin
- **System Overview**: View system stats and monitor activity.

## Departments
- Cardiology, Neurology, Orthopedics, Pediatrics, General Medicine, Dermatology, Dental, Gynaecology, Psychiatry, ENT, Ophthalmology.

## Tech Stack
- Frontend: HTML5, Tailwind CSS, Vanilla JS
- Backend: Flask, MySQL, JWT Auth
- PDF: ReportLab
