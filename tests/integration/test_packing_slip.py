import os
import tempfile
import unittest

from core.database import DatabaseHandler
from core.inventory_service import InventoryService
from core.sales_logic import SalesLogic
from core.repositories import InventoryRepository, ProductRepository
from shared.structs import AccountType
from core.packing_slip_generator import generate_packing_slip


class PackingSlipIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseHandler(":memory:")
        inventory_repo = InventoryRepository(self.db)
        product_repo = ProductRepository(self.db)
        self.inventory_service = InventoryService(inventory_repo, product_repo)
        self.sales_logic = SalesLogic(self.db, inventory_service=self.inventory_service)
        self.customer_id = self.db.add_account("Cust", None, None, None, AccountType.CUSTOMER.value)
        self.product_id = self.db.add_product(
            sku="PROD1",
            name="Widget",
            description="",
            cost=0,
            sale_price=0,
            is_active=True,
            quantity_on_hand=10,
            reorder_point=0,
            reorder_quantity=0,
            safety_stock=0,
        )

    def tearDown(self):
        self.db.close()

    def test_partial_shipment_packing_slip(self):
        quote = self.sales_logic.create_quote(self.customer_id, reference_number="PO123")
        item = self.sales_logic.add_item_to_sales_document(quote.id, self.product_id, 5, unit_price_override=1.0)
        so = self.sales_logic.convert_quote_to_sales_order(quote.id)
        self.sales_logic.create_shipment(so.id, {item.id: 2})
        items_after = self.sales_logic.get_items_for_sales_document(so.id)
        shipped_items = [(item.product_description, 2)]
        remaining_items = [
            (i.product_description, i.quantity - i.shipped_quantity)
            for i in items_after
            if i.quantity - i.shipped_quantity > 0
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "slip.pdf")
            generate_packing_slip(self.sales_logic, so.id, shipped_items, remaining_items, path)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)


if __name__ == "__main__":
    unittest.main()
