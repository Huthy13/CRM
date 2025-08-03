import unittest
from unittest.mock import MagicMock, patch, call
import datetime
import os
import tempfile
import zlib

# Assuming core.sales_logic and shared.structs are importable
# Add project root to sys.path if necessary for imports, or configure test runner
# For example, if tests are run from project root:
# import sys
# import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.sales_logic import SalesLogic
from core.database import DatabaseHandler
from core.address_book_logic import AddressBookLogic
from shared.structs import (
    SalesDocument,
    SalesDocumentItem,
    SalesDocumentStatus,
    SalesDocumentType,
    Account,
    AccountType,
    Product,
    InventoryTransactionType,
    Address,
)
from core.packing_slip_generator import generate_packing_slip_pdf

class TestSalesLogic(unittest.TestCase):

    def setUp(self):
        self.mock_db_handler = MagicMock()
        self.sales_logic = SalesLogic(self.mock_db_handler)

    def test_exposes_db_handler(self):
        self.assertIs(self.sales_logic.db, self.mock_db_handler)

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

        prefs = {'require_reference_on_quote_accept': False, 'default_quote_expiry_days': 30}
        with patch.object(self.sales_logic, '_generate_sales_document_number', return_value="S00000") as mock_gen_num, \
             patch('core.sales_logic.load_preferences', return_value=prefs):
            self.mock_db_handler.get_sales_document_by_id.return_value = {
                "id": mock_new_doc_id,
                "document_number": "S00000",
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
            self.assertEqual(call_args['doc_number'], "S00000")
            self.assertEqual(call_args['customer_id'], mock_customer_id)
            self.assertEqual(call_args['document_type'], SalesDocumentType.QUOTE.value)
            self.assertEqual(call_args['status'], SalesDocumentStatus.QUOTE_DRAFT.value)
            self.assertEqual(call_args['notes'], mock_notes)
            self.assertTrue(call_args['created_date'].startswith(datetime.date.today().isoformat()))
            self.assertTrue(call_args['expiry_date'].startswith((datetime.date.today() + datetime.timedelta(days=30)).isoformat()[:10]))

    def test_create_quote_respects_expiry_preference(self):
        mock_customer_id = 1
        self.mock_db_handler.get_account_details.return_value = {
            "id": mock_customer_id,
            "name": "Test Customer",
            "account_type": AccountType.CUSTOMER.value,
        }
        mock_new_doc_id = 101
        self.mock_db_handler.add_sales_document.return_value = mock_new_doc_id
        prefs = {'require_reference_on_quote_accept': False, 'default_quote_expiry_days': 45}
        with patch.object(self.sales_logic, '_generate_sales_document_number', return_value="S00001") as mock_gen_num, \
             patch('core.sales_logic.load_preferences', return_value=prefs):
            self.mock_db_handler.get_sales_document_by_id.return_value = {
                "id": mock_new_doc_id,
                "document_number": "S00001",
                "customer_id": mock_customer_id,
                "document_type": SalesDocumentType.QUOTE.value,
                "created_date": datetime.datetime.now().isoformat(),
                "expiry_date": (datetime.datetime.now() + datetime.timedelta(days=45)).isoformat(),
                "status": SalesDocumentStatus.QUOTE_DRAFT.value,
                "notes": None,
                "subtotal": 0.0, "taxes": 0.0, "total_amount": 0.0, "related_quote_id": None
            }

            self.sales_logic.create_quote(customer_id=mock_customer_id)

            call_args = self.mock_db_handler.add_sales_document.call_args[1]
            self.assertTrue(
                call_args['expiry_date'].startswith(
                    (datetime.date.today() + datetime.timedelta(days=45)).isoformat()[:10]
                )
            )

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
            "document_number": "S00000", "created_date": "2023-01-01T00:00:00",
            "subtotal":0, "taxes":0, "total_amount":0
        }
        self.mock_db_handler.get_product_details.return_value = {
            "product_id": mock_product_id, "name": "Test Product", "sale_price": 100.00, "cost": 80.0
        }
        new_item_id = 50
        self.mock_db_handler.add_sales_document_item.return_value = new_item_id
        # Ensure all expected keys are present for SalesDocumentItem construction
        mock_item_dict = {
            "id": new_item_id, "sales_document_id": mock_doc_id, "product_id": mock_product_id,
            "product_description": "Test Product", "quantity": mock_quantity,
            "unit_price": 100.00, "discount_percentage": mock_discount,
            "line_total": 180.00, "note": None
        }
        self.mock_db_handler.get_sales_document_item_by_id.return_value = mock_item_dict
        self.mock_db_handler.get_items_for_sales_document.return_value = [mock_item_dict.copy()]

        mock_address_book_logic_instance = MagicMock()
        mock_customer = MagicMock()
        mock_customer.pricing_rule_id = None
        mock_address_book_logic_instance.get_account_details.return_value = mock_customer

        with patch('core.sales_logic.AddressBookLogic', return_value=mock_address_book_logic_instance):
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
            "document_number": "S00000", "created_date": "2023-01-01T00:00:00", "customer_id": 1,
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
            "document_number": "S00000", "created_date": "2023-01-01T00:00:00", "customer_id": 1,
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
            "document_number": "S00000", "created_date": "2023-01-01T00:00:00",
            "subtotal":0, "taxes":0, "total_amount":0
        }
        self.mock_db_handler.get_product_details.return_value = {
            "product_id": mock_product_id, "name": "Test Product", "sale_price": 100.00, "cost": 80.0
        }
        new_item_id = 50
        self.mock_db_handler.add_sales_document_item.return_value = new_item_id
        # Ensure all expected keys are present for SalesDocumentItem construction
        mock_item_dict = {
            "id": new_item_id, "sales_document_id": mock_doc_id, "product_id": mock_product_id,
            "product_description": "Test Product", "quantity": mock_quantity,
            "unit_price": 100.00, "discount_percentage": mock_discount,
            "line_total": 180.00, "note": None
        }
        self.mock_db_handler.get_sales_document_item_by_id.return_value = mock_item_dict
        self.mock_db_handler.get_items_for_sales_document.return_value = [mock_item_dict.copy()]

        mock_address_book_logic_instance = MagicMock()
        mock_customer = MagicMock()
        mock_customer.pricing_rule_id = None
        mock_address_book_logic_instance.get_account_details.return_value = mock_customer

        with patch('core.sales_logic.AddressBookLogic', return_value=mock_address_book_logic_instance):
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
            "document_number": "S00000", "created_date": "2023-01-01T00:00:00", "customer_id": 1,
            "subtotal":0, "taxes":0, "total_amount":0}
        self.mock_db_handler.get_product_details.return_value = {"product_id": 1, "name": "Test Product", "sale_price": None, "cost": None}

        mock_address_book_logic_instance = MagicMock()
        mock_customer = MagicMock()
        mock_customer.pricing_rule_id = None
        mock_address_book_logic_instance.get_account_details.return_value = mock_customer

        with patch('core.sales_logic.AddressBookLogic', return_value=mock_address_book_logic_instance):
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
            "unit_price": 100.00, "discount_percentage": 0.0, "line_total": 100.00, "note": None
        }
        updated_item_data = {
            "id": mock_item_id, "sales_document_id": mock_doc_id, "product_id": mock_product_id,
            "product_description": "New Product Name", "quantity": new_quantity,
            "unit_price": new_unit_price, "discount_percentage": new_discount,
            "line_total": new_quantity * new_unit_price * (1 - new_discount / 100.0), "note": None
        }

        self.mock_db_handler.get_sales_document_item_by_id.side_effect = [
            initial_item_data, # For the first call in update_sales_document_item
            updated_item_data  # For the call to get_sales_document_item_details at the end
        ]
        self.mock_db_handler.get_sales_document_by_id.return_value = { "id": mock_doc_id, "status": SalesDocumentStatus.QUOTE_DRAFT.value, "document_type": SalesDocumentType.QUOTE.value, "customer_id": 1, "document_number": "S00000", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0}
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
            "discount_percentage": 0.0, "line_total": 100.00, "note": None
        }
        self.mock_db_handler.get_sales_document_by_id.return_value = {"id": mock_doc_id, "status": SalesDocumentStatus.INVOICE_PAID.value, "document_type":SalesDocumentType.INVOICE.value, "customer_id":1, "document_number":"I", "created_date":"d","subtotal":0,"taxes":0,"total_amount":0}
        self.mock_db_handler.get_product_details.return_value = {"product_id":1, "name":"P", "sale_price":10}
        with self.assertRaisesRegex(ValueError, "Items cannot be modified for a document with status 'Invoice Paid'."):
            self.sales_logic.update_sales_document_item(item_id=mock_item_id, product_id=1, quantity=2, unit_price_override=20.0)

    def test_convert_quote_to_sales_order_success(self):
        mock_quote_id = 1
        mock_customer_id = 5
        mock_quote_data = {"id": mock_quote_id, "document_number": "S00000", "customer_id": mock_customer_id, "document_type": SalesDocumentType.QUOTE.value, "created_date": "date", "status": SalesDocumentStatus.QUOTE_ACCEPTED.value, "notes": "N", "subtotal": 200.0, "taxes": 20.0, "total_amount": 220.0, "reference_number": "PO123"}

        self.mock_db_handler.get_sales_document_by_id.side_effect = [mock_quote_data, {**mock_quote_data, "document_type": SalesDocumentType.SALES_ORDER.value, "status": SalesDocumentStatus.SO_OPEN.value}]

        with patch.object(self.sales_logic, 'get_items_for_sales_document', return_value=[]):
            sales_order = self.sales_logic.convert_quote_to_sales_order(mock_quote_id)

        self.assertIsNotNone(sales_order)
        self.assertEqual(sales_order.id, mock_quote_id)
        self.assertEqual(sales_order.document_type, SalesDocumentType.SALES_ORDER)
        self.assertEqual(sales_order.status, SalesDocumentStatus.SO_OPEN)
        self.mock_db_handler.update_sales_document.assert_called_once_with(mock_quote_id, {"document_type": SalesDocumentType.SALES_ORDER.value, "status": SalesDocumentStatus.SO_OPEN.value})

    def test_convert_quote_to_sales_order_does_not_adjust_inventory(self):
        mock_quote_id = 1
        mock_customer_id = 5
        mock_quote_data = {
            "id": mock_quote_id,
            "document_number": "S00000",
            "customer_id": mock_customer_id,
            "document_type": SalesDocumentType.QUOTE.value,
            "created_date": "date",
            "status": SalesDocumentStatus.QUOTE_ACCEPTED.value,
            "notes": "N",
            "subtotal": 0.0,
            "taxes": 0.0,
            "total_amount": 0.0,
            "reference_number": "PO123",
        }
        self.mock_db_handler.get_sales_document_by_id.side_effect = [
            mock_quote_data,
            {**mock_quote_data, "document_type": SalesDocumentType.SALES_ORDER.value, "status": SalesDocumentStatus.SO_OPEN.value},
        ]
        with patch.object(self.sales_logic.inventory_service, "adjust_stock") as mock_adjust:
            sales_order = self.sales_logic.convert_quote_to_sales_order(mock_quote_id)

        self.assertIsNotNone(sales_order)
        mock_adjust.assert_not_called()

    def test_convert_quote_to_sales_order_requires_reference_number_if_enabled(self):
        mock_quote_id = 1
        mock_quote_data = {
            "id": mock_quote_id,
            "document_number": "S00000",
            "customer_id": 5,
            "document_type": SalesDocumentType.QUOTE.value,
            "created_date": "date",
            "status": SalesDocumentStatus.QUOTE_ACCEPTED.value,
            "notes": "N",
            "subtotal": 0.0,
            "taxes": 0.0,
            "total_amount": 0.0,
            "reference_number": None,
        }
        self.mock_db_handler.get_sales_document_by_id.return_value = mock_quote_data
        with patch("core.sales_logic.load_preferences", return_value={"require_reference_on_quote_accept": True}):
            with self.assertRaisesRegex(ValueError, "Reference number is required"):
                self.sales_logic.convert_quote_to_sales_order(mock_quote_id)

    def test_convert_quote_to_sales_order_allows_missing_reference_when_disabled(self):
        mock_quote_id = 1
        mock_quote_data = {
            "id": mock_quote_id,
            "document_number": "S00000",
            "customer_id": 5,
            "document_type": SalesDocumentType.QUOTE.value,
            "created_date": "date",
            "status": SalesDocumentStatus.QUOTE_ACCEPTED.value,
            "notes": "N",
            "subtotal": 0.0,
            "taxes": 0.0,
            "total_amount": 0.0,
            "reference_number": None,
        }
        self.mock_db_handler.get_sales_document_by_id.side_effect = [
            mock_quote_data,
            {**mock_quote_data, "document_type": SalesDocumentType.SALES_ORDER.value, "status": SalesDocumentStatus.SO_OPEN.value},
        ]
        with patch("core.sales_logic.load_preferences", return_value={"require_reference_on_quote_accept": False}):
            with patch.object(self.sales_logic, 'get_items_for_sales_document', return_value=[]):
                sales_order = self.sales_logic.convert_quote_to_sales_order(mock_quote_id)
        self.assertIsNotNone(sales_order)

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
        mock_so_data = {"id": mock_so_id, "document_number": "S00000", "customer_id": mock_customer_id, "document_type": SalesDocumentType.SALES_ORDER.value, "created_date": "date", "status": SalesDocumentStatus.SO_FULFILLED.value, "notes": "N", "subtotal": 200.0, "taxes": 20.0, "total_amount": 220.0}
        mock_so_item_data = [{"id": 10, "sales_document_id": mock_so_id, "product_id": 100, "product_description": "Item 1", "quantity": 2.0, "unit_price": 100.0, "discount_percentage": 0.0, "line_total": 200.0, "note": None}]
        new_invoice_id = 2

        self.mock_db_handler.get_sales_document_by_id.side_effect = [mock_so_data, {"id": new_invoice_id, "document_number": "S00001", "customer_id": mock_customer_id, "document_type": SalesDocumentType.INVOICE.value, "status": SalesDocumentStatus.INVOICE_DRAFT.value, "related_quote_id":mock_so_id, "total_amount":220.0, "created_date":"d"}]
        self.mock_db_handler.get_items_for_sales_document.side_effect = [[{k:v for k,v in item.items()} for item in mock_so_item_data], [{**item, "sales_document_id":new_invoice_id} for item in mock_so_item_data]]
        self.mock_db_handler.add_sales_document.return_value = new_invoice_id
        self.mock_db_handler.add_sales_document_item.return_value = 20

        with patch.object(self.sales_logic, '_generate_sales_document_number', return_value="S00001") as mock_gen_num:
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
            "discount_percentage": 0.0, "line_total": 50.0, "note": None
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
            "discount_percentage": 0.0, "line_total": 50.0, "note": None
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
            {"id": mock_item_id1, "sales_document_id": mock_doc_id, "product_id": 1, "product_description": "Item 1", "quantity": 1, "unit_price": 10, "discount_percentage": 0, "line_total": 10, "note": None},
            {"id": mock_item_id2, "sales_document_id": mock_doc_id, "product_id": 2, "product_description": "Item 2", "quantity": 2, "unit_price": 20, "discount_percentage": 0, "line_total": 40, "note": None}
        ]
        self.mock_db_handler.get_items_for_sales_document.return_value = mock_items_list
        self.sales_logic.delete_sales_document(mock_doc_id)
        self.mock_db_handler.delete_sales_document_item.assert_not_called()
        self.mock_db_handler.delete_sales_document.assert_called_once_with(mock_doc_id)

    def test_delete_sales_document_not_found(self):
        self.mock_db_handler.get_sales_document_by_id.return_value = None
        with self.assertRaisesRegex(ValueError, "Sales document with ID 999 not found."):
            self.sales_logic.delete_sales_document(999)

    def test_delete_sales_document_with_items_invalid_status(self):
        mock_doc_id = 1
        self.mock_db_handler.get_sales_document_by_id.return_value = {"id": mock_doc_id, "status": SalesDocumentStatus.INVOICE_SENT.value, "document_type":SalesDocumentType.INVOICE.value, "customer_id":1, "document_number":"I", "created_date":"d", "subtotal":0,"taxes":0,"total_amount":0}
        self.mock_db_handler.get_items_for_sales_document.return_value = [ # Ensure items have all keys
            {"id": 10, "sales_document_id": mock_doc_id, "product_id": 1, "product_description": "Item 1", "quantity": 1, "unit_price": 10, "discount_percentage": 0, "line_total": 10, "note": None}
        ]
        with self.assertRaisesRegex(ValueError, "Cannot delete document with status 'Invoice Sent' that has items. Consider voiding first."):
            self.sales_logic.delete_sales_document(mock_doc_id)
        self.mock_db_handler.delete_sales_document_item.assert_not_called()
        self.mock_db_handler.delete_sales_document.assert_not_called()

    def test_confirm_sales_order_adjusts_inventory(self):
        mock_inventory_service = MagicMock()
        sales_logic = SalesLogic(
            self.mock_db_handler, inventory_service=mock_inventory_service
        )
        doc_id = 1
        self.mock_db_handler.get_sales_document_by_id.return_value = {
            "id": doc_id,
            "document_number": "S00000",
            "customer_id": 1,
            "document_type": SalesDocumentType.SALES_ORDER.value,
            "status": SalesDocumentStatus.SO_OPEN.value,
            "created_date": "2023-01-01",
            "subtotal": 0,
            "taxes": 0,
            "total_amount": 0,
        }
        item = SalesDocumentItem(
            item_id=10,
            sales_document_id=doc_id,
            product_id=100,
            product_description="Item",
            quantity=5,
        )
        with patch.object(sales_logic, "get_items_for_sales_document", return_value=[item]):
            sales_logic.confirm_sales_order(doc_id)

        mock_inventory_service.adjust_stock.assert_called_once()
        self.mock_db_handler.update_sales_document.assert_called_with(
            doc_id, {"status": SalesDocumentStatus.SO_FULFILLED.value}
        )

    def test_confirm_sales_order_queues_replenishment_when_insufficient_stock(self):
        mock_so_id = 1
        so_data = {
            "id": mock_so_id,
            "document_number": "S00000",
            "customer_id": 1,
            "document_type": SalesDocumentType.SALES_ORDER.value,
            "status": SalesDocumentStatus.SO_OPEN.value,
            "created_date": "2023-01-01",
            "subtotal": 0.0,
            "taxes": 0.0,
            "total_amount": 0.0,
        }
        self.mock_db_handler.get_sales_document_by_id.side_effect = [
            so_data,
            {**so_data, "status": SalesDocumentStatus.SO_FULFILLED.value},
        ]
        item = SalesDocumentItem(
            item_id=10,
            sales_document_id=mock_so_id,
            product_id=100,
            product_description="Item 1",
            quantity=5.0,
        )
        mock_inv_repo = self.sales_logic.inventory_service.inventory_repo
        mock_inv_repo.log_transaction = MagicMock()
        mock_inv_repo.get_stock_level = MagicMock(return_value=-5)
        mock_inv_repo.add_replenishment_item = MagicMock()
        self.sales_logic.product_repo.get_product_details = MagicMock(
            return_value={"reorder_point": 0, "reorder_quantity": 0}
        )
        with patch.object(
            self.sales_logic, "get_items_for_sales_document", return_value=[item]
        ):
            so = self.sales_logic.confirm_sales_order(mock_so_id)

        self.assertIsNotNone(so)
        mock_inv_repo.add_replenishment_item.assert_called_once_with(100, 5.0)

    def test_record_item_shipment_partial(self):
        item_id = 10
        doc_id = 1
        item_dict = {
            "id": item_id,
            "sales_document_id": doc_id,
            "product_id": 101,
            "product_description": "Item",
            "quantity": 10,
            "unit_price": 0,
            "discount_percentage": 0,
            "line_total": 0,
            "note": None,
            "shipped_quantity": 0,
            "is_shipped": 0,
        }
        updated_item_dict = {**item_dict, "shipped_quantity": 4}
        self.mock_db_handler.get_sales_document_item_by_id.side_effect = [
            item_dict,
            item_dict,
            updated_item_dict,
        ]
        self.mock_db_handler.get_sales_document_by_id.return_value = {
            "id": doc_id,
            "document_number": "S00001",
            "customer_id": 1,
            "document_type": SalesDocumentType.SALES_ORDER.value,
            "status": SalesDocumentStatus.SO_OPEN.value,
            "created_date": "2023-01-01",
            "subtotal": 0,
            "taxes": 0,
            "total_amount": 0,
        }
        self.mock_db_handler.get_shipment_references_for_sales_document.return_value = []
        self.mock_db_handler.are_all_items_shipped.return_value = False
        self.sales_logic.inventory_service.adjust_stock = MagicMock()
        self.sales_logic.inventory_service.inventory_repo.get_stock_level = MagicMock(
            return_value=10
        )

        updated_item = self.sales_logic.record_item_shipment(item_id, 4)

        self.mock_db_handler.update_sales_document_item.assert_called_once_with(
            item_id, {"shipped_quantity": 4, "is_shipped": 0}
        )
        self.sales_logic.inventory_service.adjust_stock.assert_called_once_with(
            101, -4, InventoryTransactionType.SALE, reference="S00001.001"
        )
        self.mock_db_handler.update_sales_document.assert_not_called()
        self.assertEqual(updated_item.shipped_quantity, 4)

    def test_record_item_shipment_completes_document(self):
        item_id = 10
        doc_id = 1
        item_dict = {
            "id": item_id,
            "sales_document_id": doc_id,
            "product_id": 101,
            "product_description": "Item",
            "quantity": 5,
            "unit_price": 0,
            "discount_percentage": 0,
            "line_total": 0,
            "note": None,
            "shipped_quantity": 3,
            "is_shipped": 0,
        }
        updated_item_dict = {**item_dict, "shipped_quantity": 5, "is_shipped": 1}
        self.mock_db_handler.get_sales_document_item_by_id.side_effect = [
            item_dict,
            item_dict,
            updated_item_dict,
        ]
        self.mock_db_handler.get_sales_document_by_id.return_value = {
            "id": doc_id,
            "document_number": "S00001",
            "customer_id": 1,
            "document_type": SalesDocumentType.SALES_ORDER.value,
            "status": SalesDocumentStatus.SO_OPEN.value,
            "created_date": "2023-01-01",
            "subtotal": 0,
            "taxes": 0,
            "total_amount": 0,
        }
        self.mock_db_handler.get_shipment_references_for_sales_document.return_value = []
        self.mock_db_handler.are_all_items_shipped.return_value = True
        self.sales_logic.inventory_service.adjust_stock = MagicMock()
        self.sales_logic.inventory_service.inventory_repo.get_stock_level = MagicMock(
            return_value=5
        )

        updated_item = self.sales_logic.record_item_shipment(item_id, 2)

        self.mock_db_handler.update_sales_document_item.assert_called_once_with(
            item_id, {"shipped_quantity": 5, "is_shipped": 1}
        )
        self.sales_logic.inventory_service.adjust_stock.assert_called_once_with(
            101, -2, InventoryTransactionType.SALE, reference="S00001.001"
        )
        self.mock_db_handler.update_sales_document.assert_called_once_with(
            doc_id, {"status": SalesDocumentStatus.SO_FULFILLED.value}
        )
        self.assertEqual(updated_item.shipped_quantity, 5)

    def test_record_item_shipment_insufficient_stock(self):
        item_id = 10
        doc_id = 1
        item_dict = {
            "id": item_id,
            "sales_document_id": doc_id,
            "product_id": 101,
            "product_description": "Item",
            "quantity": 5,
            "unit_price": 0,
            "discount_percentage": 0,
            "line_total": 0,
            "note": None,
            "shipped_quantity": 0,
            "is_shipped": 0,
        }
        self.mock_db_handler.get_sales_document_item_by_id.return_value = item_dict
        self.mock_db_handler.get_sales_document_by_id.return_value = {
            "id": doc_id,
            "document_number": "S00001",
            "customer_id": 1,
            "document_type": SalesDocumentType.SALES_ORDER.value,
            "status": SalesDocumentStatus.SO_OPEN.value,
            "created_date": "2023-01-01",
            "subtotal": 0,
            "taxes": 0,
            "total_amount": 0,
        }
        self.mock_db_handler.get_shipment_references_for_sales_document.return_value = []
        self.sales_logic.inventory_service.inventory_repo.get_stock_level = MagicMock(
            return_value=1
        )
        with self.assertRaises(ValueError):
            self.sales_logic.record_item_shipment(item_id, 2)

    def test_record_shipment_multiple_items(self):
        doc_id = 1
        item1_id = 10
        item2_id = 11
        item1 = {
            "id": item1_id,
            "sales_document_id": doc_id,
            "product_id": 101,
            "product_description": "Item1",
            "quantity": 5,
            "unit_price": 0,
            "discount_percentage": 0,
            "line_total": 0,
            "note": None,
            "shipped_quantity": 0,
            "is_shipped": 0,
        }
        item2 = {
            "id": item2_id,
            "sales_document_id": doc_id,
            "product_id": 102,
            "product_description": "Item2",
            "quantity": 3,
            "unit_price": 0,
            "discount_percentage": 0,
            "line_total": 0,
            "note": None,
            "shipped_quantity": 0,
            "is_shipped": 0,
        }
        self.mock_db_handler.get_sales_document_item_by_id.side_effect = [
            item1,
            item2,
        ]
        self.mock_db_handler.get_sales_document_by_id.return_value = {
            "id": doc_id,
            "document_number": "S00001",
            "customer_id": 1,
            "document_type": SalesDocumentType.SALES_ORDER.value,
            "status": SalesDocumentStatus.SO_OPEN.value,
            "created_date": "2023-01-01",
            "subtotal": 0,
            "taxes": 0,
            "total_amount": 0,
        }
        self.mock_db_handler.get_shipment_references_for_sales_document.return_value = []
        self.mock_db_handler.are_all_items_shipped.return_value = False
        self.sales_logic.inventory_service.adjust_stock = MagicMock()
        self.sales_logic.inventory_service.inventory_repo.get_stock_level = MagicMock(return_value=10)

        shipment_number = self.sales_logic.record_shipment(
            doc_id, {item1_id: 2, item2_id: 1}
        )
        self.assertEqual(shipment_number, "S00001.001")

        expected_calls = [
            call(101, -2, InventoryTransactionType.SALE, reference="S00001.001"),
            call(102, -1, InventoryTransactionType.SALE, reference="S00001.001"),
        ]
        self.sales_logic.inventory_service.adjust_stock.assert_has_calls(
            expected_calls, any_order=True
        )

if __name__ == '__main__':
    unittest.main()

class TestSalesLogicWithPricingRules(unittest.TestCase):
    def setUp(self):
        self.db_handler = DatabaseHandler(db_name=':memory:')
        self.sales_logic = SalesLogic(self.db_handler)
        self.address_book_logic = AddressBookLogic(self.db_handler)

        # Create a customer
        self.customer = self.address_book_logic.save_account(Account(name="Test Customer", account_type=AccountType.CUSTOMER))

        # Create a product
        self.product = Product(name="Test Product", cost=100.0, sale_price=150.0)
        self.product.product_id = self.address_book_logic.save_product(self.product)

        # Create a quote
        self.quote = self.sales_logic.create_quote(customer_id=self.customer.account_id)


    def tearDown(self):
        self.db_handler.close()

    def test_add_item_with_fixed_markup_rule(self):
        """Test adding an item for a customer with a fixed markup rule."""
        rule_id = self.address_book_logic.create_pricing_rule(rule_name="Fixed Markup Rule", fixed_markup=20.0)
        self.address_book_logic.assign_pricing_rule(self.customer.account_id, rule_id)

        item = self.sales_logic.add_item_to_sales_document(self.quote.id, self.product.product_id, 1)

        self.assertEqual(item.unit_price, 120.0)

    def test_add_item_with_markup_rule(self):
        """Test adding an item for a customer with a markup rule."""
        rule_id = self.address_book_logic.create_pricing_rule(rule_name="Markup Rule", markup_percentage=25.0)
        self.address_book_logic.assign_pricing_rule(self.customer.account_id, rule_id)

        item = self.sales_logic.add_item_to_sales_document(self.quote.id, self.product.product_id, 1)

        # cost is 100.0, markup is 25%, so price should be 125.0
        self.assertEqual(item.unit_price, 125.0)

    def test_add_item_with_combined_rule(self):
        """Test adding an item for a customer with both fixed and percentage markup."""
        rule_id = self.address_book_logic.create_pricing_rule(rule_name="Combined Rule", fixed_markup=10.0, markup_percentage=20.0)
        self.address_book_logic.assign_pricing_rule(self.customer.account_id, rule_id)

        item = self.sales_logic.add_item_to_sales_document(self.quote.id, self.product.product_id, 1)

        # cost 100 + fixed 10 = 110; 20% markup -> 132
        self.assertEqual(item.unit_price, 132.0)

    def test_add_item_with_no_rule(self):
        """Test adding an item for a customer with no pricing rule."""
        item = self.sales_logic.add_item_to_sales_document(self.quote.id, self.product.product_id, 1)

        # Should use the product's sale_price
        self.assertEqual(item.unit_price, 150.0)

    def test_update_item_with_pricing_rule(self):
        """Test that updating an item still respects the pricing rule."""
        rule_id = self.address_book_logic.create_pricing_rule(rule_name="Fixed Markup Rule", fixed_markup=10.0)
        self.address_book_logic.assign_pricing_rule(self.customer.account_id, rule_id)

        item = self.sales_logic.add_item_to_sales_document(self.quote.id, self.product.product_id, 1)
        self.assertEqual(item.unit_price, 110.0)

        updated_item = self.sales_logic.update_sales_document_item(item.id, self.product.product_id, 2, unit_price_override=None)

        self.assertEqual(updated_item.unit_price, 110.0)
        self.assertEqual(updated_item.quantity, 2)

    def test_get_shipments_for_order(self):
        mock_data = [
            {
                "shipment_number": "S00001.001",
                "created_at": "2024-01-01",
                "item_id": 10,
                "product_description": "Widget",
                "quantity": 2,
            }
        ]
        self.sales_logic.sales_repo.get_shipments_for_sales_document = MagicMock(
            return_value=mock_data
        )
        shipments = self.sales_logic.get_shipments_for_order(5)
        expected = [
            {
                "number": "S00001.001",
                "created_at": "2024-01-01",
                "items": [
                    {
                        "item_id": 10,
                        "product_description": "Widget",
                        "quantity": 2,
                    }
                ],
            }
        ]
        self.assertEqual(shipments, expected)
        self.sales_logic.sales_repo.get_shipments_for_sales_document.assert_called_once_with(5)


class TestPackingSlipGeneration(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseHandler(db_name=':memory:')
        self.sales_logic = SalesLogic(self.db)
        self.address_book_logic = AddressBookLogic(self.db)

        addr = Address(
            street="123 Main",
            city="Town",
            state="TS",
            zip_code="12345",
            country="USA",
        )
        addr.address_type = "Shipping"
        addr.is_primary = True
        self.customer = Account(
            name="Cust", account_type=AccountType.CUSTOMER, addresses=[addr]
        )
        self.customer = self.address_book_logic.save_account(self.customer)

        self.product = Product(name="Widget", cost=5.0, sale_price=10.0)
        self.product.product_id = self.address_book_logic.save_product(self.product)
        self.sales_logic.inventory_service.adjust_stock(
            self.product.product_id, 5, InventoryTransactionType.ADJUSTMENT
        )

        self.quote = self.sales_logic.create_quote(
            customer_id=self.customer.account_id, reference_number="REF1"
        )
        self.item = self.sales_logic.add_item_to_sales_document(
            self.quote.id, self.product.product_id, 5
        )
        self.sales_order = self.sales_logic.convert_quote_to_sales_order(
            self.quote.id
        )

    def tearDown(self):
        self.db.close()

    def test_packing_slip_generation(self):
        shipments = {self.item.id: 1}
        shipment_number = self.sales_logic.record_shipment(
            self.sales_order.id, shipments
        )
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.close()
        generate_packing_slip_pdf(
            self.sales_order.id,
            shipments,
            shipment_number,
            output_path=tmp.name,
            db_handler=self.db,
        )
        self.assertTrue(os.path.exists(tmp.name))
        self.assertGreater(os.path.getsize(tmp.name), 0)
        with open(tmp.name, "rb") as f:
            raw = f.read()
        stream_start = raw.find(b"stream")
        stream_start = raw.find(b"\n", stream_start) + 1
        stream_end = raw.find(b"endstream", stream_start)
        decompressed = zlib.decompress(raw[stream_start:stream_end])
        self.assertIn(b"Qty Remaining", decompressed)
        self.assertNotIn(b"No remaining items", decompressed)
        os.unlink(tmp.name)

    def test_packing_slip_no_remaining_items(self):
        shipments = {self.item.id: 5}
        shipment_number = self.sales_logic.record_shipment(
            self.sales_order.id, shipments
        )
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.close()
        generate_packing_slip_pdf(
            self.sales_order.id,
            shipments,
            shipment_number,
            output_path=tmp.name,
            db_handler=self.db,
        )
        self.assertTrue(os.path.exists(tmp.name))
        self.assertGreater(os.path.getsize(tmp.name), 0)
        with open(tmp.name, "rb") as f:
            raw = f.read()
        stream_start = raw.find(b"stream")
        stream_start = raw.find(b"\n", stream_start) + 1
        stream_end = raw.find(b"endstream", stream_start)
        decompressed = zlib.decompress(raw[stream_start:stream_end])
        self.assertNotIn(b"Items Remaining to Ship", decompressed)
        self.assertNotIn(b"Qty Remaining", decompressed)
        os.unlink(tmp.name)

    def test_packing_slip_with_previous_shipments(self):
        shipments_first = {self.item.id: 2}
        first_number = self.sales_logic.record_shipment(
            self.sales_order.id, shipments_first
        )
        shipments_second = {self.item.id: 1}
        self.sales_logic.record_shipment(self.sales_order.id, shipments_second)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.close()
        generate_packing_slip_pdf(
            self.sales_order.id,
            shipments_first,
            first_number,
            previous_shipments={},
            output_path=tmp.name,
            db_handler=self.db,
        )
        with open(tmp.name, "rb") as f:
            raw = f.read()
        stream_start = raw.find(b"stream")
        stream_start = raw.find(b"\n", stream_start) + 1
        stream_end = raw.find(b"endstream", stream_start)
        decompressed = zlib.decompress(raw[stream_start:stream_end])
        self.assertIn(b"3.00", decompressed)
        os.unlink(tmp.name)
