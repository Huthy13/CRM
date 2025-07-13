import unittest
import sqlite3
from core.logic.product_management import ProductLogic
from core.database import DatabaseHandler
from shared.structs import Product

class TestUnitTypes(unittest.TestCase):
    def setUp(self):
        self.db_handler = DatabaseHandler(db_name=":memory:")
        self.product_logic = ProductLogic(self.db_handler)

    def tearDown(self):
        self.db_handler.close()

    def test_add_unit_type(self):
        unit_type_id = self.product_logic.add_unit_type("Test Unit")
        self.assertIsNotNone(unit_type_id)
        unit_types = self.product_logic.get_all_unit_types()
        self.assertEqual(len(unit_types), 1)
        self.assertEqual(unit_types[0]['name'], "Test Unit")

    def test_update_unit_type(self):
        unit_type_id = self.product_logic.add_unit_type("Test Unit")
        self.product_logic.update_unit_type(unit_type_id, "Updated Test Unit")
        unit_types = self.product_logic.get_all_unit_types()
        self.assertEqual(len(unit_types), 1)
        self.assertEqual(unit_types[0]['name'], "Updated Test Unit")

    def test_delete_unit_type(self):
        unit_type_id = self.product_logic.add_unit_type("Test Unit")
        self.product_logic.delete_unit_type(unit_type_id)
        unit_types = self.product_logic.get_all_unit_types()
        self.assertEqual(len(unit_types), 0)

    def test_product_with_unit_type(self):
        unit_type_id = self.product_logic.add_unit_type("Pieces")
        product = Product(
            name="Test Product",
            description="A product for testing",
            cost=19.99,
            sale_price=29.99,
            is_active=True,
            category="Test Category",
            unit_of_measure="Pieces"
        )
        product_id = self.product_logic.save_product(product)
        self.assertIsNotNone(product_id)

        retrieved_product = self.product_logic.get_product_details(product_id)
        self.assertEqual(retrieved_product.unit_of_measure, "Pieces")

if __name__ == '__main__':
    unittest.main()
