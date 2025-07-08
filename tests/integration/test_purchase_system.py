import unittest
import os
import datetime
from core.database import DatabaseHandler
from core.purchase_logic import PurchaseLogic
from shared.structs import PurchaseDocumentStatus, AccountType

class TestPurchaseSystemIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db_name = "test_purchase_system.db"
        if os.path.exists(cls.test_db_name):
            os.remove(cls.test_db_name)

        cls.db_handler = DatabaseHandler(db_name=cls.test_db_name)
        # The PurchaseLogic class expects db_handler, not the connection
        cls.purchase_logic = PurchaseLogic(cls.db_handler)

        # Setup a vendor account
        # Ensure add_account in DatabaseHandler includes account_type if modified
        # For this test, we assume add_account takes all necessary params including account_type.
        # If add_account was not updated to include account_type, this will fail or need adjustment.
        # Based on previous work, Account.account_type is now a field.
        # db_handler.add_account needs: name, phone, bill_addr, ship_addr, same_as_bill, web, desc, type
        cls.vendor1_id = cls.db_handler.add_account(
            name="Test Vendor One",
            phone="123-456-7890",
            billing_address_id=None,
            shipping_address_id=None,
            same_as_billing=False,
            website="vendor.com",
            description="Main vendor for testing",
            account_type=AccountType.VENDOR.value # Use the string value for DB
        )
        cls.vendor2_id = cls.db_handler.add_account(
            name="Test Vendor Two",
            phone="987-654-3210",
            billing_address_id=None,
            shipping_address_id=None,
            same_as_billing=False,
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
        self.assertTrue(rfq_doc.document_number.startswith("RFQ-"))

        # 2. Add items to RFQ
        item1 = self.purchase_logic.add_item_to_document(rfq_doc.id, "Product Alpha", 10)
        self.assertIsNotNone(item1)
        self.assertEqual(item1.product_description, "Product Alpha")
        self.assertEqual(item1.quantity, 10)
        self.assertIsNone(item1.unit_price)

        item2 = self.purchase_logic.add_item_to_document(rfq_doc.id, "Service Beta", 1) # e.g. a service
        self.assertIsNotNone(item2)
        self.assertEqual(item2.product_description, "Service Beta")

        # 3. Update item quotes (and document becomes 'Quoted')
        updated_item1 = self.purchase_logic.update_item_quote(item1.id, 50.25) # Price $50.25
        self.assertIsNotNone(updated_item1)
        self.assertEqual(updated_item1.unit_price, 50.25)
        self.assertEqual(updated_item1.total_price, 502.50) # 10 * 50.25

        # Check if document status updated to QUOTED after first item quote
        rfq_doc_after_quote = self.purchase_logic.get_purchase_document_details(rfq_doc.id)
        self.assertEqual(rfq_doc_after_quote.status, PurchaseDocumentStatus.QUOTED)

        updated_item2 = self.purchase_logic.update_item_quote(item2.id, 150.00)
        self.assertEqual(updated_item2.unit_price, 150.00)
        self.assertEqual(updated_item2.total_price, 150.00)

        # 4. Convert RFQ to PO
        po_doc = self.purchase_logic.convert_rfq_to_po(rfq_doc.id)
        self.assertIsNotNone(po_doc)
        self.assertEqual(po_doc.status, PurchaseDocumentStatus.PO_ISSUED)
        # Document number might change or stay same based on logic - current logic keeps it same.
        self.assertEqual(po_doc.document_number, rfq_doc.document_number)

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
        item_rfq1_v1 = self.purchase_logic.add_item_to_document(rfq1_v1.id, "Item", 1)
        self.purchase_logic.update_item_quote(item_rfq1_v1.id, 10) # Now rfq1_v1 is QUOTED

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
        item_a = self.purchase_logic.add_item_to_document(rfq_to_delete.id, "Item A", 1)
        item_b = self.purchase_logic.add_item_to_document(rfq_to_delete.id, "Item B", 2)

        items_before_delete = self.purchase_logic.get_items_for_document(rfq_to_delete.id)
        self.assertEqual(len(items_before_delete), 2)

        self.purchase_logic.delete_purchase_document(rfq_to_delete.id)

        # Check document is deleted
        deleted_doc_check = self.purchase_logic.get_purchase_document_details(rfq_to_delete.id)
        self.assertIsNone(deleted_doc_check)

        # Check items are deleted (due to ON DELETE CASCADE)
        items_after_delete = self.db_handler.get_items_for_document(rfq_to_delete.id) # Use DB direct to check
        self.assertEqual(len(items_after_delete), 0)

    def test_delete_specific_item(self):
        rfq = self.purchase_logic.create_rfq(vendor_id=self.vendor1_id)
        item1 = self.purchase_logic.add_item_to_document(rfq.id, "Keep", 1)
        item2_to_delete = self.purchase_logic.add_item_to_document(rfq.id, "DeleteMe", 1)

        items_before = self.purchase_logic.get_items_for_document(rfq.id)
        self.assertEqual(len(items_before), 2)

        self.purchase_logic.delete_document_item(item2_to_delete.id)

        items_after = self.purchase_logic.get_items_for_document(rfq.id)
        self.assertEqual(len(items_after), 1)
        self.assertEqual(items_after[0].id, item1.id)
        self.assertEqual(items_after[0].product_description, "Keep")

if __name__ == '__main__':
    unittest.main()
