import sqlite3

def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create common tables used across domains."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS addresses (
            address_id INTEGER PRIMARY KEY AUTOINCREMENT,
            street TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            zip TEXT NOT NULL,
            country TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pricing_rules (
            rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_name TEXT UNIQUE NOT NULL,
            markup_percentage FLOAT,
            fixed_price FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT either_markup_or_fixed CHECK (markup_percentage IS NOT NULL OR fixed_price IS NOT NULL)
        )
    """)
