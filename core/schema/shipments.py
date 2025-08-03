import sqlite3


def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create tables for shipments and their items."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sales_document_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sales_document_id) REFERENCES sales_documents(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS shipment_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_id INTEGER NOT NULL,
            sales_document_item_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shipment_id) REFERENCES shipments(id),
            FOREIGN KEY (sales_document_item_id) REFERENCES sales_document_items(id)
        )
        """
    )
