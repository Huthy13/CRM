import sqlite3

from .schema import (
    accounts,
    common,
    company,
    interactions,
    products,
    inventory,
    purchase,
    sales,
    tasks,
    users,
    versioning,
)

DB_NAME = "product_management.db"

def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(db_conn=None):
    """Create all necessary tables for the application."""
    conn_was_provided = db_conn is not None
    conn = db_conn if conn_was_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        for module in (
            common,
            products,
            accounts,
            users,
            interactions,
            tasks,
            sales,
            purchase,
            inventory,
            company,
        ):
            module.create_schema(cursor)
        # Ensure account_documents table exists for storing documents linked to accounts
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS account_documents (
                document_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                document_name TEXT,
                description TEXT,
                document_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE
            )
            """
        )
        versioning.ensure_version_table(cursor, versioning.SCHEMA_VERSION)
        conn.commit()
        print("Database tables created successfully (if they didn't exist).")
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
        raise
    finally:
        if not conn_was_provided and conn:
            conn.close()

def initialize_database(db_conn=None):
    """Initialise the database and seed essential data."""
    db_label = DB_NAME if db_conn is None else "provided connection"
    print(f"Initializing database '{db_label}'...")
    create_tables(db_conn=db_conn)

    conn_was_provided = db_conn is not None
    conn = db_conn if conn_was_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (username) VALUES ('system_user')")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error seeding initial data: {e}")
    finally:
        if not conn_was_provided and conn:
            conn.close()

if __name__ == "__main__":
    initialize_database()
