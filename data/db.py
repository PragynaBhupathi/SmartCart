"""
SmartCart — Database Layer (SQLite)
Handles all product CRUD operations.
"""

import sqlite3
import os
from config import DB_PATH

# Ensure data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and seed sample products if empty."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                barcode   TEXT PRIMARY KEY,
                name      TEXT NOT NULL,
                category  TEXT NOT NULL DEFAULT 'General',
                price     REAL NOT NULL,
                unit      TEXT NOT NULL DEFAULT 'piece',
                stock     INTEGER DEFAULT -1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total      REAL DEFAULT 0,
                items      INTEGER DEFAULT 0
            )
        """)
        conn.commit()

    # Seed if empty
    if count_products() == 0:
        _seed_products()


def _seed_products():
    samples = [
        # barcode,              name,                     category,        price,   unit
        ("8901234567890", "Amul Milk 1L",              "Dairy",          62.00,  "litre"),
        ("8901234567891", "Amul Butter 100g",           "Dairy",          55.00,  "pack"),
        ("8901234100252", "Amul Paneer 200g",           "Dairy",          85.00,  "pack"),
        ("8902100010013", "Britannia Bread",            "Bakery",         45.00,  "loaf"),
        ("8902100010020", "Britannia Good Day",         "Bakery",         30.00,  "pack"),
        ("8902100050018", "Britannia NutriChoice",      "Bakery",         55.00,  "pack"),
        ("8888820008001", "Maggi Noodles 70g",          "Instant Food",   14.00,  "pack"),
        ("8888820008002", "Yippee Noodles 70g",         "Instant Food",   12.00,  "pack"),
        ("8901764101283", "Tata Salt 1kg",              "Staples",        22.00,  "kg"),
        ("8901725123456", "Sunflower Oil 1L",           "Staples",       160.00,  "litre"),
        ("8908001301234", "Aashirvaad Atta 5kg",        "Staples",       265.00,  "kg"),
        ("8901725001234", "Fortune Rice 5kg",           "Staples",       320.00,  "kg"),
        ("8901243116017", "Tata Dal 500g",              "Staples",        65.00,  "pack"),
        ("7622210100054", "Cadbury Dairy Milk 40g",     "Chocolate",      40.00,  "piece"),
        ("5000159407236", "KitKat 4 Finger",            "Chocolate",      30.00,  "piece"),
        ("8901491109016", "Munch",                      "Chocolate",      10.00,  "piece"),
        ("8906002510013", "Parle-G Biscuits",           "Snacks",         10.00,  "pack"),
        ("8902080000004", "Lays Classic 26g",           "Snacks",         20.00,  "pack"),
        ("8901063007013", "Haldiram Bhujia 150g",       "Snacks",         60.00,  "pack"),
        ("8901019002003", "Nescafe Classic 50g",        "Beverages",     140.00,  "jar"),
        ("4890201001387", "Coca-Cola 750ml",            "Beverages",      45.00,  "bottle"),
        ("8901030064018", "Horlicks 500g",              "Beverages",     220.00,  "jar"),
        ("8906001123456", "Real Fruit Juice 1L",        "Beverages",      99.00,  "litre"),
        ("8906063700061", "Red Bull 250ml",             "Beverages",     115.00,  "can"),
        ("8901030868023", "Colgate Toothpaste 200g",    "Personal Care",  89.00,  "tube"),
        ("8901063123456", "Dettol Soap 75g",            "Personal Care",  35.00,  "piece"),
        ("8901030560049", "Dove Shampoo 180ml",         "Personal Care", 175.00,  "bottle"),
        ("8901396918041", "Dettol Sanitizer 50ml",      "Personal Care",  65.00,  "bottle"),
        ("8901764011017", "Surf Excel 500g",            "Household",      95.00,  "pack"),
        ("8901764011024", "Vim Dishwash 500ml",         "Household",      55.00,  "bottle"),
    ]
    with get_conn() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO products (barcode, name, category, price, unit) VALUES (?,?,?,?,?)",
            samples
        )
        conn.commit()


# ── CRUD ─────────────────────────────────────────────────────────────────────
def get_product(barcode):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE barcode = ?", (barcode,)
        ).fetchone()
    return dict(row) if row else None


def get_all_products():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM products ORDER BY category, name"
        ).fetchall()
    return [dict(r) for r in rows]


def get_categories():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM products ORDER BY category"
        ).fetchall()
    return [r["category"] for r in rows]


def add_product(barcode, name, category, price, unit="piece"):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO products (barcode, name, category, price, unit) VALUES (?,?,?,?,?)",
            (barcode, name, category, price, unit)
        )
        conn.commit()


def update_product(barcode, name, category, price, unit):
    with get_conn() as conn:
        conn.execute(
            "UPDATE products SET name=?, category=?, price=?, unit=? WHERE barcode=?",
            (name, category, price, unit, barcode)
        )
        conn.commit()


def delete_product(barcode):
    with get_conn() as conn:
        conn.execute("DELETE FROM products WHERE barcode = ?", (barcode,))
        conn.commit()


def count_products():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]


def search_products(query):
    q = f"%{query}%"
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM products WHERE name LIKE ? OR barcode LIKE ? OR category LIKE ? ORDER BY name",
            (q, q, q)
        ).fetchall()
    return [dict(r) for r in rows]
