import sqlite3

try:
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    # Bảng user
    cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    name TEXT,
    is_admin INTEGER DEFAULT 0
)

    ''')

    # Bảng đơn hàng
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            address TEXT,
            total INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Bảng sản phẩm trong đơn
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price INTEGER,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    ''')
    # Bảng sản phẩm
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price INTEGER,
            image TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Khởi tạo CSDL thành công.")

except Exception as e:
    print("❌ Lỗi khi tạo CSDL:", e)
