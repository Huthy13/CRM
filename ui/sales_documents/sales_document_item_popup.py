import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from typing import Optional
from shared.structs import SalesDocumentItem, Product # Import Sales version

class SalesDocumentItemPopup(Toplevel): # Changed class name
    def __init__(self, master, sales_logic, product_logic, document_id: int, item_data: Optional[dict] = None):
        super().__init__(master)
        self.sales_logic = sales_logic # Use sales_logic
        self.product_logic = product_logic
        self.document_id = document_id # This is the sales_document_id
        self.item_id = item_data.get('id') if item_data else None

        self.product_map = {}

        self.title(f"{'Edit' if self.item_id else 'Add'} Line Item")
        self.geometry("450x300") # Adjusted size for discount field
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.item_saved = False

        # --- UI Elements ---
        frame = ttk.Frame(self, padding="10")
        frame.pack(expand=True, fill=tk.BOTH)

        row = 0
        # Product Selection
        ttk.Label(frame, text="Product:").grid(row=row, column=0, padx=5, pady=(0,2), sticky=tk.W)
        self.product_combobox = ttk.Combobox(frame, width=47, state="readonly")
        self.product_combobox.grid(row=row, column=1, padx=5, pady=(0,5), sticky=tk.EW)
        self.populate_products_dropdown()
        self.product_combobox.bind("<<ComboboxSelected>>", self._on_product_selected)
        self.product_combobox.focus_set()
        row += 1

        # Quantity
        ttk.Label(frame, text="Quantity:").grid(row=row, column=0, padx=5, pady=(5,2), sticky=tk.W)
        self.quantity_var = tk.StringVar(value="1") # Default to 1
        self.quantity_entry = ttk.Entry(frame, width=15, textvariable=self.quantity_var)
        self.quantity_entry.grid(row=row, column=1, padx=5, pady=(5,5), sticky=tk.E)
        row += 1

        # Unit Price (Sale Price)
        self.unit_price_label = ttk.Label(frame, text="Unit Price ($):")
        self.unit_price_var = tk.StringVar(value="0.00")
        self.unit_price_entry = ttk.Entry(frame, width=15, textvariable=self.unit_price_var)
        self.unit_price_label.grid(row=row, column=0, padx=5, pady=(5,2), sticky=tk.W)
        self.unit_price_entry.grid(row=row, column=1, padx=5, pady=(5,5), sticky=tk.E)
        row += 1

        # Discount Percentage
        ttk.Label(frame, text="Discount (%):").grid(row=row, column=0, padx=5, pady=(5,2), sticky=tk.W)
        self.discount_var = tk.StringVar(value="0.0") # Default discount
        self.discount_entry = ttk.Entry(frame, width=15, textvariable=self.discount_var)
        self.discount_entry.grid(row=row, column=1, padx=5, pady=(5,5), sticky=tk.E)
        row += 1

        # Line Total (Read-only display)
        self.line_total_label = ttk.Label(frame, text="Line Total ($):")
        self.line_total_label.grid(row=row, column=0, padx=5, pady=(5,2), sticky=tk.W)
        self.line_total_display_var = tk.StringVar(value="$0.00")
        self.line_total_display_label = ttk.Label(frame, textvariable=self.line_total_display_var, width=15, anchor=tk.E, relief="sunken", borderwidth=1)
        self.line_total_display_label.grid(row=row, column=1, padx=5, pady=(5,5), sticky=tk.E)
        row += 1

        # --- Buttons ---
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=(10,0), sticky=tk.E)
        self.save_button = ttk.Button(button_frame, text="Save Line Item", command=self.save_item)
        self.save_button.pack(side=tk.RIGHT, padx=5)
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        self.cancel_button.pack(side=tk.RIGHT)

        # Bindings for auto-calculation
        self.quantity_var.trace_add("write", self._on_value_change)
        self.unit_price_var.trace_add("write", self._on_value_change)
        self.discount_var.trace_add("write", self._on_value_change)

        if item_data:
            self.load_item_data(item_data)
        else: # New item
            self._calculate_and_display_line_total() # Initial calculation with defaults

    def load_item_data(self, item_data: dict):
        """Loads existing item data into the form fields."""
        if item_data.get('product_id'):
            prod_id_to_select = item_data.get('product_id')
            selected_prod_name = None
            for name, p_id in self.product_map.items():
                if p_id == prod_id_to_select:
                    selected_prod_name = name
                    break
            if selected_prod_name:
                self.product_combobox.set(selected_prod_name)
            else:
                self.product_combobox.set("<Select Product>") # Fallback if product not found

        self.quantity_var.set(str(item_data.get('quantity', '1')))
        self.unit_price_var.set(f"{item_data.get('unit_price', 0.0):.2f}")
        self.discount_var.set(f"{item_data.get('discount_percentage', 0.0):.1f}")
        # Line total will be recalculated by trace or explicitly
        self._calculate_and_display_line_total()


    def _on_value_change(self, *args):
        self._calculate_and_display_line_total()

    def _calculate_and_display_line_total(self):
        try:
            quantity = float(self.quantity_var.get()) if self.quantity_var.get() else 0.0
            unit_price = float(self.unit_price_var.get()) if self.unit_price_var.get() else 0.0
            discount = float(self.discount_var.get()) if self.discount_var.get() else 0.0
        except ValueError:
            self.line_total_display_var.set("Invalid")
            return

        if quantity < 0: quantity = 0
        if unit_price < 0: unit_price = 0
        if not (0 <= discount <= 100): discount = 0 # Basic validation, or show error

        line_total_val = quantity * unit_price * (1 - (discount / 100.0))
        self.line_total_display_var.set(f"${line_total_val:.2f}")


    def populate_products_dropdown(self):
        self.product_map.clear()
        product_display_names = ["<Select Product>"]
        all_products = self.product_logic.get_all_products() # Expects list of Product objects or dicts

        for prod_data in all_products: # Assuming get_all_products returns dicts now
            prod_name = prod_data.get('name')
            prod_id = prod_data.get('product_id') # This should be the DB 'id'
            if prod_name and prod_id is not None:
                display_name = f"{prod_name}"
                self.product_map[display_name] = prod_id
                product_display_names.append(display_name)

        self.product_combobox['values'] = sorted(product_display_names)
        self.product_combobox.set("<Select Product>")


    def _on_product_selected(self, event=None):
        selected_product_name = self.product_combobox.get()
        product_id = self.product_map.get(selected_product_name)

        if product_id:
            product_details = self.product_logic.get_product_details(product_id) # Expects dict
            if product_details and product_details.get('sale_price') is not None:
                self.unit_price_var.set(f"{product_details['sale_price']:.2f}")
            else: # Product found but no sale price
                self.unit_price_var.set("0.00")
                messagebox.showwarning("No Sale Price", f"Product '{selected_product_name}' does not have a sale price set.", parent=self)
        else: # "<Select Product>" or error
            self.unit_price_var.set("0.00")
        # Line total will auto-update due to trace

    def save_item(self):
        selected_product_name = self.product_combobox.get()
        quantity_str = self.quantity_var.get().strip()
        unit_price_str = self.unit_price_var.get().strip()
        discount_str = self.discount_var.get().strip()

        if not selected_product_name or selected_product_name == "<Select Product>":
            messagebox.showerror("Validation Error", "Please select a product.", parent=self)
            return
        selected_product_id = self.product_map.get(selected_product_name)
        if selected_product_id is None: # Should not happen if selection is from list
            messagebox.showerror("Error", "Invalid product selection.", parent=self)
            return

        try:
            quantity = float(quantity_str)
            if quantity <= 0: raise ValueError("Quantity must be positive.")
        except ValueError:
            messagebox.showerror("Validation Error", "Quantity must be a valid positive number.", parent=self)
            return

        try:
            unit_price = float(unit_price_str)
            if unit_price < 0: raise ValueError("Unit price cannot be negative.")
        except ValueError:
            messagebox.showerror("Validation Error", "Unit Price must be a valid number.", parent=self)
            return

        try:
            discount_percentage = float(discount_str)
            if not (0 <= discount_percentage <= 100):
                raise ValueError("Discount percentage must be between 0 and 100.")
        except ValueError:
            messagebox.showerror("Validation Error", "Discount must be a valid percentage (0-100).", parent=self)
            return

        # Fetch product description from product_logic, not just name, if available
        product_details_for_desc = self.product_logic.get_product_details(selected_product_id)
        final_product_description = product_details_for_desc.get('name', selected_product_name) if product_details_for_desc else selected_product_name

        # Line total is calculated by sales_logic.add_item_to_sales_document or update_sales_document_item
        try:
            if self.item_id is None: # Adding new item
                new_item = self.sales_logic.add_item_to_sales_document(
                    doc_id=self.document_id,
                    product_id=selected_product_id,
                    quantity=quantity,
                    unit_price_override=unit_price, # Pass the UI entered price as override
                    discount_percentage=discount_percentage,
                    product_description_override=final_product_description # Pass the fetched name/description
                )
                if new_item:
                    messagebox.showinfo("Success", "Item added successfully.", parent=self)
                    self.item_saved = True; self.destroy()
                else: messagebox.showerror("Error", "Failed to add item.", parent=self)
            else: # Editing existing item
                updated_item = self.sales_logic.update_sales_document_item(
                    item_id=self.item_id,
                    product_id=selected_product_id,
                    quantity=quantity,
                    unit_price_override=unit_price,
                    discount_percentage=discount_percentage,
                    product_description_override=final_product_description
                )
                if updated_item:
                    messagebox.showinfo("Success", "Item updated successfully.", parent=self)
                    self.item_saved = True; self.destroy()
                else: messagebox.showerror("Error", "Failed to update item.", parent=self)
        except ValueError as ve: messagebox.showerror("Error", str(ve), parent=self)
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"An error occurred: {e}", parent=self)
            import traceback; traceback.print_exc()


if __name__ == '__main__':
    class MockProductLogic:
        def get_all_products(self):
            # Simulate return of list of dicts as DatabaseHandler.get_all_products might
            return [
                {'product_id': 1, 'name': 'Super Widget', 'sale_price': 19.99},
                {'product_id': 2, 'name': 'Mega Gadget', 'sale_price': 29.50}
            ]
        def get_product_details(self, pid):
            if pid == 1: return {'product_id': 1, 'name': 'Super Widget', 'sale_price': 19.99, 'description': 'A truly super widget.'}
            if pid == 2: return {'product_id': 2, 'name': 'Mega Gadget', 'sale_price': 29.50, 'description': 'The best gadget ever.'}
            return None

    class MockSalesLogic:
        def add_item_to_sales_document(self, doc_id, product_id, quantity, unit_price_override, discount_percentage, product_description_override):
            print(f"Mock Add: DocID {doc_id}, ProdID {product_id}, Qty {quantity}, Price {unit_price_override}, Discount {discount_percentage}%, Desc: {product_description_override}")
            # Simulate SalesDocumentItem object creation for return
            from shared.structs import SalesDocumentItem # Local import
            return SalesDocumentItem(item_id=123, sales_document_id=doc_id, product_id=product_id, quantity=quantity, unit_price=unit_price_override, discount_percentage=discount_percentage, product_description=product_description_override)

        def update_sales_document_item(self, item_id, product_id, quantity, unit_price_override, discount_percentage, product_description_override):
            print(f"Mock Update: ItemID {item_id}, ProdID {product_id}, Qty {quantity}, Price {unit_price_override}, Discount {discount_percentage}%, Desc: {product_description_override}")
            from shared.structs import SalesDocumentItem # Local import
            return SalesDocumentItem(item_id=item_id, sales_document_id=1, product_id=product_id, quantity=quantity, unit_price=unit_price_override, discount_percentage=discount_percentage, product_description=product_description_override)

        # Minimal mock for get_sales_document_item_details needed if load_item_data calls it
        def get_sales_document_item_details(self, item_id): return None


    root = tk.Tk()
    root.title("Item Popup Test Host")

    mock_prod_logic = MockProductLogic()
    mock_sales_logic = MockSalesLogic() # Sales logic now passed

    def open_add_item_popup():
        popup = SalesDocumentItemPopup(root, mock_sales_logic, mock_prod_logic, document_id=1)
        root.wait_window(popup)

    def open_edit_item_popup():
        sample_item_data = {
            'id': 101, 'sales_document_id': 1, 'product_id': 1,
            'product_description': 'Super Widget', 'quantity': 2.0,
            'unit_price': 19.99, 'discount_percentage': 10.0, 'line_total': 35.98
        }
        popup = SalesDocumentItemPopup(root, mock_sales_logic, mock_prod_logic, document_id=1, item_data=sample_item_data)
        root.wait_window(popup)

    ttk.Button(root, text="Add Sales Item", command=open_add_item_popup).pack(pady=10)
    ttk.Button(root, text="Edit Sales Item", command=open_edit_item_popup).pack(pady=10)
    root.mainloop()
Tool output for `create_file_with_block`:
