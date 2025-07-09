import tkinter as tk
from tkinter import ttk, messagebox
from shared.structs import Product
# from core.address_book_logic import AddressBookLogic # Not directly needed if ProductLogic handles all product aspects
from core.logic.product_management import ProductLogic # Import ProductLogic
from ui.category_popup import CategoryListPopup

class ProductDetailsPopup(tk.Toplevel):
    def __init__(self, master_window, product_tab_controller, product_logic: ProductLogic, product_id=None): # Changed logic to product_logic
        self.product_tab_controller = product_tab_controller
        super().__init__(master_window)
        self.product_logic = product_logic # Store and use ProductLogic
        self.product_id = product_id
        self.title(f"{'Edit' if product_id else 'Add'} Product")
        self.geometry("400x320")

        self.product_data = None # To store loaded product data if editing
        self.is_active_var = tk.BooleanVar(value=True) # Variable for Checkbutton

        # --- UI Elements ---
        tk.Label(self, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = tk.Entry(self, width=40)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.description_entry = tk.Entry(self, width=40)
        self.description_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self, text="Cost:").grid(row=2, column=0, padx=5, pady=5, sticky="w") # Label changed
        self.cost_entry = tk.Entry(self, width=40) # Renamed from price_entry
        self.cost_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(self, text="Category:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.category_combobox = ttk.Combobox(self, width=37)
        self.category_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="ew") # Use sticky

        self.manage_categories_button = ttk.Button(self, text="...", command=self.open_category_manager, width=3)
        self.manage_categories_button.grid(row=3, column=2, padx=(0, 5), pady=5, sticky="w")

        self.grid_columnconfigure(1, weight=1) # Allow combobox to expand a bit if window is resized

        self.populate_category_combobox()


        tk.Label(self, text="Unit of Measure:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.unit_of_measure_combobox = ttk.Combobox(self, width=37) # Changed to Combobox
        self.unit_of_measure_combobox.grid(row=4, column=1, padx=5, pady=5)
        self.populate_unit_of_measure_combobox()

        tk.Label(self, text="Active:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.active_checkbutton = tk.Checkbutton(self, variable=self.is_active_var)
        self.active_checkbutton.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        # Save and Cancel Buttons
        self.save_button = tk.Button(self, text="Save", command=self.save_product)
        self.save_button.grid(row=6, column=0, padx=5, pady=10, sticky="e")

        self.cancel_button = tk.Button(self, text="Cancel", command=self.destroy)
        self.cancel_button.grid(row=6, column=1, padx=5, pady=10, sticky="w")

        if self.product_id:
            self.load_product_details()
        else: # For new product, still populate lists but don't set specific values
            self.category_combobox.set("")
            self.unit_of_measure_combobox.set("")


    def populate_category_combobox(self):
        self.category_path_to_leaf_id_map = {}
        self.leaf_id_to_category_path_map = {}
        try:
            flat_paths_data = self.product_logic.get_flat_category_paths() # Use product_logic
            display_paths = []
            for leaf_id, path_str in flat_paths_data:
                display_paths.append(path_str)
                self.category_path_to_leaf_id_map[path_str] = leaf_id
                self.leaf_id_to_category_path_map[leaf_id] = path_str

            self.category_combobox['values'] = display_paths
            if not self.product_id and display_paths: # For new product, default to first if available
                self.category_combobox.set("") # Or set to first: display_paths[0]
            elif not display_paths:
                 self.category_combobox.set("")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load categories: {e}", parent=self)
            self.category_combobox['values'] = []
            self.category_combobox.set("")


    def populate_unit_of_measure_combobox(self):
        try:
            units = self.product_logic.get_all_product_units_of_measure() # Use product_logic
            self.unit_of_measure_combobox['values'] = units
            if not self.product_id and units: # For new product
                self.unit_of_measure_combobox.set("") # Or set to first: units[0]
            elif not units:
                self.unit_of_measure_combobox.set("")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load units of measure: {e}", parent=self)
            self.unit_of_measure_combobox['values'] = []
            self.unit_of_measure_combobox.set("")

    def open_category_manager(self):
        # Store current selection to try and re-select it later
        current_selected_path = self.category_combobox.get()

        category_manager_popup = CategoryListPopup(self, self.product_logic) # Use product_logic
        self.wait_window(category_manager_popup) # Wait for the category manager to close

        # Refresh the combobox contents
        self.populate_category_combobox()

        # Try to re-select the previously selected/typed path
        if current_selected_path in self.category_combobox['values']:
            self.category_combobox.set(current_selected_path)
        elif self.category_combobox['values']: # If previous not found, select first available
            self.category_combobox.current(0)
        else: # If list is empty
            self.category_combobox.set('')


    def load_product_details(self):
        product_details = self.product_logic.get_product_details(self.product_id) # Use product_logic
        if product_details:
            self.product_data = product_details
            self.name_entry.insert(0, product_details.name if product_details.name else "")
            self.description_entry.insert(0, product_details.description if product_details.description else "")
            cost_display = f"${product_details.cost:.2f}" if product_details.cost is not None else ""
            self.cost_entry.insert(0, cost_display)

            # Product.category from logic layer is the full path string
            category_path_to_set = product_details.category if product_details.category else ""

            # Ensure this path is in the combobox values. If not, it implies an issue or stale data.
            # For robustness, it might be good to refresh combobox values if path not found,
            # but for now, we assume populate_category_combobox has run and is up-to-date.
            if category_path_to_set and category_path_to_set not in self.category_combobox['values']:
                # This case should ideally not happen if categories are managed correctly and list is fresh
                # If it does, we could add it or show a warning. For now, just try to set it.
                # To be safe, add it to the list if it's a valid path from an existing product
                # but somehow not in the current combobox list (e.g. if list was filtered)
                # However, get_flat_category_paths() should list all.
                 pass # Or log a warning: print(f"Warning: Category path '{category_path_to_set}' not in combobox values during load.")

            self.category_combobox.set(category_path_to_set)

            current_unit = product_details.unit_of_measure if product_details.unit_of_measure else ""
            if current_unit and current_unit not in self.unit_of_measure_combobox['values']:
                current_values_uom = list(self.unit_of_measure_combobox['values'])
                updated_values_uom = [current_unit] + current_values_uom
                self.unit_of_measure_combobox['values'] = updated_values_uom
            self.unit_of_measure_combobox.set(current_unit)

            self.is_active_var.set(product_details.is_active)
        else:
            messagebox.showerror("Error", f"Could not load details for product ID: {self.product_id}")
            self.destroy()

    def save_product(self):
        name = self.name_entry.get().strip()
        description = self.description_entry.get().strip()
        cost_str = self.cost_entry.get().strip() # Renamed from price_str

        selected_category_path = self.category_combobox.get().strip()
        leaf_category_name = ""
        if selected_category_path:
            # Extract leaf name from path "Parent\\Child\\Leaf" -> "Leaf"
            leaf_category_name = selected_category_path.split('\\')[-1]

        unit_of_measure = self.unit_of_measure_combobox.get().strip()
        is_active = self.is_active_var.get()

        if not name:
            messagebox.showerror("Validation Error", "Name cannot be empty.")
            return

        # Attempt to parse cost, stripping '$' if present
        if cost_str.startswith('$'):
            cost_str_to_parse = cost_str[1:]
        else:
            cost_str_to_parse = cost_str

        try:
            cost = float(cost_str_to_parse)
            if cost < 0:
                messagebox.showerror("Validation Error", "Cost cannot be negative.")
                return
        except ValueError:
            messagebox.showerror("Validation Error", "Cost must be a valid number (e.g., 123.45).")
            return

        product_obj = Product(
            product_id=self.product_id,
            name=name,
            description=description,
            cost=cost,
            category=leaf_category_name, # Save only the leaf name
            unit_of_measure=unit_of_measure,
            is_active=is_active
        )

        try:
            self.product_logic.save_product(product_obj) # Use product_logic
            messagebox.showinfo("Success", "Product saved successfully!")
            self.product_tab_controller.refresh_products_list()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save product: {e}")

if __name__ == '__main__':
    # This is for testing purposes
    # Note: The MockLogic below would need to be updated to MockProductLogic
    # and have the methods expected by ProductDetailsPopup if running this file standalone.
    class MockProductLogic: # Renamed for clarity
        def get_product_details(self, product_id):
            print(f"MockProductLogic: get_product_details called for ID: {product_id}")
            if product_id == 1:
                return Product(product_id=1, name="Test Product", description="A product for testing", cost=19.99) # cost not price
            return None

        def save_product(self, product):
            print(f"MockProductLogic: save_product called with: {product.name if product else 'None'}")

        def get_flat_category_paths(self): return [ (1, "CatA\\Sub1"), (2, "CatB")]
        def get_all_product_units_of_measure(self): return ["Each", "Box"]


    class MockMaster(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Mock Master")
            self.geometry("200x100")
            tk.Button(self, text="Open Add Product", command=self.open_add_product).pack(pady=5)
            tk.Button(self, text="Open Edit Product", command=self.open_edit_product).pack(pady=5)

        def open_add_product(self):
            mock_controller = self
            popup = ProductDetailsPopup(self, mock_controller, MockLogic())
            self.wait_window(popup)

        def open_edit_product(self):
            mock_controller = self
            popup = ProductDetailsPopup(self, mock_controller, MockLogic(), product_id=1)
            self.wait_window(popup)

        def refresh_products_list(self):
            print("MockMaster: refresh_products_list called")

    app = MockMaster()
    app.mainloop()
