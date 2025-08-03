import os
import subprocess
import time
import unittest
import tkinter as tk
from unittest.mock import MagicMock

from core.database import DatabaseHandler
from core.sales_logic import SalesLogic
from core.address_book_logic import AddressBookLogic
from shared.structs import AccountType
from ui.sales_documents.sales_document_popup import SalesDocumentPopup


class SalesShipmentsUITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xvfb = subprocess.Popen(["Xvfb", ":1"])
        os.environ["DISPLAY"] = ":1"
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.xvfb.terminate()

    def setUp(self):
        self.db = DatabaseHandler(":memory:")
        self.sales_logic = SalesLogic(self.db)
        self.address_logic = AddressBookLogic(self.db)
        self.root = tk.Tk()
        self.root.withdraw()

        self.customer_id = self.db.add_account(
            "Cust", None, None, None, AccountType.CUSTOMER.value
        )
        self.product_id = self.db.add_product(
            sku="P1",
            name="Product",
            description="",
            cost=1.0,
            sale_price=10.0,
            is_active=True,
            quantity_on_hand=10,
        )
        quote = self.sales_logic.create_quote(
            self.customer_id, reference_number="REF"
        )
        self.sales_logic.add_item_to_sales_document(
            quote.id, self.product_id, 5, unit_price_override=10.0
        )
        self.so = self.sales_logic.convert_quote_to_sales_order(quote.id)
        items = self.sales_logic.get_items_for_sales_document(self.so.id)
        self.sales_logic.record_item_shipment(items[0].id, 2)

    def tearDown(self):
        self.root.destroy()
        self.db.close()

    def test_shipments_displayed(self):
        popup = SalesDocumentPopup(
            self.root,
            self.sales_logic,
            self.address_logic,
            MagicMock(),
            document_id=self.so.id,
        )
        shipments = popup.shipments_tree.get_children()
        self.assertEqual(len(shipments), 1)
        first = shipments[0]
        subitems = popup.shipments_tree.get_children(first)
        self.assertEqual(len(subitems), 1)
        popup.destroy()


if __name__ == "__main__":
    unittest.main()
