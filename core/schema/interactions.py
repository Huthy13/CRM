import sqlite3

def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create the interactions table and trigger."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            contact_id INTEGER,
            interaction_type TEXT CHECK(interaction_type IN ('Call', 'Email', 'Meeting', 'Visit', 'Other')) NOT NULL,
            date_time TEXT NOT NULL,
            subject TEXT(150) NOT NULL,
            description TEXT,
            created_by_user_id INTEGER,
            attachment_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES accounts (id) ON DELETE SET NULL,
            FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE SET NULL,
            FOREIGN KEY (created_by_user_id) REFERENCES users (user_id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_interactions_updated_at
        AFTER UPDATE ON interactions
        FOR EACH ROW
        BEGIN
            UPDATE interactions SET updated_at = CURRENT_TIMESTAMP WHERE interaction_id = OLD.interaction_id;
        END;
    """)
