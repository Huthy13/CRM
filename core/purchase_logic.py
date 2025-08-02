import datetime
from typing import Optional, List
import logging
from core.database import DatabaseHandler
from core.inventory_service import InventoryService
from core.repositories import (
    PurchaseRepository,
    AccountRepository,
    ProductRepository,
    InventoryRepository,
)
from shared.structs import (
    PurchaseDocument,
    PurchaseDocumentItem,
    PurchaseDocumentStatus,
    Account,
    AccountType,
    InventoryTransactionType,
)

logger = logging.getLogger(__name__)


class PurchaseLogic:
    def __init__(
        self,
        repo_or_db,
        account_repo=None,
        product_repo=None,
        inventory_service: InventoryService | None = None,
    ):
        if isinstance(repo_or_db, PurchaseRepository):
            self.purchase_repo = repo_or_db
            db_handler = self.purchase_repo.db
            self.account_repo = account_repo or AccountRepository(db_handler)
            self.product_repo = product_repo or ProductRepository(db_handler)
        else:
            db_handler = repo_or_db
            self.purchase_repo = PurchaseRepository(db_handler)
            self.account_repo = account_repo or AccountRepository(db_handler)
            self.product_repo = product_repo or ProductRepository(db_handler)

        inv_repo = InventoryRepository(db_handler)
        self.inventory_service = inventory_service or InventoryService(
            inv_repo, self.product_repo
        )

    def _generate_document_number(self) -> str:
        """Generates a unique purchase document number in the format ``P#####``.

        The numbering is shared across all purchase documents.
        """
        prefix = "P"
        all_docs_raw = self.purchase_repo.get_all_purchase_documents(is_active=None)
        max_seq = -1
        for doc_dict in all_docs_raw:
            doc_num_str = doc_dict.get("document_number")
            if doc_num_str and doc_num_str.startswith(prefix):
                try:
                    seq_part = int(doc_num_str[len(prefix):])
                    if seq_part > max_seq:
                        max_seq = seq_part
                except (ValueError, IndexError):
                    pass  # Ignore malformed numbers

        next_seq = max_seq + 1
        return f"{prefix}{next_seq:05d}"

    # TODO: PurchaseLogic will need access to ProductLogic or direct product fetching methods from DB
    # For now, product_description will be passed through if product_id is also given.
    # A more robust solution would fetch description from product_id if not overridden.

    def create_rfq(self, vendor_id: int, notes: str = None) -> Optional[PurchaseDocument]:
        """Creates a new Request for Quote (RFQ)."""
        vendor_account_dict = self.account_repo.get_account_details(vendor_id)
        if not vendor_account_dict:
            raise ValueError(f"Vendor with ID {vendor_id} not found.")

        if vendor_account_dict.get('account_type') != AccountType.VENDOR.value:
             raise ValueError(f"Account ID {vendor_id} is not a registered Vendor.")

        doc_number = self._generate_document_number()
        created_date_str = datetime.datetime.now().isoformat()

        new_doc_id = self.purchase_repo.add_purchase_document(
            doc_number=doc_number,
            vendor_id=vendor_id,
            created_date=created_date_str,
            status=PurchaseDocumentStatus.RFQ.value,
            notes=notes
        )
        if new_doc_id:
            return self.get_purchase_document_details(new_doc_id)
        return None

    def add_item_to_document(self, doc_id: int, product_id: int, quantity: float,
                             product_description_override: Optional[str] = None,
                             unit_price: Optional[float] = None,
                             total_price: Optional[float] = None,
                             note: str | None = None) -> Optional[PurchaseDocumentItem]:
        """Adds an item (linked to a product) to an RFQ or PO."""
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Purchase document with ID {doc_id} not found.")

        if doc.status not in [
            PurchaseDocumentStatus.RFQ,
            PurchaseDocumentStatus.QUOTED,
            PurchaseDocumentStatus.PO_ISSUED,
        ]:
            # Only editable in these statuses
            raise ValueError(
                "Cannot add items unless document status is RFQ, Quoted, or PO-Issued."
            )

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        final_description = product_description_override
        if not final_description:
            product_info = self.product_repo.get_product_details(product_id)
            if product_info and product_info.get('name'):
                final_description = product_info.get('name')
            else:
                final_description = f"Product ID: {product_id}"

        # Calculate total_price if unit_price is provided
        if unit_price is not None and total_price is None: # total_price might be pre-calculated by UI
            total_price = quantity * unit_price

        new_item_id = self.purchase_repo.add_purchase_document_item(
            doc_id=doc_id,
            product_id=product_id,
            product_description=final_description,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            note=note
        )
        if new_item_id:
            return self.get_purchase_document_item_details(new_item_id)
        return None

    def update_document_item(self, item_id: int, product_id: int, quantity: float,
                             unit_price: Optional[float],
                             product_description_override: Optional[str] = None,
                             note: str | None = None) -> Optional[PurchaseDocumentItem]:
        """Updates an existing document item. If unit_price is provided for an RFQ item, status may change to Quoted."""
        item_to_update = self.get_purchase_document_item_details(item_id)
        if not item_to_update:
            raise ValueError(f"Item with ID {item_id} not found for update.")

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if unit_price is not None and unit_price < 0:
            raise ValueError("Unit price cannot be negative if provided.")

        final_description = product_description_override
        if not final_description:
            if item_to_update.product_id != product_id or not item_to_update.product_description:
                 product_info = self.product_repo.get_product_details(product_id)
                 if product_info and product_info.get('name'):
                     final_description = product_info.get('name')
                 else:
                     final_description = f"Product ID: {product_id}"
            else:
                final_description = item_to_update.product_description

        item_to_update.product_id = product_id
        item_to_update.product_description = final_description
        item_to_update.quantity = quantity
        item_to_update.unit_price = unit_price
        item_to_update.note = note if note is not None else item_to_update.note
        item_to_update.calculate_total_price()

        self.purchase_repo.update_purchase_document_item(
            item_id=item_to_update.id,
            product_id=item_to_update.product_id,
            product_description=item_to_update.product_description,
            quantity=item_to_update.quantity,
            unit_price=item_to_update.unit_price,
            total_price=item_to_update.total_price,
            note=item_to_update.note
        )

        if unit_price is not None:
            parent_doc = self.get_purchase_document_details(item_to_update.purchase_document_id)
            if parent_doc and parent_doc.status == PurchaseDocumentStatus.RFQ:
                self.purchase_repo.update_purchase_document_status(parent_doc.id, PurchaseDocumentStatus.QUOTED.value)

        return self.get_purchase_document_item_details(item_id)

    def convert_rfq_to_po(self, doc_id: int) -> Optional[PurchaseDocument]:
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found.")

        if doc.status != PurchaseDocumentStatus.QUOTED:
            raise ValueError(f"Only RFQs with status 'Quoted' can be converted to PO. Current status: {doc.status.value}")

        # When converting, we can either update the status and keep the number,
        # or generate a new PO number. Generating a new PO number is often cleaner.
        new_po_number = self._generate_document_number()
        self.purchase_repo.update_purchase_document(doc_id, {
            "status": PurchaseDocumentStatus.PO_ISSUED.value,
            "document_number": new_po_number
        })
        items = self.get_items_for_document(doc_id)
        for item in items:
            if item.product_id:
                self.inventory_service.record_purchase_order(
                    item.product_id, item.quantity, reference=f"PO#{new_po_number}"
                )
        return self.get_purchase_document_details(doc_id)

    def mark_document_received(self, doc_id: int) -> Optional[PurchaseDocument]:
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found.")

        if doc.status != PurchaseDocumentStatus.PO_ISSUED:
            raise ValueError(f"Only POs with status 'PO-Issued' can be marked as Received. Current status: {doc.status.value}")

        self.purchase_repo.update_purchase_document_status(doc_id, PurchaseDocumentStatus.RECEIVED.value)
        return self.get_purchase_document_details(doc_id)

    def close_purchase_document(self, doc_id: int) -> Optional[PurchaseDocument]:
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found.")

        if doc.status != PurchaseDocumentStatus.RECEIVED:
            raise ValueError(f"Only documents with status 'Received' can be closed. Current status: {doc.status.value}")

        self.purchase_repo.update_purchase_document_status(doc_id, PurchaseDocumentStatus.CLOSED.value)
        return self.get_purchase_document_details(doc_id)

    def update_document_notes(self, doc_id: int, notes: str) -> Optional[PurchaseDocument]:
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found.")
        self.purchase_repo.update_purchase_document_notes(doc_id, notes)
        return self.get_purchase_document_details(doc_id)

    def update_document_status(self, doc_id: int, new_status: PurchaseDocumentStatus) -> Optional[PurchaseDocument]:
        """Updates the status of a purchase document.

        Handles transitions that require inventory adjustments or special
        numbering such as converting an RFQ into a purchase order or receiving
        an issued PO.
        """
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found for status update.")

        # No change requested
        if doc.status == new_status:
            return doc

        # Prevent updates to closed documents
        if doc.status == PurchaseDocumentStatus.CLOSED and new_status != PurchaseDocumentStatus.CLOSED:
            raise ValueError("Cannot change status of a closed document.")

        # Converting a quoted RFQ into an issued PO
        if new_status == PurchaseDocumentStatus.PO_ISSUED and doc.status != PurchaseDocumentStatus.PO_ISSUED:
            return self.convert_rfq_to_po(doc_id)

        # Receiving an issued PO affects inventory
        if new_status == PurchaseDocumentStatus.RECEIVED and doc.status == PurchaseDocumentStatus.PO_ISSUED:
            return self.receive_purchase_order(doc_id)

        # Reverting an issued PO prior to receipt should clear on-order qty
        if doc.status == PurchaseDocumentStatus.PO_ISSUED and new_status != PurchaseDocumentStatus.RECEIVED:
            items = self.get_items_for_document(doc_id)
            for item in items:
                if item.product_id:
                    self.inventory_service.record_purchase_order(
                        item.product_id,
                        -item.quantity,
                        reference=f"PO#{doc.document_number}",
                    )

        self.purchase_repo.update_purchase_document_status(doc_id, new_status.value)
        return self.get_purchase_document_details(doc_id)

    def get_purchase_document_details(self, doc_id: int) -> Optional[PurchaseDocument]:
        doc_data = self.purchase_repo.get_purchase_document_by_id(doc_id)
        if doc_data:
            status_enum = None
            if doc_data.get("status"):
                try:
                    status_enum = PurchaseDocumentStatus(doc_data["status"])
                except ValueError:
                    logger.warning(
                        "Invalid status '%s' in DB for doc ID %s",
                        doc_data["status"],
                        doc_id,
                    )

            return PurchaseDocument(
                doc_id=doc_data["id"],
                document_number=doc_data["document_number"],
                vendor_id=doc_data["vendor_id"],
                created_date=doc_data["created_date"],
                status=status_enum,
                notes=doc_data.get("notes"),
                is_active=bool(doc_data.get("is_active", True)),
            )
        return None

    def get_all_documents_by_criteria(
        self,
        vendor_id: int = None,
        status: PurchaseDocumentStatus = None,
        is_active: Optional[bool] = True,
    ) -> List[PurchaseDocument]:
        status_value = status.value if status else None
        docs_data = self.purchase_repo.get_all_purchase_documents(
            vendor_id=vendor_id, status=status_value, is_active=is_active
        )
        result_list = []
        for doc_data in docs_data:
            status_enum = None
            if doc_data.get("status"):
                try:
                    status_enum = PurchaseDocumentStatus(doc_data["status"])
                except ValueError:
                    logger.warning(
                        "Invalid status '%s' in DB for doc ID %s",
                        doc_data["status"],
                        doc_data["id"],
                    )

            result_list.append(
                PurchaseDocument(
                    doc_id=doc_data["id"],
                    document_number=doc_data["document_number"],
                    vendor_id=doc_data["vendor_id"],
                    created_date=doc_data["created_date"],
                    status=status_enum,
                    notes=doc_data.get("notes"),
                    is_active=bool(doc_data.get("is_active", True)),
                )
            )
        return result_list

    def get_items_for_document(self, doc_id: int) -> List[PurchaseDocumentItem]:
        items_data = self.purchase_repo.get_items_for_document(doc_id)
        result_list = []
        for item_data in items_data:
            result_list.append(PurchaseDocumentItem(
                item_id=item_data['id'],
                purchase_document_id=item_data['purchase_document_id'],
                product_id=item_data.get('product_id'),
                product_description=item_data['product_description'],
                quantity=item_data['quantity'],
                unit_price=item_data.get('unit_price'),
                total_price=item_data.get('total_price'),
                note=item_data.get('note')
            ))
        return result_list

    def get_purchase_document_item_details(self, item_id: int) -> Optional[PurchaseDocumentItem]:
        item_data = self.purchase_repo.get_purchase_document_item_by_id(item_id)
        if item_data:
            return PurchaseDocumentItem(
                item_id=item_data['id'],
                purchase_document_id=item_data['purchase_document_id'],
                product_id=item_data.get('product_id'),
                product_description=item_data['product_description'],
                quantity=item_data['quantity'],
                unit_price=item_data.get('unit_price'),
                total_price=item_data.get('total_price'),
                note=item_data.get('note')
            )
        return None

    def delete_document_item(self, item_id: int):
        item = self.get_purchase_document_item_details(item_id)
        if not item:
            raise ValueError(f"Item with ID {item_id} not found.")

        doc = self.get_purchase_document_details(item.purchase_document_id)
        if doc and doc.status not in [
            PurchaseDocumentStatus.RFQ,
            PurchaseDocumentStatus.QUOTED,
            PurchaseDocumentStatus.PO_ISSUED,
        ]:
            raise ValueError(
                "Cannot delete items unless document status is RFQ, Quoted, or PO-Issued."
            )

        self.purchase_repo.delete_purchase_document_item(item_id)

    def receive_purchase_order(self, doc_id: int) -> PurchaseDocument:
        """Increment inventory for a received purchase order."""
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Purchase document with ID {doc_id} not found.")
        if doc.status != PurchaseDocumentStatus.PO_ISSUED:
            raise ValueError(
                "Cannot receive a document that is not an issued purchase order."
            )
        items = self.get_items_for_document(doc_id)
        for item in items:
            if item.product_id:
                self.inventory_service.record_purchase_order(
                    item.product_id, -item.quantity, reference=f"PO#{doc.document_number}"
                )
                self.inventory_service.adjust_stock(
                    item.product_id,
                    item.quantity,
                    InventoryTransactionType.PURCHASE,
                    reference=f"PO#{doc.document_number}",
                )
        self.purchase_repo.update_purchase_document_status(
            doc_id, PurchaseDocumentStatus.RECEIVED.value
        )
        return self.get_purchase_document_details(doc_id)

    def delete_purchase_document(self, doc_id: int):
        """Soft delete a purchase document and adjust inventory if needed."""
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found.")

        # If the document represents an issued PO, remove on-order quantities
        if doc.status == PurchaseDocumentStatus.PO_ISSUED:
            items = self.get_items_for_document(doc_id)
            for item in items:
                if item.product_id:
                    self.inventory_service.record_purchase_order(
                        item.product_id,
                        -item.quantity,
                        reference=f"PO#{doc.document_number}",
                    )

        # Mark document inactive
        self.purchase_repo.delete_purchase_document(doc_id)

# Remove the old update_item_quote method as its functionality is merged into update_document_item
# def update_item_quote(self, item_id: int, unit_price: float) -> Optional[PurchaseDocumentItem]:
#     """Updates the unit price for an item and recalculates total. Sets document to 'Quoted'."""
#     item_dict = self.db.get_purchase_document_item_by_id(item_id)
#     if not item_dict:
#         raise ValueError(f"Item with ID {item_id} not found.")
#     item_obj = PurchaseDocumentItem(
#         item_id=item_dict['id'],
#         purchase_document_id=item_dict['purchase_document_id'],
#         product_id=item_dict.get('product_id'),
#         product_description=item_dict['product_description'],
#         quantity=item_dict['quantity'],
#         unit_price=item_dict.get('unit_price'),
#         total_price=item_dict.get('total_price')
#     )
#     if unit_price < 0:
#         raise ValueError("Unit price cannot be negative.")
#     item_obj.unit_price = unit_price
#     item_obj.calculate_total_price()
#     self.db.update_purchase_document_item(
#         item_id=item_obj.id,
#         product_id=item_obj.product_id,
#         product_description=item_obj.product_description,
#         quantity=item_obj.quantity,
#         unit_price=item_obj.unit_price,
#         total_price=item_obj.total_price
#     )
#     doc = self.get_purchase_document_details(item_obj.purchase_document_id)
#     if doc and doc.status == PurchaseDocumentStatus.RFQ:
#         self.db.update_purchase_document_status(doc.id, PurchaseDocumentStatus.QUOTED.value)
#     return self.get_purchase_document_item_details(item_id)
