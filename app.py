
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import func


from werkzeug.utils import secure_filename
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///farmhub.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)

# Message model for user-shop chat
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, nullable=False)
    sender_type = db.Column(db.String(10), nullable=False)  # 'user' or 'shop'
    receiver_id = db.Column(db.Integer, nullable=False)
    receiver_type = db.Column(db.String(10), nullable=False)  # 'user' or 'shop'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(200))
    product_type = db.Column(db.String(50))
    unit = db.Column(db.String(20))
    price_unit = db.Column(db.String(20))
    sold = db.Column(db.Integer, default=0)
    available = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0)
    price = db.Column(db.Float, default=0)
    # approved flag: only approved products are shown to public users
    approved = db.Column(db.Boolean, default=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    address_house = db.Column(db.String(100))
    address_street = db.Column(db.String(100))
    address_city = db.Column(db.String(100))
    address_district = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    password = db.Column(db.String(200), nullable=False)
    profile_image = db.Column(db.String(200))
    password_hint_question = db.Column(db.String(200))
    password_hint_answer = db.Column(db.String(200))

# New Shop model
class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    address_house = db.Column(db.String(100))
    address_street = db.Column(db.String(100))
    address_city = db.Column(db.String(100))
    address_district = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    password = db.Column(db.String(200), nullable=False)
    profile_image = db.Column(db.String(200))
    password_hint_question = db.Column(db.String(200))
    password_hint_answer = db.Column(db.String(200))
    total_income = db.Column(db.Float, default=0.0)  # Track total income for commission threshold
    commission_payment_status = db.Column(db.String(20), default='clear')  # 'clear', 'pending', 'blocked'
    commission_amount_owed = db.Column(db.Float, default=0.0)  # Current amount owed in commission


# Cart model to store user cart items
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


# Orders and order items
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, default=0.0)
    shipping_fee = db.Column(db.Float, default=0.0)
    shipping_option = db.Column(db.String(20))
    payment_method = db.Column(db.String(50))
    address = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    # workflow fields
    status = db.Column(db.String(30), default='pending')
    delivery_date = db.Column(db.DateTime, nullable=True)
    # associate order with a single shop (this app assumes orders are for one shop)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, default=0.0)
    

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    stars = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    image = db.Column(db.Text)  # Path to uploaded rating image
    description = db.Column(db.Text)  # Detailed review description
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)  # target buyer
    shop_id = db.Column(db.Integer, nullable=True)  # target shop
    message = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    read = db.Column(db.Boolean, default=False)


# Tips model for admin-managed tips/announcements
class Tip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# Commission settings model for admin-configurable commission rates
class CommissionSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    commission_rate = db.Column(db.Float, default=0.0)  # percentage (e.g., 5.0 for 5%)
    commission_type = db.Column(db.String(20), default='percentage')  # 'percentage' or 'fixed'
    threshold_amount = db.Column(db.Float, default=1000.0)  # ₱1,000 threshold
    qr_code_image = db.Column(db.String(200))  # Path to QR code image for commission payments
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# Commission payment model to track seller commission payments
class CommissionPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    amount_owed = db.Column(db.Float, nullable=False)
    payment_proof = db.Column(db.String(200))  # Path to uploaded payment proof image
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    submitted_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    reviewed_at = db.Column(db.DateTime, nullable=True)
    admin_notes = db.Column(db.Text)

# Initialize database tables
with app.app_context():
    db.create_all()
    print("Database tables created.")

# Seed sample tips if none exist
with app.app_context():
    try:
        if Tip.query.count() == 0:
            sample_tips = [
                Tip(title="Welcome to FarmHub!", body="Get started by browsing products or registering your shop."),
                Tip(title="Commission System", body="Sellers pay a commission on monthly sales above the threshold."),
                Tip(title="Product Approval", body="All products need admin approval before appearing publicly."),
            ]
            db.session.add_all(sample_tips)
            db.session.commit()
            print("Sample tips added.")
    except Exception:
        db.session.rollback()

@app.route("/seller/dashboard")
def seller_dashboard():
    """Seller dashboard with income statistics and recent sales"""
    shop_id = session.get('shop_id')
    if not shop_id:
        flash("Please log in as a shop to access the dashboard.", "warning")
        return redirect(url_for('login'))
    
    from datetime import datetime, date, timedelta
    
    # Get current time references
    today = date.today()
    start_of_today = datetime.combine(today, datetime.min.time())
    start_of_month = datetime(today.year, today.month, 1)
    start_of_year = datetime(today.year, 1, 1)
    
    # Calculate total income today
    income_today = db.session.query(func.sum(Order.total)).filter(
        Order.shop_id == shop_id,
        Order.status == 'delivered',
        Order.timestamp >= start_of_today
    ).scalar() or 0.0
    
    # Calculate total income this month
    income_month = db.session.query(func.sum(Order.total)).filter(
        Order.shop_id == shop_id,
        Order.status == 'delivered',
        Order.timestamp >= start_of_month
    ).scalar() or 0.0
    
    # Calculate total income this year
    income_year = db.session.query(func.sum(Order.total)).filter(
        Order.shop_id == shop_id,
        Order.status == 'delivered',
        Order.timestamp >= start_of_year
    ).scalar() or 0.0
    
    # Get recent 5 products sold (from delivered orders)
    recent_sales = db.session.query(
        Product.name,
        OrderItem.price,
        Order.timestamp,
        OrderItem.quantity
    ).join(OrderItem, OrderItem.product_id == Product.id
    ).join(Order, Order.id == OrderItem.order_id
    ).filter(
        Order.shop_id == shop_id,
        Order.status == 'delivered'
    ).order_by(Order.timestamp.desc()).limit(5).all()
    
    # Format recent sales data
    recent_products = []
    for sale in recent_sales:
        recent_products.append({
            'name': sale.name,
            'price': sale.price,
            'date_sold': sale.timestamp,
            'quantity': sale.quantity,
            'subtotal': sale.price * sale.quantity
        })
    
    # Get shop info
    shop = Shop.query.get(shop_id)
    
    return render_template('seller/dashboard.html',
                         income_today=income_today,
                         income_month=income_month,
                         income_year=income_year,
                         recent_products=recent_products,
                         shop=shop)

@app.route("/seller/commission-payment", methods=["GET", "POST"])
def seller_commission_payment():
    """Page for sellers to pay commission with QR code and upload proof"""
    shop_id = session.get('shop_id')
    if not shop_id:
        flash("Please log in as a shop.", "warning")
        return redirect(url_for('login'))
    
    shop = Shop.query.get(shop_id)
    commission_settings = CommissionSettings.query.first()
    
    if not commission_settings:
        flash("Commission settings not configured.", "warning")
        return redirect(url_for('seller_products'))
    
    from datetime import datetime, date
    
    # Calculate THIS MONTH's income
    today = date.today()
    start_of_month = datetime(today.year, today.month, 1)
    
    monthly_income = db.session.query(func.sum(Order.total)).filter(
        Order.shop_id == shop_id,
        Order.status == 'delivered',
        Order.timestamp >= start_of_month
    ).scalar() or 0.0
    
    # Calculate commission owed based on monthly income
    if shop.commission_amount_owed == 0 and monthly_income >= commission_settings.threshold_amount:
        if commission_settings.commission_type == 'percentage':
            shop.commission_amount_owed = (monthly_income * commission_settings.commission_rate) / 100.0
        else:
            shop.commission_amount_owed = commission_settings.commission_rate
        db.session.commit()
    
    if request.method == "POST":
        payment_proof = request.files.get('payment_proof')
        
        if not payment_proof or not allowed_file(payment_proof.filename):
            flash("Please upload a valid payment proof image.", "warning")
            return redirect(url_for('seller_commission_payment'))
        
        # Save payment proof
        filename = secure_filename(f"payment_proof_{shop_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{payment_proof.filename.rsplit('.', 1)[1].lower()}")
        proof_folder = os.path.join('static', 'images', 'payment-proofs')
        os.makedirs(proof_folder, exist_ok=True)
        proof_path = os.path.join(proof_folder, filename)
        payment_proof.save(proof_path)
        proof_path = '/' + proof_path.replace('\\', '/').replace(os.path.sep, '/')
        
        # Create commission payment record
        commission_payment = CommissionPayment(
            shop_id=shop_id,
            amount_owed=shop.commission_amount_owed,
            payment_proof=proof_path,
            status='pending'
        )
        db.session.add(commission_payment)
        
        # Update shop status
        shop.commission_payment_status = 'pending'
        db.session.commit()
        
        flash("Payment proof submitted successfully! Waiting for admin approval.", "success")
        return redirect(url_for('seller_products'))
    
    return render_template('seller/commission_payment.html',
                         shop=shop,
                         commission_settings=commission_settings)

@app.route("/seller/products")
def seller_products():
    # require shop login
    shop_id = session.get('shop_id')
    if not shop_id:
        flash("Please log in as a shop to access products.", "warning")
        return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)
    per_page = 4
    # only show products that belong to the logged-in shop (show all regardless of approval so shop can manage)
    products = Product.query.filter_by(shop_id=shop_id).paginate(page=page, per_page=per_page)
    
    # Check for out of stock and low stock products
    all_products = Product.query.filter_by(shop_id=shop_id).all()
    out_of_stock_count = sum(1 for p in all_products if p.available == 0)
    low_stock_count = sum(1 for p in all_products if 0 < p.available <= 5)
    
    # Create notifications for out of stock and low stock items (avoid duplicates)
    for product in all_products:
        if product.available == 0:
            # Check if notification already exists for this product
            existing = Notification.query.filter_by(
                shop_id=shop_id,
                message=f"Product '{product.name}' is out of stock!"
            ).first()
            if not existing:
                notification = Notification(
                    shop_id=shop_id,
                    message=f"Product '{product.name}' is out of stock!",
                    read=False
                )
                db.session.add(notification)
        elif 0 < product.available <= 5:
            # Check if notification already exists for this product
            existing = Notification.query.filter_by(
                shop_id=shop_id,
                message=f"Product '{product.name}' is low on stock (only {product.available} left)!"
            ).first()
            if not existing:
                notification = Notification(
                    shop_id=shop_id,
                    message=f"Product '{product.name}' is low on stock (only {product.available} left)!",
                    read=False
                )
                db.session.add(notification)
    
    try:
        db.session.commit()
    except:
        db.session.rollback()
    
    return render_template("seller/products.html", 
                         products=products, 
                         out_of_stock_count=out_of_stock_count,
                         low_stock_count=low_stock_count)


@app.route('/seller/product/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    # Only allow deletion if the shop is logged in and owns the product
    shop_id = session.get('shop_id')
    if not shop_id:
        flash("Please log in as a shop to perform this action.", "warning")
        return redirect(url_for('login'))

    product = Product.query.get_or_404(product_id)
    if product.shop_id != shop_id:
        flash("You don't have permission to delete this product.", "danger")
        return redirect(url_for('seller_products'))

    try:
        # If the product image is a local file, try to remove it (best-effort)
        if product.image:
            # image is stored as path like '/static/product-images/..' or similar
            img_path = product.image.lstrip('/')
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except Exception:
                    pass

        db.session.delete(product)
        db.session.commit()
        flash("Product deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete product: {e}", "danger")

    return redirect(url_for('seller_products'))

@app.route("/seller/shop/edit", methods=["GET", "POST"])
def edit_shop():
    shop_id = session.get('shop_id')
    if not shop_id:
        flash("Please log in as a shop to edit your shop details.", "warning")
        return redirect(url_for('login'))

    shop = Shop.query.get_or_404(shop_id)

    if request.method == 'POST':
        shop_name = request.form.get('shop_name')
        description = request.form.get('description')
        owner_name = request.form.get('owner_name')
        email = request.form.get('email')
        address_house = request.form.get('address_house')
        address_street = request.form.get('address_street')
        address_city = request.form.get('address_city')
        phone = request.form.get('phone')
        password = request.form.get('password')
        re_password = request.form.get('re_password')

        # Basic validation
        if password or re_password:
            if password != re_password:
                flash('Passwords do not match.', 'danger')
                return render_template('seller/edit_shop.html', shop=shop)
            else:
                shop.password = password

        # If email changed, ensure uniqueness across shops and users
        if email and email != shop.email:
            if Shop.query.filter_by(email=email).first():
                flash('Email already registered for another shop.', 'danger')
                return render_template('seller/edit_shop.html', shop=shop)
            if User.query.filter_by(email=email).first():
                flash('Email already registered as a user.', 'danger')
                return render_template('seller/edit_shop.html', shop=shop)
            shop.email = email

        # Update remaining fields
        shop.shop_name = shop_name or shop.shop_name
        shop.description = description or shop.description
        shop.owner_name = owner_name or shop.owner_name
        shop.address_house = address_house
        shop.address_street = address_street
        shop.address_city = address_city
        shop.phone = phone

        try:
            db.session.commit()
            flash('Shop details updated successfully.', 'success')
            return redirect(url_for('edit_shop'))
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to update shop: {e}', 'danger')
            return render_template('seller/edit_shop.html', shop=shop)

    # GET
    return render_template('seller/edit_shop.html', shop=shop)


@app.route("/seller/account", methods=["GET", "POST"])
def seller_account():
    shop_id = session.get('shop_id')
    if not shop_id:
        flash("Please log in as a shop to edit account details.", "warning")
        return redirect(url_for('login'))

    shop = Shop.query.get_or_404(shop_id)

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        re_password = request.form.get('re_password')
        address_house = request.form.get('address_house')
        address_street = request.form.get('address_street')
        address_city = request.form.get('address_city')

        # Validate password match if provided
        if password or re_password:
            if password != re_password:
                flash('Passwords do not match.', 'danger')
                return render_template('seller/sellers_account.html', shop=shop)
            else:
                shop.password = password

        # If email changed, ensure uniqueness across shops and users
        if email and email != shop.email:
            if Shop.query.filter_by(email=email).first():
                flash('Email already registered for another shop.', 'danger')
                return render_template('seller/sellers_account.html', shop=shop)
            if User.query.filter_by(email=email).first():
                flash('Email already registered as a user.', 'danger')
                return render_template('seller/sellers_account.html', shop=shop)
            shop.email = email

        # Update owner name
        owner_full = (first_name or '') + (' ' + last_name if last_name else '')
        shop.owner_name = owner_full.strip() or shop.owner_name
        # Update address fields
        shop.address_house = address_house
        shop.address_street = address_street
        shop.address_city = address_city

        try:
            db.session.commit()
            # update session owner name
            session['shop_owner_name'] = shop.owner_name
            session['shop_profile_image'] = shop.profile_image
            flash('Owner account updated successfully.', 'success')
            return redirect(url_for('seller_account'))
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to update owner account: {e}', 'danger')
            return render_template('seller/sellers_account.html', shop=shop)

    return render_template('seller/sellers_account.html', shop=shop)

@app.route("/seller/messages", methods=["GET", "POST"])
def seller_messages():
    shop_id = session.get('shop_id')
    if not shop_id:
        flash("Please log in as a shop to access messages.", "warning")
        return redirect(url_for('login'))

    # Get all users who have messaged this shop or been messaged by this shop
    user_ids = db.session.query(Message.sender_id).filter(Message.receiver_id == shop_id, Message.receiver_type == 'shop', Message.sender_type == 'user')
    user_ids2 = db.session.query(Message.receiver_id).filter(Message.sender_id == shop_id, Message.sender_type == 'shop', Message.receiver_type == 'user')
    all_user_ids = user_ids.union(user_ids2).distinct().subquery()
    recent_chats = db.session.query(User.id, User.first_name, User.last_name).filter(User.id.in_(db.session.query(all_user_ids))).all()

    # Get selected user to chat with
    user_id = request.args.get('user_id', type=int)
    messages = []
    user_name = None
    if user_id:
        user = User.query.get(user_id)
        user_name = f"{user.first_name} {user.last_name}" if user else None
        messages = Message.query.filter(
            ((Message.sender_id == shop_id) & (Message.sender_type == 'shop') & (Message.receiver_id == user_id) & (Message.receiver_type == 'user')) |
            ((Message.sender_id == user_id) & (Message.sender_type == 'user') & (Message.receiver_id == shop_id) & (Message.receiver_type == 'shop'))
        ).order_by(Message.timestamp).all()

    if request.method == "POST" and user_id:
        content = request.form.get("message")
        if content:
            msg = Message(
                sender_id=shop_id,
                sender_type='shop',
                receiver_id=user_id,
                receiver_type='user',
                content=content
            )
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for('seller_messages', user_id=user_id))

    return render_template("seller/messages.html", recent_chats=recent_chats, messages=messages, user_id=user_id, user_name=user_name)

@app.route("/seller/orderHistory")
def seller_order_history():
    shop_id = session.get('shop_id')
    if not shop_id:
        flash('Please log in as a shop to view orders.', 'warning')
        return redirect(url_for('login'))

    orders = Order.query.filter_by(shop_id=shop_id).order_by(Order.timestamp.desc()).all()
    order_list = []
    for o in orders:
        items = db.session.query(OrderItem, Product).join(Product, OrderItem.product_id == Product.id).filter(OrderItem.order_id == o.id).all()
        item_list = []
        for oi, product in items:
            item_list.append({
                'name': product.name,
                'image': product.image,
                'quantity': oi.quantity,
                'price': oi.price,
                'subtotal': (oi.price or 0) * (oi.quantity or 0)
            })
        buyer = User.query.get(o.user_id)
        # build buyer address from available fields
        buyer_address = None
        if buyer:
            addr_parts = [buyer.address_house, buyer.address_street, buyer.address_city]
            buyer_address = ', '.join([p for p in addr_parts if p]) if any(addr_parts) else None

        order_list.append({
            'id': o.id,
            'total': o.total,
            'shipping_fee': o.shipping_fee if hasattr(o, 'shipping_fee') else 0.0,
            'shipping_option': o.shipping_option,
            'payment_method': o.payment_method,
            'address': o.address,
            'timestamp': o.timestamp,
            'items': item_list,
            'status': o.status,
            'delivery_date': o.delivery_date,
            'buyer_name': f"{buyer.first_name} {buyer.last_name}" if buyer else None,
            'buyer_email': buyer.email if buyer else None,
            'buyer_phone': buyer.phone if buyer else None,
            'buyer_address': buyer_address
        })
    return render_template("seller/orderHistory.html", orders=order_list)

@app.route("/users/profile")
def user_profile():
    return render_template("users/profile.html")

@app.route("/users/messages", methods=["GET", "POST"])
def user_messages():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to access messages.", "warning")
        return redirect(url_for('login'))

    # Get recent shops the user has chatted with
    recent_chats = db.session.query(Message.receiver_id, Shop.shop_name)
    recent_chats = recent_chats.join(Shop, Message.receiver_id == Shop.id)
    recent_chats = recent_chats.filter(Message.sender_id == user_id, Message.sender_type == 'user', Message.receiver_type == 'shop').distinct().all()

    # Get selected shop to chat with
    shop_id = request.args.get('shop_id', type=int)
    messages = []
    shop_name = None
    if shop_id:
        shop = Shop.query.get(shop_id)
        shop_name = shop.shop_name if shop else None
        messages = Message.query.filter(
            ((Message.sender_id == user_id) & (Message.sender_type == 'user') & (Message.receiver_id == shop_id) & (Message.receiver_type == 'shop')) |
            ((Message.sender_id == shop_id) & (Message.sender_type == 'shop') & (Message.receiver_id == user_id) & (Message.receiver_type == 'user'))
        ).order_by(Message.timestamp).all()

    if request.method == "POST" and shop_id:
        content = request.form.get("message")
        if content:
            msg = Message(
                sender_id=user_id,
                sender_type='user',
                receiver_id=shop_id,
                receiver_type='shop',
                content=content
            )
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for('user_messages', shop_id=shop_id))

    return render_template("users/messages.html", recent_chats=recent_chats, messages=messages, shop_id=shop_id, shop_name=shop_name)

@app.route("/users/ratings")
def user_ratings():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view your ratings.', 'warning')
        return redirect(url_for('login'))

    # get ratings for this user joined with product
    rows = db.session.query(Rating, Product).join(Product, Rating.product_id == Product.id).filter(Rating.user_id == user_id).order_by(Rating.timestamp.desc()).all()
    rated_items = []
    for rating, product in rows:
        # prepare an image URL for template
        if product.image:
            if str(product.image).startswith('/'):
                image_url = product.image
            else:
                # assume filename stored
                image_url = url_for('static', filename='product-images/' + product.image)
        else:
            image_url = url_for('static', filename='images/product-images/banana-lakatan.jpg')
        # format timestamp for display
        try:
            rated_date_str = rating.timestamp.strftime('%b %d, %Y %H:%M') if rating.timestamp else None
        except Exception:
            rated_date_str = str(rating.timestamp)
        rated_items.append({
            'name': product.name,
            'image_url': image_url,
            'category': product.product_type,
            'rated_date': rated_date_str,
            'stars': rating.stars,
            'comment': rating.comment,
            'description': rating.description,
            'rating_image': rating.image
        })
    return render_template("users/ratings.html", rated_items=rated_items)

@app.route("/users/orderHistory")
def user_order_history():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view order history.', 'warning')
        return redirect(url_for('login'))

    # query orders for the user
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.timestamp.desc()).all()

    # build a list of orders with items
    order_list = []
    for o in orders:
        items = db.session.query(OrderItem, Product).join(Product, OrderItem.product_id == Product.id).filter(OrderItem.order_id == o.id).all()
        item_list = []
        for oi, product in items:
            # check if current user already rated this product for this order
            user_rating = None
            user_id = session.get('user_id')
            if user_id:
                user_rating = Rating.query.filter_by(user_id=user_id, product_id=product.id, order_id=o.id).first()
            item_list.append({
                'product_id': product.id,
                'name': product.name,
                'image': product.image,
                'quantity': oi.quantity,
                'price': oi.price,
                'subtotal': (oi.price or 0) * (oi.quantity or 0),
                'user_rated': True if user_rating else False,
                'user_rating': user_rating.stars if user_rating else None
            })
        # populate base order dict
        order_dict = {
            'id': o.id,
            'total': o.total,
            'shipping_fee': o.shipping_fee if hasattr(o, 'shipping_fee') else 0.0,
            'shipping_option': o.shipping_option,
            'payment_method': o.payment_method,
            'address': o.address,
            'timestamp': o.timestamp,
            'items': item_list,
            'status': o.status,
            'delivery_date': o.delivery_date,
            'shop_id': o.shop_id,
            # include seller/shop details so template can show shop location in the tracking modal
            'seller_name': None,
            'seller_address': None,
            'seller_email': None,
            'seller_phone': None
        }
        # if order is tied to a shop, fetch shop info
        if o.shop_id:
            shop = Shop.query.get(o.shop_id)
            if shop:
                seller_addr_parts = [shop.address_house, shop.address_street, shop.address_city]
                seller_addr = ' '.join([p for p in seller_addr_parts if p])
                order_dict['seller_name'] = shop.shop_name
                order_dict['seller_address'] = seller_addr
                order_dict['seller_email'] = shop.email
                order_dict['seller_phone'] = shop.phone

        # include buyer contact info (current user)
        try:
            buyer = User.query.get(user_id)
            if buyer:
                order_dict['buyer_email'] = buyer.email
                order_dict['buyer_phone'] = buyer.phone
            else:
                order_dict['buyer_email'] = None
                order_dict['buyer_phone'] = None
        except Exception:
            order_dict['buyer_email'] = None
            order_dict['buyer_phone'] = None

        order_list.append(order_dict)
    now = datetime.utcnow()
    return render_template("users/orderHistory.html", orders=order_list, now=now)


@app.route('/seller/order/<int:order_id>/confirm', methods=['POST'])
def seller_confirm_order(order_id):
    shop_id = session.get('shop_id')
    if not shop_id:
        flash('Please log in as a shop.', 'warning')
        return redirect(url_for('login'))
    order = Order.query.get_or_404(order_id)
    if order.shop_id != shop_id:
        flash('Not authorized.', 'danger')
        return redirect(url_for('seller_order_history'))

    # expect delivery_date in form YYYY-MM-DD
    delivery_date_str = request.form.get('delivery_date')
    try:
        from datetime import date
        delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d') if delivery_date_str else None
        order.delivery_date = delivery_date
        order.status = 'confirmed'
        db.session.commit()
        
        # Check if delivery is today
        today = date.today()
        is_today = False
        delivery_msg = f'will be delivered on {delivery_date.date()}'
        
        if delivery_date and delivery_date.date() == today:
            is_today = True
            delivery_msg = 'will be delivered TODAY'
        
        # Notify buyer
        note = Notification(
            user_id=order.user_id, 
            shop_id=None, 
            message=f'Your order #{order.id} has been confirmed by the seller and {delivery_msg}.'
        )
        db.session.add(note)
        db.session.commit()
        
        flash('Order confirmed and buyer notified.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to confirm order: {e}', 'danger')
    return redirect(url_for('seller_order_history'))


@app.route('/seller/order/<int:order_id>/cancel', methods=['POST'])
def seller_cancel_order(order_id):
    shop_id = session.get('shop_id')
    if not shop_id:
        flash('Please log in as a shop.', 'warning')
        return redirect(url_for('login'))
    order = Order.query.get_or_404(order_id)
    if order.shop_id != shop_id:
        flash('Not authorized.', 'danger')
        return redirect(url_for('seller_order_history'))
    try:
        order.status = 'cancelled'
        db.session.commit()
        note = Notification(user_id=order.user_id, shop_id=None, message=f'Your order #{order.id} was cancelled by the seller.')
        db.session.add(note)
        db.session.commit()
        flash('Order cancelled and buyer notified.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to cancel order: {e}', 'danger')
    return redirect(url_for('seller_order_history'))


@app.route('/users/order/<int:order_id>/mark_received', methods=['POST'])
def user_mark_received(order_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in.', 'warning')
        return redirect(url_for('login'))
    order = Order.query.get_or_404(order_id)
    if order.user_id != user_id:
        flash('Not authorized.', 'danger')
        return redirect(url_for('user_order_history'))
    try:
        # Mark order as delivered
        order.status = 'delivered'
        
        # Update shop's total income (no automatic commission deduction)
        if order.shop_id:
            shop = Shop.query.get(order.shop_id)
            if shop:
                order_total = order.total or 0.0
                # Add full amount to shop's total income
                shop.total_income += order_total
        
        db.session.commit()
        
        # Notify seller
        note = Notification(user_id=None, shop_id=order.shop_id, message=f'Order #{order.id} was marked received by the buyer.')
        db.session.add(note)
        db.session.commit()
        flash('Order marked as received and seller notified.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to update order: {e}', 'danger')
    return redirect(url_for('user_order_history'))


@app.route('/seller/notifications')
def seller_notifications():
    """Show notifications for sellers (shop owners)"""
    shop_id = session.get('shop_id')
    if not shop_id:
        flash('Please log in as a shop to view notifications.', 'warning')
        return redirect(url_for('login'))
    
    # Get notifications for this shop
    notifications = Notification.query.filter_by(shop_id=shop_id).order_by(Notification.timestamp.desc()).all()
    
    # Format notifications for template
    formatted_notifications = []
    for notif in notifications:
        # Determine notification type and icon
        notif_type = "Order"
        icon = "📦"
        status_color = "blue"
        
        if "out of stock" in notif.message.lower():
            notif_type = "Out of Stock"
            icon = "🚫"
            status_color = "red"
        elif "low on stock" in notif.message.lower():
            notif_type = "Low Stock"
            icon = "⚠️"
            status_color = "orange"
        elif "approved" in notif.message.lower() or "confirmed" in notif.message.lower():
            notif_type = "Product Approved"
            icon = "✅"
            status_color = "green"
        elif "new order" in notif.message.lower():
            notif_type = "New Order"
            icon = "🛒"
            status_color = "orange"
        elif "received" in notif.message.lower() or "delivered" in notif.message.lower():
            notif_type = "Order Delivered"
            icon = "📬"
            status_color = "gray"
        
        formatted_notifications.append({
            'id': notif.id,
            'type': notif_type,
            'icon': icon,
            'message': notif.message,
            'date': notif.timestamp.strftime('%Y-%m-%d %H:%M') if notif.timestamp else '',
            'status_color': status_color,
            'read': notif.read
        })
    
    return render_template('seller/notifications.html', notifications=formatted_notifications)


@app.route('/seller/notifications/count')
def seller_notification_count():
    """API endpoint to get unread notification count for sellers"""
    shop_id = session.get('shop_id')
    if not shop_id:
        return jsonify({'count': 0})
    
    # Count unread notifications (including stock alerts)
    unread_count = Notification.query.filter_by(shop_id=shop_id, read=False).count()
    return jsonify({'count': unread_count})


@app.route('/users/notifications')
def user_notifications():
    """Show notifications for users (buyers)"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view notifications.', 'warning')
        return redirect(url_for('login'))
    
    # Get notifications for this user
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.timestamp.desc()).all()
    
    # Get today's date for delivery checks
    from datetime import date
    today = date.today()
    
    # Format notifications for template
    formatted_notifications = []
    for notif in notifications:
        # Determine notification type and status
        notif_type = "Order Update"
        icon = "📦"
        status = "Info"
        status_color = "blue"
        
        if "confirmed" in notif.message.lower() or "approved" in notif.message.lower():
            notif_type = "Order Confirmed"
            icon = "✅"
            status = "Confirmed"
            status_color = "green"
        elif "shipped" in notif.message.lower():
            notif_type = "Order Update"
            icon = "🚚"
            status = "Shipped"
            status_color = "green"
        elif "cancelled" in notif.message.lower():
            notif_type = "Order Cancelled"
            icon = "❌"
            status = "Cancelled"
            status_color = "red"
        elif "delivered" in notif.message.lower() or "delivery" in notif.message.lower():
            notif_type = "Delivery"
            icon = "📬"
            status = "Delivered Today"
            status_color = "gray"
        
        formatted_notifications.append({
            'id': notif.id,
            'type': notif_type,
            'icon': icon,
            'message': notif.message,
            'date': notif.timestamp.strftime('%Y-%m-%d %H:%M') if notif.timestamp else '',
            'status': status,
            'status_color': status_color,
            'read': notif.read
        })
    
    return render_template('users/notifications.html', notifications=formatted_notifications)


@app.route('/notifications/list')
def notifications_list():
    # show notifications for current user/shop
    user_id = session.get('user_id')
    shop_id = session.get('shop_id')
    
    if user_id:
        return redirect(url_for('user_notifications'))
    elif shop_id:
        return redirect(url_for('seller_notifications'))
    else:
        flash('Please log in to view notifications.', 'warning')
        return redirect(url_for('login'))

@app.route("/users/account/edit")
def user_account_edit():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to edit account details.", "warning")
        return redirect(url_for('login'))

    user = User.query.get_or_404(user_id)
    return render_template("users/edit_account.html", user=user)


@app.route("/users/account", methods=["GET", "POST"])
def user_account():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to edit account details.", "warning")
        return redirect(url_for('login'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        re_password = request.form.get('re_password')
        address_house = request.form.get('address_house')
        address_street = request.form.get('address_street')
        address_city = request.form.get('address_city')

        # Validate password match if provided
        if password or re_password:
            if password != re_password:
                flash('Passwords do not match.', 'account_error')
                return render_template('users/edit_account.html', user=user)
            else:
                user.password = password

        # If email changed, ensure uniqueness across users and shops
        if email and email != user.email:
            if User.query.filter_by(email=email).first():
                flash('Email already registered for another user.', 'account_error')
                return render_template('users/edit_account.html', user=user)
            if Shop.query.filter_by(email=email).first():
                flash('Email already registered as a shop.', 'account_error')
                return render_template('users/edit_account.html', user=user)
            user.email = email

        # Update name fields
        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
        # Update address fields
        user.address_house = address_house
        user.address_street = address_street
        user.address_city = address_city

        try:
            db.session.commit()
            # update session user name/email
            session['user_first_name'] = user.first_name
            session['user_last_name'] = user.last_name
            session['user_email'] = user.email
            session['user_profile_image'] = user.profile_image
            flash('Account updated successfully.', 'account_success')
            return redirect(url_for('user_account'))
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to update account: {e}', 'account_error')
            return render_template('users/edit_account.html', user=user)

    return render_template('users/edit_account.html', user=user)

@app.route("/users/upload_profile_image", methods=["POST"])
def upload_user_profile_image():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to upload profile image.", "warning")
        return redirect(url_for('login'))

    if 'profile_image' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(request.referrer or url_for('user_account'))

    file = request.files['profile_image']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(request.referrer or url_for('user_account'))

    if file and allowed_file(file.filename):
        try:
            user = User.query.get_or_404(user_id)
            
            # Remove old profile image if it exists
            if user.profile_image:
                old_path = user.profile_image.lstrip('/')
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception:
                        pass

            filename = secure_filename(file.filename)
            # Add timestamp to filename to avoid conflicts
            timestamp = str(int(datetime.utcnow().timestamp()))
            name, ext = os.path.splitext(filename)
            filename = f"user_{user_id}_{timestamp}{ext}"
            
            # Ensure profile upload folder exists
            os.makedirs(app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)
            
            file_path = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Store relative path in database
            user.profile_image = '/' + file_path.replace('\\', '/').replace(os.path.sep, '/')
            db.session.commit()
            
            # Update session
            session['user_profile_image'] = user.profile_image
            
            flash('Profile picture updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to upload profile picture: {e}', 'danger')
    else:
        flash('Invalid file type. Please upload a PNG, JPG, JPEG, or GIF file.', 'danger')

    return redirect(request.referrer or url_for('user_account'))

@app.route("/seller/upload_profile_image", methods=["POST"])
def upload_shop_profile_image():
    shop_id = session.get('shop_id')
    if not shop_id:
        flash("Please log in as a shop to upload profile image.", "warning")
        return redirect(url_for('login'))

    if 'profile_image' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(request.referrer or url_for('seller_account'))

    file = request.files['profile_image']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(request.referrer or url_for('seller_account'))

    if file and allowed_file(file.filename):
        try:
            shop = Shop.query.get_or_404(shop_id)
            
            # Remove old profile image if it exists
            if shop.profile_image:
                old_path = shop.profile_image.lstrip('/')
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception:
                        pass

            filename = secure_filename(file.filename)
            # Add timestamp to filename to avoid conflicts
            timestamp = str(int(datetime.utcnow().timestamp()))
            name, ext = os.path.splitext(filename)
            filename = f"shop_{shop_id}_{timestamp}{ext}"
            
            # Ensure profile upload folder exists
            os.makedirs(app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)
            
            file_path = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Store relative path in database
            shop.profile_image = '/' + file_path.replace('\\', '/').replace(os.path.sep, '/')
            db.session.commit()
            
            # Update session
            session['shop_profile_image'] = shop.profile_image
            
            flash('Profile picture updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to upload profile picture: {e}', 'danger')
    else:
        flash('Invalid file type. Please upload a PNG, JPG, JPEG, or GIF file.', 'danger')

    return redirect(request.referrer or url_for('seller_account'))

@app.route("/admin/upload_profile_image", methods=["POST"])
def upload_admin_profile_image():
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to upload profile image.', 'warning')
        return redirect(url_for('login'))

    if 'profile_image' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(request.referrer or url_for('admin_dashboard'))

    file = request.files['profile_image']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(request.referrer or url_for('admin_dashboard'))

    if file and allowed_file(file.filename):
        try:
            # Remove old admin profile image if it exists
            old_admin_image = session.get('admin_profile_image')
            if old_admin_image:
                old_path = old_admin_image.lstrip('/')
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception:
                        pass

            filename = secure_filename(file.filename)
            # Add timestamp to filename to avoid conflicts
            timestamp = str(int(datetime.utcnow().timestamp()))
            name, ext = os.path.splitext(filename)
            filename = f"admin_{timestamp}{ext}"
            
            # Ensure profile upload folder exists
            os.makedirs(app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)
            
            file_path = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Store relative path in session
            session['admin_profile_image'] = '/' + file_path.replace('\\', '/').replace(os.path.sep, '/')
            
            flash('Profile picture updated successfully!', 'success')
        except Exception as e:
            flash(f'Failed to upload profile picture: {e}', 'danger')
    else:
        flash('Invalid file type. Please upload a PNG, JPG, JPEG, or GIF file.', 'danger')

    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route("/")
def home():
    # if 'user_id' not in session:
    #     flash("Please log in to access this page.", "warning")
    #     return redirect(url_for('login'))
    return render_template("home.html")

@app.route("/allProducts")
def all_products():
    # optional filters:
    # - product type via query string: /allProducts?type=Crops
    # - keyword search: /allProducts?q=tomato
    product_type = request.args.get('type')
    q = (request.args.get('q') or '').strip()
    # only show approved products to public
    query = db.session.query(Product, Shop.shop_name).join(Shop, Product.shop_id == Shop.id).filter(Product.approved == True)
    if product_type:
        # filter by product_type (case-insensitive match)
        query = query.filter(db.func.lower(Product.product_type) == product_type.lower())
    if q:
        like = f"%{q}%"
        # search by product name, product type, or shop name
        query = query.filter(
            (Product.name.ilike(like)) |
            (Product.product_type.ilike(like)) |
            (Shop.shop_name.ilike(like))
        )
    products = query.all()
    # pass the selected type and query to the template for display (None when showing all)
    return render_template("allProducts.html", products=products, selected_type=product_type, q=q)

@app.route("/shops")
def shops():
    # optional keyword search: /shops?q=market
    q = (request.args.get('q') or '').strip()
    if q:
        like = f"%{q}%"
        shops = Shop.query.filter((Shop.shop_name.ilike(like)) | (Shop.description.ilike(like))).all()
    else:
        shops = Shop.query.all()
    # compute average rating per shop (average of product ratings via ratings table)
    shops_with_avg = []
    for shop in shops:
        avg = db.session.query(func.avg(Rating.stars)).join(Product, Rating.product_id == Product.id).filter(Product.shop_id == shop.id).scalar()
        shop_avg = float(avg) if avg is not None else 0.0  # Default to 0.0 instead of None
        # attach to object for template convenience
        setattr(shop, 'avg_rating', shop_avg)
        shops_with_avg.append(shop)
    return render_template("shops.html", shops=shops_with_avg, q=q)

@app.route('/api/suggest')
def api_suggest():
    """Return up to 5 suggestions for products or shops as the user types.

    Query params:
      - scope: 'products' | 'shops' (default: 'products')
      - q: search text
    Response: JSON array of { label, url, type, id }
    """
    scope = (request.args.get('scope') or 'all').lower()
    q = (request.args.get('q') or '').strip()
    results = []
    if not q:
        return jsonify(results)

    like = f"%{q}%"
    try:
        if scope == 'shops':
            rows = Shop.query.filter((Shop.shop_name.ilike(like)) | (Shop.description.ilike(like)))\
                             .order_by(Shop.shop_name.asc())\
                             .limit(5).all()
            for s in rows:
                # build shop image url
                if s.profile_image:
                    if str(s.profile_image).startswith('/'):
                        shop_img = s.profile_image
                    else:
                        shop_img = url_for('static', filename=f"images/profiles/{s.profile_image}")
                else:
                    shop_img = url_for('static', filename='images/logo.png')
                results.append({
                    'label': s.shop_name,
                    'url': url_for('view_shop', shop_id=s.id),
                    'type': 'shop',
                    'id': s.id,
                    'image': shop_img,
                    'shop_image': shop_img
                })
        elif scope == 'products':
            # products scope (default): only approved products
            rows = db.session.query(Product, Shop)\
                .join(Shop, Product.shop_id == Shop.id)\
                .filter(Product.approved == True)\
                .filter((Product.name.ilike(like)) | (Product.product_type.ilike(like)))\
                .order_by(Product.name.asc())\
                .limit(5).all()
            for p, shop in rows:
                # product image url
                if p.image:
                    prod_img = p.image if str(p.image).startswith('/') else '/' + str(p.image).lstrip('/\\')
                else:
                    prod_img = url_for('static', filename='images/product-images/kalabasa.jpg')
                # shop image url
                if shop.profile_image:
                    if str(shop.profile_image).startswith('/'):
                        shop_img = shop.profile_image
                    else:
                        shop_img = url_for('static', filename=f"images/profiles/{shop.profile_image}")
                else:
                    shop_img = url_for('static', filename='images/logo.png')
                results.append({
                    'label': f"{p.name} — {shop.shop_name}",
                    'url': url_for('view_product', product_id=p.id),
                    'type': 'product',
                    'id': p.id,
                    'image': prod_img,
                    'shop_image': shop_img
                })
        else:
            # combined: return up to 5 items mixed
            prod_rows = db.session.query(Product, Shop)\
                .join(Shop, Product.shop_id == Shop.id)\
                .filter(Product.approved == True)\
                .filter((Product.name.ilike(like)) | (Product.product_type.ilike(like)))\
                .order_by(Product.name.asc())\
                .limit(5).all()
            shop_rows = Shop.query.filter((Shop.shop_name.ilike(like)) | (Shop.description.ilike(like)))\
                .order_by(Shop.shop_name.asc())\
                .limit(5).all()
            # Prefer mixing: take up to 3 products and up to 2 shops, then fill to 5
            prod_take = prod_rows[:3]
            shop_take = shop_rows[:2]
            combined = []
            for p, shop in prod_take:
                # product image url
                if p.image:
                    prod_img = p.image if str(p.image).startswith('/') else '/' + str(p.image).lstrip('/\\')
                else:
                    prod_img = url_for('static', filename='images/product-images/kalabasa.jpg')
                # shop image url
                if shop.profile_image:
                    if str(shop.profile_image).startswith('/'):
                        shop_img = shop.profile_image
                    else:
                        shop_img = url_for('static', filename=f"images/profiles/{shop.profile_image}")
                else:
                    shop_img = url_for('static', filename='images/logo.png')
                combined.append({'label': f"{p.name} — {shop.shop_name}", 'url': url_for('view_product', product_id=p.id), 'type': 'product', 'id': p.id, 'image': prod_img, 'shop_image': shop_img})
            for s in shop_take:
                if s.profile_image:
                    if str(s.profile_image).startswith('/'):
                        shop_img2 = s.profile_image
                    else:
                        shop_img2 = url_for('static', filename=f"images/profiles/{s.profile_image}")
                else:
                    shop_img2 = url_for('static', filename='images/logo.png')
                combined.append({'label': s.shop_name, 'url': url_for('view_shop', shop_id=s.id), 'type': 'shop', 'id': s.id, 'image': shop_img2, 'shop_image': shop_img2})
            # fill remaining up to 5
            if len(combined) < 5:
                # add remaining products then shops
                for p, shop in prod_rows[3:]:
                    if len(combined) >= 5: break
                    if p.image:
                        prod_img = p.image if str(p.image).startswith('/') else '/' + str(p.image).lstrip('/\\')
                    else:
                        prod_img = url_for('static', filename='images/product-images/kalabasa.jpg')
                    if shop.profile_image:
                        if str(shop.profile_image).startswith('/'):
                            shop_img = shop.profile_image
                        else:
                            shop_img = url_for('static', filename=f"images/profiles/{shop.profile_image}")
                    else:
                        shop_img = url_for('static', filename='images/logo.png')
                    combined.append({'label': f"{p.name} — {shop.shop_name}", 'url': url_for('view_product', product_id=p.id), 'type': 'product', 'id': p.id, 'image': prod_img, 'shop_image': shop_img})
                for s in shop_rows[2:]:
                    if len(combined) >= 5: break
                    if s.profile_image:
                        if str(s.profile_image).startswith('/'):
                            shop_img2 = s.profile_image
                        else:
                            shop_img2 = url_for('static', filename=f"images/profiles/{s.profile_image}")
                    else:
                        shop_img2 = url_for('static', filename='images/logo.png')
                    combined.append({'label': s.shop_name, 'url': url_for('view_shop', shop_id=s.id), 'type': 'shop', 'id': s.id, 'image': shop_img2, 'shop_image': shop_img2})
            results = combined
    except Exception:
        # fail closed with empty suggestions
        results = []

    return jsonify(results)

@app.route('/search')
def unified_search():
    """Show combined results for products and shops for a query q."""
    q = (request.args.get('q') or '').strip()
    products = []
    shops = []
    if q:
        like = f"%{q}%"
        products = db.session.query(Product, Shop.shop_name)\
            .join(Shop, Product.shop_id == Shop.id)\
            .filter(Product.approved == True)\
            .filter((Product.name.ilike(like)) | (Product.product_type.ilike(like)) | (Shop.shop_name.ilike(like)))\
            .all()
        shops = Shop.query.filter((Shop.shop_name.ilike(like)) | (Shop.description.ilike(like))).all()
    return render_template('search.html', q=q, products=products, shops=shops)

@app.route("/viewShop/<int:shop_id>")
def view_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    # when a public user views a shop, only show approved products; the shop owner sees all via seller_products
    # support optional filtering by product type via querystring: /viewShop/<id>?type=Crops
    requested_type = request.args.get('type')
    if requested_type and requested_type.lower() not in ('all', 'all products', 'home'):
        products = Product.query.filter_by(shop_id=shop_id, approved=True).filter(func.lower(Product.product_type) == requested_type.lower()).all()
        selected_type = requested_type
    else:
        products = Product.query.filter_by(shop_id=shop_id, approved=True).all()
        # normalize selected_type to None or 'All'
        selected_type = None if not requested_type or requested_type.lower() in ('home',) else ('All' if requested_type and requested_type.lower() in ('all','all products') else None)
    # compute average rating for this shop (from ratings on its products)
    shop_rating = 0.0  # Default to 0.0 instead of None
    try:
        avg = db.session.query(func.avg(Rating.stars)).join(Product, Rating.product_id == Product.id).filter(Product.shop_id == shop.id).scalar()
        if avg is not None:
            shop_rating = float(avg)
    except Exception:
        shop_rating = 0.0  # Default to 0.0 instead of None

    # compute total number of ratings for display
    try:
        rating_count = db.session.query(func.count(Rating.id)).join(Product, Rating.product_id == Product.id).filter(Product.shop_id == shop.id).scalar() or 0
    except Exception:
        rating_count = 0

    # derive a friendly "joined" string from earliest activity (rating or order) if available
    joined_str = 'Unknown'
    try:
        earliest = db.session.query(func.min(Rating.timestamp)).join(Product, Rating.product_id == Product.id).filter(Product.shop_id == shop.id).scalar()
        if not earliest:
            earliest = db.session.query(func.min(Order.timestamp)).filter(Order.shop_id == shop.id).scalar()
        if earliest:
            now = datetime.utcnow()
            # earliest may be a string in some edge cases; ensure it's a datetime
            try:
                delta = now - earliest
            except Exception:
                # try parsing if it's a string
                try:
                    parsed = datetime.fromisoformat(str(earliest))
                    delta = now - parsed
                except Exception:
                    delta = None

            if delta is None:
                joined_str = 'Unknown'
            else:
                days = delta.days
                if days < 1:
                    joined_str = 'Today'
                elif days < 30:
                    joined_str = f'{days} day{'' if days == 1 else 's'} ago'
                elif days < 365:
                    months = days // 30
                    joined_str = f'{months} month{'' if months == 1 else 's'} ago'
                else:
                    years = days // 365
                    joined_str = f'{years} year{'' if years == 1 else 's'} ago'
    except Exception:
        joined_str = 'Unknown'

    return render_template("viewShop.html", shop=shop, products=products, shop_rating=shop_rating, rating_count=rating_count, joined_str=joined_str, selected_type=selected_type)

@app.route("/help")
def help():
    return render_template("help.html")


# Help article routes - maps article slugs to template files
HELP_ARTICLES = {
    # Getting Started
    'create_account': 'help/create_account.html',
    'login_logout': 'help/login_logout.html',
    'update_profile': 'help/update_profile.html',
    'reset_password': 'help/reset_password.html',
    # Browsing Products
    'search_products': 'help/search_products.html',
    'filter_category': 'help/filter_category.html',
    'view_product_details': 'help/view_product_details.html',
    'check_availability': 'help/check_availability.html',
    # Ordering
    'add_to_cart': 'help/add_to_cart.html',
    'edit_cart': 'help/edit_cart.html',
    'place_order': 'help/place_order.html',
    'use_vouchers': 'help/use_vouchers.html',
    'track_order': 'help/track_order.html',
    # Delivery & Pickup
    'how_delivery_works': 'help/how_delivery_works.html',
    'delivery_options': 'help/delivery_options.html',
    'update_delivery_address': 'help/update_delivery_address.html',
    'track_delivery': 'help/track_delivery.html',
    'delivery_times': 'help/delivery_times.html',
    # Farmers & Sellers
    'register_seller': 'help/register_seller.html',
    'list_products': 'help/list_products.html',
    'manage_inventory': 'help/manage_inventory.html',
    'view_sales': 'help/view_sales.html',
    'how_commission_works': 'help/how_commission_works.html',
    # Returns & Refunds
    'request_return': 'help/request_return.html',
    'refund_policy': 'help/refund_policy.html',
    'wrong_damaged_item': 'help/wrong_damaged_item.html',
    # Safety & Support
    'product_quality': 'help/product_quality.html',
    'privacy_security': 'help/privacy_security.html',
    'contact_support': 'help/contact_support.html',
    'faq': 'help/faq.html',
}

@app.route("/help/<article>")
def help_article(article):
    """Render individual help articles"""
    if article in HELP_ARTICLES:
        return render_template(HELP_ARTICLES[article])
    else:
        flash("Help article not found.", "warning")
        return redirect(url_for('help'))


@app.route('/tips')
def public_tips():
    # public view of admin tips with optional search
    q = request.args.get('q', '')
    if q:
        pattern = f"%{q}%"
        tips = Tip.query.filter((Tip.title.ilike(pattern)) | (Tip.body.ilike(pattern))).order_by(Tip.created_at.desc()).all()
    else:
        tips = Tip.query.order_by(Tip.created_at.desc()).all()
    return render_template('tips.html', tips=tips, q=q)

@app.route("/product/<int:product_id>")
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    shop = Shop.query.get(product.shop_id)
    shop_name = shop.shop_name if shop else "Unknown Shop"
    # pass the full shop object so the template can link to the shop page
    # If product is not approved, only allow shop owner or admin to view it
    if not product.approved:
        # allow admin
        if not (session.get('admin_logged_in') or session.get('shop_id') == product.shop_id):
            flash('Product not available.', 'warning')
            return redirect(url_for('all_products'))
    # compute shop average rating from all ratings of products belonging to this shop
    shop_rating = 0.0  # Default to 0.0 instead of None
    if shop:
        avg = db.session.query(func.avg(Rating.stars)).join(Product, Rating.product_id == Product.id).filter(Product.shop_id == shop.id).scalar()
        if avg is not None:
            shop_rating = float(avg)

    # Get product ratings with user information
    ratings_query = db.session.query(Rating, User).join(User, Rating.user_id == User.id).filter(Rating.product_id == product_id).order_by(Rating.timestamp.desc())
    product_ratings = []
    for rating, user in ratings_query:
        # Build user display name
        user_display_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else "Anonymous User"
        
        # Prepare rating data for template
        rating_data = {
            'id': rating.id,
            'stars': rating.stars,
            'comment': rating.comment,
            'description': rating.description,
            'image': rating.image,
            'timestamp': rating.timestamp,
            'user_name': user_display_name,
            'user_profile_image': user.profile_image
        }
        product_ratings.append(rating_data)

    # Attach current user info (if logged in) so templates can show user address conveniently
    current_user_obj = None
    user_id = session.get('user_id')
    if user_id:
        try:
            current_user_obj = User.query.get(user_id)
            # Build a single-address string from stored address parts for template convenience
            addr_parts = [getattr(current_user_obj, 'address_house', None), getattr(current_user_obj, 'address_street', None), getattr(current_user_obj, 'address_city', None)]
            addr_joined = ' '.join([p for p in (part.strip() for part in addr_parts if part) if p]) if current_user_obj else None
            # attach a transient `address` attribute the template expects
            if current_user_obj:
                setattr(current_user_obj, 'address', addr_joined)
        except Exception:
            current_user_obj = None

    return render_template("viewProduct.html", product=product, shop_name=shop_name, shop=shop, shop_rating=shop_rating, current_user=current_user_obj, product_ratings=product_ratings)


@app.route('/rate_product', methods=['POST'])
def rate_product():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to rate products.', 'warning')
        return redirect(url_for('login'))

    product_id = request.form.get('product_id', type=int)
    order_id = request.form.get('order_id', type=int)
    stars = request.form.get('stars', type=int)
    comment = request.form.get('comment')
    description = request.form.get('description')

    if not product_id or not stars:
        flash('Invalid rating submission.', 'danger')
        return redirect(request.referrer or url_for('user_order_history'))

    try:
        # Handle image upload
        image_path = None
        if 'rating_image' in request.files:
            file = request.files['rating_image']
            if file and file.filename != '' and allowed_file(file.filename):
                # Create a secure filename
                filename = secure_filename(file.filename)
                # Add timestamp and user ID to avoid conflicts
                timestamp = str(int(datetime.utcnow().timestamp()))
                name, ext = os.path.splitext(filename)
                filename = f"rating_{user_id}_{product_id}_{timestamp}{ext}"
                
                # Ensure rating images folder exists
                rating_folder = os.path.join('static', 'images', 'rating-images')
                os.makedirs(rating_folder, exist_ok=True)
                
                file_path = os.path.join(rating_folder, filename)
                file.save(file_path)
                
                # Store relative path for database
                image_path = '/' + file_path.replace('\\', '/').replace(os.path.sep, '/')

        existing = Rating.query.filter_by(user_id=user_id, product_id=product_id, order_id=order_id).first()
        if existing:
            # Remove old image if updating with new one
            if image_path and existing.image:
                old_path = existing.image.lstrip('/')
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception:
                        pass
            
            existing.stars = stars
            existing.comment = comment
            existing.description = description
            if image_path:
                existing.image = image_path
            existing.timestamp = datetime.utcnow()
        else:
            new_rating = Rating(
                user_id=user_id, 
                product_id=product_id, 
                order_id=order_id, 
                stars=stars, 
                comment=comment,
                description=description,
                image=image_path
            )
            db.session.add(new_rating)

        db.session.flush()

        # recompute product average
        avg = db.session.query(func.avg(Rating.stars)).filter(Rating.product_id == product_id).scalar()
        product = Product.query.get(product_id)
        if avg is not None and product:
            product.rating = float(avg)

        db.session.commit()

        flash('Thank you for your detailed rating and review!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to submit rating: {e}', 'danger')

    return redirect(request.referrer or url_for('user_order_history'))

from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('static', 'product-images')
PROFILE_UPLOAD_FOLDER = os.path.join('static', 'images', 'profiles')
RATING_UPLOAD_FOLDER = os.path.join('static', 'images', 'rating-images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROFILE_UPLOAD_FOLDER'] = PROFILE_UPLOAD_FOLDER
app.config['RATING_UPLOAD_FOLDER'] = RATING_UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/seller/addProduct", methods=["GET", "POST"])
def add_product():
    shop_id = session.get('shop_id')
    if not shop_id:
        flash("You must be logged in as a shop to add products.", "danger")
        return redirect(url_for("login"))
    
    from datetime import datetime, date
    
    # Check if shop needs to pay commission before adding products
    shop = Shop.query.get(shop_id)
    commission_settings = CommissionSettings.query.first()
    
    # Only block if status is 'blocked' (commission owed but not submitted)
    # Allow if 'pending' (payment proof submitted, waiting for approval)
    if shop and shop.commission_payment_status == 'blocked':
        flash("You need to submit commission payment proof before adding products.", "warning")
        return redirect(url_for("seller_commission_payment"))
    
    # Check if shop has exceeded MONTHLY threshold and needs to pay commission
    if shop and commission_settings and shop.commission_payment_status == 'clear':
        # Calculate THIS MONTH's income
        today = date.today()
        start_of_month = datetime(today.year, today.month, 1)
        
        monthly_income = db.session.query(func.sum(Order.total)).filter(
            Order.shop_id == shop_id,
            Order.status == 'delivered',
            Order.timestamp >= start_of_month
        ).scalar() or 0.0
        
        # Check if they have an approved payment for this month
        approved_payment_this_month = CommissionPayment.query.filter(
            CommissionPayment.shop_id == shop_id,
            CommissionPayment.status == 'approved',
            CommissionPayment.reviewed_at >= start_of_month
        ).first()
        
        # If monthly income >= threshold and no approved payment this month, require commission payment
        if monthly_income >= commission_settings.threshold_amount and not approved_payment_this_month:
            # Calculate commission amount if not already set
            if shop.commission_amount_owed == 0:
                if commission_settings.commission_type == 'percentage':
                    shop.commission_amount_owed = (monthly_income * commission_settings.commission_rate) / 100.0
                else:
                    shop.commission_amount_owed = commission_settings.commission_rate
                shop.commission_payment_status = 'blocked'
                db.session.commit()
            
            # Block and redirect to payment
            if request.method == "POST":
                flash("You've reached the threshold this month. Please pay commission before adding new products.", "warning")
                return redirect(url_for("seller_commission_payment"))
            else:
                return redirect(url_for("seller_commission_payment"))
    
    if request.method == "POST":
        name = request.form.get("product-name")
        category = request.form.get("product-category")
        quantity = request.form.get("product-quantity", type=int)
        unit = request.form.get("product-unit")
        markup = request.form.get("product-markup", type=float)
        price = request.form.get("product-price", type=float)
        price_unit = request.form.get("product-price-unit")
        selling_price = request.form.get("product-selling-price", type=float)
        image_file = request.files.get("product-image")

        image_path = None
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Ensure upload folder exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image_file.save(image_path)
            image_path = '/' + image_path.replace('\\', '/').replace(os.path.sep, '/')

        new_product = Product(
            name=name,
            image=image_path,
            product_type=category,
            unit=unit,
            price_unit=price_unit,
            sold=0,
            available=quantity,
            rating=0,
            price=selling_price if selling_price else price,
            shop_id=shop_id
        )
        db.session.add(new_product)
        db.session.commit()
        flash("Product added successfully!", "success")
        return redirect(url_for("seller_products"))

    return render_template("seller/addProduct.html")

@app.route("/seller/editProduct/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    shop_id = session.get('shop_id')
    if not shop_id:
        flash("You must be logged in as a shop to edit products.", "danger")
        return redirect(url_for("login"))
    
    product = Product.query.get_or_404(product_id)
    
    # Verify product belongs to this shop
    if product.shop_id != shop_id:
        flash("You don't have permission to edit this product.", "danger")
        return redirect(url_for("seller_products"))
    
    if request.method == "POST":
        product.name = request.form.get("product-name")
        product.product_type = request.form.get("product-category")
        product.available = request.form.get("product-quantity", type=int)
        product.unit = request.form.get("product-unit")
        product.price_unit = request.form.get("product-price-unit")
        selling_price = request.form.get("product-selling-price", type=float)
        
        if selling_price:
            product.price = selling_price
        
        image_file = request.files.get("product-image")
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image_file.save(image_path)
            product.image = '/' + image_path.replace('\\', '/').replace(os.path.sep, '/')
        
        db.session.commit()
        flash("Product updated successfully!", "success")
        return redirect(url_for("seller_products"))
    
    return render_template("seller/editProduct.html", product=product)

@app.route("/notifications")
def notifications():
    # Redirect to appropriate notification page based on user type
    user_id = session.get('user_id')
    shop_id = session.get('shop_id')
    
    if user_id:
        return redirect(url_for('user_notifications'))
    elif shop_id:
        return redirect(url_for('seller_notifications'))
    else:
        flash('Please log in to view notifications.', 'warning')
        return redirect(url_for('login'))

@app.route("/cart")
def cart():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view your cart.', 'warning')
        return redirect(url_for('login'))

    # join cart items with products and shops
    items = db.session.query(Cart, Product, Shop).join(Product, Cart.product_id == Product.id).join(Shop, Product.shop_id == Shop.id).filter(Cart.user_id == user_id).all()

    # prepare a list of dicts for template
    cart_items = []
    total = 0.0
    for cart_item, product, shop in items:
        subtotal = (product.price or 0) * (cart_item.quantity or 0)
        total += subtotal
        # Check stock status
        is_out_of_stock = product.available is None or product.available <= 0
        exceeds_stock = not is_out_of_stock and cart_item.quantity > product.available
        cart_items.append({
            'cart_id': cart_item.id,
            'product_id': product.id,
            'name': product.name,
            'image': product.image,
            'price': product.price,
            'quantity': cart_item.quantity,
            'unit': (product.unit or product.price_unit) if (product.unit or product.price_unit) else 'kg',
            'shop_name': shop.shop_name,
            'subtotal': subtotal,
            'available': product.available,
            'is_out_of_stock': is_out_of_stock,
            'exceeds_stock': exceeds_stock
        })

    return render_template('cart.html', cart_items=cart_items, total=total)


@app.route('/place_order', methods=['GET', 'POST'])
def place_order():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to place an order.', 'warning')
        return redirect(url_for('login'))

    # fetch cart items
    items = db.session.query(Cart, Product, Shop).join(Product, Cart.product_id == Product.id).join(Shop, Product.shop_id == Shop.id).filter(Cart.user_id == user_id).all()
    if request.method == 'GET':
        if not items:
            flash('Your cart is empty.', 'warning')
            return redirect(url_for('cart'))

        cart_items = []
        total = 0.0
        user = User.query.get(user_id)
        for cart_item, product, shop in items:
            subtotal = (product.price or 0) * (cart_item.quantity or 0)
            total += subtotal
            cart_items.append({
                'cart_id': cart_item.id,
                'product_id': product.id,
                'name': product.name,
                'image': product.image,
                'price': product.price,
                'quantity': cart_item.quantity,
                'unit': (product.unit or product.price_unit) if (product.unit or product.price_unit) else 'kg',
                'shop_name': shop.shop_name,
                'subtotal': subtotal
            })
        # compute estimated shipping fee for display based on user's city and total KG
        try:
            user_city = (user.address_city or '').strip()
        except Exception:
            user_city = ''
        # total_kg assumed to be sum of quantities (system tracks kg units for products)
        total_kg = 0.0
        for it in cart_items:
            try:
                total_kg += float(it.get('quantity') or 0)
            except Exception:
                total_kg += 0.0

        def get_shipping_rate(municipality):
            if not municipality:
                return 1
            m = municipality.strip().lower()
            rates = {
                'mambusao': 1,
                'sapian': 2,
                'sigma': 3,
                'dao': 4,
                'cuartero': 5,
                'jamindan': 6,
                'ivisan': 7,
                'dumalag': 8,
                'dumarao': 9,
                'tapaz': 10
            }
            return rates.get(m, 1)

        est_rate = get_shipping_rate(user_city)
        est_shipping_fee = est_rate * total_kg

        return render_template('placeOrder.html', cart_items=cart_items, total=total, user=user, est_shipping_fee=est_shipping_fee, est_total_with_shipping=total + est_shipping_fee, total_kg=total_kg)
        

    # POST - create order
    shipping_option = request.form.get('shippingOption')
    payment_method = request.form.get('paymentMethod') or 'Cash on Delivery'
    # assemble address from user account as fallback
    user = User.query.get(user_id)
    address = request.form.get('address') or f"{user.address_house or ''} {user.address_street or ''} {user.address_city or ''}".strip()

    if not items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart'))

    # compute total again and validate stock
    total = 0.0
    out_of_stock_items = []
    for cart_item, product, shop in items:
        # Check if product is out of stock
        if product.available is None or product.available <= 0:
            out_of_stock_items.append(product.name)
        # Check if requested quantity exceeds available stock
        elif cart_item.quantity > product.available:
            out_of_stock_items.append(f"{product.name} (only {product.available} available, but {cart_item.quantity} in cart)")
        else:
            total += (product.price or 0) * cart_item.quantity
    
    # If any items are out of stock, show error and redirect to cart
    if out_of_stock_items:
        if len(out_of_stock_items) == 1:
            flash(f"Sorry, the following item is out of stock: {out_of_stock_items[0]}. Please update your cart.", 'danger')
        else:
            items_list = ", ".join(out_of_stock_items)
            flash(f"Sorry, the following items are out of stock: {items_list}. Please update your cart.", 'danger')
        return redirect(url_for('cart'))

    try:
        # compute shipping fee for POST (server-side authoritative)
        try:
            user_city = (user.address_city or '').strip()
        except Exception:
            user_city = ''
        # total_kg assumed to be sum of quantities
        total_kg = 0.0
        for cart_item, product, shop in items:
            try:
                total_kg += float(cart_item.quantity or 0)
            except Exception:
                total_kg += 0.0

        def get_shipping_rate(municipality):
            if not municipality:
                return 1
            m = municipality.strip().lower()
            rates = {
                'mambusao': 1,
                'sapian': 2,
                'sigma': 3,
                'dao': 4,
                'cuartero': 5,
                'jamindan': 6,
                'ivisan': 7,
                'dumalag': 8,
                'dumarao': 9,
                'tapaz': 10
            }
            return rates.get(m, 1)

        shipping_fee = 0.0
        if shipping_option and shipping_option.lower() == 'delivery':
            rate = get_shipping_rate(user_city)
            shipping_fee = rate * total_kg

        # set shop_id from first cart item's shop (assumes single-shop orders)
        shop_id = items[0][2].id if items and len(items) > 0 else None
        order = Order(user_id=user_id, total=total + shipping_fee, shipping_fee=shipping_fee, shipping_option=shipping_option, payment_method=payment_method, address=address, shop_id=shop_id)
        db.session.add(order)
        db.session.flush()  # get order.id

        for cart_item, product, shop in items:
            oi = OrderItem(order_id=order.id, product_id=product.id, quantity=cart_item.quantity, price=product.price or 0)
            db.session.add(oi)
            # deduct inventory and increase sold count
            if product.available is not None:
                product.available = (product.available or 0) - cart_item.quantity
            product.sold = (product.sold or 0) + cart_item.quantity

        # clear cart
        for cart_item, product, shop in items:
            db.session.delete(cart_item)

        db.session.commit()
        # notify seller that a new order needs confirmation
        try:
            note = Notification(
                user_id=None, 
                shop_id=shop_id, 
                message=f'New order #{order.id} has been placed by {user.first_name} {user.last_name}. Please confirm and set delivery date.'
            )
            db.session.add(note)
            db.session.commit()
        except Exception:
            db.session.rollback()

        flash('Order placed successfully!', 'success')
        return redirect(url_for('user_order_history'))
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to place order: {e}', 'danger')
        return redirect(url_for('cart'))


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to add items to cart.', 'warning')
        return redirect(url_for('login'))

    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int) or 1

    if not product_id:
        flash('Invalid product.', 'danger')
        return redirect(request.referrer or url_for('home'))

    product = Product.query.get(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(request.referrer or url_for('home'))

    # Check if product is out of stock
    if product.available is None or product.available <= 0:
        flash(f'Sorry, {product.name} is currently out of stock.', 'danger')
        return redirect(request.referrer or url_for('view_product', product_id=product_id))

    # If cart entry exists, check total quantity against available stock
    existing = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    new_total_quantity = (existing.quantity or 0) + quantity if existing else quantity
    
    # Validate stock availability
    if product.available is not None and new_total_quantity > product.available:
        available_to_add = product.available - (existing.quantity or 0) if existing else product.available
        if available_to_add <= 0:
            flash(f'Sorry, {product.name} is out of stock. Only {product.available} units available and you already have {existing.quantity or 0} in your cart.', 'danger')
        else:
            flash(f'Sorry, only {available_to_add} more units of {product.name} can be added to your cart. Available stock: {product.available}, Current cart quantity: {existing.quantity or 0}.', 'danger')
        return redirect(request.referrer or url_for('view_product', product_id=product_id))

    try:
        if existing:
            existing.quantity = new_total_quantity
        else:
            new_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
            db.session.add(new_item)
        db.session.commit()
        flash('Item added to cart.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to add to cart: {e}', 'danger')

    return redirect(request.referrer or url_for('cart'))


@app.route('/buy_now', methods=['POST'])
def buy_now():
    """Add the product to the user's cart (or update quantity) and redirect to checkout (place_order).
    This keeps the existing cart behavior but sends the user straight to the place order page.
    """
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to continue to checkout.', 'warning')
        return redirect(url_for('login'))

    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int) or 1

    if not product_id:
        flash('Invalid product.', 'danger')
        return redirect(request.referrer or url_for('home'))

    product = Product.query.get(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(request.referrer or url_for('home'))

    # Check if product is out of stock
    if product.available is None or product.available <= 0:
        flash(f'Sorry, {product.name} is currently out of stock. Cannot proceed with purchase.', 'danger')
        return redirect(request.referrer or url_for('view_product', product_id=product_id))

    # Validate available stock
    if product.available is not None and quantity > product.available:
        flash(f'Sorry, not enough stock for {product.name}. Only {product.available} units available, but you requested {quantity}.', 'danger')
        return redirect(request.referrer or url_for('view_product', product_id=product_id))

    existing = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    try:
        if existing:
            # set the cart entry to the requested quantity for immediate checkout
            existing.quantity = quantity
        else:
            new_item = Cart(user_id=user_id, product_id=product_id, quantity=quantity)
            db.session.add(new_item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to prepare item for checkout: {e}', 'danger')
        return redirect(request.referrer or url_for('view_product', product_id=product_id))

    # Redirect the user to the place_order page to complete checkout
    return redirect(url_for('place_order'))


@app.route('/cart/update', methods=['POST'])
def update_cart_item():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    cart_id = request.form.get('cart_id', type=int)
    quantity = request.form.get('quantity', type=int)
    item = Cart.query.get(cart_id)
    if not item or item.user_id != user_id:
        flash('Cart item not found.', 'danger')
        return redirect(url_for('cart'))

    if quantity <= 0:
        # remove
        try:
            db.session.delete(item)
            db.session.commit()
            flash('Item removed from cart.', 'info')
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to remove item: {e}', 'danger')
        return redirect(url_for('cart'))

    # Validate stock availability before updating
    product = Product.query.get(item.product_id)
    if product:
        # Check if product is out of stock
        if product.available is None or product.available <= 0:
            flash(f'Sorry, {product.name} is currently out of stock.', 'danger')
            return redirect(url_for('cart'))
        
        # Check if requested quantity exceeds available stock
        if product.available is not None and quantity > product.available:
            flash(f'Sorry, only {product.available} units of {product.name} are available. Your cart has been updated to the maximum available quantity.', 'warning')
            quantity = product.available

    try:
        item.quantity = quantity
        db.session.commit()
        flash('Cart updated.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to update cart: {e}', 'danger')
    return redirect(url_for('cart'))


@app.route('/cart/remove', methods=['POST'])
def remove_cart_item():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    cart_id = request.form.get('cart_id', type=int)
    item = Cart.query.get(cart_id)
    if not item or item.user_id != user_id:
        flash('Cart item not found.', 'danger')
        return redirect(url_for('cart'))

    try:
        db.session.delete(item)
        db.session.commit()
        flash('Item removed from cart.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to remove item: {e}', 'danger')
    return redirect(url_for('cart'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("fname")
        last_name = request.form.get("lname")
        email = request.form.get("email")
        address_house = request.form.get("address_house")
        address_street = request.form.get("address_street")
        address_city = request.form.get("address_city")
        phone = request.form.get("phone")
        password = request.form.get("password")
        re_password = request.form.get("re_password")
        password_hint_question = request.form.get("password_hint_question")
        password_hint_answer = request.form.get("password_hint_answer")

        if password != re_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("register.html")

        # Also prevent registering an email that already exists as a shop
        if Shop.query.filter_by(email=email).first():
            flash("Email already registered as a shop.", "danger")
            return render_template("register.html")

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            address_house=address_house,
            address_street=address_street,
            address_city=address_city,
            phone=phone,
            password=password,
            password_hint_question=password_hint_question,
            password_hint_answer=password_hint_answer
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/registerShop", methods=["GET", "POST"])
def register_shop():
    if request.method == "POST":
        shop_name = request.form.get("shop_name")
        description = request.form.get("description") 
        owner_name = request.form.get("owner_name")
        email = request.form.get("email")
        address_house = request.form.get("address_house")
        address_street = request.form.get("address_street")
        address_city = request.form.get("address_city")
        phone = request.form.get("phone")
        password = request.form.get("password")
        re_password = request.form.get("re_password")
        password_hint_question = request.form.get("password_hint_question")
        password_hint_answer = request.form.get("password_hint_answer")

        if password != re_password:
            flash("Passwords do not match.", "danger")
            return render_template("registerShop.html")

        if Shop.query.filter_by(email=email).first():
            flash("Email already registered for a shop.", "danger")
            return render_template("registerShop.html")

        # Also prevent registering a shop email that already exists as a user
        if User.query.filter_by(email=email).first():
            flash("Email already registered as a user.", "danger")
            return render_template("registerShop.html")

        new_shop = Shop(
            shop_name=shop_name,
            description=description, 
            owner_name=owner_name,
            email=email,
            address_house=address_house,
            address_street=address_street,
            address_city=address_city,
            phone=phone,
            password=password,
            password_hint_question=password_hint_question,
            password_hint_answer=password_hint_answer
        )
        db.session.add(new_shop)
        db.session.commit()
        flash("Shop registration successful! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("registerShop.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # Support admin login using fixed credentials
        # allow using 'admin' as username (email field) with password 'password'
        if (email == 'admin' or email == 'admin@gmail.com') and password == 'password':
            session['admin_logged_in'] = True
            session['user_type'] = 'admin'
            flash('Admin login successful.', 'success')
            return redirect(url_for('admin_dashboard'))
        # First check if the email exists in either users or shops
        user_by_email = User.query.filter_by(email=email).first()
        shop_by_email = Shop.query.filter_by(email=email).first()

        # If email doesn't exist anywhere
        if not user_by_email and not shop_by_email:
            flash("Email is not registered.", "danger")
            return render_template("login.html")

        # If email belongs to a user, attempt user login first
        if user_by_email:
            if user_by_email.password == password:
                session['user_id'] = user_by_email.id
                session['user_first_name'] = user_by_email.first_name
                session['user_last_name'] = user_by_email.last_name
                session['user_email'] = user_by_email.email
                session['user_profile_image'] = user_by_email.profile_image
                session['user_type'] = 'user'
                flash("Login successful! (User)", "success")
                return redirect(url_for("home"))
            else:
                flash("Incorrect password for user account.", "danger")
                return render_template("login.html")

        # Otherwise try shop login
        if shop_by_email:
            if shop_by_email.password == password:
                session['shop_id'] = shop_by_email.id
                session['shop_name'] = shop_by_email.shop_name
                session['shop_profile_image'] = shop_by_email.profile_image
                session['user_type'] = 'shop'
                flash("Login successful! (Shop)", "success")
                return redirect(url_for("home"))
            else:
                flash("Incorrect password for shop account.", "danger")
                return render_template("login.html")
    return render_template("login.html")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        # Start with step 1: email entry
        return render_template("forgot_password.html", step="email")
    
    if request.method == "POST":
        step = request.form.get("step")
        
        # Step 1: Verify email exists
        if step == "email":
            email = request.form.get("email")
            
            # Check if email exists in User or Shop table
            user = User.query.filter_by(email=email).first()
            shop = Shop.query.filter_by(email=email).first()
            
            if not user and not shop:
                flash("Email is not registered in our system.", "danger")
                return render_template("forgot_password.html", step="email")
            
            # Get the hint question
            account = user if user else shop
            
            if not account.password_hint_question or not account.password_hint_answer:
                flash("No security question set for this account. Please contact support.", "danger")
                return render_template("forgot_password.html", step="email")
            
            # Move to step 2: show hint question
            return render_template("forgot_password.html", 
                                 step="hint", 
                                 email=email, 
                                 hint_question=account.password_hint_question)
        
        # Step 2: Verify hint answer
        elif step == "hint":
            email = request.form.get("email")
            hint_answer = request.form.get("hint_answer")
            
            # Get account again
            user = User.query.filter_by(email=email).first()
            shop = Shop.query.filter_by(email=email).first()
            account = user if user else shop
            
            if not account:
                flash("Session expired. Please start over.", "danger")
                return render_template("forgot_password.html", step="email")
            
            # Check if answer matches (case-insensitive comparison)
            if account.password_hint_answer.lower().strip() != hint_answer.lower().strip():
                flash("Incorrect answer. Please try again.", "danger")
                return render_template("forgot_password.html", 
                                     step="hint", 
                                     email=email, 
                                     hint_question=account.password_hint_question)
            
            # Answer is correct, move to step 3: reset password
            return render_template("forgot_password.html", step="reset", email=email)
        
        # Step 3: Reset password
        elif step == "reset":
            email = request.form.get("email")
            new_password = request.form.get("new_password")
            confirm_password = request.form.get("confirm_password")
            
            if new_password != confirm_password:
                flash("Passwords do not match.", "danger")
                return render_template("forgot_password.html", step="reset", email=email)
            
            # Update password
            user = User.query.filter_by(email=email).first()
            shop = Shop.query.filter_by(email=email).first()
            account = user if user else shop
            
            if not account:
                flash("Session expired. Please start over.", "danger")
                return render_template("forgot_password.html", step="email")
            
            try:
                account.password = new_password
                db.session.commit()
                flash("Password reset successful! You can now login with your new password.", "success")
                return redirect(url_for("login"))
            except Exception as e:
                db.session.rollback()
                flash(f"Failed to reset password: {e}", "danger")
                return render_template("forgot_password.html", step="reset", email=email)
    
    return render_template("forgot_password.html", step="email")

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('shop_id', None)
    session.pop('user_type', None)
    # clear admin flag as well
    session.pop('admin_logged_in', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/admin/dashboard')
def admin_dashboard():
    # simple admin protection
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to access the admin dashboard.', 'warning')
        return redirect(url_for('login'))
    # query all products with their shop names for admin view
    products = db.session.query(Product, Shop).join(Shop, Product.shop_id == Shop.id).all()
    # compute totals
    total_users = db.session.query(User).count()
    total_shops = db.session.query(Shop).count()
    total_products = db.session.query(Product).count()
    # Render the existing admin dashboard template with products and totals
    return render_template('admin/dashboard.html', products=products, total_users=total_users, total_shops=total_shops, total_products=total_products)

@app.route("/admin/view/shops")
def admin_view_shops():
    # admin protection
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('login'))

    shops = Shop.query.all()
    total_users = db.session.query(User).count()
    total_shops = db.session.query(Shop).count()
    total_products = db.session.query(Product).count()
    return render_template("admin/view_shops.html", shops=shops, total_users=total_users, total_shops=total_shops, total_products=total_products)


@app.route("/admin/view/users")
def admin_view_users():
    # admin protection
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('login'))

    users = User.query.all()
    total_users = db.session.query(User).count()
    total_shops = db.session.query(Shop).count()
    total_products = db.session.query(Product).count()
    return render_template("admin/view_users.html", users=users, total_users=total_users, total_shops=total_shops, total_products=total_products)


@app.route('/admin/product/approve/<int:product_id>', methods=['POST'])
def admin_approve_product(product_id):
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('login'))

    product = Product.query.get_or_404(product_id)
    try:
        product.approved = True
        db.session.commit()
        
        # Notify the seller that their product has been approved
        note = Notification(
            user_id=None, 
            shop_id=product.shop_id, 
            message=f'Your product "{product.name}" has been approved and is now visible to customers.'
        )
        db.session.add(note)
        db.session.commit()
        
        flash('Product approved and seller notified.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to approve product: {e}', 'danger')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/product/disapprove/<int:product_id>', methods=['POST'])
def admin_disapprove_product(product_id):
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('login'))

    product = Product.query.get_or_404(product_id)
    try:
        product.approved = False
        db.session.commit()
        flash('Product disapproved.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to disapprove product: {e}', 'danger')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/tips')
def admin_tips():
    # admin protection
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('login'))

    tips = Tip.query.order_by(Tip.created_at.desc()).all()
    return render_template('admin/tips.html', tips=tips)


@app.route('/admin/tips/create', methods=['POST'])
def admin_create_tip():
    # admin protection
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('login'))

    title = request.form.get('title')
    body = request.form.get('body')
    if not title and not body:
        flash('Please provide a title or description for the tip.', 'warning')
        return redirect(url_for('admin_tips'))

    try:
        tip = Tip(title=title, body=body)
        db.session.add(tip)
        db.session.commit()
        flash('Tip created successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to create tip: {e}', 'danger')

    return redirect(url_for('admin_tips'))


@app.route('/admin/tips/edit/<int:tip_id>', methods=['POST'])
def admin_edit_tip(tip_id):
    # admin protection
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('login'))

    tip = Tip.query.get_or_404(tip_id)
    title = request.form.get('title')
    body = request.form.get('body')
    try:
        tip.title = title or tip.title
        tip.body = body or tip.body
        db.session.commit()
        flash('Tip updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to update tip: {e}', 'danger')

    return redirect(url_for('admin_tips'))


@app.route('/admin/sales')
def admin_view_sales():
    # admin protection
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('login'))

    # Get all orders with their items, products, and shops
    orders = Order.query.order_by(Order.timestamp.desc()).all()
    
    # Calculate total sales statistics
    total_sales = 0.0
    total_fees = 0.0
    total_orders = 0
    
    sales_by_shop = {}
    sales_data = []
    
    for order in orders:
        order_items = db.session.query(OrderItem, Product, Shop)\
            .join(Product, OrderItem.product_id == Product.id)\
            .join(Shop, Product.shop_id == Shop.id)\
            .filter(OrderItem.order_id == order.id).all()
        
        order_total = 0.0
        order_shop = None
        
        for order_item, product, shop in order_items:
            item_subtotal = (order_item.price or 0) * (order_item.quantity or 0)
            order_total += item_subtotal
            order_shop = shop
            
            # Track sales by shop
            if shop.id not in sales_by_shop:
                sales_by_shop[shop.id] = {
                    'shop_name': shop.shop_name,
                    'total_sales': 0.0,
                    'order_count': 0
                }
        
        shipping_fee = order.shipping_fee or 0.0
        order_grand_total = order_total + shipping_fee
        
        total_sales += order_total
        total_fees += shipping_fee
        total_orders += 1
        
        # Update shop statistics
        if order_shop and order_shop.id in sales_by_shop:
            sales_by_shop[order_shop.id]['total_sales'] += order_total
            sales_by_shop[order_shop.id]['order_count'] += 1
        
        # Get buyer info
        buyer = User.query.get(order.user_id) if order.user_id else None
        buyer_name = f"{buyer.first_name} {buyer.last_name}" if buyer else "Unknown"
        
        sales_data.append({
            'order_id': order.id,
            'timestamp': order.timestamp,
            'buyer_name': buyer_name,
            'shop_name': order_shop.shop_name if order_shop else "Unknown",
            'product_total': order_total,
            'shipping_fee': shipping_fee,
            'grand_total': order_grand_total,
            'status': order.status,
            'payment_method': order.payment_method
        })
    
    # Convert sales_by_shop dict to list for easier template rendering
    shop_sales_list = list(sales_by_shop.values())
    shop_sales_list.sort(key=lambda x: x['total_sales'], reverse=True)
    
    # Calculate totals for statistics
    total_users = db.session.query(User).count()
    total_shops = db.session.query(Shop).count()
    total_products = db.session.query(Product).count()
    
    return render_template('admin/view_sales.html',
                         sales_data=sales_data,
                         total_sales=total_sales,
                         total_fees=total_fees,
                         total_orders=total_orders,
                         shop_sales_list=shop_sales_list,
                         total_users=total_users,
                         total_shops=total_shops,
                         total_products=total_products)


@app.route('/admin/payment-settings', methods=['GET'])
def admin_payment_settings():
    """Admin page to view and manage commission settings"""
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('login'))
    
    # Get current commission settings (or create default if none exist)
    settings = CommissionSettings.query.first()
    if not settings:
        settings = CommissionSettings(
            commission_rate=5.0,
            commission_type='percentage',
            threshold_amount=1000.0
        )
        db.session.add(settings)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            settings = CommissionSettings.query.first()
    
    # Calculate statistics
    total_users = db.session.query(User).count()
    total_shops = db.session.query(Shop).count()
    total_products = db.session.query(Product).count()
    
    # Get shops that have reached commission threshold
    shops_with_commission = Shop.query.filter(Shop.total_income >= settings.threshold_amount).all()
    
    return render_template('admin/payment_settings.html',
                         settings=settings,
                         total_users=total_users,
                         total_shops=total_shops,
                         total_products=total_products,
                         shops_with_commission=shops_with_commission)


@app.route('/admin/payment-settings/update', methods=['POST'])
def admin_update_payment_settings():
    """Update commission settings including QR code upload"""
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('login'))
    
    try:
        commission_rate = float(request.form.get('commission_rate', 5.0))
        commission_type = request.form.get('commission_type', 'percentage')
        threshold_amount = float(request.form.get('threshold_amount', 1000.0))
        
        # Validate inputs
        if commission_rate < 0 or commission_rate > 100:
            flash('Commission rate must be between 0 and 100.', 'warning')
            return redirect(url_for('admin_payment_settings'))
        
        if threshold_amount < 0:
            flash('Threshold amount must be positive.', 'warning')
            return redirect(url_for('admin_payment_settings'))
        
        # Get or create settings
        settings = CommissionSettings.query.first()
        if not settings:
            settings = CommissionSettings()
            db.session.add(settings)
        
        settings.commission_rate = commission_rate
        settings.commission_type = commission_type
        settings.threshold_amount = threshold_amount
        
        # Handle QR code upload
        qr_code_file = request.files.get('qr_code_image')
        if qr_code_file and allowed_file(qr_code_file.filename):
            # Delete old QR code if exists
            if settings.qr_code_image:
                old_path = settings.qr_code_image.lstrip('/')
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception:
                        pass
            
            # Save new QR code
            filename = secure_filename(f"commission_qr_{datetime.now().strftime('%Y%m%d%H%M%S')}.{qr_code_file.filename.rsplit('.', 1)[1].lower()}")
            qr_folder = os.path.join('static', 'images', 'gcash-qr')
            os.makedirs(qr_folder, exist_ok=True)
            qr_path = os.path.join(qr_folder, filename)
            qr_code_file.save(qr_path)
            settings.qr_code_image = '/' + qr_path.replace('\\', '/').replace(os.path.sep, '/')
        
        settings.updated_at = datetime.now()
        db.session.commit()
        flash('Payment settings updated successfully!', 'success')
    except ValueError:
        flash('Invalid input. Please enter valid numbers.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to update settings: {e}', 'danger')
    
    return redirect(url_for('admin_payment_settings'))

@app.route('/admin/commission-payments')
def admin_commission_payments():
    """Admin page to review commission payment submissions"""
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('login'))
    
    # Get all commission payment submissions
    payments = db.session.query(CommissionPayment, Shop).join(
        Shop, CommissionPayment.shop_id == Shop.id
    ).order_by(CommissionPayment.submitted_at.desc()).all()
    
    payment_list = []
    for payment, shop in payments:
        payment_list.append({
            'id': payment.id,
            'shop_id': shop.id,
            'shop_name': shop.shop_name,
            'shop_email': shop.email,
            'amount_owed': payment.amount_owed,
            'payment_proof': payment.payment_proof,
            'status': payment.status,
            'submitted_at': payment.submitted_at,
            'reviewed_at': payment.reviewed_at,
            'admin_notes': payment.admin_notes
        })
    
    # Calculate statistics
    total_users = db.session.query(User).count()
    total_shops = db.session.query(Shop).count()
    total_products = db.session.query(Product).count()
    pending_payments = len([p for p in payment_list if p['status'] == 'pending'])
    
    return render_template('admin/commission_payments.html',
                         payments=payment_list,
                         total_users=total_users,
                         total_shops=total_shops,
                         total_products=total_products,
                         pending_payments=pending_payments)

@app.route('/admin/commission-payment/<int:payment_id>/approve', methods=['POST'])
def admin_approve_commission_payment(payment_id):
    """Approve a commission payment submission"""
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('login'))
    
    try:
        payment = CommissionPayment.query.get_or_404(payment_id)
        shop = Shop.query.get(payment.shop_id)
        
        # Update payment status
        payment.status = 'approved'
        payment.reviewed_at = datetime.now()
        payment.admin_notes = request.form.get('admin_notes', '')
        
        # Reset shop commission status - allow adding products again
        shop.commission_payment_status = 'clear'
        shop.commission_amount_owed = 0.0
        
        db.session.commit()
        
        # Notify shop
        notification = Notification(
            user_id=None,
            shop_id=shop.id,
            message=f'Your commission payment of \u20b1{payment.amount_owed:.2f} has been approved. You can now add products.'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash(f'Payment approved for {shop.shop_name}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to approve payment: {e}', 'danger')
    
    return redirect(url_for('admin_commission_payments'))

@app.route('/admin/commission-payment/<int:payment_id>/reject', methods=['POST'])
def admin_reject_commission_payment(payment_id):
    """Reject a commission payment submission"""
    if not session.get('admin_logged_in') or session.get('user_type') != 'admin':
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('login'))
    
    try:
        payment = CommissionPayment.query.get_or_404(payment_id)
        shop = Shop.query.get(payment.shop_id)
        
        # Update payment status
        payment.status = 'rejected'
        payment.reviewed_at = datetime.now()
        payment.admin_notes = request.form.get('admin_notes', '')
        
        # Set shop to blocked - they need to resubmit
        shop.commission_payment_status = 'blocked'
        
        db.session.commit()
        
        # Notify shop
        notification = Notification(
            user_id=None,
            shop_id=shop.id,
            message=f'Your commission payment submission was rejected. Please resubmit valid payment proof. Reason: {payment.admin_notes}'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash(f'Payment rejected for {shop.shop_name}.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to reject payment: {e}', 'danger')
    
    return redirect(url_for('admin_commission_payments'))

def initialize_database_properly():
    """Initialize database with proper schema including all required columns"""
    import subprocess
    import sys
    
    # Run the initialization script
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'init_database.py')
    try:
        subprocess.run([sys.executable, script_path], check=True)
        print("Database initialized successfully")
    except subprocess.CalledProcessError as e:
        print(f"Database initialization failed: {e}")
        # Fallback to basic create_all
        with app.app_context():
            db.create_all()

    # ensure shipping_fee column exists in orders table (only for SQLite)
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        try:
            import sqlite3
            db_path = os.path.join(os.path.dirname(__file__), 'instance', 'farmhub.db')
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cols = [r[1] for r in cur.execute("PRAGMA table_info('order')").fetchall()]
                if 'shipping_fee' not in cols:
                    try:
                        cur.execute("ALTER TABLE 'order' ADD COLUMN shipping_fee FLOAT DEFAULT 0.0")
                        conn.commit()
                        print('Added shipping_fee column to order table')
                    except Exception:
                        # best-effort, ignore failures
                        pass
                conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    app.run(debug=True)