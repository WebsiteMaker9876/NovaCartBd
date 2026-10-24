import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'novacartbd_secret_key_2026')

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text or 'product'

def init_db():
    conn = get_db_connection()
    
    # Products Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            category TEXT,
            regular_price REAL,
            sale_price REAL NOT NULL,
            main_image_url TEXT,
            features TEXT,
            description TEXT
        )
    ''')

    # Product Images Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS product_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            image_url TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    # Orders Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_address TEXT NOT NULL,
            shipping_area TEXT NOT NULL,
            total_amount REAL NOT NULL,
            product_name TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Site Settings Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS site_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_name TEXT DEFAULT 'NovaCart BD',
            tagline TEXT DEFAULT 'Shop Smart, Live Better',
            header_banner_url TEXT,
            notice_text TEXT,
            phone TEXT DEFAULT '01700000000',
            whatsapp TEXT DEFAULT '01700000000',
            logo_url TEXT,
            google_site_verification TEXT,
            google_adsense_code TEXT,
            fb_pixel_id TEXT
        )
    ''')

    # Default Settings
    settings = conn.execute('SELECT * FROM site_settings WHERE id = 1').fetchone()
    if not settings:
        conn.execute('''
            INSERT INTO site_settings (id, site_name, tagline, notice_text, google_adsense_code)
            VALUES (1, 'NovaCart BD', 'Shop Smart, Live Better', 'সারা বাংলাদেশে ক্যাশ অন ডেলিভারি দেওয়া হয়!', '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1619234614836027" crossorigin="anonymous"></script>')
        ''')

    conn.commit()
    conn.close()

# Initialize Database
init_db()

# Context Processor for Global Variables
@app.context_processor
def inject_globals():
    conn = get_db_connection()
    site_settings = conn.execute('SELECT * FROM site_settings WHERE id = 1').fetchone()
    conn.close()
    return dict(site_settings=site_settings)

# Context Processor for Math in Templates
@app.template_filter('discount_percent')
def discount_percent_filter(regular, sale):
    if regular and regular > sale:
        return int(((regular - sale) / regular) * 100)
    return 0

# --- ROUTES ---

@app.route('/')
def home():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    
    # Calculate discount percents dynamically for products
    processed_products = []
    for p in products:
        p_dict = dict(p)
        reg = p_dict.get('regular_price')
        sale = p_dict.get('sale_price')
        if reg and reg > sale:
            p_dict['discount_percent'] = int(((reg - sale) / reg) * 100)
        else:
            p_dict['discount_percent'] = 0
        processed_products.append(p_dict)

    conn.close()
    return render_template('index.html', products=processed_products)

@app.route('/landing/<slug>')
def landing_page(slug):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE slug = ?', (slug,)).fetchone()
    
    if not product:
        # Fallback search by ID or Code if slug mismatch
        product = conn.execute('SELECT * FROM products WHERE product_code = ?', (slug,)).fetchone()

    if not product:
        conn.close()
        return redirect(url_for('home'))
    
    product_dict = dict(product)
    reg = product_dict.get('regular_price')
    sale = product_dict.get('sale_price')
    if reg and reg > sale:
        product_dict['discount_percent'] = int(((reg - sale) / reg) * 100)
    else:
        product_dict['discount_percent'] = 0

    gallery_images = conn.execute('SELECT * FROM product_images WHERE product_id = ?', (product['id'],)).fetchall()
    conn.close()
    
    features = product['features'].split('|') if product['features'] else []
    
    return render_template('landing_page.html', product=product_dict, gallery_images=gallery_images, features=features)

@app.route('/submit-order', methods=['POST'])
def submit_order():
    product_id = request.form.get('product_id')
    customer_name = request.form.get('customer_name')
    customer_phone = request.form.get('customer_phone')
    customer_address = request.form.get('customer_address')
    shipping_area = request.form.get('shipping_area')

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    if not product:
        conn.close()
        return "Invalid Product", 400

    shipping_charge = 60 if shipping_area == 'inside_dhaka' else 120
    total_amount = product['sale_price'] + shipping_charge
    order_id = f"NC-{conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0] + 1001}"

    conn.execute('''
        INSERT INTO orders (order_id, customer_name, customer_phone, customer_address, shipping_area, total_amount, product_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, customer_name, customer_phone, customer_address, shipping_area, total_amount, product['name']))

    conn.commit()
    conn.close()

    return render_template('order_success.html', order_id=order_id, total_amount=total_amount, customer_name=customer_name)

# Legal Pages Routes
@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/refund-policy')
def refund_policy():
    return render_template('refund_policy.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/track')
def track():
    return render_template('track.html')

if __name__ == '__main__':
    app.run(debug=True)
