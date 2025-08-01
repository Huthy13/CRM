import sqlite3

SCHEMA_VERSION = 1

def ensure_version_table(cursor: sqlite3.Cursor, version: int) -> None:
    """Ensure the schema_version table exists and is set to the given version."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
    row = cursor.fetchone()
    if row is None:
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    elif row[0] != version:
        cursor.execute("UPDATE schema_version SET version = ?, applied_at = CURRENT_TIMESTAMP", (version,))
