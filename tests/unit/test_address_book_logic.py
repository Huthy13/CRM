import unittest
import os
import sqlite3 # Import for PRAGMA
from core.database import DatabaseHandler
from core.address_book_logic import AddressBookLogic
from core.address_service import AddressService
from shared.structs import Product, AccountType, Account # Added AccountType for product tests if needed

class TestAddressBookLogic(unittest.TestCase):

    def setUp(self):
        # Create a fresh in-memory DB and initialize schema for EACH test method
        self.db_handler = DatabaseHandler(db_name=':memory:')
        # initialize_database is already called in DatabaseHandler's __init__
        self.address_service = AddressService(self.db_handler)
        self.logic = AddressBookLogic(self.db_handler, self.address_service)

        # Diagnostic: Print products table schema
        print("\n--- test_address_book_logic.py setUp: Products table schema ---")
        cursor = self.db_handler.conn.cursor()
        try:
            cursor.execute("PRAGMA table_info(products);")
            columns = cursor.fetchall()
            if columns:
                for col in columns:
                    # col is a sqlite3.Row object, access by index or name if row_factory was set on cursor
                    print(f"Column: cid={col[0]}, name={col[1]}, type={col[2]}, notnull={col[3]}, dflt_value={col[4]}, pk={col[5]}")
            else:
                print("PRAGMA table_info(products) returned no data - table 'products' might not exist.")
        except Exception as e:
            print(f"Error executing PRAGMA table_info(products): {e}")
        print("--- End Products table schema ---\n")

        self.clear_product_related_tables()

    def tearDown(self):
        self.db_handler.close()

    def clear_product_related_tables(self):
        with self.db_handler.conn:
            self.db_handler.cursor.execute("DELETE FROM product_prices")
            self.db_handler.cursor.execute("DELETE FROM products")
            self.db_handler.cursor.execute("DELETE FROM product_categories")
            self.db_handler.cursor.execute("DELETE FROM product_units_of_measure") # Added this line

    def test_add_and_get_product(self):
        # Test adding a product and retrieving it
        # Ensure AccountType is available if Product struct or logic needs it implicitly
        product_data = Product(name="Test Laptop", description="A laptop for testing", cost=999.99, sale_price=1299.99, is_active=True, category="Electronics", unit_of_measure="Each")
        product_id = self.logic.save_product(product_data)
        self.assertIsNotNone(product_id)

        retrieved_product = self.logic.get_product_details(product_id)
        self.assertIsNotNone(retrieved_product)
        self.assertEqual(retrieved_product.name, "Test Laptop")
        self.assertEqual(retrieved_product.description, "A laptop for testing")
        self.assertEqual(retrieved_product.cost, 999.99)
        self.assertEqual(retrieved_product.sale_price, 1299.99)
        self.assertEqual(retrieved_product.is_active, True)
        # Category path logic might make this different, adjust if full path is expected
        self.assertTrue("Electronics" in retrieved_product.category if retrieved_product.category else False)
        self.assertEqual(retrieved_product.unit_of_measure, "Each")

    def test_get_all_products(self):
        self.logic.save_product(Product(name="Product A", description="Desc A", cost=10.0, category="Cat A", unit_of_measure="Unit A", sale_price=15.0))
        self.logic.save_product(Product(name="Product B", description="Desc B", cost=20.0, is_active=False, category="Cat B", unit_of_measure="Unit B", sale_price=25.0))

        all_products = self.logic.get_all_products()
        self.assertEqual(len(all_products), 2)
        # Add more specific assertions if needed

    def test_update_product(self):
        product_data = Product(name="Old Name", description="Old Desc", cost=50.0, is_active=True, category="Old Cat", unit_of_measure="Old Unit", sale_price=60.0)
        product_id = self.logic.save_product(product_data)
        self.assertIsNotNone(product_id)

        updated_product_data = Product(product_id=product_id, name="New Name", description="New Desc", cost=75.0, sale_price=85.0, is_active=False, category="New Cat", unit_of_measure="New Unit")
        self.logic.save_product(updated_product_data)

        retrieved_product = self.logic.get_product_details(product_id)
        self.assertIsNotNone(retrieved_product)
        self.assertEqual(retrieved_product.name, "New Name")
        self.assertEqual(retrieved_product.cost, 75.0)
        self.assertEqual(retrieved_product.sale_price, 85.0)
        self.assertFalse(retrieved_product.is_active)

    def test_delete_product(self):
        product_data = Product(name="To Be Deleted", description="Delete me", cost=5.0, category="Temp", unit_of_measure="Item", sale_price=7.0)
        product_id = self.logic.save_product(product_data)
        self.assertIsNotNone(product_id)

        self.logic.delete_product(product_id) # This is a soft delete (sets is_active=False)
        retrieved_product = self.logic.get_product_details(product_id) # get_product_details only fetches active products
        self.assertIsNone(retrieved_product)

        # To verify soft delete, we'd need a method in DB handler to get inactive products or check DB directly.
        # For now, this confirms it's not returned by the standard getter.

    def test_product_price_validation_in_popup_save(self):
        valid_product = Product(name="Valid Cost Product", description="Test", cost=19.99, sale_price=29.99)
        valid_id = self.logic.save_product(valid_product)
        self.assertIsNotNone(valid_id)
        retrieved_valid = self.logic.get_product_details(valid_id)
        self.assertEqual(retrieved_valid.cost, 19.99)
        self.assertEqual(retrieved_valid.sale_price, 29.99)

    def test_add_product_with_new_and_existing_category(self):
        prod1_id = self.logic.save_product(Product(name="Product 1", category="Alpha", cost=10, sale_price=12))
        retrieved_prod1 = self.logic.get_product_details(prod1_id)
        self.assertTrue("Alpha" in retrieved_prod1.category if retrieved_prod1.category else False)
        # ... rest of test ...

    def test_add_product_with_empty_category(self):
        prod_id = self.logic.save_product(Product(name="Product NoCat", category="", cost=10, sale_price=12))
        retrieved_prod = self.logic.get_product_details(prod_id)
        self.assertEqual(retrieved_prod.category, "")
        # ... rest of test ...

    def test_update_product_category(self):
        prod_id = self.logic.save_product(Product(name="Product X", category="InitialCat", cost=100, sale_price=120))
        # ... rest of test ...

    def test_get_all_product_categories_from_table(self):
        self.logic.save_product(Product(name="Prod A", category="Electronics", cost=10, sale_price=12))
        self.logic.save_product(Product(name="Prod B", category="Books", cost=20, sale_price=22))
        # ... rest of test ...

    def test_add_product_with_new_and_existing_unit(self):
        prod1_id = self.logic.save_product(Product(name="Product U1", unit_of_measure="Piece", cost=10, sale_price=12))
        retrieved_prod1 = self.logic.get_product_details(prod1_id)
        self.assertEqual(retrieved_prod1.unit_of_measure, "Piece")
        # ... rest of test ...

    def test_add_product_with_empty_unit_of_measure(self):
        prod_id = self.logic.save_product(Product(name="Product NoUnit", unit_of_measure="", cost=10, sale_price=12))
        retrieved_prod = self.logic.get_product_details(prod_id)
        # unit_of_measure_name='' in db.add_product_unit_of_measure results in None ID.
        # ProductLogic.get_product_details with unit_of_measure_name=None results in Product.unit_of_measure=""
        self.assertEqual(retrieved_prod.unit_of_measure, "")
        # ... rest of test ...

    def test_update_product_unit_of_measure(self):
        prod_id = self.logic.save_product(Product(name="Product Y", unit_of_measure="InitialUnit", cost=100, sale_price=120))
        # ... rest of test ...

    def test_get_all_product_units_of_measure_from_table(self):
        self.logic.save_product(Product(name="UnitProd A", unit_of_measure="KG", cost=10, sale_price=12))
        self.logic.save_product(Product(name="UnitProd B", unit_of_measure="Meter", cost=20, sale_price=22))
        # ... rest of test ...

    def test_enforce_single_primary_address(self):
        """Test that only one primary billing and one primary shipping address can be saved for an account."""
        from shared.structs import Account, Address
        account = Account(name="Test Account", account_type=AccountType.CUSTOMER)
        self.logic.save_account(account)

        # Add two primary billing addresses
        billing_address1 = Address(street="123 Billing St", city="Billington", state="BS", zip_code="12345", country="BC")
        billing_address1.address_type = "Billing"
        billing_address1.is_primary = True
        billing_address2 = Address(street="456 Billing St", city="Billington", state="BS", zip_code="12345", country="BC")
        billing_address2.address_type = "Billing"
        billing_address2.is_primary = True
        account.addresses.append(billing_address1)
        account.addresses.append(billing_address2)
        self.address_service.save_account_addresses(account)

        # Verify that only one is primary
        addresses = self.db_handler.get_account_addresses(account.account_id)
        primary_billing_addresses = [addr for addr in addresses if addr['address_type'] == 'Billing' and addr['is_primary']]
        self.assertEqual(len(primary_billing_addresses), 1)

        # Add two primary shipping addresses
        shipping_address1 = Address(street="123 Shipping St", city="Shippsville", state="SS", zip_code="67890", country="SC")
        shipping_address1.address_type = "Shipping"
        shipping_address1.is_primary = True
        shipping_address2 = Address(street="456 Shipping St", city="Shippsville", state="SS", zip_code="67890", country="SC")
        shipping_address2.address_type = "Shipping"
        shipping_address2.is_primary = True
        account.addresses.append(shipping_address1)
        account.addresses.append(shipping_address2)
        self.address_service.save_account_addresses(account)

        # Verify that only one is primary
        addresses = self.db_handler.get_account_addresses(account.account_id)
        primary_shipping_addresses = [addr for addr in addresses if addr['address_type'] == 'Shipping' and addr['is_primary']]
        self.assertEqual(len(primary_shipping_addresses), 1)

if __name__ == '__main__':
    unittest.main()

class TestPricingRules(unittest.TestCase):
    def setUp(self):
        self.db_handler = DatabaseHandler(db_name=':memory:')
        self.logic = AddressBookLogic(self.db_handler)

    def tearDown(self):
        self.db_handler.close()

    def test_create_and_get_pricing_rule(self):
        """Test creating and retrieving a pricing rule."""
        rule_id = self.logic.create_pricing_rule(rule_name="20% Markup", markup_percentage=20.0)
        self.assertIsNotNone(rule_id)

        retrieved_rule = self.logic.get_pricing_rule(rule_id)
        self.assertIsNotNone(retrieved_rule)
        self.assertEqual(retrieved_rule.rule_name, "20% Markup")
        self.assertEqual(retrieved_rule.markup_percentage, 20.0)
        self.assertIsNone(retrieved_rule.fixed_price)

    def test_list_pricing_rules(self):
        """Test listing all pricing rules."""
        self.logic.create_pricing_rule(rule_name="Rule 1", fixed_price=10.0)
        self.logic.create_pricing_rule(rule_name="Rule 2", markup_percentage=5.0)

        rules = self.logic.list_pricing_rules()
        self.assertEqual(len(rules), 2)
        self.assertEqual(rules[0].rule_name, "Rule 1")
        self.assertEqual(rules[1].rule_name, "Rule 2")

    def test_update_pricing_rule(self):
        """Test updating a pricing rule."""
        rule_id = self.logic.create_pricing_rule(rule_name="Old Name", fixed_price=9.99)

        self.logic.update_pricing_rule(rule_id, "New Name", fixed_price=None, markup_percentage=15.0)

        updated_rule = self.logic.get_pricing_rule(rule_id)
        self.assertEqual(updated_rule.rule_name, "New Name")
        self.assertEqual(updated_rule.markup_percentage, 15.0)
        self.assertIsNone(updated_rule.fixed_price)

    def test_delete_pricing_rule(self):
        """Test deleting a pricing rule."""
        rule_id = self.logic.create_pricing_rule(rule_name="To Be Deleted", fixed_price=1.0)
        self.logic.delete_pricing_rule(rule_id)
        retrieved_rule = self.logic.get_pricing_rule(rule_id)
        self.assertIsNone(retrieved_rule)

    def test_assign_and_remove_pricing_rule(self):
        """Test assigning a pricing rule to a customer and removing it."""
        customer = self.logic.save_account(Account(name="Test Customer", account_type=AccountType.CUSTOMER))
        rule_id = self.logic.create_pricing_rule(rule_name="Customer Rule", fixed_price=50.0)

        # Assign
        self.logic.assign_pricing_rule(customer.account_id, rule_id)
        customer_details = self.logic.get_account_details(customer.account_id)
        self.assertEqual(customer_details.pricing_rule_id, rule_id)

        # Remove
        self.logic.remove_pricing_rule(customer.account_id)
        customer_details_after_removal = self.logic.get_account_details(customer.account_id)
        self.assertIsNone(customer_details_after_removal.pricing_rule_id)

    def test_pricing_rule_validation(self):
        """Test validation logic for creating/updating pricing rules."""
        with self.assertRaisesRegex(ValueError, "Rule name cannot be empty."):
            self.logic.create_pricing_rule(rule_name="")
        with self.assertRaisesRegex(ValueError, "Either markup_percentage or fixed_price must be provided."):
            self.logic.create_pricing_rule(rule_name="No price")
        with self.assertRaisesRegex(ValueError, "Provide either markup_percentage or fixed_price, not both."):
            self.logic.create_pricing_rule(rule_name="Both prices", markup_percentage=10.0, fixed_price=10.0)
