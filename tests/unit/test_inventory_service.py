import unittest

from core.database import DatabaseHandler
from core.repositories import InventoryRepository, ProductRepository
from core.inventory_service import InventoryService
from shared.structs import InventoryTransactionType

TEST_DB = ":memory:"

class InventoryServiceTest(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseHandler(TEST_DB)
        self.inventory_repo = InventoryRepository(self.db)
        self.product_repo = ProductRepository(self.db)
        self.product_id = self.db.add_product(
            sku="PROD1", name="Test Prod", description="desc", cost=0, sale_price=0, is_active=True,
            quantity_on_hand=8, reorder_point=5, reorder_quantity=10, safety_stock=2
        )

    def tearDown(self):
        self.db.close()

    def test_adjust_stock_logs_and_queues(self):
        service = InventoryService(self.inventory_repo, self.product_repo)
        new_level = service.adjust_stock(
            self.product_id, -6, InventoryTransactionType.SALE, reference="SO#1"
        )
        self.assertEqual(new_level, 2)
        tx = self.inventory_repo.get_transactions(self.product_id)
        self.assertEqual(len(tx), 1)
        self.assertEqual(tx[0]["transaction_type"], InventoryTransactionType.SALE.value)
        queue = self.inventory_repo.get_replenishment_queue()
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["quantity_needed"], 10)

    def test_adjust_stock_increase(self):
        service = InventoryService(self.inventory_repo, self.product_repo)
        service.adjust_stock(self.product_id, 5, InventoryTransactionType.PURCHASE)
        level = self.inventory_repo.get_stock_level(self.product_id)
        self.assertEqual(level, 13)
        queue = self.inventory_repo.get_replenishment_queue()
        self.assertEqual(len(queue), 0)

    def test_record_purchase_order_tracks_quantity(self):
        service = InventoryService(self.inventory_repo, self.product_repo)
        service.record_purchase_order(self.product_id, 4, reference="PO#1")
        self.assertEqual(self.inventory_repo.get_on_order_level(self.product_id), 4)
        # On-hand stock should remain unchanged
        self.assertEqual(self.inventory_repo.get_stock_level(self.product_id), 8)
        service.record_purchase_order(self.product_id, -2, reference="PO#1")
        self.assertEqual(self.inventory_repo.get_on_order_level(self.product_id), 2)

if __name__ == "__main__":
    unittest.main()
