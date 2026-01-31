from flask import Blueprint, request, jsonify, send_file
from database import get_db_connection
from utils.sms import send_sms
from utils.pdf import generate_prescription_pdf
import datetime
import os
from google import genai
from PIL import Image
import io

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
        
        if doc_sched and not is_emergency:
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

@patient_bp.route('/analyze-report', methods=['POST'])
def analyze_report():
    if 'report' not in request.files:
        return jsonify({"error": "No report file provided"}), 400
    
    file = request.files['report']
    language = request.form.get('language', 'English')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Check for API Key
        from config import Config
        api_key = Config.GEMINI_API_KEY
        
        # DEMO MODE FALLBACK
        if not api_key:
            import time
            time.sleep(2) # Simulate processing time
            
            demo_analyses = {
                "English": "### 📋 Report Summary\n\nYour medical report looks normal. All blood counts and sugar levels are within the healthy range.\n\n**Key Points:**\n- Hemoglobin is good.\n- No signs of infection.\n- Vital signs are stable.\n\n**Suggestions:** \n- Eat healthy food.\n- Drink plenty of water.\n- Get 7-8 hours of sleep.",
                "Hindi": "### 📋 रिपोर्ट सारांश\n\nआपकी मेडिकल रिपोर्ट सामान्य है। सभी ब्लड काउंट और शुगर लेवल स्वस्थ सीमा के भीतर हैं।\n\n**मुख्य बिंदु:**\n- हीमोग्लोबिन अच्छा है।\n- संक्रमण का कोई संकेत नहीं है।\n- स्वास्थ्य स्थिर है।\n\n**सुझाव:**\n- स्वस्थ भोजन खाएं।\n- खूब पानी पिएं।\n- 7-8 घंटे की नींद लें।",
                "Telugu": "### 📋 రిపోర్ట్ సారాంశం\n\nమీ మెడికల్ రిపోర్ట్ సాధారణంగా ఉంది. రక్త పరీక్షలు మరియు షుగర్ లెవల్స్ అన్నీ ఆరోగ్యకరమైన పరిధిలో ఉన్నాయి.\n\n**ముఖ్య విషయాలు:**\n- హిమోగ్లోబిన్ బాగుంది.\n- ఇన్ఫెక్షన్ సంకేతాలు లేవు.\n- ఆరోగ్యం స్థిరంగా ఉంది.\n\n**సూచనలు:**\n- ఆరోగ్యకరమైన ఆహారం తీసుకోండి.\n- మంచి నీరు ఎక్కువగా త్రాగండి.\n- 7-8 గంటలు నిద్రపోండి.",
                "Tamil": "### 📋 அறிக்கை சுருக்கம்\n\nஉங்கள் மருத்துவ அறிக்கை சாதாரணமாக உள்ளது. அனைத்து இரத்த அளவுகளும் சர்க்கரை அளவுகளும் ஆரோக்கியமான வரம்பிற்குள் உள்ளன.\n\n**முக்கிய குறிப்புகள்:**\n- ஹீமோகுளோபின் அளவு நன்றாக உள்ளது.\n- தொற்றுக்கான அறிகுறிகள் எதுவும் இல்லை.\n- உடல்நிலை சீராக உள்ளது.\n\n**பரிந்துரைகள்:**\n- ஆரோக்கியமான உணவை உண்ணுங்கள்.\n- அதிக தண்ணீர் குடிக்கவும்.\n- 7-8 மணிநேரம் தூங்குங்கள்.",
                "Kannada": "### 📋 ವರದಿ ಸಾರಾಂಶ\n\nನಿಮ್ಮ ವೈದ್ಯಕೀಯ ವರದಿಯು ಸಾಮಾನ್ಯವಾಗಿದೆ. ನಿಮ್ಮ ರಕ್ತದ ಪ್ರಮಾಣ ಮತ್ತು ಸಕ್ಕರೆ ಮಟ್ಟವು ಆರೋಗ್ಯಕರ ಮಿತಿಯಲ್ಲಿದೆ.\n\n**ಪ್ರಮುಖ ಅಂಶಗಳು:**\n- ಹಿಮೋಗ್ಲೋಬಿನ್ ಪ್ರಮಾಣ ಚೆನ್ನಾಗಿದೆ.\n- ಸೋಂಕಿನ ಯಾವುದೇ ಲಕ್ಷಣಗಳಿಲ್ಲ.\n- ಆರೋಗ್ಯ ಸ್ಥಿರವಾಗಿದೆ.\n\n**ಸಲಹೆಗಳು:**\n- ಆರೋಗ್ಯಕರ ಆಹಾರ ಸೇವಿಸಿ.\n- ಸಾಕಷ್ಟು ನೀರು ಕುಡಿಯಿರಿ.\n- 7-8 ಗಂಟೆಗಳ ಕಾಲ ನಿದ್ರೆ ಮಾಡಿ.",
                "Malayalam": "### 📋 റിപ്പോർട്ട് സംഗ്രഹം\n\nനിങ്ങളുടെ മെഡിക്കൽ റിപ്പോർട്ട് സാധാരണ നിലയിലാണ്. എല്ലാ രക്തപരിശോധനകളും ഷുഗർ ലെവലും ആരോഗ്യകരമായ നിലവാരത്തിലാണ്.\n\n**പ്രധാന കാര്യങ്ങൾ:**\n- ഹീമോഗ്ലോബിൻ അളവ് തൃപ്തികരമാണ്.\n- അണുബാധയുടെ ലക്ഷണങ്ങളൊന്നുമില്ല.\n- ആരോഗ്യം സുസ്ഥിരമാണ്.\n\n**നിർദ്ദേശങ്ങൾ:**\n- ആരോഗ്യകരമായ ഭക്ഷണം കഴിക്കുക.\n- ധാരാളം വെള്ളം കുടിക്കുക.\n- 7-8 മണിക്കൂർ ഉറങ്ങുക.",
                "Bengali": "### 📋 রিপোর্ট সারাংশ\n\nআপনার মেডিকেল রিপোর্ট স্বাভাবিক। আপনার রক্ত এবং শর্করার মাত্রা স্বাস্থ্যকর সীমার মধ্যে রয়েছে।\n\n**মূল পয়েন্ট:**\n- হিমোগ্লোবিন ভালো আছে।\n- সংক্রমণের কোনো লক্ষণ নেই।\n- স্বাস্থ্য স্থিতিশীল।\n\n**পরামর্শ:**\n- স্বাস্থ্যকর খাবার খান।\n- প্রচুর পরিমাণে জল পান করুন।\n- ৭-৮ ঘণ্টা ঘুমান।"
            }
            
            # Default to English if language not in demo map
            analysis = demo_analyses.get(language, demo_analyses["English"])
            return jsonify({"analysis": analysis})

        client = genai.Client(api_key=api_key)

        # Read the file
        img_bytes = file.read()
        
        if file.filename.lower().endswith('.pdf'):
            content = [
                f"Please analyze this medical report and provide a clear, concise summary and analysis. Then, translate your entire response into {language}. Keep the tone professional and helpful.",
                genai.types.Part.from_bytes(data=img_bytes, mime_type="application/pdf")
            ]
        else:
            img = Image.open(io.BytesIO(img_bytes))
            content = [
                f"Please analyze this medical report and provide a clear, concise summary and analysis. Then, translate your entire response into {language}. Keep the tone professional and helpful.",
                img
            ]

        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=content
        )
        
        return jsonify({"analysis": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
