import datetime
from typing import Optional, List
from core.database import DatabaseHandler # Assuming DatabaseHandler is in core.database
from shared.structs import PurchaseDocument, PurchaseDocumentItem, PurchaseDocumentStatus, Account, AccountType # Import Account and AccountType

class PurchaseLogic:
    def __init__(self, db_handler: DatabaseHandler):
        self.db = db_handler

    def _generate_document_number(self, prefix: str) -> str:
        """Generates a unique document number, e.g., RFQ-YYYYMMDD-XXXX or PO-YYYYMMDD-XXXX."""
        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d")

        all_docs_raw = self.db.get_all_purchase_documents()

        current_max_seq = 0
        search_prefix_full = f"{prefix}-{date_str}-"

        for doc_dict in all_docs_raw:
            doc_num = doc_dict.get("document_number")
            if doc_num and doc_num.startswith(search_prefix_full):
                try:
                    seq_part = int(doc_num.split('-')[-1])
                    if seq_part > current_max_seq:
                        current_max_seq = seq_part
                except ValueError:
                    pass

        next_seq = current_max_seq + 1
        return f"{search_prefix_full}{next_seq:04d}"

    # TODO: PurchaseLogic will need access to ProductLogic or direct product fetching methods from DB
    # For now, product_description will be passed through if product_id is also given.
    # A more robust solution would fetch description from product_id if not overridden.

    def create_rfq(self, vendor_id: int, notes: str = None) -> Optional[PurchaseDocument]:
        """Creates a new Request for Quote (RFQ)."""
        vendor_account_dict = self.db.get_account_details(vendor_id)
        if not vendor_account_dict:
            raise ValueError(f"Vendor with ID {vendor_id} not found.")

        if vendor_account_dict.get('account_type') != AccountType.VENDOR.value:
             raise ValueError(f"Account ID {vendor_id} is not a registered Vendor.")

        doc_number = self._generate_document_number("RFQ")
        created_date_str = datetime.datetime.now().isoformat()

        new_doc_id = self.db.add_purchase_document(
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
                             total_price: Optional[float] = None) -> Optional[PurchaseDocumentItem]:
        """Adds an item (linked to a product) to an RFQ or PO."""
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Purchase document with ID {doc_id} not found.")

        if doc.status not in [PurchaseDocumentStatus.RFQ, PurchaseDocumentStatus.PO_ISSUED, PurchaseDocumentStatus.QUOTED]:
             # Allow adding items to RFQ, Quoted (e.g. vendor adds more options), or PO_ISSUED (e.g. change order)
             pass

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        final_description = product_description_override
        if not final_description:
            product_info = self.db.get_product_details(product_id)
            if product_info and product_info.get('name'):
                final_description = product_info.get('name')
            else:
                final_description = f"Product ID: {product_id}"

        # Calculate total_price if unit_price is provided
        if unit_price is not None and total_price is None: # total_price might be pre-calculated by UI
            total_price = quantity * unit_price

        new_item_id = self.db.add_purchase_document_item(
            doc_id=doc_id,
            product_id=product_id,
            product_description=final_description,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price
        )
        if new_item_id:
            return self.get_purchase_document_item_details(new_item_id)
        return None

    def update_document_item(self, item_id: int, product_id: int, quantity: float,
                             unit_price: Optional[float],
                             product_description_override: Optional[str] = None) -> Optional[PurchaseDocumentItem]:
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
                 product_info = self.db.get_product_details(product_id)
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
        item_to_update.calculate_total_price()

        self.db.update_purchase_document_item(
            item_id=item_to_update.id,
            product_id=item_to_update.product_id,
            product_description=item_to_update.product_description,
            quantity=item_to_update.quantity,
            unit_price=item_to_update.unit_price,
            total_price=item_to_update.total_price
        )

        if unit_price is not None:
            parent_doc = self.get_purchase_document_details(item_to_update.purchase_document_id)
            if parent_doc and parent_doc.status == PurchaseDocumentStatus.RFQ:
                self.db.update_purchase_document_status(parent_doc.id, PurchaseDocumentStatus.QUOTED.value)

        return self.get_purchase_document_item_details(item_id)

    def convert_rfq_to_po(self, doc_id: int) -> Optional[PurchaseDocument]:
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found.")

        if doc.status != PurchaseDocumentStatus.QUOTED:
            raise ValueError(f"Only RFQs with status 'Quoted' can be converted to PO. Current status: {doc.status.value}")

        self.db.update_purchase_document_status(doc_id, PurchaseDocumentStatus.PO_ISSUED.value)
        return self.get_purchase_document_details(doc_id)

    def mark_document_received(self, doc_id: int) -> Optional[PurchaseDocument]:
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found.")

        if doc.status != PurchaseDocumentStatus.PO_ISSUED:
            raise ValueError(f"Only POs with status 'PO-Issued' can be marked as Received. Current status: {doc.status.value}")

        self.db.update_purchase_document_status(doc_id, PurchaseDocumentStatus.RECEIVED.value)
        return self.get_purchase_document_details(doc_id)

    def close_purchase_document(self, doc_id: int) -> Optional[PurchaseDocument]:
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found.")

        if doc.status != PurchaseDocumentStatus.RECEIVED:
            raise ValueError(f"Only documents with status 'Received' can be closed. Current status: {doc.status.value}")

        self.db.update_purchase_document_status(doc_id, PurchaseDocumentStatus.CLOSED.value)
        return self.get_purchase_document_details(doc_id)

    def update_document_notes(self, doc_id: int, notes: str) -> Optional[PurchaseDocument]:
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found.")
        self.db.update_purchase_document_notes(doc_id, notes)
        return self.get_purchase_document_details(doc_id)

    def update_document_status(self, doc_id: int, new_status: PurchaseDocumentStatus) -> Optional[PurchaseDocument]:
        """Updates the status of a purchase document."""
        # Basic validation or transition logic can be added here if needed.
        # For now, directly update using the DB handler.
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found for status update.")

        # Example: Prevent changing status from Closed (can be more elaborate)
        if doc.status == PurchaseDocumentStatus.CLOSED and new_status != PurchaseDocumentStatus.CLOSED:
            raise ValueError("Cannot change status of a closed document.")

        self.db.update_purchase_document_status(doc_id, new_status.value)
        return self.get_purchase_document_details(doc_id) # Return updated document

    def get_purchase_document_details(self, doc_id: int) -> Optional[PurchaseDocument]:
        doc_data = self.db.get_purchase_document_by_id(doc_id)
        if doc_data:
            status_enum = None
            if doc_data.get('status'):
                try:
                    status_enum = PurchaseDocumentStatus(doc_data['status'])
                except ValueError:
                     print(f"Warning: Invalid status '{doc_data['status']}' in DB for doc ID {doc_id}")

            return PurchaseDocument(
                doc_id=doc_data['id'],
                document_number=doc_data['document_number'],
                vendor_id=doc_data['vendor_id'],
                created_date=doc_data['created_date'],
                status=status_enum,
                notes=doc_data.get('notes')
            )
        return None

    def get_all_documents_by_criteria(self, vendor_id: int = None, status: PurchaseDocumentStatus = None) -> List[PurchaseDocument]:
        status_value = status.value if status else None
        docs_data = self.db.get_all_purchase_documents(vendor_id=vendor_id, status=status_value)
        result_list = []
        for doc_data in docs_data:
            status_enum = None
            if doc_data.get('status'):
                try:
                    status_enum = PurchaseDocumentStatus(doc_data['status'])
                except ValueError:
                    print(f"Warning: Invalid status '{doc_data['status']}' in DB for doc ID {doc_data['id']}")

            result_list.append(PurchaseDocument(
                doc_id=doc_data['id'],
                document_number=doc_data['document_number'],
                vendor_id=doc_data['vendor_id'],
                created_date=doc_data['created_date'],
                status=status_enum,
                notes=doc_data.get('notes')
            ))
        return result_list

    def get_items_for_document(self, doc_id: int) -> List[PurchaseDocumentItem]:
        items_data = self.db.get_items_for_document(doc_id)
        result_list = []
        for item_data in items_data:
            result_list.append(PurchaseDocumentItem(
                item_id=item_data['id'],
                purchase_document_id=item_data['purchase_document_id'],
                product_id=item_data.get('product_id'),
                product_description=item_data['product_description'],
                quantity=item_data['quantity'],
                unit_price=item_data.get('unit_price'),
                total_price=item_data.get('total_price')
            ))
        return result_list

    def get_purchase_document_item_details(self, item_id: int) -> Optional[PurchaseDocumentItem]:
        item_data = self.db.get_purchase_document_item_by_id(item_id)
        if item_data:
            return PurchaseDocumentItem(
                item_id=item_data['id'],
                purchase_document_id=item_data['purchase_document_id'],
                product_id=item_data.get('product_id'),
                product_description=item_data['product_description'],
                quantity=item_data['quantity'],
                unit_price=item_data.get('unit_price'),
                total_price=item_data.get('total_price')
            )
        return None

    def delete_document_item(self, item_id: int):
        item = self.get_purchase_document_item_details(item_id)
        if not item:
            raise ValueError(f"Item with ID {item_id} not found.")

        doc = self.get_purchase_document_details(item.purchase_document_id)
        if doc and doc.status not in [PurchaseDocumentStatus.RFQ, PurchaseDocumentStatus.QUOTED]:
            pass

        self.db.delete_purchase_document_item(item_id)

    def delete_purchase_document(self, doc_id: int):
        doc = self.get_purchase_document_details(doc_id)
        if not doc:
            raise ValueError(f"Document with ID {doc_id} not found.")

        self.db.delete_purchase_document(doc_id)

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
