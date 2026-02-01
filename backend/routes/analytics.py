from flask import Blueprint, jsonify, request
from database import get_db_connection
import datetime
from datetime import timedelta

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/dashboard', methods=['GET'])
def get_dashboard_analytics():
    """
    Provides comprehensive analytics data for admin dashboard visualizations
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.date.today()
    
    analytics = {}
    
    # ========== APPOINTMENT TRENDS (Last 7 Days) ==========
    dates = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    cursor.execute("""
        SELECT appointment_date, COUNT(*) as count 
        FROM appointments 
        WHERE appointment_date >= %s AND appointment_date <= %s
        GROUP BY appointment_date
        ORDER BY appointment_date ASC
    """, (dates[0], dates[-1]))
    
    appt_data = {row['appointment_date'].isoformat(): row['count'] for row in cursor.fetchall()}
    analytics['appointment_trends'] = {
        'labels': [d for d in dates],
        'data': [appt_data.get(d, 0) for d in dates]
    }
    
    # ========== APPOINTMENT STATUS DISTRIBUTION ==========
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM appointments 
        GROUP BY status
    """)
    status_data = cursor.fetchall()
    analytics['appointment_status'] = {
        'labels': [row['status'].capitalize() for row in status_data],
        'data': [row['count'] for row in status_data]
    }
    
    # ========== DEPARTMENT WORKLOAD (Appointments per Department) ==========
    cursor.execute("""
        SELECT dept.name, COUNT(a.id) as appointment_count
        FROM departments dept
        LEFT JOIN doctors d ON dept.id = d.department_id
        LEFT JOIN appointments a ON d.id = a.doctor_id
        GROUP BY dept.id, dept.name
        ORDER BY appointment_count DESC
    """)
    dept_data = cursor.fetchall()
    analytics['department_workload'] = {
        'labels': [row['name'] for row in dept_data],
        'data': [row['appointment_count'] for row in dept_data]
    }
    
    # ========== PATIENT GENDER DISTRIBUTION ==========
    cursor.execute("""
        SELECT gender, COUNT(*) as count 
        FROM patients 
        WHERE gender IS NOT NULL
        GROUP BY gender
    """)
    gender_data = cursor.fetchall()
    analytics['patient_gender'] = {
        'labels': [row['gender'] for row in gender_data],
        'data': [row['count'] for row in gender_data]
    }
    
    # ========== PATIENT AGE GROUPS ==========
    cursor.execute("""
        SELECT age_group, COUNT(*) as count
        FROM (
            SELECT 
                CASE 
                    WHEN age < 18 THEN 'Children (0-17)'
                    WHEN age BETWEEN 18 AND 35 THEN 'Young Adults (18-35)'
                    WHEN age BETWEEN 36 AND 55 THEN 'Adults (36-55)'
                    WHEN age > 55 THEN 'Seniors (55+)'
                    ELSE 'Unknown'
                END as age_group
            FROM patients
            WHERE age IS NOT NULL
        ) AS age_categories
        GROUP BY age_group
        ORDER BY 
            CASE 
                WHEN age_group = 'Children (0-17)' THEN 1
                WHEN age_group = 'Young Adults (18-35)' THEN 2
                WHEN age_group = 'Adults (36-55)' THEN 3
                WHEN age_group = 'Seniors (55+)' THEN 4
                ELSE 5
            END
    """)
    age_data = cursor.fetchall()
    analytics['patient_age_groups'] = {
        'labels': [row['age_group'] for row in age_data],
        'data': [row['count'] for row in age_data]
    }
    
    # ========== APPOINTMENT TYPE DISTRIBUTION ==========
    cursor.execute("""
        SELECT type, COUNT(*) as count 
        FROM appointments 
        GROUP BY type
    """)
    type_data = cursor.fetchall()
    analytics['appointment_types'] = {
        'labels': [row['type'].capitalize() for row in type_data],
        'data': [row['count'] for row in type_data]
    }
    
    # ========== REVENUE STATISTICS (Pharmacy Orders) ==========
    cursor.execute("""
        SELECT 
            DATE(created_at) as order_date,
            SUM(total_amount) as daily_revenue
        FROM orders
        WHERE created_at >= %s
        GROUP BY DATE(created_at)
        ORDER BY order_date ASC
    """, (dates[0],))
    
    revenue_data = {row['order_date'].isoformat(): float(row['daily_revenue']) for row in cursor.fetchall()}
    analytics['revenue_trends'] = {
        'labels': dates,
        'data': [revenue_data.get(d, 0) for d in dates]
    }
    
    # ========== TOTAL REVENUE ==========
    cursor.execute("SELECT SUM(total_amount) as total FROM orders")
    total_rev = cursor.fetchone()
    analytics['total_revenue'] = float(total_rev['total']) if total_rev['total'] else 0
    
    # ========== TOP PERFORMING DOCTORS (by appointment count) ==========
    cursor.execute("""
        SELECT d.full_name, COUNT(a.id) as appointment_count
        FROM doctors d
        LEFT JOIN appointments a ON d.id = a.doctor_id
        GROUP BY d.id, d.full_name
        ORDER BY appointment_count DESC
        LIMIT 5
    """)
    top_doctors = cursor.fetchall()
    analytics['top_doctors'] = {
        'labels': [row['full_name'] for row in top_doctors],
        'data': [row['appointment_count'] for row in top_doctors]
    }
    
    # ========== MEDICINE STOCK ALERTS (Low Stock) ==========
    cursor.execute("""
        SELECT name, stock_quantity, department_id
        FROM medicines
        WHERE stock_quantity < 50
        ORDER BY stock_quantity ASC
        LIMIT 10
    """)
    low_stock = cursor.fetchall()
    analytics['low_stock_medicines'] = {
        'labels': [row['name'] for row in low_stock],
        'data': [row['stock_quantity'] for row in low_stock]
    }
    
    # ========== RECENT REGISTRATIONS (Last 30 Days) ==========
    thirty_days_ago = (today - timedelta(days=30)).isoformat()
    cursor.execute("""
        SELECT DATE(created_at) as reg_date, COUNT(*) as count
        FROM users
        WHERE created_at >= %s
        GROUP BY DATE(created_at)
        ORDER BY reg_date ASC
    """, (thirty_days_ago,))
    
    reg_data_raw = cursor.fetchall()
    reg_dates = [(today - timedelta(days=i)).isoformat() for i in range(29, -1, -1)]
    reg_data = {row['reg_date'].isoformat(): row['count'] for row in reg_data_raw}
    
    analytics['user_registrations'] = {
        'labels': reg_dates,
        'data': [reg_data.get(d, 0) for d in reg_dates]
    }
    
    conn.close()
    return jsonify(analytics)


@analytics_bp.route('/summary', methods=['GET'])
def get_summary_stats():
    """
    Provides quick summary statistics for KPI cards
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.date.today()
    
    summary = {}
    
    # Total counts
    cursor.execute("SELECT COUNT(*) as count FROM doctors")
    summary['total_doctors'] = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM patients")
    summary['total_patients'] = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM appointments")
    summary['total_appointments'] = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE appointment_date = %s", (today.isoformat(),))
    summary['today_appointments'] = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(total_amount) as total FROM orders")
    total_rev = cursor.fetchone()
    summary['total_revenue'] = float(total_rev['total']) if total_rev['total'] else 0
    
    cursor.execute("SELECT COUNT(*) as count FROM departments")
    summary['total_departments'] = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM medicines WHERE stock_quantity < 50")
    summary['low_stock_count'] = cursor.fetchone()['count']
    
    # Pending appointments
    cursor.execute("SELECT COUNT(*) as count FROM appointments WHERE status = 'pending'")
    summary['pending_appointments'] = cursor.fetchone()['count']
    
    conn.close()
    return jsonify(summary)
