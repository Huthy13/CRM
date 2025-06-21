import unittest
import sqlite3 # Using sqlite3 for in-memory database for testing
from core.logic import AddressBookLogic
from core.database import DatabaseHandler # Assuming this is your DB handler class
from shared.structs import Account, Contact, Address

class TestLogic(unittest.TestCase):

    def setUp(self):
        """Set up an in-memory SQLite database for each test."""
        self.conn = sqlite3.connect(':memory:')
        # The DatabaseHandler now takes the db_name (or path) directly.
        # It also calls create_tables() in its __init__.
        self.db_handler = DatabaseHandler(db_name=':memory:')
        # Ensure the logic layer uses this specific db_handler instance.
        self.logic = AddressBookLogic(self.db_handler)
        # It's also good practice to ensure the db_handler in logic
        # uses the same connection if it were to be managed separately,
        # but since DatabaseHandler(':memory:') creates its own in-memory db,
        # and logic uses the passed db_handler, this should be fine.
        # If logic.py created its own db_handler, we'd have an issue.
        # self.db_handler.conn = self.conn # This line might be redundant if db_handler(':memory:') works as expected

    def tearDown(self):
        """Close the database connection after each test."""
        self.conn.close()

    def test_add_and_get_address(self):
        """Test adding and retrieving an address."""
        address_id = self.logic.add_address("123 Main St", "Anytown", "CA", "90210", "USA")
        self.assertIsNotNone(address_id, "Address ID should not be None")

        address_obj = self.logic.get_address_obj(address_id)
        self.assertIsNotNone(address_obj, "Address object should not be None")
        self.assertEqual(address_obj.street, "123 Main St")
        self.assertEqual(address_obj.city, "Anytown")
        self.assertEqual(address_obj.state, "CA")
        self.assertEqual(address_obj.zip_code, "90210")
        self.assertEqual(address_obj.country, "USA")

    def test_update_address(self):
        """Test updating an address."""
        address_id = self.logic.add_address("456 Oak Ave", "Otherville", "NY", "10001", "USA")
        self.logic.update_address(address_id, "789 Pine Ln", "New City", "TX", "75001", "USA")

        address_obj = self.logic.get_address_obj(address_id)
        self.assertEqual(address_obj.street, "789 Pine Ln")
        self.assertEqual(address_obj.city, "New City")
        self.assertEqual(address_obj.state, "TX")
        self.assertEqual(address_obj.zip_code, "75001")

    def test_save_and_get_account(self):
        """Test saving (add/update) and retrieving an account."""
        # Add billing and shipping addresses first
        billing_address_id = self.logic.add_address("1 Billing Rd", "Billville", "BS", "B1B1B1", "BC")
        shipping_address_id = self.logic.add_address("1 Shipping Wy", "Shipburg", "SS", "S1S1S1", "SC")

        # Test adding a new account
        new_account = Account(
            name="Test Account Inc.",
            phone="123-456-7890",
            billing_address_id=billing_address_id,
            shipping_address_id=shipping_address_id,
            website="http://testaccount.com",
            description="A test account"
        )
        # The save_account in logic should handle the db interaction and return the ID
        # For now, we assume save_account doesn't directly return the ID,
        # so we'll retrieve it to confirm.
        self.logic.save_account(new_account)
        # We need a way to get the last inserted ID or get account by name for verification
        # Assuming get_accounts() returns (id, name) tuples and there's only one account
        accounts = self.logic.get_accounts()
        self.assertEqual(len(accounts), 1)
        account_id_from_db, account_name_from_db = accounts[0]
        self.assertEqual(account_name_from_db, "Test Account Inc.")

        retrieved_account = self.logic.get_account_details(account_id_from_db)
        self.assertIsNotNone(retrieved_account)
        self.assertEqual(retrieved_account.name, "Test Account Inc.")
        self.assertEqual(retrieved_account.phone, "123-456-7890")
        self.assertEqual(retrieved_account.billing_address_id, billing_address_id)
        self.assertEqual(retrieved_account.shipping_address_id, shipping_address_id)
        self.assertEqual(retrieved_account.website, "http://testaccount.com")
        self.assertEqual(retrieved_account.description, "A test account")

        # Test updating an existing account
        retrieved_account.name = "Updated Test Account LLC"
        retrieved_account.phone = "987-654-3210"
        self.logic.save_account(retrieved_account) # save_account should detect existing ID and update

        updated_account = self.logic.get_account_details(account_id_from_db)
        self.assertEqual(updated_account.name, "Updated Test Account LLC")
        self.assertEqual(updated_account.phone, "987-654-3210")

    def test_delete_account(self):
        """Test deleting an account."""
        billing_address_id = self.logic.add_address("1 Delete Rd", "Delville", "DS", "D1D1D1", "DC")
        new_account = Account(name="To Be Deleted", phone="1112223333", billing_address_id=billing_address_id)
        self.logic.save_account(new_account)
        # Get the ID of the newly created account
        accounts = self.logic.get_accounts()
        account_id_to_delete = accounts[0][0]

        self.logic.delete_account(account_id_to_delete)
        deleted_account = self.logic.get_account_details(account_id_to_delete)
        self.assertIsNone(deleted_account, "Account should be None after deletion")
        # Also verify associated contacts are deleted (once contact tests are in place)

    def test_save_and_get_contact(self):
        """Test saving (add/update) and retrieving a contact."""
        # First, create an account for the contact
        billing_address_id = self.logic.add_address("Acc Main St", "Acc City", "AS", "A1A1A1", "AC")
        account = Account(name="Contact's Account", phone="555-0000", billing_address_id=billing_address_id)
        self.logic.save_account(account)
        accounts = self.logic.get_accounts()
        account_id = accounts[0][0] # Get the ID of the created account

        # Test adding a new contact
        new_contact = Contact(
            name="John Doe",
            phone="555-1234",
            email="john.doe@example.com",
            role="Tester",
            account_id=account_id
        )
        contact_id = self.logic.save_contact(new_contact)
        self.assertIsNotNone(contact_id, "Contact ID should not be None after saving")
        new_contact.contact_id = contact_id # Set the ID on the object

        retrieved_contact = self.logic.get_contact_details(contact_id)
        self.assertIsNotNone(retrieved_contact)
        self.assertEqual(retrieved_contact.name, "John Doe")
        self.assertEqual(retrieved_contact.email, "john.doe@example.com")
        self.assertEqual(retrieved_contact.role, "Tester")
        self.assertEqual(retrieved_contact.account_id, account_id)

        # Test updating an existing contact
        retrieved_contact.name = "Jane Doe"
        retrieved_contact.email = "jane.doe@example.com"
        updated_contact_id = self.logic.save_contact(retrieved_contact) # save_contact should detect existing ID
        self.assertEqual(updated_contact_id, contact_id) # ID should remain the same

        updated_contact_details = self.logic.get_contact_details(contact_id)
        self.assertEqual(updated_contact_details.name, "Jane Doe")
        self.assertEqual(updated_contact_details.email, "jane.doe@example.com")

    def test_get_contacts_by_account(self):
        """Test retrieving contacts associated with a specific account."""
        # Account 1
        b_addr1_id = self.logic.add_address("Acc1 St", "City1", "S1", "11111", "C1")
        acc1 = Account(name="Account One", phone="111-1111", billing_address_id=b_addr1_id)
        self.logic.save_account(acc1)
        acc1_id = self.logic.get_accounts()[0][0]

        # Account 2
        b_addr2_id = self.logic.add_address("Acc2 St", "City2", "S2", "22222", "C2")
        acc2 = Account(name="Account Two", phone="222-2222", billing_address_id=b_addr2_id)
        self.logic.save_account(acc2)
        acc2_id = self.logic.get_accounts()[1][0]


        # Contacts for Account 1
        self.logic.save_contact(Contact(name="Contact A", phone="A1", email="a@1.com", role="Dev", account_id=acc1_id))
        self.logic.save_contact(Contact(name="Contact B", phone="B1", email="b@1.com", role="PM", account_id=acc1_id))

        # Contact for Account 2
        self.logic.save_contact(Contact(name="Contact C", phone="C2", email="c@2.com", role="QA", account_id=acc2_id))

        contacts_acc1 = self.logic.get_contacts_by_account(acc1_id)
        self.assertEqual(len(contacts_acc1), 2)
        self.assertTrue(any(c.name == "Contact A" for c in contacts_acc1))
        self.assertTrue(any(c.name == "Contact B" for c in contacts_acc1))

        contacts_acc2 = self.logic.get_contacts_by_account(acc2_id)
        self.assertEqual(len(contacts_acc2), 1)
        self.assertEqual(contacts_acc2[0].name, "Contact C")

    def test_get_all_contacts(self):
        """Test retrieving all contacts."""
        b_addr1_id = self.logic.add_address("All1 St", "CityA1", "SA1", "A1111", "CA1")
        acc1 = Account(name="Global Corp", phone="100-1000", billing_address_id=b_addr1_id)
        self.logic.save_account(acc1)
        acc1_id = self.logic.get_accounts()[0][0]

        b_addr2_id = self.logic.add_address("All2 St", "CityA2", "SA2", "A2222", "CA2")
        acc2 = Account(name="Local LLC", phone="200-2000", billing_address_id=b_addr2_id)
        self.logic.save_account(acc2)
        acc2_id = self.logic.get_accounts()[1][0]

        self.logic.save_contact(Contact(name="Alpha", phone="001", email="alpha@g.com", role="Lead", account_id=acc1_id))
        self.logic.save_contact(Contact(name="Beta", phone="002", email="beta@l.com", role="Support", account_id=acc2_id))
        self.logic.save_contact(Contact(name="Gamma", phone="003", email="gamma@g.com", role="Intern", account_id=acc1_id))

        all_contacts = self.logic.get_all_contacts()
        self.assertEqual(len(all_contacts), 3)
        contact_names = [c.name for c in all_contacts]
        self.assertIn("Alpha", contact_names)
        self.assertIn("Beta", contact_names)
        self.assertIn("Gamma", contact_names)

    def test_delete_contact(self):
        """Test deleting a contact."""
        b_addr_id = self.logic.add_address("DelCon St", "DelCon City", "DS", "DCS01", "DC")
        account = Account(name="Contact Delete Account", phone="555-9999", billing_address_id=b_addr_id)
        self.logic.save_account(account)
        account_id = self.logic.get_accounts()[0][0]

        contact_to_delete_id = self.logic.save_contact(
            Contact(name="Delete Me", phone="000-0000", email="del@me.com", role="Temp", account_id=account_id)
        )
        self.assertIsNotNone(contact_to_delete_id)

        self.logic.delete_contact(contact_to_delete_id)
        deleted_contact_details = self.logic.get_contact_details(contact_to_delete_id)
        self.assertIsNone(deleted_contact_details, "Contact should be None after deletion")

        # Ensure other contacts are not affected (if any)
        other_contact_id = self.logic.save_contact(
            Contact(name="Still Here", phone="111-1111", email="still@here.com", role="Perm", account_id=account_id)
        )
        still_here_details = self.logic.get_contact_details(other_contact_id)
        self.assertIsNotNone(still_here_details)

if __name__ == '__main__':
    unittest.main()
