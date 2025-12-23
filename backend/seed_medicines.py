
import pymysql
import random
from database import get_db_connection

# Department list
departments = ['Cardiology', 'Neurology', 'Orthopedics', 'Pediatrics', 'General Medicine', 'Dermatology', 'Dental', 'Gynaecology']

# Sample data for generation
medicine_prefixes = {
    'Cardiology': ['Cardio', 'Heart', 'Press', 'Vasc', 'Pulse', 'Beat', 'Aort', 'Cor', 'Vent', 'Atri'],
    'Neurology': ['Neuro', 'Brain', 'Ceph', 'Synap', 'Dend', 'Cereb', 'MIND', 'Neur', 'Axon', 'Lob'],
    'Orthopedics': ['Bone', 'Joint', 'Flex', 'Osteo', 'Skel', 'Vert', 'Spine', 'Cart', 'Mob', 'Strut'],
    'Pediatrics': ['Kiddy', 'Child', 'Grow', 'Ped', 'Infant', 'Tot', 'Jun', 'Neo', 'Baby', 'Sml'],
    'General Medicine': ['Cure', 'Heal', 'Pan', 'Gen', 'Med', 'Health', 'Life', 'Vit', 'Bio', 'Rem'],
    'Dermatology': ['Derm', 'Skin', 'Glow', 'Epi', 'Cut', 'Rash', 'Spot', 'Clear', 'Soft', 'Pore'],
    'Dental': ['Dent', 'Tooth', 'Gum', 'Smile', 'Brite', 'Oral', 'Molar', 'Canine', 'Root', 'Fil'],
    'Gynaecology': ['Fem', 'Gyn', 'Natal', 'Ov', 'Repro', 'Mat', 'Wom', 'Cycle', 'Estro', 'Gest']
}

medicine_suffixes = ['mol', 'prin', 'tatin', 'zole', 'line', 'cillin', 'fen', 'dine', 'sine', 'mine']

descriptions = [
    "Effective for mild symptoms.",
    "Fast acting relief.",
    "Prescribed for chronic conditions.",
    "Daily supplement.",
    "High potency formula.",
    "Extended release tablets.",
    "Liquid suspension.",
    "Topical application.",
    "Chewable tablets.",
    "Intravenous solution."
]

def generate_medicines():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get Department IDs
        dept_map = {}
        for d in departments:
            cursor.execute("SELECT id FROM departments WHERE name = %s", (d,))
            res = cursor.fetchone()
            if res:
                dept_map[d] = res['id']
            else:
                print(f"Warning: Department {d} not found.")

        # Seed 20 medicines for each dept
        for dept_name, dept_id in dept_map.items():
            print(f"Seeding {dept_name}...")
            
            # Check existing count
            cursor.execute("SELECT COUNT(*) as c FROM medicines WHERE department_id = %s", (dept_id,))
            count = cursor.fetchone()['c']
            
            medicines_to_add = 20 - count
            if medicines_to_add <= 0:
                print(f"  Already has {count} medicines. Skipping.")
                continue

            prefixes = medicine_prefixes.get(dept_name, ['Med'])
            
            for i in range(medicines_to_add):
                name = f"{random.choice(prefixes)}{random.choice(medicine_suffixes)} {random.randint(10, 500)}mg"
                desc = random.choice(descriptions)
                price = round(random.uniform(10.0, 500.0), 2)
                stock = random.randint(50, 500)
                image_url = f"https://placehold.co/300x200?text={name.replace(' ', '+')}"
                
                cursor.execute("""
                    INSERT INTO medicines (department_id, name, description, price, stock_quantity, image_url)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (dept_id, name, desc, price, stock, image_url))
                
        print("Seeding complete.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    generate_medicines()
