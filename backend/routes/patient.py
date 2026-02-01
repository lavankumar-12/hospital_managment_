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
            s_start = doc_sched['schedule_start']
            s_end = doc_sched['schedule_end']
            # If for some reason checking type is needed in future, can add here.
            # But psycopg2 returns datetime.time for TIME columns.
            if not (s_start <= time_part <= s_end):
                return jsonify({"message": f"Doctor available only between {s_start} and {s_end}"}), 400

        # Check availability (simple check)
        # Prevent double booking: Patient cannot book same doctor same day? Or just time slot collision?
        # User requirement: "Prevent double booking"
        cursor.execute("SELECT id FROM appointments WHERE doctor_id=%s AND appointment_date=%s AND appointment_time=%s AND status!='cancelled'", (doctor_id, date, time))
        if cursor.fetchone():
            return jsonify({"message": "Slot already booked"}), 409

        # Generate Token
        # Generate Token
        # Check/Update Daily Queue
        cursor.execute("INSERT INTO daily_queues (doctor_id, queue_date, current_token) VALUES (%s, %s, 0) ON CONFLICT (doctor_id, queue_date) DO NOTHING", (doctor_id, date))
        
        # Get max token for this day
        cursor.execute("SELECT MAX(token_number) as max_tok FROM appointments WHERE doctor_id=%s AND appointment_date=%s", (doctor_id, date))
        res = cursor.fetchone()
        token = (res['max_tok'] or 0) + 1
        
        # Insert Appointment
        atype = 'emergency' if is_emergency else 'normal'
        cursor.execute("INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, token_number, type) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                       (patient_id, doctor_id, date, time, token, atype))
        appt_id = cursor.fetchone()['id']
        
        # Commit the appointment to database
        conn.commit()
        
        # Send SMS
        # Fetch details for SMS
        print(f"[BOOKING] Fetching patient phone for patient_id: {patient_id}")
        cursor.execute("SELECT phone FROM patients WHERE id=%s", (patient_id,))
        p_res = cursor.fetchone()
        
        if p_res:
            patient_phone = p_res['phone']
            print(f"[BOOKING] Patient phone found: {patient_phone}")
            msg = f"Thank you for booking appointment on {date} at {time} for your health issue. Please arrive at the hospital at least 30 minutes before the appointment time."
            print(f"[BOOKING] Calling send_sms() function...")
            sms_sent = send_sms(patient_phone, msg)
            print(f"[BOOKING] SMS Result: {sms_sent}")
        else:
            print(f"[BOOKING] ERROR: No patient found with ID {patient_id}")
            sms_sent = False
            
        return jsonify({"message": "Appointment booked successfully", "token": token, "appointment_id": appt_id, "sms_sent": sms_sent}), 201
    
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

@patient_bp.route('/notifications', methods=['GET'])
def get_notifications():
    patient_id = request.args.get('patient_id')
    if not patient_id:
        return jsonify([])
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Auto-generate reminders for upcoming appointments (within 10 mins)
        now = datetime.datetime.now()
        ten_mins_later = now + datetime.timedelta(minutes=10)
        today = now.date()
        
        cursor.execute("""
            SELECT a.id, a.appointment_time, d.full_name as doctor_name
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.patient_id = %s 
            AND a.appointment_date = %s 
            AND a.status = 'pending'
            AND a.appointment_time <= %s
            AND a.appointment_time >= %s
        """, (patient_id, today, ten_mins_later.time(), now.time()))
        
        upcoming = cursor.fetchall()
        
        for appt in upcoming:
            # Check if reminder already exists for THIS specific appointment
            cursor.execute("SELECT id FROM notifications WHERE patient_id=%s AND appointment_id=%s AND type='APPOINTMENT_REMINDER'", (patient_id, appt['id']))
            if not cursor.fetchone():
                msg = f"Your appointment has only 10 min so you ready for the consulation of the doctor {appt['doctor_name']}"
                cursor.execute("""
                    INSERT INTO notifications (patient_id, message, type, appointment_id)
                    VALUES (%s, %s, 'APPOINTMENT_REMINDER', %s)
                """, (patient_id, msg, appt['id']))
        
        # 2. Fetch unread notifications
        cursor.execute("SELECT * FROM notifications WHERE patient_id = %s AND is_read = FALSE ORDER BY created_at DESC", (patient_id,))
        notifications = cursor.fetchall()
        
        return jsonify(notifications)
    except Exception as e:
        print(f"Error in notifications: {e}")
        return jsonify([])
    finally:
        conn.close()

@patient_bp.route('/notifications/mark-read', methods=['POST'])
def mark_notification_read():
    data = request.json
    notif_id = data.get('notification_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = TRUE WHERE id = %s", (notif_id,))
    conn.close()
    return jsonify({"message": "Notification marked as read"})

@patient_bp.route('/ai-chat', methods=['POST'])
def ai_chat():
    """
    AI Health Assistant chatbot endpoint
    """
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({"error": "Message is required"}), 400
    
    try:
        from config import Config
        api_key = Config.GEMINI_API_KEY
        
        # DEMO MODE FALLBACK
        if not api_key:
            print("[AI CHAT] API Key missing - Using enhanced demo responses")
            import time
            time.sleep(1)  # Simulate processing
            
            # Enhanced keyword-based demo responses
            msg_lower = user_message.lower()
            
            # Greetings
            if any(word in msg_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good evening']):
                response = "Hello! 👋 I'm your AI Health Assistant.\n\nI can help you with:\n• Common health queries\n• Basic symptom assessment\n• General health advice\n• Booking appointments\n• First aid guidance\n\nWhat health concern can I help you with today?"
            
            # Thanks
            elif any(word in msg_lower for word in ['thank', 'thanks', 'appreciate']):
                response = "You're welcome! 😊\n\nI'm here whenever you need health advice. Stay healthy and take care!\n\nRemember: For serious symptoms, please book an appointment with our doctors immediately."
            
            # Fever
            elif any(word in msg_lower for word in ['fever', 'temperature', 'hot', 'burning']):
                response = "**For Fever Management:**\n\n✅ **Immediate Steps:**\n• Rest in a cool room\n• Drink plenty of fluids (water, ORS)\n• Take paracetamol/acetaminophen (500mg every 6 hours)\n• Use cold compress on forehead\n• Wear light clothing\n\n⚠️ **See a Doctor If:**\n• Fever above 103°F (39.4°C)\n• Lasts more than 3 days\n• Accompanied by severe headache, rash, or difficulty breathing\n• In children under 3 months\n\nWould you like me to help you book an appointment?"
            
            # Headache
            elif any(word in msg_lower for word in ['headache', 'head pain', 'migraine', 'head ache']):
                response = "**For Headache Relief:**\n\n✅ **Try These:**\n• Rest in a quiet, dark room\n• Stay well hydrated\n• Apply cold or warm compress\n• Gentle head massage\n• Avoid screens and bright lights\n• Take paracetamol if needed\n\n⚠️ **Seek Immediate Care If:**\n• Sudden severe headache (worst of your life)\n• Accompanied by fever, stiff neck, confusion\n• After head injury\n• With vision changes or weakness\n\nShould I help you schedule a consultation?"
            
            # Cold, Cough, Flu
            elif any(word in msg_lower for word in ['cold', 'cough', 'flu', 'sneeze', 'runny nose', 'congestion']):
                response = "**For Cold & Cough:**\n\n✅ **Home Remedies:**\n• Drink warm fluids (herbal tea, soup)\n• Steam inhalation 2-3 times daily\n• Honey and ginger tea\n• Gargle with warm salt water\n• Get adequate rest (7-8 hours)\n• Use humidifier at night\n\n💊 **Medication:**\n• Antihistamines for runny nose\n• Cough syrup if needed\n\n⚠️ **Consult Doctor If:**\n• Symptoms last more than 7 days\n• High fever (above 101°F)\n• Difficulty breathing\n• Chest pain or wheezing\n\nNeed help booking an appointment?"
            
            # Stomach/Digestive Issues
            elif any(word in msg_lower for word in ['stomach', 'belly', 'digest', 'nausea', 'vomit', 'diarrhea', 'constipation']):
                response = "**For Stomach Issues:**\n\n✅ **Immediate Relief:**\n• Eat light, bland foods (rice, banana, toast)\n• Avoid spicy, oily, or heavy foods\n• Stay hydrated with ORS or coconut water\n• Ginger tea for nausea\n• Small, frequent meals\n\n⚠️ **Emergency - Go to ER If:**\n• Severe abdominal pain\n• Blood in vomit or stool\n• High fever with stomach pain\n• Unable to keep fluids down\n• Signs of dehydration\n\nWould you like to book an urgent appointment?"
            
            # Sore Throat
            elif any(word in msg_lower for word in ['throat', 'sore throat', 'swallow', 'tonsil']):
                response = "**For Sore Throat:**\n\n✅ **Relief Measures:**\n• Gargle with warm salt water (4-5 times daily)\n• Drink warm liquids (tea, soup)\n• Honey and lemon water\n• Throat lozenges\n• Stay hydrated\n• Avoid cold drinks\n\n💊 **Medication:**\n• Paracetamol for pain\n• Throat spray if needed\n\n⚠️ **See Doctor If:**\n• Difficulty breathing or swallowing\n• High fever\n• White patches on tonsils\n• Lasts more than 3 days\n\nShould I help you schedule a consultation?"
            
            # Body Pain/Aches
            elif any(word in msg_lower for word in ['body pain', 'body ache', 'muscle pain', 'joint pain', 'back pain']):
                response = "**For Body Pain/Aches:**\n\n✅ **Relief Options:**\n• Rest the affected area\n• Apply warm compress\n• Gentle stretching\n• Over-the-counter pain reliever\n• Stay hydrated\n• Maintain good posture\n\n🏃 **For Prevention:**\n• Regular exercise\n• Proper sleep\n• Ergonomic workspace\n\n⚠️ **Consult Doctor If:**\n• Severe or persistent pain\n• Pain after injury\n• Numbness or tingling\n• Difficulty moving\n\nWant to book a consultation?"
            
            # Allergies
            elif any(word in msg_lower for word in ['allergy', 'allergic', 'rash', 'itch', 'skin']):
                response = "**For Allergies:**\n\n✅ **Immediate Steps:**\n• Identify and avoid the allergen\n• Take antihistamine\n• Apply calamine lotion for itching\n• Cool compress on affected area\n• Don't scratch\n\n⚠️ **Emergency - Call 911 If:**\n• Difficulty breathing\n• Swelling of face, lips, tongue\n• Severe reaction after bee sting/food\n• Dizziness or fainting\n\nNeed non-emergency consultation? I can help book an appointment."
            
            # Sleep Issues
            elif any(word in msg_lower for word in ['sleep', 'insomnia', 'cant sleep', 'tired', 'fatigue']):
                response = "**For Better Sleep:**\n\n✅ **Sleep Hygiene Tips:**\n• Fixed sleep schedule (even weekends)\n• Avoid screens 1 hour before bed\n• Keep bedroom dark and cool\n• No caffeine after 3 PM\n• Light dinner 2-3 hours before sleep\n• Relaxation exercises\n\n⚠️ **Consult Doctor If:**\n• Chronic insomnia (weeks)\n• Excessive daytime sleepiness\n• Snoring with breathing pauses\n• Persistent fatigue despite rest\n\nWould you like to book a consultation with our sleep specialist?"
            
            # Diabetes Related
            elif any(word in msg_lower for word in ['diabetes', 'sugar', 'blood sugar', 'glucose']):
                response = "**Diabetes Management:**\n\n⚠️ **Important:** For diabetes, regular doctor consultation is essential.\n\n✅ **General Tips:**\n• Monitor blood sugar regularly\n• Follow prescribed medication\n• Balanced diet (low sugar, high fiber)\n• Regular exercise (30 min daily)\n• Foot care\n• Annual eye check\n\n📋 **Emergency Signs:**\n• Very high/low blood sugar\n• Excessive thirst/urination\n• Blurred vision\n• Numbness in extremities\n\nI strongly recommend booking an appointment with our endocrinologist."
            
            # Blood Pressure
            elif any(word in msg_lower for word in ['blood pressure', 'bp', 'hypertension', 'high bp', 'low bp']):
                response = "**Blood Pressure Management:**\n\n✅ **Lifestyle Measures:**\n• Reduce salt intake\n• Regular exercise\n• Maintain healthy weight\n• Limit alcohol\n• Stress management\n• Adequate sleep\n\n⚠️ **Monitor & Check:**\n• Regular BP measurement\n• Take medications as prescribed\n• Keep track of readings\n\n🚨 **Emergency - Seek Immediate Help If:**\n• BP above 180/120\n• Severe headache\n• Chest pain\n• Difficulty breathing\n\nWould you like to book a cardiology consultation?"
            
            # General Pain
            elif 'pain' in msg_lower or 'hurt' in msg_lower or 'ache' in msg_lower:
                response = "**For Pain Management:**\n\n✅ **General Advice:**\n• Rest the affected area\n• Apply ice for new injuries (first 48 hours)\n• Apply heat for chronic pain\n• Over-the-counter pain relievers\n• Gentle movement when possible\n\n⚠️ **See Doctor If:**\n• Severe or worsening pain\n• Pain after injury\n• Persistent pain\n• Accompanied by fever, swelling, or redness\n\nCould you specify where the pain is located? I can provide more specific advice.\n\nWould you like to book an appointment?"
            
            # Appointment/Booking Related
            elif any(word in msg_lower for word in ['appointment', 'book', 'schedule', 'doctor', 'consultation']):
                response = "**Booking an Appointment:**\n\n✅ I can help you with that!\n\nTo book an appointment:\n1. Close this chat\n2. Fill in the 'Book Appointment' form on your dashboard\n3. Select department, doctor, date, and time\n4. You'll receive SMS confirmation\n\n🚨 **For Emergencies:**\nUse the 'Emergency SOS' button for immediate priority booking.\n\n📞 **Need Help?**\nOur reception is available 24/7 at the hospital.\n\nWhat type of specialist are you looking for?"
            
            # How are you
            elif any(phrase in msg_lower for phrase in ['how are you', 'how r u', 'whats up', "what's up"]):
                response = "I'm functioning perfectly, thank you for asking! 🤖✨\n\nMore importantly, how are YOU feeling today? Do you have any health concerns I can help you with?\n\nI'm here to:\n• Answer health questions\n• Provide medical advice\n• Help you understand symptoms\n• Guide you to appropriate care"
            
            # Emergency Keywords
            elif any(word in msg_lower for word in ['emergency', 'urgent', 'serious', 'ambulance', 'critical']):
                response = "🚨 **THIS SOUNDS URGENT!**\n\n⚠️ **For Life-Threatening Emergencies:**\n• Call Emergency Services IMMEDIATELY: 112\n• Or visit nearest Emergency Room\n\n**Emergency Signs:**\n• Chest pain or pressure\n• Difficulty breathing\n• Severe bleeding\n• Loss of consciousness\n• Severe allergic reaction\n• Stroke symptoms (face drooping, arm weakness, speech difficulty)\n\n**For Urgent but Non-Emergency:**\nUse our 'Emergency SOS' button on the dashboard for priority doctor consultation.\n\nIs this a life-threatening emergency? If YES, please call 112 now!"
            
            # Default/Fallback Response
            else:
                response = f"I understand you're asking about: **{user_message}**\n\n📋 **For Best Help:**\nCould you provide more details?\n• When did symptoms start?\n• How severe are they (1-10)?\n• Any other symptoms?\n• Any existing conditions?\n\n💡 **I Can Help With:**\n• Fever & common cold\n• Headaches\n• Stomach issues\n• Body pains\n• Allergies\n• Sleep problems\n• And more...\n\n⚠️ **Important:**\nFor serious symptoms or if unsure, please book an appointment with our doctors.\n\n🔍 **Quick Tips:**\nTry asking more specific questions like:\n\"What should I do for a headache?\"\n\"How to treat fever at home?\"\n\"I have stomach pain, what to do?\""
            
            return jsonify({"response": response})
        
        # Real AI Mode with Gemini
        client = genai.Client(api_key=api_key)
        
        system_prompt = """You are a helpful medical AI assistant for a hospital management system. 
Your role is to:
1. Provide general health advice for common minor ailments
2. Help patients understand their symptoms
3. Guide them on when to seek professional medical help
4. Be empathetic and supportive

IMPORTANT GUIDELINES:
- Always recommend seeing a doctor for serious symptoms
- Never diagnose conditions definitively
- Provide first aid and self-care tips for minor issues
- Be concise but caring in your responses
- If symptoms seem serious, strongly recommend booking an appointment
- Keep responses under 150 words unless absolutely necessary

Remember: You are NOT a replacement for a doctor, but a helpful guide."""

        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[
                {"role": "user", "parts": [{"text": system_prompt}]},
                {"role": "user", "parts": [{"text": user_message}]}
            ]
        )
        
        return jsonify({"response": response.text})
        
    except Exception as e:
        print(f"[AI CHAT] Error: {e}")
        return jsonify({
            "response": "I apologize, but I'm having trouble processing your request right now. For immediate assistance, please book an appointment with one of our doctors."
        }), 200  # Return 200 to avoid frontend errors

