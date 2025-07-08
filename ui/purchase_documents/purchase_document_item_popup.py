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

        self.title(f"{'Edit' if self.item_id else 'Add'} Document Item")
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
        self.product_combobox = ttk.Combobox(frame, width=47, state="readonly") # Width might need adjustment
        self.product_combobox.grid(row=row, column=1, padx=5, pady=(0,5), sticky=tk.EW)
        self.populate_products_dropdown()
        self.product_combobox.focus_set() # Focus here first
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
        # TODO: Add validation for quantity to be numeric (e.g., using validatecommand)
        row += 1

        # Unit Price - for now, only visible if editing an existing item that might have it
        # or if we decide to allow setting it during 'add' for certain document statuses.
        # For simplicity in "Add Item" for an RFQ, this might be hidden or disabled.
        self.unit_price_label = ttk.Label(frame, text="Unit Price:")
        self.unit_price_var = tk.StringVar()
        self.unit_price_entry = ttk.Entry(frame, width=15, textvariable=self.unit_price_var)

        # For "Add Item" to RFQ, unit price is usually not set.
        # We'll handle visibility/state based on whether it's a new item or editing, and doc status.
        # For now, let's assume it's not part of the "Add Item" for an RFQ.
        # If item_data and 'unit_price' in item_data: # Logic for edit mode
        #     self.unit_price_label.grid(row=row, column=0, padx=5, pady=(5,2), sticky=tk.W)
        #     self.unit_price_entry.grid(row=row, column=1, padx=5, pady=(5,5), sticky=tk.E)
        #     row += 1


        # --- Buttons ---
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=(10,0), sticky=tk.E)

        self.save_button = ttk.Button(button_frame, text="Save Item", command=self.save_item)
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
            # self.description_entry.insert(0, item_data.get('product_description', '')) # No longer direct entry
            self.quantity_var.set(str(item_data.get('quantity', '')))
            if item_data.get('unit_price') is not None:
                 self.unit_price_var.set(str(item_data.get('unit_price', '')))

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
        if selected_product_id is None: # Should not happen if combobox is populated correctly
            messagebox.showerror("Error", "Invalid product selection.", parent=self)
            return

        # Description will be handled by PurchaseLogic based on product_id
        # Or, if a description override field exists, get it here.

        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                raise ValueError("Quantity must be a positive number.")
        except ValueError:
            messagebox.showerror("Validation Error", "Quantity must be a valid positive number.", parent=self)
            self.quantity_entry.focus_set()
            return

        # unit_price = None # For RFQ add item
        # if self.item_id and unit_price_str: # If editing and price is provided
        #     try:
        #         unit_price = float(unit_price_str)
        #         if unit_price < 0:
        #             raise ValueError("Unit price cannot be negative.")
        #     except ValueError:
        #         messagebox.showerror("Validation Error", "Unit Price must be a valid non-negative number.", parent=self)
        #         self.unit_price_entry.focus_set()
        #         return

        try:
            if self.item_id is None: # Adding new item
                # product_description_override can be added if we want to allow overriding the fetched product name
                new_item = self.purchase_logic.add_item_to_document(
                    doc_id=self.document_id,
                    product_id=selected_product_id,
                    quantity=quantity
                    # product_description_override = "Optional override" # If needed
                )
                if new_item:
                    messagebox.showinfo("Success", "Item added successfully.", parent=self)
                    self.item_saved = True
                    self.destroy()
                else:
                    messagebox.showerror("Error", "Failed to add item.", parent=self)
            else:
                # TODO: Implement update logic for item (will use self.item_id)
                # self.purchase_logic.update_document_item(...)
                messagebox.showinfo("TODO", "Item update not yet implemented.", parent=self)
                # For now, just close if it was an "edit" attempt
                # self.item_saved = True
                # self.destroy()
                pass

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
