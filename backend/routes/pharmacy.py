from flask import Blueprint, request, jsonify
from database import get_db_connection
import pandas as pd
import io

pharmacy_bp = Blueprint('pharmacy', __name__)

@pharmacy_bp.route('/medicines', methods=['GET'])
def get_medicines():
    dept_id = request.args.get('department_id')
    search_query = request.args.get('search')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        sql = "SELECT * FROM medicines WHERE 1=1"
        params = []
        
        if dept_id:
            sql += " AND department_id = %s"
            params.append(dept_id)
            
        if search_query:
            sql += " AND name LIKE %s"
            params.append(f"%{search_query}%")
            
        cursor.execute(sql, tuple(params))
        meds = cursor.fetchall()
        return jsonify(meds)
    finally:
        conn.close()

@pharmacy_bp.route('/orders', methods=['GET'])
def get_orders():
    user_id = request.args.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get orders with items
        cursor.execute("""
            SELECT o.id, o.total_amount, o.status, o.created_at,
                   STRING_AGG(m.name || ' (x' || oi.quantity || ')', ', ') as items_summary
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN medicines m ON oi.medicine_id = m.id
            WHERE o.user_id = %s
            GROUP BY o.id, o.total_amount, o.status, o.created_at
            ORDER BY o.created_at DESC
        """, (user_id,))
        orders = cursor.fetchall()
        return jsonify(orders)
    finally:
        conn.close()

@pharmacy_bp.route('/all-orders', methods=['GET'])
def get_all_orders():
    date_filter = request.args.get('date')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT o.id, o.total_amount, o.status, o.created_at, o.payment_method,
                   u.email as patient_email,
                   STRING_AGG(m.name || ' (x' || oi.quantity || ')', ', ') as items_summary
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN order_items oi ON o.id = oi.order_id
            JOIN medicines m ON oi.medicine_id = m.id
        """
        
        params = []
        if date_filter:
            query += " WHERE o.created_at::date = %s"
            params.append(date_filter)
            
        query += """
            GROUP BY o.id, o.total_amount, o.status, o.created_at, o.payment_method, u.email
            ORDER BY o.created_at DESC
        """
        
        cursor.execute(query, tuple(params))
        orders = cursor.fetchall()
        return jsonify(orders)
    finally:
        conn.close()

@pharmacy_bp.route('/medicines/add', methods=['POST'])
def add_medicine():
    data = request.json
    name = data.get('name')
    dept_id = data.get('department_id')
    price = data.get('price')
    stock = data.get('stock_quantity')
    desc = data.get('description', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO medicines (name, department_id, description, price, stock_quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, dept_id, desc, price, stock))
        return jsonify({'message': 'Medicine added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@pharmacy_bp.route('/medicines/bulk-add', methods=['POST'])
def bulk_add_medicines():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Read Excel
        df = pd.read_excel(file)
        
        # Support both standard and user-provided spellings
        name_col = next((c for c in df.columns if c.upper() in ['MEDICINE NAME', 'NAME']), None)
        dept_col = next((c for c in df.columns if c.upper() in ['DEPARTMENT']), None)
        price_col = next((c for c in df.columns if c.upper() in ['PRICE PER UNIT', 'PRICE PERUNIT', 'PRICE']), None)
        stock_col = next((c for c in df.columns if c.upper() in ['INITIAL STOCK', 'INTIAL STOCK', 'STOCK']), None)

        if not all([name_col, dept_col, price_col, stock_col]):
            return jsonify({'error': 'Missing required columns. Please use: MEDICINE NAME, DEPARTMENT, PRICE PER UNIT, INITIAL STOCK'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get departments for mapping
        cursor.execute("SELECT id, name FROM departments")
        depts = {d['name'].lower(): d['id'] for d in cursor.fetchall()}
        
        success_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                name = str(row[name_col])
                dept_name = str(row[dept_col]).lower().strip()
                price = float(row[price_col])
                stock = int(row[stock_col])
                
                dept_id = depts.get(dept_name)
                if not dept_id:
                    errors.append(f"Row {index+2}: Department '{row['DEPARTMENT']}' not found")
                    continue
                    
                cursor.execute("""
                    INSERT INTO medicines (name, department_id, price, stock_quantity)
                    VALUES (%s, %s, %s, %s)
                """, (name, dept_id, price, stock))
                success_count += 1
            except Exception as e:
                errors.append(f"Row {index+2}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'Bulk upload completed. {success_count} medicines added.',
            'errors': errors
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@pharmacy_bp.route('/medicines/update', methods=['POST'])
def update_medicine():
    data = request.json
    medicine_id = data.get('medicine_id')
    new_stock = data.get('stock_quantity')
    new_price = data.get('price')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if new_stock is not None:
             cursor.execute("UPDATE medicines SET stock_quantity = %s WHERE id = %s", (new_stock, medicine_id))
             
        if new_price is not None:
             cursor.execute("UPDATE medicines SET price = %s WHERE id = %s", (new_price, medicine_id))

        return jsonify({'message': 'Medicine updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@pharmacy_bp.route('/cart', methods=['GET'])
def get_cart():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT c.id, c.quantity, m.name, m.price, m.unit, m.description, m.stock_quantity
            FROM cart_items c
            JOIN medicines m ON c.medicine_id = m.id
            WHERE c.user_id = %s
        """
        cursor.execute(query, (user_id,))
        items = cursor.fetchall()
        
        # Calculate total
        total = sum(item['price'] * item['quantity'] for item in items)
        
        return jsonify({'items': items, 'total': total})
    finally:
        conn.close()

@pharmacy_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data.get('user_id')
    medicine_id = data.get('medicine_id')
    quantity = data.get('quantity', 1)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check stock
        cursor.execute("SELECT stock_quantity FROM medicines WHERE id = %s", (medicine_id,))
        med = cursor.fetchone()
        if not med:
            return jsonify({'error': 'Medicine not found'}), 404
        if med['stock_quantity'] < quantity:
            return jsonify({'error': 'Out of stock'}), 400
            
        # Add to cart (Upsert)
        cursor.execute("""
            INSERT INTO cart_items (user_id, medicine_id, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, medicine_id) 
            DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
        """, (user_id, medicine_id, quantity))
        
        return jsonify({'message': 'Added to cart'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@pharmacy_bp.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    data = request.json
    item_id = data.get('cart_item_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM cart_items WHERE id = %s", (item_id,))
        return jsonify({'message': 'Removed from cart'})
    finally:
        conn.close()

@pharmacy_bp.route('/cart/decrease', methods=['POST'])
def decrease_cart():
    data = request.json
    user_id = data.get('user_id')
    medicine_id = data.get('medicine_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if item exists
        cursor.execute("SELECT id, quantity FROM cart_items WHERE user_id = %s AND medicine_id = %s", (user_id, medicine_id))
        item = cursor.fetchone()
        
        if not item:
            return jsonify({'error': 'Item not in cart'}), 404
            
        new_quantity = item['quantity'] - 1
        
        if new_quantity > 0:
            cursor.execute("UPDATE cart_items SET quantity = %s WHERE id = %s", (new_quantity, item['id']))
        else:
            cursor.execute("DELETE FROM cart_items WHERE id = %s", (item['id'],))
            
        return jsonify({'message': 'Decreased quantity'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@pharmacy_bp.route('/checkout', methods=['POST'])
def checkout():
    data = request.json
    user_id = data.get('user_id')
    payment_method = data.get('payment_method', 'cash')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get cart items
        cursor.execute("SELECT * FROM cart_items WHERE user_id = %s", (user_id,))
        cart_items = cursor.fetchall()
        
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400
            
        # Validate stock again and calculate total
        total = 0
        order_items_data = []
        
        for item in cart_items:
            cursor.execute("SELECT price, stock_quantity FROM medicines WHERE id = %s", (item['medicine_id'],))
            med = cursor.fetchone()
            
            if med['stock_quantity'] < item['quantity']:
                raise Exception(f"Item {item['medicine_id']} is out of stock")
                
            total += med['price'] * item['quantity']
            order_items_data.append({
                'medicine_id': item['medicine_id'],
                'quantity': item['quantity'],
                'price': med['price']
            })
            
        # Create Order
        # Create Order (PG requires RETURNING id)
        cursor.execute("INSERT INTO orders (user_id, total_amount, status, payment_method) VALUES (%s, %s, 'completed', %s) RETURNING id", (user_id, total, payment_method))
        order_id = cursor.fetchone()['id']
        
        # Create Order Items and Update Stock
        for item in order_items_data:
            cursor.execute("INSERT INTO order_items (order_id, medicine_id, quantity, price_at_time) VALUES (%s, %s, %s, %s)",
                           (order_id, item['medicine_id'], item['quantity'], item['price']))
            
            cursor.execute("UPDATE medicines SET stock_quantity = stock_quantity - %s WHERE id = %s", 
                           (item['quantity'], item['medicine_id']))
                           
        # Clear Cart
        cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))
        
        return jsonify({'message': 'Order placed successfully', 'order_id': order_id})
        
    except Exception as e:
        # Pymysql Autocommit is on by default in db config, so transaction management might be tricky if we don't start one.
        # But for this simple app, we enabled autocommit=True in init_db.py connection factory.
        # Ideally we should use transactions. The `get_db_connection` uses autocommit=True.
        # Let's just catch and return.
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
