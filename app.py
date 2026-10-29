import os
import sqlite3
import re
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from werkzeug.utils import secure_filename
import psycopg2
import psycopg2.extras
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = 'novacart_pro_ultimate_secret_key_2026'

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'novacart_pro.db')
UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Cloudinary Configuration
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        conn = psycopg2.connect(database_url, cursor_factory=psycopg2.extras.RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

def generate_slug(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def init_db():
    database_url = os.environ.get('DATABASE_URL')
    with get_db() as conn:
        cursor = conn.cursor()
        if database_url:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    icon TEXT DEFAULT 'fa-tags'
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER,
                    customer_name TEXT NOT NULL,
                    rating INTEGER DEFAULT 5,
                    comment TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    address TEXT NOT NULL,
                    delivery_area TEXT NOT NULL,
                    delivery_charge REAL NOT NULL,
                    items_summary TEXT NOT NULL,
                    total_price REAL NOT NULL,
                    status TEXT DEFAULT 'Pending',
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    icon TEXT DEFAULT 'fa-tags'
                )
            ''')
            cursor.execute('''
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    customer_name TEXT NOT NULL,
                    rating INTEGER DEFAULT 5,
                    comment TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
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

        default_settings = {
            'site_name': 'NovaCart BD',
            'tagline': 'Shop Smart, Live Better',
            'logo_url': '',
            'header_banner_url': 'https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?w=1200&q=80',
            'banner_link': '#',
            'phone': '+880 1568-022033',
            'whatsapp': '+8801568022033',
            'fb_pixel_id': '',
            'google_site_verification': '',
            'google_adsense_code': '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1619234614836027" crossorigin="anonymous"></script>',
            'admin_password': 'admin123#novacart',
            'notice_text': '🚀 ক্যাশ অন ডেলিভারি সারা বাংলাদেশে! ৩ দিনের মধ্যে নিশ্চিত রিটার্ন পলিসি।'
        }
        
        for key, val in default_settings.items():
            if database_url:
                cursor.execute("INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING", (key, val))
            else:
                cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
            
        cursor.execute("SELECT COUNT(*) FROM products")
        row = cursor.fetchone()
        count = row['count'] if isinstance(row, dict) else row[0]
        if count == 0:
            sample_products = [
                ("NC-3622", "electric-duck-climbing-stairs-toy", "Electric Small Duck Climbing Stairs Toy", 1290.0, 850.0, "Toys", 
                 "https://images.unsplash.com/photo-1531651008558-ed1740375b39?w=800", 
                 "https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?w=800,https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?w=800",
                 "বাচ্চাদের আকর্ষনীয় মিউজিক ও লাইটিং|স্বয়ংক্রিয় সিঁড়ি বেয়ে ওঠার মজার খেলা|১০০% সেইফ ও প্রিমিয়াম প্লাস্টিক উপাদান|ব্যাটারি চালিত ও অত্যন্ত টেকসই",
                 "সারা বাংলাদেশে ক্যাশ অন ডেলিভারিতে অর্ডার করুন আপনার বাচ্চার জন্য সেরা উপহার ট্রেন্ডি ডাক ক্লাইম্বিং টয়। এটি বাচ্চাদের মনোযোগ ও বুদ্ধি বৃদ্ধিতে সাহায্য করে।", 1, 1),
                
                ("NC-10220", "16-in-1-multifunctional-vegetable-chopper", "16-in-1 Multifunctional Vegetable Chopper", 1190.0, 890.0, "Kitchen & Dining", 
                 "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?w=800", 
                 "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=800,https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800",
                 "১৬টি ভিন্ন ধরনের কাটিং ও চপিং ব্লেড|স্টেইনলেস স্টিল মরিচারোধী ব্লেড|সহজে পরিষ্কারযোগ্য ও ডিশওয়াশার সেফ|রান্নার সময় বাঁচায় ৭০%",
                 "Professional Kitchen Food Cutter with Stainless Steel Blades. আপনার রান্নাঘরের নিত্যদিনের কাজকে করুন সহজ ও দ্রুত।", 1, 1)
            ]
            
            sample_reviews = [
                (1, "মোঃ আরমান হোসেন", 5, "পণ্যটি সত্যিই অনেক সুন্দর এবং বাচ্চার খুব পছন্দ হয়েছে। ধন্যবাদ ডেলিভারি ম্যান ভাইয়াকে।"),
                (2, "তানজিনা আক্তার", 5, "রান্নার সময় অনেক বেঁচে যায়! ব্লেডগুলো খুব ধারালো ও শক্তপোক্ত।")
            ]

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

            if database_url:
                for cat in categories:
                    cursor.execute("INSERT INTO categories (name, icon) VALUES (%s, %s)", cat)
                for prod in sample_products:
                    cursor.execute("INSERT INTO products (code, slug, name, regular_price, sale_price, category, image, gallery_images, features, description, is_new, is_top) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", prod)
                for rev in sample_reviews:
                    cursor.execute("INSERT INTO reviews (product_id, customer_name, rating, comment) VALUES (%s, %s, %s, %s)", rev)
            else:
                cursor.executemany("INSERT INTO categories (name, icon) VALUES (?, ?)", categories)
                cursor.executemany("INSERT INTO products (code, slug, name, regular_price, sale_price, category, image, gallery_images, features, description, is_new, is_top) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_products)
                cursor.executemany("INSERT INTO reviews (product_id, customer_name, rating, comment) VALUES (?, ?, ?, ?)", sample_reviews)
            
        conn.commit()

init_db()

def get_settings():
    database_url = os.environ.get('DATABASE_URL')
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
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
    database_url = os.environ.get('DATABASE_URL')
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()
        if cat:
            if database_url:
                cursor.execute("SELECT * FROM products WHERE category = %s ORDER BY id DESC", (cat,))
            else:
                cursor.execute("SELECT * FROM products WHERE category = ? ORDER BY id DESC", (cat,))
            products = cursor.fetchall()
        else:
            cursor.execute("SELECT * FROM products ORDER BY id DESC")
            products = cursor.fetchall()
                
    return render_template('index.html', products=products, categories=categories, current_cat=cat, settings=settings)

@app.route('/p/<slug>')
def product_landing(slug):
    settings = get_settings()
    database_url = os.environ.get('DATABASE_URL')
    ph = '%s' if database_url else '?'
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM products WHERE slug = {ph}", (slug,))
        product = cursor.fetchone()
        if not product:
            if slug.isdigit():
                cursor.execute(f"SELECT * FROM products WHERE id = {ph}", (int(slug),))
                product = cursor.fetchone()
            if not product:
                return redirect(url_for('index'))
        
        gallery = []
        if product['gallery_images']:
            gallery = [img.strip() for img in product['gallery_images'].split(',') if img.strip()]
        
        features = []
        if product['features']:
            features = [f.strip() for f in product['features'].split('|') if f.strip()]
            
        cursor.execute(f"SELECT * FROM reviews WHERE product_id = {ph} ORDER BY id DESC", (product['id'],))
        reviews = cursor.fetchall()
        
    return render_template('landing_page.html', product=product, gallery=gallery, features=features, reviews=reviews, settings=settings)

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

@app.route('/add_review/<int:product_id>', methods=['POST'])
def add_review(product_id):
    name = request.form.get('customer_name')
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment')
    database_url = os.environ.get('DATABASE_URL')
    ph = '%s' if database_url else '?'
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT slug FROM products WHERE id = {ph}", (product_id,))
        cursor.execute(f"INSERT INTO reviews (product_id, customer_name, rating, comment) VALUES ({ph}, {ph}, {ph}, {ph})",
                     (product_id, name, rating, comment))
        conn.commit()
        
    flash('ধন্যবাদ! আপনার রিভিউটি সফলভাবে যুক্ত হয়েছে।', 'success')
    return redirect(url_for('product_landing', slug=product['slug']))

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
    
    database_url = os.environ.get('DATABASE_URL')
    ph = '%s' if database_url else '?'
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM products WHERE id = {ph}", (product_id,))
        product = cursor.fetchone()
        if not product:
            return redirect(url_for('index'))
            
        total = product['sale_price'] + delivery_charge
        items_summary = f"{product['name']} (কোড: {product['code']})"
        
        if database_url:
            cursor.execute(
                "INSERT INTO orders (customer_name, phone, address, delivery_area, delivery_charge, items_summary, total_price) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (name, phone, address, area_display, delivery_charge, items_summary, total)
            )
            row = cursor.fetchone()
            order_id = row['id'] if isinstance(row, dict) else row[0]
        else:
            cursor.execute(
                "INSERT INTO orders (customer_name, phone, address, delivery_area, delivery_charge, items_summary, total_price) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, phone, address, area_display, delivery_charge, items_summary, total)
            )
            order_id = cursor.lastrowid
        conn.commit()
        
    return render_template('order_success.html', order_id=order_id, name=name, phone=phone, address=address, product=product, total=total, charge=delivery_charge)

@app.route('/track', methods=['GET', 'POST'])
def track_order():
    order = None
    searched = False
    database_url = os.environ.get('DATABASE_URL')
    ph = '%s' if database_url else '?'
    if request.method == 'POST':
        searched = True
        query = request.form.get('query')
        with get_db() as conn:
            cursor = conn.cursor()
            if query.isdigit():
                cursor.execute(f"SELECT * FROM orders WHERE id = {ph} OR phone = {ph}", (int(query), query))
            else:
                cursor.execute(f"SELECT * FROM orders WHERE phone = {ph}", (query,))
            order = cursor.fetchone()
    return render_template('track.html', order=order, searched=searched)

@app.route('/sitemap.xml')
def sitemap():
    host = request.host_url.rstrip('/')
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT slug FROM products")
        products = cursor.fetchall()
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += f'  <url><loc>{host}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>\n'
    xml += f'  <url><loc>{host}/privacy-policy</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>\n'
    xml += f'  <url><loc>{host}/terms</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>\n'
    xml += f'  <url><loc>{host}/refund-policy</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>\n'
    xml += f'  <url><loc>{host}/about</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>\n'
    xml += f'  <url><loc>{host}/contact</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>\n'
    xml += f'  <url><loc>{host}/track</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>\n'
    for p in products:
        xml += f'  <url><loc>{host}/p/{p["slug"]}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    host = request.host_url.rstrip('/')
    txt = f"User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: {host}/sitemap.xml"
    return Response(txt, mimetype='text/plain')

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
    database_url = os.environ.get('DATABASE_URL')
    ph = '%s' if database_url else '?'
    if request.method == 'POST':
        action = request.form.get('action')
        with get_db() as conn:
            cursor = conn.cursor()
            if action == 'add_product':
                code = request.form.get('code')
                name = request.form.get('name')
                slug = generate_slug(name)
                regular_price = float(request.form.get('regular_price'))
                sale_price = float(request.form.get('sale_price'))
                category = request.form.get('category')
                features = request.form.get('features')
                description = request.form.get('description')
                
                image_url = request.form.get('image_url', '')
                if 'image_file' in request.files:
                    file = request.files['image_file']
                    if file and file.filename != '' and allowed_file(file.filename):
                        upload_result = cloudinary.uploader.upload(file)
                        image_url = upload_result.get('secure_url')

                gallery_list = []
                if 'gallery_files' in request.files:
                    files = request.files.getlist('gallery_files')
                    for file in files:
                        if file and file.filename != '' and allowed_file(file.filename):
                            upload_result = cloudinary.uploader.upload(file)
                            gallery_list.append(upload_result.get('secure_url'))
                
                extra_gallery = request.form.get('gallery_images_text', '')
                if extra_gallery:
                    for g in extra_gallery.split(','):
                        if g.strip():
                            gallery_list.append(g.strip())
                            
                gallery_images_str = ','.join(gallery_list)

                cursor.execute(f"INSERT INTO products (code, slug, name, regular_price, sale_price, category, image, gallery_images, features, description) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})",
                             (code, slug, name, regular_price, sale_price, category, image_url, gallery_images_str, features, description))
                conn.commit()
                flash('প্রডাক্ট ও ল্যান্ডিং পেজ সফলভাবে তৈরি করা হয়েছে!', 'success')
                
            elif action == 'add_category':
                cat_name = request.form.get('cat_name')
                icon = request.form.get('icon', 'fa-tags')
                cursor.execute(f"INSERT INTO categories (name, icon) VALUES ({ph}, {ph})", (cat_name, icon))
                conn.commit()
                flash('ক্যাটাগরি যুক্ত করা হয়েছে!', 'success')
                
            elif action == 'update_settings':
                fields = ['site_name', 'tagline', 'banner_link', 'phone', 'whatsapp', 'fb_pixel_id', 'google_site_verification', 'google_adsense_code', 'admin_password', 'notice_text']
                for field in fields:
                    val = request.form.get(field, '')
                    if database_url:
                        cursor.execute("INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", (field, val))
                    else:
                        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (field, val))
                
                if 'logo_file' in request.files:
                    file = request.files['logo_file']
                    if file and file.filename != '' and allowed_file(file.filename):
                        upload_result = cloudinary.uploader.upload(file)
                        logo_url = upload_result.get('secure_url')
                        if database_url:
                            cursor.execute("INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", ('logo_url', logo_url))
                        else:
                            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ('logo_url', logo_url))

                banner_url = request.form.get('banner_url_text', '')
                if 'banner_file' in request.files:
                    file = request.files['banner_file']
                    if file and file.filename != '' and allowed_file(file.filename):
                        upload_result = cloudinary.uploader.upload(file)
                        banner_url = upload_result.get('secure_url')
                
                if banner_url:
                    if database_url:
                        cursor.execute("INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", ('header_banner_url', banner_url))
                    else:
                        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ('header_banner_url', banner_url))

                conn.commit()
                flash('ওয়েবসাইট সেটিংস ও ব্যানার সফলভাবে সেভ করা হয়েছে!', 'success')
                
        return redirect(url_for('admin'))
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY id DESC")
        products = cursor.fetchall()
        cursor.execute("SELECT * FROM orders ORDER BY id DESC")
        orders = cursor.fetchall()
        cursor.execute("SELECT * FROM categories ORDER BY id DESC")
        categories = cursor.fetchall()
    return render_template('admin.html', products=products, orders=orders, categories=categories, settings=get_settings())

@app.route('/admin/delete_product/<int:product_id>')
@login_required
def delete_product(product_id):
    database_url = os.environ.get('DATABASE_URL')
    ph = '%s' if database_url else '?'
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM products WHERE id = {ph}", (product_id,))
        conn.commit()
    flash('প্রডাক্ট মুছে ফেলা হয়েছে!', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/update_order/<int:order_id>/<string:status>')
@login_required
def update_order_status(order_id, status):
    database_url = os.environ.get('DATABASE_URL')
    ph = '%s' if database_url else '?'
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE orders SET status = {ph} WHERE id = {ph}", (status, order_id))
        conn.commit()
    flash('অর্ডার স্ট্যাটাস আপডেট করা হয়েছে!', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
