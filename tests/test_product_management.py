import unittest
import os
from core.database import DatabaseHandler
from core.logic import AddressBookLogic
from shared.structs import Product

class TestProductManagement(unittest.TestCase):
    def setUp(self):
        # Use a temporary database for testing
        self.test_db_name = "test_product_management.db"
        self.db_handler = DatabaseHandler(db_name=self.test_db_name)
        self.logic = AddressBookLogic(self.db_handler)

    def tearDown(self):
        # Close the database connection and remove the test database file
        self.db_handler.close()
        if os.path.exists(self.test_db_name):
            os.remove(self.test_db_name)

    def test_add_and_get_product(self):
        # Test adding a product and retrieving it
        product_data = Product(name="Test Laptop", description="A laptop for testing", price=999.99, is_active=True, category="Electronics", unit_of_measure="Each")
        product_id = self.logic.save_product(product_data)
        self.assertIsNotNone(product_id)

        retrieved_product = self.logic.get_product_details(product_id)
        self.assertIsNotNone(retrieved_product)
        self.assertEqual(retrieved_product.name, "Test Laptop")
        self.assertEqual(retrieved_product.description, "A laptop for testing")
        self.assertEqual(retrieved_product.price, 999.99)
        self.assertEqual(retrieved_product.is_active, True)
        self.assertEqual(retrieved_product.category, "Electronics")
        self.assertEqual(retrieved_product.unit_of_measure, "Each")


    def test_get_all_products(self):
        # Test retrieving all products
        self.logic.save_product(Product(name="Product A", description="Desc A", price=10.0, category="Cat A", unit_of_measure="Unit A"))
        self.logic.save_product(Product(name="Product B", description="Desc B", price=20.0, is_active=False, category="Cat B", unit_of_measure="Unit B"))

        all_products = self.logic.get_all_products()
        self.assertEqual(len(all_products), 2)

        product_a = next(p for p in all_products if p.name == "Product A")
        self.assertIsNotNone(product_a)
        self.assertEqual(product_a.category, "Cat A")
        self.assertEqual(product_a.unit_of_measure, "Unit A")
        self.assertTrue(product_a.is_active) # Default is_active is True

        product_b = next(p for p in all_products if p.name == "Product B")
        self.assertIsNotNone(product_b)
        self.assertEqual(product_b.category, "Cat B")
        self.assertEqual(product_b.unit_of_measure, "Unit B")
        self.assertFalse(product_b.is_active)


    def test_update_product(self):
        # Test updating an existing product
        product_data = Product(name="Old Name", description="Old Desc", price=50.0, is_active=True, category="Old Cat", unit_of_measure="Old Unit")
        product_id = self.logic.save_product(product_data)
        self.assertIsNotNone(product_id)

        updated_product_data = Product(product_id=product_id, name="New Name", description="New Desc", price=75.0, is_active=False, category="New Cat", unit_of_measure="New Unit")
        self.logic.save_product(updated_product_data)

        retrieved_product = self.logic.get_product_details(product_id)
        self.assertIsNotNone(retrieved_product)
        self.assertEqual(retrieved_product.name, "New Name")
        self.assertEqual(retrieved_product.description, "New Desc")
        self.assertEqual(retrieved_product.price, 75.0)
        self.assertEqual(retrieved_product.is_active, False)
        self.assertEqual(retrieved_product.category, "New Cat")
        self.assertEqual(retrieved_product.unit_of_measure, "New Unit")

    def test_delete_product(self):
        # Test deleting a product
        product_data = Product(name="To Be Deleted", description="Delete me", price=5.0, category="Temp", unit_of_measure="Item")
        product_id = self.logic.save_product(product_data)
        self.assertIsNotNone(product_id)

        self.logic.delete_product(product_id)
        retrieved_product = self.logic.get_product_details(product_id)
        self.assertIsNone(retrieved_product)

        # Ensure it's not in all products list
        all_products = self.logic.get_all_products()
        self.assertFalse(any(p.product_id == product_id for p in all_products))

    def test_product_price_validation_in_popup_save(self):
        # This is a more conceptual test for the popup logic if it were directly testable here.
        # For actual UI testing, a different framework (e.g., Selenium, Appium, or tkinter-specific tools) would be needed.
        # Here, we're ensuring the database/logic layer handles data correctly.

        # Test case: Valid price
        valid_product = Product(name="Valid Price Product", description="Test", price=19.99)
        valid_id = self.logic.save_product(valid_product)
        self.assertIsNotNone(valid_id)
        retrieved_valid = self.logic.get_product_details(valid_id)
        self.assertEqual(retrieved_valid.price, 19.99)

        # The popup's price validation (e.g., non-negative, numeric) is handled in the UI layer (ProductDetailsPopup).
        # Unit tests here focus on the backend logic.

if __name__ == '__main__':
    unittest.main()
