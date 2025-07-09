import datetime
from core.database import DatabaseHandler # Assuming DatabaseHandler is accessible
from shared.structs import SalesDocument, SalesDocumentItem, Product # Assuming these structs

class SalesLogic:
    def __init__(self, db_handler: DatabaseHandler):
        self.db = db_handler

    def create_sales_document(self, customer_id: int, document_date: datetime.date,
                              status: str, items_data: list[dict]) -> int | None:
        """
        Creates a new sales document and its items.
        items_data is a list of dictionaries, each like:
        {'product_id': X, 'quantity': Y}
        Returns the new sales_document_id or None if error.
        """
        if not customer_id or not document_date or not status:
            # Basic validation
            return None

        total_amount = 0
        document_items = []

        for item_data in items_data:
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity')

            if not product_id or quantity is None or quantity <= 0:
                # Invalid item data
                return None

            unit_price = self.db.get_product_price_for_sales_document(product_id)
            if unit_price is None:
                # Product not found or price not available
                return None

            line_total = quantity * unit_price
            total_amount += line_total
            document_items.append({
                'product_id': product_id,
                'quantity': quantity,
                'unit_price': unit_price,
                'line_total': line_total
            })

        try:
            doc_date_iso = document_date.isoformat()
            document_id = self.db.add_sales_document(
                customer_id=customer_id,
                document_date=doc_date_iso,
                status=status,
                total_amount=total_amount
            )

            if not document_id:
                # Failed to create document header
                return None

            for item in document_items:
                self.db.add_sales_document_item(
                    document_id=document_id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    line_total=item['line_total']
                )

            return document_id
        except Exception as e:
            # Log error e
            print(f"Error creating sales document: {e}")
            # Potentially rollback or cleanup if transactionality is not handled by DB wrapper on partial failure
            return None

    def get_sales_document_details(self, document_id: int) -> SalesDocument | None:
        """
        Retrieves a sales document and its items.
        Returns a SalesDocument object (which could contain its items) or None.
        """
        doc_data = self.db.get_sales_document(document_id)
        if not doc_data:
            return None

        sales_doc = SalesDocument(
            document_id=doc_data['document_id'],
            customer_id=doc_data['customer_id'],
            document_date=datetime.date.fromisoformat(doc_data['document_date']) if doc_data.get('document_date') else None,
            status=doc_data['status'],
            total_amount=doc_data['total_amount']
        )

        # Add customer name to the sales_doc object if needed, e.g., sales_doc.customer_name = doc_data.get('customer_name')
        # This depends on whether SalesDocument struct is extended or if UI handles this separately

        items_data = self.db.get_sales_document_items(document_id)
        sales_doc.items = [] # Assuming SalesDocument struct can hold items
        for item_data in items_data:
            item = SalesDocumentItem(
                item_id=item_data['item_id'],
                document_id=item_data['document_id'],
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                line_total=item_data['line_total']
            )
            # Add product_name to item if needed: item.product_name = item_data.get('product_name')
            sales_doc.items.append(item)

        return sales_doc

    def get_all_sales_documents(self, customer_id: int = None) -> list[SalesDocument]:
        """Retrieves all sales documents, optionally filtered by customer."""
        docs_data = self.db.get_all_sales_documents(customer_id=customer_id)
        sales_documents = []
        for doc_data in docs_data:
            doc = SalesDocument(
                document_id=doc_data['document_id'],
                customer_id=doc_data['customer_id'],
                document_date=datetime.date.fromisoformat(doc_data['document_date']) if doc_data.get('document_date') else None,
                status=doc_data['status'],
                total_amount=doc_data['total_amount']
            )
            # Add customer_name if needed: doc.customer_name = doc_data.get('customer_name')
            sales_documents.append(doc)
        return sales_documents

    def update_sales_document_status(self, document_id: int, new_status: str) -> bool:
        """Updates the status of a sales document."""
        doc = self.db.get_sales_document(document_id)
        if not doc:
            return False
        try:
            self.db.update_sales_document(
                document_id=document_id,
                customer_id=doc['customer_id'],
                document_date=doc['document_date'], # Keep original date
                status=new_status,
                total_amount=doc['total_amount'] # Keep original total
            )
            return True
        except Exception as e:
            print(f"Error updating sales document status: {e}")
            return False

    def delete_sales_document(self, document_id: int) -> bool:
        """Deletes a sales document and its items (via CASCADE in DB)."""
        try:
            self.db.delete_sales_document(document_id)
            return True
        except Exception as e:
            print(f"Error deleting sales document: {e}")
            return False

    def update_sales_document_items(self, document_id: int, items_data: list[dict]) -> bool:
        """
        Updates items for a sales document.
        This can be complex: it might involve deleting all existing items and adding new ones,
        or trying to match and update existing items.
        For simplicity, this example will delete existing items and add the new set.
        The sales document's total_amount will be recalculated.
        """
        doc_header = self.db.get_sales_document(document_id)
        if not doc_header:
            return False # Document not found

        # Delete existing items for this document
        existing_items = self.db.get_sales_document_items(document_id)
        for item in existing_items:
            self.db.delete_sales_document_item(item['item_id'])

        new_total_amount = 0
        new_document_items = []

        for item_data in items_data:
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity')

            if not product_id or quantity is None or quantity <= 0:
                return False # Invalid item data

            unit_price = self.db.get_product_price_for_sales_document(product_id)
            if unit_price is None:
                return False # Product price not found

            line_total = quantity * unit_price
            new_total_amount += line_total
            new_document_items.append({
                'product_id': product_id,
                'quantity': quantity,
                'unit_price': unit_price,
                'line_total': line_total
            })

        try:
            # Add new items
            for item in new_document_items:
                self.db.add_sales_document_item(
                    document_id=document_id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    line_total=item['line_total']
                )

            # Update the document header with the new total amount
            self.db.update_sales_document(
                document_id=document_id,
                customer_id=doc_header['customer_id'],
                document_date=doc_header['document_date'],
                status=doc_header['status'], # Keep original status or allow update
                total_amount=new_total_amount
            )
            return True
        except Exception as e:
            print(f"Error updating sales document items: {e}")
            return False

    # Individual item management (optional, if needed beyond full replacement)
    def add_item_to_sales_document(self, document_id: int, product_id: int, quantity: int) -> bool:
        """Adds a single item to an existing sales document and recalculates total."""
        doc = self.db.get_sales_document(document_id)
        if not doc: return False

        unit_price = self.db.get_product_price_for_sales_document(product_id)
        if unit_price is None: return False

        line_total = quantity * unit_price

        try:
            self.db.add_sales_document_item(document_id, product_id, quantity, unit_price, line_total)
            new_total_amount = doc['total_amount'] + line_total
            self.db.update_sales_document(
                document_id=document_id,
                customer_id=doc['customer_id'],
                document_date=doc['document_date'],
                status=doc['status'],
                total_amount=new_total_amount
            )
            return True
        except Exception as e:
            print(f"Error adding item to sales document: {e}")
            return False

    def remove_item_from_sales_document(self, item_id: int) -> bool:
        """Removes an item from a sales document and recalculates total."""
        item_to_delete = self.db.get_sales_document_item(item_id)
        if not item_to_delete: return False

        document_id = item_to_delete['document_id']
        doc = self.db.get_sales_document(document_id)
        if not doc: return False # Should not happen if item exists

        try:
            self.db.delete_sales_document_item(item_id)
            new_total_amount = doc['total_amount'] - item_to_delete['line_total']
            self.db.update_sales_document(
                document_id=document_id,
                customer_id=doc['customer_id'],
                document_date=doc['document_date'],
                status=doc['status'],
                total_amount=new_total_amount
            )
            return True
        except Exception as e:
            print(f"Error removing item from sales document: {e}")
            return False

    def update_document_item_quantity(self, item_id: int, new_quantity: int) -> bool:
        """Updates an item's quantity and recalculates document total."""
        item_to_update = self.db.get_sales_document_item(item_id)
        if not item_to_update or new_quantity <= 0:
            return False

        document_id = item_to_update['document_id']
        doc = self.db.get_sales_document(document_id)
        if not doc: return False

        old_line_total = item_to_update['line_total']
        new_line_total = new_quantity * item_to_update['unit_price']

        try:
            self.db.update_sales_document_item(
                item_id=item_id,
                product_id=item_to_update['product_id'],
                quantity=new_quantity,
                unit_price=item_to_update['unit_price'],
                line_total=new_line_total
            )

            current_total_less_old_item = doc['total_amount'] - old_line_total
            final_total_amount = current_total_less_old_item + new_line_total

            self.db.update_sales_document(
                document_id=document_id,
                customer_id=doc['customer_id'],
                document_date=doc['document_date'],
                status=doc['status'],
                total_amount=final_total_amount
            )
            return True
        except Exception as e:
            print(f"Error updating item quantity: {e}")
            return False

# Example usage (illustrative, typically called from UI layer)
if __name__ == '__main__':
    # This is for demonstration; actual db_handler would be instantiated by the application
    # For this example, let's assume a db_handler is magically available
    # db_handler = DatabaseHandler(db_name='../address_book.db') # Adjust path as needed for direct script run

    # sales_logic = SalesLogic(db_handler)

    # # Example: Create a sales document
    # items = [{'product_id': 1, 'quantity': 2}, {'product_id': 2, 'quantity': 1}] # Example product IDs
    # new_doc_id = sales_logic.create_sales_document(
    #     customer_id=1, # Example customer ID
    #     document_date=datetime.date.today(),
    #     status="Draft",
    #     items_data=items
    # )
    # if new_doc_id:
    #     print(f"Created sales document with ID: {new_doc_id}")
    #     details = sales_logic.get_sales_document_details(new_doc_id)
    #     if details:
    #         print(f"Details: {details.to_dict()}")
    #         if hasattr(details, 'items'):
    #             for item in details.items:
    #                 print(f"  Item: {item.to_dict()}")
    # else:
    #     print("Failed to create sales document.")

    # # Example: Get all sales documents
    # all_docs = sales_logic.get_all_sales_documents()
    # print(f"\nAll Sales Documents ({len(all_docs)}):")
    # for doc_summary in all_docs:
    #     print(doc_summary.to_dict())

    # db_handler.close()
    pass
