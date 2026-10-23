import os
import sqlite3
import re
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'novacart_pro_landing_secret_key_2026'

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'novacart_pro.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def generate_slug(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                icon TEXT DEFAULT 'fa-tags'
            )
        ''')
        
        # Extended Products Table with Slug and Gallery Images
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                slug TEXT UNIQUE,
                name TEXT NOT NULL,
                regular_price REAL NOT NULL,
                sale_price REAL NOT NULL,
                category TEXT NOT NULL,
                image TEXT,
                gallery_images TEXT,
                features TEXT,
                description TEXT,
                is_new INTEGER DEFAULT 0,
                is_top INTEGER DEFAULT 0
            )
        ''')
        
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
        default_settings = {
            'site_name': 'NovaCart BD',
            'tagline': 'Shop Smart, Live Better',
            'logo_url': '',
            'header_banner_url': 'https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?w=1200&q=80',
            'banner_link': '#',
            'phone': '+880 1568-022033',
            'whatsapp': '+880 1568-022033',
            'fb_pixel_id': '',
            'admin_password': 'admin123#novacart',
            'notice_text': '🚀 ক্যাশ অন ডেলিভারি সারা বাংলাদেশে! ৩ দিনের মধ্যে নিশ্চিত রিটার্ন পলিসি।'
        }
        
        for key, val in default_settings.items():
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
            
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            sample_products = [
                ("NC-3622", "electric-duck-climbing-stairs-toy", "Electric Small Duck Climbing Stairs Toy", 1290.0, 850.0, "Toys", 
                 "https://images.unsplash.com/photo-1531651008558-ed1740375b39?w=800", 
                 "https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?w=800,https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?w=800,https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?w=800",
                 "বাচ্চাদের আকর্ষনীয় মিউজিক ও লাইটিং|স্বয়ংক্রিয় সিঁড়ি বেয়ে ওঠার মজার খেলা|১০০% সেইফ ও প্রিমিয়াম প্লাস্টিক উপাদান|ব্যাটারি চালিত ও অত্যন্ত টেকসই",
                 "সারা বাংলাদেশে ক্যাশ অন ডেলিভারিতে অর্ডার করুন আপনার বাচ্চার জন্য সেরা উপহার ট্রেন্ডি ডাক ক্লাইম্বিং টয়। এটি বাচ্চাদের মনোযোগ ও বুদ্ধি বৃদ্ধিতে সাহায্য করে।", 1, 1),
                
                ("NC-10220", "16-in-1-multifunctional-vegetable-chopper", "16-in-1 Multifunctional Vegetable Chopper", 1190.0, 890.0, "Kitchen & Dining", 
                 "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?w=800", 
                 "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=800,https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800",
                 "১৬টি ভিন্ন ধরনের কাটিং ও চপিং ব্লেড|স্টেইনলেস স্টিল মরিচারোধী ব্লেড|সহজে পরিষ্কারযোগ্য ও ডিশওয়াশার সেফ|রান্নার সময় বাঁচায় ৭০%",
                 "Professional Kitchen Food Cutter with Stainless Steel Blades. আপনার রান্নাঘরের নিত্যদিনের কাজকে করুন সহজ ও দ্রুত।", 1, 1),

                ("NC-12523", "anker-tws-ac-100-buds-pro-earbuds", "Anker TWS AC-100 Buds Pro Earbuds", 1190.0, 790.0, "Gadgets & Electronics", 
                 "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=800", 
                 "https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?w=800,https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800",
                 "হাই রেস ক্রিস্টাল ক্লিয়ার সাউন্ড|এক চার্জে ৩০ ঘণ্টা ব্যাটারি ব্যাকআপ|একটিভ নয়েজ ক্যানসেলেশন (ANC)|ওয়াটারপ্রুফ IPX7 রেটিং",
                 "Hi-Res Audio Certified True Wireless Earbuds. গান শোনা বা গেমিংয়ের জন্য সেরা সাউন্ড অভিজ্ঞতা।", 1, 1)
            ]
            cursor.executemany("INSERT INTO products (code, slug, name, regular_price, sale_price, category, image, gallery_images, features, description, is_new, is_top) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_products)
            
            categories = [
                ("Toys", "fa-robot"),
                ("Kitchen & Dining", "fa-utensils"),
                ("Womens Bags", "fa-bag-shopping"),
                ("Baby Toy", "fa-child"),
                ("Skin Care", "fa-pump-soap"),
                ("Makeup", "fa-wand-magic-sparkles"),
                ("Watches", "fa-clock"),
                ("Gadgets & Electronics", "fa-laptop")
            ]
            cursor.executemany("INSERT INTO categories (name, icon) VALUES (?, ?)", categories)
            
        conn.commit()

init_db()

def get_settings():
    with get_db() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {row['key']: row['value'] for row in rows}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_global_vars():
    return dict(site_settings=get_settings())

@app.route('/')
def index():
    cat = request.args.get('category')
    settings = get_settings()
    with get_db() as conn:
        categories = conn.execute("SELECT * FROM categories").fetchall()
        if cat:
            products = conn.execute("SELECT * FROM products WHERE category = ? ORDER BY id DESC", (cat,)).fetchall()
        else:
            products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
                
    return render_template('index.html', products=products, categories=categories, current_cat=cat, settings=settings)

# High-Converting Custom Landing Page Route via Product Slug
@app.route('/p/<slug>')
def product_landing(slug):
    settings = get_settings()
    with get_db() as conn:
        product = conn.execute("SELECT * FROM products WHERE slug = ?", (slug,)).fetchone()
        if not product:
            # Fallback check by ID if numeric passed
            if slug.isdigit():
                product = conn.execute("SELECT * FROM products WHERE id = ?", (int(slug),)).fetchone()
            if not product:
                return redirect(url_for('index'))
        
        gallery = []
        if product['gallery_images']:
            gallery = [img.strip() for img in product['gallery_images'].split(',') if img.strip()]
        
        features = []
        if product['features']:
            features = [f.strip() for f in product['features'].split('|') if f.strip()]
            
        related = conn.execute("SELECT * FROM products WHERE category = ? AND id != ? LIMIT 4", (product['category'], product['id'])).fetchall()
        
    return render_template('landing_page.html', product=product, gallery=gallery, features=features, related=related, settings=settings)

@app.route('/quick_order/<int:product_id>', methods=['POST'])
def quick_order(product_id):
    name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    area = request.form.get('area')
    
    charge_map = {'dhaka_inside': 60.0, 'dhaka_sub': 100.0, 'outside_dhaka': 120.0}
    charge_name_map = {'dhaka_inside': 'ঢাকা সিটি (৬০ টাকা)', 'dhaka_sub': 'ঢাকা সাব এরিয়া (১০০ টাকা)', 'outside_dhaka': 'ঢাকার বাইরে (১২০ টাকা)'}
    
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

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password_input = request.form.get('password')
        settings = get_settings()
        if password_input == settings.get('admin_password', 'admin123#novacart'):
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('ভুল পাসওয়ার্ড দেওয়া হয়েছে!', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        action = request.form.get('action')
        with get_db() as conn:
            if action == 'add_product':
                code = request.form.get('code')
                name = request.form.get('name')
                slug = generate_slug(name)
                regular_price = float(request.form.get('regular_price'))
                sale_price = float(request.form.get('sale_price'))
                category = request.form.get('category')
                image = request.form.get('image')
                gallery_images = request.form.get('gallery_images')
                features = request.form.get('features')
                description = request.form.get('description')
                is_new = 1 if request.form.get('is_new') else 0
                is_top = 1 if request.form.get('is_top') else 0
                
                conn.execute("INSERT INTO products (code, slug, name, regular_price, sale_price, category, image, gallery_images, features, description, is_new, is_top) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                             (code, slug, name, regular_price, sale_price, category, image, gallery_images, features, description, is_new, is_top))
                conn.commit()
                flash('প্রডাক্ট ও ল্যান্ডিং পেজ সফলভাবে যুক্ত করা হয়েছে!', 'success')
                
            elif action == 'add_category':
                cat_name = request.form.get('cat_name')
                icon = request.form.get('icon', 'fa-tags')
                conn.execute("INSERT INTO categories (name, icon) VALUES (?, ?)", (cat_name, icon))
                conn.commit()
                flash('ক্যাটাগরি যুক্ত করা হয়েছে!', 'success')
                
            elif action == 'update_settings':
                fields = ['site_name', 'tagline', 'logo_url', 'header_banner_url', 'banner_link', 'phone', 'whatsapp', 'fb_pixel_id', 'admin_password', 'notice_text']
                for field in fields:
                    val = request.form.get(field, '')
                    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (field, val))
                conn.commit()
                flash('ওয়েবসাইট সেটিংস সফলভাবে সেভ করা হয়েছে!', 'success')
                
        return redirect(url_for('admin'))
        
    with get_db() as conn:
        products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        categories = conn.execute("SELECT * FROM categories").fetchall()
    return render_template('admin.html', products=products, orders=orders, categories=categories, settings=get_settings())

@app.route('/admin/delete_product/<int:product_id>')
@login_required
def delete_product(product_id):
    with get_db() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
    flash('প্রডাক্ট মুছে ফেলা হয়েছে!', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/update_order/<int:order_id>/<string:status>')
@login_required
def update_order_status(order_id, status):
    with get_db() as conn:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        conn.commit()
    flash('অর্ডার স্ট্যাটাস আপডেট করা হয়েছে!', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
