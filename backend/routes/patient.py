from flask import Blueprint, request, jsonify, send_file
from database import get_db_connection
from utils.sms import send_sms
from utils.pdf import generate_prescription_pdf
import datetime

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/departments', methods=['GET'])
def get_departments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM departments")
    depts = cursor.fetchall()
    conn.close()
    return jsonify(depts)

@patient_bp.route('/doctors', methods=['GET'])
def get_doctors():
    dept_id = request.args.get('department_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT d.*, dept.name as dept_name FROM doctors d JOIN departments dept ON d.department_id = dept.id"
    params = []
    if dept_id:
        query += " WHERE d.department_id = %s"
        params.append(dept_id)
        
    cursor.execute(query, tuple(params))
    doctors = cursor.fetchall()
    conn.close()
    return jsonify(doctors)

@patient_bp.route('/book', methods=['POST'])
def book_appointment():
    data = request.json
    patient_id = data.get('patient_id') # In real app, get from token
    doctor_id = data.get('doctor_id')
    date = data.get('date') # YYYY-MM-DD
    time = data.get('time') # HH:MM
    is_emergency = data.get('is_emergency', False)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check leave
        cursor.execute("SELECT id FROM doctor_leaves WHERE doctor_id=%s AND leave_date=%s", (doctor_id, date))
        if cursor.fetchone():
            return jsonify({"message": "Doctor is on leave on this date"}), 400

        # Check schedule
        # Check schedule
        try:
            time_part = datetime.datetime.strptime(time, "%H:%M").time()
        except ValueError:
            time_part = datetime.datetime.strptime(time, "%H:%M:%S").time()
        cursor.execute("SELECT schedule_start, schedule_end FROM doctors WHERE id=%s", (doctor_id,))
        doc_sched = cursor.fetchone()
        
        if doc_sched:
            s_start = (datetime.datetime.min + doc_sched['schedule_start']).time()
            s_end = (datetime.datetime.min + doc_sched['schedule_end']).time()
            if not (s_start <= time_part <= s_end):
                return jsonify({"message": f"Doctor available only between {s_start} and {s_end}"}), 400

        # Check availability (simple check)
        # Prevent double booking: Patient cannot book same doctor same day? Or just time slot collision?
        # User requirement: "Prevent double booking"
        cursor.execute("SELECT id FROM appointments WHERE doctor_id=%s AND appointment_date=%s AND appointment_time=%s AND status!='cancelled'", (doctor_id, date, time))
        if cursor.fetchone():
            return jsonify({"message": "Slot already booked"}), 409

        # Generate Token
        # Check/Update Daily Queue
        cursor.execute("INSERT INTO daily_queues (doctor_id, queue_date, current_token) VALUES (%s, %s, 0) ON DUPLICATE KEY UPDATE id=id", (doctor_id, date))
        
        # Get max token for this day
        cursor.execute("SELECT MAX(token_number) as max_tok FROM appointments WHERE doctor_id=%s AND appointment_date=%s", (doctor_id, date))
        res = cursor.fetchone()
        token = (res['max_tok'] or 0) + 1
        
        # Insert Appointment
        atype = 'emergency' if is_emergency else 'normal'
        cursor.execute("INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, token_number, type) VALUES (%s, %s, %s, %s, %s, %s)",
                       (patient_id, doctor_id, date, time, token, atype))
        appt_id = cursor.lastrowid
        
        # Send SMS
        # Fetch details for SMS
        cursor.execute("SELECT phone FROM patients WHERE id=%s", (patient_id,))
        p_res = cursor.fetchone()
        if p_res:
            msg = f"Thank you for booking appointment on {date} at {time} for your health issue. Please arrive at the hospital at least 30 minutes before the appointment time."
            send_sms(p_res['phone'], msg)
            
        return jsonify({"message": "Appointment booked successfully", "token": token, "appointment_id": appt_id}), 201
    
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        conn.close()

@patient_bp.route('/appointments/<int:patient_id>', methods=['GET'])
def get_history(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Join doctor name
    cursor.execute("""
        SELECT a.*, d.full_name as doctor_name, dept.name as dept_name 
        FROM appointments a 
        JOIN doctors d ON a.doctor_id = d.id 
        JOIN departments dept ON d.department_id = dept.id
        WHERE a.patient_id = %s 
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """, (patient_id,))
    appts = cursor.fetchall()
    conn.close()
    return jsonify(appts)

@patient_bp.route('/prescription/download/<int:appt_id>', methods=['GET'])
def download_prescription(appt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, d.full_name as doctor_name, dept.name as dept_name, p.full_name as patient_name, p.age, p.gender
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN departments dept ON d.department_id = dept.id
        JOIN patients p ON a.patient_id = p.id
        WHERE a.id = %s
    """, (appt_id,))
    
    data = cursor.fetchone()
    conn.close()
    
    if not data:
        return jsonify({"message": "Appointment not found"}), 404
        
    pdf_buffer = generate_prescription_pdf(
        doctor_name=data['doctor_name'],
        department=data['dept_name'],
        patient_name=data['patient_name'],
        age=data['age'],
        gender=data['gender'],
        date=str(data['appointment_date']),
        time=str(data['appointment_time'])
    )
    
    return send_file(pdf_buffer, as_attachment=True, download_name=f"prescription_{appt_id}.pdf", mimetype='application/pdf')

@patient_bp.route('/queue-status', methods=['GET'])
def queue_status():
    doctor_id = request.args.get('doctor_id')
    date = request.args.get('date') or datetime.date.today().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT current_token FROM daily_queues WHERE doctor_id=%s AND queue_date=%s", (doctor_id, date))
    res = cursor.fetchone()
    
    current = res['current_token'] if res else 0
    
    # Calculate estimated wait time properly? 
    # Approx 15 mins per patient? 
    # waiting = (your_token - current_token) * 15
    # For now just return current token
    conn.close()
    return jsonify({"current_token": current})

@patient_bp.route('/check-availability', methods=['GET'])
def check_availability():
    doctor_id = request.args.get('doctor_id')
    date = request.args.get('date')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM doctor_leaves WHERE doctor_id=%s AND leave_date=%s", (doctor_id, date))
        if cursor.fetchone():
             return jsonify({"available": False, "message": "Doctor is on leave"}), 200
        return jsonify({"available": True}), 200
    finally:
        conn.close()
