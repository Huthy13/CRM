import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
# from core.purchase_logic import PurchaseLogic # Will be passed in
# from shared.structs import PurchaseDocumentItem # For type hinting

class PurchaseDocumentItemPopup(tk.Toplevel):
    def __init__(self, master, purchase_logic, document_id: int, item_data: Optional[dict] = None):
        super().__init__(master)
        self.purchase_logic = purchase_logic
        self.document_id = document_id
        self.item_id = item_data.get('id') if item_data else None # For editing later

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
        ttk.Label(frame, text="Product/Service Description:").grid(row=row, column=0, columnspan=2, padx=5, pady=(0,2), sticky=tk.W)
        row += 1
        self.description_entry = ttk.Entry(frame, width=50)
        self.description_entry.grid(row=row, column=0, columnspan=2, padx=5, pady=(0,5), sticky=tk.EW)
        self.description_entry.focus_set() # Focus on this field initially
        row += 1

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
            self.description_entry.insert(0, item_data.get('product_description', ''))
            self.quantity_var.set(str(item_data.get('quantity', '')))
            if item_data.get('unit_price') is not None:
                 self.unit_price_var.set(str(item_data.get('unit_price', '')))


    def save_item(self):
        description = self.description_entry.get().strip()
        quantity_str = self.quantity_var.get().strip()
        # unit_price_str = self.unit_price_var.get().strip() # For later

        if not description:
            messagebox.showerror("Validation Error", "Product/Service Description cannot be empty.", parent=self)
            self.description_entry.focus_set()
            return

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
                new_item = self.purchase_logic.add_item_to_document(
                    doc_id=self.document_id,
                    product_description=description,
                    quantity=quantity
                    # unit_price will be None for initial RFQ item add via this path
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
