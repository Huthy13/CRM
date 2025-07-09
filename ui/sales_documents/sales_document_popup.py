import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from shared.structs import SalesDocument, SalesDocumentItem, Account, Product # Assuming structs
# Placeholder for a potential product selection popup/widget
# from ui.products.product_selector_popup import ProductSelectorPopup

class SalesDocumentPopup(tk.Toplevel):
    def __init__(self, master, calling_tab, sales_logic, customer_logic, product_logic, document_id=None):
        super().__init__(master)
        self.calling_tab = calling_tab
        self.sales_logic = sales_logic
        self.customer_logic = customer_logic # For customer dropdown
        self.product_logic = product_logic # For product selection and prices
        self.document_id = document_id

        self.title(f"{'Edit' if document_id else 'New'} Sales Document")
        self.geometry("900x700") # Adjusted size for more content

        self.document_data = None # To store loaded document if editing
        self.line_items_data = [] # Stores current line items for the UI (list of SalesDocumentItem or dicts)
        self.selected_line_item_iid = None

        self._setup_ui()

        if self.document_id:
            self._load_document_details()
        else:
            # Default new document values
            self.doc_date_entry.insert(0, datetime.date.today().isoformat())
            self.status_combobox.current(0) # Default to first status e.g. "Draft"
            self._update_totals_display() # Show 0.00

    def _setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Header Frame
        header_frame = ttk.LabelFrame(main_frame, text="Document Header", padding="10")
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.columnconfigure(1, weight=1) # Allow entry fields to expand

        ttk.Label(header_frame, text="Customer:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.customer_combobox = ttk.Combobox(header_frame, state="readonly", width=40)
        self.customer_combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self._populate_customer_combobox()

        ttk.Label(header_frame, text="Doc Date:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.doc_date_entry = ttk.Entry(header_frame, width=40) # Consider using a Datepicker widget if available
        self.doc_date_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(header_frame, text="Status:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.status_combobox = ttk.Combobox(header_frame, state="readonly", values=["Draft", "Sent", "Accepted", "Closed", "Cancelled"], width=38)
        self.status_combobox.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        # Line Items Frame
        items_frame = ttk.LabelFrame(main_frame, text="Line Items", padding="10")
        items_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.rowconfigure(1, weight=1) # Allow items_frame to expand vertically
        items_frame.columnconfigure(0, weight=1) # Allow treeview to expand horizontally

        # Line Items Treeview
        item_columns = ("item_id", "product_name", "quantity", "unit_price", "line_total")
        self.items_tree = ttk.Treeview(items_frame, columns=item_columns, show="headings", selectmode="browse")

        self.items_tree.heading("item_id", text="ID") # Hidden or very small
        self.items_tree.heading("product_name", text="Product")
        self.items_tree.heading("quantity", text="Qty")
        self.items_tree.heading("unit_price", text="Unit Price")
        self.items_tree.heading("line_total", text="Total")

        self.items_tree.column("item_id", width=0, stretch=False) # Hidden
        self.items_tree.column("product_name", width=300)
        self.items_tree.column("quantity", width=80, anchor=tk.E)
        self.items_tree.column("unit_price", width=100, anchor=tk.E)
        self.items_tree.column("line_total", width=120, anchor=tk.E)

        self.items_tree.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        items_frame.rowconfigure(0, weight=1)
        items_frame.columnconfigure(0, weight=1)
        self.items_tree.bind("<<TreeviewSelect>>", self._on_line_item_select)

        # Line Item Buttons
        item_button_frame = ttk.Frame(items_frame)
        item_button_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        self.add_item_button = ttk.Button(item_button_frame, text="Add Item", command=self._add_item_dialog)
        self.add_item_button.pack(side=tk.LEFT, padx=5)
        self.edit_item_button = ttk.Button(item_button_frame, text="Edit Item", command=self._edit_item_dialog)
        self.edit_item_button.pack(side=tk.LEFT, padx=5)
        self.remove_item_button = ttk.Button(item_button_frame, text="Remove Item", command=self._remove_item)
        self.remove_item_button.pack(side=tk.LEFT, padx=5)

        # Totals Frame
        totals_frame = ttk.Frame(main_frame, padding="5")
        totals_frame.grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Label(totals_frame, text="Document Total:").pack(side=tk.LEFT, padx=5)
        self.total_amount_label = ttk.Label(totals_frame, text="$0.00", font=("Arial", 12, "bold"))
        self.total_amount_label.pack(side=tk.LEFT, padx=5)

        # Action Buttons (Save, Cancel)
        action_button_frame = ttk.Frame(main_frame, padding="10")
        action_button_frame.grid(row=3, column=0, sticky="e", padx=5, pady=10)

        self.save_button = ttk.Button(action_button_frame, text="Save Document", command=self._save_document)
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ttk.Button(action_button_frame, text="Cancel", command=self.destroy)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Store customer data for mapping display name to ID
        self.customers_map = {} # name: id

    def _populate_customer_combobox(self):
        try:
            accounts = self.customer_logic.get_all_accounts() # This should return Account structs or dicts
            self.customers_map = {acc.name: acc.account_id for acc in accounts} # Adjust if not structs
            self.customer_combobox['values'] = sorted(list(self.customers_map.keys()))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load customers: {e}", parent=self)

    def _on_line_item_select(self, event=None):
        selected = self.items_tree.selection()
        if selected:
            self.selected_line_item_iid = selected[0] # This is the iid, can map to index or actual item_id
        else:
            self.selected_line_item_iid = None

    def _load_document_details(self):
        self.document_data = self.sales_logic.get_sales_document_details(self.document_id)
        if not self.document_data:
            messagebox.showerror("Error", f"Could not load document ID: {self.document_id}", parent=self)
            self.destroy()
            return

        # Populate header
        customer_id = self.document_data.customer_id
        customer_name_to_select = ""
        for name, c_id in self.customers_map.items():
            if c_id == customer_id:
                customer_name_to_select = name
                break
        if customer_name_to_select:
            self.customer_combobox.set(customer_name_to_select)
        else:
            # Customer might be inactive or not in current list, handle gracefully
            # Potentially add it to combobox if it's a valid existing customer not in the list
            # For now, leave blank or show ID.
            self.customer_combobox.set(f"ID: {customer_id}" if customer_id else "Unknown Customer")


        self.doc_date_entry.delete(0, tk.END)
        self.doc_date_entry.insert(0, self.document_data.document_date.isoformat() if self.document_data.document_date else "")

        if self.document_data.status in self.status_combobox['values']:
            self.status_combobox.set(self.document_data.status)
        else:
            # Status from DB not in predefined list, handle (e.g. add it, or default)
            self.status_combobox.set(self.document_data.status) # Or set to a default

        # Populate line items
        self.line_items_data = list(self.document_data.items) # Make a mutable copy of SalesDocumentItem structs
        self._refresh_line_items_tree()
        self._update_totals_display()

    def _refresh_line_items_tree(self):
        self.items_tree.delete(*self.items_tree.get_children())
        self.selected_line_item_iid = None
        for idx, item_struct in enumerate(self.line_items_data):
            # Need product name for display. item_struct is SalesDocumentItem.
            # SalesLogic.get_sales_document_details -> items are SalesDocumentItem.
            # These don't have product_name. This needs to be fetched.
            product_details = self.product_logic.get_product_details(item_struct.product_id) # ProductLogic needed
            product_name = product_details.name if product_details else "Unknown Product"

            # Using index as IID for simplicity in this local list context
            # When saving, new items won't have item_id yet.
            # Existing items from DB will have item_struct.item_id.
            iid = str(idx) # Use list index as IID for the tree

            self.items_tree.insert("", "end", iid=iid, values=(
                item_struct.item_id if item_struct.item_id else "New", # Display actual ID or "New"
                product_name,
                item_struct.quantity,
                f"${item_struct.unit_price:,.2f}",
                f"${item_struct.line_total:,.2f}"
            ))

    def _update_totals_display(self):
        current_total = sum(item.line_total for item in self.line_items_data)
        self.total_amount_label.config(text=f"${current_total:,.2f}")

    def _add_item_dialog(self):
        # This would open another small dialog to select a product and quantity
        # For now, let's simulate adding a dummy item
        # In a real app: ProductSelectorPopup(self, self.product_logic, callback=self._add_item_to_list)

        # --- Placeholder for Product Selection & Quantity Input ---
        # For this example, let's assume we get product_id and quantity from a mock dialog
        # And we fetch product details (especially price)

        # Mocking product selection
        # This requires a ProductSelectorPopup or similar UI
        # For now, let's manually create a new item for testing purposes.
        # This part needs to be replaced with a proper product selection dialog.

        # Example: Open a dialog that returns a product_id and quantity
        # For now, we'll create a placeholder item.
        # This is NOT a complete implementation for adding an item.

        # Let's say a dialog returns: product_id = 1, quantity = 1
        # This is where you'd call a product selector.
from ui.sales_documents.sales_document_item_popup import SalesDocumentItemPopup # Import the item popup

class SalesDocumentPopup(tk.Toplevel):
    def __init__(self, master, calling_tab, sales_logic, customer_logic, product_logic, document_id=None):
        super().__init__(master)
        self.calling_tab = calling_tab
        self.sales_logic = sales_logic
        self.customer_logic = customer_logic # For customer dropdown
        self.product_logic = product_logic # For product selection and prices
        self.document_id = document_id

        self.title(f"{'Edit' if document_id else 'New'} Sales Document")
        self.geometry("900x700") # Adjusted size for more content

        self.document_data = None # To store loaded document if editing
        self.line_items_data = [] # Stores current line items for the UI (list of SalesDocumentItem structs)
        self.selected_line_item_iid = None

        self.available_products_for_item_popup = None # Cache products for item popup

        self._setup_ui()

        if self.document_id:
            self._load_document_details()
        else:
            # Default new document values
            self.doc_date_entry.insert(0, datetime.date.today().isoformat())
            if self.status_combobox['values']: # Check if list is not empty
                self.status_combobox.current(0) # Default to first status e.g. "Draft"
            self._update_totals_display() # Show 0.00

    def _setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Header Frame
        header_frame = ttk.LabelFrame(main_frame, text="Document Header", padding="10")
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.columnconfigure(1, weight=1) # Allow entry fields to expand

        ttk.Label(header_frame, text="Customer:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.customer_combobox = ttk.Combobox(header_frame, state="readonly", width=40)
        self.customer_combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self._populate_customer_combobox()

        ttk.Label(header_frame, text="Doc Date:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.doc_date_entry = ttk.Entry(header_frame, width=40) # Consider using a Datepicker widget if available
        self.doc_date_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(header_frame, text="Status:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.status_combobox = ttk.Combobox(header_frame, state="readonly", values=["Draft", "Sent", "Accepted", "Closed", "Cancelled"], width=38)
        self.status_combobox.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        # Line Items Frame
        items_frame = ttk.LabelFrame(main_frame, text="Line Items", padding="10")
        items_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.rowconfigure(1, weight=1) # Allow items_frame to expand vertically
        items_frame.columnconfigure(0, weight=1) # Allow treeview to expand horizontally

        # Line Items Treeview
        item_columns = ("item_id_display", "product_name", "quantity", "unit_price", "line_total") # Renamed first col
        self.items_tree = ttk.Treeview(items_frame, columns=item_columns, show="headings", selectmode="browse")

        self.items_tree.heading("item_id_display", text="Item ID")
        self.items_tree.heading("product_name", text="Product")
        self.items_tree.heading("quantity", text="Qty")
        self.items_tree.heading("unit_price", text="Unit Price")
        self.items_tree.heading("line_total", text="Total")

        self.items_tree.column("item_id_display", width=60, anchor=tk.W)
        self.items_tree.column("product_name", width=300)
        self.items_tree.column("quantity", width=80, anchor=tk.E)
        self.items_tree.column("unit_price", width=100, anchor=tk.E)
        self.items_tree.column("line_total", width=120, anchor=tk.E)

        self.items_tree.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        items_frame.rowconfigure(0, weight=1)
        items_frame.columnconfigure(0, weight=1)
        self.items_tree.bind("<<TreeviewSelect>>", self._on_line_item_select)
        self.items_tree.bind("<Double-1>", lambda e: self._edit_item_dialog()) # Double click to edit


        # Line Item Buttons
        item_button_frame = ttk.Frame(items_frame)
        item_button_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        self.add_item_button = ttk.Button(item_button_frame, text="Add Item", command=self._add_item_dialog)
        self.add_item_button.pack(side=tk.LEFT, padx=5)
        self.edit_item_button = ttk.Button(item_button_frame, text="Edit Item", command=self._edit_item_dialog)
        self.edit_item_button.pack(side=tk.LEFT, padx=5)
        self.remove_item_button = ttk.Button(item_button_frame, text="Remove Item", command=self._remove_item)
        self.remove_item_button.pack(side=tk.LEFT, padx=5)

        # Totals Frame
        totals_frame = ttk.Frame(main_frame, padding="5")
        totals_frame.grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Label(totals_frame, text="Document Total:").pack(side=tk.LEFT, padx=5)
        self.total_amount_label = ttk.Label(totals_frame, text="$0.00", font=("Arial", 12, "bold"))
        self.total_amount_label.pack(side=tk.LEFT, padx=5)

        # Action Buttons (Save, Cancel)
        action_button_frame = ttk.Frame(main_frame, padding="10")
        action_button_frame.grid(row=3, column=0, sticky="e", padx=5, pady=10)

        self.save_button = ttk.Button(action_button_frame, text="Save Document", command=self._save_document)
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ttk.Button(action_button_frame, text="Cancel", command=self.destroy)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Store customer data for mapping display name to ID
        self.customers_map = {} # name: id

        # Pre-fetch products for item popup
        self._load_available_products_for_item_popup()


    def _load_available_products_for_item_popup(self):
        try:
            self.available_products_for_item_popup = self.product_logic.get_all_products()
        except Exception as e:
            print(f"Error loading products for item popup: {e}")
            self.available_products_for_item_popup = []


    def _populate_customer_combobox(self):
        try:
            accounts = self.customer_logic.get_all_accounts()
            if accounts:
                self.customers_map = {acc.name: acc.account_id for acc in accounts}
                self.customer_combobox['values'] = sorted(list(self.customers_map.keys()))
            else:
                self.customer_combobox['values'] = []
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load customers: {e}", parent=self)
            self.customer_combobox['values'] = []


    def _on_line_item_select(self, event=None):
        selected = self.items_tree.selection()
        if selected:
            self.selected_line_item_iid = selected[0]
        else:
            self.selected_line_item_iid = None

    def _load_document_details(self):
        self.document_data = self.sales_logic.get_sales_document_details(self.document_id)
        if not self.document_data:
            messagebox.showerror("Error", f"Could not load document ID: {self.document_id}", parent=self)
            self.destroy()
            return

        customer_id = self.document_data.customer_id
        customer_name_to_select = ""
        for name, c_id in self.customers_map.items():
            if c_id == customer_id:
                customer_name_to_select = name
                break
        if customer_name_to_select:
            self.customer_combobox.set(customer_name_to_select)
        else:
            # Try to get account details if not in initial map (e.g. if map was filtered or stale)
            acc_details = self.customer_logic.get_account_details(customer_id)
            if acc_details:
                 self.customer_combobox.set(acc_details.name)
            else:
                self.customer_combobox.set(f"ID: {customer_id}" if customer_id else "Unknown Customer")


        self.doc_date_entry.delete(0, tk.END)
        self.doc_date_entry.insert(0, self.document_data.document_date.isoformat() if self.document_data.document_date else "")

        if self.document_data.status in self.status_combobox['values']:
            self.status_combobox.set(self.document_data.status)
        else:
            current_statuses = list(self.status_combobox['values'])
            current_statuses.append(self.document_data.status)
            self.status_combobox['values'] = current_statuses
            self.status_combobox.set(self.document_data.status)


        # Populate line items - document_data.items should be list of SalesDocumentItem from logic
        self.line_items_data = []
        if hasattr(self.document_data, 'items'):
            for item_struct in self.document_data.items:
                 # Create a new SalesDocumentItem instance for local list to avoid modifying original from logic
                copied_item = SalesDocumentItem(
                    item_id=item_struct.item_id,
                    document_id=item_struct.document_id,
                    product_id=item_struct.product_id,
                    quantity=item_struct.quantity,
                    unit_price=item_struct.unit_price,
                    line_total=item_struct.line_total
                )
                # We need product_name for display, store it on the copied_item if not already part of struct
                # SalesDocumentItem struct does not have product_name.
                # The DB method get_sales_document_item *does* fetch product_name.
                # SalesLogic.get_sales_document_details -> items should ideally have product_name.
                # For now, fetch it if SalesDocumentItem doesn't have it.
                if not hasattr(copied_item, 'product_name'):
                    prod_details = self.product_logic.get_product_details(copied_item.product_id)
                    copied_item.product_name = prod_details.name if prod_details else "Unknown Product"
                self.line_items_data.append(copied_item)

        self._refresh_line_items_tree()
        self._update_totals_display()

    def _refresh_line_items_tree(self):
        self.items_tree.delete(*self.items_tree.get_children())
        self.selected_line_item_iid = None
        for idx, item_struct in enumerate(self.line_items_data):
            # item_struct is now a SalesDocumentItem from our local list.
            # It should have product_name if _load_document_details or _add/_edit handled it.
            product_name = getattr(item_struct, 'product_name', "Loading...") # Default if not set
            if product_name == "Loading...": # Fetch if needed
                prod_details = self.product_logic.get_product_details(item_struct.product_id)
                product_name = prod_details.name if prod_details else "Unknown Product"
                item_struct.product_name = product_name # Cache it on our local struct copy

            iid = str(idx)

            self.items_tree.insert("", "end", iid=iid, values=(
                item_struct.item_id if item_struct.item_id else "New",
                product_name,
                item_struct.quantity,
                f"${item_struct.unit_price:,.2f}",
                f"${item_struct.line_total:,.2f}"
            ))

    def _update_totals_display(self):
        current_total = sum(item.line_total for item in self.line_items_data if hasattr(item, 'line_total'))
        self.total_amount_label.config(text=f"${current_total:,.2f}")

    def _add_item_dialog(self):
        item_popup = SalesDocumentItemPopup(
            self,
            self.product_logic,
            available_products=self.available_products_for_item_popup
        )
        result = item_popup.show() # Blocks until item_popup closes

        if result:
            # result = {product_id, product_name, quantity, unit_price, line_total, item_id (None for new)}
            new_item = SalesDocumentItem(
                item_id=None, # Always None for a newly added item to this UI list
                document_id=self.document_id, # Can be None if main doc is new
                product_id=result['product_id'],
                quantity=result['quantity'],
                unit_price=result['unit_price'],
                line_total=result['line_total']
            )
            new_item.product_name = result['product_name'] # Store for display

            self.line_items_data.append(new_item)
            self._refresh_line_items_tree()
            self._update_totals_display()


    def _edit_item_dialog(self):
        if not self.selected_line_item_iid:
            messagebox.showwarning("No Selection", "Please select an item to edit.", parent=self)
            return

        try:
            item_index = int(self.selected_line_item_iid) # IID is the index
            item_to_edit_struct = self.line_items_data[item_index] # This is SalesDocumentItem
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Invalid item selection.", parent=self)
            return

        # Prepare data for SalesDocumentItemPopup
        existing_item_data_for_popup = {
            'product_id': item_to_edit_struct.product_id,
            'quantity': item_to_edit_struct.quantity,
            'item_id': item_to_edit_struct.item_id # Pass existing item_id
        }

        item_popup = SalesDocumentItemPopup(
            self,
            self.product_logic,
            existing_item_data=existing_item_data_for_popup,
            available_products=self.available_products_for_item_popup
        )
        result = item_popup.show()

        if result:
            # Update the item in self.line_items_data list
            item_to_edit_struct.product_id = result['product_id']
            item_to_edit_struct.quantity = result['quantity']
            item_to_edit_struct.unit_price = result['unit_price']
            item_to_edit_struct.line_total = result['line_total']
            item_to_edit_struct.product_name = result['product_name'] # Update for display
            # item_to_edit_struct.item_id remains the same if it existed

            self._refresh_line_items_tree()
            self._update_totals_display()


    def _remove_item(self):
        if not self.selected_line_item_iid:
            messagebox.showwarning("No Selection", "Please select an item to remove.", parent=self)
            return

        item_index = int(self.selected_line_item_iid) # IID is the index
        if 0 <= item_index < len(self.line_items_data):
            del self.line_items_data[item_index]
            self._refresh_line_items_tree()
            self._update_totals_display()
        self.selected_line_item_iid = None # Clear selection

    def _save_document(self):
        selected_customer_name = self.customer_combobox.get()
        if not selected_customer_name or selected_customer_name not in self.customers_map:
            messagebox.showerror("Validation Error", "Please select a valid customer.", parent=self)
            return
        customer_id = self.customers_map[selected_customer_name]

        doc_date_str = self.doc_date_entry.get().strip()
        try:
            doc_date = datetime.date.fromisoformat(doc_date_str)
        except ValueError:
            messagebox.showerror("Validation Error", "Invalid document date format. Use YYYY-MM-DD.", parent=self)
            return

        status = self.status_combobox.get()
        if not status:
            messagebox.showerror("Validation Error", "Please select a status.", parent=self)
            return

        if not self.line_items_data:
            messagebox.showwarning("Validation Error", "Cannot save a document with no line items.", parent=self)
            return

        # Prepare items_data for sales_logic
        # SalesLogic expects items_data: list of dicts {'product_id': X, 'quantity': Y} for create/update_items
        items_for_logic = []
        for ui_item in self.line_items_data: # ui_item is SalesDocumentItem struct
            items_for_logic.append({
                'product_id': ui_item.product_id,
                'quantity': ui_item.quantity,
                # item_id and unit_price might be needed if sales_logic.update_sales_document_items is more granular
                # For now, assuming it recalculates price based on product_id and quantity.
                # If SalesDocumentItem struct from UI has item_id (for existing items), pass it.
                'item_id': ui_item.item_id # Pass item_id if available
            })

        try:
            if self.document_id: # Editing existing document
                # SalesLogic needs a method like:
                # update_sales_document_header_and_items(doc_id, customer_id, date, status, items_data)
                # For now, we use update_sales_document_items which also updates total.
                # And a separate call to update header fields if they changed.

                # First, update items and document total through sales_logic
                success_items = self.sales_logic.update_sales_document_items(self.document_id, items_for_logic)
                if not success_items:
                    messagebox.showerror("Save Error", "Failed to update document items.", parent=self)
                    return

                # Then, fetch the potentially updated total and update other header fields
                # Note: update_sales_document_items in sales_logic already updates total.
                # We just need to ensure other header fields like status, customer, date are updated.
                updated_doc_data = self.sales_logic.get_sales_document_details(self.document_id) # Re-fetch to get new total
                final_total_amount = updated_doc_data.total_amount if updated_doc_data else sum(item.line_total for item in self.line_items_data)

                self.sales_logic.db.update_sales_document( # Directly using DB for simplicity here. SalesLogic should wrap.
                    document_id=self.document_id,
                    customer_id=customer_id,
                    document_date=doc_date.isoformat(),
                    status=status,
                    total_amount=final_total_amount # This total is from update_sales_document_items
                )
                messagebox.showinfo("Success", "Sales document updated successfully!", parent=self)

            else: # Creating new document
                new_doc_id = self.sales_logic.create_sales_document(
                    customer_id=customer_id,
                    document_date=doc_date,
                    status=status,
                    items_data=items_for_logic # This list of dicts
                )
                if new_doc_id:
                    messagebox.showinfo("Success", f"Sales document created with ID: {new_doc_id}", parent=self)
                    self.document_id = new_doc_id # So it's now in "edit" mode if saved again
                else:
                    messagebox.showerror("Save Error", "Failed to create sales document.", parent=self)
                    return # Stay on popup if creation failed

            self.calling_tab.refresh_documents_list()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Save Error", f"An error occurred: {e}", parent=self)


if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw() # Hide main root window for popup test

    # Mock Logics
    class MockSalesLogic:
        def get_sales_document_details(self, doc_id):
            if doc_id == 1:
                doc = SalesDocument(document_id=1, customer_id=101, document_date=datetime.date(2023,1,10), status="Draft", total_amount=150.0)
                item1 = SalesDocumentItem(item_id=1, document_id=1, product_id=1001, quantity=2, unit_price=25.0, line_total=50.0)
                item2 = SalesDocumentItem(item_id=2, document_id=1, product_id=1002, quantity=1, unit_price=100.0, line_total=100.0)
                doc.items = [item1, item2]
                return doc
            return None

        def create_sales_document(self, customer_id, document_date, status, items_data):
            print(f"MOCK: Create Sales Doc: CustID {customer_id}, Date {document_date}, Status {status}, Items: {len(items_data)}")
            return 999 # New Doc ID

        def update_sales_document_items(self, document_id, items_data):
            print(f"MOCK: Update Sales Doc Items: DocID {document_id}, Items: {len(items_data)}")
            # Simulate recalculating total
            # In real logic, this would update DB and SalesLogic would fetch new total.
            # Here, we'd need to simulate the DB's total calculation.
            # For now, just return True
            return True

        # Mocking db directly for the save method's current implementation
        class MockDb:
            def update_sales_document(self, document_id, customer_id, document_date, status, total_amount):
                 print(f"MOCK DB: Update Sales Doc Header: DocID {document_id}, CustID {customer_id}, Date {document_date}, Status {status}, Total {total_amount}")
        db = MockDb()


    class MockCustomerLogic: # Simulates AccountLogic
        def get_all_accounts(self):
            # Returns list of Account-like objects
            class MockAcc:
                def __init__(self, id, name): self.account_id = id; self.name = name
            return [MockAcc(101, "Customer A"), MockAcc(102, "Customer B")]

    class MockProductLogic:
        def get_product_details(self, product_id):
            if product_id == 1001:
                return Product(product_id=1001, name="Product X", cost=25.0)
            if product_id == 1002:
                return Product(product_id=1002, name="Product Y", cost=100.0)
            return Product(product_id=product_id, name=f"Product {product_id}", cost=10.0) # Default mock

    class MockCallingTab:
        def refresh_documents_list(self):
            print("MOCK: Calling tab refresh_documents_list called.")

    mock_sales_logic = MockSalesLogic()
    mock_customer_logic = MockCustomerLogic()
    mock_product_logic = MockProductLogic()
    mock_calling_tab = MockCallingTab()

    # Test New Document
    # popup_new = SalesDocumentPopup(root, mock_calling_tab, mock_sales_logic, mock_customer_logic, mock_product_logic, document_id=None)
    # root.wait_window(popup_new)

    # Test Edit Document
    popup_edit = SalesDocumentPopup(root, mock_calling_tab, mock_sales_logic, mock_customer_logic, mock_product_logic, document_id=1)
    root.mainloop() # Need mainloop for Toplevel to show correctly
