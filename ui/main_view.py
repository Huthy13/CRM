import tkinter as tk
from tkinter import ttk
from core.database import DatabaseHandler
from core.address_book_logic import AddressBookLogic
from ui.contacts.contact_tab import ContactTab
from ui.accounts.account_tab import AccountTab
from ui.interactions.interaction_tab import InteractionLogTab
from ui.tasks.task_tab import TaskTab
from ui.products.product_tab import ProductTab
from core.logic.product_management import ProductLogic # Import ProductLogic
from core.purchase_logic import PurchaseLogic
from ui.purchase_documents.purchase_document_tab import PurchaseDocumentTab
from ui.company_info_tab import CompanyInfoTab # Import the new tab


class AddressBookView:
    def __init__(self, root, logic: AddressBookLogic): # logic is AddressBookLogic
        self.root = root
        self.root.title("Ace's CRM")
        self.root.geometry("950x750")

        self.address_book_logic = logic

        # Initialize other logic handlers
        self.db_handler = self.address_book_logic.db # Get the shared DB handler
        self.product_logic = ProductLogic(self.db_handler) # Initialize ProductLogic
        self.purchase_logic = PurchaseLogic(self.db_handler) # Initialize PurchaseLogic


        # Track the currently selected contact's ID and account's ID
        self.selected_contact_id = None
        self.selected_account_id = None

        # Setup Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.root.columnconfigure(0, weight=1) # Allow notebook to expand
        self.root.rowconfigure(0, weight=1)    # Allow notebook to expand


        # Initialize all tabs
        self.account_tab = AccountTab(self.notebook, self.address_book_logic)
        self.contact_tab = ContactTab(self.notebook, self.address_book_logic)
        self.interaction_log_tab = InteractionLogTab(self.notebook, self.address_book_logic)
        self.task_tab = TaskTab(self.notebook, self.address_book_logic)
        self.product_tab = ProductTab(self.notebook, self.address_book_logic, self.product_logic) # Pass product_logic here too
        self.purchase_document_tab = PurchaseDocumentTab(self.notebook, self.purchase_logic, self.address_book_logic, self.product_logic) # Pass product_logic
        self.company_info_tab = CompanyInfoTab(self.notebook, self.db_handler) # Add CompanyInfoTab


        # Add frames from tabs to Notebook
        self.notebook.add(self.account_tab.frame, text="Account Administration")
        self.notebook.add(self.contact_tab.frame, text="Contact Information")
        self.notebook.add(self.interaction_log_tab, text="Interaction Log")
        self.notebook.add(self.task_tab, text="Tasks")
        self.notebook.add(self.product_tab.frame, text="Products")
        self.notebook.add(self.purchase_document_tab.frame, text="Purchase Documents")
        self.notebook.add(self.company_info_tab.frame, text="Company Information") # Add the new tab to the notebook
