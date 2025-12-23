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
        # Get current queue
        cursor.execute("SELECT current_token FROM daily_queues WHERE doctor_id=%s AND queue_date=%s", (doctor_id, date))
        res = cursor.fetchone()
        
        if not res:
            # Init if not existing
            cursor.execute("INSERT INTO daily_queues (doctor_id, queue_date, current_token) VALUES (%s, %s, 0)", (doctor_id, date))
            current = 0
        else:
            current = res['current_token']
        
        next_tok = current + 1
        
        # Check if next token exists in appointments
        cursor.execute("SELECT id FROM appointments WHERE doctor_id=%s AND appointment_date=%s AND token_number=%s", (doctor_id, date, next_tok))
        if not cursor.fetchone():
             return jsonify({"message": "No more patients in queue"}), 404
             
        # Update queue
        cursor.execute("UPDATE daily_queues SET current_token = %s WHERE doctor_id=%s AND queue_date=%s", (next_tok, doctor_id, date))
        
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
    conn.close()
    
    return jsonify({"message": "Consultation completed"}), 200

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
    cursor.execute("SELECT leave_date FROM doctor_leaves WHERE doctor_id=%s AND leave_date >= CURDATE()", (doctor_id,))
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
