import sqlite3

def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create account related tables and triggers."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            website TEXT,
            description TEXT,
            pricing_rule_id INTEGER,
            payment_term_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pricing_rule_id) REFERENCES pricing_rules (rule_id) ON DELETE SET NULL,
            FOREIGN KEY (payment_term_id) REFERENCES payment_terms (term_id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_addresses (
            account_id INTEGER NOT NULL,
            address_id INTEGER NOT NULL,
            address_type TEXT NOT NULL,
            is_primary BOOLEAN DEFAULT 0,
            FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
            FOREIGN KEY (address_id) REFERENCES addresses (address_id) ON DELETE CASCADE,
            PRIMARY KEY (account_id, address_id, address_type)
        )
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_accounts_updated_at
        AFTER UPDATE ON accounts
        FOR EACH ROW
        BEGIN
            UPDATE accounts SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            role TEXT,
            account_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_contacts_updated_at
        AFTER UPDATE ON contacts
        FOR EACH ROW
        BEGIN
            UPDATE contacts SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_documents (
            document_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE
        )
    """)
