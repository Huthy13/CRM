import datetime
from typing import Optional, List
from core.database import DatabaseHandler
from shared.structs import (
    SalesDocument, SalesDocumentItem, SalesDocumentStatus, SalesDocumentType,
    Account, AccountType, Product
)

class SalesLogic:
    def __init__(self, db_handler: DatabaseHandler):
        self.db = db_handler

    def _generate_sales_document_number(self, doc_type: SalesDocumentType) -> str:
        """
        Generates a unique document number for Quotes (QUO-YYYYMMDD-XXXX)
        and Invoices (INV-YYYYMMDD-XXXX).
        XXXX is a 4-digit incrementing number for that day and type.
        """
        prefix = "QUO" if doc_type == SalesDocumentType.QUOTE else "INV"
        today_str = datetime.date.today().strftime("%Y%m%d")
        full_prefix = f"{prefix}-{today_str}-"

        # Query existing documents of the same type for today to find the max sequence
        # This is a simplified approach; a more robust one might involve a dedicated sequence table
        # or more complex query if performance for very high volume is a concern.
        all_docs_raw = self.db.get_all_sales_documents(document_type=doc_type.value)
        max_seq_today = 0
        for doc_dict in all_docs_raw:
            doc_num_str = doc_dict.get("document_number")
            if doc_num_str and doc_num_str.startswith(full_prefix):
                try:
                    seq_part = int(doc_num_str.split('-')[-1])
                    if seq_part > max_seq_today:
                        max_seq_today = seq_part
                except ValueError:
                    pass # Ignore malformed numbers

        next_seq = max_seq_today + 1
        return f"{full_prefix}{next_seq:04d}"

    def create_quote(self, customer_id: int, notes: str = None, expiry_date_iso: Optional[str] = None) -> Optional[SalesDocument]:
        """Creates a new Quote."""
        customer_account_dict = self.db.get_account_details(customer_id)
        if not customer_account_dict:
            raise ValueError(f"Customer with ID {customer_id} not found.")
        if customer_account_dict.get('account_type') != AccountType.CUSTOMER.value:
             raise ValueError(f"Account ID {customer_id} is not a registered Customer.")

        doc_number = self._generate_sales_document_number(SalesDocumentType.QUOTE)
        created_date_str = datetime.datetime.now().isoformat()
        # Default expiry if not provided (e.g., 30 days from creation)
        if not expiry_date_iso:
            expiry_date_iso = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()


        new_doc_id = self.db.add_sales_document(
            doc_number=doc_number,
            customer_id=customer_id,
            document_type=SalesDocumentType.QUOTE.value,
            created_date=created_date_str,
            expiry_date=expiry_date_iso,
            status=SalesDocumentStatus.QUOTE_DRAFT.value,
            notes=notes
        )
        if new_doc_id:
            return self.get_sales_document_details(new_doc_id)
        return None

    def add_item_to_sales_document(self, doc_id: int, product_id: int, quantity: float,
                                   product_description_override: Optional[str] = None,
                                   unit_price_override: Optional[float] = None, # This would be the sale price
                                   discount_percentage: Optional[float] = 0.0
                                   ) -> Optional[SalesDocumentItem]:
        """Adds an item to a Quote or Invoice."""
        doc = self.get_sales_document_details(doc_id)
        if not doc:
            raise ValueError(f"Sales document with ID {doc_id} not found.")

        # Define statuses where items can be added/modified
        editable_statuses = [
            SalesDocumentStatus.QUOTE_DRAFT,
            SalesDocumentStatus.INVOICE_DRAFT
        ]
        if doc.status not in editable_statuses:
             raise ValueError(f"Items cannot be added to a document with status '{doc.status.value}'.")

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if discount_percentage is not None and not (0 <= discount_percentage <= 100):
            raise ValueError("Discount percentage must be between 0 and 100.")

        product_info = self.db.get_product_details(product_id) # Fetches dict with 'name', 'sale_price' etc.
        if not product_info:
            raise ValueError(f"Product with ID {product_id} not found.")

        final_description = product_description_override if product_description_override else product_info.get('name', f"Product ID: {product_id}")

        # Use override if provided, otherwise product's sale_price, else error or default (e.g. 0)
        final_unit_price = unit_price_override
        if final_unit_price is None:
            final_unit_price = product_info.get('sale_price') # Assumes get_product_details fetches this
            if final_unit_price is None:
                raise ValueError(f"Sale price for product ID {product_id} not found and no override provided.")

        if final_unit_price < 0:
            raise ValueError("Unit price cannot be negative.")

        # Calculate line_total
        effective_discount = discount_percentage if discount_percentage is not None else 0.0
        line_total = quantity * final_unit_price * (1 - (effective_discount / 100.0))

        new_item_id = self.db.add_sales_document_item(
            sales_doc_id=doc_id,
            product_id=product_id,
            product_description=final_description,
            quantity=quantity,
            unit_price=final_unit_price,
            discount_percentage=effective_discount,
            line_total=line_total
        )
        if new_item_id:
            self._recalculate_sales_document_totals(doc_id)
            return self.get_sales_document_item_details(new_item_id)
        return None

    def update_sales_document_item(self, item_id: int, product_id: int, quantity: float,
                                   unit_price_override: Optional[float], # Sale price
                                   discount_percentage: Optional[float] = 0.0,
                                   product_description_override: Optional[str] = None
                                   ) -> Optional[SalesDocumentItem]:
        item_to_update = self.get_sales_document_item_details(item_id)
        if not item_to_update:
            raise ValueError(f"Item with ID {item_id} not found for update.")

        doc = self.get_sales_document_details(item_to_update.sales_document_id)
        editable_statuses = [SalesDocumentStatus.QUOTE_DRAFT, SalesDocumentStatus.INVOICE_DRAFT]
        if doc.status not in editable_statuses:
            raise ValueError(f"Items cannot be modified for a document with status '{doc.status.value}'.")

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if discount_percentage is not None and not (0 <= discount_percentage <= 100):
            raise ValueError("Discount percentage must be between 0 and 100.")

        product_info = self.db.get_product_details(product_id)
        if not product_info:
            raise ValueError(f"Product with ID {product_id} not found.")

        final_description = product_description_override
        if not final_description:
            if item_to_update.product_id != product_id or not item_to_update.product_description:
                final_description = product_info.get('name', f"Product ID: {product_id}")
            else:
                final_description = item_to_update.product_description

        final_unit_price = unit_price_override
        if final_unit_price is None:
            final_unit_price = product_info.get('sale_price')
            if final_unit_price is None:
                 raise ValueError(f"Sale price for product ID {product_id} not found and no override provided.")

        if final_unit_price < 0:
            raise ValueError("Unit price cannot be negative.")

        effective_discount = discount_percentage if discount_percentage is not None else 0.0
        new_line_total = quantity * final_unit_price * (1 - (effective_discount / 100.0))

        updates = {
            "product_id": product_id,
            "product_description": final_description,
            "quantity": quantity,
            "unit_price": final_unit_price,
            "discount_percentage": effective_discount,
            "line_total": new_line_total
        }
        self.db.update_sales_document_item(item_id, updates)
        self._recalculate_sales_document_totals(doc.id)
        return self.get_sales_document_item_details(item_id)

    def _recalculate_sales_document_totals(self, doc_id: int):
        """Recalculates subtotal, taxes (if any), and total_amount for a sales document."""
        items = self.get_items_for_sales_document(doc_id)
        subtotal = sum(item.line_total for item in items if item.line_total is not None)

        # Basic tax calculation (e.g., 0% for now, can be made configurable)
        tax_rate = 0.00
        taxes = subtotal * tax_rate
        total_amount = subtotal + taxes

        updates = {
            "subtotal": subtotal,
            "taxes": taxes,
            "total_amount": total_amount
        }
        self.db.update_sales_document(doc_id, updates)

    def convert_quote_to_invoice(self, quote_id: int, due_date_iso: Optional[str] = None) -> Optional[SalesDocument]:
        quote_doc = self.get_sales_document_details(quote_id)
        if not quote_doc:
            raise ValueError(f"Quote with ID {quote_id} not found.")
        if quote_doc.document_type != SalesDocumentType.QUOTE:
            raise ValueError(f"Document ID {quote_id} is not a Quote.")
        if quote_doc.status != SalesDocumentStatus.QUOTE_ACCEPTED:
            raise ValueError(f"Only accepted Quotes can be converted to Invoices. Current status: {quote_doc.status.value}")

        invoice_number = self._generate_sales_document_number(SalesDocumentType.INVOICE)
        created_date_str = datetime.datetime.now().isoformat()

        # Default due date if not provided (e.g., 30 days from creation)
        final_due_date_iso = due_date_iso
        if not final_due_date_iso:
            final_due_date_iso = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()

        new_invoice_id = self.db.add_sales_document(
            doc_number=invoice_number,
            customer_id=quote_doc.customer_id,
            document_type=SalesDocumentType.INVOICE.value,
            created_date=created_date_str,
            due_date=final_due_date_iso,
            status=SalesDocumentStatus.INVOICE_DRAFT.value, # Or INVOICE_SENT if sent immediately
            notes=quote_doc.notes, # Copy notes from quote
            subtotal=quote_doc.subtotal,
            taxes=quote_doc.taxes,
            total_amount=quote_doc.total_amount,
            related_quote_id=quote_id
        )

        if not new_invoice_id:
            raise Exception("Failed to create invoice record in database.")

        # Copy items from quote to invoice
        quote_items = self.get_items_for_sales_document(quote_id)
        for item in quote_items:
            self.db.add_sales_document_item(
                sales_doc_id=new_invoice_id,
                product_id=item.product_id,
                product_description=item.product_description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_percentage=item.discount_percentage,
                line_total=item.line_total
            )
        # Recalculate totals for the new invoice just in case, though they are copied
        self._recalculate_sales_document_totals(new_invoice_id)
        return self.get_sales_document_details(new_invoice_id)

    def update_sales_document_status(self, doc_id: int, new_status: SalesDocumentStatus) -> Optional[SalesDocument]:
        doc = self.get_sales_document_details(doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found for status update.")

        # Add validation for status transitions if needed
        # Example: Cannot change status of a PAID invoice back to DRAFT
        if doc.status == SalesDocumentStatus.INVOICE_PAID and new_status != SalesDocumentStatus.INVOICE_PAID:
             if new_status != SalesDocumentStatus.INVOICE_VOID: # Allow voiding a paid invoice
                raise ValueError("Cannot change status of a paid invoice, except to void it.")

        # Example: Quote specific transitions
        if doc.document_type == SalesDocumentType.QUOTE:
            valid_quote_statuses = [s for s in SalesDocumentStatus if s.name.startswith("QUOTE_")]
            if new_status not in valid_quote_statuses:
                raise ValueError(f"Invalid status '{new_status.value}' for a Quote.")
        # Example: Invoice specific transitions
        elif doc.document_type == SalesDocumentType.INVOICE:
            valid_invoice_statuses = [s for s in SalesDocumentStatus if s.name.startswith("INVOICE_")]
            if new_status not in valid_invoice_statuses:
                raise ValueError(f"Invalid status '{new_status.value}' for an Invoice.")


        self.db.update_sales_document(doc_id, {"status": new_status.value})
        return self.get_sales_document_details(doc_id)

    def update_document_notes(self, doc_id: int, notes: str) -> Optional[SalesDocument]:
        doc = self.get_sales_document_details(doc_id)
        if not doc:
            raise ValueError(f"Sales document with ID {doc_id} not found.")
        self.db.update_sales_document(doc_id, {"notes": notes})
        return self.get_sales_document_details(doc_id)

    def get_sales_document_details(self, doc_id: int) -> Optional[SalesDocument]:
        doc_data = self.db.get_sales_document_by_id(doc_id)
        if doc_data:
            status_enum = None
            if doc_data.get('status'):
                try:
                    status_enum = SalesDocumentStatus(doc_data['status'])
                except ValueError:
                     print(f"Warning: Invalid sales status '{doc_data['status']}' in DB for doc ID {doc_id}")

            doc_type_enum = None
            if doc_data.get('document_type'):
                try:
                    doc_type_enum = SalesDocumentType(doc_data['document_type'])
                except ValueError:
                    print(f"Warning: Invalid sales document type '{doc_data['document_type']}' in DB for doc ID {doc_id}")

            return SalesDocument(
                doc_id=doc_data['id'],
                document_number=doc_data['document_number'],
                customer_id=doc_data['customer_id'],
                document_type=doc_type_enum,
                created_date=doc_data['created_date'],
                expiry_date=doc_data.get('expiry_date'),
                due_date=doc_data.get('due_date'),
                status=status_enum,
                notes=doc_data.get('notes'),
                subtotal=doc_data.get('subtotal'),
                taxes=doc_data.get('taxes'),
                total_amount=doc_data.get('total_amount'),
                related_quote_id=doc_data.get('related_quote_id')
            )
        return None

    def get_all_sales_documents_by_criteria(self, customer_id: int = None, doc_type: SalesDocumentType = None, status: SalesDocumentStatus = None) -> List[SalesDocument]:
        doc_type_value = doc_type.value if doc_type else None
        status_value = status.value if status else None

        docs_data = self.db.get_all_sales_documents(customer_id=customer_id, document_type=doc_type_value, status=status_value)
        result_list = []
        for doc_data in docs_data:
            status_enum = None
            if doc_data.get('status'):
                try:
                    status_enum = SalesDocumentStatus(doc_data['status'])
                except ValueError:
                    print(f"Warning: Invalid sales status '{doc_data['status']}' in DB for doc ID {doc_data['id']}")

            doc_type_enum = None
            if doc_data.get('document_type'):
                try:
                    doc_type_enum = SalesDocumentType(doc_data['document_type'])
                except ValueError:
                    print(f"Warning: Invalid sales document type '{doc_data['document_type']}' in DB for doc ID {doc_data['id']}")

            result_list.append(SalesDocument(
                doc_id=doc_data['id'],
                document_number=doc_data['document_number'],
                customer_id=doc_data['customer_id'],
                document_type=doc_type_enum,
                created_date=doc_data['created_date'],
                expiry_date=doc_data.get('expiry_date'),
                due_date=doc_data.get('due_date'),
                status=status_enum,
                notes=doc_data.get('notes'),
                subtotal=doc_data.get('subtotal'),
                taxes=doc_data.get('taxes'),
                total_amount=doc_data.get('total_amount'),
                related_quote_id=doc_data.get('related_quote_id')
            ))
        return result_list

    def get_items_for_sales_document(self, doc_id: int) -> List[SalesDocumentItem]:
        items_data = self.db.get_items_for_sales_document(doc_id)
        result_list = []
        for item_data in items_data:
            result_list.append(SalesDocumentItem(
                item_id=item_data['id'],
                sales_document_id=item_data['sales_document_id'],
                product_id=item_data.get('product_id'),
                product_description=item_data['product_description'],
                quantity=item_data['quantity'],
                unit_price=item_data.get('unit_price'),
                discount_percentage=item_data.get('discount_percentage'),
                line_total=item_data.get('line_total')
            ))
        return result_list

    def get_sales_document_item_details(self, item_id: int) -> Optional[SalesDocumentItem]:
        item_data = self.db.get_sales_document_item_by_id(item_id)
        if item_data:
            return SalesDocumentItem(
                item_id=item_data['id'],
                sales_document_id=item_data['sales_document_id'],
                product_id=item_data.get('product_id'),
                product_description=item_data['product_description'],
                quantity=item_data['quantity'],
                unit_price=item_data.get('unit_price'),
                discount_percentage=item_data.get('discount_percentage'),
                line_total=item_data.get('line_total')
            )
        return None

    def delete_sales_document_item(self, item_id: int):
        item = self.get_sales_document_item_details(item_id)
        if not item:
            raise ValueError(f"Sales document item with ID {item_id} not found.")

        doc = self.get_sales_document_details(item.sales_document_id)
        editable_statuses = [SalesDocumentStatus.QUOTE_DRAFT, SalesDocumentStatus.INVOICE_DRAFT]
        if doc.status not in editable_statuses:
            raise ValueError(f"Items cannot be deleted from a document with status '{doc.status.value}'.")

        self.db.delete_sales_document_item(item_id)
        self._recalculate_sales_document_totals(doc.id)


    def delete_sales_document(self, doc_id: int):
        doc = self.get_sales_document_details(doc_id)
        if not doc:
            raise ValueError(f"Sales document with ID {doc_id} not found.")

        # Add any business logic checks here, e.g., cannot delete a PAID invoice.
        # For now, allowing deletion if found.
        # Note: DB ON DELETE CASCADE should handle items if configured on FK.
        # If not, items must be deleted manually first.
        # The sales_document_items table in database_setup.py does NOT have ON DELETE CASCADE.
        # So, we must delete items first.

        items = self.get_items_for_sales_document(doc_id)
        if items:
             # Check if document status allows item/document deletion
            deletable_doc_statuses = [
                SalesDocumentStatus.QUOTE_DRAFT, SalesDocumentStatus.QUOTE_REJECTED, SalesDocumentStatus.QUOTE_EXPIRED,
                SalesDocumentStatus.INVOICE_DRAFT, SalesDocumentStatus.INVOICE_VOID
            ]
            if doc.status not in deletable_doc_statuses :
                 raise ValueError(f"Cannot delete document with status '{doc.status.value}' that has items. Consider voiding first.")

            for item in items:
                self.db.delete_sales_document_item(item.id) # Use the item's own ID

        self.db.delete_sales_document(doc_id)
