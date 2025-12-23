# API Documentation

Base URL: `http://localhost:5000/api`

## Authentication
- **POST** `/auth/register`
  - Body: `{ email, password, full_name, age, gender, phone }`
  - Returns: `{ message }`
- **POST** `/auth/login`
  - Body: `{ email, password }`
  - Returns: `{ token, role, user_id }`
- **GET** `/auth/me`
  - Headers: `Authorization: Bearer <token>`
  - Returns: `{ user, profile }`

## Patient
- **GET** `/patient/departments`
- **GET** `/patient/doctors?department_id=<id>`
- **POST** `/patient/book`
  - Body: `{ patient_id, doctor_id, date, time, is_emergency }`
  - Returns: `{ message, token, appointment_id }`
- **GET** `/patient/appointments/<patient_id>`
- **GET** `/patient/queue-status?doctor_id=<id>&date=<date>`
- **GET** `/patient/prescription/download/<appointment_id>` (Returns PDF file)

## Doctor
- **GET** `/doctor/appointments?doctor_id=<id>&date=<date>`
- **POST** `/doctor/next-token`
  - Body: `{ doctor_id }`
  - Returns: `{ message, current_token }`
- **POST** `/doctor/complete-consultation`
  - Body: `{ appointment_id }`

## Admin
- **GET** `/admin/stats`
  - Returns: `{ total_doctors, total_patients, today_appointments, queues: [] }`
