import sqlite3

conn = sqlite3.connect('shop.db')
cursor = conn.cursor()

products = [
    ('Áo thun', 150000, 'https://via.placeholder.com/150'),
    ('Quần jean', 250000, 'https://via.placeholder.com/150'),
    ('Giày sneaker', 500000, 'https://via.placeholder.com/150')
]

cursor.executemany('''
    INSERT INTO products (name, price, image)
    VALUES (?, ?, ?)
''', products)

conn.commit()
conn.close()
print("✅ Đã thêm sản phẩm mẫu.")
