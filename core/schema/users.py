import sqlite3

def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create the users table."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    """)
