import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
# from core.purchase_logic import PurchaseLogic # Will be passed in
# from core.logic.product_management import ProductLogic # Will be passed in (adjust import path if needed)
from shared.structs import PurchaseDocumentItem, Product # For type hinting

class PurchaseDocumentItemPopup(tk.Toplevel):
    def __init__(self, master, purchase_logic, product_logic, document_id: int, item_data: Optional[dict] = None): # Added product_logic
        super().__init__(master)
        self.purchase_logic = purchase_logic
        self.product_logic = product_logic # Store product_logic
        self.document_id = document_id
        self.item_id = item_data.get('id') if item_data else None # For editing later

        self.product_map = {} # To map product name to product_id

        self.title(f"{'Edit' if self.item_id else 'Add'} Line Item")
        self.geometry("400x200") # Initial size, can adjust
        self.resizable(False, False)

        self.grab_set() # Make it modal
        self.focus_set()

        self.item_saved = False # Flag to indicate if save was successful

        # --- UI Elements ---
        frame = ttk.Frame(self, padding="10")
        frame.pack(expand=True, fill=tk.BOTH)

        row = 0
        # Product Selection
        ttk.Label(frame, text="Product:").grid(row=row, column=0, padx=5, pady=(0,2), sticky=tk.W)
        self.product_combobox = ttk.Combobox(frame, width=47, state="readonly")
        self.product_combobox.grid(row=row, column=1, padx=5, pady=(0,5), sticky=tk.EW)
        self.populate_products_dropdown()
        self.product_combobox.bind("<<ComboboxSelected>>", self._on_product_selected) # Bind event
        self.product_combobox.focus_set()
        row += 1

        # Description display (read-only, updates based on product selection or if manually set for non-catalog)
        # For now, we assume description comes from product. If manual override needed, this would change.
        # ttk.Label(frame, text="Description:").grid(row=row, column=0, padx=5, pady=(0,2), sticky=tk.W)
        # self.description_display = ttk.Label(frame, text="", width=50, relief="groove", padding=2) # Or a disabled Entry
        # self.description_display.grid(row=row, column=1, padx=5, pady=(0,5), sticky=tk.EW)
        # self.product_combobox.bind("<<ComboboxSelected>>", self.update_description_display) # TODO
        # row += 1


        ttk.Label(frame, text="Quantity:").grid(row=row, column=0, padx=5, pady=(5,2), sticky=tk.W)
        self.quantity_var = tk.StringVar()
        self.quantity_entry = ttk.Entry(frame, width=15, textvariable=self.quantity_var)
        self.quantity_entry.grid(row=row, column=1, padx=5, pady=(5,5), sticky=tk.E)
        row += 1

        # Unit Price
        self.unit_price_label = ttk.Label(frame, text="Unit Price:") # Definition
        self.unit_price_var = tk.StringVar() # Definition
        self.unit_price_entry = ttk.Entry(frame, width=15, textvariable=self.unit_price_var) # Definition
        self.unit_price_label.grid(row=row, column=0, padx=5, pady=(5,2), sticky=tk.W)
        self.unit_price_entry.grid(row=row, column=1, padx=5, pady=(5,5), sticky=tk.E)
        row += 1

        # Total Price (Read-only display)
        self.total_price_label = ttk.Label(frame, text="Total Price:") # Define if not already
        self.total_price_label.grid(row=row, column=0, padx=5, pady=(5,2), sticky=tk.W)
        self.total_price_display_var = tk.StringVar(value="$0.00") # Default display
        self.total_price_display_label = ttk.Label(frame, textvariable=self.total_price_display_var, width=15, anchor=tk.E, relief="sunken", borderwidth=1)
        self.total_price_display_label.grid(row=row, column=1, padx=5, pady=(5,5), sticky=tk.E)
        row += 1

        # Adjust popup geometry if new fields make it too cramped
        self.geometry("400x250") # Increased height

        # --- Buttons ---
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=(10,0), sticky=tk.E)

        self.save_button = ttk.Button(button_frame, text="Save Line Item", command=self.save_item)
        self.save_button.pack(side=tk.RIGHT, padx=5)

        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        self.cancel_button.pack(side=tk.RIGHT)

        if item_data:
            # If editing, try to set the product combobox
            if item_data.get('product_id'):
                # This requires product_map to be populated first by populate_products_dropdown
                # We might need to find the product name from product_id to set the combobox
                # For now, this part of editing is deferred until full edit mode is implemented
                pass
            self.quantity_var.set(str(item_data.get('quantity', '0'))) # Default to '0' if None
            if item_data.get('unit_price') is not None:
                 self.unit_price_var.set(f"{item_data.get('unit_price', 0.0):.2f}") # Format to 2 decimal places
            else:
                self.unit_price_var.set("0.00")
            self._calculate_and_display_total_price() # Calculate on load if editing
        else: # New item
            self.quantity_var.set("1") # Default quantity for new item
            self.unit_price_var.set("0.00") # Default unit price
            self._calculate_and_display_total_price()


        # Bindings for auto-calculation
        self.quantity_var.trace_add("write", self._on_price_quantity_change)
        self.unit_price_var.trace_add("write", self._on_price_quantity_change)

        # Adjustments for Edit Mode after all UI elements are defined and product list populated
        if item_data:
            # Set product in combobox
            if item_data.get('product_id'):
                product_id_to_select = item_data.get('product_id')
                selected_product_name = None
                for name, p_id in self.product_map.items():
                    if p_id == product_id_to_select:
                        selected_product_name = name
                        break
                if selected_product_name:
                    self.product_combobox.set(selected_product_name)
                else:
                    # Product ID from item_data not found in current product list, maybe log warning
                    self.product_combobox.set("<Select Product>") # Fallback

            # Set quantity (already done before, but ensure it's correct)
            self.quantity_var.set(str(item_data.get('quantity', '0')))

            # Set unit price: Use saved item's unit price if available, otherwise load default from product
            if item_data.get('unit_price') is not None:
                self.unit_price_var.set(f"{item_data.get('unit_price'):.2f}")
            else:
                # No unit price in item_data, so trigger default price loading if a product is set
                if self.product_combobox.get() != "<Select Product>":
                    self._on_product_selected() # Load default price for the selected product
                else: # No product selected in combobox either
                    self.unit_price_var.set("0.00")

            self._calculate_and_display_total_price() # Ensure total is calculated with final values
        else: # New item (already handled mostly, but ensure _on_product_selected isn't called if not needed)
            if self.product_combobox.get() == "<Select Product>": # If default "<Select Product>" is set
                 self.unit_price_var.set("0.00") # Ensure unit price is also default
            # Initial calculation for new item is already done after setting default qty/price

    def _on_price_quantity_change(self, *args):
        self._calculate_and_display_total_price()

    def _calculate_and_display_total_price(self):
        try:
            quantity = float(self.quantity_var.get()) if self.quantity_var.get() else 0.0
            unit_price = float(self.unit_price_var.get()) if self.unit_price_var.get() else 0.0
        except ValueError:
            self.total_price_display_var.set("Invalid") # Or some error indication
            return

        if quantity < 0: quantity = 0 # Treat negative as 0 for calculation
        if unit_price < 0: unit_price = 0 # Treat negative as 0

        total_price = quantity * unit_price
        self.total_price_display_var.set(f"${total_price:.2f}")


    def populate_products_dropdown(self):
        self.product_map.clear()
        product_display_names = ["<Select Product>"]

        # Assuming self.product_logic.get_all_products() returns a list of Product objects
        all_products = self.product_logic.get_all_products()
        for prod in all_products:
            # Using a more unique display if names can be non-unique, e.g., "Name (ID: X)"
            # For now, assuming names are reasonably distinct for selection.
            display_name = f"{prod.name}" # Consider adding (ID: {prod.product_id}) if names aren't unique
            self.product_map[display_name] = prod.product_id
            product_display_names.append(display_name)

        self.product_combobox['values'] = sorted(product_display_names)
        self.product_combobox.set("<Select Product>")
        # TODO: If editing an item, set the combobox to the item's current product.

    def _on_product_selected(self, event=None):
        """Handles product selection in the combobox to update the default unit price."""
        selected_product_name = self.product_combobox.get()
        product_id = self.product_map.get(selected_product_name)

        if product_id:
            product_details = self.product_logic.get_product_details(product_id)
            if product_details and product_details.cost is not None:
                self.unit_price_var.set(f"{product_details.cost:.2f}")
            else:
                self.unit_price_var.set("0.00") # Default if no cost or product not found
        else:
            self.unit_price_var.set("0.00") # Default if "<Select Product>" or error

        # Total price will auto-update due to the trace on unit_price_var

    # def update_description_display(self, event=None): # TODO if using a separate description label
    #     selected_product_name = self.product_combobox.get()
    #     product_id = self.product_map.get(selected_product_name)
    #     if product_id:
    #         # Fetch full product details if needed, or use already fetched data
    #         # For now, assume name is description enough or product_logic provides it
    #         # self.description_display.config(text=selected_product_name) # Or product.description
    #         pass
    #     else:
    #         # self.description_display.config(text="")
    #         pass

    def save_item(self):
        selected_product_name = self.product_combobox.get()
        quantity_str = self.quantity_var.get().strip()

        if not selected_product_name or selected_product_name == "<Select Product>":
            messagebox.showerror("Validation Error", "Please select a product.", parent=self)
            self.product_combobox.focus_set()
            return

        selected_product_id = self.product_map.get(selected_product_name)
        if selected_product_id is None:
            messagebox.showerror("Error", "Invalid product selection.", parent=self)
            return

        unit_price_str = self.unit_price_var.get().strip()

        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                raise ValueError("Quantity must be a positive number.")
        except ValueError:
            messagebox.showerror("Validation Error", "Quantity must be a valid positive number.", parent=self)
            self.quantity_entry.focus_set()
            return

        unit_price = None
        if unit_price_str: # Only parse if not empty
            try:
                unit_price = float(unit_price_str)
                if unit_price < 0:
                    # Allow zero price, but not negative
                    messagebox.showerror("Validation Error", "Unit Price cannot be negative.", parent=self)
                    self.unit_price_entry.focus_set()
                    return
            except ValueError:
                messagebox.showerror("Validation Error", "Unit Price must be a valid number (e.g., 123.45).", parent=self)
                self.unit_price_entry.focus_set()
                return

        # Recalculate total_price based on validated quantity and unit_price for saving
        # This ensures the saved total_price is accurate even if display had a temp "Invalid"
        current_total_price = None
        if quantity is not None and unit_price is not None:
             current_total_price = quantity * unit_price

        try:
            if self.item_id is None: # Adding new item
                new_item = self.purchase_logic.add_item_to_document(
                    doc_id=self.document_id,
                    product_id=selected_product_id,
                    quantity=quantity,
                    # product_description_override can be passed if needed
                    unit_price=unit_price, # Pass the parsed unit price
                    total_price=current_total_price # Pass the calculated total price
                )
                if new_item:
                    messagebox.showinfo("Success", "Item added successfully.", parent=self)
                    self.item_saved = True
                    self.destroy()
                else:
                    messagebox.showerror("Error", "Failed to add item.", parent=self)
            else: # Editing existing item
                 # This will call the new update_document_item in PurchaseLogic
                updated_item = self.purchase_logic.update_document_item(
                    item_id=self.item_id,
                    product_id=selected_product_id, # Assuming product can be changed, or keep original if not
                    # description will be fetched by logic based on product_id or use override
                    quantity=quantity,
                    unit_price=unit_price
                )
                if updated_item:
                    messagebox.showinfo("Success", "Item updated successfully.", parent=self)
                    self.item_saved = True
                    self.destroy()
                else:
                    messagebox.showerror("Error", "Failed to update item.", parent=self)

        except ValueError as ve:
            messagebox.showerror("Error", str(ve), parent=self)
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"An error occurred: {e}", parent=self)


if __name__ == '__main__':
    # Example Usage (requires mocking purchase_logic)
    class MockPurchaseLogic:
        def add_item_to_document(self, doc_id, product_description, quantity):
            print(f"Mock: Adding item '{product_description}', qty {quantity} to doc {doc_id}")
            from shared.structs import PurchaseDocumentItem # Local import for mock
            # Simulate successful save by returning a mock item
            return PurchaseDocumentItem(item_id=123, purchase_document_id=doc_id,
                                        product_description=product_description, quantity=quantity)

    root = tk.Tk()
    root.title("Main Window (for testing Item Popup)")
    # Hide root window as we only want to test the popup
    # root.withdraw()

    def open_add_item_popup():
        # Normally, purchase_logic and document_id would come from the parent popup/tab
        mock_logic = MockPurchaseLogic()
        test_doc_id = 1

        popup = PurchaseDocumentItemPopup(root, mock_logic, test_doc_id)
        root.wait_window(popup)
        if popup.item_saved:
            print("Item was saved (simulated).")
        else:
            print("Item popup closed without saving.")

    ttk.Button(root, text="Open Add Item Popup", command=open_add_item_popup).pack(pady=20)
    root.geometry("300x100")
    root.mainloop()
