# 🏥 Sunrise Hospital Management System
### *Luxury Care Meet Real-Time Efficiency*

A comprehensive Hospital Management System (HMS) featuring a premium user interface, AI-powered medical diagnostics, and a real-time token-based queue management system.

---

## ✨ Premium Features

### 👤 Patient Experience
- **Live Doctor Status**: Real-time "Pause" banners instantly alert you if your doctor is on a break or attending an emergency.
- **Smart Appointment Booking**: Seamless scheduling with specialized doctors.
- **🚨 Emergency SOS**: One-click "Get Help Now" for immediate priority allocation.
- **AI Report Analyzer**: Upload medical reports (Images/PDFs) for instant AI-powered analysis and explanations in your preferred language.
- **Real-Time Queue Tracking**: View live updates of the current serving token.
- **Dashboard Notifications**: Instant pop-up alerts for queue updates and 10-min appointment reminders.
- **Integrated Pharmacy**: Full-featured pharmacy store with cart management and order history.
- **Prescription Vault**: Digital access to all past prescriptions with PDF download support.

### 👨‍⚕️ Doctor Console
- **Pause & Resume**: One-click "Emergency Pause" to stop the queue and notify all waiting patients instantly.
- **Dynamic Queue Management**: One-click "Call Next Patient" with auto-sync status updates.
- **Patient Status Lifecycle**: Automatic tracking of patient flow (Pending → Called/Serving → Completed).
- **Emergency Pulsing Alerts**: Intense UI notifications for high-priority emergency cases.
- **Schedule Management**: Set daily shift timings and mark leaves/holidays.

### 💊 Pharmacist Terminal
- **Inventory Engine**: Real-time stock tracking with low-stock visual cues.
- **Medicine Studio**: Add, edit, and manage medicine details including department mapping.
- **Order Processing**: Track and manage patient medicine orders.

### 🛡️ Admin Command Center
- **System Orchestration**: High-level overview of hospital activity and stats.
- **Security Guardian**: Centralized management of hospital users and departments.
- **Data Analytics**: Insightful charts on patient flow and department usage.

---

## 🛠️ Tech Stack

- **Frontend**: HTML5, Vanilla JavaScript, **Tailwind CSS**, Custom Animations.
- **Backend**: **Flask** (Python), **Neon (PostgreSQL)**, JWT Authentication.
- **AI Engine**: **Google Gemini Pro Vision** (for Medical Report Analysis).
- **Notifications**: Custom-built Dashboard Popup, Toast notification system, and SMS alerts.
- **Reports**: ReportLab for dynamic PDF Prescription generation.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- PostgreSQL Connection (or local setup)

### 2. Database Setup
1. Can use **Neon Serverless Postgres** or local PostgreSQL.
2. Configure credentials in `backend/config.py`:
   ```python
   DB_HOST = 'your-neon-hostname'
   DB_USER = 'your-username'
   DB_PASSWORD = 'your-password'
   DB_NAME = 'neondb'
   DB_SSL_MODE = 'require'
   ```
3. Initialize the schema:
   ```sh
   cd backend
   python init_db.py
   ```

### 3. Backend Execution
```sh
pip install -r backend/requirements.txt
python backend/app.py
```
*Port: `http://localhost:5001`*

### 4. Frontend Launch
Open `frontend/index.html` directly in your browser or serve it via Live Server:
```sh
cd frontend
python -m http.server 8000
```
*Access: `http://localhost:8000`*

---

## 🔐 Default Credentials

| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@hospital.com` | `lavan` |
| **Doctor** | `doctor@hospital.com` | `doctor123` |
| **Pharmacist**| `pharmacist@hospital.com` | `pharmacy123` |
| **Patient** | *Register a new account* | `--` |

---

## 🏥 Departments
`Cardiology` | `Neurology` | `Orthopedics` | `Pediatrics` | `General Medicine` | `Dermatology` | `Gynaecology` | `Dental` | `Psychiatry` | `ENT` | `Ophthalmology`

---
*Created with ❤️ by Sunrise Hospital Tech Team*
