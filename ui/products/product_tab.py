import tkinter as tk
from tkinter import messagebox, ttk
from ui.products.product_popup import ProductDetailsPopup
from ui.products.adjust_inventory_popup import AdjustInventoryPopup
from ui.products.transaction_history_popup import TransactionHistoryPopup
from ui.inventory_reports import InventoryReportPopup
from shared.structs import Product
# from core.logic.product_management import ProductLogic # For type hinting

class ProductTab:
    def __init__(self, master, address_book_logic, product_logic, inventory_service, purchase_logic): # Changed 'logic' to specific logics
        self.frame = tk.Frame(master)
        self.address_book_logic = address_book_logic # May not be needed by product_tab directly
        self.product_logic = product_logic # Store and use this for product operations
        self.inventory_service = inventory_service
        self.purchase_logic = purchase_logic
        self.selected_product_id = None

        self.setup_product_tab()
        self.load_products()

        self.frame.bind("<FocusIn>", self.load_products)

    def setup_product_tab(self):
        button_width = 20
        button_frame = tk.Frame(self.frame)
        button_frame.grid(row=0, column=0, columnspan=4, pady=5, sticky="w")

        self.new_button = tk.Button(
            button_frame, text="New",
            command=self.create_new_product, width=button_width)
        self.new_button.pack(side=tk.LEFT, padx=5)

        self.edit_button = tk.Button(
            button_frame, text="Edit",
            command=self.edit_existing_product, width=button_width)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = tk.Button(
            button_frame, text="Delete",
            command=self.remove_product, width=button_width)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        self.adjust_inventory_button = tk.Button(
            button_frame, text="Adjust Inventory",
            command=self.adjust_inventory, width=button_width)
        self.adjust_inventory_button.pack(side=tk.LEFT, padx=5)

        self.view_transactions_button = tk.Button(
            button_frame, text="Transaction History",
            command=self.view_transactions, width=button_width)
        self.view_transactions_button.pack(side=tk.LEFT, padx=5)

        self.reports_button = tk.Button(
            button_frame, text="Inventory Reports",
            command=self.open_reports, width=button_width)
        self.reports_button.pack(side=tk.LEFT, padx=5)

        self.tree = ttk.Treeview(
            self.frame,
            columns=(
                "id",
                "name",
                "description",
                "cost",
                "active",
                "category",
                "unit_of_measure",
                "qty_on_hand",
                "on_order",
                "reorder_point",
                "reorder_qty",
                "safety_stock",
            ),
            show="headings",
        )  # "price" -> "cost"

        self.tree.column("id", width=0, stretch=False) # Hidden ID column
        self.tree.heading("name", text="Product Name", command=lambda: self.sort_column("name", False))
        self.tree.heading("description", text="Description", command=lambda: self.sort_column("description", False))
        self.tree.heading("cost", text="Cost", command=lambda: self.sort_column("cost", False)) # "price" -> "cost"
        self.tree.heading("active", text="Active", command=lambda: self.sort_column("active", False))
        self.tree.heading("category", text="Category", command=lambda: self.sort_column("category", False))
        self.tree.heading("unit_of_measure", text="Unit of Measure", command=lambda: self.sort_column("unit_of_measure", False))
        self.tree.heading("qty_on_hand", text="On Hand", command=lambda: self.sort_column("qty_on_hand", False))
        self.tree.heading("on_order", text="On Order", command=lambda: self.sort_column("on_order", False))
        self.tree.heading("reorder_point", text="Reorder Point", command=lambda: self.sort_column("reorder_point", False))
        self.tree.heading("reorder_qty", text="Reorder Qty", command=lambda: self.sort_column("reorder_qty", False))
        self.tree.heading("safety_stock", text="Safety Stock", command=lambda: self.sort_column("safety_stock", False))

        self.tree.column("name", width=150, anchor=tk.W)
        self.tree.column("description", width=250, anchor=tk.W)
        self.tree.column("cost", width=80, anchor=tk.E)  # "price" -> "cost"
        self.tree.column("active", width=60, anchor=tk.CENTER)
        self.tree.column("category", width=100, anchor=tk.W)
        self.tree.column("unit_of_measure", width=100, anchor=tk.W)
        self.tree.column("qty_on_hand", width=80, anchor=tk.E)
        self.tree.column("on_order", width=80, anchor=tk.E)
        self.tree.column("reorder_point", width=100, anchor=tk.E)
        self.tree.column("reorder_qty", width=100, anchor=tk.E)
        self.tree.column("safety_stock", width=100, anchor=tk.E)

        self.tree.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.on_product_select)

    def sort_column(self, col, reverse):
        # Get data from treeview, specially handling the 'cost' column
        data_to_sort = []
        for k in self.tree.get_children(""):
            value_str = self.tree.set(k, col)
            if col == "cost":
                try:
                    # Attempt to convert cost to float after stripping '$'
                    actual_value = float(value_str.lstrip('$'))
                except ValueError:
                    actual_value = value_str # Fallback to string if conversion fails
            else:
                actual_value = value_str
            data_to_sort.append((actual_value, k))

        # Define a sort key that tries float conversion, falls back to string
        def sort_key(item):
            val = item[0]
            if isinstance(val, (int, float)):
                return (0, val) # Type 0 for numbers
            try:
                return (0, float(val)) # Try converting string to float
            except ValueError:
                return (1, str(val).lower()) # Type 1 for strings, case-insensitive

        data_to_sort.sort(key=sort_key, reverse=reverse)

        # Reorder items in the treeview
        for index, (val, k) in enumerate(data_to_sort):
            self.tree.move(k, "", index)

        # Update the heading command to toggle sort direction
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def on_product_select(self, event=None):
        selected_items = self.tree.selection()
        if selected_items:
            self.selected_product_id = selected_items[0]
        else:
            self.selected_product_id = None

    def remove_product(self):
        if not self.selected_product_id:
            messagebox.showwarning("No Selection", "Please select a product to delete.")
            return

        id_to_process = self.selected_product_id
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the selected product (ID: {id_to_process})?"
        )

        if confirm:
            try:
                self.product_logic.delete_product(id_to_process) # Use product_logic
                self.load_products()
                messagebox.showinfo(
                    "Success",
                    f"Product (ID: {id_to_process}) deleted successfully."
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete product: {e}")
            self.selected_product_id = None

    def edit_existing_product(self):
        if not self.selected_product_id:
            messagebox.showwarning("No Selection", "Please select a product to edit.")
            return
        # Pass self.product_logic to the popup
        popup = ProductDetailsPopup(self.frame.master, self, self.product_logic, product_id=self.selected_product_id)
        self.frame.master.wait_window(popup)
        self.load_products()

    def create_new_product(self):
        # Pass self.product_logic to the popup
        popup = ProductDetailsPopup(self.frame.master, self, self.product_logic, product_id=None)
        self.frame.master.wait_window(popup)
        self.load_products()

    def load_products(self, event=None):
        self.tree.delete(*self.tree.get_children())
        self.selected_product_id = None

        try:
            products = self.product_logic.get_all_products() # Use product_logic
            for product in products:
                self.tree.insert("", "end", iid=product.product_id, values=(
                    product.product_id,
                    product.name,
                    product.description,
                    f"${product.cost:.2f}", # Format cost with $
                    "Yes" if product.is_active else "No",
                    product.category,
                    product.unit_of_measure,
                    product.quantity_on_hand,
                    self.inventory_service.get_on_order_level(product.product_id),
                    product.reorder_point,
                    product.reorder_quantity,
                    product.safety_stock,
                ))
        except Exception as e:
            import traceback
            detailed_error_message = f"Detailed error in load_products: {type(e).__name__}: {e}"
            print(detailed_error_message)
            traceback.print_exc() # Prints the traceback to standard error
            messagebox.showerror("Load Error", f"Failed to load products. See console for details.\n{type(e).__name__}: {e}")
            # Kept the original print for your observation too, if it helps, but traceback is more important.
            # print(f"Original simple error in load_products: {e}")

    def refresh_products_list(self):
        self.load_products()

    def adjust_inventory(self):
        if not self.selected_product_id:
            messagebox.showwarning("No Selection", "Please select a product to adjust.")
            return
        product = self.product_logic.get_product_details(int(self.selected_product_id))
        if not product:
            messagebox.showerror("Error", "Could not load product details.")
            return
        popup = AdjustInventoryPopup(
            self.frame.master, self.inventory_service, product, self.refresh_products_list
        )
        self.frame.master.wait_window(popup)
        self.load_products()

    def view_transactions(self):
        if not self.selected_product_id:
            messagebox.showwarning("No Selection", "Please select a product to view transactions.")
            return
        popup = TransactionHistoryPopup(
            self.frame.master, self.inventory_service, int(self.selected_product_id)
        )
        self.frame.master.wait_window(popup)

    def open_reports(self):
        popup = InventoryReportPopup(
            self.frame.master, self.product_logic, self.inventory_service, self.purchase_logic
        )
        self.frame.master.wait_window(popup)

# Example of how to integrate into a main application (for testing)
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Product Management Tab Test")

    class MockLogic:
        def get_all_products(self):
            print("MockLogic: get_all_products called")
            return [
                Product(product_id=1, name="Laptop Pro", description="High-end laptop", price=1200.00),
                Product(product_id=2, name="Wireless Mouse", description="Ergonomic wireless mouse", price=25.99),
                Product(product_id=3, name="Mechanical Keyboard", description="RGB mechanical keyboard", price=75.50)
            ]

        def delete_product(self, product_id):
            print(f"MockLogic: delete_product called for {product_id}")
            messagebox.showinfo("Mock Delete", f"Product {product_id} would be deleted.")
            return True

        def get_product_details(self, product_id):
            print(f"MockLogic: get_product_details called for {product_id}")
            if product_id == 1:
                 return Product(product_id=1, name="Laptop Pro", description="High-end laptop", price=1200.00)
            return None

        def save_product(self, product):
            print(f"MockLogic: save_product called for {product.name if product else 'None'}")

    mock_logic = MockLogic()
    app_tab = ProductTab(root, mock_logic)
    app_tab.frame.pack(expand=True, fill=tk.BOTH)
    root.geometry("800x500") # Adjusted size
    root.mainloop()
