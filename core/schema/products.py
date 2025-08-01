import sqlite3

def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create product related tables and triggers."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_units_of_measure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            description TEXT,
            FOREIGN KEY (parent_id) REFERENCES product_categories(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category_id INTEGER,
            unit_of_measure_id INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES product_categories(id),
            FOREIGN KEY (unit_of_measure_id) REFERENCES product_units_of_measure(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price_type TEXT NOT NULL DEFAULT 'SALE',
            price DECIMAL(10, 2) NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            valid_from DATE NOT NULL,
            valid_to DATE,
            FOREIGN KEY (product_id) REFERENCES products(id),
            UNIQUE (product_id, price_type, valid_from, currency)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            location_id INTEGER NOT NULL,
            quantity DECIMAL(10, 2) NOT NULL DEFAULT 0,
            min_stock DECIMAL(10, 2) DEFAULT 0,
            max_stock DECIMAL(10, 2) DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_product_location ON product_inventory (product_id, location_id);
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            vendor_sku TEXT,
            lead_time INTEGER,
            last_price DECIMAL(10, 2),
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (vendor_id) REFERENCES accounts(id),
            UNIQUE (product_id, vendor_id)
        )
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_products_updated_at
        AFTER UPDATE ON products
        FOR EACH ROW
        BEGIN
            UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
    """)
