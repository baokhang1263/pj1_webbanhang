from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('shop.db')
    conn.row_factory = sqlite3.Row
    return conn

app.secret_key = 'secret-key-rat-mat'  # Thay bằng chuỗi khó đoán

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id_, name, email):
        self.id = id_
        self.name = name
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['name'], user['email'])
    return None


# Danh sách sản phẩm

orders = []  # Danh sách đơn hàng toàn hệ thống (RAM)

@app.route('/')
def home():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('index.html', products=products)


@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    cart = session.get('cart', {})
    product_id = str(product_id)
    cart[product_id] = cart.get(product_id, 0) + 1
    session['cart'] = cart
    return redirect(url_for('home'))


@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    for pid, qty in cart.items():
        for p in products:
            if str(p['id']) == pid:
                item = p.copy()
                item['qty'] = qty
                item['subtotal'] = item['price'] * qty
                total += item['subtotal']
                cart_items.append(item)
    return render_template('cart.html', cart_items=cart_items, total=total)
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
    session['cart'] = cart
    return redirect(url_for('view_cart'))
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('home'))

    cart_items = []
    total = 0
    conn = get_db_connection()
    for pid, qty in cart.items():
        product = conn.execute('SELECT * FROM products WHERE id = ?', (pid,)).fetchone()
        if product:
            item = {
                'name': product['name'],
                'price': product['price'],
                'qty': qty,
                'subtotal': product['price'] * qty
            }
            total += item['subtotal']
            cart_items.append(item)

    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        phone = request.form.get('phone')

        # 🔗 Lưu đơn hàng vào DB
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Lưu vào bảng orders
        cursor.execute('''
            INSERT INTO orders (user_id, name, phone, address, total)
            VALUES (?, ?, ?, ?, ?)
        ''', (current_user.id, name, phone, address, total))

        order_id = cursor.lastrowid  # ID của đơn hàng vừa tạo

        # 2. Lưu vào bảng order_items
        for item in cart_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_name, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['name'], item['qty'], item['price']))

        conn.commit()
        conn.close()

        session['cart'] = {}  # Xoá giỏ hàng sau khi đặt
        return render_template('success.html', name=name)

    return render_template('checkout.html', cart_items=cart_items, total=total)


# --- Các route chính ở trên (home, add_to_cart, cart, checkout) ---

# ✅ Route đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        existing = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            conn.close()
            return 'Email đã được đăng ký!'

        conn.execute('INSERT INTO users (email, password, name) VALUES (?, ?, ?)',
                     (email, password, name))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

# ✅ Route đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
        conn.close()

        if user:
            user_obj = User(user['id'], user['name'], user['email'])
            login_user(user_obj)
            return redirect(url_for('home'))
        else:
            return 'Sai tài khoản hoặc mật khẩu!'
    return render_template('login.html')


# ✅ Route đăng xuất
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/my-orders')
@login_required
def my_orders():
    conn = get_db_connection()

    # 1. Lấy tất cả đơn hàng của người dùng
    orders = conn.execute(
        'SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC',
        (current_user.id,)
    ).fetchall()

    all_orders = []

    for order in orders:
        # 2. Lấy sản phẩm theo từng đơn hàng
        items = conn.execute(
            'SELECT * FROM order_items WHERE order_id = ?',
            (order['id'],)
        ).fetchall()

        all_orders.append({
            'id': order['id'],
            'name': order['name'],
            'phone': order['phone'],
            'address': order['address'],
            'total': order['total'],
            'items': items
        })

    conn.close()
    return render_template('my_orders.html', orders=all_orders)
@app.route('/admin/products', methods=['GET', 'POST'])
@login_required
def admin_products():
    conn = get_db_connection()

    # Kiểm tra người dùng có phải admin không
    user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user.id,)).fetchone()
    if not user['is_admin']:
        conn.close()
        return "403 – Bạn không có quyền truy cập", 403

    # Nếu POST: thêm sản phẩm mới
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        image = request.form.get('image')
        conn.execute('INSERT INTO products (name, price, image) VALUES (?, ?, ?)',
                     (name, price, image))
        conn.commit()

    # Lấy danh sách sản phẩm
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    print("⚙️ Vào được route /admin/products")
    return render_template('admin_products.html', products=products)
@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    conn = get_db_connection()

    user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user.id,)).fetchone()
    if not user['is_admin']:
        conn.close()
        return "403 – Không đủ quyền", 403

    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_products'))

@app.route('/test123')
def test123():
    return "Đã vào đúng file app.py!"
# ✅ Cuối cùng: khởi chạy app
import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

