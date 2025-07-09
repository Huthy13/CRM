import tkinter as tk
from tkinter import ttk
from core.database import DatabaseHandler
from core.address_book_logic import AddressBookLogic
from ui.contacts.contact_tab import ContactTab
from ui.accounts.account_tab import AccountTab
from ui.interactions.interaction_tab import InteractionLogTab
from ui.tasks.task_tab import TaskTab
from ui.products.product_tab import ProductTab
from ui.sales_documents.sales_document_tab import SalesDocumentTab # Import SalesDocumentTab

# Import necessary logic modules
from core.logic.sales_logic import SalesLogic
# Removed: from core.logic.product_management import ProductLogic


class AddressBookView:
    def __init__(self, root, db_handler: DatabaseHandler): # Changed logic to db_handler for clarity
        self.root = root
        self.root.title("Ace's CRM")
        self.root.geometry("1000x750") # Adjusted for potentially more content, including new tab

        # Instantiate all necessary logic classes
        self.address_book_logic = AddressBookLogic(db_handler) # Existing logic, also serves as product_logic for now
        # Removed: self.product_logic = ProductLogic(db_handler)
        self.sales_logic = SalesLogic(db_handler) # New Sales Logic
        # TaskLogic and InteractionLogic are likely part of AddressBookLogic or instantiated within their tabs
        # For ProductTab, it takes 'logic' which is AddressBookLogic in current ProductTab.
        # This might need adjustment if ProductTab strictly needs ProductLogic.
        # For SalesDocumentTab, it needs sales_logic, customer_logic (AddressBookLogic), and product_logic.

        # Track the currently selected contact's ID and account's ID (if needed at this level)
        self.selected_contact_id = None
        self.selected_account_id = None

        # Setup Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.root.columnconfigure(0, weight=1) # Allow notebook to expand
        self.root.rowconfigure(0, weight=1)    # Allow notebook to expand


        # Initialize Tabs, passing appropriate logic instances
        self.account_tab = AccountTab(self.notebook, self.address_book_logic)
        self.contact_tab = ContactTab(self.notebook, self.address_book_logic)
        # Assuming InteractionLogTab and TaskTab also use AddressBookLogic or a part of it
        self.interaction_log_tab = InteractionLogTab(self.notebook, self.address_book_logic)
        self.task_tab = TaskTab(self.notebook, self.address_book_logic)

        # ProductTab might need specific ProductLogic.
        # The current ProductTab takes a generic 'logic'. If it's fine with AddressBookLogic, no change.
        # If it needs ProductLogic, it should be self.product_logic.
        # Let's assume ProductTab is designed to work with AddressBookLogic for now, as per existing pattern.
        # If ProductTab's 'logic' needs methods from ProductLogic not in AddressBookLogic, this is an issue.
        # For now, I'll pass AddressBookLogic to ProductTab to maintain current structure.
        # A better approach might be for ProductTab to take ProductLogic directly.
        # The ProductTab uses self.logic.save_product, get_all_products etc. These are in AddressBookLogic.
        self.product_tab = ProductTab(self.notebook, self.address_book_logic)

        # Initialize SalesDocumentTab
        self.sales_document_tab = SalesDocumentTab(
            self.notebook,
            sales_logic=self.sales_logic,
            customer_logic=self.address_book_logic, # AddressBookLogic for customer operations
            product_logic=self.address_book_logic # Using AddressBookLogic for product ops as well
        )

        # Add frames from tabs to Notebook
        self.notebook.add(self.account_tab.frame, text="Accounts")
        self.notebook.add(self.contact_tab.frame, text="Contacts")
        self.notebook.add(self.interaction_log_tab, text="Interactions")
        self.notebook.add(self.task_tab, text="Tasks")
        self.notebook.add(self.product_tab.frame, text="Products")
        self.notebook.add(self.sales_document_tab.frame, text="Sales Documents") # Add new tab
