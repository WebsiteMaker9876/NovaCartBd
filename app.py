import os
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'novacart_secret_key_2026'

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'novacart.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # Categories Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        ''')
        
        # Products Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                name TEXT NOT NULL,
                regular_price REAL NOT NULL,
                sale_price REAL NOT NULL,
                category TEXT NOT NULL,
                image TEXT,
                description TEXT
            )
        ''')
        
        # Orders Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                delivery_area TEXT NOT NULL,
                delivery_charge REAL NOT NULL,
                items_summary TEXT NOT NULL,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'Pending',
                order_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            sample_products = [
                ("3622", "Electric Small Duck Climbing Stairs Toy", 1290.0, 850.0, "Toys", "https://images.unsplash.com/photo-1531651008558-ed1740375b39?w=500", "সারা বাংলাদেশে ক্যাশ অন ডেলিভারিতে অর্ডার করুন আপনার পছন্দের ট্রেন্ডি টয়।"),
                ("10220", "16-in-1 Multifunctional Vegetable Chopper", 1190.0, 890.0, "Kitchen & Dining", "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?w=500", "Professional Kitchen Food Cutter with Stainless Steel Blades."),
                ("7019", "Nylon Backpack Durable Waterproof Casual Shoulder Bag", 1150.0, 850.0, "Womens Bags", "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500", "Durable Waterproof Casual Shoulder Bag (Black)."),
                ("4875", "Curren 8402 Chronograph Men's Watch", 1290.0, 850.0, "Watches", "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500", "Stylish Chronograph Men's Watch."),
                ("12523", "Anker TWS AC-100 Buds Pro", 1190.0, 790.0, "Gadgets & Electronics", "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500", "Hi-Res Audio Certified True Wireless Earbuds.")
            ]
            cursor.executemany("INSERT INTO products (code, name, regular_price, sale_price, category, image, description) VALUES (?, ?, ?, ?, ?, ?, ?)", sample_products)
            
            categories = [("Toys",), ("Kitchen & Dining",), ("Womens Bags",), ("Baby Toy",), ("Skin Care",), ("Makeup",), ("Watches",), ("Gadgets & Electronics",)]
            cursor.executemany("INSERT INTO categories (name) VALUES (?)", categories)
            conn.commit()

init_db()

@app.route('/')
def index():
    cat = request.args.get('category')
    with get_db() as conn:
        categories = conn.execute("SELECT * FROM categories").fetchall()
        if cat:
            products = conn.execute("SELECT * FROM products WHERE category = ?", (cat,)).fetchall()
        else:
            products = conn.execute("SELECT * FROM products").fetchall()
    return render_template('index.html', products=products, categories=categories, current_cat=cat)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    with get_db() as conn:
        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        related = conn.execute("SELECT * FROM products WHERE category = ? AND id != ? LIMIT 3", (product['category'], product_id)).fetchall()
    return render_template('product_detail.html', product=product, related=related)

@app.route('/quick_order/<int:product_id>', methods=['POST'])
def quick_order(product_id):
    name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    area = request.form.get('area')
    
    charge_map = {
        'dhaka_inside': 60.0,
        'dhaka_sub': 100.0,
        'outside_dhaka': 120.0
    }
    charge_name_map = {
        'dhaka_inside': 'ঢাকা সিটি (৬০ টাকা)',
        'dhaka_sub': 'ঢাকা সাব এরিয়া (১০০ টাকা)',
        'outside_dhaka': 'ঢাকার বাইরে (১২০ টাকা)'
    }
    
    delivery_charge = charge_map.get(area, 60.0)
    area_display = charge_name_map.get(area, 'ঢাকা সিটি (৬০ টাকা)')
    
    with get_db() as conn:
        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if not product:
            return redirect(url_for('index'))
            
        total = product['sale_price'] + delivery_charge
        items_summary = f"{product['name']} (কোড: {product['code']})"
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (customer_name, phone, address, delivery_area, delivery_charge, items_summary, total_price) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, phone, address, area_display, delivery_charge, items_summary, total)
        )
        conn.commit()
        order_id = cursor.lastrowid
        
    return render_template('order_success.html', order_id=order_id, name=name, phone=phone, address=address, product=product, total=total, charge=delivery_charge)

@app.route('/track', methods=['GET', 'POST'])
def track_order():
    order = None
    searched = False
    if request.method == 'POST':
        searched = True
        query = request.form.get('query')
        with get_db() as conn:
            order = conn.execute("SELECT * FROM orders WHERE id = ? OR phone = ?", (query, query)).fetchone()
    return render_template('track.html', order=order, searched=searched)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_product':
            code = request.form.get('code')
            name = request.form.get('name')
            regular_price = float(request.form.get('regular_price'))
            sale_price = float(request.form.get('sale_price'))
            category = request.form.get('category')
            image = request.form.get('image')
            description = request.form.get('description')
            
            with get_db() as conn:
                conn.execute("INSERT INTO products (code, name, regular_price, sale_price, category, image, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (code, name, regular_price, sale_price, category, image, description))
                conn.commit()
        elif action == 'add_category':
            cat_name = request.form.get('cat_name')
            with get_db() as conn:
                conn.execute("INSERT INTO categories (name) VALUES (?)", (cat_name,))
                conn.commit()
        return redirect(url_for('admin'))
        
    with get_db() as conn:
        products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        categories = conn.execute("SELECT * FROM categories").fetchall()
    return render_template('admin.html', products=products, orders=orders, categories=categories)

@app.route('/admin/delete_product/<int:product_id>')
def delete_product(product_id):
    with get_db() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
    return redirect(url_for('admin'))

@app.route('/admin/update_order/<int:order_id>/<string:status>')
def update_order_status(order_id, status):
    with get_db() as conn:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        conn.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
