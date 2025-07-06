import unittest
import os
from core.database import DatabaseHandler
from core.address_book_logic import AddressBookLogic
from shared.structs import Product

class TestAddressBookLogic(unittest.TestCase):
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
        product_data = Product(name="Test Laptop", description="A laptop for testing", cost=999.99, is_active=True, category="Electronics", unit_of_measure="Each") # price -> cost
        product_id = self.logic.save_product(product_data)
        self.assertIsNotNone(product_id)

        retrieved_product = self.logic.get_product_details(product_id)
        self.assertIsNotNone(retrieved_product)
        self.assertEqual(retrieved_product.name, "Test Laptop")
        self.assertEqual(retrieved_product.description, "A laptop for testing")
        self.assertEqual(retrieved_product.cost, 999.99) # price -> cost
        self.assertEqual(retrieved_product.is_active, True)
        self.assertEqual(retrieved_product.category, "Electronics")
        self.assertEqual(retrieved_product.unit_of_measure, "Each")


    def test_get_all_products(self):
        # Test retrieving all products
        self.logic.save_product(Product(name="Product A", description="Desc A", cost=10.0, category="Cat A", unit_of_measure="Unit A")) # price -> cost
        self.logic.save_product(Product(name="Product B", description="Desc B", cost=20.0, is_active=False, category="Cat B", unit_of_measure="Unit B")) # price -> cost

        all_products = self.logic.get_all_products()
        self.assertEqual(len(all_products), 2)

        product_a = next(p for p in all_products if p.name == "Product A")
        self.assertIsNotNone(product_a)
        self.assertEqual(product_a.category, "Cat A")
        self.assertEqual(product_a.unit_of_measure, "Unit A")
        self.assertTrue(product_a.is_active)

        product_b = next(p for p in all_products if p.name == "Product B")
        self.assertIsNotNone(product_b)
        self.assertEqual(product_b.category, "Cat B")
        self.assertEqual(product_b.unit_of_measure, "Unit B")
        self.assertFalse(product_b.is_active)


    def test_update_product(self):
        # Test updating an existing product
        product_data = Product(name="Old Name", description="Old Desc", cost=50.0, is_active=True, category="Old Cat", unit_of_measure="Old Unit") # price -> cost
        product_id = self.logic.save_product(product_data)
        self.assertIsNotNone(product_id)

        updated_product_data = Product(product_id=product_id, name="New Name", description="New Desc", cost=75.0, is_active=False, category="New Cat", unit_of_measure="New Unit") # price -> cost
        self.logic.save_product(updated_product_data)

        retrieved_product = self.logic.get_product_details(product_id)
        self.assertIsNotNone(retrieved_product)
        self.assertEqual(retrieved_product.name, "New Name")
        self.assertEqual(retrieved_product.description, "New Desc")
        self.assertEqual(retrieved_product.cost, 75.0) # price -> cost
        self.assertEqual(retrieved_product.is_active, False)
        self.assertEqual(retrieved_product.category, "New Cat")
        self.assertEqual(retrieved_product.unit_of_measure, "New Unit")

    def test_delete_product(self):
        # Test deleting a product
        product_data = Product(name="To Be Deleted", description="Delete me", cost=5.0, category="Temp", unit_of_measure="Item") # price -> cost
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

        # Test case: Valid cost
        valid_product = Product(name="Valid Cost Product", description="Test", cost=19.99)
        valid_id = self.logic.save_product(valid_product)
        self.assertIsNotNone(valid_id)
        retrieved_valid = self.logic.get_product_details(valid_id)
        self.assertEqual(retrieved_valid.cost, 19.99) # price -> cost in assertion

        # The popup's cost validation (e.g., non-negative, numeric) is handled in the UI layer (ProductDetailsPopup).
        # Unit tests here focus on the backend logic.

    def test_add_product_with_new_and_existing_category(self):
        # Add product with a new category
        prod1_id = self.logic.save_product(Product(name="Product 1", category="Alpha", cost=10)) # price -> cost
        retrieved_prod1 = self.logic.get_product_details(prod1_id)
        self.assertEqual(retrieved_prod1.category, "Alpha")

        # Check if "Alpha" is in the categories table
        categories = self.logic.get_all_product_categories()
        self.assertIn("Alpha", categories)

        # Add product with an existing category
        prod2_id = self.logic.save_product(Product(name="Product 2", category="Alpha", cost=20)) # price -> cost
        retrieved_prod2 = self.logic.get_product_details(prod2_id)
        self.assertEqual(retrieved_prod2.category, "Alpha")

        # Ensure "Alpha" is still there and not duplicated in the master list
        categories_after_second_add = self.logic.get_all_product_categories()
        self.assertEqual(categories_after_second_add.count("Alpha"), 1)
        self.assertEqual(len(categories_after_second_add), 1)

        # Add product with another new category
        self.logic.save_product(Product(name="Product 3", category="Beta", cost=30)) # price -> cost
        categories_after_third_add = self.logic.get_all_product_categories()
        self.assertIn("Beta", categories_after_third_add)
        self.assertEqual(len(categories_after_third_add), 2) # Alpha, Beta

    def test_add_product_with_empty_category(self):
        prod_id = self.logic.save_product(Product(name="Product NoCat", category="", cost=10))
        retrieved_prod = self.logic.get_product_details(prod_id)
        self.assertEqual(retrieved_prod.category, "") # Empty category path should be empty string

        # Ensure empty string is not added to the categories table
        categories = self.logic.get_all_product_categories()
        self.assertNotIn("", categories)
        self.assertEqual(len(categories), 0)

    def test_update_product_category(self):
        # Add product with initial category
        prod_id = self.logic.save_product(Product(name="Product X", category="InitialCat", cost=100)) # price -> cost
        retrieved_prod_initial = self.logic.get_product_details(prod_id)
        self.assertEqual(retrieved_prod_initial.category, "InitialCat")

        # Update to a new category
        self.logic.save_product(Product(product_id=prod_id, name="Product X Updated", category="UpdatedCat", cost=110)) # price -> cost
        retrieved_prod_updated = self.logic.get_product_details(prod_id)
        self.assertEqual(retrieved_prod_updated.category, "UpdatedCat")

        categories = self.logic.get_all_product_categories()
        self.assertIn("InitialCat", categories)
        self.assertIn("UpdatedCat", categories)
        self.assertEqual(len(categories), 2)

        # Update to an existing category
        self.logic.save_product(Product(product_id=prod_id, name="Product X Final", category="InitialCat", cost=120)) # price -> cost
        retrieved_prod_final = self.logic.get_product_details(prod_id)
        self.assertEqual(retrieved_prod_final.category, "InitialCat")

        categories_final = self.logic.get_all_product_categories()
        self.assertEqual(categories_final.count("InitialCat"), 1)
        self.assertEqual(categories_final.count("UpdatedCat"), 1)
        self.assertEqual(len(categories_final), 2)


    def test_get_all_product_categories_from_table(self):
        # Test retrieving unique product categories from the dedicated table
        self.logic.save_product(Product(name="Prod A", category="Electronics", cost=10)) # price -> cost
        self.logic.save_product(Product(name="Prod B", category="Books", cost=20)) # price -> cost
        self.logic.save_product(Product(name="Prod C", category="Electronics", cost=30)) # price -> cost
        self.logic.save_product(Product(name="Prod D", category="Home Goods", cost=40)) # price -> cost
        self.logic.save_product(Product(name="Prod E", category="", cost=50)) # price -> cost
        self.logic.save_product(Product(name="Prod F", category="Books", cost=60)) # price -> cost

        categories = self.logic.get_all_product_categories() # This now calls get_all_product_categories_from_table

        self.assertIsInstance(categories, list)
        self.assertEqual(len(categories), 3)
        self.assertIn("Electronics", categories)
        self.assertIn("Books", categories)
        self.assertIn("Home Goods", categories)
        self.assertNotIn("", categories)

        # Check sorting (logic layer should receive sorted list from DB)
        self.assertEqual(categories, sorted(categories))

        # Test that categories persist even if no product uses them
        prod_a_id = self.logic.get_all_products()[0].product_id # Get an ID
        self.logic.delete_product(prod_a_id)
        # Find another product with a unique category to delete
        home_goods_prod = next(p for p in self.logic.get_all_products() if p.category == "Home Goods")
        self.logic.delete_product(home_goods_prod.product_id)

        # Delete all products for "Books"
        book_products = [p for p in self.logic.get_all_products() if p.category == "Books"]
        for p in book_products:
            self.logic.delete_product(p.product_id)

        # Delete all products for "Electronics"
        elec_products = [p for p in self.logic.get_all_products() if p.category == "Electronics"]
        for p in elec_products:
            self.logic.delete_product(p.product_id)

        remaining_products = self.logic.get_all_products()
        self.assertEqual(len(remaining_products), 1) # Prod E (with empty category) should remain
        if remaining_products: # Ensure it's the one we expect
            self.assertEqual(remaining_products[0].name, "Prod E")
            self.assertEqual(remaining_products[0].category, "") # Path for None category_id is ""

        # Categories should still exist in the product_categories table
        categories_after_deletes = self.logic.get_all_product_categories()
        self.assertEqual(len(categories_after_deletes), 3) # Electronics, Books, Home Goods should persist
        self.assertIn("Electronics", categories_after_deletes)
        self.assertIn("Books", categories_after_deletes)
        self.assertIn("Home Goods", categories_after_deletes)


        # Test with no categories initially
        self.tearDown()
        self.setUp()
        no_categories = self.logic.get_all_product_categories()
        self.assertEqual(len(no_categories), 0)

# --- Unit of Measure Tests ---

    def test_add_product_with_new_and_existing_unit(self):
        prod1_id = self.logic.save_product(Product(name="Product U1", unit_of_measure="Piece", cost=10)) # price -> cost
        retrieved_prod1 = self.logic.get_product_details(prod1_id)
        self.assertEqual(retrieved_prod1.unit_of_measure, "Piece")

        units = self.logic.get_all_product_units_of_measure()
        self.assertIn("Piece", units)

        prod2_id = self.logic.save_product(Product(name="Product U2", unit_of_measure="Piece", cost=20)) # price -> cost
        retrieved_prod2 = self.logic.get_product_details(prod2_id)
        self.assertEqual(retrieved_prod2.unit_of_measure, "Piece")

        units_after_second_add = self.logic.get_all_product_units_of_measure()
        self.assertEqual(units_after_second_add.count("Piece"), 1)
        self.assertEqual(len(units_after_second_add), 1)

        self.logic.save_product(Product(name="Product U3", unit_of_measure="Box", cost=30)) # price -> cost
        units_after_third_add = self.logic.get_all_product_units_of_measure()
        self.assertIn("Box", units_after_third_add)
        self.assertEqual(len(units_after_third_add), 2)

    def test_add_product_with_empty_unit_of_measure(self):
        prod_id = self.logic.save_product(Product(name="Product NoUnit", unit_of_measure="", cost=10)) # price -> cost
        retrieved_prod = self.logic.get_product_details(prod_id)
        self.assertEqual(retrieved_prod.unit_of_measure, None)

        units = self.logic.get_all_product_units_of_measure()
        self.assertNotIn("", units)
        self.assertEqual(len(units), 0)

    def test_update_product_unit_of_measure(self):
        prod_id = self.logic.save_product(Product(name="Product Y", unit_of_measure="InitialUnit", cost=100)) # price -> cost
        retrieved_prod_initial = self.logic.get_product_details(prod_id)
        self.assertEqual(retrieved_prod_initial.unit_of_measure, "InitialUnit")

        self.logic.save_product(Product(product_id=prod_id, name="Product Y Updated", unit_of_measure="UpdatedUnit", cost=110)) # price -> cost
        retrieved_prod_updated = self.logic.get_product_details(prod_id)
        self.assertEqual(retrieved_prod_updated.unit_of_measure, "UpdatedUnit")

        units = self.logic.get_all_product_units_of_measure()
        self.assertIn("InitialUnit", units)
        self.assertIn("UpdatedUnit", units)
        self.assertEqual(len(units), 2)

        self.logic.save_product(Product(product_id=prod_id, name="Product Y Final", unit_of_measure="InitialUnit", cost=120)) # price -> cost
        retrieved_prod_final = self.logic.get_product_details(prod_id)
        self.assertEqual(retrieved_prod_final.unit_of_measure, "InitialUnit")

        units_final = self.logic.get_all_product_units_of_measure()
        self.assertEqual(units_final.count("InitialUnit"), 1)
        self.assertEqual(units_final.count("UpdatedUnit"), 1)
        self.assertEqual(len(units_final), 2)

    def test_get_all_product_units_of_measure_from_table(self):
        self.logic.save_product(Product(name="UnitProd A", unit_of_measure="KG", cost=10)) # price -> cost
        self.logic.save_product(Product(name="UnitProd B", unit_of_measure="Meter", cost=20)) # price -> cost
        self.logic.save_product(Product(name="UnitProd C", unit_of_measure="KG", cost=30)) # price -> cost
        self.logic.save_product(Product(name="UnitProd D", unit_of_measure="Liter", cost=40)) # price -> cost
        self.logic.save_product(Product(name="UnitProd E", unit_of_measure="", cost=50)) # price -> cost

        units = self.logic.get_all_product_units_of_measure()

        self.assertIsInstance(units, list)
        self.assertEqual(len(units), 3)
        self.assertIn("KG", units)
        self.assertIn("Meter", units)
        self.assertIn("Liter", units)
        self.assertNotIn("", units)
        self.assertEqual(units, sorted(units))

        # Test persistence after product deletion
        products_to_delete = self.logic.get_all_products()
        for p in products_to_delete:
            self.logic.delete_product(p.product_id)

        remaining_products = self.logic.get_all_products()
        self.assertEqual(len(remaining_products), 0)

        units_after_deletes = self.logic.get_all_product_units_of_measure()
        self.assertEqual(len(units_after_deletes), 3)
        self.assertIn("KG", units_after_deletes)
        self.assertIn("Meter", units_after_deletes)
        self.assertIn("Liter", units_after_deletes)

        self.tearDown()
        self.setUp()
        no_units = self.logic.get_all_product_units_of_measure()
        self.assertEqual(len(no_units), 0)


if __name__ == '__main__':
    unittest.main()
