import tkinter as tk
from tkinter import ttk
from core.database import DatabaseHandler
from core.logic import AddressBookLogic
from ui.contact_tab import ContactTab
from ui.account_tab import AccountTab


class AddressBookView:
    def __init__(self, root, logic): # Add logic parameter
        self.root = root
        self.root.title("Ace's CRM")

        # Use the passed-in logic instance
        self.logic = logic
        # db_handler is part of logic or not directly needed by main_view if logic handles all DB interactions

        # Track the currently selected contact's ID and account's ID
        self.selected_contact_id = None
        self.selected_account_id = None

        # Setup Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Initialize AccountTab and ContactTab
        self.account_tab = AccountTab(self.notebook, self.logic)
        self.contact_tab = ContactTab(self.notebook, self.logic)

        # Add frames from AccountTab and ContactTab to Notebook
        self.notebook.add(self.account_tab.frame, text="Account Administration")
        self.notebook.add(self.contact_tab.frame, text="Contact Information")
