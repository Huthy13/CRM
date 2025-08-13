import os
import sqlite3
import tempfile

from core.database_setup import initialize_database
from core.schema import versioning


def test_initialize_database_applies_migrations():
    """Existing databases are upgraded in place without data loss."""

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        # Create a database that mimics an old schema version (v1)
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        cur.execute("INSERT INTO schema_version (version) VALUES (1)")
        # Simulate a simplified version of the original products table prior to
        # version 2.  It lacks the inventory related columns that the migration
        # will add but includes an ``updated_at`` column so that triggers created
        # during table initialisation function correctly.
        cur.execute(
            "CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, name TEXT, updated_at DATETIME)"
        )
        cur.execute("INSERT INTO products (sku, name) VALUES ('P1', 'Prod')")
        cur.execute(
            "CREATE TABLE product_inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, location_id INTEGER, quantity REAL)"
        )
        cur.execute(
            "INSERT INTO product_inventory (product_id, location_id, quantity) VALUES (1,1,7)"
        )
        conn.commit()
        conn.close()

        # Run initialization which should apply migrations and preserve data
        conn = sqlite3.connect(path)
        initialize_database(db_conn=conn)

        cur = conn.cursor()
        cur.execute("PRAGMA table_info(products)")
        cols = {row[1] for row in cur.fetchall()}
        assert {
            "quantity_on_hand",
            "reorder_point",
            "reorder_quantity",
            "safety_stock",
        }.issubset(cols)

        cur.execute(
            "SELECT quantity_on_hand, reorder_point, reorder_quantity, safety_stock FROM products WHERE id=1"
        )
        qoh, rp, rq, ss = cur.fetchone()
        assert qoh == 7
        assert rp == 0 and rq == 0 and ss == 0

        cur.execute("SELECT MAX(version) FROM schema_version")
        assert cur.fetchone()[0] == versioning.SCHEMA_VERSION
        conn.close()
    finally:
        os.remove(path)

