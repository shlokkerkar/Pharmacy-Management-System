import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# Connect to SQLite database and create tables if they don't exist
conn = sqlite3.connect('pharmacy.db')
c = conn.cursor()

# Create medicines table
c.execute('''CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                buy_price REAL NOT NULL,
                sell_price REAL NOT NULL,
                stock INTEGER NOT NULL,
                expiry_date TEXT NOT NULL
            )''')

# Create customers table
c.execute('''CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT NOT NULL,
                address TEXT NOT NULL
            )''')

# Create sales table with prescription column
c.execute('''CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                medicine_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                total REAL NOT NULL,
                date TEXT NOT NULL,
                prescription TEXT,
                FOREIGN KEY(customer_id) REFERENCES customers(id),
                FOREIGN KEY(medicine_id) REFERENCES medicines(id)
            )''')

# If the sales table existed without prescription column, add it
try:
    c.execute("ALTER TABLE sales ADD COLUMN prescription TEXT")
except sqlite3.OperationalError:
    # Column already exists
    pass

conn.commit()
conn.close()

# Helper function to create a new connection
def connect_db():
    return sqlite3.connect('pharmacy.db')


def fetch_medicines():
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM medicines")
    data = c.fetchall()
    conn.close()
    return data


def fetch_customers():
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM customers")
    data = c.fetchall()
    conn.close()
    return data


def fetch_sales():
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        SELECT c.name AS customer_name,
               m.name AS medicine_name,
               s.quantity,
               s.total,
               s.date,
               s.prescription
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        JOIN medicines m ON s.medicine_id = m.id
    """)
    data = c.fetchall()
    conn.close()
    return data


def calculate_total_sales():
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT SUM(total) FROM sales")
    total = c.fetchone()[0] or 0
    conn.close()
    return total


def calculate_total_profit():
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        SELECT SUM(s.quantity * (m.sell_price - m.buy_price))
        FROM sales s
        JOIN medicines m ON s.medicine_id = m.id
    """)
    profit = c.fetchone()[0] or 0
    conn.close()
    return profit


def medicines_expiring_this_week():
    conn = connect_db()
    c = conn.cursor()
    today = datetime.now()
    end_of_week = (today + timedelta(days=7)).strftime('%Y-%m-%d')
    c.execute(
        "SELECT COUNT(*) FROM medicines WHERE expiry_date <= ? AND expiry_date >= ?",
        (end_of_week, today.strftime('%Y-%m-%d'))
    )
    count = c.fetchone()[0] or 0
    conn.close()
    return count


def add_medicine(name, category, buy_price, sell_price, stock, expiry_date):
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO medicines (name, category, buy_price, sell_price, stock, expiry_date) VALUES (?, ?, ?, ?, ?, ?)",
        (name, category, buy_price, sell_price, stock, expiry_date)
    )
    conn.commit()
    conn.close()


def add_customer(name, contact, address):
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO customers (name, contact, address) VALUES (?, ?, ?)",
        (name, contact, address)
    )
    conn.commit()
    conn.close()


def record_sale(customer_id, medicine_id, quantity, prescription_path=None):
    conn = connect_db()
    c = conn.cursor()

    # Check medicine stock and price
    c.execute("SELECT sell_price, stock FROM medicines WHERE id = ?", (medicine_id,))
    medicine = c.fetchone()

    if not medicine:
        conn.close()
        return "Medicine not found."

    price, stock = medicine
    if stock < quantity:
        conn.close()
        return "Not enough stock available."

    total = price * quantity
    new_stock = stock - quantity

    # Update stock and record the sale with prescription path
    c.execute("UPDATE medicines SET stock = ? WHERE id = ?", (new_stock, medicine_id))
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute(
        "INSERT INTO sales (customer_id, medicine_id, quantity, total, date, prescription) VALUES (?, ?, ?, ?, ?, ?)",
        (customer_id, medicine_id, quantity, total, date, prescription_path)
    )

    conn.commit()
    conn.close()
    return "Sale recorded successfully!"


def generate_report(start_date, end_date):
    conn = connect_db()
    query = """
    SELECT s.date,
           c.name as Customer,
           m.name as Medicine,
           s.quantity,
           s.total,
           s.prescription
    FROM sales s
    JOIN customers c ON s.customer_id = c.id
    JOIN medicines m ON s.medicine_id = m.id
    WHERE s.date BETWEEN ? AND ?
    """
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    conn.close()
    return df


def delete_medicine(medicine_id):
    conn = connect_db()
    c = conn.cursor()
    c.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))
    conn.commit()
    conn.close()


def delete_customer(customer_id):
    conn = connect_db()
    c = conn.cursor()
    c.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()


def update_medicine(medicine_id, name, category, buy_price, sell_price, stock, expiry_date):
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        "UPDATE medicines SET name = ?, category = ?, buy_price = ?, sell_price = ?, expiry_date = ?, stock = ? WHERE id = ?",
        (name, category, buy_price, sell_price, expiry_date, stock, medicine_id)
    )
    conn.commit()
    conn.close()


def update_customer(customer_id, name, contact, address):
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        "UPDATE customers SET name = ?, contact = ?, address = ? WHERE id = ?",
        (name, contact, address, customer_id)
    )
    
    conn.commit()
    conn.close()
