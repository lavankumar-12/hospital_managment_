from flask import Blueprint, request, jsonify
from database import get_db_connection
import datetime

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/appointments', methods=['GET'])
def get_daily_appointments():
    doctor_id = request.args.get('doctor_id')
    date = request.args.get('date') or datetime.date.today().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, p.full_name as patient_name, p.age, p.gender
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.doctor_id = %s AND a.appointment_date = %s
        ORDER BY a.token_number ASC
    """, (doctor_id, date))
    
    appts = cursor.fetchall()
    conn.close()
    return jsonify(appts)

@doctor_bp.route('/next-token', methods=['POST'])
def call_next_token():
    data = request.json
    doctor_id = data.get('doctor_id')
    date = datetime.date.today().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Find the next pending appointment for this doctor today
        # We order by token_number to ensure we take the next one in sequence
        cursor.execute("""
            SELECT a.id, a.patient_id, a.token_number, d.full_name as doctor_name 
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.doctor_id=%s AND a.appointment_date=%s AND a.status='pending'
            ORDER BY a.token_number ASC LIMIT 1
        """, (doctor_id, date))
        appt = cursor.fetchone()
        
        if not appt:
             return jsonify({"message": "No more pending patients in queue"}), 404
             
        next_tok = appt['token_number']
        
        # Update appointment status to 'called'
        cursor.execute("UPDATE appointments SET status='called' WHERE id=%s", (appt['id'],))
        
        # Update daily_queues to reflect the currently serving token
        # Check if entry exists for today
        cursor.execute("SELECT id FROM daily_queues WHERE doctor_id=%s AND queue_date=%s", (doctor_id, date))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO daily_queues (doctor_id, queue_date, current_token) VALUES (%s, %s, %s)", (doctor_id, date, next_tok))
        else:
            cursor.execute("UPDATE daily_queues SET current_token = %s WHERE doctor_id=%s AND queue_date=%s", (next_tok, doctor_id, date))
        
        # Create notification for patient
        message = f"Please proceed to the cabin of Dr. {appt['doctor_name']}. Your token number {next_tok} is called."
        cursor.execute("""
            INSERT INTO notifications (patient_id, message, type, appointment_id)
            VALUES (%s, %s, 'CALL_NEXT', %s)
        """, (appt['patient_id'], message, appt['id']))
        
        conn.commit()
        return jsonify({"message": "Called next token", "current_token": next_tok}), 200
        
    except Exception as e:
         return jsonify({"message": str(e)}), 500
    finally:
         conn.close()

@doctor_bp.route('/complete-consultation', methods=['POST'])
def complete_consultation():
    data = request.json
    appt_id = data.get('appointment_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE appointments SET status='completed' WHERE id=%s", (appt_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Consultation completed"}), 200

@doctor_bp.route('/appointment/accept', methods=['POST'])
def accept_appointment():
    data = request.json
    appt_id = data.get('appointment_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE appointments SET status='accepted' WHERE id=%s", (appt_id,))
        conn.commit()
        return jsonify({"message": "Appointment accepted"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        conn.close()

@doctor_bp.route('/appointment/reschedule', methods=['POST'])
def reschedule_appointment():
    data = request.json
    appt_id = data.get('appointment_id')
    new_date = data.get('new_date')
    new_time = data.get('new_time')
    note = data.get('note', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE appointments 
            SET status='rescheduled', appointment_date=%s, appointment_time=%s, reschedule_note=%s 
            WHERE id=%s
        """, (new_date, new_time, note, appt_id))
        
        # Notify patient
        cursor.execute("SELECT patient_id FROM appointments WHERE id=%s", (appt_id,))
        patient = cursor.fetchone()
        if patient:
            msg = f"Your appointment has been rescheduled to {new_date} at {new_time}. Note: {note}"
            cursor.execute("""
                INSERT INTO notifications (patient_id, message, type, appointment_id)
                VALUES (%s, %s, 'APPOINTMENT_REMINDER', %s)
            """, (patient['patient_id'], msg, appt_id))
            
        conn.commit()
        return jsonify({"message": "Appointment rescheduled"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        conn.close()

@doctor_bp.route('/pause', methods=['POST'])
def pause_consultations():
    data = request.json
    doctor_id = data.get('doctor_id')
    reason = data.get('reason', 'Emergency break')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE doctors SET is_paused=TRUE, pause_reason=%s WHERE id=%s", (reason, doctor_id))
        
        # Notify all pending/accepted patients for today
        cursor.execute("SELECT patient_id FROM appointments WHERE doctor_id=%s AND appointment_date=CURRENT_DATE AND status IN ('pending', 'accepted', 'called')", (doctor_id,))
        patients = cursor.fetchall()
        for p in patients:
            cursor.execute("""
                INSERT INTO notifications (patient_id, message, type)
                VALUES (%s, %s, 'APPOINTMENT_REMINDER')
            """, (p['patient_id'], f"Consultations are temporarily paused by the doctor. Reason: {reason}. Please wait."))
            
        conn.commit()
        return jsonify({"message": "Consultations paused"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        conn.close()

@doctor_bp.route('/resume', methods=['POST'])
def resume_consultations():
    data = request.json
    doctor_id = data.get('doctor_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE doctors SET is_paused=FALSE, pause_reason=NULL WHERE id=%s", (doctor_id,))
        
        # Notify patients
        cursor.execute("SELECT patient_id FROM appointments WHERE doctor_id=%s AND appointment_date=CURRENT_DATE AND status IN ('pending', 'accepted')", (doctor_id,))
        patients = cursor.fetchall()
        for p in patients:
            cursor.execute("""
                INSERT INTO notifications (patient_id, message, type)
                VALUES (%s, %s, 'APPOINTMENT_REMINDER')
            """, (p['patient_id'], "The doctor has resumed consultations. Thank you for your patience."))
            
        conn.commit()
        return jsonify({"message": "Consultations resumed"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        conn.close()

@doctor_bp.route('/schedule', methods=['POST'])
def update_schedule():
    data = request.json
    doctor_id = data.get('doctor_id')
    start = data.get('start_time')
    end = data.get('end_time')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE doctors SET schedule_start=%s, schedule_end=%s WHERE id=%s", (start, end, doctor_id))
        return jsonify({"message": "Schedule updated"}), 200
    finally:
        conn.close()

@doctor_bp.route('/leave', methods=['POST'])
def add_leave():
    data = request.json
    doctor_id = data.get('doctor_id')
    date = data.get('date')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO doctor_leaves (doctor_id, leave_date) VALUES (%s, %s)", (doctor_id, date))
        return jsonify({"message": "Leave marked"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        conn.close()

@doctor_bp.route('/leaves', methods=['GET'])
def get_leaves():
    doctor_id = request.args.get('doctor_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT leave_date FROM doctor_leaves WHERE doctor_id=%s AND leave_date >= CURRENT_DATE", (doctor_id,))
    leaves = [r['leave_date'].isoformat() for r in cursor.fetchall()]
    conn.close()
    return jsonify(leaves)

@doctor_bp.route('/me', methods=['GET'])
def get_doctor_details():
    doctor_id = request.args.get('doctor_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors WHERE id=%s", (doctor_id,))
    doc = cursor.fetchone()
    # Serialize times
    if doc:
        doc['schedule_start'] = str(doc['schedule_start'])
        doc['schedule_end'] = str(doc['schedule_end'])
    conn.close()
    return jsonify(doc)
