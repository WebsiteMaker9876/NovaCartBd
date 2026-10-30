import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# রেন্ডার এবং সুপাবেজ ডাটাবেজ কানেকশন কনফিগারেশন
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgresql://") and "+psycopg2" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ====================
# ডাটাবেজ মডেলসমূহ (Database Models)
# ====================

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True, cascade='all, delete-orphan')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)                 # রেগুলার প্রাইস
    discount_price = db.Column(db.Float, nullable=True)         # ডিসকাউন্ট বা সেল প্রাইস
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    image_url = db.Column(db.String(300))
    is_free_delivery = db.Column(db.Boolean, default=False)     # ফ্রি ডেলিভারি ফ্ল্যাগ

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Pending')

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default='NovaCart BD')
    site_title = db.Column(db.String(200), default='NovaCart BD - Online Shopping in Bangladesh')
    meta_description = db.Column(db.Text, default='Best online shopping store in Bangladesh with Cash on Delivery.')
    meta_keywords = db.Column(db.String(300), default='ecommerce, online shop, bangladesh, nova cart')
    whatsapp_number = db.Column(db.String(50))
    facebook_pixel_id = db.Column(db.String(100))
    google_search_console = db.Column(db.String(200))
    google_adsense_code = db.Column(db.Text)                    # গুগল এডসেন্স স্ক্রিপ্ট কোড
    notice_text = db.Column(db.String(300))
    delivery_inside_dhaka = db.Column(db.Float, default=80.0)
    delivery_outside_dhaka = db.Column(db.Float, default=150.0)
    admin_password = db.Column(db.String(100), default='admin123')

# ====================
# অটো-টেবিল এবং কলাম আপডেট সিস্টেম (Auto-Migration)
# ====================
with app.app_context():
    db.create_all()
    
    inspector = inspect(db.engine)
    
    # Product টেবিলে নতুন কলাম অটো চেক ও যোগ
    if 'product' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('product')]
        with db.engine.begin() as conn:
            if 'description' not in columns:
                conn.execute(text('ALTER TABLE product ADD COLUMN description TEXT;'))
            if 'is_free_delivery' not in columns:
                conn.execute(text('ALTER TABLE product ADD COLUMN is_free_delivery BOOLEAN DEFAULT FALSE;'))
            if 'discount_price' not in columns:
                conn.execute(text('ALTER TABLE product ADD COLUMN discount_price FLOAT;'))

    # Settings টেবিলে এডসেন্স ও ডেলিভারি কলাম অটো চেক ও যোগ
    if 'settings' in inspector.get_table_names():
        set_columns = [c['name'] for c in inspector.get_columns('settings')]
        with db.engine.begin() as conn:
            if 'site_name' not in set_columns:
                conn.execute(text("ALTER TABLE settings ADD COLUMN site_name VARCHAR(100) DEFAULT 'NovaCart BD';"))
            if 'site_title' not in set_columns:
                conn.execute(text("ALTER TABLE settings ADD COLUMN site_title VARCHAR(200);"))
            if 'meta_description' not in set_columns:
                conn.execute(text("ALTER TABLE settings ADD COLUMN meta_description TEXT;"))
            if 'meta_keywords' not in set_columns:
                conn.execute(text("ALTER TABLE settings ADD COLUMN meta_keywords VARCHAR(300);"))
            if 'google_adsense_code' not in set_columns:
                conn.execute(text("ALTER TABLE settings ADD COLUMN google_adsense_code TEXT;"))
            if 'delivery_inside_dhaka' not in set_columns:
                conn.execute(text("ALTER TABLE settings ADD COLUMN delivery_inside_dhaka FLOAT DEFAULT 80.0;"))
            if 'delivery_outside_dhaka' not in set_columns:
                conn.execute(text("ALTER TABLE settings ADD COLUMN delivery_outside_dhaka FLOAT DEFAULT 150.0;"))

# ====================
# রুট ও রাউটিং (Routes)
# ====================

@app.route('/')
def index():
    categories = Category.query.all()
    products = Product.query.all()
    site_settings = Settings.query.first()
    return render_template('index.html', categories=categories, products=products, site_settings=site_settings, settings=site_settings)

@app.route('/admin')
def admin_dashboard():
    categories = Category.query.all()
    products = Product.query.all()
    orders = Order.query.all()
    site_settings = Settings.query.first()
    return render_template('admin.html', categories=categories, products=products, orders=orders, site_settings=site_settings, settings=site_settings)

# --- সেটিংস, এসইও ও এডসেন্স কোড আপডেট ---
@app.route('/admin/settings/update', methods=['POST'])
def update_settings():
    site_settings = Settings.query.first()
    if not site_settings:
        site_settings = Settings()
        db.session.add(site_settings)
    
    site_settings.site_name = request.form.get('site_name')
    site_settings.site_title = request.form.get('site_title')
    site_settings.meta_description = request.form.get('meta_description')
    site_settings.meta_keywords = request.form.get('meta_keywords')
    site_settings.whatsapp_number = request.form.get('whatsapp_number')
    site_settings.facebook_pixel_id = request.form.get('facebook_pixel_id')
    site_settings.google_search_console = request.form.get('google_search_console')
    site_settings.google_adsense_code = request.form.get('google_adsense_code')  # এডসেন্স কোড
    site_settings.notice_text = request.form.get('notice_text')
    
    in_dhaka = request.form.get('delivery_inside_dhaka')
    out_dhaka = request.form.get('delivery_outside_dhaka')
    if in_dhaka:
        site_settings.delivery_inside_dhaka = float(in_dhaka)
    if out_dhaka:
        site_settings.delivery_outside_dhaka = float(out_dhaka)
    
    password = request.form.get('admin_password')
    if password:
        site_settings.admin_password = password
        
    db.session.commit()
    flash('সেটিংস, এসইও ও এডসেন্স সফলভাবে আপডেট করা হয়েছে!', 'success')
    return redirect(url_for('admin_dashboard'))

# --- প্রোডাক্ট ম্যানেজমেন্ট (ডিসকাউন্ট ও ফ্রি ডেলিভারি সহ) ---
@app.route('/admin/product/add', methods=['POST'])
def add_product():
    title = request.form.get('title')
    price = request.form.get('price')
    discount_price = request.form.get('discount_price')
    description = request.form.get('description')
    category_id = request.form.get('category_id')
    image_url = request.form.get('image_url')
    is_free_delivery = True if request.form.get('is_free_delivery') == 'on' else False
    
    if title and price and category_id:
        new_prod = Product(
            title=title, 
            price=float(price),
            discount_price=float(discount_price) if discount_price else None, 
            description=description, 
            category_id=int(category_id), 
            image_url=image_url,
            is_free_delivery=is_free_delivery
        )
        db.session.add(new_prod)
        db.session.commit()
        flash('নতুন প্রোডাক্ট ডিসকাউন্টসহ সফলভাবে পাবলিশ করা হয়েছে!', 'success')
    else:
        flash('দয়া করে প্রয়োজনীয় তথ্যগুলো পূরণ করুন।', 'danger')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/product/delete/<int:id>', methods=['POST'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('প্রোডাক্টটি সফলভাবে ডিলিট করা হয়েছে!', 'success')
    return redirect(url_for('admin_dashboard'))

# --- ক্যাটাগরি ম্যানেজমেন্ট ---
@app.route('/admin/category/add', methods=['POST'])
def add_category():
    category_name = request.form.get('name')
    if category_name:
        existing = Category.query.filter_by(name=category_name).first()
        if not existing:
            new_cat = Category(name=category_name)
            db.session.add(new_cat)
            db.session.commit()
            flash('ক্যাটাগরি সফলভাবে যোগ করা হয়েছে!', 'success')
        else:
            flash('এই ক্যাটাগরি ইতিমধ্যে তৈরি করা আছে!', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/category/delete/<int:id>', methods=['POST'])
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('ক্যাটাগরি সফলভাবে মুছে ফেলা হয়েছে!', 'success')
    return redirect(url_for('admin_dashboard'))

# --- অর্ডার ম্যানেজমেন্ট ---
@app.route('/admin/order/status/<int:id>', methods=['POST'])
def update_order_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status')
    if new_status:
        order.status = new_status
        db.session.commit()
        flash('অর্ডারের স্ট্যাটাস সফলভাবে আপডেট করা হয়েছে!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/order/delete/<int:id>', methods=['POST'])
def delete_order(id):
    order = Order.query.get_or_404(id)
    if order.status and order.status.lower() == 'completed':
        db.session.delete(order)
        db.session.commit()
        flash('সম্পন্ন হওয়া অর্ডারটি সফলভাবে ডিলিট করা হয়েছে।', 'success')
    else:
        flash('যে অর্ডারগুলোর কাজ এখনো সম্পূর্ণ (Completed) হয়নি সেগুলো ডিলিট করা যাবে না!', 'danger')
        
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
