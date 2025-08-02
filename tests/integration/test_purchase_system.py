import unittest
import os
import datetime
from core.database import DatabaseHandler
from core.purchase_logic import PurchaseLogic
from core.logic.product_management import ProductLogic # Import ProductLogic
from shared.structs import PurchaseDocumentStatus, AccountType, Product # Import Product for creation

class TestPurchaseSystemIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db_name = "test_purchase_system.db"
        if os.path.exists(cls.test_db_name):
            os.remove(cls.test_db_name)

        cls.db_handler = DatabaseHandler(db_name=cls.test_db_name)
        cls.purchase_logic = PurchaseLogic(cls.db_handler)
        cls.product_logic = ProductLogic(cls.db_handler) # Instantiate ProductLogic

        # Create some products to be used in tests
        cls.product1 = cls.product_logic.save_product(Product(name="Test Laptop X1", description="High-end testing laptop", cost=1200.00, category="Electronics", unit_of_measure="Unit"))
        cls.product2 = cls.product_logic.save_product(Product(name="Wireless Test Mouse", description="Ergonomic mouse for testing", cost=25.00, category="Peripherals", unit_of_measure="Unit"))
        # save_product should return the product object with id, or just the id.
        # Assuming save_product returns the object with ID for simplicity here.
        # If it returns ID, we'd fetch the object.
        # Let's assume product_logic.save_product returns the full Product object with ID.
        # If not, we'll need to adjust or fetch them.
        # For now, let's assume product1 and product2 have their IDs set by save_product.
        # If save_product returns ID:
        # p1_id = cls.product_logic.save_product(...)
        # cls.product1 = cls.product_logic.get_product_details(p1_id)
        # To be safe, let's get them after saving if save_product only returns ID
        if isinstance(cls.product1, int): # If save_product returns ID
             cls.product1 = cls.product_logic.get_product_details(cls.product1)
        if isinstance(cls.product2, int):
             cls.product2 = cls.product_logic.get_product_details(cls.product2)


        # Setup a vendor account
        # Ensure add_account in DatabaseHandler includes account_type if modified
        # For this test, we assume add_account takes all necessary params including account_type.
        # If add_account was not updated to include account_type, this will fail or need adjustment.
        # Based on previous work, Account.account_type is now a field.
        # db_handler.add_account needs: name, phone, bill_addr, ship_addr, same_as_bill, web, desc, type
        cls.vendor1_id = cls.db_handler.add_account(
            name="Test Vendor One",
            phone="123-456-7890",
            website="vendor.com",
            description="Main vendor for testing",
            account_type=AccountType.VENDOR.value # Use the string value for DB
        )
        cls.vendor2_id = cls.db_handler.add_account(
            name="Test Vendor Two",
            phone="987-654-3210",
            website="vendor2.com",
            description="Second vendor",
            account_type=AccountType.VENDOR.value
        )


    @classmethod
    def tearDownClass(cls):
        cls.db_handler.close()
        if os.path.exists(cls.test_db_name):
            os.remove(cls.test_db_name)

    def setUp(self):
        # Clean relevant tables before each test
        self.db_handler.cursor.execute("DELETE FROM purchase_document_items")
        self.db_handler.cursor.execute("DELETE FROM purchase_documents")
        # Note: Accounts are not deleted here to persist vendors across tests in this class
        self.db_handler.conn.commit()

    def test_full_rfq_to_po_lifecycle(self):
        # 1. Create RFQ
        rfq_doc = self.purchase_logic.create_rfq(vendor_id=self.vendor1_id, notes="Initial RFQ for Project X")
        self.assertIsNotNone(rfq_doc)
        self.assertIsNotNone(rfq_doc.id)
        self.assertEqual(rfq_doc.status, PurchaseDocumentStatus.RFQ)
        self.assertEqual(rfq_doc.vendor_id, self.vendor1_id)
        self.assertTrue(rfq_doc.document_number.startswith("P"))

        # 2. Add items to RFQ (using product_id)
        self.assertIsNotNone(self.product1, "Product1 should be loaded")
        self.assertIsNotNone(self.product1.product_id, "Product1 ID should not be None")
        item1 = self.purchase_logic.add_item_to_document(rfq_doc.id, product_id=self.product1.product_id, quantity=10)
        self.assertIsNotNone(item1)
        self.assertEqual(item1.product_id, self.product1.product_id)
        self.assertEqual(item1.product_description, self.product1.name) # Assuming logic fetches name as description
        self.assertEqual(item1.quantity, 10)
        self.assertIsNone(item1.unit_price)

        self.assertIsNotNone(self.product2, "Product2 should be loaded")
        self.assertIsNotNone(self.product2.product_id, "Product2 ID should not be None")
        item2 = self.purchase_logic.add_item_to_document(rfq_doc.id, product_id=self.product2.product_id, quantity=1)
        self.assertIsNotNone(item2)
        self.assertEqual(item2.product_id, self.product2.product_id)
        self.assertEqual(item2.product_description, self.product2.name)


        # 3. Update item quotes (and document becomes 'Quoted')
        # Simulate editing item1 to add a price
        updated_item1 = self.purchase_logic.update_document_item(
            item_id=item1.id,
            product_id=item1.product_id, # Keep the same product
            quantity=item1.quantity,    # Keep the same quantity
            unit_price=50.25            # Set the unit price
        )
        self.assertIsNotNone(updated_item1)
        self.assertEqual(updated_item1.unit_price, 50.25)
        self.assertEqual(updated_item1.total_price, 502.50) # 10 * 50.25

        # Check if document status updated to QUOTED after first item quote
        rfq_doc_after_quote = self.purchase_logic.get_purchase_document_details(rfq_doc.id)
        self.assertEqual(rfq_doc_after_quote.status, PurchaseDocumentStatus.QUOTED)

        # Simulate editing item2 to add a price
        updated_item2 = self.purchase_logic.update_document_item(
            item_id=item2.id,
            product_id=item2.product_id,
            quantity=item2.quantity,
            unit_price=150.00
        )
        self.assertEqual(updated_item2.unit_price, 150.00)
        self.assertEqual(updated_item2.total_price, 150.00)

        # 4. Convert RFQ to PO
        po_doc = self.purchase_logic.convert_rfq_to_po(rfq_doc.id)
        self.assertIsNotNone(po_doc)
        self.assertEqual(po_doc.status, PurchaseDocumentStatus.PO_ISSUED)
        # Document number should now be a new PO number
        self.assertTrue(po_doc.document_number.startswith("P"))
        self.assertNotEqual(po_doc.document_number, rfq_doc.document_number)

        # 5. Mark PO as Received
        received_doc = self.purchase_logic.mark_document_received(po_doc.id)
        self.assertIsNotNone(received_doc)
        self.assertEqual(received_doc.status, PurchaseDocumentStatus.RECEIVED)

        # 6. Close PO
        closed_doc = self.purchase_logic.close_purchase_document(received_doc.id)
        self.assertIsNotNone(closed_doc)
        self.assertEqual(closed_doc.status, PurchaseDocumentStatus.CLOSED)

        # Verify items are still there and priced
        items_final = self.purchase_logic.get_items_for_document(closed_doc.id)
        self.assertEqual(len(items_final), 2)
        self.assertEqual(items_final[0].total_price, 502.50)
        self.assertEqual(items_final[1].total_price, 150.00)


    def test_get_all_documents_filtering(self):
        rfq1_v1 = self.purchase_logic.create_rfq(vendor_id=self.vendor1_id, notes="V1 RFQ1")
        rfq2_v1 = self.purchase_logic.create_rfq(vendor_id=self.vendor1_id, notes="V1 RFQ2")
        rfq1_v2 = self.purchase_logic.create_rfq(vendor_id=self.vendor2_id, notes="V2 RFQ1")

        # Add items and quote rfq1_v1 to change its status
        self.assertIsNotNone(self.product1, "Product1 must exist")
        item_rfq1_v1 = self.purchase_logic.add_item_to_document(rfq1_v1.id, product_id=self.product1.product_id, quantity=1)
        self.assertIsNotNone(item_rfq1_v1, "Item should be created for rfq1_v1")
        self.purchase_logic.update_document_item( # Use update_document_item
            item_id=item_rfq1_v1.id,
            product_id=item_rfq1_v1.product_id,
            quantity=item_rfq1_v1.quantity,
            unit_price=10.0 # Set price to quote
        ) # Now rfq1_v1 is QUOTED

        # Get all
        all_docs = self.purchase_logic.get_all_documents_by_criteria()
        self.assertEqual(len(all_docs), 3)

        # Get by vendor1
        v1_docs = self.purchase_logic.get_all_documents_by_criteria(vendor_id=self.vendor1_id)
        self.assertEqual(len(v1_docs), 2)
        self.assertTrue(all(d.vendor_id == self.vendor1_id for d in v1_docs))

        # Get by status RFQ
        rfq_status_docs = self.purchase_logic.get_all_documents_by_criteria(status=PurchaseDocumentStatus.RFQ)
        self.assertEqual(len(rfq_status_docs), 2) # rfq2_v1 and rfq1_v2
        self.assertTrue(all(d.status == PurchaseDocumentStatus.RFQ for d in rfq_status_docs))

        # Get by status QUOTED
        quoted_status_docs = self.purchase_logic.get_all_documents_by_criteria(status=PurchaseDocumentStatus.QUOTED)
        self.assertEqual(len(quoted_status_docs), 1)
        self.assertEqual(quoted_status_docs[0].id, rfq1_v1.id)

        # Get by vendor AND status
        v1_rfq_docs = self.purchase_logic.get_all_documents_by_criteria(vendor_id=self.vendor1_id, status=PurchaseDocumentStatus.RFQ)
        self.assertEqual(len(v1_rfq_docs), 1)
        self.assertEqual(v1_rfq_docs[0].id, rfq2_v1.id) # rfq1_v1 for vendor1 is now QUOTED

    def test_delete_document_and_items_cascade(self):
        rfq_to_delete = self.purchase_logic.create_rfq(vendor_id=self.vendor1_id, notes="To be deleted")
        self.assertIsNotNone(self.product1, "Product1 must exist for this test")
        self.assertIsNotNone(self.product2, "Product2 must exist for this test")
        item_a = self.purchase_logic.add_item_to_document(rfq_to_delete.id, product_id=self.product1.product_id, quantity=1)
        item_b = self.purchase_logic.add_item_to_document(rfq_to_delete.id, product_id=self.product2.product_id, quantity=2)

        items_before_delete = self.purchase_logic.get_items_for_document(rfq_to_delete.id)
        self.assertEqual(len(items_before_delete), 2)

        self.purchase_logic.delete_purchase_document(rfq_to_delete.id)

        deleted_doc_check = self.purchase_logic.get_purchase_document_details(rfq_to_delete.id)
        self.assertIsNotNone(deleted_doc_check)
        self.assertFalse(deleted_doc_check.is_active)

        items_after_delete = self.db_handler.get_items_for_document(
            rfq_to_delete.id
        )  # Use DB direct to check
        self.assertEqual(len(items_after_delete), 2)

    def test_delete_specific_item(self):
        rfq = self.purchase_logic.create_rfq(vendor_id=self.vendor1_id)
        self.assertIsNotNone(self.product1, "Product1 must exist")
        self.assertIsNotNone(self.product2, "Product2 must exist")
        item1 = self.purchase_logic.add_item_to_document(rfq.id, product_id=self.product1.product_id, quantity=1)
        item2_to_delete = self.purchase_logic.add_item_to_document(rfq.id, product_id=self.product2.product_id, quantity=1)

        items_before = self.purchase_logic.get_items_for_document(rfq.id)
        self.assertEqual(len(items_before), 2)

        self.purchase_logic.delete_document_item(item2_to_delete.id)

        items_after = self.purchase_logic.get_items_for_document(rfq.id)
        self.assertEqual(len(items_after), 1)
        self.assertEqual(items_after[0].id, item1.id)
        self.assertEqual(items_after[0].product_description, self.product1.name) # Expect product name

if __name__ == '__main__':
    unittest.main()
