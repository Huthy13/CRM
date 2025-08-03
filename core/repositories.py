import logging
from core.database import DatabaseHandler

logger = logging.getLogger(__name__)

class AddressRepository:
    """Repository for address-related database operations."""
    def __init__(self, db: DatabaseHandler):
        self.db = db

    def add_address(self, street, city, state, zip_code, country):
        return self.db.add_address(street, city, state, zip_code, country)

    def get_address(self, address_id):
        return self.db.get_address(address_id)

    def update_address(self, address_id, street, city, state, zip_code, country):
        self.db.update_address(address_id, street, city, state, zip_code, country)

    def get_existing_address_by_id(self, street, city, zip_code):
        return self.db.get_existing_address_by_id(street, city, zip_code)


class ContactRepository:
    """Repository for contact-related database operations."""
    def __init__(self, db: DatabaseHandler):
        self.db = db

    def get_contact_details(self, contact_id):
        return self.db.get_contact_details(contact_id)

    def add_contact(self, name, phone, email, role, account_id):
        return self.db.add_contact(name, phone, email, role, account_id)

    def update_contact(self, contact_id, name, phone, email, role, account_id):
        self.db.update_contact(contact_id, name, phone, email, role, account_id)

    def get_contacts_by_account(self, account_id):
        return self.db.get_contacts_by_account(account_id)

    def get_all_contacts(self):
        return self.db.get_all_contacts()

    def delete_contact(self, contact_id):
        self.db.delete_contact(contact_id)

    def get_all_users(self):
        return self.db.get_all_users()


class AccountRepository:
    """Repository for account-related database operations."""
    def __init__(self, db: DatabaseHandler):
        self.db = db

    def add_account_address(self, account_id, address_id, address_type, is_primary):
        self.db.add_account_address(account_id, address_id, address_type, is_primary)

    def get_account_addresses(self, account_id):
        return self.db.get_account_addresses(account_id)

    def add_account(self, name, phone, website, description, account_type, pricing_rule_id=None, payment_term_id=None):
        return self.db.add_account(name, phone, website, description, account_type, pricing_rule_id, payment_term_id)

    def get_all_accounts(self):
        return self.db.get_all_accounts()

    def get_accounts(self):
        return self.db.get_accounts()

    def delete_account(self, account_id):
        self.db.delete_account(account_id)

    def get_account_details(self, account_id):
        return self.db.get_account_details(account_id)

    def update_account(self, account_id, name, phone, website, description, account_type, pricing_rule_id=None, payment_term_id=None):
        self.db.update_account(account_id, name, phone, website, description, account_type, pricing_rule_id, payment_term_id)

    def clear_account_addresses(self, account_id):
        self.db.cursor.execute("DELETE FROM account_addresses WHERE account_id = ?", (account_id,))
        self.db.conn.commit()

    # Payment terms
    def add_payment_term(self, term_name, days=None):
        return self.db.add_payment_term(term_name, days)

    def get_payment_term(self, term_id):
        return self.db.get_payment_term(term_id)

    def get_all_payment_terms(self):
        return self.db.get_all_payment_terms()

    def update_payment_term(self, term_id, term_name, days=None):
        self.db.update_payment_term(term_id, term_name, days)

    def delete_payment_term(self, term_id):
        self.db.delete_payment_term(term_id)

    def assign_payment_term_to_account(self, account_id, term_id):
        self.db.assign_payment_term_to_account(account_id, term_id)

    def remove_payment_term_from_account(self, account_id):
        self.db.remove_payment_term_from_account(account_id)


class ProductRepository:
    """Repository for product-related operations."""
    def __init__(self, db: DatabaseHandler):
        self.db = db

    def add_product(self, **kwargs):
        return self.db.add_product(**kwargs)

    def update_product(self, **kwargs):
        self.db.update_product(**kwargs)

    def delete_product(self, product_id):
        self.db.delete_product(product_id)

    def get_product_details(self, product_id):
        return self.db.get_product_details(product_id)

    def get_all_products(self):
        return self.db.get_all_products()

    def get_all_product_categories_from_table(self):
        return self.db.get_all_product_categories_from_table()

    def add_product_category(self, name, parent_id=None):
        return self.db.add_product_category(name, parent_id)

    def update_product_category_name(self, category_id, new_name):
        self.db.update_product_category_name(category_id, new_name)

    def update_product_category_parent(self, category_id, new_parent_id):
        self.db.update_product_category_parent(category_id, new_parent_id)

    def delete_product_category(self, category_id):
        self.db.delete_product_category(category_id)

    def get_all_product_units_of_measure_from_table(self):
        return self.db.get_all_product_units_of_measure_from_table()

    def add_product_unit_of_measure(self, name):
        return self.db.add_product_unit_of_measure(name)

    # Pricing rules
    def add_pricing_rule(self, rule_name, markup_percentage=None, fixed_markup=None):
        return self.db.add_pricing_rule(rule_name, markup_percentage, fixed_markup)

    def get_pricing_rule(self, rule_id):
        return self.db.get_pricing_rule(rule_id)

    def get_all_pricing_rules(self):
        return self.db.get_all_pricing_rules()

    def update_pricing_rule(self, rule_id, rule_name, markup_percentage=None, fixed_markup=None):
        self.db.update_pricing_rule(rule_id, rule_name, markup_percentage, fixed_markup)

    def delete_pricing_rule(self, rule_id):
        self.db.delete_pricing_rule(rule_id)

    def assign_pricing_rule_to_customer(self, customer_id, rule_id):
        self.db.assign_pricing_rule_to_customer(customer_id, rule_id)

    def remove_pricing_rule_from_customer(self, customer_id):
        self.db.remove_pricing_rule_from_customer(customer_id)

    # Vendor associations
    def get_default_vendor(self, product_id):
        return self.db.get_default_vendor_for_product(product_id)


class TaskRepository:
    """Repository for task-related operations."""
    def __init__(self, db: DatabaseHandler):
        self.db = db

    def add_task(self, task_data: dict) -> int:
        return self.db.add_task(task_data)

    def get_task(self, task_id: int):
        return self.db.get_task(task_id)

    def get_tasks(self, **filters):
        return self.db.get_tasks(**filters)

    def update_task(self, task_id: int, task_data: dict):
        self.db.update_task(task_id, task_data)

    def delete_task(self, task_id: int, soft_delete: bool = True):
        self.db.delete_task(task_id, soft_delete)

    def update_task_status(self, task_id: int, new_status: str, updated_at_iso: str):
        self.db.update_task_status(task_id, new_status, updated_at_iso)

    def get_overdue_tasks(self, current_date_iso: str):
        return self.db.get_overdue_tasks(current_date_iso)


class PurchaseRepository:
    """Repository for purchase document operations."""
    def __init__(self, db: DatabaseHandler):
        self.db = db

    def add_purchase_document(self, **kwargs):
        return self.db.add_purchase_document(**kwargs)

    def get_purchase_document_by_id(self, doc_id: int):
        return self.db.get_purchase_document_by_id(doc_id)

    def get_all_purchase_documents(self, **filters):
        return self.db.get_all_purchase_documents(**filters)

    def update_purchase_document_status(self, doc_id: int, new_status: str):
        self.db.update_purchase_document_status(doc_id, new_status)

    def add_purchase_document_item(self, **kwargs):
        return self.db.add_purchase_document_item(**kwargs)

    def get_purchase_document_item_by_id(self, item_id: int):
        return self.db.get_purchase_document_item_by_id(item_id)

    def update_purchase_document_item(self, **kwargs):
        self.db.update_purchase_document_item(**kwargs)

    def update_purchase_document(self, doc_id: int, updates: dict):
        self.db.update_purchase_document(doc_id, updates)

    def update_purchase_document_notes(self, doc_id: int, notes: str):
        self.db.update_purchase_document_notes(doc_id, notes)

    def delete_purchase_document_item(self, item_id: int):
        self.db.delete_purchase_document_item(item_id)

    def delete_purchase_document(self, doc_id: int):
        self.db.delete_purchase_document(doc_id)

    def get_items_for_document(self, doc_id: int):
        return self.db.get_items_for_document(doc_id)

    def add_purchase_receipt(self, item_id: int, quantity: float, received_date: str | None = None):
        return self.db.add_purchase_receipt(item_id, quantity, received_date)

    def get_total_received_for_item(self, item_id: int) -> float:
        return self.db.get_total_received_for_item(item_id)

    def mark_item_fully_received(self, item_id: int):
        self.db.mark_purchase_item_received(item_id)

    def are_all_items_received(self, doc_id: int) -> bool:
        return self.db.are_all_items_received(doc_id)


class InteractionRepository:
    """Repository for interaction-related operations."""
    def __init__(self, db: DatabaseHandler):
        self.db = db

    def add_interaction(self, *args, **kwargs):
        return self.db.add_interaction(*args, **kwargs)

    def get_interaction(self, interaction_id):
        return self.db.get_interaction(interaction_id)

    def get_interactions(self, **filters):
        return self.db.get_interactions(**filters)

    def update_interaction(self, interaction_id, *args, **kwargs):
        self.db.update_interaction(interaction_id, *args, **kwargs)

    def delete_interaction(self, interaction_id):
        self.db.delete_interaction(interaction_id)


class SalesRepository:
    """Repository for sales document operations."""
    def __init__(self, db: DatabaseHandler):
        self.db = db

    def get_all_sales_documents(self, **filters):
        return self.db.get_all_sales_documents(**filters)

    def add_sales_document(self, **kwargs):
        return self.db.add_sales_document(**kwargs)

    def update_sales_document(self, doc_id: int, updates: dict):
        self.db.update_sales_document(doc_id, updates)

    def update_sales_document_item(self, item_id: int, updates: dict):
        self.db.update_sales_document_item(item_id, updates)

    def add_sales_document_item(self, **kwargs):
        return self.db.add_sales_document_item(**kwargs)

    def get_sales_document_by_id(self, doc_id: int):
        return self.db.get_sales_document_by_id(doc_id)

    def get_items_for_sales_document(self, doc_id: int):
        return self.db.get_items_for_sales_document(doc_id)

    def get_shipments_for_sales_document(self, doc_id: int):
        return self.db.get_shipments_for_sales_document(doc_id)

    def get_shipment_references_for_sales_document(self, doc_id: int) -> list[str]:
        return self.db.get_shipment_references_for_sales_document(doc_id)

    def get_sales_document_item_by_id(self, item_id: int):
        return self.db.get_sales_document_item_by_id(item_id)

    def delete_sales_document_item(self, item_id: int):
        self.db.delete_sales_document_item(item_id)

    def are_all_items_shipped(self, doc_id: int) -> bool:
        return self.db.are_all_items_shipped(doc_id)

    def delete_sales_document(self, doc_id: int):
        self.db.delete_sales_document(doc_id)


class InventoryRepository:
    """Repository for inventory management operations."""
    def __init__(self, db: DatabaseHandler):
        self.db = db

    def log_transaction(self, product_id: int, quantity_change: float,
                        transaction_type: str, reference: str = None):
        return self.db.log_inventory_transaction(
            product_id, quantity_change, transaction_type, reference
        )

    def get_transactions(self, product_id: int = None):
        return self.db.get_inventory_transactions(product_id)

    def get_stock_level(self, product_id: int) -> float:
        return self.db.get_stock_level(product_id)

    def get_on_order_level(self, product_id: int) -> float:
        return self.db.get_on_order_quantity(product_id)

    def get_all_on_order_levels(self):
        return self.db.get_all_on_order_quantities()

    def add_replenishment_item(self, product_id: int, quantity_needed: float):
        return self.db.add_replenishment_item(product_id, quantity_needed)

    def get_replenishment_queue(self):
        return self.db.get_replenishment_queue()

    def remove_replenishment_item(self, item_id: int):
        self.db.remove_replenishment_item(item_id)


class PurchaseOrderRepository:
    """Repository for purchase order operations."""
    def __init__(self, db: DatabaseHandler):
        self.db = db

    def add_purchase_order(self, **kwargs):
        return self.db.add_purchase_order(**kwargs)

    def get_purchase_order_by_id(self, order_id: int):
        return self.db.get_purchase_order_by_id(order_id)

    def get_all_purchase_orders(self, **filters):
        return self.db.get_all_purchase_orders(**filters)

    def update_purchase_order_status(self, order_id: int, new_status: str):
        self.db.update_purchase_order_status(order_id, new_status)

    def delete_purchase_order(self, order_id: int):
        self.db.delete_purchase_order(order_id)

    def add_line_item(self, **kwargs):
        return self.db.add_purchase_order_line_item(**kwargs)

    def get_line_items_for_order(self, order_id: int):
        return self.db.get_purchase_order_line_items(order_id)

    def delete_line_item(self, item_id: int):
        self.db.delete_purchase_order_line_item(item_id)
