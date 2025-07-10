import unittest
import tkinter as tk
import os
from core.database import DatabaseHandler
from shared.structs import CompanyInformation, Address
from ui.company_info_tab import CompanyInfoTab

# Define a consistent test database name
TEST_DB_NAME = "test_crm_app_company_info.db"

class TestCompanyInfo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up a temporary database for all tests in this class."""
        # Ensure we're using a test-specific database
        cls.db_handler = DatabaseHandler(db_name=TEST_DB_NAME)
        # Ensure tables are created
        cls.db_handler.create_tables()

    @classmethod
    def tearDownClass(cls):
        """Close the database connection and remove the test database file."""
        cls.db_handler.close()
        try:
            os.remove(TEST_DB_NAME)
        except OSError as e:
            print(f"Error removing test database {TEST_DB_NAME}: {e}")

    def setUp(self):
        """Clean up and reset database before each test."""
        # Clear relevant tables before each test to ensure isolation
        self.db_handler.cursor.execute("DELETE FROM company_information")
        self.db_handler.cursor.execute("DELETE FROM addresses")
        self.db_handler.conn.commit()

        # Add a default company info record for tests that might expect one
        # This matches the logic in CompanyInfoTab that adds one if none exists
        self.db_handler.add_company_information("Default Test Company", "123-456-7890", None, None)


        # Setup Tkinter root for UI tests (if directly testing UI components)
        # Attempt to create a root window only if a display is available
        try:
            self.root = tk.Tk()
            # self.root.withdraw() # Hide the main window during tests if it's created
        except tk.TclError as e:
            if "no display name" in str(e):
                print("Skipping Tkinter root creation due to no display.")
                self.root = None
            else:
                raise # Reraise if it's a different TclError

    def tearDown(self):
        """Destroy Tkinter root after each test, if it was created."""
        if self.root:
            self.root.destroy()


    def test_01_add_and_get_company_information(self):
        """Test adding and retrieving company information from the database."""
        # Clear any default entry first if a specific one is being tested for add.
        self.db_handler.cursor.execute("DELETE FROM company_information")
        self.db_handler.conn.commit()

        test_name = "Test Corp"
        test_phone = "555-0101"
        billing_addr_id = self.db_handler.add_address("123 Billing St", "Billville", "BS", "B1B1B1", "BCountry")
        shipping_addr_id = self.db_handler.add_address("456 Shipping Rd", "Shipburg", "SS", "S1S1S1", "SCountry")

        company_id = self.db_handler.add_company_information(test_name, test_phone, billing_addr_id, shipping_addr_id)
        self.assertIsNotNone(company_id, "Adding company info should return an ID.")

        retrieved_info_dict = self.db_handler.get_company_information()
        self.assertIsNotNone(retrieved_info_dict, "Should retrieve company information.")
        self.assertEqual(retrieved_info_dict['name'], test_name)
        self.assertEqual(retrieved_info_dict['phone'], test_phone)
        self.assertEqual(retrieved_info_dict['billing_address_id'], billing_addr_id)
        self.assertEqual(retrieved_info_dict['shipping_address_id'], shipping_addr_id)
        self.assertEqual(retrieved_info_dict['billing_street'], "123 Billing St")
        self.assertEqual(retrieved_info_dict['shipping_city'], "Shipburg")


    def test_02_update_company_information(self):
        """Test updating existing company information in the database."""
        original_info = self.db_handler.get_company_information()
        self.assertIsNotNone(original_info, "Prerequisite: Default company info should exist.")
        company_id_to_update = original_info['company_id']

        new_name = "Updated Test Corp"
        new_phone = "555-0202"
        new_billing_addr_id = self.db_handler.add_address("789 New Bill St", "NewBillVille", "NB", "NB1NB1", "NBCountry")

        self.db_handler.update_company_information(company_id_to_update, new_name, new_phone, new_billing_addr_id, None)

        updated_info = self.db_handler.get_company_information() # Fetches the first/only one
        self.assertEqual(updated_info['name'], new_name)
        self.assertEqual(updated_info['phone'], new_phone)
        self.assertEqual(updated_info['billing_address_id'], new_billing_addr_id)
        self.assertIsNone(updated_info['shipping_address_id'], "Shipping address ID should be None after update.")
        self.assertEqual(updated_info['billing_street'], "789 New Bill St")


    def test_03_company_info_tab_load_data(self):
        """Test that CompanyInfoTab loads data correctly."""
        if not self.root:
            self.skipTest("Tkinter root not available, skipping UI-dependent test.")
        # Ensure there's data to load
        test_name = "Tab Load Test Co"
        phone = "111-222-3333"
        b_addr_id = self.db_handler.add_address("1 Main St", "LoadCity", "LC", "L1L1L1", "LCountry")

        # Clear existing and add specific for this test
        self.db_handler.cursor.execute("DELETE FROM company_information")
        self.db_handler.add_company_information(test_name, phone, b_addr_id, None)
        self.db_handler.conn.commit()

        tab = CompanyInfoTab(self.root, self.db_handler)
        tab.load_company_data() # Explicitly call load

        self.assertIsNotNone(tab.company_info, "CompanyInfo object should be loaded.")
        self.assertEqual(tab.company_info.name, test_name)
        self.assertEqual(tab.company_info.phone, phone)
        self.assertEqual(tab.company_info.billing_address_id, b_addr_id)

        self.assertIsNotNone(tab.billing_address, "Billing Address object should be loaded.")
        self.assertEqual(tab.billing_address.street, "1 Main St")
        self.assertEqual(tab.billing_address.city, "LoadCity")


    def test_04_company_info_tab_save_data_new_addresses(self):
        """Test CompanyInfoTab saving data with new addresses."""
        if not self.root:
            self.skipTest("Tkinter root not available, skipping UI-dependent test.")
        tab = CompanyInfoTab(self.root, self.db_handler) # This will load or create default

        # Simulate user input
        tab.name_entry.insert(0, "Save Test Inc.")
        tab.phone_entry.insert(0, "999-888-7777")
        tab.billing_street_entry.insert(0, "123 Save St")
        tab.billing_city_entry.insert(0, "Saveville")
        tab.billing_state_entry.insert(0, "SV")
        tab.billing_zip_entry.insert(0, "SVSVSV")
        tab.billing_country_entry.insert(0, "SCountry")

        tab.same_as_billing_var.set(False) # Ensure shipping is different
        tab.toggle_shipping_fields() # Enable shipping fields

        tab.shipping_street_entry.insert(0, "456 ShipSave Ave")
        tab.shipping_city_entry.insert(0, "Shipton")
        tab.shipping_state_entry.insert(0, "SH")
        tab.shipping_zip_entry.insert(0, "SHSHSH")
        tab.shipping_country_entry.insert(0, "SCountry")

        tab.save_company_information()

        # Verify database
        saved_info = self.db_handler.get_company_information()
        self.assertEqual(saved_info['name'], "Save Test Inc.")
        self.assertEqual(saved_info['phone'], "999-888-7777")
        self.assertIsNotNone(saved_info['billing_address_id'])
        self.assertIsNotNone(saved_info['shipping_address_id'])
        self.assertNotEqual(saved_info['billing_address_id'], saved_info['shipping_address_id'])

        self.assertEqual(saved_info['billing_street'], "123 Save St")
        self.assertEqual(saved_info['billing_city'], "Saveville")
        self.assertEqual(saved_info['shipping_street'], "456 ShipSave Ave")
        self.assertEqual(saved_info['shipping_city'], "Shipton")


    def test_05_company_info_tab_save_data_same_address(self):
        """Test CompanyInfoTab saving data when shipping is same as billing."""
        if not self.root:
            self.skipTest("Tkinter root not available, skipping UI-dependent test.")
        tab = CompanyInfoTab(self.root, self.db_handler)

        tab.name_entry.insert(0, "SameAddress Co.")
        tab.phone_entry.insert(0, "777-666-5555")
        tab.billing_street_entry.insert(0, "789 Same St")
        tab.billing_city_entry.insert(0, "SameCity")
        tab.billing_state_entry.insert(0, "SA")
        tab.billing_zip_entry.insert(0, "SASASA")
        tab.billing_country_entry.insert(0, "SCountry")

        tab.same_as_billing_var.set(True)
        tab.toggle_shipping_fields() # This will copy billing to shipping and disable shipping fields

        tab.save_company_information()

        saved_info = self.db_handler.get_company_information()
        self.assertEqual(saved_info['name'], "SameAddress Co.")
        self.assertEqual(saved_info['billing_street'], "789 Same St")
        self.assertIsNotNone(saved_info['billing_address_id'])
        self.assertEqual(saved_info['billing_address_id'], saved_info['shipping_address_id'])
        # Check if shipping address details in DB match billing (since they point to the same ID)
        self.assertEqual(saved_info['shipping_street'], "789 Same St")
        self.assertEqual(saved_info['shipping_city'], "SameCity")

    def test_06_company_info_tab_initial_load_no_data(self):
        """Test CompanyInfoTab initial load when no company data exists in DB."""
        if not self.root:
            self.skipTest("Tkinter root not available, skipping UI-dependent test.")
        # Ensure DB is empty for this specific test condition
        self.db_handler.cursor.execute("DELETE FROM company_information")
        self.db_handler.cursor.execute("DELETE FROM addresses")
        self.db_handler.conn.commit()

        tab = CompanyInfoTab(self.root, self.db_handler) # Should create a default entry

        self.assertIsNotNone(tab.company_info, "CompanyInfo should be initialized.")
        self.assertEqual(tab.company_info.name, "My Company", "Default name should be set.")
        self.assertIsNotNone(tab.company_info.company_id, "Default company should get an ID after save.")

        # Verify a default record was added to the DB
        db_entry = self.db_handler.get_company_information()
        self.assertIsNotNone(db_entry)
        self.assertEqual(db_entry['name'], "My Company")

if __name__ == '__main__':
    unittest.main(verbosity=2)
