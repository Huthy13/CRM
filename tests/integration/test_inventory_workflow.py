import unittest

from core.database import DatabaseHandler
from core.inventory_service import InventoryService
from core.purchase_order_service import PurchaseOrderService
from core.replenishment_service import ReplenishmentService
from core.sales_logic import SalesLogic
from core.repositories import (
    InventoryRepository,
    ProductRepository,
    PurchaseOrderRepository,
)
from shared.structs import AccountType

TEST_DB = ":memory:"

class InventoryWorkflowIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseHandler(TEST_DB)
        self.inventory_repo = InventoryRepository(self.db)
        self.product_repo = ProductRepository(self.db)
        self.po_repo = PurchaseOrderRepository(self.db)
        self.inventory_service = InventoryService(self.inventory_repo, self.product_repo)
        self.po_service = PurchaseOrderService(self.po_repo, self.inventory_service)
        self.replenish_service = ReplenishmentService(
            self.inventory_repo, self.product_repo, self.po_service
        )
        self.sales_logic = SalesLogic(self.db, inventory_service=self.inventory_service)
        # accounts
        self.customer_id = self.db.add_account("Cust", None, None, None, AccountType.CUSTOMER.value)
        self.vendor_id = self.db.add_account("Vend", None, None, None, AccountType.VENDOR.value)
        self.product_id = self.db.add_product(
            sku="PROD4", name="Thing", description="", cost=0, sale_price=0, is_active=True,
            quantity_on_hand=15, reorder_point=10, reorder_quantity=20
        )
        self.db.cursor.execute(
            "INSERT INTO product_vendors (product_id, vendor_id) VALUES (?, ?)",
            (self.product_id, self.vendor_id),
        )
        self.db.conn.commit()

    def tearDown(self):
        self.db.close()

    def test_full_inventory_cycle(self):
        quote = self.sales_logic.create_quote(self.customer_id, reference_number="PO123")
        self.sales_logic.add_item_to_sales_document(
            quote.id, self.product_id, 10, unit_price_override=5.0
        )
        so = self.sales_logic.convert_quote_to_sales_order(quote.id)
        self.sales_logic.confirm_sales_order(so.id)
        queue = self.inventory_repo.get_replenishment_queue()
        self.assertEqual(len(queue), 1)
        po_ids = self.replenish_service.process_queue()
        self.assertEqual(len(po_ids), 1)
        self.po_service.receive_purchase_order(po_ids[0])
        level = self.inventory_repo.get_stock_level(self.product_id)
        self.assertEqual(level, 25)

if __name__ == "__main__":
    unittest.main()
