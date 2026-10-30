import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # এটিকে আপনার সিক্রেট কি দিয়ে পরিবর্তন করতে পারেন

# রেন্ডার এবং সুপাবেজ ডাটাবেজ কানেকশন কনফিগারেশন
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

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
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    image_url = db.Column(db.String(300))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Pending') # স্ট্যাটাস: Pending, Completed ইত্যাদি

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    whatsapp_number = db.Column(db.String(50))
    facebook_pixel_id = db.Column(db.String(100))
    google_search_console = db.Column(db.String(200))
    notice_text = db.Column(db.String(300))
    admin_password = db.Column(db.String(100))

# ====================
# রুট ও রাউটিং (Routes)
# ====================

@app.route('/')
def index():
    categories = Category.query.all()
    products = Product.query.all()
    site_settings = Settings.query.first()
    return render_template('index.html', categories=categories, products=products, site_settings=site_settings)

@app.route('/admin')
def admin_dashboard():
    categories = Category.query.all()
    orders = Order.query.all()
    site_settings = Settings.query.first()
    return render_template('admin.html', categories=categories, orders=orders, site_settings=site_settings)

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
    flash('অপ্রয়োজনীয় ক্যাটাগরি সফলভাবে মুছে ফেলা হয়েছে!', 'success')
    return redirect(url_for('admin_dashboard'))

# --- অর্ডার ম্যানেজমেন্ট ও ডিলিট অপশন ---
@app.route('/admin/order/delete/<int:id>', methods=['POST'])
def delete_order(id):
    order = Order.query.get_or_404(id)
    
    # শুধুমাত্র কমপ্লিট হওয়া অর্ডারগুলোই ডিলিট করা যাবে
    if order.status and order.status.lower() == 'completed':
        db.session.delete(order)
        db.session.commit()
        flash('সম্পন্ন হওয়া অর্ডারটি সফলভাবে ডিলিট করা হয়েছে।', 'success')
    else:
        flash('যে অর্ডারগুলোর কাজ এখনো সম্পূর্ণ হয়নি সেগুলো ডিলিট করা যাবে না!', 'danger')
        
    return redirect(url_for('admin_dashboard'))

# --- সাইট সেটিংস আপডেট (পিক্সেল, সার্চ কনসোল, পাসওয়ার্ড ইত্যাদি) ---
@app.route('/admin/settings/update', methods=['POST'])
def update_settings():
    site_settings = Settings.query.first()
    if not site_settings:
        site_settings = Settings()
        db.session.add(site_settings)
    
    site_settings.whatsapp_number = request.form.get('whatsapp_number')
    site_settings.facebook_pixel_id = request.form.get('facebook_pixel_id')
    site_settings.google_search_console = request.form.get('google_search_console')
    site_settings.notice_text = request.form.get('notice_text')
    
    password = request.form.get('admin_password')
    if password:
        site_settings.admin_password = password
        
    db.session.commit()
    flash('সেটিংস সফলভাবে সেভ করা হয়েছে!', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # স্বয়ংক্রিয়ভাবে নতুন Settings টেবিল তৈরি করে নেবে
    app.run(debug=True)
