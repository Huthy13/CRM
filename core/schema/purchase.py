import sqlite3

def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create purchase document tables and triggers."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_number TEXT UNIQUE NOT NULL,
            vendor_id INTEGER NOT NULL,
            created_date TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES accounts(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_document_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_document_id INTEGER NOT NULL,
            product_id INTEGER,
            product_description TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL,
            total_price REAL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (purchase_document_id) REFERENCES purchase_documents(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_purchase_documents_updated_at
        AFTER UPDATE ON purchase_documents
        FOR EACH ROW
        BEGIN
            UPDATE purchase_documents SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_purchase_document_items_updated_at
        AFTER UPDATE ON purchase_document_items
        FOR EACH ROW
        BEGIN
            UPDATE purchase_document_items SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
    """)
