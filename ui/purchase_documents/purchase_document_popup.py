import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List # Added for type hints
import datetime # Moved to top and ensured it's used generally

from shared.structs import PurchaseDocument, PurchaseDocumentItem, PurchaseDocumentStatus, AccountType
# from core.purchase_logic import PurchaseLogic # Will be passed in
# from core.address_book_logic import AddressBookLogic
# from shared.structs import PurchaseDocument, PurchaseDocumentItem, PurchaseDocumentStatus, AccountType

NO_VENDOR_LABEL = "<Select Vendor>"

class PurchaseDocumentPopup(tk.Toplevel):
    def __init__(self, master, purchase_logic, account_logic, document_id=None, parent_controller=None): # Added parent_controller
        super().__init__(master)
        self.purchase_logic = purchase_logic
        self.account_logic = account_logic # For populating vendor dropdown
        self.document_id = document_id
        self.parent_controller = parent_controller # Store it

        self.title(f"{'Edit' if document_id else 'New'} Purchase Document")
        self.geometry("700x500") # Adjusted size

        self.document_data: Optional[PurchaseDocument] = None
        self.items_data: List[PurchaseDocumentItem] = []
        self.vendor_map = {} # For mapping vendor name to ID

        self._setup_ui()

        if self.document_id:
            self.load_document_and_items()
        else:
            # Initialize for a new RFQ
            self.doc_number_var.set("(Auto-generated)")
            self.created_date_var.set(datetime.date.today().isoformat()) # Show today's date
            self.status_var.set(PurchaseDocumentStatus.RFQ.value)
            self.populate_vendor_dropdown() # Populate vendors for selection
            self.vendor_combobox.set(NO_VENDOR_LABEL)


    def _setup_ui(self):
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # --- Document Details Tab ---
        self.details_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.details_tab, text="Document Details")
        self._setup_details_tab()

        # --- Document Items Tab ---
        self.items_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.items_tab, text="Document Items")
        self._setup_items_tab()

        # Save and Close Buttons (at the bottom of the popup)
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10, padx=10, fill=tk.X)

        self.save_button = ttk.Button(button_frame, text="Save", command=self.save_document)
        self.save_button.pack(side=tk.RIGHT, padx=5)

        self.close_button = ttk.Button(button_frame, text="Close", command=self.destroy)
        self.close_button.pack(side=tk.RIGHT, padx=5)


    def _setup_details_tab(self):
        frame = self.details_tab

        # Variables for fields
        self.doc_number_var = tk.StringVar()
        self.created_date_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.selected_vendor_id = tk.IntVar() # Or StringVar if storing name then mapping

        row = 0
        ttk.Label(frame, text="Document #:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.doc_number_var, state=tk.DISABLED, width=40).grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1

        ttk.Label(frame, text="Vendor:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        self.vendor_combobox = ttk.Combobox(frame, state="readonly", width=37)
        self.vendor_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1

        ttk.Label(frame, text="Created Date:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.created_date_var, state=tk.DISABLED, width=40).grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1

        ttk.Label(frame, text="Status:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        # Status might be a Label or a Combobox for specific transitions later
        self.status_label = ttk.Label(frame, textvariable=self.status_var, width=40) # Using Label for now
        self.status_label.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        # Example for status combobox if needed for transitions:
        # self.status_combobox = ttk.Combobox(frame, textvariable=self.status_var, values=[s.value for s in PurchaseDocumentStatus], state="readonly")
        # self.status_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        row += 1

        ttk.Label(frame, text="Notes:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.NW)
        self.notes_text = tk.Text(frame, height=5, width=50)
        self.notes_text.grid(row=row, column=1, padx=5, pady=5, sticky=tk.EW)
        frame.grid_columnconfigure(1, weight=1) # Allow notes text to expand

    def _setup_items_tab(self):
        frame = self.items_tab

        # Buttons for item management
        item_button_frame = ttk.Frame(frame)
        item_button_frame.pack(pady=5, padx=5, fill=tk.X)

        ttk.Button(item_button_frame, text="Add Item", command=self.add_item).pack(side=tk.LEFT, padx=5)
        self.edit_item_button = ttk.Button(item_button_frame, text="Edit Item", command=self.edit_item, state=tk.DISABLED)
        self.edit_item_button.pack(side=tk.LEFT, padx=5)
        self.remove_item_button = ttk.Button(item_button_frame, text="Remove Item", command=self.remove_item, state=tk.DISABLED)
        self.remove_item_button.pack(side=tk.LEFT, padx=5)

        # Treeview for items
        item_columns = ("desc", "qty", "unit_price", "total_price")
        self.items_tree = ttk.Treeview(frame, columns=item_columns, show="headings", selectmode="browse")
        self.items_tree.heading("desc", text="Product/Service Description")
        self.items_tree.heading("qty", text="Quantity")
        self.items_tree.heading("unit_price", text="Unit Price")
        self.items_tree.heading("total_price", text="Total Price")

        self.items_tree.column("desc", width=300)
        self.items_tree.column("qty", width=80, anchor=tk.E)
        self.items_tree.column("unit_price", width=100, anchor=tk.E)
        self.items_tree.column("total_price", width=100, anchor=tk.E)

        self.items_tree.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_tree_select)
        # TODO: Add scrollbar for items treeview

    def populate_vendor_dropdown(self):
        self.vendor_map.clear()
        vendor_names = [NO_VENDOR_LABEL]
        # Assuming account_logic.get_all_accounts() returns Account objects
        # and we filter by account_type.
        all_accounts = self.account_logic.get_all_accounts()
        for acc in all_accounts:
            if acc.account_type == AccountType.VENDOR: # Compare with Enum member
                self.vendor_map[acc.name] = acc.account_id
                vendor_names.append(acc.name)

        self.vendor_combobox['values'] = sorted(list(set(vendor_names))) # Unique, sorted
        if self.document_data and self.document_data.vendor_id:
            for name, v_id in self.vendor_map.items():
                if v_id == self.document_data.vendor_id:
                    self.vendor_combobox.set(name)
                    return
        self.vendor_combobox.set(NO_VENDOR_LABEL)


    def load_document_and_items(self):
        if not self.document_id: return

        self.document_data = self.purchase_logic.get_purchase_document_details(self.document_id)
        if not self.document_data:
            messagebox.showerror("Error", f"Could not load document with ID {self.document_id}.")
            self.destroy()
            return

        self.doc_number_var.set(self.document_data.document_number)
        self.created_date_var.set(self.document_data.created_date.split("T")[0] if self.document_data.created_date else "") # Just date part
        self.status_var.set(self.document_data.status.value if self.document_data.status else "N/A")
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", self.document_data.notes or "")

        self.populate_vendor_dropdown() # This will set the vendor if found
        self.load_items_for_document()
        self.update_ui_states_based_on_status()


    def load_items_for_document(self):
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)

        if self.document_data and self.document_data.id:
            self.items_data = self.purchase_logic.get_items_for_document(self.document_data.id)
            for item in self.items_data:
                self.items_tree.insert("", tk.END, values=(
                    item.product_description,
                    f"{item.quantity:.2f}", # Format as float
                    f"{item.unit_price:.2f}" if item.unit_price is not None else "",
                    f"{item.total_price:.2f}" if item.total_price is not None else ""
                ), iid=str(item.id))
        self.on_item_tree_select(None)


    def on_item_tree_select(self, event):
        selected = self.items_tree.selection()
        can_edit_delete = bool(selected) and self.can_edit_items()

        self.edit_item_button.config(state=tk.NORMAL if can_edit_delete else tk.DISABLED)
        self.remove_item_button.config(state=tk.NORMAL if can_edit_delete else tk.DISABLED)

    def can_edit_items(self) -> bool:
        """Determines if items can be edited based on document status."""
        if not self.document_data or not self.document_data.status:
            return True # New document, can always edit
        return self.document_data.status in [PurchaseDocumentStatus.RFQ, PurchaseDocumentStatus.QUOTED]


    def update_ui_states_based_on_status(self):
        """Enable/disable fields based on document status."""
        can_edit_doc_details = True # Default
        can_edit_items_flag = self.can_edit_items()

        if self.document_data and self.document_data.status:
            current_status = self.document_data.status
            if current_status not in [PurchaseDocumentStatus.RFQ, PurchaseDocumentStatus.QUOTED]:
                self.vendor_combobox.config(state=tk.DISABLED)
                # Notes might still be editable
            if current_status in [PurchaseDocumentStatus.PO_ISSUED, PurchaseDocumentStatus.RECEIVED, PurchaseDocumentStatus.CLOSED]:
                 self.notes_text.config(state=tk.DISABLED) # Example: lock notes after PO issued
                 can_edit_doc_details = False


        # Item buttons
        self.edit_item_button.config(state=tk.NORMAL if can_edit_items_flag and self.items_tree.selection() else tk.DISABLED)
        self.remove_item_button.config(state=tk.NORMAL if can_edit_items_flag and self.items_tree.selection() else tk.DISABLED)
        # Add item button
        add_item_btn = self.items_tab.winfo_children()[0].winfo_children()[0] # Find "Add Item" button
        add_item_btn.config(state=tk.NORMAL if can_edit_items_flag else tk.DISABLED)


    def add_item(self):
        messagebox.showinfo("TODO", "Add Item functionality not fully implemented.")
        # Placeholder: Open a simple dialog to get item details
        # Then call self.purchase_logic.add_item_to_document(self.document_data.id, ...)
        # self.load_items_for_document()

    def edit_item(self):
        selected = self.items_tree.selection()
        if not selected: return
        item_id = int(selected[0])
        messagebox.showinfo("TODO", f"Edit Item {item_id} functionality not fully implemented.")
        # Placeholder: Open dialog, prefill with item data, then update
        # item_to_edit = next((i for i in self.items_data if i.id == item_id), None)
        # ...
        # self.purchase_logic.update_item_quote(item_id, new_unit_price) or a more general update
        # self.load_items_for_document()

    def remove_item(self):
        selected = self.items_tree.selection()
        if not selected: return
        item_id = int(selected[0])
        item_to_delete = next((i for i in self.items_data if i.id == item_id), None)

        if not item_to_delete: return

        confirm = messagebox.askyesno("Confirm Delete",
                                      f"Delete item '{item_to_delete.product_description}'?")
        if confirm:
            try:
                self.purchase_logic.delete_document_item(item_id)
                self.load_items_for_document()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete item: {e}")

    def save_document(self):
        # Validate Vendor
        selected_vendor_name = self.vendor_combobox.get()
        if not selected_vendor_name or selected_vendor_name == NO_VENDOR_LABEL:
            messagebox.showerror("Validation Error", "Please select a vendor.")
            return

        current_vendor_id = self.vendor_map.get(selected_vendor_name)
        if current_vendor_id is None: # Should not happen if list is populated correctly
            messagebox.showerror("Error", "Selected vendor is invalid.")
            return

        notes_content = self.notes_text.get("1.0", tk.END).strip()

        try:
            if self.document_id is None: # Creating a new document (RFQ)
                # Ensure a vendor is selected
                if current_vendor_id is None or selected_vendor_name == NO_VENDOR_LABEL: # Double check, though validated above
                    messagebox.showerror("Validation Error", "A vendor must be selected to create an RFQ.")
                    return

                new_doc = self.purchase_logic.create_rfq(
                    vendor_id=current_vendor_id,
                    notes=notes_content
                )
                if new_doc:
                    self.document_id = new_doc.id # IMPORTANT: Update the popup's state
                    self.document_data = new_doc
                    messagebox.showinfo("Success", f"RFQ {new_doc.document_number} created successfully.")

                    # Refresh the entire popup to reflect the new document's state
                    # This will correctly set doc number, status, and enable item tab functionalities.
                    self.load_document_and_items()

                    # Update the title to "Edit Purchase Document" as it's no longer new
                    self.title(f"Edit Purchase Document - {new_doc.document_number}")

                    # Switch to the items tab to encourage adding items
                    self.notebook.select(self.items_tab)

                    # Notify the main tab to refresh its list
                    if self.parent_controller and hasattr(self.parent_controller, 'load_documents'):
                         self.parent_controller.load_documents()
                else:
                    messagebox.showerror("Error", "Failed to create RFQ. Please check logs or input.")
            else: # Updating an existing document
                # Only notes and potentially vendor (if status allows) are directly updatable here.
                # Status changes have dedicated methods in logic.
                if self.document_data.vendor_id != current_vendor_id:
                    if self.document_data.status == PurchaseDocumentStatus.RFQ: # Allow vendor change for RFQ
                        # Need a DB method to update vendor_id if this is allowed
                        # self.db_handler.update_purchase_document_vendor(self.document_id, current_vendor_id)
                        # For now, let's assume vendor is fixed after creation or handled by more complex logic
                        messagebox.showwarning("Info", "Vendor change for existing documents not implemented here.")
                    else:
                        messagebox.showwarning("Warning", "Vendor cannot be changed for this document status.")

                self.purchase_logic.update_document_notes(self.document_id, notes_content)
                self.document_data = self.purchase_logic.get_purchase_document_details(self.document_id) # Re-fetch
                messagebox.showinfo("Success", f"Document {self.document_data.document_number} updated.")
                self.load_document_and_items() # Refresh display

            # Notify the main tab to refresh its list (if master is the tab controller)
            if hasattr(self.master, 'load_documents'): # Check if master has the method
                 self.master.load_documents() # This assumes master is the PurchaseDocumentTab instance

        except ValueError as ve:
            messagebox.showerror("Validation Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

        # Potentially close after save: self.destroy()
        # Or keep open for item management if new.

import datetime # Required for default created_date

if __name__ == '__main__':
    # Mocking for standalone testing
    class MockDBHandler:
        def get_all_accounts(self): return []
        def get_account_details(self, acc_id): return None
        # ... other methods needed by PurchaseLogic
        def add_purchase_document(self, **kwargs): return 1
        def get_purchase_document_by_id(self, doc_id):
            if doc_id == 1:
                return {"id": 1, "document_number": "RFQ-TEST-001", "vendor_id": 101,
                        "created_date": datetime.datetime.now().isoformat(),
                        "status": "RFQ", "notes": "Test notes from mock"}
            return None
        def get_items_for_document(self, doc_id): return []
        def add_purchase_document_item(self, **kwargs): return 10
        def update_purchase_document_notes(self, doc_id, notes): pass


    class MockAccountLogic:
        def get_all_accounts(self):
            # Simulate Account objects
            from shared.structs import Account, AccountType
            return [
                Account(account_id=101, name="Vendor A", account_type=AccountType.VENDOR),
                Account(account_id=102, name="Vendor B", account_type=AccountType.VENDOR),
                Account(account_id=201, name="Customer X", account_type=AccountType.CUSTOMER)
            ]
        def get_account_details(self, acc_id): return None


    class MockPurchaseLogic:
        def __init__(self, db_handler): self.db = db_handler
        def create_rfq(self, vendor_id, notes):
            doc_id = self.db.add_purchase_document(
                document_number="RFQ-MOCK-001", vendor_id=vendor_id,
                created_date=datetime.datetime.now().isoformat(), status="RFQ", notes=notes)
            return self.get_purchase_document_details(doc_id)
        def get_purchase_document_details(self, doc_id):
            data = self.db.get_purchase_document_by_id(doc_id)
            if data:
                 from shared.structs import PurchaseDocument, PurchaseDocumentStatus
                 return PurchaseDocument(doc_id=data['id'], document_number=data['document_number'],
                                         vendor_id=data['vendor_id'], created_date=data['created_date'],
                                         status=PurchaseDocumentStatus(data['status']), notes=data['notes'])
            return None
        def get_items_for_document(self, doc_id): return []
        def update_document_notes(self, doc_id, notes): pass
        # ... other methods

    root = tk.Tk()
    root.title("Popup Test")

    mock_db = MockDBHandler()
    mock_pl = MockPurchaseLogic(mock_db)
    mock_al = MockAccountLogic()

    def open_new():
        popup = PurchaseDocumentPopup(root, mock_pl, mock_al)
        root.wait_window(popup)

    def open_edit():
        # Create a dummy doc first to get an ID for editing
        # This is simplified; real scenario would involve selecting from a list
        doc = mock_pl.create_rfq(vendor_id=101, notes="Initial for edit")
        if doc:
            popup = PurchaseDocumentPopup(root, mock_pl, mock_al, document_id=doc.id)
            root.wait_window(popup)
        else:
            print("Failed to create mock document for editing.")


    ttk.Button(root, text="New Document", command=open_new).pack(pady=10)
    ttk.Button(root, text="Edit Document (ID 1)", command=open_edit).pack(pady=10)

    root.mainloop()
