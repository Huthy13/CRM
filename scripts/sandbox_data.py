import os
import sys

# Add project root to sys.path to allow imports from core and shared
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Go up one more level
sys.path.insert(0, project_root)

from core.database import DatabaseHandler
from core.address_book_logic import AddressBookLogic # Corrected import
from core.purchase_logic import PurchaseLogic
from shared.structs import Account, Contact, Address, PurchaseDocument, PurchaseDocumentItem, PurchaseDocumentStatus
import datetime

def populate_purchase_documents(db_handler: DatabaseHandler, purchase_logic: PurchaseLogic, address_book_logic: AddressBookLogic):
    print("Populating sample purchase documents...")
    try:
        # Attempt to get a vendor. We'll use "Test Account 01"
        # This assumes AddressBookLogic has a method to get account by name or similar
        # For simplicity, let's assume account with ID 1 is "Test Account 01" if it exists
        vendor_account_details = address_book_logic.get_account_details(1) # Fetches account with ID 1
        if not vendor_account_details:
            print("Could not find vendor account with ID 1 (Test Account 01) to create a PO. Skipping PO creation.")
            return

        vendor_id = vendor_account_details.account_id # account_id from the Account object

        # Create a sample Purchase Document
        po_doc = PurchaseDocument(
            document_number="PO-SANDBOX-001",
            vendor_id=vendor_id,
            created_date=datetime.datetime.now().isoformat(),
            status=PurchaseDocumentStatus.PO_ISSUED,
            notes="Sample PO created by sandbox script."
        )
        # Use db handler directly for sandbox simplicity
        new_doc_id = purchase_logic.db.add_purchase_document(
            doc_number=po_doc.document_number,
            vendor_id=po_doc.vendor_id,
            created_date=po_doc.created_date,
            status=po_doc.status.value, # Ensure enum value is passed
            notes=po_doc.notes
        )
        created_doc_obj = None
        if new_doc_id:
            created_doc_obj = purchase_logic.get_purchase_document_details(new_doc_id)

        if not created_doc_obj or not created_doc_obj.id:
            print(f"Failed to create purchase document {po_doc.document_number}.")
            return

        print(f"Purchase Document '{created_doc_obj.document_number}' created with ID {created_doc_obj.id}.")

        # Add items to the Purchase Document
        item1 = PurchaseDocumentItem(
            purchase_document_id=created_doc_obj.id,
            product_description="Sandbox Item A - Super Widget",
            quantity=10,
            unit_price=19.99,
            product_id=None # Assuming no specific product link for sandbox items for now
        )
        item1.calculate_total_price()
        # Use db handler directly for sandbox simplicity
        new_item1_id = purchase_logic.db.add_purchase_document_item(
            doc_id=item1.purchase_document_id,
            product_description=item1.product_description,
            quantity=item1.quantity,
            product_id=item1.product_id,
            unit_price=item1.unit_price,
            total_price=item1.total_price
        )
        if new_item1_id:
            added_item1 = purchase_logic.get_purchase_document_item_details(new_item1_id)
            if added_item1:
                 print(f"Added item '{added_item1.product_description}' to PO {created_doc_obj.document_number}")

        item2 = PurchaseDocumentItem(
            purchase_document_id=created_doc_obj.id,
            product_description="Sandbox Item B - Mega Gadget",
            quantity=5,
            unit_price=125.50,
            product_id=None
        )
        item2.calculate_total_price()
        new_item2_id = purchase_logic.db.add_purchase_document_item(
            doc_id=item2.purchase_document_id,
            product_description=item2.product_description,
            quantity=item2.quantity,
            product_id=item2.product_id,
            unit_price=item2.unit_price,
            total_price=item2.total_price
        )
        if new_item2_id:
            added_item2 = purchase_logic.get_purchase_document_item_details(new_item2_id)
            if added_item2:
                print(f"Added item '{added_item2.product_description}' to PO {created_doc_obj.document_number}")

        # Create a second PO for variety
        po_doc_2 = PurchaseDocument(
            document_number="PO-SANDBOX-002",
            vendor_id=vendor_id, # Same vendor for simplicity
            created_date=datetime.datetime.now().isoformat(),
            status=PurchaseDocumentStatus.RFQ,
            notes="Sample RFQ created by sandbox script."
        )
        new_doc_2_id = purchase_logic.db.add_purchase_document(
            doc_number=po_doc_2.document_number,
            vendor_id=po_doc_2.vendor_id,
            created_date=po_doc_2.created_date,
            status=po_doc_2.status.value, # Ensure enum value
            notes=po_doc_2.notes
        )
        created_doc_obj_2 = None
        if new_doc_2_id:
            created_doc_obj_2 = purchase_logic.get_purchase_document_details(new_doc_2_id)

        if not created_doc_obj_2 or not created_doc_obj_2.id:
            print(f"Failed to create purchase document {po_doc_2.document_number}.")
            return
        print(f"Purchase Document '{created_doc_obj_2.document_number}' created with ID {created_doc_obj_2.id}.")

        item3 = PurchaseDocumentItem(
            purchase_document_id=created_doc_obj_2.id,
            product_description="Sandbox Item C - Tiny Gizmo",
            quantity=100,
            unit_price=1.75,
            product_id=None
        )
        item3.calculate_total_price()
        new_item3_id = purchase_logic.db.add_purchase_document_item(
            doc_id=item3.purchase_document_id,
            product_description=item3.product_description,
            quantity=item3.quantity,
            product_id=item3.product_id,
            unit_price=item3.unit_price,
            total_price=item3.total_price
        )
        if new_item3_id:
            added_item3 = purchase_logic.get_purchase_document_item_details(new_item3_id)
            if added_item3:
                print(f"Added item '{added_item3.product_description}' to PO {created_doc_obj_2.document_number}")


    except Exception as e:
        print(f"Error during purchase document population: {e}")
        import traceback
        traceback.print_exc()


def populate_data():
    """
    Populates the database with sample accounts, contacts, and purchase documents.
    """
    print("Connecting to the database...")
    db_handler = DatabaseHandler() # Uses default "address_book.db" in core directory
    address_book_logic = AddressBookLogic(db_handler)
    purchase_logic = PurchaseLogic(db_handler) # Initialize PurchaseLogic
    print("Database connected.")

    print("Starting data population for Accounts and Contacts...")
    # Add 10 Accounts
    for i in range(1, 11):
        # print(f"Adding Account {i}...") # Reduced verbosity
        billing_street = f"{i*10} Billing St"
        billing_city = f"Billtown{i}"
        billing_state = "BS"
        billing_zip = f"B{i:05}"
        billing_country = "BCN"
        billing_address_id = address_book_logic.add_address(billing_street, billing_city, billing_state, billing_zip, billing_country)

        shipping_street = f"{i*10} Shipping Ave"
        shipping_city = f"Shipton{i}"
        shipping_state = "SS"
        shipping_zip = f"S{i:05}"
        shipping_country = "SCN"
        shipping_address_id = address_book_logic.add_address(shipping_street, shipping_city, shipping_state, shipping_zip, shipping_country)

        account = Account(
            name=f"Test Account {i:02}",
            phone=f"555-01{i:02}",
            billing_address_id=billing_address_id,
            shipping_address_id=shipping_address_id,
            website=f"http://testaccount{i}.com",
            description=f"This is test account number {i}."
        )
        # Ensure save_account returns the created Account object or its ID
        created_account = address_book_logic.save_account(account)
        if created_account:
            print(f"Account '{created_account.name}' added with ID {created_account.account_id}.")
        else:
            print(f"Failed to add account '{account.name}'.")


    all_accounts_tuples = address_book_logic.get_accounts()
    test_accounts_tuples = [acc for acc in all_accounts_tuples if acc[1].startswith("Test Account")]
    if not test_accounts_tuples:
        print("No 'Test Account' found. Cannot add contacts as planned.")
    else:
        print(f"Found {len(test_accounts_tuples)} 'Test Account's to associate contacts with.")

    for i in range(1, 11):
        if not test_accounts_tuples: break # No accounts to assign to

        account_tuple_for_contact = test_accounts_tuples[(i-1) % len(test_accounts_tuples)]
        account_id_for_contact = account_tuple_for_contact[0]
        account_name_for_contact = account_tuple_for_contact[1]

        # print(f"Adding Contact {i} for account '{account_name_for_contact}' (ID: {account_id_for_contact})...") # Reduced verbosity
        contact = Contact(
            name=f"Contact Person {i:02}",
            phone=f"555-02{i:02}",
            email=f"contact{i}@testaccount.com",
            role=f"Role {i}",
            account_id=account_id_for_contact
        )
        # Ensure save_contact returns the created Contact object or its ID
        created_contact = address_book_logic.save_contact(contact)
        if created_contact:
            print(f"Contact '{created_contact.name}' added with ID {created_contact.contact_id} to account '{account_name_for_contact}'.")
        else:
            print(f"Failed to add contact '{contact.name}'.")

    print("Finished Accounts and Contacts population.")

    # Populate Purchase Documents
    populate_purchase_documents(db_handler, purchase_logic, address_book_logic)

    print("Data population script finished.")
    db_handler.close()
    print("Database connection closed.")

if __name__ == "__main__":
    db_file_path = os.path.join(project_root, "core", "address_book.db")
    if os.path.exists(db_file_path):
        print(f"Deleting existing database file: {db_file_path}")
        try:
            os.remove(db_file_path)
            print("Old database file deleted.")
        except OSError as e:
            print(f"Error deleting database file {db_file_path}: {e}")
            print("Please check permissions or if the file is in use.")
            sys.exit(1)

    # The prompt was removed earlier, this just proceeds.
    # print("Skipping database existence check and proceeding with data population.")
    populate_data()
