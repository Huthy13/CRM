import unittest
from unittest.mock import MagicMock, patch
import datetime

# Assuming core.sales_logic and shared.structs are importable
# Add project root to sys.path if necessary for imports, or configure test runner
# For example, if tests are run from project root:
# import sys
# import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.sales_logic import SalesLogic
from shared.structs import (
    SalesDocument, SalesDocumentItem, SalesDocumentStatus, SalesDocumentType,
    Account, AccountType, Product
)

class TestSalesLogic(unittest.TestCase):

    def setUp(self):
        self.mock_db_handler = MagicMock()
        self.sales_logic = SalesLogic(self.mock_db_handler)

    def test_create_quote_success(self):
        mock_customer_id = 1
        mock_notes = "Test quote notes"

        self.mock_db_handler.get_account_details.return_value = {
            "id": mock_customer_id,
            "name": "Test Customer",
            "account_type": AccountType.CUSTOMER.value
        }

        mock_new_doc_id = 100
        self.mock_db_handler.add_sales_document.return_value = mock_new_doc_id

        with patch.object(self.sales_logic, '_generate_sales_document_number', return_value="QUO-20230101-0001") as mock_gen_num:
            self.mock_db_handler.get_sales_document_by_id.return_value = {
                "id": mock_new_doc_id,
                "document_number": "QUO-20230101-0001",
                "customer_id": mock_customer_id,
                "document_type": SalesDocumentType.QUOTE.value,
                "created_date": datetime.datetime.now().isoformat(),
                "expiry_date": (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat(),
                "status": SalesDocumentStatus.QUOTE_DRAFT.value,
                "notes": mock_notes,
                "subtotal": 0.0, "taxes": 0.0, "total_amount": 0.0, "related_quote_id": None
            }

            quote = self.sales_logic.create_quote(customer_id=mock_customer_id, notes=mock_notes)

            self.assertIsNotNone(quote)
            self.assertEqual(quote.id, mock_new_doc_id)
            self.assertEqual(quote.customer_id, mock_customer_id)
            self.assertEqual(quote.notes, mock_notes)
            self.assertEqual(quote.document_type, SalesDocumentType.QUOTE)
            self.assertEqual(quote.status, SalesDocumentStatus.QUOTE_DRAFT)
            mock_gen_num.assert_called_once_with(SalesDocumentType.QUOTE)

            self.mock_db_handler.add_sales_document.assert_called_once()
            call_args = self.mock_db_handler.add_sales_document.call_args[1]
            self.assertEqual(call_args['doc_number'], "QUO-20230101-0001")
            self.assertEqual(call_args['customer_id'], mock_customer_id)
            self.assertEqual(call_args['document_type'], SalesDocumentType.QUOTE.value)
            self.assertEqual(call_args['status'], SalesDocumentStatus.QUOTE_DRAFT.value)
            self.assertEqual(call_args['notes'], mock_notes)
            self.assertTrue(call_args['created_date'].startswith(datetime.date.today().isoformat()))
            self.assertTrue(call_args['expiry_date'].startswith((datetime.date.today() + datetime.timedelta(days=30)).isoformat()[:10]))

    def test_create_quote_customer_not_found(self):
        self.mock_db_handler.get_account_details.return_value = None
        with self.assertRaisesRegex(ValueError, "Customer with ID 999 not found."):
            self.sales_logic.create_quote(customer_id=999)

    def test_create_quote_account_not_customer(self):
        self.mock_db_handler.get_account_details.return_value = {
            "id": 1, "name": "Test Vendor", "account_type": AccountType.VENDOR.value
        }
        with self.assertRaisesRegex(ValueError, "Account ID 1 is not a registered Customer."):
            self.sales_logic.create_quote(customer_id=1)

    def test_add_item_to_sales_document_success_quote_draft(self):
        mock_doc_id = 1
        mock_product_id = 10
        mock_quantity = 2.0
        mock_discount = 10.0

        self.mock_db_handler.get_sales_document_by_id.return_value = {
            "id": mock_doc_id, "customer_id": 1, "document_type": SalesDocumentType.QUOTE.value,
            "status": SalesDocumentStatus.QUOTE_DRAFT.value,
            "document_number": "QUO-TEST-001", "created_date": "2023-01-01T00:00:00",
            "subtotal":0, "taxes":0, "total_amount":0
        }
        self.mock_db_handler.get_product_details.return_value = {
            "product_id": mock_product_id, "name": "Test Product", "sale_price": 100.00
        }
        new_item_id = 50
        self.mock_db_handler.add_sales_document_item.return_value = new_item_id
        # Ensure all expected keys are present for SalesDocumentItem construction
        mock_item_dict = {
            "id": new_item_id, "sales_document_id": mock_doc_id, "product_id": mock_product_id,
            "product_description": "Test Product", "quantity": mock_quantity,
            "unit_price": 100.00, "discount_percentage": mock_discount,
            "line_total": 180.00
        }
        self.mock_db_handler.get_sales_document_item_by_id.return_value = mock_item_dict
        self.mock_db_handler.get_items_for_sales_document.return_value = [mock_item_dict.copy()]

        item = self.sales_logic.add_item_to_sales_document(
            doc_id=mock_doc_id, product_id=mock_product_id, quantity=mock_quantity, discount_percentage=mock_discount)

        self.assertIsNotNone(item)
        self.assertEqual(item.id, new_item_id)
        self.mock_db_handler.add_sales_document_item.assert_called_once()
        call_args = self.mock_db_handler.add_sales_document_item.call_args[1]
        self.assertEqual(call_args['line_total'], 180.00)
        self.mock_db_handler.update_sales_document.assert_called_once()
        update_call_args = self.mock_db_handler.update_sales_document.call_args[0]
        self.assertEqual(update_call_args[1]['total_amount'], 180.00)

    def test_add_item_to_sales_document_product_not_found(self):
        self.mock_db_handler.get_sales_document_by_id.return_value = {
            "id": 1, "status": SalesDocumentStatus.QUOTE_DRAFT.value, "document_type": SalesDocumentType.QUOTE.value,
            "document_number": "QUO-TEST-001", "created_date": "2023-01-01T00:00:00", "customer_id": 1,
            "subtotal":0, "taxes":0, "total_amount":0}
        self.mock_db_handler.get_product_details.return_value = None
        with self.assertRaisesRegex(ValueError, "Product with ID 999 not found."):
            self.sales_logic.add_item_to_sales_document(doc_id=1, product_id=999, quantity=1)

    def test_add_item_to_sales_document_doc_not_found(self):
        self.mock_db_handler.get_sales_document_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, "Sales document with ID 777 not found."):
            self.sales_logic.add_item_to_sales_document(doc_id=777, product_id=1, quantity=1)

    def test_add_item_to_sales_document_invalid_status(self):
        self.mock_db_handler.get_sales_document_by_id.return_value = {
            "id": 1, "status": SalesDocumentStatus.QUOTE_SENT.value, "document_type": SalesDocumentType.QUOTE.value,
            "document_number": "QUO-TEST-001", "created_date": "2023-01-01T00:00:00", "customer_id": 1,
            "subtotal":0, "taxes":0, "total_amount":0}
        self.mock_db_handler.get_product_details.return_value = {"product_id":1, "name":"P", "sale_price":10}
        with self.assertRaisesRegex(ValueError, "Items cannot be added to a document with status 'Quote Sent'."):
            self.sales_logic.add_item_to_sales_document(doc_id=1, product_id=1, quantity=1)

    def test_add_item_to_sales_document_success_so_open(self):
        mock_doc_id = 1
        mock_product_id = 10
        mock_quantity = 2.0
        mock_discount = 10.0

        self.mock_db_handler.get_sales_document_by_id.return_value = {
            "id": mock_doc_id, "customer_id": 1, "document_type": SalesDocumentType.SALES_ORDER.value,
            "status": SalesDocumentStatus.SO_OPEN.value,
            "document_number": "SO-TEST-001", "created_date": "2023-01-01T00:00:00",
            "subtotal":0, "taxes":0, "total_amount":0
        }
        self.mock_db_handler.get_product_details.return_value = {
            "product_id": mock_product_id, "name": "Test Product", "sale_price": 100.00
        }
        new_item_id = 50
        self.mock_db_handler.add_sales_document_item.return_value = new_item_id
        # Ensure all expected keys are present for SalesDocumentItem construction
        mock_item_dict = {
            "id": new_item_id, "sales_document_id": mock_doc_id, "product_id": mock_product_id,
            "product_description": "Test Product", "quantity": mock_quantity,
            "unit_price": 100.00, "discount_percentage": mock_discount,
            "line_total": 180.00
        }
        self.mock_db_handler.get_sales_document_item_by_id.return_value = mock_item_dict
        self.mock_db_handler.get_items_for_sales_document.return_value = [mock_item_dict.copy()]

        item = self.sales_logic.add_item_to_sales_document(
            doc_id=mock_doc_id, product_id=mock_product_id, quantity=mock_quantity, discount_percentage=mock_discount)

        self.assertIsNotNone(item)
        self.assertEqual(item.id, new_item_id)
        self.mock_db_handler.add_sales_document_item.assert_called_once()
        call_args = self.mock_db_handler.add_sales_document_item.call_args[1]
        self.assertEqual(call_args['line_total'], 180.00)
        self.mock_db_handler.update_sales_document.assert_called_once()
        update_call_args = self.mock_db_handler.update_sales_document.call_args[0]
        self.assertEqual(update_call_args[1]['total_amount'], 180.00)

    def test_add_item_to_sales_document_no_sale_price(self):
        self.mock_db_handler.get_sales_document_by_id.return_value = {
            "id": 1, "status": SalesDocumentStatus.QUOTE_DRAFT.value, "document_type": SalesDocumentType.QUOTE.value,
            "document_number": "QUO-TEST-001", "created_date": "2023-01-01T00:00:00", "customer_id": 1,
            "subtotal":0, "taxes":0, "total_amount":0}
        self.mock_db_handler.get_product_details.return_value = {"product_id": 1, "name": "Test Product", "sale_price": None}
        with self.assertRaisesRegex(ValueError, "Sale price for product ID 1 not found and no override provided."):
            self.sales_logic.add_item_to_sales_document(doc_id=1, product_id=1, quantity=1)

    def test_update_sales_document_item_success(self):
        mock_item_id = 10
        mock_doc_id = 1
        mock_product_id = 20
        new_quantity = 3.0
        new_unit_price = 150.0
        new_discount = 5.0

        initial_item_data = {
            "id": mock_item_id, "sales_document_id": mock_doc_id, "product_id": 10,
            "product_description": "Old Product Name", "quantity": 1.0,
            "unit_price": 100.00, "discount_percentage": 0.0, "line_total": 100.00
        }
        updated_item_data = {
            "id": mock_item_id, "sales_document_id": mock_doc_id, "product_id": mock_product_id,
            "product_description": "New Product Name", "quantity": new_quantity,
            "unit_price": new_unit_price, "discount_percentage": new_discount,
            "line_total": new_quantity * new_unit_price * (1 - new_discount / 100.0)
        }

        self.mock_db_handler.get_sales_document_item_by_id.side_effect = [
            initial_item_data, # For the first call in update_sales_document_item
            updated_item_data  # For the call to get_sales_document_item_details at the end
        ]
        self.mock_db_handler.get_sales_document_by_id.return_value = { "id": mock_doc_id, "status": SalesDocumentStatus.QUOTE_DRAFT.value, "document_type": SalesDocumentType.QUOTE.value, "customer_id": 1, "document_number": "Q", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0}
        self.mock_db_handler.get_product_details.return_value = {"product_id": mock_product_id, "name": "New Product Name", "sale_price": new_unit_price}
        expected_line_total = new_quantity * new_unit_price * (1 - new_discount / 100.0)
        self.mock_db_handler.get_items_for_sales_document.return_value = [updated_item_data.copy()] # Simulates items after update

        updated_item = self.sales_logic.update_sales_document_item(item_id=mock_item_id, product_id=mock_product_id, quantity=new_quantity, unit_price_override=new_unit_price, discount_percentage=new_discount)
        self.assertIsNotNone(updated_item)
        self.assertAlmostEqual(updated_item.line_total, expected_line_total)
        self.mock_db_handler.update_sales_document_item.assert_called_once()
        self.mock_db_handler.update_sales_document.assert_called_once()

    def test_update_sales_document_item_item_not_found(self):
        self.mock_db_handler.get_sales_document_item_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, "Item with ID 999 not found for update."):
            self.sales_logic.update_sales_document_item(item_id=999, product_id=1, quantity=1, unit_price_override=10.0)

    def test_update_sales_document_item_invalid_status(self):
        mock_item_id = 10
        mock_doc_id = 1
        self.mock_db_handler.get_sales_document_item_by_id.return_value = {
            "id": mock_item_id, "sales_document_id": mock_doc_id, "product_id": 10,
            "product_description": "Any Desc", "quantity": 1.0, "unit_price": 100.00,
            "discount_percentage": 0.0, "line_total": 100.00
        }
        self.mock_db_handler.get_sales_document_by_id.return_value = {"id": mock_doc_id, "status": SalesDocumentStatus.INVOICE_PAID.value, "document_type":SalesDocumentType.INVOICE.value, "customer_id":1, "document_number":"I", "created_date":"d","subtotal":0,"taxes":0,"total_amount":0}
        self.mock_db_handler.get_product_details.return_value = {"product_id":1, "name":"P", "sale_price":10}
        with self.assertRaisesRegex(ValueError, "Items cannot be modified for a document with status 'Invoice Paid'."):
            self.sales_logic.update_sales_document_item(item_id=mock_item_id, product_id=1, quantity=2, unit_price_override=20.0)

    def test_convert_quote_to_sales_order_success(self):
        mock_quote_id = 1
        mock_customer_id = 5
        mock_quote_data = {"id": mock_quote_id, "document_number": "QUO-001", "customer_id": mock_customer_id, "document_type": SalesDocumentType.QUOTE.value, "created_date": "date", "status": SalesDocumentStatus.QUOTE_ACCEPTED.value, "notes": "N", "subtotal": 200.0, "taxes": 20.0, "total_amount": 220.0}

        self.mock_db_handler.get_sales_document_by_id.side_effect = [mock_quote_data, {**mock_quote_data, "document_type": SalesDocumentType.SALES_ORDER.value, "status": SalesDocumentStatus.SO_OPEN.value}]

        sales_order = self.sales_logic.convert_quote_to_sales_order(mock_quote_id)

        self.assertIsNotNone(sales_order)
        self.assertEqual(sales_order.id, mock_quote_id)
        self.assertEqual(sales_order.document_type, SalesDocumentType.SALES_ORDER)
        self.assertEqual(sales_order.status, SalesDocumentStatus.SO_OPEN)
        self.mock_db_handler.update_sales_document.assert_called_once_with(mock_quote_id, {"document_type": SalesDocumentType.SALES_ORDER.value, "status": SalesDocumentStatus.SO_OPEN.value})

    def test_convert_quote_to_sales_order_quote_not_found(self):
        self.mock_db_handler.get_sales_document_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, "Quote with ID 999 not found."):
            self.sales_logic.convert_quote_to_sales_order(999)

    def test_convert_quote_to_sales_order_not_a_quote(self):
        self.mock_db_handler.get_sales_document_by_id.return_value = {"id": 1, "document_type": SalesDocumentType.INVOICE.value, "status": SalesDocumentStatus.INVOICE_DRAFT.value, "customer_id":1, "document_number":"I", "created_date":"d","subtotal":0,"taxes":0,"total_amount":0}
        with self.assertRaisesRegex(ValueError, "Document ID 1 is not a Quote."):
            self.sales_logic.convert_quote_to_sales_order(1)

    def test_convert_sales_order_to_invoice_success(self):
        mock_so_id = 1
        mock_customer_id = 5
        mock_so_data = {"id": mock_so_id, "document_number": "SO-001", "customer_id": mock_customer_id, "document_type": SalesDocumentType.SALES_ORDER.value, "created_date": "date", "status": SalesDocumentStatus.SO_FULFILLED.value, "notes": "N", "subtotal": 200.0, "taxes": 20.0, "total_amount": 220.0}
        mock_so_item_data = [{"id": 10, "sales_document_id": mock_so_id, "product_id": 100, "product_description": "Item 1", "quantity": 2.0, "unit_price": 100.0, "discount_percentage": 0.0, "line_total": 200.0}]
        new_invoice_id = 2

        self.mock_db_handler.get_sales_document_by_id.side_effect = [mock_so_data, {"id": new_invoice_id, "document_number": "INV-001", "customer_id": mock_customer_id, "document_type": SalesDocumentType.INVOICE.value, "status": SalesDocumentStatus.INVOICE_DRAFT.value, "related_quote_id":mock_so_id, "total_amount":220.0, "created_date":"d"}]
        self.mock_db_handler.get_items_for_sales_document.side_effect = [[{k:v for k,v in item.items()} for item in mock_so_item_data], [{**item, "sales_document_id":new_invoice_id} for item in mock_so_item_data]]
        self.mock_db_handler.add_sales_document.return_value = new_invoice_id
        self.mock_db_handler.add_sales_document_item.return_value = 20

        with patch.object(self.sales_logic, '_generate_sales_document_number', return_value="INV-001") as mock_gen_num:
            invoice = self.sales_logic.convert_sales_order_to_invoice(mock_so_id)
            self.assertIsNotNone(invoice)
            self.assertEqual(invoice.id, new_invoice_id)
            self.assertEqual(invoice.document_type, SalesDocumentType.INVOICE)
            mock_gen_num.assert_called_once_with(SalesDocumentType.INVOICE)
            self.mock_db_handler.add_sales_document.assert_called_once()
            self.mock_db_handler.add_sales_document_item.assert_called_once()
            self.mock_db_handler.update_sales_document.assert_called_once()

    def test_update_sales_document_status_success(self):
        mock_doc_id = 1
        new_status = SalesDocumentStatus.QUOTE_SENT
        self.mock_db_handler.get_sales_document_by_id.side_effect = [
            {"id": mock_doc_id, "document_type": SalesDocumentType.QUOTE.value, "status": SalesDocumentStatus.QUOTE_DRAFT.value, "customer_id":1, "document_number":"Q", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0},
            {"id": mock_doc_id, "document_type": SalesDocumentType.QUOTE.value, "status": new_status.value, "customer_id":1, "document_number":"Q", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0}
        ]
        updated_doc = self.sales_logic.update_sales_document_status(mock_doc_id, new_status)
        self.assertEqual(updated_doc.status, new_status)
        self.mock_db_handler.update_sales_document.assert_called_once_with(mock_doc_id, {"status": new_status.value})

    def test_update_sales_document_status_doc_not_found(self):
        self.mock_db_handler.get_sales_document_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, "Document with ID 999 not found for status update."):
            self.sales_logic.update_sales_document_status(999, SalesDocumentStatus.QUOTE_SENT)

    def test_update_sales_document_status_invalid_transition_for_paid_invoice(self):
        mock_doc_id = 1
        self.mock_db_handler.get_sales_document_by_id.return_value = {"id": mock_doc_id, "document_type": SalesDocumentType.INVOICE.value, "status": SalesDocumentStatus.INVOICE_PAID.value, "customer_id":1, "document_number":"I", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0}
        with self.assertRaisesRegex(ValueError, "Cannot change status of a paid invoice, except to void it."):
            self.sales_logic.update_sales_document_status(mock_doc_id, SalesDocumentStatus.INVOICE_DRAFT)

    def test_update_sales_document_status_void_paid_invoice(self):
        mock_doc_id = 1
        self.mock_db_handler.get_sales_document_by_id.side_effect = [
            {"id": mock_doc_id, "document_type": SalesDocumentType.INVOICE.value, "status": SalesDocumentStatus.INVOICE_PAID.value, "customer_id":1, "document_number":"I", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0},
            {"id": mock_doc_id, "document_type": SalesDocumentType.INVOICE.value, "status": SalesDocumentStatus.INVOICE_VOID.value, "customer_id":1, "document_number":"I", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0}
        ]
        updated_doc = self.sales_logic.update_sales_document_status(mock_doc_id, SalesDocumentStatus.INVOICE_VOID)
        self.assertEqual(updated_doc.status, SalesDocumentStatus.INVOICE_VOID)
        self.mock_db_handler.update_sales_document.assert_called_once_with(mock_doc_id, {"status": SalesDocumentStatus.INVOICE_VOID.value})

    def test_update_sales_document_status_invalid_status_for_doc_type(self):
        mock_doc_id = 1
        self.mock_db_handler.get_sales_document_by_id.return_value = {"id": mock_doc_id, "document_type": SalesDocumentType.QUOTE.value, "status": SalesDocumentStatus.QUOTE_DRAFT.value, "customer_id":1, "document_number":"Q", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0}
        with self.assertRaisesRegex(ValueError, "Invalid status 'Invoice Sent' for a Quote."):
            self.sales_logic.update_sales_document_status(mock_doc_id, SalesDocumentStatus.INVOICE_SENT)

        self.mock_db_handler.get_sales_document_by_id.return_value = {"id": mock_doc_id, "document_type": SalesDocumentType.SALES_ORDER.value, "status": SalesDocumentStatus.SO_OPEN.value, "customer_id":1, "document_number":"SO", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0}
        with self.assertRaisesRegex(ValueError, "Invalid status 'Invoice Sent' for a Sales Order."):
            self.sales_logic.update_sales_document_status(mock_doc_id, SalesDocumentStatus.INVOICE_SENT)

    def test_delete_sales_document_item_success(self):
        mock_item_id = 1
        mock_doc_id = 100
        self.mock_db_handler.get_sales_document_item_by_id.return_value = {
            "id": mock_item_id, "sales_document_id": mock_doc_id, "product_id": 1,
            "product_description": "Desc", "quantity": 1.0, "unit_price": 50.0,
            "discount_percentage": 0.0, "line_total": 50.0
        }
        self.mock_db_handler.get_sales_document_by_id.return_value = {"id": mock_doc_id, "status": SalesDocumentStatus.QUOTE_DRAFT.value, "document_type": SalesDocumentType.QUOTE.value, "customer_id":1, "document_number":"Q", "created_date":"d", "subtotal":100,"taxes":0,"total_amount":100}
        self.mock_db_handler.get_items_for_sales_document.return_value = [] # After deletion

        self.sales_logic.delete_sales_document_item(mock_item_id)
        self.mock_db_handler.delete_sales_document_item.assert_called_once_with(mock_item_id)
        self.mock_db_handler.update_sales_document.assert_called_once()
        update_call_args = self.mock_db_handler.update_sales_document.call_args[0]
        self.assertEqual(update_call_args[1]['subtotal'], 0)

    def test_delete_sales_document_item_not_found(self):
        self.mock_db_handler.get_sales_document_item_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, f"Sales document item with ID 999 not found."):
            self.sales_logic.delete_sales_document_item(999)

    def test_delete_sales_document_item_invalid_status(self):
        mock_item_id = 1
        mock_doc_id = 100
        self.mock_db_handler.get_sales_document_item_by_id.return_value = {
            "id": mock_item_id, "sales_document_id": mock_doc_id, "product_id": 1,
            "product_description": "Desc", "quantity": 1.0, "unit_price": 50.0,
            "discount_percentage": 0.0, "line_total": 50.0
        }
        self.mock_db_handler.get_sales_document_by_id.return_value = {"id": mock_doc_id, "status": SalesDocumentStatus.INVOICE_SENT.value, "document_type":SalesDocumentType.INVOICE.value, "customer_id":1, "document_number":"I", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0}
        with self.assertRaisesRegex(ValueError, "Items cannot be deleted from a document with status 'Invoice Sent'."):
            self.sales_logic.delete_sales_document_item(mock_item_id)

    def test_delete_sales_document_success_no_items(self):
        mock_doc_id = 1
        self.mock_db_handler.get_sales_document_by_id.return_value = {"id": mock_doc_id, "status": SalesDocumentStatus.QUOTE_DRAFT.value, "document_type":SalesDocumentType.QUOTE.value, "customer_id":1, "document_number":"Q", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0}
        self.mock_db_handler.get_items_for_sales_document.return_value = [] # No items
        self.sales_logic.delete_sales_document(mock_doc_id)
        self.mock_db_handler.delete_sales_document.assert_called_once_with(mock_doc_id)
        self.mock_db_handler.delete_sales_document_item.assert_not_called()

    def test_delete_sales_document_success_with_items_draft_status(self):
        mock_doc_id = 1
        mock_item_id1 = 10
        mock_item_id2 = 11
        self.mock_db_handler.get_sales_document_by_id.return_value = {"id": mock_doc_id, "status": SalesDocumentStatus.QUOTE_DRAFT.value, "document_type":SalesDocumentType.QUOTE.value, "customer_id":1, "document_number":"Q", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0}
        mock_items_list = [
            {"id": mock_item_id1, "sales_document_id": mock_doc_id, "product_id": 1, "product_description": "Item 1", "quantity": 1, "unit_price": 10, "discount_percentage": 0, "line_total": 10},
            {"id": mock_item_id2, "sales_document_id": mock_doc_id, "product_id": 2, "product_description": "Item 2", "quantity": 2, "unit_price": 20, "discount_percentage": 0, "line_total": 40}
        ]
        self.mock_db_handler.get_items_for_sales_document.return_value = mock_items_list
        self.sales_logic.delete_sales_document(mock_doc_id)
        self.assertEqual(self.mock_db_handler.delete_sales_document_item.call_count, 2)
        self.mock_db_handler.delete_sales_document_item.assert_any_call(mock_item_id1)
        self.mock_db_handler.delete_sales_document_item.assert_any_call(mock_item_id2)
        self.mock_db_handler.delete_sales_document.assert_called_once_with(mock_doc_id)

    def test_delete_sales_document_not_found(self):
        self.mock_db_handler.get_sales_document_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, "Sales document with ID 999 not found."):
            self.sales_logic.delete_sales_document(999)

    def test_delete_sales_document_with_items_invalid_status(self):
        mock_doc_id = 1
        self.mock_db_handler.get_sales_document_by_id.return_value = {"id": mock_doc_id, "status": SalesDocumentStatus.INVOICE_SENT.value, "document_type":SalesDocumentType.INVOICE.value, "customer_id":1, "document_number":"I", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0}
        self.mock_db_handler.get_items_for_sales_document.return_value = [ # Ensure items have all keys
            {"id": 10, "sales_document_id": mock_doc_id, "product_id": 1, "product_description": "Item 1", "quantity": 1, "unit_price": 10, "discount_percentage": 0, "line_total": 10}
        ]
        with self.assertRaisesRegex(ValueError, "Cannot delete document with status 'Invoice Sent' that has items. Consider voiding first."):
            self.sales_logic.delete_sales_document(mock_doc_id)
        self.mock_db_handler.delete_sales_document_item.assert_not_called()
        self.mock_db_handler.delete_sales_document.assert_not_called()

if __name__ == '__main__':
    unittest.main()
