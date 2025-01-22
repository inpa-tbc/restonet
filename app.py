import os
import logging
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('app.log'),
                        logging.StreamHandler()
                    ])

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Ensure the instance folder exists
os.makedirs('instance', exist_ok=True)

# Configure file upload
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'img')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Database Models
class MenuCategory(db.Model):
    __tablename__ = 'menu_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(100), nullable=True)
    image = db.Column(db.String(200), nullable=True)
    items = db.relationship('MenuItem', backref='category', lazy=True)

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('menu_categories.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=True)

class RestaurantInfo(db.Model):
    __tablename__ = 'restaurant_info'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    working_hours = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    logo = db.Column(db.String(200), nullable=True)
    whatsapp_number = db.Column(db.String(20), nullable=True)
    instagram = db.Column(db.String(100), nullable=True)
    snapchat = db.Column(db.String(100), nullable=True)
    tiktok = db.Column(db.String(100), nullable=True)
    facebook = db.Column(db.String(100), nullable=True)

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder=''):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        file.save(filepath)
        return os.path.join(folder, filename)
    return None

# Authentication Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# Admin Dashboard Routes
@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    restaurant_info = RestaurantInfo.query.first()
    return render_template('admin/dashboard.html', 
                           restaurant_info=restaurant_info, 
                           MenuCategory=MenuCategory, 
                           MenuItem=MenuItem)

@app.route('/admin/restaurant-settings', methods=['GET', 'POST'])
def restaurant_settings():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    restaurant_info = RestaurantInfo.query.first()
    
    if request.method == 'POST':
        # Update restaurant information
        if not restaurant_info:
            restaurant_info = RestaurantInfo()
            db.session.add(restaurant_info)
        
        # Update text fields
        restaurant_info.name = request.form.get('name')
        restaurant_info.address = request.form.get('address')
        restaurant_info.phone = request.form.get('phone')
        restaurant_info.email = request.form.get('email')
        restaurant_info.working_hours = request.form.get('working_hours')
        restaurant_info.description = request.form.get('description')
        restaurant_info.whatsapp_number = request.form.get('whatsapp_number')
        restaurant_info.instagram = request.form.get('instagram')
        restaurant_info.snapchat = request.form.get('snapchat')
        restaurant_info.tiktok = request.form.get('tiktok')
        restaurant_info.facebook = request.form.get('facebook')
        
        # Handle logo upload
        logo = request.files.get('logo')
        if logo:
            logo_path = save_uploaded_file(logo, 'restaurant')
            if logo_path:
                restaurant_info.logo = logo_path
        
        db.session.commit()
        flash('تم تحديث معلومات المطعم بنجاح', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/restaurant_settings.html', restaurant_info=restaurant_info)

# Routes for adding categories and menu items
@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            icon = request.form.get('icon', 'fa-utensils')

            # Handle file upload
            image = request.files.get('image')
            image_filename = None
            if image and allowed_file(image.filename):
                filename = secure_filename(f"{name}_{image.filename}")
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'categories', filename)
                
                # Ensure upload directory exists
                os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'categories'), exist_ok=True)
                
                image.save(image_path)
                image_filename = f'categories/{filename}'

            # Create new category
            new_category = MenuCategory(
                name=name, 
                description=description, 
                icon=icon,
                image=image_filename
            )
            db.session.add(new_category)
            db.session.commit()

            return redirect(url_for('index'))
        except Exception as e:
            logging.error(f"Error adding category: {e}")
            return f"حدث خطأ: {e}", 500

    # GET request: render add category form
    return render_template('add_category.html')

@app.route('/add_menu_item', methods=['GET', 'POST'])
@app.route('/add_menu_item/<int:category_id>', methods=['GET', 'POST'])
def add_menu_item(category_id=None):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    categories = MenuCategory.query.all()

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        category_id = request.form.get('category_id')
        image = request.files.get('image')

        # Validate inputs
        if not name or not category_id or not price:
            flash('يرجى ملء جميع الحقول المطلوبة', 'error')
            return render_template('add_menu_item.html', categories=categories, category_id=category_id)

        # Handle image upload
        image_filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(f"{name}_{image.filename}")
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'menu-items', filename)
            
            # Ensure upload directory exists
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'menu-items'), exist_ok=True)
            
            image.save(image_path)
            image_filename = f'menu-items/{filename}'

        # Create new menu item
        new_item = MenuItem(
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            image=image_filename
        )
        
        try:
            db.session.add(new_item)
            db.session.commit()
            flash('تمت إضافة الصنف بنجاح', 'success')
            return redirect(url_for('add_menu_item'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة الصنف: {str(e)}', 'error')

    return render_template('add_menu_item.html', categories=categories, category_id=category_id)

# Routes for retrieving menu items
@app.route('/get_menu_items/<int:category_id>')
def get_menu_items(category_id):
    try:
        # Fetch menu items for the specified category
        menu_items = MenuItem.query.filter_by(category_id=category_id).all()
        
        # Convert menu items to a list of dictionaries
        menu_items_list = [{
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': item.price,
            'image': url_for('static', filename=f'img/{item.image}') if item.image else None
        } for item in menu_items]
        
        return jsonify(menu_items_list)
    except Exception as e:
        app.logger.error(f"Error fetching menu items: {e}")
        return jsonify({'error': 'حدث خطأ أثناء جلب القائمة'}), 500

# Routes
@app.route('/')
def index():
    try:
        restaurant_info = RestaurantInfo.query.first()
        app.logger.debug(f"Restaurant Info: {restaurant_info.__dict__ if restaurant_info else None}")
        
        # Get all menu categories
        categories = db.session.query(
            MenuCategory.id,
            MenuCategory.name,
            MenuCategory.description
        ).all()
        
        return render_template('index.html', 
                             restaurant_info=restaurant_info,
                             categories=categories)
    except Exception as e:
        app.logger.error(f"Error in index route: {str(e)}")
        return str(e), 500

@app.route('/category/<int:category_id>')
def view_category(category_id):
    try:
        category = MenuCategory.query.get_or_404(category_id)
        menu_items = MenuItem.query.filter_by(category_id=category_id).all()
        restaurant_info = RestaurantInfo.query.first()
        
        return render_template('category.html', 
                             category=category, 
                             menu_items=menu_items,
                             restaurant_info=restaurant_info)
    except Exception as e:
        app.logger.error(f"Error in category route: {e}")
        return f"حدث خطأ أثناء تحميل الصفحة: {e}", 500

def add_items_to_categories():
    categories = MenuCategory.query.all()
    for category in categories:
        for i in range(10):
            item = MenuItem(
                category_id=category.id,
                name=f'Item {i+1} for {category.name}',
                description=f'Description for item {i+1} in {category.name}',
                price=10.0 + i,
                image=f'static/img/default_item_{(i % 5) + 1}.jpg'  # Default image path
            )
            db.session.add(item)
    db.session.commit()

# Run the application
if __name__ == '__main__':
    # Create the instance directory if it doesn't exist
    os.makedirs('instance', exist_ok=True)
    
    # Initialize the database
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default admin user if not exists
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
        
        # Add restaurant information if not exists
        restaurant_info = RestaurantInfo.query.first()
        if not restaurant_info:
            restaurant_info = RestaurantInfo(
                name='مطعم شبام للمأكولات اليمنية',
                address='Emin Ali Yasin Sk. No:11, 34093 Fatih, 34093 molla güarani/İstanbul',
                phone='+905404017777',
                email='info@shabamrestaurant.com',
                working_hours='يومياً من 10 صباحاً حتى 11 مساءً',
                description='نقدم أشهى المأكولات اليمنية التقليدية في أجواء مميزة',
                whatsapp_number='905404017777',
                instagram='https://www.instagram.com/mandishebam/',
                snapchat='https://www.snapchat.com/add/mandishebam',
                tiktok='https://www.tiktok.com/@mandisebam',
                facebook='https://www.facebook.com/mandishebam/'
            )
            db.session.add(restaurant_info)
        else:
            # Update existing restaurant info
            restaurant_info.phone = '+905404017777'
            restaurant_info.whatsapp_number = '905404017777'
            restaurant_info.instagram = 'https://www.instagram.com/mandishebam/'
            restaurant_info.snapchat = 'https://www.snapchat.com/add/mandishebam'
            restaurant_info.tiktok = 'https://www.tiktok.com/@mandisebam'
            restaurant_info.facebook = 'https://www.facebook.com/mandishebam/'
        db.session.commit()
            
        # Add default menu categories if none exist
        if not MenuCategory.query.first():
            categories = [
                MenuCategory(name='المندي', description='أشهى أطباق المندي اليمني'),
                MenuCategory(name='المشويات', description='تشكيلة متنوعة من المشويات'),
                MenuCategory(name='المقبلات', description='مقبلات شهية'),
                MenuCategory(name='المشروبات', description='مشروبات منعشة')
            ]
            for category in categories:
                db.session.add(category)
            db.session.commit()
        
        # Add items to categories
        add_items_to_categories()
        print('Added 10 items with images to each category.')
    
    app.run(host='0.0.0.0', debug=True)
