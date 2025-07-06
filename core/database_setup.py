import sqlite3
from datetime import datetime

DB_NAME = "product_management.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def create_tables(db_conn=None):
    """
    Creates all necessary tables in the database if they don't already exist.
    Accepts an optional database connection. If provided, uses it; otherwise, creates a new one.
    The provided connection is NOT closed by this function. Connections created internally are closed.
    """
    conn_was_provided = db_conn is not None
    conn = db_conn if conn_was_provided else get_db_connection()

    try:
        cursor = conn.cursor()

        # Products Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category_id INTEGER,
            unit_of_measure TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES product_categories(id)
        )
        """)

        # Product Categories Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            description TEXT,
            FOREIGN KEY (parent_id) REFERENCES product_categories(id)
        )
        """)

        # Product Prices Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            valid_from DATE NOT NULL,
            valid_to DATE,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        """)

        # Product Inventory Table
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

        # Product Vendors Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            vendor_sku TEXT,
            lead_time INTEGER,
            last_price DECIMAL(10, 2),
            FOREIGN KEY (product_id) REFERENCES products(id),
            UNIQUE (product_id, vendor_id)
        )
        """)

        # Triggers to update `updated_at` timestamp on products table
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_products_updated_at
        AFTER UPDATE ON products
        FOR EACH ROW
        BEGIN
            UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        """)

        conn.commit() # Commit changes
        print("Database tables created successfully (if they didn't exist).")

    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
        # If an external connection was provided, do not rollback here; let the caller manage.
        # If an internal connection, a rollback might be considered, but typically
        # CREATE TABLE IF NOT EXISTS failures are due to syntax or DB lock, not data issues needing rollback.
        raise # Re-raise to ensure test setup failure is clear
    finally:
        if not conn_was_provided and conn:
            conn.close()

def initialize_database(db_conn=None):
    """
    Initializes the database by creating the tables.
    Accepts an optional database connection to pass to create_tables.
    """
    print(f"Initializing database '{DB_NAME if not db_conn else "provided connection"}'...")
    create_tables(db_conn=db_conn)

if __name__ == "__main__":
    initialize_database()
    # Example of how to connect and potentially add some initial data or test
    # conn = get_db_connection()
    # # Example: Add a root category if it doesn't exist
    # try:
    #     conn.execute("INSERT INTO product_categories (name, description) VALUES (?, ?)",
    #                  ('All Products', 'Root category for all products'))
    #     conn.commit()
    #     print("Added 'All Products' root category.")
    # except sqlite3.IntegrityError:
    #     print("'All Products' category likely already exists.")
    # conn.close()
