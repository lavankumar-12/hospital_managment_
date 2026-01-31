from flask import Blueprint, jsonify, request
from database import get_db_connection
import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.date.today().isoformat()
    
    stats = {}
    
    # Total Doctors
    cursor.execute("SELECT COUNT(*) as count FROM doctors")
    stats['total_doctors'] = cursor.fetchone()['count']
    
    # Total Patients
    cursor.execute("SELECT COUNT(*) as count FROM patients")
    stats['total_patients'] = cursor.fetchone()['count']
    
    # Today's Appointments
    cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE appointment_date = %s", (today,))
    stats['today_appointments'] = cursor.fetchone()['count']
    
    # Queue Status per Doctor
    cursor.execute("""
        SELECT d.full_name, q.current_token 
        FROM daily_queues q
        JOIN doctors d ON q.doctor_id = d.id
        WHERE q.queue_date = %s
    """, (today,))
    stats['queues'] = cursor.fetchall()
    
    conn.close()
    return jsonify(stats)

@admin_bp.route('/doctors', methods=['GET'])
def get_all_doctors():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*, u.email, dept.name as dept_name 
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        JOIN departments dept ON d.department_id = dept.id
    """)
    docs = cursor.fetchall()
    conn.close()
    return jsonify(docs)

@admin_bp.route('/patients', methods=['GET'])
def get_all_patients():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, u.email 
        FROM patients p
        JOIN users u ON p.user_id = u.id
    """)
    patients = cursor.fetchall()
    conn.close()
    return jsonify(patients)

@admin_bp.route('/todays-appointments', methods=['GET'])
def get_todays_appointments():
    today = datetime.date.today().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.token_number, a.appointment_time, a.status, a.type,
               p.full_name as patient_name,
               d.full_name as doctor_name, d.specialization, dept.name as dept_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN departments dept ON d.department_id = dept.id
        WHERE a.appointment_date = %s
        ORDER BY a.appointment_time ASC
    """, (today,))
    appts = cursor.fetchall()
    # Convert times to string
    for a in appts:
        a['appointment_time'] = str(a['appointment_time'])
    conn.close()
    return jsonify(appts)

@admin_bp.route('/add-doctor', methods=['POST'])
def add_doctor():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    phone = data.get('phone')
    department_id = data.get('department_id')
    experience = data.get('experience', 0)
    
    # Specialization is removed from form, maybe infer or leave blank
    specialization = "General" 
    
    if not all([email, password, full_name, phone, department_id]):
        return jsonify({"message": "Missing required fields"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if email exists
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return jsonify({"message": "Email already exists"}), 409
            
        # Create User
        import bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'doctor') RETURNING id", (email, hashed))
        user_id = cursor.fetchone()['id']
        
        # Create Profile
        cursor.execute("""
            INSERT INTO doctors (user_id, department_id, full_name, specialization, experience, phone) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, department_id, full_name, specialization, experience, phone))
        
        return jsonify({"message": "Doctor added successfully"}), 201
        
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        conn.close()

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if user exists check is optional as delete usually handles it gracefully or returns 0 affected
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        if cursor.rowcount == 0:
            return jsonify({'message': 'User not found'}), 404
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        conn.close()
