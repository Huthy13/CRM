import tkinter as tk
from tkinter import ttk, messagebox
from shared.structs import Product  # Import Product
from core.logic import AddressBookLogic

class ProductDetailsPopup(tk.Toplevel):
    def __init__(self, master_window, product_tab_controller, logic: AddressBookLogic, product_id=None):
        self.product_tab_controller = product_tab_controller
        super().__init__(master_window)
        self.logic = logic
        self.product_id = product_id
        self.title(f"{'Edit' if product_id else 'Add'} Product")
        self.geometry("400x320")  # Adjusted geometry for new fields

        self.product_data = None # To store loaded product data if editing
        self.is_active_var = tk.BooleanVar(value=True) # Variable for Checkbutton

        # --- UI Elements ---
        tk.Label(self, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = tk.Entry(self, width=40)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.description_entry = tk.Entry(self, width=40)
        self.description_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self, text="Price:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.price_entry = tk.Entry(self, width=40)
        self.price_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(self, text="Category:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.category_entry = tk.Entry(self, width=40)
        self.category_entry.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(self, text="Unit of Measure:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.unit_of_measure_entry = tk.Entry(self, width=40)
        self.unit_of_measure_entry.grid(row=4, column=1, padx=5, pady=5)

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

    def load_product_details(self):
        product_details = self.logic.get_product_details(self.product_id)
        if product_details:
            self.product_data = product_details
            self.name_entry.insert(0, product_details.name if product_details.name else "")
            self.description_entry.insert(0, product_details.description if product_details.description else "")
            self.price_entry.insert(0, str(product_details.price) if product_details.price is not None else "")
            self.category_entry.insert(0, product_details.category if product_details.category else "")
            self.unit_of_measure_entry.insert(0, product_details.unit_of_measure if product_details.unit_of_measure else "")
            self.is_active_var.set(product_details.is_active)
        else:
            messagebox.showerror("Error", f"Could not load details for product ID: {self.product_id}")
            self.destroy()

    def save_product(self):
        name = self.name_entry.get().strip()
        description = self.description_entry.get().strip()
        price_str = self.price_entry.get().strip()
        category = self.category_entry.get().strip()
        unit_of_measure = self.unit_of_measure_entry.get().strip()
        is_active = self.is_active_var.get()

        if not name:
            messagebox.showerror("Validation Error", "Name cannot be empty.")
            return

        try:
            price = float(price_str)
            if price < 0:
                messagebox.showerror("Validation Error", "Price cannot be negative.")
                return
        except ValueError:
            messagebox.showerror("Validation Error", "Price must be a valid number.")
            return

        product_obj = Product(
            product_id=self.product_id,
            name=name,
            description=description,
            price=price,
            category=category,
            unit_of_measure=unit_of_measure,
            is_active=is_active
        )

        try:
            self.logic.save_product(product_obj)
            messagebox.showinfo("Success", "Product saved successfully!")
            self.product_tab_controller.refresh_products_list()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save product: {e}")

if __name__ == '__main__':
    # This is for testing purposes
    class MockLogic:
        def get_product_details(self, product_id):
            print(f"Mock: get_product_details called for ID: {product_id}")
            if product_id == 1:
                return Product(product_id=1, name="Test Product", description="A product for testing", price=19.99)
            return None

        def save_product(self, product):
            print(f"Mock: save_product called with: {product.name if product else 'None'}")

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
