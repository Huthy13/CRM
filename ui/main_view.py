import tkinter as tk
from tkinter import ttk
from core.address_book_logic import AddressBookLogic
from ui.contacts.contact_tab import ContactTab
from ui.accounts.account_tab import AccountTab
from ui.interactions.interaction_tab import InteractionLogTab
from ui.tasks.task_tab import TaskTab
from ui.products.product_tab import ProductTab
from core.logic.product_management import ProductLogic # Import ProductLogic
from core.purchase_logic import PurchaseLogic
from ui.purchase_documents.purchase_document_tab import PurchaseDocumentTab
from core.sales_logic import SalesLogic # Import SalesLogic
from ui.sales_documents.sales_document_tab import SalesDocumentTab # Import SalesDocumentTab
# Company information popup
from ui.company_info_tab import CompanyInfoTab
from core.company_repository import CompanyRepository
from core.company_service import CompanyService
from core.address_service import AddressService
from core.repositories import AddressRepository, AccountRepository, InventoryRepository, ProductRepository
from core.inventory_service import InventoryService
from ui.pricing.pricing_rule_tab import PricingRuleTab
from ui.payment_terms.payment_term_tab import PaymentTermTab
from ui.category_popup import CategoryListPopup


class AddressBookView:
    def __init__(self, root, logic: AddressBookLogic): # logic is AddressBookLogic
        self.root = root
        self.root.title("Ace's CRM")
        self.root.geometry("1000x800")  # Adjusted size for new tab

        self.address_book_logic = logic

        # Initialize other logic handlers
        self.db_handler = self.address_book_logic.db # Get the shared DB handler
        product_repo = ProductRepository(self.db_handler)
        inventory_repo = InventoryRepository(self.db_handler)
        self.inventory_service = InventoryService(inventory_repo, product_repo)
        self.product_logic = ProductLogic(self.db_handler)  # Initialize ProductLogic
        self.purchase_logic = PurchaseLogic(
            self.db_handler, inventory_service=self.inventory_service
        )  # Initialize PurchaseLogic
        self.sales_logic = SalesLogic(
            self.db_handler, inventory_service=self.inventory_service
        )  # Initialize SalesLogic

        # Initialize services for company info
        address_repo = AddressRepository(self.db_handler)
        account_repo = AccountRepository(self.db_handler)
        self.address_service = AddressService(address_repo, account_repo)
        company_repo = CompanyRepository(self.db_handler)
        self.company_service = CompanyService(company_repo, self.address_service)

        # Track the currently selected contact's ID and account's ID
        self.selected_contact_id = None
        self.selected_account_id = None

        # Setup Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.root.columnconfigure(0, weight=1)  # Allow notebook to expand
        self.root.rowconfigure(0, weight=1)  # Allow notebook to expand

        # Top-level menu
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menu_bar.add_cascade(label="File", menu=file_menu)

        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Company info", command=self.open_company_info)
        settings_menu.add_command(label="Payment Terms", command=self.open_payment_terms)
        settings_menu.add_command(label="Pricing Rules", command=self.open_pricing_rules)
        settings_menu.add_command(label="Product Categories", command=self.open_product_categories)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)

        # Initialize all tabs
        self.account_tab = AccountTab(self.notebook, self.address_book_logic)
        self.contact_tab = ContactTab(self.notebook, self.address_book_logic)
        self.interaction_log_tab = InteractionLogTab(self.notebook, self.address_book_logic)
        self.task_tab = TaskTab(self.notebook, self.address_book_logic)
        self.product_tab = ProductTab(self.notebook, self.address_book_logic, self.product_logic, self.inventory_service, self.purchase_logic) # Pass product_logic here too
        self.purchase_document_tab = PurchaseDocumentTab(self.notebook, self.purchase_logic, self.address_book_logic, self.product_logic) # Pass product_logic
        self.sales_document_tab = SalesDocumentTab(
            self.notebook, self.sales_logic, self.address_book_logic, self.product_logic
        )  # Add Sales Documents tab


        # Add frames from tabs to Notebook
        self.notebook.add(self.account_tab, text="Accounts")
        self.notebook.add(self.contact_tab, text="Contacts")
        self.notebook.add(self.interaction_log_tab, text="Interaction Log")
        self.notebook.add(self.task_tab, text="Tasks")
        self.notebook.add(self.product_tab.frame, text="Products")
        self.notebook.add(self.purchase_document_tab.frame, text="Purchase")
        self.notebook.add(self.sales_document_tab.frame, text="Sales")

    def open_company_info(self):
        """Open the company information popup."""
        popup = tk.Toplevel(self.root)
        popup.title("Company Information")
        company_tab = CompanyInfoTab(popup, self.company_service)
        company_tab.frame.pack(fill="both", expand=True)

    def open_pricing_rules(self):
        """Open the pricing rules popup."""
        popup = tk.Toplevel(self.root)
        popup.title("Pricing Rules")
        pricing_tab = PricingRuleTab(popup, self.address_book_logic)
        pricing_tab.frame.pack(fill="both", expand=True)

    def open_payment_terms(self):
        """Open the payment terms popup."""
        popup = tk.Toplevel(self.root)
        popup.title("Payment Terms")
        term_tab = PaymentTermTab(popup, self.address_book_logic)
        term_tab.frame.pack(fill="both", expand=True)

    def open_product_categories(self):
        """Open the product categories popup."""
        popup = CategoryListPopup(self.root, self.product_logic)
        self.root.wait_window(popup)
