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

        vendor_id = vendor_account_details.account_id

        # Create a sample RFQ using PurchaseLogic to get auto-generated number
        print("Creating sample RFQ...")
        rfq_doc_obj = purchase_logic.create_rfq(
            vendor_id=vendor_id,
            notes="Sample RFQ automatically numbered by sandbox script."
        )

        if not rfq_doc_obj or not rfq_doc_obj.id:
            print(f"Failed to create RFQ document.")
            return

        print(f"RFQ Document '{rfq_doc_obj.document_number}' created with ID {rfq_doc_obj.id}, Status: {rfq_doc_obj.status.value}.")

        # Add items to the RFQ Document
        item1 = PurchaseDocumentItem(
            purchase_document_id=rfq_doc_obj.id,
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
                 print(f"Added item '{added_item1.product_description}' to RFQ {rfq_doc_obj.document_number}")

        item2 = PurchaseDocumentItem(
            purchase_document_id=rfq_doc_obj.id,
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
                print(f"Added item '{added_item2.product_description}' to RFQ {rfq_doc_obj.document_number}")

        # Create a second document, this time let's make it a PO after creation
        print("Creating sample PO (via RFQ then conversion)...")
        po_doc_obj = purchase_logic.create_rfq(
            vendor_id=vendor_id, # Same vendor for simplicity
            notes="Sample PO (initially RFQ) automatically numbered by sandbox script."
        )

        if not po_doc_obj or not po_doc_obj.id:
            print(f"Failed to create initial RFQ for PO conversion.")
            return

        print(f"Initial document '{po_doc_obj.document_number}' created with ID {po_doc_obj.id}, Status: {po_doc_obj.status.value}.")

        # Simulate quoting and conversion to PO
        # Add an item (required for some status transitions, or just good for testing)
        item3 = PurchaseDocumentItem(
            purchase_document_id=po_doc_obj.id,
            product_description="Sandbox Item C - Tiny Gizmo for PO",
            quantity=100,
            unit_price=1.75, # Providing a unit price
            product_id=None
        )
        item3.calculate_total_price()
        # Use the proper PurchaseLogic method to add items which might also update status to Quoted
        added_item3_obj = purchase_logic.add_item_to_document(
            doc_id=po_doc_obj.id,
            product_id=item3.product_id, # Will be None
            quantity=item3.quantity,
            unit_price=item3.unit_price, # Pass unit price
            product_description_override=item3.product_description
        )

        if added_item3_obj:
            print(f"Added item '{added_item3_obj.product_description}' to document {po_doc_obj.document_number}")
            # Check if status became Quoted (add_item_to_document in PurchaseLogic might do this if unit_price is given)
            # For sandbox, let's explicitly update status to Quoted if not already, then to PO_Issued
            # This requires get_purchase_document_details to be accurate.
            current_doc_state = purchase_logic.get_purchase_document_details(po_doc_obj.id)
            if current_doc_state.status == PurchaseDocumentStatus.RFQ:
                 print(f"Updating status of doc {current_doc_state.document_number} to Quoted...")
                 purchase_logic.update_document_status(current_doc_state.id, PurchaseDocumentStatus.QUOTED)
                 current_doc_state = purchase_logic.get_purchase_document_details(po_doc_obj.id) # Refresh state

            if current_doc_state.status == PurchaseDocumentStatus.QUOTED:
                print(f"Converting doc {current_doc_state.document_number} to PO-Issued...")
                po_final_obj = purchase_logic.convert_rfq_to_po(current_doc_state.id)
                if po_final_obj:
                    print(f"Document '{po_final_obj.document_number}' is now PO-Issued with ID {po_final_obj.id}.")
                else:
                    print(f"Failed to convert doc {current_doc_state.document_number} to PO-Issued.")
            else:
                print(f"Document {current_doc_state.document_number} status is {current_doc_state.status.value}, not converting to PO for sandbox.")
        else:
            print(f"Failed to add item to document {po_doc_obj.document_number}, cannot proceed with PO conversion steps.")


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
