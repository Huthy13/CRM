import unittest

from core.database import DatabaseHandler
from core.repositories import (
    InventoryRepository,
    ProductRepository,
    PurchaseOrderRepository,
)
from core.inventory_service import InventoryService
from core.purchase_order_service import PurchaseOrderService
from core.replenishment_service import ReplenishmentService
from shared.structs import InventoryTransactionType

TEST_DB = ":memory:"

class ReplenishmentServiceTest(unittest.TestCase):
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
        # vendor and product
        self.vendor_id = self.db.add_account("Vendor", None, None, None, "VENDOR")
        self.product_id = self.db.add_product(
            sku="PROD3", name="Gadget", description="desc", cost=0, sale_price=0, is_active=True,
            quantity_on_hand=5, reorder_point=6, reorder_quantity=10
        )
        self.db.cursor.execute(
            "INSERT INTO product_vendors (product_id, vendor_id) VALUES (?, ?)",
            (self.product_id, self.vendor_id),
        )
        self.db.conn.commit()

    def tearDown(self):
        self.db.close()

    def test_process_queue_creates_po(self):
        # trigger replenishment by selling 1 unit -> stock 4 (below reorder 6)
        self.inventory_service.adjust_stock(
            self.product_id, -1, InventoryTransactionType.SALE
        )
        queue = self.inventory_repo.get_replenishment_queue()
        self.assertEqual(len(queue), 1)
        created = self.replenish_service.process_queue()
        self.assertEqual(len(created), 1)
        queue = self.inventory_repo.get_replenishment_queue()
        self.assertEqual(len(queue), 0)
        orders = self.po_repo.get_all_purchase_orders()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["vendor_id"], self.vendor_id)

if __name__ == "__main__":
    unittest.main()
