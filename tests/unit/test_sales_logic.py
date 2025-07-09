import unittest
from unittest.mock import MagicMock, patch, call
import datetime

# Assuming paths are set up for imports from core and shared
from core.logic.sales_logic import SalesLogic
from shared.structs import SalesDocument, SalesDocumentItem, Product # For type hinting and creating test objects
from core.database import DatabaseHandler # For type hinting mocks

class TestSalesLogic(unittest.TestCase):

    def setUp(self):
        self.mock_db_handler = MagicMock(spec=DatabaseHandler)
        self.sales_logic = SalesLogic(self.mock_db_handler)

    def test_create_sales_document_success(self):
        self.mock_db_handler.get_product_price_for_sales_document.side_effect = [10.00, 20.00] # Prices for 2 items
        self.mock_db_handler.add_sales_document.return_value = 1 # New document ID
        self.mock_db_handler.add_sales_document_item.return_value = 101 # Dummy item ID, not strictly checked here

        customer_id = 1
        doc_date = datetime.date(2024, 1, 15)
        status = "Draft"
        items_data = [
            {'product_id': 10, 'quantity': 2}, # Total 2 * 10.00 = 20.00
            {'product_id': 20, 'quantity': 3}  # Total 3 * 20.00 = 60.00
        ]
        # Expected total_amount = 80.00

        new_doc_id = self.sales_logic.create_sales_document(customer_id, doc_date, status, items_data)

        self.assertEqual(new_doc_id, 1)
        self.mock_db_handler.add_sales_document.assert_called_once_with(
            customer_id=customer_id,
            document_date=doc_date.isoformat(),
            status=status,
            total_amount=80.00
        )
        self.assertEqual(self.mock_db_handler.add_sales_document_item.call_count, 2)
        self.mock_db_handler.add_sales_document_item.assert_any_call(
            document_id=1, product_id=10, quantity=2, unit_price=10.00, line_total=20.00
        )
        self.mock_db_handler.add_sales_document_item.assert_any_call(
            document_id=1, product_id=20, quantity=3, unit_price=20.00, line_total=60.00
        )

    def test_create_sales_document_invalid_item_data(self):
        result = self.sales_logic.create_sales_document(1, datetime.date.today(), "Draft", [{'product_id': 1, 'quantity': 0}])
        self.assertIsNone(result)
        self.mock_db_handler.add_sales_document.assert_not_called()

    def test_create_sales_document_product_price_not_found(self):
        self.mock_db_handler.get_product_price_for_sales_document.return_value = None
        items_data = [{'product_id': 99, 'quantity': 1}]
        result = self.sales_logic.create_sales_document(1, datetime.date.today(), "Draft", items_data)
        self.assertIsNone(result)
        self.mock_db_handler.get_product_price_for_sales_document.assert_called_once_with(99)
        self.mock_db_handler.add_sales_document.assert_not_called()

    def test_get_sales_document_details_found(self):
        doc_id = 1
        db_doc_data = {
            'document_id': doc_id, 'customer_id': 10, 'document_date': '2024-01-15',
            'status': 'Sent', 'total_amount': 100.00, 'customer_name': 'Test Customer'
        }
        db_items_data = [
            {'item_id': 101, 'document_id': doc_id, 'product_id': 100, 'quantity': 2, 'unit_price': 25.00, 'line_total': 50.00, 'product_name': 'Product A'},
            {'item_id': 102, 'document_id': doc_id, 'product_id': 200, 'quantity': 1, 'unit_price': 50.00, 'line_total': 50.00, 'product_name': 'Product B'}
        ]
        self.mock_db_handler.get_sales_document.return_value = db_doc_data
        self.mock_db_handler.get_sales_document_items.return_value = db_items_data

        result_doc = self.sales_logic.get_sales_document_details(doc_id)

        self.assertIsNotNone(result_doc)
        self.assertIsInstance(result_doc, SalesDocument)
        self.assertEqual(result_doc.document_id, doc_id)
        self.assertEqual(result_doc.status, 'Sent')
        self.assertEqual(len(result_doc.items), 2)
        self.assertIsInstance(result_doc.items[0], SalesDocumentItem)
        self.assertEqual(result_doc.items[0].product_id, 100)

        self.mock_db_handler.get_sales_document.assert_called_once_with(doc_id)
        self.mock_db_handler.get_sales_document_items.assert_called_once_with(doc_id)


    def test_get_sales_document_details_not_found(self):
        self.mock_db_handler.get_sales_document.return_value = None
        result = self.sales_logic.get_sales_document_details(999)
        self.assertIsNone(result)
        self.mock_db_handler.get_sales_document.assert_called_once_with(999)
        self.mock_db_handler.get_sales_document_items.assert_not_called()

    def test_get_all_sales_documents(self):
        db_docs_data = [
            {'document_id': 1, 'customer_id': 10, 'document_date': '2024-01-15', 'status': 'Sent', 'total_amount': 100.00, 'customer_name': 'Cust A'},
            {'document_id': 2, 'customer_id': 20, 'document_date': '2024-01-16', 'status': 'Draft', 'total_amount': 200.00, 'customer_name': 'Cust B'}
        ]
        # Note: SalesLogic.get_all_sales_documents converts these dicts to SalesDocument structs.
        # The mock should return what the DB method returns.
        self.mock_db_handler.get_all_sales_documents.return_value = db_docs_data

        results = self.sales_logic.get_all_sales_documents()

        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], SalesDocument)
        self.assertEqual(results[0].document_id, 1)
        self.mock_db_handler.get_all_sales_documents.assert_called_once_with(customer_id=None)

    def test_update_sales_document_status_success(self):
        doc_id = 1
        original_doc_data = {'document_id': doc_id, 'customer_id': 1, 'document_date': '2024-01-01', 'status': 'Draft', 'total_amount': 100.0}
        self.mock_db_handler.get_sales_document.return_value = original_doc_data

        success = self.sales_logic.update_sales_document_status(doc_id, "Sent")

        self.assertTrue(success)
        self.mock_db_handler.get_sales_document.assert_called_once_with(doc_id)
        self.mock_db_handler.update_sales_document.assert_called_once_with(
            document_id=doc_id,
            customer_id=original_doc_data['customer_id'],
            document_date=original_doc_data['document_date'],
            status="Sent", # New status
            total_amount=original_doc_data['total_amount']
        )

    def test_update_sales_document_status_doc_not_found(self):
        self.mock_db_handler.get_sales_document.return_value = None
        success = self.sales_logic.update_sales_document_status(99, "Sent")
        self.assertFalse(success)
        self.mock_db_handler.update_sales_document.assert_not_called()

    def test_delete_sales_document_success(self):
        self.sales_logic.delete_sales_document(1)
        self.mock_db_handler.delete_sales_document.assert_called_once_with(1)

    def test_update_sales_document_items_success(self):
        doc_id = 1
        original_doc_data = {'document_id': doc_id, 'customer_id': 1, 'document_date': '2024-01-01', 'status': 'Draft', 'total_amount': 0.0}
        self.mock_db_handler.get_sales_document.return_value = original_doc_data
        self.mock_db_handler.get_sales_document_items.return_value = [ # Simulate one old item
             {'item_id': 100, 'document_id': doc_id, 'product_id': 10, 'quantity': 1, 'unit_price': 10.0, 'line_total': 10.0}
        ]
        self.mock_db_handler.get_product_price_for_sales_document.return_value = 5.0 # Price for new item

        new_items_data = [{'product_id': 20, 'quantity': 2}] # Expected total: 2 * 5.0 = 10.0

        success = self.sales_logic.update_sales_document_items(doc_id, new_items_data)

        self.assertTrue(success)
        self.mock_db_handler.delete_sales_document_item.assert_called_once_with(100) # Old item deleted
        self.mock_db_handler.add_sales_document_item.assert_called_once_with(
            document_id=doc_id, product_id=20, quantity=2, unit_price=5.0, line_total=10.0
        )
        # Check that the document header (total) was updated
        self.mock_db_handler.update_sales_document.assert_called_once_with(
            document_id=doc_id,
            customer_id=original_doc_data['customer_id'],
            document_date=original_doc_data['document_date'],
            status=original_doc_data['status'],
            total_amount=10.0 # New total
        )

    def test_add_item_to_sales_document_success(self):
        doc_id = 1
        original_doc_data = {'document_id': doc_id, 'customer_id': 1, 'document_date': '2024-01-01', 'status': 'Draft', 'total_amount': 50.0}
        self.mock_db_handler.get_sales_document.return_value = original_doc_data
        self.mock_db_handler.get_product_price_for_sales_document.return_value = 15.0 # Price for new item

        success = self.sales_logic.add_item_to_sales_document(doc_id, product_id=30, quantity=1)

        self.assertTrue(success)
        self.mock_db_handler.add_sales_document_item.assert_called_once_with(
            doc_id, 30, 1, 15.0, 15.0
        )
        self.mock_db_handler.update_sales_document.assert_called_once_with(
            document_id=doc_id,
            customer_id=original_doc_data['customer_id'],
            document_date=original_doc_data['document_date'],
            status=original_doc_data['status'],
            total_amount=65.0 # 50.0 (original) + 15.0 (new item)
        )

    def test_remove_item_from_sales_document_success(self):
        doc_id = 1
        item_id_to_remove = 101
        item_to_delete_data = {'item_id': item_id_to_remove, 'document_id': doc_id, 'product_id': 1, 'quantity': 2, 'unit_price': 10.0, 'line_total': 20.0}
        original_doc_data = {'document_id': doc_id, 'customer_id': 1, 'document_date': '2024-01-01', 'status': 'Draft', 'total_amount': 100.0}

        self.mock_db_handler.get_sales_document_item.return_value = item_to_delete_data
        self.mock_db_handler.get_sales_document.return_value = original_doc_data

        success = self.sales_logic.remove_item_from_sales_document(item_id_to_remove)

        self.assertTrue(success)
        self.mock_db_handler.delete_sales_document_item.assert_called_once_with(item_id_to_remove)
        self.mock_db_handler.update_sales_document.assert_called_once_with(
            document_id=doc_id,
            customer_id=original_doc_data['customer_id'],
            document_date=original_doc_data['document_date'],
            status=original_doc_data['status'],
            total_amount=80.0 # 100.0 (original) - 20.0 (removed item)
        )

    def test_update_document_item_quantity_success(self):
        doc_id = 1
        item_id_to_update = 101
        new_quantity = 3

        original_item_data = {'item_id': item_id_to_update, 'document_id': doc_id, 'product_id': 1, 'quantity': 2, 'unit_price': 10.0, 'line_total': 20.0}
        original_doc_data = {'document_id': doc_id, 'customer_id': 1, 'document_date': '2024-01-01', 'status': 'Draft', 'total_amount': 100.0}

        self.mock_db_handler.get_sales_document_item.return_value = original_item_data
        self.mock_db_handler.get_sales_document.return_value = original_doc_data

        success = self.sales_logic.update_document_item_quantity(item_id_to_update, new_quantity)

        self.assertTrue(success)
        expected_new_line_total = new_quantity * original_item_data['unit_price'] # 3 * 10.0 = 30.0
        self.mock_db_handler.update_sales_document_item.assert_called_once_with(
            item_id=item_id_to_update,
            product_id=original_item_data['product_id'],
            quantity=new_quantity,
            unit_price=original_item_data['unit_price'],
            line_total=expected_new_line_total
        )

        # Original total 100. Original item total 20. New item total 30.
        # New document total = 100 - 20 + 30 = 110
        expected_new_doc_total = original_doc_data['total_amount'] - original_item_data['line_total'] + expected_new_line_total
        self.mock_db_handler.update_sales_document.assert_called_once_with(
            document_id=doc_id,
            customer_id=original_doc_data['customer_id'],
            document_date=original_doc_data['document_date'],
            status=original_doc_data['status'],
            total_amount=expected_new_doc_total
        )

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
