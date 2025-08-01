import unittest

from core.database import DatabaseHandler
from core.repositories import InventoryRepository, ProductRepository, PurchaseOrderRepository
from core.inventory_service import InventoryService
from core.purchase_order_service import PurchaseOrderService
from shared.structs import (
    InventoryTransactionType,
    PurchaseOrderLineItem,
    PurchaseOrderStatus,
)

TEST_DB = ":memory:"

class PurchaseOrderServiceTest(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseHandler(TEST_DB)
        self.inventory_repo = InventoryRepository(self.db)
        self.product_repo = ProductRepository(self.db)
        self.po_repo = PurchaseOrderRepository(self.db)
        self.inventory_service = InventoryService(self.inventory_repo, self.product_repo)
        # vendor and product
        self.vendor_id = self.db.add_account("Vendor", None, None, None, "VENDOR")
        self.product_id = self.db.add_product(sku="PROD2", name="Widget", description="desc", cost=0, sale_price=0, is_active=True)
        # map product to vendor
        self.db.cursor.execute(
            "INSERT INTO product_vendors (product_id, vendor_id) VALUES (?, ?)",
            (self.product_id, self.vendor_id),
        )
        self.db.conn.commit()

    def tearDown(self):
        self.db.close()

    def test_create_and_receive_po(self):
        service = PurchaseOrderService(self.po_repo, self.inventory_service)
        line = PurchaseOrderLineItem(product_id=self.product_id, quantity=5)
        po = service.create_purchase_order(self.vendor_id, [line])
        self.assertEqual(po.status, PurchaseOrderStatus.OPEN)
        self.assertEqual(po.vendor_id, self.vendor_id)
        po = service.receive_purchase_order(po.id)
        self.assertEqual(po.status, PurchaseOrderStatus.RECEIVED)
        level = self.inventory_repo.get_stock_level(self.product_id)
        self.assertEqual(level, 5)
        tx = self.inventory_repo.get_transactions(self.product_id)
        self.assertEqual(tx[0]["transaction_type"], InventoryTransactionType.PURCHASE.value)

if __name__ == "__main__":
    unittest.main()
