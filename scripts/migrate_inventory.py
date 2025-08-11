"""One-time migration to add inventory columns to products and backfill quantities."""
import sqlite3
from core.database_setup import DB_NAME
from shared.logging_config import setup_logging

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

def add_column_if_missing(cursor, table, column, definition):
    if not column_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def run_migration(db_path=DB_NAME):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        add_column_if_missing(cur, "products", "quantity_on_hand", "REAL NOT NULL DEFAULT 0")
        add_column_if_missing(cur, "products", "reorder_point", "REAL NOT NULL DEFAULT 0")
        add_column_if_missing(cur, "products", "reorder_quantity", "REAL NOT NULL DEFAULT 0")
        add_column_if_missing(cur, "products", "safety_stock", "REAL NOT NULL DEFAULT 0")
        cur.execute(
            """
            UPDATE products
            SET quantity_on_hand = (
                SELECT IFNULL(SUM(quantity),0) FROM product_inventory WHERE product_id = products.id
            )
            """
        )
        conn.commit()
        print("Inventory migration completed.")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_logging()
    run_migration()
