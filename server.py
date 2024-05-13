from flask import Flask, render_template, request, redirect, url_for, session, jsonify, json, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session
from functools import wraps
import os, json
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'sadgasasdsadasdasfasdasdasdasd'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///BSCS-CSM2.db'
db = SQLAlchemy(app)

UPLOAD_FOLDER = 'static/assets/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

'''
==========================================================
Model
===========================================================
'''
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    gender = db.Column(db.String(60), nullable=False)
    phoneNumber = db.Column(db.String(60), nullable=True)
    city = db.Column(db.String(60), nullable=True)
    streetOrHouseNumber = db.Column(db.String(60), nullable=True)
    province = db.Column(db.String(60), nullable=True)
    barangay = db.Column(db.String(60), nullable=True) 
    create_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    update_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"User('{self.fullname}', '{self.email}', '{self.gender}', '{self.phoneNumber}', '{self.city}', '{self.streetOrHouseNumber}')"


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pName = db.Column(db.String(60), unique=True, nullable=False)
    pDesc = db.Column(db.String(120), nullable=False) 
    pPrice = db.Column(db.String(60), nullable=False)
    piamge = db.Column(db.String(60), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    create_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    update_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    def __repr__(self):
        return f"Product('{self.pName}', '{self.pDesc}', '{self.pPrice}', '{self.piamge}', '{self.category}')"



class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    paid = db.Column(db.Integer, nullable=False, default=False)
    recipt = db.Column(db.String(100), nullable=True, default=0)
    delivered = db.Column(db.Integer, nullable=True, default=0)
    create_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    update_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    def __repr__(self):
        return f"CartItem('{self.id}','{self.product_id}', '{self.name}', '{self.price}', '{self.quantity}', '{self.paid}', '{self.delivered}')"

with app.app_context():
    db.create_all()

'''
==========================================================
Extra
===========================================================
'''   
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


'''
==========================================================
Authentication
===========================================================
'''
@app.route('/login', methods=['GET', 'POST'])
def signin():
    if 'logged_in' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['logged_in'] = True
            session['id'] = user.id
            
            if user.is_admin:
                session['is_admin'] = True
                return jsonify({'status': 'success', 'admin': True})
            else:
                return jsonify({'status': 'success', 'admin': False})
        else:
           return jsonify({'status': 'error', 'message': 'Invalid email or password'})

    return render_template('signin.html', invalid_input=False)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = f"{request.form['fname']} {request.form['lname']}"
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['password']
        gender = request.form['gender']
        phoneNumber = None
        city = None
        streetOrHouseNumber = None
        is_admin = False  
        
        if email.endswith('@admin.com'):
            is_admin = True

        if password == confirm_password:

             # If gender is "Other", store the specified text in the database
            if gender == 'Other':
                gender = request.form['otherText']

            hashed_password = generate_password_hash(password)
            new_user = User(fullname=fullname, email=email, gender=gender, password=hashed_password,
                            phoneNumber=phoneNumber, city=city, streetOrHouseNumber=streetOrHouseNumber,
                            is_admin=is_admin)  
            db.session.add(new_user)
            db.session.commit()
            return "1" 
        else:
            return 'Passwords do not match. Please try again.'
    return render_template('signup.html')

@app.route('/update_user', methods=['POST'])
def update_user():
    user_id = session['id']
    user = db.session.get(User, user_id)
    if user:
        user.fullname = request.form['fullname']
        user.email = request.form['email']
        user.gender = request.form['gender']
        user.phoneNumber = request.form['phoneNumber']
        user.city = request.form['city']
        user.streetOrHouseNumber = request.form['streetOrHouseNumber']
        user.province = request.form['province']
        user.barangay = request.form['barangay']
        
        # Check if gender is "Other" and update otherText field accordingly
        if user.gender == 'Other':
            user.otherText = request.form.get('otherText', '')  # Get value from form or empty string if not provided

        db.session.commit()
        return jsonify({"success": True})  # Success response as JSON
    else:
        return jsonify({"error": "User not found"})  # Error response as JSON

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    session.pop('id', None)
    session.pop('is_admin', None)  
    return redirect(url_for('home'))

'''
==========================================================
Admin Side
===========================================================
'''

@app.route('/categories', methods=['GET'])
def categories():
    categories = db.session.query(Product.category).distinct().all()
    
    category_names = [category[0] for category in categories]
    
    return jsonify(category_names)


@app.route('/products/category/<category>', methods=['GET'])
@login_required
def product_by_category(category):
    categories = ["Hot Coffee", "Cold Coffee", "Frappuccino"]
    if category in categories:
        products = Product.query.filter_by(category=category).all()
        product_details = [{
            'id': product.id,
            'pName': product.pName,
            'pDesc': product.pDesc,
            'pPrice': product.pPrice,
            'piamge': product.piamge,
            'category': product.category,
            'create_at': product.create_at,
            'update_at': product.update_at
        } for product in products]
        return jsonify(product_details)
    else:
        return jsonify([])

@app.route('/product_details/<int:product_id>')
def product_details(product_id):
    product = Product.query.get_or_404(product_id)

    product_details = {
        'id': product.id,
        'pName': product.pName,
        'pDesc': product.pDesc,
        'pPrice': product.pPrice,
        'piamge': product.piamge,
        'category': product.category,
        'create_at': product.create_at,
        'update_at': product.update_at
    }

    return jsonify(product_details)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.pName = request.form['productName']
        product.pDesc = request.form['productDescription']
        product.pPrice = request.form['productPrice']
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('manage_products'))

    return render_template('manage_products.html', product=product)


@app.route('/remove_product/<int:product_id>', methods=['POST'])
def remove_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product removed successfully!', 'success')
    return redirect(url_for('manage_products'))

@app.route('/dashboard_admin')
@login_required
def dashboard_admin():
    if 'is_admin' in session and session['is_admin']:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('home'))

@app.route('/manage_orders')
def manage_orders():
    # Fetch cart items with user's full name sorted by creation date (newest first)
    cart_items = db.session.query(CartItem, User.fullname)\
                    .join(User, CartItem.user_id == User.id)\
                    .order_by(desc(CartItem.create_at))\
                    .all()
    return render_template('manage_orders.html', cart_items=cart_items)


@app.route('/manage_products')
def manage_products():
    # Query all products from the Product table
    products = Product.query.all()
    return render_template('manage_products.html', products=products)



@app.route('/manage_users')
def manage_users():
    # Query regular users (non-admins)
    regular_users = User.query.filter_by(is_admin=False).all()
    return render_template('manage_users.html', users=regular_users)

'''
==========================================================
Routes
===========================================================
'''


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('aboutUs.html')

@app.route('/gcash', methods=['GET'])
@login_required
def gcash():
    return render_template('gcash.html')

@app.route('/confirm', methods=['GET'])
@login_required
def confirm():
    return render_template('confirm.html')

@app.route('/myaccount', methods=['GET'])
@login_required
def myaccount():
    user_id = session['id'] 
    data = User.query.filter_by(id=user_id).all()
    return render_template('myaccount.html',userDatas=data)

@app.route('/products', methods=['GET'])
@login_required
def product():
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

@app.route('/add_prod', methods=['GET','POST'])
@login_required
def product_add():
    if request.method == 'POST':
        pName = request.form['productName']
        pDesc = request.form['productDescription']
        pPrice = request.form['productPrice']
        pCategory = request.form['productCategory']  # Get selected category from the form

        # Check if file is uploaded
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        # Check if file is allowed
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Create new product with category
            new_product = Product(pName=pName, pDesc=pDesc, pPrice=pPrice, piamge=filename, category=pCategory)
            db.session.add(new_product)
            db.session.commit()
            
            return redirect(url_for('manage_products'))
    
    # Fetch categories to populate the dropdown menu
    categories = Product.query.with_entities(Product.category).distinct().all()
    
    return render_template('reg_product.html', categories=categories)


@app.route('/checkout', methods=['GET'])
@login_required
def checkout():
    user_id = session['id']   
    user_data = User.query.filter_by(id=user_id).first()  
    cart_items = CartItem.query.filter(and_(CartItem.user_id == user_id, CartItem.paid == 0, CartItem.recipt == 0)).all()
    return render_template('cart.html', userDatas=user_data, cartData=cart_items)


@app.route('/buyNow', methods=['POST'])
def buyNow():
    recipt = request.form.get('randomString')
    user_id = session['id'] 
  
    cart_items = CartItem.query.filter(and_(CartItem.user_id == user_id, CartItem.paid == 0, CartItem.recipt == 0)).all()
    for cart_item in cart_items:
        cart_item.paid = 1
        cart_item.recipt = recipt
        db.session.commit()
    return jsonify({'Reciept': recipt})




@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):

    product = Product.query.get_or_404(product_id)

    user_id = session['id'] 
    cart_item = CartItem(
        product_id=product_id,
        name=product.pName,  
        price=product.pPrice, 
        quantity=1,  
        user_id=user_id
    )

    db.session.add(cart_item)
    db.session.commit()

    return jsonify({'message': 'Product added to cart'})



@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    db.session.delete(cart_item)
    db.session.commit()
    return redirect(request.referrer)


@app.route('/barista', methods=['GET'])
@login_required
def barista():
    user_id = session['id']   
    
    cart_items = CartItem.query.filter(and_(CartItem.user_id == user_id, CartItem.delivered == 0)).all()

    # Preprocess the cart items to consolidate similar items and calculate total prices
    merged_items = defaultdict(int)
    for item in cart_items:
        merged_items[item.name] += item.quantity

    # Calculate total price for each item
    for name, quantity in merged_items.items():
        items = [i for i in cart_items if i.name == name]
        merged_items[name] = {
            'quantity': quantity,
            'total_price': sum(item.price for item in items)
        }

    return render_template('barista.html', cartData=merged_items)


@app.route('/delivered', methods=['POST'])
def delivered():
    user_id = session['id'] 
    cart_items = CartItem.query.filter(and_(CartItem.user_id == user_id, CartItem.delivered == 0)).all()
    for cart_item in cart_items:
        cart_item.delivered = 1
        db.session.commit()
    return jsonify({'msg': 'delivered'})

@app.route('/location', methods=['GET'])
@login_required
def location():
    user_id = session['id']   
    
    cart_items = CartItem.query.filter(and_(CartItem.user_id == user_id, CartItem.delivered == 0)).all()

    # Preprocess the cart items to consolidate similar items and calculate total prices
    merged_items = defaultdict(int)
    for item in cart_items:
        merged_items[item.name] += item.quantity

    # Calculate total price for each item
    for name, quantity in merged_items.items():
        items = [i for i in cart_items if i.name == name]
        merged_items[name] = {
            'quantity': quantity,
            'total_price': sum(item.price for item in items)
        }
    return render_template('location.html',cartData=merged_items)

'''
==========================================================
Custom filter
===========================================================
'''

def combine_dicts(*dicts):
    result = {}
    for d in dicts:
        result.update(d)
    return result

@app.template_filter('combine')
def filter_combine_dicts(*dicts):
    return combine_dicts(*dicts)




'''
==========================================================
End
===========================================================
'''
if __name__ == '__main__':
    app.run(debug=True)