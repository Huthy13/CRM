import unittest
import os
import datetime
from core.database import DatabaseHandler
from core.address_book_logic import AddressBookLogic
from shared.structs import Interaction, InteractionType, Account, Contact, AccountType # Import AccountType

class TestAccountInteractions(unittest.TestCase): # Renamed class for clarity
    @classmethod
    def setUpClass(cls):
        cls.test_db_name = "test_interactions_app.db"
        # Ensure any old test DB is removed before starting
        if os.path.exists(cls.test_db_name):
            os.remove(cls.test_db_name)

        cls.db_handler = DatabaseHandler(db_name=cls.test_db_name)
        cls.logic = AddressBookLogic(cls.db_handler)

        # Setup a dummy account and contact for linking interactions
        cls.account1_id = cls.db_handler.add_account("Test Account 1", "1234567890", None, None, False, "test.com", "Desc", None) # Added None for account_type
        cls.contact1_id = cls.db_handler.add_contact("Test Contact 1", "0987654321", "contact@test.com", "Tester", cls.account1_id)
        cls.default_user_id = cls.db_handler.get_user_id_by_username('system_user')

    @classmethod
    def tearDownClass(cls):
        cls.db_handler.close()
        if os.path.exists(cls.test_db_name):
            os.remove(cls.test_db_name)

    def setUp(self):
        # Ensure each test starts with a clean slate for interactions
        self.db_handler.cursor.execute("DELETE FROM interactions")
        # Clear accounts and contacts tables as well for account type tests
        self.db_handler.cursor.execute("DELETE FROM contacts")
        self.db_handler.cursor.execute("DELETE FROM accounts")
        # Re-add default account and contact for interaction tests if needed by them
        # For simplicity, we'll re-initialize them here. Consider more granular setup if tests become slow.
        TestAccountInteractions.account1_id = self.db_handler.add_account("Test Account 1", "1234567890", None, None, False, "test.com", "Desc", None) # Add with None type initially
        TestAccountInteractions.contact1_id = self.db_handler.add_contact("Test Contact 1", "0987654321", "contact@test.com", "Tester", TestAccountInteractions.account1_id)


        self.db_handler.conn.commit()

        self.past_datetime = datetime.datetime.now() - datetime.timedelta(days=1)
        self.future_datetime = datetime.datetime.now() + datetime.timedelta(days=1)

    # Account Type Tests
    def test_save_and_get_account_with_type_customer(self):
        account = Account(
            name="Customer Account",
            phone="1112223333",
            website="customer.com",
            description="A test customer.",
            account_type=AccountType.CUSTOMER
        )
        self.logic.save_account(account) # save_account will set the ID on the object if it's new

        # Retrieve by name as ID is not directly returned by save_account in this setup
        # A more robust way would be if save_account returned the ID or the full object
        # For now, let's assume names are unique for this test or fetch all and filter.
        # The db_handler.add_account returns lastrowid, but logic.save_account doesn't directly.
        # Let's modify logic.save_account to set the ID on the passed object or return it.
        # For now, we'll fetch all and find.

        all_accounts = self.logic.get_all_accounts()
        found_account = None
        for acc in all_accounts:
            if acc.name == "Customer Account":
                found_account = acc
                break

        self.assertIsNotNone(found_account, "Failed to find the saved customer account.")
        self.assertIsNotNone(found_account.account_id, "Account ID should be set after saving.")

        retrieved_account = self.logic.get_account_details(found_account.account_id)
        self.assertIsNotNone(retrieved_account)
        self.assertEqual(retrieved_account.name, "Customer Account")
        self.assertEqual(retrieved_account.account_type, AccountType.CUSTOMER)

    def test_save_and_get_account_with_type_vendor(self):
        account = Account(
            name="Vendor Company",
            phone="4445556666",
            website="vendor.co",
            description="A test vendor.",
            account_type=AccountType.VENDOR
        )
        self.logic.save_account(account)

        all_accounts = self.logic.get_all_accounts()
        found_account = next((acc for acc in all_accounts if acc.name == "Vendor Company"), None)

        self.assertIsNotNone(found_account, "Failed to find the saved vendor account.")
        self.assertIsNotNone(found_account.account_id)

        retrieved_account = self.logic.get_account_details(found_account.account_id)
        self.assertIsNotNone(retrieved_account)
        self.assertEqual(retrieved_account.account_type, AccountType.VENDOR)

    def test_save_and_get_account_with_no_type(self):
        account = Account(
            name="Neutral Biz",
            phone="7778889999",
            description="No specific type."
            # account_type is None by default
        )
        self.logic.save_account(account)

        all_accounts = self.logic.get_all_accounts()
        found_account = next((acc for acc in all_accounts if acc.name == "Neutral Biz"), None)

        self.assertIsNotNone(found_account, "Failed to find the saved neutral account.")
        self.assertIsNotNone(found_account.account_id)

        retrieved_account = self.logic.get_account_details(found_account.account_id)
        self.assertIsNotNone(retrieved_account)
        self.assertIsNone(retrieved_account.account_type, "Account type should be None for neutral account.")

    def test_update_account_add_type(self):
        account = Account(name="Initially NoType Inc.", phone="123123")
        self.logic.save_account(account)

        all_accounts = self.logic.get_all_accounts()
        saved_account = next((acc for acc in all_accounts if acc.name == "Initially NoType Inc."), None)
        self.assertIsNotNone(saved_account)
        self.assertIsNone(saved_account.account_type)

        # Update with type
        saved_account.account_type = AccountType.CONTACT
        self.logic.save_account(saved_account) # save_account handles update if ID is present

        updated_account = self.logic.get_account_details(saved_account.account_id)
        self.assertIsNotNone(updated_account)
        self.assertEqual(updated_account.account_type, AccountType.CONTACT)

    def test_update_account_change_type(self):
        account = Account(name="TypeChanger Ltd.", phone="456456", account_type=AccountType.CUSTOMER)
        self.logic.save_account(account)

        all_accounts = self.logic.get_all_accounts()
        saved_account = next((acc for acc in all_accounts if acc.name == "TypeChanger Ltd."), None)
        self.assertIsNotNone(saved_account)
        self.assertEqual(saved_account.account_type, AccountType.CUSTOMER)

        # Update to Vendor
        saved_account.account_type = AccountType.VENDOR
        self.logic.save_account(saved_account)

        updated_account = self.logic.get_account_details(saved_account.account_id)
        self.assertIsNotNone(updated_account)
        self.assertEqual(updated_account.account_type, AccountType.VENDOR)

    def test_update_account_remove_type(self):
        account = Account(name="TypeRemover Co.", phone="789789", account_type=AccountType.VENDOR)
        self.logic.save_account(account)

        all_accounts = self.logic.get_all_accounts()
        saved_account = next((acc for acc in all_accounts if acc.name == "TypeRemover Co."), None)
        self.assertIsNotNone(saved_account)
        self.assertEqual(saved_account.account_type, AccountType.VENDOR)

        # Update to None
        saved_account.account_type = None
        self.logic.save_account(saved_account)

        updated_account = self.logic.get_account_details(saved_account.account_id)
        self.assertIsNotNone(updated_account)
        self.assertIsNone(updated_account.account_type)

    def test_get_all_accounts_includes_types(self):
        self.logic.save_account(Account(name="Cust1", phone="001", account_type=AccountType.CUSTOMER))
        self.logic.save_account(Account(name="Vend1", phone="002", account_type=AccountType.VENDOR))
        self.logic.save_account(Account(name="Cont1", phone="003", account_type=AccountType.CONTACT))
        self.logic.save_account(Account(name="NoType1", phone="004"))

        all_accounts = self.logic.get_all_accounts() # This should now return list of Account objects
        # Account for the default account created in setUp
        self.assertEqual(len(all_accounts), 5, "Should include the 4 test accounts + 1 from setUp")

        types_found = {acc.name: acc.account_type for acc in all_accounts}
        self.assertEqual(types_found["Cust1"], AccountType.CUSTOMER)
        self.assertEqual(types_found["Vend1"], AccountType.VENDOR)
        self.assertEqual(types_found["Cont1"], AccountType.CONTACT)
        self.assertIsNone(types_found["NoType1"])
        self.assertIsNone(types_found.get("Test Account 1"), "Default account from setUp should have None type")


    # Original Interaction Tests (ensure they still pass or adapt if necessary)
    def test_create_interaction_call_with_company(self):
        interaction = Interaction(
            company_id=self.account1_id,
            interaction_type=InteractionType.CALL,
            date_time=self.past_datetime,
            subject="Test Call Subject",
            description="Call description here.",
            created_by_user_id=self.default_user_id
        )
        interaction_id = self.logic.save_interaction(interaction)
        self.assertIsNotNone(interaction_id)

        retrieved = self.logic.get_interaction_details(interaction_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.subject, "Test Call Subject")
        self.assertEqual(retrieved.interaction_type, InteractionType.CALL)
        self.assertEqual(retrieved.company_id, self.account1_id)

    def test_create_interaction_email_with_contact(self):
        interaction = Interaction(
            contact_id=self.contact1_id,
            interaction_type=InteractionType.EMAIL,
            date_time=self.past_datetime,
            subject="Email Subject",
            description="Email body.",
            created_by_user_id=self.default_user_id
        )
        interaction_id = self.logic.save_interaction(interaction)
        self.assertIsNotNone(interaction_id)
        retrieved = self.logic.get_interaction_details(interaction_id)
        self.assertEqual(retrieved.interaction_type, InteractionType.EMAIL)
        self.assertEqual(retrieved.contact_id, self.contact1_id)

    def test_create_interaction_meeting_with_both(self):
        interaction = Interaction(
            company_id=self.account1_id,
            contact_id=self.contact1_id,
            interaction_type=InteractionType.MEETING,
            date_time=self.past_datetime,
            subject="Meeting about X",
            created_by_user_id=self.default_user_id
        )
        interaction_id = self.logic.save_interaction(interaction)
        self.assertIsNotNone(interaction_id)
        retrieved = self.logic.get_interaction_details(interaction_id)
        self.assertEqual(retrieved.interaction_type, InteractionType.MEETING)
        self.assertEqual(retrieved.company_id, self.account1_id)
        self.assertEqual(retrieved.contact_id, self.contact1_id)

    def test_reject_future_date(self):
        interaction = Interaction(
            company_id=self.account1_id,
            interaction_type=InteractionType.VISIT,
            date_time=self.future_datetime,
            subject="Future Visit",
            created_by_user_id=self.default_user_id
        )
        with self.assertRaisesRegex(ValueError, "Interaction date and time cannot be in the future."):
            self.logic.save_interaction(interaction)

    def test_reject_missing_subject(self):
        interaction = Interaction(
            company_id=self.account1_id,
            interaction_type=InteractionType.OTHER,
            date_time=self.past_datetime,
            subject="", # Empty subject
            created_by_user_id=self.default_user_id
        )
        with self.assertRaisesRegex(ValueError, "Interaction subject cannot be empty."):
            self.logic.save_interaction(interaction)

    def test_reject_long_subject(self):
        long_subject = "s" * 151
        interaction = Interaction(
            company_id=self.account1_id,
            interaction_type=InteractionType.OTHER,
            date_time=self.past_datetime,
            subject=long_subject,
            created_by_user_id=self.default_user_id
        )
        with self.assertRaisesRegex(ValueError, "Interaction subject cannot exceed 150 characters."):
            self.logic.save_interaction(interaction)

    def test_reject_invalid_interaction_type_value(self):
        interaction = Interaction(
            company_id=self.account1_id,
            interaction_type="INVALID_TYPE_STRING", # Invalid string
            date_time=self.past_datetime,
            subject="Test Subject",
            created_by_user_id=self.default_user_id
        )
        with self.assertRaisesRegex(ValueError, "Invalid interaction type string: 'INVALID_TYPE_STRING'."):
            self.logic.save_interaction(interaction)

    def test_reject_invalid_interaction_type_object(self):
        interaction = Interaction(
            company_id=self.account1_id,
            interaction_type=object(), # Not an enum or valid string
            date_time=self.past_datetime,
            subject="Test Subject",
            created_by_user_id=self.default_user_id
        )
        with self.assertRaisesRegex(ValueError, "Invalid interaction type. Must be an InteractionType enum."):
            self.logic.save_interaction(interaction)


    def test_reject_missing_company_and_contact(self):
        interaction = Interaction(
            interaction_type=InteractionType.CALL,
            date_time=self.past_datetime,
            subject="No Link",
            created_by_user_id=self.default_user_id
        )
        with self.assertRaisesRegex(ValueError, "Interaction must be associated with a company or a contact."):
            self.logic.save_interaction(interaction)

    def test_update_interaction(self):
        interaction = Interaction(
            company_id=self.account1_id,
            interaction_type=InteractionType.CALL,
            date_time=self.past_datetime,
            subject="Initial Subject",
            created_by_user_id=self.default_user_id
        )
        interaction_id = self.logic.save_interaction(interaction)
        self.assertIsNotNone(interaction_id)

        # Update
        interaction.interaction_id = interaction_id # Set ID for update
        interaction.subject = "Updated Subject"
        interaction.interaction_type = InteractionType.EMAIL
        updated_id = self.logic.save_interaction(interaction)
        self.assertEqual(interaction_id, updated_id)

        retrieved = self.logic.get_interaction_details(interaction_id)
        self.assertEqual(retrieved.subject, "Updated Subject")
        self.assertEqual(retrieved.interaction_type, InteractionType.EMAIL)


    def test_delete_interaction(self):
        interaction = Interaction(
            contact_id=self.contact1_id,
            interaction_type=InteractionType.VISIT,
            date_time=self.past_datetime,
            subject="To Be Deleted",
            created_by_user_id=self.default_user_id
        )
        interaction_id = self.logic.save_interaction(interaction)
        self.assertIsNotNone(interaction_id)

        self.logic.delete_interaction(interaction_id)
        retrieved = self.logic.get_interaction_details(interaction_id)
        self.assertIsNone(retrieved)

    def test_get_all_interactions_unfiltered(self):
        self.logic.save_interaction(Interaction(company_id=self.account1_id, interaction_type=InteractionType.CALL, date_time=self.past_datetime, subject="Call 1", created_by_user_id=self.default_user_id))
        self.logic.save_interaction(Interaction(contact_id=self.contact1_id, interaction_type=InteractionType.EMAIL, date_time=self.past_datetime, subject="Email 1", created_by_user_id=self.default_user_id))

        all_interactions = self.logic.get_all_interactions()
        self.assertEqual(len(all_interactions), 2)

    def test_get_interactions_by_company_id(self):
        # Account 2 for filtering
        account2_id = self.db_handler.add_account("Filter Account", "111222333", None, None, False, "filter.com", "Desc", None) # Added None for account_type

        self.logic.save_interaction(Interaction(company_id=self.account1_id, interaction_type=InteractionType.CALL, date_time=self.past_datetime, subject="Call A1", created_by_user_id=self.default_user_id))
        self.logic.save_interaction(Interaction(company_id=account2_id, interaction_type=InteractionType.MEETING, date_time=self.past_datetime, subject="Meeting A2", created_by_user_id=self.default_user_id))

        company1_interactions = self.logic.get_all_interactions(company_id=self.account1_id)
        self.assertEqual(len(company1_interactions), 1)
        self.assertEqual(company1_interactions[0].subject, "Call A1")

    def test_get_interactions_by_contact_id(self):
         # Contact 2 for filtering
        contact2_id = self.db_handler.add_contact("Filter Contact", "222333444", "filter@con.com", "FilterRole", None)

        self.logic.save_interaction(Interaction(contact_id=self.contact1_id, interaction_type=InteractionType.EMAIL, date_time=self.past_datetime, subject="Email C1", created_by_user_id=self.default_user_id))
        self.logic.save_interaction(Interaction(contact_id=contact2_id, interaction_type=InteractionType.VISIT, date_time=self.past_datetime, subject="Visit C2", created_by_user_id=self.default_user_id))

        contact1_interactions = self.logic.get_all_interactions(contact_id=self.contact1_id)
        self.assertEqual(len(contact1_interactions), 1)
        self.assertEqual(contact1_interactions[0].subject, "Email C1")

    def test_delete_account_cascades_to_interactions(self):
        # Create a new account and an interaction linked to it
        temp_account_id = self.db_handler.add_account("Temp Account", "555555", None, None, False, "temp.com", "Temp Desc", None) # Added None for account_type
        interaction = Interaction(
            company_id=temp_account_id,
            interaction_type=InteractionType.CALL,
            date_time=self.past_datetime,
            subject="Interaction for Temp Account",
            created_by_user_id=self.default_user_id
        )
        interaction_id = self.logic.save_interaction(interaction)
        self.assertIsNotNone(interaction_id)

        # Delete the account
        self.logic.delete_account(temp_account_id) # This uses logic.delete_account

        # Verify the interaction's company_id is now NULL
        retrieved_interaction = self.logic.get_interaction_details(interaction_id)
        self.assertIsNotNone(retrieved_interaction, "Interaction should still exist.")
        self.assertIsNone(retrieved_interaction.company_id, "Interaction's company_id should be NULL after account deletion.")
        self.assertEqual(retrieved_interaction.subject, "Interaction for Temp Account")


    def test_delete_contact_cascades_to_interactions(self):
        # Create a new contact and an interaction linked to it
        temp_contact_id = self.db_handler.add_contact("Temp Contact", "666666", "temp@contact.com", "TempRole", self.account1_id)
        interaction = Interaction(
            contact_id=temp_contact_id,
            interaction_type=InteractionType.EMAIL,
            date_time=self.past_datetime,
            subject="Interaction for Temp Contact",
            created_by_user_id=self.default_user_id
        )
        interaction_id = self.logic.save_interaction(interaction)
        self.assertIsNotNone(interaction_id)

        # Delete the contact
        self.logic.delete_contact(temp_contact_id) # This uses logic.delete_contact

        # Verify the interaction's contact_id is now NULL
        retrieved_interaction = self.logic.get_interaction_details(interaction_id)
        self.assertIsNotNone(retrieved_interaction, "Interaction should still exist.")
        self.assertIsNone(retrieved_interaction.contact_id, "Interaction's contact_id should be NULL after contact deletion.")
        self.assertEqual(retrieved_interaction.subject, "Interaction for Temp Contact")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
