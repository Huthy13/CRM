import unittest
from unittest.mock import MagicMock, patch
import datetime

# Before importing PurchaseLogic, ensure shared.structs and core.database can be found
# This might require adjusting sys.path if running tests directly from this file's directory
# For `python -m unittest discover`, it usually works if tests are in a package structure.

from core.purchase_logic import PurchaseLogic
from shared.structs import PurchaseDocument, PurchaseDocumentItem, PurchaseDocumentStatus, AccountType
from core.database import DatabaseHandler # Actual import for type hint, but will be mocked

class TestPurchaseLogic(unittest.TestCase):

    def setUp(self):
        self.mock_db_handler = MagicMock(spec=DatabaseHandler)
        self.purchase_logic = PurchaseLogic(self.mock_db_handler)

        # Mock a vendor account that get_account_details might return
        self.mock_vendor_account_dict = {
            "id": 1, "name": "Test Vendor", "account_type": AccountType.VENDOR.value
            # Add other fields if PurchaseLogic starts checking them more deeply
        }
        self.mock_db_handler.get_account_details.return_value = self.mock_vendor_account_dict

    def test_generate_document_number_first_of_day(self):
        # Mock datetime to control date string
        with patch('core.purchase_logic.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.strftime.return_value = "20230101" # YYYYMMDD
            mock_datetime.datetime.now.return_value = mock_now

            # Simulate no existing documents for this prefix and date
            self.mock_db_handler.get_all_purchase_documents.return_value = []

            doc_number = self.purchase_logic._generate_document_number("RFQ")
            self.assertEqual(doc_number, "RFQ-20230101-0001")

    def test_generate_document_number_subsequent_of_day(self):
        with patch('core.purchase_logic.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.strftime.return_value = "20230101"
            mock_datetime.datetime.now.return_value = mock_now

            # Simulate one existing document
            existing_doc_num = "RFQ-20230101-0001"
            self.mock_db_handler.get_all_purchase_documents.return_value = [{"document_number": existing_doc_num}]

            doc_number = self.purchase_logic._generate_document_number("RFQ")
            self.assertEqual(doc_number, "RFQ-20230101-0002")

    def test_create_rfq_success(self):
        self.mock_db_handler.add_purchase_document.return_value = 123 # New document ID

        # Mock get_purchase_document_by_id to return a dict that PurchaseLogic.get_purchase_document_details will convert
        mock_created_doc_dict = {
            "id": 123, "document_number": "RFQ-20230101-0001", "vendor_id": 1,
            "created_date": "dummy_iso_date", "status": "RFQ", "notes": "Test notes"
        }
        self.mock_db_handler.get_purchase_document_by_id.return_value = mock_created_doc_dict

        with patch.object(self.purchase_logic, '_generate_document_number', return_value="RFQ-20230101-0001"):
            rfq = self.purchase_logic.create_rfq(vendor_id=1, notes="Test notes")

        self.assertIsNotNone(rfq)
        self.assertEqual(rfq.id, 123)
        self.assertEqual(rfq.document_number, "RFQ-20230101-0001")
        self.assertEqual(rfq.vendor_id, 1)
        self.assertEqual(rfq.status, PurchaseDocumentStatus.RFQ)
        self.assertEqual(rfq.notes, "Test notes")
        self.mock_db_handler.add_purchase_document.assert_called_once()
        # Check that created_date was passed (value is dynamic, so check key)
        self.assertIn('created_date', self.mock_db_handler.add_purchase_document.call_args[1])


    def test_create_rfq_vendor_not_found(self):
        self.mock_db_handler.get_account_details.return_value = None # Simulate vendor not found
        with self.assertRaisesRegex(ValueError, "Vendor with ID 99 not found."):
            self.purchase_logic.create_rfq(vendor_id=99)

    def test_add_item_to_document_success(self):
        doc_id = 1
        # Mock the parent document
        self.mock_db_handler.get_purchase_document_by_id.return_value = {
            "id": doc_id, "document_number": "RFQ-001", "vendor_id": 1,
            "created_date": "date", "status": PurchaseDocumentStatus.RFQ.value, "notes": ""
        }
        self.mock_db_handler.add_purchase_document_item.return_value = 50 # New item ID

        # Mock get_purchase_document_item_by_id to return the item dict
        self.mock_db_handler.get_purchase_document_item_by_id.return_value = {
            "id": 50, "purchase_document_id": doc_id, "product_description": "Test Item",
            "quantity": 2.0, "unit_price": None, "total_price": None
        }

        item = self.purchase_logic.add_item_to_document(doc_id, "Test Item", 2.0)
        self.assertIsNotNone(item)
        self.assertEqual(item.id, 50)
        self.assertEqual(item.product_description, "Test Item")
        self.assertEqual(item.quantity, 2.0)
        self.mock_db_handler.add_purchase_document_item.assert_called_with(
            doc_id=doc_id, product_description="Test Item", quantity=2.0,
            unit_price=None, total_price=None
        )

    def test_add_item_to_document_doc_not_found(self):
        self.mock_db_handler.get_purchase_document_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, "Purchase document with ID 999 not found."):
            self.purchase_logic.add_item_to_document(999, "Test Item", 1)

    def test_add_item_to_document_invalid_quantity(self):
        # Ensure the mock returns all necessary fields for PurchaseDocument instantiation
        self.mock_db_handler.get_purchase_document_by_id.return_value = {
            "id": 1, "document_number": "RFQ-001", "vendor_id": 1,
            "created_date": "date_str", "status": PurchaseDocumentStatus.RFQ.value, "notes": ""
        }
        with self.assertRaisesRegex(ValueError, "Quantity must be positive."):
            self.purchase_logic.add_item_to_document(1, "Test Item", 0)


    def test_update_item_quote_success(self):
        item_id = 5
        doc_id = 1
        # Mock existing item and its document
        self.mock_db_handler.get_purchase_document_item_by_id.return_value = {
            "id": item_id, "purchase_document_id": doc_id, "product_description": "Old Desc",
            "quantity": 10.0, "unit_price": None, "total_price": None # All keys for PurchaseDocumentItem
        }
        # Mock for get_purchase_document_details called within update_item_quote
        self.mock_db_handler.get_purchase_document_by_id.side_effect = [
            { # First call for the document status check
                "id": doc_id, "document_number": "RFQ-DOC-001", "vendor_id": 1,
                "created_date": "date1", "status": PurchaseDocumentStatus.RFQ.value, "notes": ""
            },
            { # Second call for returning the updated document (if get_purchase_document_item_details calls it)
              # Actually, get_purchase_document_item_details is called, which calls get_purchase_document_item_by_id again.
              # So, the mock for get_purchase_document_item_by_id needs to be robust or reset.
              # Let's ensure the second call to get_purchase_document_item_by_id for the return also works.
                "id": doc_id, "document_number": "RFQ-DOC-001", "vendor_id": 1,
                "created_date": "date1", "status": PurchaseDocumentStatus.QUOTED.value, "notes": "" # Status is now QUOTED
            }
        ]
        # Adjust get_purchase_document_item_by_id to be called multiple times if necessary
        # For simplicity, the second call to get_purchase_document_item_details will use the same item data initially
        # then it's updated. The key is that get_purchase_document_item_by_id is called for the return.
        # Let's make it simpler: get_purchase_document_item_by_id returns the item that will be updated.
        # The return value of update_item_quote calls get_purchase_document_item_details(item_id)
        # which in turn calls self.db.get_purchase_document_item_by_id(item_id)

        # Store the expected updated state for the second call
        expected_updated_item_dict = {
            "id": item_id, "purchase_document_id": doc_id, "product_description": "Old Desc",
            "quantity": 10.0, "unit_price": 5.0, "total_price": 50.0
        }

        def mock_get_item_side_effect(called_item_id):
            if called_item_id == item_id:
                # First call returns original, subsequent calls could return updated
                # For this test, let's assume it's called once for initial fetch, then for return.
                # The logic updates it in DB, then re-fetches. So the mock should reflect that.
                if self.mock_db_handler.update_purchase_document_item.called:
                     return expected_updated_item_dict # After update
                return { # Before update
                    "id": item_id, "purchase_document_id": doc_id, "product_description": "Old Desc",
                    "quantity": 10.0, "unit_price": None, "total_price": None
                }
            return None

        self.mock_db_handler.get_purchase_document_item_by_id.side_effect = mock_get_item_side_effect

        updated_item = self.purchase_logic.update_item_quote(item_id, 5.0)

        self.assertIsNotNone(updated_item)
        self.assertEqual(updated_item.unit_price, 5.0)
        self.assertEqual(updated_item.total_price, 50.0) # 10 * 5

        self.mock_db_handler.update_purchase_document_item.assert_called_with(
            item_id=item_id, product_description="Old Desc", quantity=10.0,
            unit_price=5.0, total_price=50.0
        )
        self.mock_db_handler.update_purchase_document_status.assert_called_with(doc_id, PurchaseDocumentStatus.QUOTED.value)

    def test_update_item_quote_item_not_found(self):
        self.mock_db_handler.get_purchase_document_item_by_id.side_effect = None # Clear side_effect from previous test
        self.mock_db_handler.get_purchase_document_item_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, "Item with ID 999 not found."):
            self.purchase_logic.update_item_quote(999, 10.0)

    def test_update_item_quote_negative_price(self):
        self.mock_db_handler.get_purchase_document_item_by_id.side_effect = None
        self.mock_db_handler.get_purchase_document_item_by_id.return_value = {
            "id": 1, "purchase_document_id": 1, "product_description": "Test", "quantity": 1 # More complete
        }
        with self.assertRaisesRegex(ValueError, "Unit price cannot be negative."):
            self.purchase_logic.update_item_quote(1, -5.0)

    def test_convert_rfq_to_po_success(self):
        doc_id = 1
        self.mock_db_handler.get_purchase_document_by_id.side_effect = None # Clear side_effect

        initial_doc_state = {
            "id": doc_id, "document_number": "RFQ-002", "vendor_id": 2,
            "created_date": "date2", "status": PurchaseDocumentStatus.QUOTED.value, "notes": "notes"
        }
        updated_doc_state = {
            "id": doc_id, "document_number": "RFQ-002", "vendor_id": 2,
            "created_date": "date2", "status": PurchaseDocumentStatus.PO_ISSUED.value, "notes": "notes"
        }

        # First call to get_purchase_document_details (inside convert_rfq_to_po) gets initial state.
        # Second call (at the end of convert_rfq_to_po) should get updated state.
        self.mock_db_handler.get_purchase_document_by_id.side_effect = [initial_doc_state, updated_doc_state]

        updated_doc = self.purchase_logic.convert_rfq_to_po(doc_id)

        self.assertIsNotNone(updated_doc)
        self.assertEqual(updated_doc.status, PurchaseDocumentStatus.PO_ISSUED)
        self.mock_db_handler.update_purchase_document_status.assert_called_with(doc_id, PurchaseDocumentStatus.PO_ISSUED.value)

    def test_convert_rfq_to_po_wrong_status(self):
        doc_id = 1
        self.mock_db_handler.get_purchase_document_by_id.side_effect = None
        self.mock_db_handler.get_purchase_document_by_id.return_value = {
            "id": doc_id, "document_number": "RFQ-003", "vendor_id": 3,
            "created_date": "date3", "status": PurchaseDocumentStatus.RFQ.value, "notes": "notes"
        }
        with self.assertRaisesRegex(ValueError, "Only RFQs with status 'Quoted' can be converted to PO."):
            self.purchase_logic.convert_rfq_to_po(doc_id)

    def test_mark_document_received_success(self):
        doc_id = 1
        self.mock_db_handler.get_purchase_document_by_id.side_effect = None
        initial_doc_state = {
            "id": doc_id, "document_number": "PO-004", "vendor_id": 4,
            "created_date": "date4", "status": PurchaseDocumentStatus.PO_ISSUED.value, "notes": "notes"
        }
        updated_doc_state = {
            "id": doc_id, "document_number": "PO-004", "vendor_id": 4,
            "created_date": "date4", "status": PurchaseDocumentStatus.RECEIVED.value, "notes": "notes"
        }
        self.mock_db_handler.get_purchase_document_by_id.side_effect = [initial_doc_state, updated_doc_state]
        updated_doc = self.purchase_logic.mark_document_received(doc_id)
        self.assertEqual(updated_doc.status, PurchaseDocumentStatus.RECEIVED)
        self.mock_db_handler.update_purchase_document_status.assert_called_with(doc_id, PurchaseDocumentStatus.RECEIVED.value)

    def test_close_purchase_document_success(self):
        doc_id = 1
        self.mock_db_handler.get_purchase_document_by_id.side_effect = None
        initial_doc_state = {
            "id": doc_id, "document_number": "PO-005", "vendor_id": 5,
            "created_date": "date5", "status": PurchaseDocumentStatus.RECEIVED.value, "notes": "notes"
        }
        updated_doc_state = {
            "id": doc_id, "document_number": "PO-005", "vendor_id": 5,
            "created_date": "date5", "status": PurchaseDocumentStatus.CLOSED.value, "notes": "notes"
        }
        self.mock_db_handler.get_purchase_document_by_id.side_effect = [initial_doc_state, updated_doc_state]
        updated_doc = self.purchase_logic.close_purchase_document(doc_id)
        self.assertEqual(updated_doc.status, PurchaseDocumentStatus.CLOSED)
        self.mock_db_handler.update_purchase_document_status.assert_called_with(doc_id, PurchaseDocumentStatus.CLOSED.value)

    # Example for a getter method
    def test_get_purchase_document_details(self):
        doc_id = 7
        mock_doc_data = {
            "id": doc_id, "document_number": "RFQ-123", "vendor_id": 1,
            "created_date": "2023-01-01T00:00:00", "status": "RFQ", "notes": "Test"
        }
        self.mock_db_handler.get_purchase_document_by_id.return_value = mock_doc_data

        doc_obj = self.purchase_logic.get_purchase_document_details(doc_id)

        self.assertIsNotNone(doc_obj)
        self.assertEqual(doc_obj.id, doc_id)
        self.assertEqual(doc_obj.status, PurchaseDocumentStatus.RFQ)
        self.mock_db_handler.get_purchase_document_by_id.assert_called_with(doc_id)

    def test_get_items_for_document_logic(self):
        doc_id = 8
        mock_items_data = [
            {"id": 1, "purchase_document_id": doc_id, "product_description": "Item A", "quantity": 1.0},
            {"id": 2, "purchase_document_id": doc_id, "product_description": "Item B", "quantity": 2.0}
        ]
        self.mock_db_handler.get_items_for_document.return_value = mock_items_data

        items_list = self.purchase_logic.get_items_for_document(doc_id)

        self.assertEqual(len(items_list), 2)
        self.assertIsInstance(items_list[0], PurchaseDocumentItem)
        self.assertEqual(items_list[0].product_description, "Item A")
        self.mock_db_handler.get_items_for_document.assert_called_with(doc_id)

if __name__ == '__main__':
    unittest.main()
