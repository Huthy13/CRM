import sqlite3

def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create sales document tables and triggers."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            created_date TEXT NOT NULL,
            expiry_date TEXT,
            due_date TEXT,
            status TEXT NOT NULL,
            notes TEXT,
            subtotal REAL DEFAULT 0.0,
            taxes REAL DEFAULT 0.0,
            total_amount REAL DEFAULT 0.0,
            related_quote_id INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES accounts(id),
            FOREIGN KEY (related_quote_id) REFERENCES sales_documents(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_document_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sales_document_id INTEGER NOT NULL,
            product_id INTEGER,
            product_description TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            discount_percentage REAL DEFAULT 0.0,
            line_total REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sales_document_id) REFERENCES sales_documents(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_sales_documents_updated_at
        AFTER UPDATE ON sales_documents
        FOR EACH ROW
        BEGIN
            UPDATE sales_documents SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_sales_document_items_updated_at
        AFTER UPDATE ON sales_document_items
        FOR EACH ROW
        BEGIN
            UPDATE sales_document_items SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
    """)
