import datetime
from typing import Optional, List
import logging
from core.database import DatabaseHandler
from core.address_book_logic import AddressBookLogic
from core.inventory_service import InventoryService
from core.repositories import (
    SalesRepository,
    AccountRepository,
    ProductRepository,
    InventoryRepository,
)
from shared.structs import (
    SalesDocument,
    SalesDocumentItem,
    SalesDocumentStatus,
    SalesDocumentType,
    Account,
    AccountType,
    Product,
    InventoryTransactionType,
)

logger = logging.getLogger(__name__)


class SalesLogic:
    def __init__(
        self,
        repo_or_db,
        account_repo=None,
        product_repo=None,
        inventory_service: InventoryService | None = None,
    ):
        if isinstance(repo_or_db, SalesRepository):
            self.sales_repo = repo_or_db
            db_handler = self.sales_repo.db
            self.account_repo = account_repo or AccountRepository(db_handler)
            self.product_repo = product_repo or ProductRepository(db_handler)
        else:
            db_handler = repo_or_db
            self.sales_repo = SalesRepository(db_handler)
            self.account_repo = account_repo or AccountRepository(db_handler)
            self.product_repo = product_repo or ProductRepository(db_handler)

        inv_repo = InventoryRepository(db_handler)
        self.inventory_service = inventory_service or InventoryService(
            inv_repo, self.product_repo
        )
        # Expose the underlying database handler for legacy callers
        self.db = db_handler
        self._db = db_handler

    def _generate_sales_document_number(self, doc_type: SalesDocumentType) -> str:
        """Generates a unique sales document number in the format ``S#####``.

        The numbering is shared across all sales documents regardless of type.
        """
        prefix = "S"
        all_docs_raw = self.sales_repo.get_all_sales_documents(is_active=None)
        max_seq = -1
        for doc_dict in all_docs_raw:
            doc_num_str = doc_dict.get("document_number")
            if doc_num_str and doc_num_str.startswith(prefix):
                try:
                    seq_part = int(doc_num_str[len(prefix):])
                    if seq_part > max_seq:
                        max_seq = seq_part
                except ValueError:
                    pass  # Ignore malformed numbers

        next_seq = max_seq + 1
        return f"{prefix}{next_seq:05d}"

    def create_quote(self, customer_id: int, notes: str = None, expiry_date_iso: Optional[str] = None,
                     reference_number: Optional[str] = None) -> Optional[SalesDocument]:
        """Creates a new Quote."""
        customer_account_dict = self.account_repo.get_account_details(customer_id)
        if not customer_account_dict:
            raise ValueError(f"Customer with ID {customer_id} not found.")
        if customer_account_dict.get('account_type') != AccountType.CUSTOMER.value:
             raise ValueError(f"Account ID {customer_id} is not a registered Customer.")

        doc_number = self._generate_sales_document_number(SalesDocumentType.QUOTE)
        created_date_str = datetime.datetime.now().isoformat()
        # Default expiry if not provided (e.g., 30 days from creation)
        if not expiry_date_iso:
            expiry_date_iso = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()


        new_doc_id = self.sales_repo.add_sales_document(
            doc_number=doc_number,
            customer_id=customer_id,
            document_type=SalesDocumentType.QUOTE.value,
            created_date=created_date_str,
            status=SalesDocumentStatus.QUOTE_DRAFT.value,
            reference_number=reference_number,
            expiry_date=expiry_date_iso,
            notes=notes
        )
        if new_doc_id:
            return self.get_sales_document_details(new_doc_id)
        return None

    def add_item_to_sales_document(self, doc_id: int, product_id: int, quantity: float,
                                   product_description_override: Optional[str] = None,
                                   unit_price_override: Optional[float] = None, # This would be the sale price
                                   discount_percentage: Optional[float] = 0.0,
                                   note: str | None = None
                                   ) -> Optional[SalesDocumentItem]:
        """Adds an item to a Quote or Invoice."""
        doc = self.get_sales_document_details(doc_id)
        if not doc:
            raise ValueError(f"Sales document with ID {doc_id} not found.")

        # Define statuses where items can be added/modified
        editable_statuses = [
            SalesDocumentStatus.QUOTE_DRAFT,
            SalesDocumentStatus.INVOICE_DRAFT,
            SalesDocumentStatus.SO_OPEN
        ]
        if doc.status not in editable_statuses:
             raise ValueError(f"Items cannot be added to a document with status '{doc.status.value}'.")

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if discount_percentage is not None and not (0 <= discount_percentage <= 100):
            raise ValueError("Discount percentage must be between 0 and 100.")

        product_info = self.product_repo.get_product_details(product_id)
        if not product_info:
            raise ValueError(f"Product with ID {product_id} not found.")

        final_description = product_description_override if product_description_override else product_info.get('name', f"Product ID: {product_id}")

        # Use override if provided, otherwise product's sale_price, else error or default (e.g. 0)
        final_unit_price = unit_price_override
        if final_unit_price is None:
            address_book_logic = AddressBookLogic(self._db)
            customer = address_book_logic.get_account_details(doc.customer_id)
            if customer and customer.pricing_rule_id:
                rule = address_book_logic.get_pricing_rule(customer.pricing_rule_id)
                if rule:
                    product_cost = product_info.get('cost')
                    if product_cost is None:
                        raise ValueError(f"Product cost for product ID {product_id} not found, cannot apply pricing rule.")
                    final_unit_price = product_cost
                    if rule.fixed_markup is not None:
                        final_unit_price += rule.fixed_markup
                    if rule.markup_percentage is not None:
                        final_unit_price *= (1 + rule.markup_percentage / 100)

            if final_unit_price is None: # If no rule was applied or customer/rule not found
                final_unit_price = product_info.get('sale_price')
                if final_unit_price is None:
                    raise ValueError(f"Sale price for product ID {product_id} not found and no override provided.")

        if final_unit_price < 0:
            raise ValueError("Unit price cannot be negative.")

        # Calculate line_total
        effective_discount = discount_percentage if discount_percentage is not None else 0.0
        line_total = quantity * final_unit_price * (1 - (effective_discount / 100.0))

        new_item_id = self.sales_repo.add_sales_document_item(
            sales_doc_id=doc_id,
            product_id=product_id,
            product_description=final_description,
            quantity=quantity,
            unit_price=final_unit_price,
            discount_percentage=effective_discount,
            line_total=line_total,
            note=note
        )
        if new_item_id:
            self._recalculate_sales_document_totals(doc_id)
            return self.get_sales_document_item_details(new_item_id)
        return None

    def update_sales_document_item(self, item_id: int, product_id: int, quantity: float,
                                   unit_price_override: Optional[float], # Sale price
                                   discount_percentage: Optional[float] = 0.0,
                                   product_description_override: Optional[str] = None,
                                   note: str | None = None
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

        product_info = self.product_repo.get_product_details(product_id)
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
            address_book_logic = AddressBookLogic(self._db)
            customer = address_book_logic.get_account_details(doc.customer_id)
            if customer and customer.pricing_rule_id:
                rule = address_book_logic.get_pricing_rule(customer.pricing_rule_id)
                if rule:
                    product_cost = product_info.get('cost')
                    if product_cost is None:
                        raise ValueError(f"Product cost for product ID {product_id} not found, cannot apply pricing rule.")
                    final_unit_price = product_cost
                    if rule.fixed_markup is not None:
                        final_unit_price += rule.fixed_markup
                    if rule.markup_percentage is not None:
                        final_unit_price *= (1 + rule.markup_percentage / 100)

            if final_unit_price is None: # If no rule was applied or customer/rule not found
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
            "line_total": new_line_total,
        }
        if note is not None:
            updates["note"] = note
        self.sales_repo.update_sales_document_item(item_id, updates)
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
        self.sales_repo.update_sales_document(doc_id, updates)

    def convert_quote_to_sales_order(self, quote_id: int) -> Optional[SalesDocument]:
        quote_doc = self.get_sales_document_details(quote_id)
        if not quote_doc:
            raise ValueError(f"Quote with ID {quote_id} not found.")
        if quote_doc.document_type != SalesDocumentType.QUOTE:
            raise ValueError(f"Document ID {quote_id} is not a Quote.")
        if not quote_doc.reference_number:
            raise ValueError("Reference number is required to convert a Quote to a Sales Order.")
        # Record inventory reductions for each item, triggering replenishment when needed
        items = self.get_items_for_sales_document(quote_id)
        for item in items:
            if item.product_id is None:
                continue
            self.inventory_service.adjust_stock(
                item.product_id,
                -item.quantity,
                InventoryTransactionType.SALE,
                reference=f"SO-{quote_id}",
            )
        # Update the document type and status
        updates = {
            "document_type": SalesDocumentType.SALES_ORDER.value,
            "status": SalesDocumentStatus.SO_OPEN.value,
        }
        self.sales_repo.update_sales_document(quote_id, updates)

        return self.get_sales_document_details(quote_id)

    def convert_sales_order_to_invoice(self, sales_order_id: int, due_date_iso: Optional[str] = None) -> Optional[SalesDocument]:
        so_doc = self.get_sales_document_details(sales_order_id)
        if not so_doc:
            raise ValueError(f"Sales Order with ID {sales_order_id} not found.")
        if so_doc.document_type != SalesDocumentType.SALES_ORDER:
            raise ValueError(f"Document ID {sales_order_id} is not a Sales Order.")
        if so_doc.status not in [SalesDocumentStatus.SO_FULFILLED, SalesDocumentStatus.SO_CLOSED]:
            raise ValueError(f"Only fulfilled or closed Sales Orders can be converted to Invoices. Current status: {so_doc.status.value}")

        invoice_number = self._generate_sales_document_number(SalesDocumentType.INVOICE)
        created_date_str = datetime.datetime.now().isoformat()

        # Default due date if not provided (e.g., 30 days from creation)
        final_due_date_iso = due_date_iso
        if not final_due_date_iso:
            final_due_date_iso = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()

        new_invoice_id = self.sales_repo.add_sales_document(
            doc_number=invoice_number,
            customer_id=so_doc.customer_id,
            document_type=SalesDocumentType.INVOICE.value,
            created_date=created_date_str,
            status=SalesDocumentStatus.INVOICE_DRAFT.value,
            reference_number=so_doc.reference_number,
            due_date=final_due_date_iso,
            notes=so_doc.notes,
            subtotal=so_doc.subtotal,
            taxes=so_doc.taxes,
            total_amount=so_doc.total_amount,
            related_quote_id=so_doc.id
        )

        if not new_invoice_id:
            raise Exception("Failed to create invoice record in database.")

        # Copy items from sales order to invoice
        so_items = self.get_items_for_sales_document(sales_order_id)
        for item in so_items:
            self.sales_repo.add_sales_document_item(
                sales_doc_id=new_invoice_id,
                product_id=item.product_id,
                product_description=item.product_description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_percentage=item.discount_percentage,
                line_total=item.line_total
            )

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
        # Example: Sales Order specific transitions
        elif doc.document_type == SalesDocumentType.SALES_ORDER:
            valid_so_statuses = [s for s in SalesDocumentStatus if s.name.startswith("SO_")]
            if new_status not in valid_so_statuses:
                raise ValueError(f"Invalid status '{new_status.value}' for a Sales Order.")
        # Example: Invoice specific transitions
        elif doc.document_type == SalesDocumentType.INVOICE:
            valid_invoice_statuses = [s for s in SalesDocumentStatus if s.name.startswith("INVOICE_")]
            if new_status not in valid_invoice_statuses:
                raise ValueError(f"Invalid status '{new_status.value}' for an Invoice.")


        self.sales_repo.update_sales_document(doc_id, {"status": new_status.value})
        return self.get_sales_document_details(doc_id)

    def update_document_notes(self, doc_id: int, notes: str) -> Optional[SalesDocument]:
        doc = self.get_sales_document_details(doc_id)
        if not doc:
            raise ValueError(f"Sales document with ID {doc_id} not found.")
        self.sales_repo.update_sales_document(doc_id, {"notes": notes})
        return self.get_sales_document_details(doc_id)

    def get_calculated_price(self, customer_id: int, product_id: int) -> float | None:
        """Calculates the price for a given customer and product, applying pricing rules."""
        final_unit_price = None
        address_book_logic = AddressBookLogic(self._db)
        customer = address_book_logic.get_account_details(customer_id)
        if customer and customer.pricing_rule_id:
            rule = address_book_logic.get_pricing_rule(customer.pricing_rule_id)
            if rule:
                product_info = self.product_repo.get_product_details(product_id)
                if product_info:
                    product_cost = product_info.get('cost')
                    if product_cost is not None:
                        final_unit_price = product_cost
                        if rule.fixed_markup is not None:
                            final_unit_price += rule.fixed_markup
                        if rule.markup_percentage is not None:
                            final_unit_price *= (1 + rule.markup_percentage / 100)

        if final_unit_price is None:
            product_info = self.product_repo.get_product_details(product_id)
            if product_info:
                final_unit_price = product_info.get('sale_price')

        return final_unit_price

    def get_sales_document_details(self, doc_id: int) -> Optional[SalesDocument]:
        doc_data = self.sales_repo.get_sales_document_by_id(doc_id)
        if doc_data:
            status_enum = None
            if doc_data.get("status"):
                try:
                    status_enum = SalesDocumentStatus(doc_data["status"])
                except ValueError:
                    logger.warning(
                        "Invalid sales status '%s' in DB for doc ID %s",
                        doc_data["status"],
                        doc_id,
                    )

            doc_type_enum = None
            if doc_data.get("document_type"):
                try:
                    doc_type_enum = SalesDocumentType(doc_data["document_type"])
                except ValueError:
                    logger.warning(
                        "Invalid sales document type '%s' in DB for doc ID %s",
                        doc_data["document_type"],
                        doc_id,
                    )

            return SalesDocument(
                doc_id=doc_data["id"],
                document_number=doc_data["document_number"],
                customer_id=doc_data["customer_id"],
                document_type=doc_type_enum,
                created_date=doc_data["created_date"],
                expiry_date=doc_data.get("expiry_date"),
                due_date=doc_data.get("due_date"),
                status=status_enum,
                notes=doc_data.get("notes"),
                reference_number=doc_data.get("reference_number"),
                subtotal=doc_data.get("subtotal"),
                taxes=doc_data.get("taxes"),
                total_amount=doc_data.get("total_amount"),
                related_quote_id=doc_data.get("related_quote_id"),
                is_active=bool(doc_data.get("is_active", True)),
            )
        return None

    def get_all_sales_documents_by_criteria(
        self,
        customer_id: int = None,
        doc_type: SalesDocumentType = None,
        status: SalesDocumentStatus = None,
        is_active: Optional[bool] = True,
    ) -> List[SalesDocument]:
        doc_type_value = doc_type.value if doc_type else None
        status_value = status.value if status else None

        docs_data = self.sales_repo.get_all_sales_documents(
            customer_id=customer_id,
            document_type=doc_type_value,
            status=status_value,
            is_active=is_active,
        )
        result_list = []
        for doc_data in docs_data:
            status_enum = None
            if doc_data.get("status"):
                try:
                    status_enum = SalesDocumentStatus(doc_data["status"])
                except ValueError:
                    logger.warning(
                        "Invalid sales status '%s' in DB for doc ID %s",
                        doc_data["status"],
                        doc_data["id"],
                    )

            doc_type_enum = None
            if doc_data.get("document_type"):
                try:
                    doc_type_enum = SalesDocumentType(doc_data["document_type"])
                except ValueError:
                    logger.warning(
                        "Invalid sales document type '%s' in DB for doc ID %s",
                        doc_data["document_type"],
                        doc_data["id"],
                    )

            result_list.append(
                SalesDocument(
                    doc_id=doc_data["id"],
                    document_number=doc_data["document_number"],
                    customer_id=doc_data["customer_id"],
                    document_type=doc_type_enum,
                    created_date=doc_data["created_date"],
                    expiry_date=doc_data.get("expiry_date"),
                    due_date=doc_data.get("due_date"),
                    status=status_enum,
                    notes=doc_data.get("notes"),
                    subtotal=doc_data.get("subtotal"),
                    taxes=doc_data.get("taxes"),
                    total_amount=doc_data.get("total_amount"),
                    related_quote_id=doc_data.get("related_quote_id"),
                    is_active=bool(doc_data.get("is_active", True)),
                )
            )
        return result_list

    def get_items_for_sales_document(self, doc_id: int) -> List[SalesDocumentItem]:
        items_data = self.sales_repo.get_items_for_sales_document(doc_id)
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
                line_total=item_data.get('line_total'),
                note=item_data.get('note')
            ))
        return result_list

    def get_sales_document_item_details(self, item_id: int) -> Optional[SalesDocumentItem]:
        item_data = self.sales_repo.get_sales_document_item_by_id(item_id)
        if item_data:
            return SalesDocumentItem(
                item_id=item_data['id'],
                sales_document_id=item_data['sales_document_id'],
                product_id=item_data.get('product_id'),
                product_description=item_data['product_description'],
                quantity=item_data['quantity'],
                unit_price=item_data.get('unit_price'),
                discount_percentage=item_data.get('discount_percentage'),
                line_total=item_data.get('line_total'),
                note=item_data.get('note')
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

        self.sales_repo.delete_sales_document_item(item_id)
        self._recalculate_sales_document_totals(doc.id)


    def confirm_sales_order(self, doc_id: int) -> SalesDocument:
        """Mark a sales order as fulfilled."""
        doc = self.get_sales_document_details(doc_id)
        if not doc:
            raise ValueError(f"Sales document with ID {doc_id} not found.")
        if doc.document_type != SalesDocumentType.SALES_ORDER:
            raise ValueError("Only sales orders can be confirmed.")
        if doc.status != SalesDocumentStatus.SO_OPEN:
            raise ValueError(
                f"Sales order must be in status '{SalesDocumentStatus.SO_OPEN.value}' to confirm."
            )
        self.sales_repo.update_sales_document(
            doc_id, {"status": SalesDocumentStatus.SO_FULFILLED.value}
        )
        return self.get_sales_document_details(doc_id)

    def delete_sales_document(self, doc_id: int):
        doc = self.get_sales_document_details(doc_id)
        if not doc:
            raise ValueError(f"Sales document with ID {doc_id} not found.")

        items = self.get_items_for_sales_document(doc_id)
        if items:
            deletable_doc_statuses = [
                SalesDocumentStatus.QUOTE_DRAFT,
                SalesDocumentStatus.QUOTE_REJECTED,
                SalesDocumentStatus.QUOTE_EXPIRED,
                SalesDocumentStatus.INVOICE_DRAFT,
                SalesDocumentStatus.INVOICE_VOID,
            ]
            if doc.status not in deletable_doc_statuses:
                raise ValueError(
                    f"Cannot delete document with status '{doc.status.value}' that has items. Consider voiding first."
                )

        # Soft delete by marking inactive
        self.sales_repo.delete_sales_document(doc_id)
