import os
import sqlite3
import tempfile
import unittest

from scripts.migrate_inventory import run_migration

class InventoryMigrationTest(unittest.TestCase):
    def test_migration_adds_columns_and_backfills(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute("CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, name TEXT)")
            cur.execute("INSERT INTO products (sku, name) VALUES ('P1', 'Prod')")
            cur.execute(
                "CREATE TABLE product_inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, location_id INTEGER, quantity REAL)"
            )
            cur.execute(
                "INSERT INTO product_inventory (product_id, location_id, quantity) VALUES (1,1,7)"
            )
            conn.commit()
            conn.close()

            run_migration(path)

            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(products)")
            cols = {row[1] for row in cur.fetchall()}
            self.assertIn("quantity_on_hand", cols)
            self.assertIn("reorder_point", cols)
            cur.execute("SELECT quantity_on_hand, reorder_point, safety_stock FROM products WHERE id=1")
            qty, rp, ss = cur.fetchone()
            self.assertEqual(qty, 7)
            self.assertEqual(rp, 0)
            self.assertEqual(ss, 0)
            conn.close()
        finally:
            os.remove(path)

if __name__ == "__main__":
    unittest.main()
