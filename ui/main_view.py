import tkinter as tk
from tkinter import ttk
from core.database import DatabaseHandler
from core.address_book_logic import AddressBookLogic
from ui.contact_tab import ContactTab
from ui.account_tab import AccountTab
from ui.interaction_tab import InteractionLogTab
from ui.task_tab import TaskTab # Import the new TaskTab
from ui.product_tab import ProductTab # Import ProductTab


class AddressBookView:
    def __init__(self, root, logic): # Add logic parameter
        self.root = root
        self.root.title("Ace's CRM")
        self.root.geometry("900x700") # Adjusted for potentially more content

        # Use the passed-in logic instance
        self.logic = logic
        # db_handler is part of logic or not directly needed by main_view if logic handles all DB interactions

        # Track the currently selected contact's ID and account's ID
        self.selected_contact_id = None
        self.selected_account_id = None

        # Setup Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.root.columnconfigure(0, weight=1) # Allow notebook to expand
        self.root.rowconfigure(0, weight=1)    # Allow notebook to expand


        # Initialize AccountTab and ContactTab
        self.account_tab = AccountTab(self.notebook, self.logic)
        self.contact_tab = ContactTab(self.notebook, self.logic)
        self.interaction_log_tab = InteractionLogTab(self.notebook, self.logic)
        self.task_tab = TaskTab(self.notebook, self.logic) # Create instance of TaskTab
        self.product_tab = ProductTab(self.notebook, self.logic) # Create instance of ProductTab

        # Add frames from tabs to Notebook
        # AccountTab and ContactTab use .frame attribute.
        # InteractionLogTab and TaskTab are tk.Frame subclasses directly.
        self.notebook.add(self.account_tab.frame, text="Account Administration")
        self.notebook.add(self.contact_tab.frame, text="Contact Information")
        self.notebook.add(self.interaction_log_tab, text="Interaction Log")
        self.notebook.add(self.task_tab, text="Tasks") # Add the new TaskTab
        self.notebook.add(self.product_tab.frame, text="Products") # Add the new ProductTab
