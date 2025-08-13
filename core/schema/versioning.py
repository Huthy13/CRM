import sqlite3
from typing import Callable, Dict


# The current schema version of the application.  Increment this whenever a
# backwards compatible migration is added below.
SCHEMA_VERSION = 2


def ensure_version_table(cursor: sqlite3.Cursor) -> None:
    """Ensure that the ``schema_version`` table exists.

    The table keeps a history of schema migrations that have been applied to the
    database.  We do **not** insert a row for the current version here because
    that is handled by :func:`apply_migrations` after any required migrations are
    executed.
    """

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def get_current_version(cursor: sqlite3.Cursor) -> int:
    """Return the most recently applied schema version.

    If the table is empty (i.e. a brand new database) we consider the version to
    be ``0``.
    """

    cursor.execute("SELECT MAX(version) FROM schema_version")
    row = cursor.fetchone()
    return row[0] if row and row[0] is not None else 0


def _column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def _add_column_if_missing(cursor: sqlite3.Cursor, table: str, column: str, definition: str) -> None:
    if not _column_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _migrate_to_2(cursor: sqlite3.Cursor) -> None:
    """Migration to schema version 2.

    Version 2 introduces inventory tracking fields on the ``products`` table. If
    these columns are missing we add them and backfill the
    ``quantity_on_hand`` value from the existing ``product_inventory`` table.
    """

    _add_column_if_missing(cursor, "products", "quantity_on_hand", "REAL NOT NULL DEFAULT 0")
    _add_column_if_missing(cursor, "products", "reorder_point", "REAL NOT NULL DEFAULT 0")
    _add_column_if_missing(cursor, "products", "reorder_quantity", "REAL NOT NULL DEFAULT 0")
    _add_column_if_missing(cursor, "products", "safety_stock", "REAL NOT NULL DEFAULT 0")

    cursor.execute(
        """
        UPDATE products
        SET quantity_on_hand = (
            SELECT IFNULL(SUM(quantity), 0)
            FROM product_inventory
            WHERE product_id = products.id
        )
        """
    )


# Mapping of schema version -> migration function.  Each migration upgrades the
# database *from* the previous version *to* the specified version.
MIGRATIONS: Dict[int, Callable[[sqlite3.Cursor], None]] = {
    2: _migrate_to_2,
}


def apply_migrations(cursor: sqlite3.Cursor, target_version: int = SCHEMA_VERSION) -> None:
    """Apply any outstanding migrations up to ``target_version``.

    This function is idempotent – running it multiple times will have no effect
    once the database has reached ``target_version``.
    """

    ensure_version_table(cursor)
    current_version = get_current_version(cursor)

    for version in range(current_version + 1, target_version + 1):
        migration = MIGRATIONS.get(version)
        if migration:
            migration(cursor)
        # Record that the migration has been applied.  We keep a history of
        # versions so a simple INSERT suffices.
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
