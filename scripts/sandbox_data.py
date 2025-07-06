import os
import sys

# Add project root to sys.path to allow imports from core and shared
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Go up one more level
sys.path.insert(0, project_root)

from core.database import DatabaseHandler
from core.logic import AddressBookLogic
from shared.structs import Account, Contact, Address

def populate_data():
    """
    Populates the database with sample accounts and contacts.
    """
    print("Connecting to the database...")
    # Uses the default database_name="address_book.db" in the core directory
    db_handler = DatabaseHandler()
    logic = AddressBookLogic(db_handler)
    print("Database connected.")

    # Placeholder for adding accounts and contacts
    print("Starting data population...")

    # Add 10 Accounts
    for i in range(1, 11):
        print(f"Adding Account {i}...")
        # Create unique addresses for each account
        billing_street = f"{i*10} Billing St"
        billing_city = f"Billtown{i}"
        billing_state = "BS"
        billing_zip = f"B{i:05}"
        billing_country = "BCN"
        billing_address_id = logic.add_address(billing_street, billing_city, billing_state, billing_zip, billing_country)

        shipping_street = f"{i*10} Shipping Ave"
        shipping_city = f"Shipton{i}"
        shipping_state = "SS"
        shipping_zip = f"S{i:05}"
        shipping_country = "SCN"
        shipping_address_id = logic.add_address(shipping_street, shipping_city, shipping_state, shipping_zip, shipping_country)

        account = Account(
            name=f"Test Account {i:02}",
            phone=f"555-01{i:02}",
            billing_address_id=billing_address_id,
            shipping_address_id=shipping_address_id,
            website=f"http://testaccount{i}.com",
            description=f"This is test account number {i}."
        )
        logic.save_account(account)
        print(f"Account '{account.name}' added.")

    # Add 10 Contacts, associating them with the accounts created
    # We need to get the account IDs first.
    # This assumes get_accounts() returns a list of (id, name) tuples.
    # And that they are returned in the order they were inserted (or we can fetch by name).
    # For simplicity, we'll assume the first 10 accounts are the ones we just added.
    # A more robust way would be to get accounts by name or store IDs when creating.

    all_accounts_tuples = logic.get_accounts() # Get (id, name)
    if len(all_accounts_tuples) < 10:
        print("Error: Less than 10 accounts found. Cannot add all contacts as planned.")
        # Filter for accounts named "Test Account XX"
        test_accounts_tuples = [acc for acc in all_accounts_tuples if acc[1].startswith("Test Account")]
    else:
        # If we have many accounts, let's try to pick the ones we just added.
        test_accounts_tuples = [acc for acc in all_accounts_tuples if acc[1].startswith("Test Account")]
        if len(test_accounts_tuples) < 10:
             print(f"Warning: Found {len(test_accounts_tuples)} accounts starting with 'Test Account'. Will use these.")
        # If there are more than 10 "Test Account XX", just take the first 10 found (IDs might not match 1-10)
        # This part can be made more robust if save_account returned the ID.
        # For now, we'll proceed, hoping the naming convention is unique enough for this script.


    for i in range(1, 11):
        if i > len(test_accounts_tuples):
            print(f"Not enough accounts to create contact {i}. Stopping contact creation.")
            break

        # Cycle through accounts for contacts if fewer than 10 test accounts were found
        account_tuple_for_contact = test_accounts_tuples[(i-1) % len(test_accounts_tuples)]
        account_id_for_contact = account_tuple_for_contact[0]
        account_name_for_contact = account_tuple_for_contact[1] # For logging

        print(f"Adding Contact {i} for account '{account_name_for_contact}' (ID: {account_id_for_contact})...")
        contact = Contact(
            name=f"Contact Person {i:02}",
            phone=f"555-02{i:02}",
            email=f"contact{i}@testaccount.com",
            role=f"Role {i}",
            account_id=account_id_for_contact
        )
        contact_id = logic.save_contact(contact)
        if contact_id:
            print(f"Contact '{contact.name}' added with ID {contact_id} to account '{account_name_for_contact}'.")
        else:
            print(f"Failed to add contact '{contact.name}'.")


    print("Data population script finished.")
    db_handler.close()
    print("Database connection closed.")

if __name__ == "__main__":
    # Check if the database file already exists. If so, ask the user if they want to proceed.
    # This is a simple check. For a real app, you might want to check if it's empty or has specific tables.
    db_file_path = os.path.join(project_root, "core", "address_book.db")
    if os.path.exists(db_file_path):
        user_response = input(f"Database file '{db_file_path}' already exists. "
                              "Running this script will add more data, potentially creating duplicates "
                              "if names are not unique or if you run it multiple times. "
                              "Continue? (yes/no): ").lower()
        if user_response not in ['yes', 'y']:
            print("Operation cancelled by user.")
            sys.exit(0)
    populate_data()
