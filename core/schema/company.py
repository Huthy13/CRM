import sqlite3

def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create company information tables and triggers."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_information (
            company_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            billing_address_id INTEGER,
            shipping_address_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (billing_address_id) REFERENCES addresses (address_id) ON DELETE SET NULL,
            FOREIGN KEY (shipping_address_id) REFERENCES addresses (address_id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_addresses (
            company_id INTEGER NOT NULL,
            address_id INTEGER NOT NULL,
            address_type TEXT NOT NULL,
            is_primary BOOLEAN DEFAULT 0,
            FOREIGN KEY (company_id) REFERENCES company_information (company_id) ON DELETE CASCADE,
            FOREIGN KEY (address_id) REFERENCES addresses (address_id) ON DELETE CASCADE,
            PRIMARY KEY (company_id, address_id, address_type)
        )
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_company_information_updated_at
        AFTER UPDATE ON company_information
        FOR EACH ROW
        BEGIN
            UPDATE company_information SET updated_at = CURRENT_TIMESTAMP WHERE company_id = OLD.company_id;
        END;
    """)
