import tkinter as tk
from tkinter import ttk, messagebox
from shared.structs import Product # Assuming Product struct for product details

class SalesDocumentItemPopup(tk.Toplevel):
    def __init__(self, master, product_logic, existing_item_data=None, available_products=None):
        """
        Popup for adding or editing a sales document line item.
        master: Parent window.
        product_logic: Instance of ProductLogic (or similar) to fetch product details/list.
        existing_item_data: Dict with {'product_id': X, 'quantity': Y} if editing.
        available_products: A list of Product structs or dicts for the product combobox.
                            If None, it will try to fetch all products.
        """
        super().__init__(master)
        self.product_logic = product_logic
        self.existing_item_data = existing_item_data
        self.result = None # To store the {product_id, quantity, unit_price, line_total, product_name}

        self.title("Add/Edit Line Item")
        self.geometry("450x200") # Adjusted size
        self.resizable(False, False)

        self.products_map = {} # name: id for combobox
        self.selected_product_details = None # Stores full Product struct of selected product

        self._setup_ui(available_products)

        if self.existing_item_data and 'product_id' in self.existing_item_data:
            self._load_existing_item()

        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)


    def _setup_ui(self, available_products):
        frame = ttk.Frame(self, padding="10")
        frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(frame, text="Product:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.product_combobox = ttk.Combobox(frame, state="readonly", width=40)
        self.product_combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.product_combobox.bind("<<ComboboxSelected>>", self._on_product_select)
        self._populate_product_combobox(available_products)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Quantity:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.quantity_spinbox = ttk.Spinbox(frame, from_=1, to=9999, increment=1, width=10)
        self.quantity_spinbox.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.quantity_spinbox.set(1) # Default quantity

        ttk.Label(frame, text="Unit Price:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.unit_price_label = ttk.Label(frame, text="$0.00")
        self.unit_price_label.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky="e")

        self.ok_button = ttk.Button(button_frame, text="OK", command=self._on_ok)
        self.ok_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self._on_cancel)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

    def _populate_product_combobox(self, available_products):
        try:
            products_list = available_products
            if products_list is None: # If not provided, fetch all
                 products_list = self.product_logic.get_all_products() # Expects list of Product structs

            if products_list:
                # Assuming products_list contains Product structs with 'product_id' and 'name'
                self.products_map = {p.name: p.product_id for p in products_list}
                self.product_combobox['values'] = sorted(list(self.products_map.keys()))
            else:
                self.product_combobox['values'] = []
                messagebox.showwarning("No Products", "No products available to select.", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load products: {e}", parent=self)
            self.product_combobox['values'] = []

    def _on_product_select(self, event=None):
        selected_name = self.product_combobox.get()
        if selected_name and selected_name in self.products_map:
            product_id = self.products_map[selected_name]
            # Fetch full product details to get the price (cost)
            self.selected_product_details = self.product_logic.get_product_details(product_id)
            if self.selected_product_details:
                price = self.selected_product_details.cost # Assuming 'cost' is the sale price
                self.unit_price_label.config(text=f"${price:,.2f}")
            else:
                self.unit_price_label.config(text="Error fetching price")
                self.selected_product_details = None # Clear if fetch failed
        else:
            self.unit_price_label.config(text="$0.00")
            self.selected_product_details = None

    def _load_existing_item(self):
        product_id = self.existing_item_data.get('product_id')
        quantity = self.existing_item_data.get('quantity', 1)

        self.selected_product_details = self.product_logic.get_product_details(product_id)
        if self.selected_product_details:
            product_name_to_select = self.selected_product_details.name

            # Check if this name is in the combobox values
            if product_name_to_select in self.product_combobox['values']:
                self.product_combobox.set(product_name_to_select)
            else:
                # Product might not be in the initial list (e.g., inactive but was on old order)
                # Add it temporarily or handle as error. For now, just show ID.
                # This implies `available_products` might need to be more dynamic or include inactive ones if editing old orders.
                self.product_combobox.set(f"ID: {product_id} (Not in list)")

            price = self.selected_product_details.cost
            self.unit_price_label.config(text=f"${price:,.2f}")
            self.quantity_spinbox.set(str(quantity))
        else:
            messagebox.showerror("Error", f"Could not load details for product ID: {product_id}", parent=self)
            # Potentially disable OK or close, for now, user can still cancel.
            self.product_combobox.set(f"Unknown Product ID: {product_id}")


    def _on_ok(self):
        selected_product_name = self.product_combobox.get()
        if not selected_product_name or not self.selected_product_details:
            messagebox.showerror("Validation Error", "Please select a valid product.", parent=self)
            return

        try:
            quantity = int(self.quantity_spinbox.get())
            if quantity <= 0:
                messagebox.showerror("Validation Error", "Quantity must be greater than zero.", parent=self)
                return
        except ValueError:
            messagebox.showerror("Validation Error", "Invalid quantity.", parent=self)
            return

        unit_price = self.selected_product_details.cost # From the stored Product struct
        line_total = quantity * unit_price

        self.result = {
            "product_id": self.selected_product_details.product_id,
            "product_name": self.selected_product_details.name, # For display in main popup's tree
            "quantity": quantity,
            "unit_price": unit_price,
            "line_total": line_total,
            # If editing, we might need to pass back the original item_id if it exists
            "item_id": self.existing_item_data.get('item_id') if self.existing_item_data else None
        }
        self.destroy()

    def _on_cancel(self):
        self.result = None # Explicitly set no result on cancel
        self.destroy()

    def show(self):
        """Show the dialog and wait for it to close. Returns the result."""
        self.wait_window()
        return self.result

# Example usage:
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Main Window (for testing item popup)")

    class MockProductLogic:
        def get_all_products(self):
            return [
                Product(product_id=1, name="Laptop", cost=1200.00, description="High-end laptop"),
                Product(product_id=2, name="Mouse", cost=25.00, description="Wireless mouse"),
                Product(product_id=3, name="Keyboard", cost=75.00, description="Mechanical keyboard")
            ]
        def get_product_details(self, product_id):
            if product_id == 1: return Product(product_id=1, name="Laptop", cost=1200.00)
            if product_id == 2: return Product(product_id=2, name="Mouse", cost=25.00)
            if product_id == 3: return Product(product_id=3, name="Keyboard", cost=75.00)
            return None

    product_logic_mock = MockProductLogic()

    all_prods_for_main_popup = product_logic_mock.get_all_products()


    def open_add_item_popup():
        # Pass the list of products fetched once by the main SalesDocumentPopup
        dialog = SalesDocumentItemPopup(root, product_logic_mock, available_products=all_prods_for_main_popup)
        result = dialog.show() # This will block until dialog is closed
        print("Add Item Result:", result)

    def open_edit_item_popup():
        existing_data = {'product_id': 2, 'quantity': 5, 'item_id': 123} # Simulate editing item with ID 123
        dialog = SalesDocumentItemPopup(root, product_logic_mock, existing_item_data=existing_data, available_products=all_prods_for_main_popup)
        result = dialog.show()
        print("Edit Item Result:", result)

    ttk.Button(root, text="Add Item", command=open_add_item_popup).pack(pady=10)
    ttk.Button(root, text="Edit Item (Mouse, Qty 5)", command=open_edit_item_popup).pack(pady=10)

    root.geometry("300x200")
    root.mainloop()
