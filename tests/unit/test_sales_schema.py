import sqlite3
from core.schema import sales

def test_create_schema_adds_shipped_columns():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create tables using older schema lacking shipped columns
    cursor.execute(
        """
        CREATE TABLE sales_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            created_date TEXT NOT NULL,
            expiry_date TEXT,
            due_date TEXT,
            status TEXT NOT NULL,
            reference_number TEXT,
            notes TEXT,
            subtotal REAL DEFAULT 0.0,
            taxes REAL DEFAULT 0.0,
            total_amount REAL DEFAULT 0.0,
            related_quote_id INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE sales_document_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sales_document_id INTEGER NOT NULL,
            product_id INTEGER,
            product_description TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            discount_percentage REAL DEFAULT 0.0,
            line_total REAL NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sales_document_id) REFERENCES sales_documents(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        """
    )
    conn.commit()

    # Run schema creation which should add missing columns
    sales.create_schema(cursor)

    cursor.execute("PRAGMA table_info(sales_document_items)")
    cols = {row[1] for row in cursor.fetchall()}
    assert "shipped_quantity" in cols
    assert "is_shipped" in cols

    conn.close()
