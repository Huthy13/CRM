import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
import datetime

from shared.structs import PurchaseDocument, PurchaseDocumentItem, PurchaseDocumentStatus, AccountType

NO_VENDOR_LABEL = "<Select Vendor>"

class PurchaseDocumentPopup(tk.Toplevel):
    def __init__(self, master, purchase_logic, account_logic, product_logic, document_id=None, parent_controller=None):
        super().__init__(master)
        self.purchase_logic = purchase_logic
        self.account_logic = account_logic
        self.product_logic = product_logic
        self.document_id = document_id
        self.parent_controller = parent_controller

        self.title(f"{'Edit' if document_id else 'New'} Purchase Document")
        self.geometry("700x550") # Increased height slightly for better spacing

        self.document_data: Optional[PurchaseDocument] = None
        self.items_data: List[PurchaseDocumentItem] = []
        self.vendor_map = {}

        self._setup_ui()

        if self.document_id:
            self.load_document_and_items()
        else:
            self.doc_number_var.set("(Auto-generated)")
            self.created_date_var.set(datetime.date.today().isoformat())
            self.status_var.set(PurchaseDocumentStatus.RFQ.value)
            self.populate_vendor_dropdown()
            self.vendor_combobox.set(NO_VENDOR_LABEL)
            self._update_document_subtotal() # Ensure subtotal is $0.00 initially
            self.update_ui_states_based_on_status() # Set initial UI states

    def _setup_ui(self):
        # Main content frame
        self.content_frame = ttk.Frame(self, padding="10")
        self.content_frame.pack(expand=True, fill=tk.BOTH)

        # Variables for fields
        self.doc_number_var = tk.StringVar()
        self.created_date_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.subtotal_var = tk.StringVar(value="$0.00")

        # Layout using grid
        current_row = 0

        # Document Details Section
        ttk.Label(self.content_frame, text="Document #:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(self.content_frame, textvariable=self.doc_number_var, state=tk.DISABLED, width=40).grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.EW)
        current_row += 1

        ttk.Label(self.content_frame, text="Vendor:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.W)
        self.vendor_combobox = ttk.Combobox(self.content_frame, state="readonly", width=37)
        self.vendor_combobox.grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.EW)
        current_row += 1

        ttk.Label(self.content_frame, text="Created Date:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(self.content_frame, textvariable=self.created_date_var, state=tk.DISABLED, width=40).grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.EW)
        current_row += 1

        ttk.Label(self.content_frame, text="Status:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.W)
        self.status_label = ttk.Label(self.content_frame, textvariable=self.status_var, width=40)
        self.status_label.grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.EW)
        current_row += 1

        # Document Items Section (within a LabelFrame)
        items_label_frame = ttk.LabelFrame(self.content_frame, text="Document Items", padding="5")
        items_label_frame.grid(row=current_row, column=0, columnspan=2, padx=5, pady=(10,5), sticky=tk.NSEW)
        self.content_frame.grid_rowconfigure(current_row, weight=1) # Allow items section to expand
        current_row += 1

        self.item_button_frame = ttk.Frame(items_label_frame)
        self.item_button_frame.pack(pady=5, fill=tk.X)

        self.add_item_button = ttk.Button(self.item_button_frame, text="Add Item", command=self.add_item)
        self.add_item_button.pack(side=tk.LEFT, padx=5)
        self.edit_item_button = ttk.Button(self.item_button_frame, text="Edit Item", command=self.edit_item, state=tk.DISABLED)
        self.edit_item_button.pack(side=tk.LEFT, padx=5)
        self.remove_item_button = ttk.Button(self.item_button_frame, text="Remove Item", command=self.remove_item, state=tk.DISABLED)
        self.remove_item_button.pack(side=tk.LEFT, padx=5)

        item_columns = ("desc", "qty", "unit_price", "total_price")
        self.items_tree = ttk.Treeview(items_label_frame, columns=item_columns, show="headings", selectmode="browse", height=5)
        self.items_tree.heading("desc", text="Product/Service Description")
        self.items_tree.heading("qty", text="Quantity")
        self.items_tree.heading("unit_price", text="Unit Price")
        self.items_tree.heading("total_price", text="Total Price")
        self.items_tree.column("desc", width=250)
        self.items_tree.column("qty", width=70, anchor=tk.E)
        self.items_tree.column("unit_price", width=90, anchor=tk.E)
        self.items_tree.column("total_price", width=90, anchor=tk.E)

        items_scrollbar = ttk.Scrollbar(items_label_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)
        self.items_tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Notes Section
        ttk.Label(self.content_frame, text="Notes:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.NW)
        self.notes_text = tk.Text(self.content_frame, height=4, width=50)
        self.notes_text.grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.EW)
        current_row += 1

        # Document Subtotal Section
        ttk.Label(self.content_frame, text="Document Subtotal:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(self.content_frame, textvariable=self.subtotal_var, font=('TkDefaultFont', 10, 'bold')).grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.E)
        current_row += 1

        self.content_frame.grid_columnconfigure(1, weight=1)

        bottom_button_frame = ttk.Frame(self)
        bottom_button_frame.pack(pady=10, padx=10, fill=tk.X, side=tk.BOTTOM)

        self.save_button = ttk.Button(bottom_button_frame, text="Save", command=self.save_document)
        self.save_button.pack(side=tk.RIGHT, padx=5)

        self.close_button = ttk.Button(bottom_button_frame, text="Close", command=self.destroy)
        self.close_button.pack(side=tk.RIGHT, padx=5)

    def populate_vendor_dropdown(self):
        self.vendor_map.clear()
        vendor_names = [NO_VENDOR_LABEL]
        all_accounts = self.account_logic.get_all_accounts()
        for acc in all_accounts:
            if acc.account_type == AccountType.VENDOR:
                self.vendor_map[acc.name] = acc.account_id
                vendor_names.append(acc.name)
        self.vendor_combobox['values'] = sorted(list(set(vendor_names)))
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
        self.created_date_var.set(self.document_data.created_date.split("T")[0] if self.document_data.created_date else "")
        self.status_var.set(self.document_data.status.value if self.document_data.status else "N/A")
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", self.document_data.notes or "")
        self.populate_vendor_dropdown()
        self.load_items_for_document() # This will also call _update_document_subtotal and update_ui_states_based_on_status at the end

    def load_items_for_document(self):
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)
        if self.document_data and self.document_data.id:
            self.items_data = self.purchase_logic.get_items_for_document(self.document_data.id)
            for item in self.items_data:
                self.items_tree.insert("", tk.END, values=(
                    item.product_description,
                    f"{item.quantity:.2f}",
                    f"{item.unit_price:.2f}" if item.unit_price is not None else "",
                    f"{item.total_price:.2f}" if item.total_price is not None else ""
                ), iid=str(item.id))
        self.on_item_tree_select(None) # Update button states based on selection
        self._update_document_subtotal()
        self.update_ui_states_based_on_status() # Ensure UI reflects current doc status and item editability

    def on_item_tree_select(self, event):
        selected = self.items_tree.selection()
        can_edit_delete = bool(selected) and self.can_edit_items()
        self.edit_item_button.config(state=tk.NORMAL if can_edit_delete else tk.DISABLED)
        self.remove_item_button.config(state=tk.NORMAL if can_edit_delete else tk.DISABLED)

    def can_edit_items(self) -> bool:
        if not self.document_data or not self.document_data.status:
            return True
        return self.document_data.status in [PurchaseDocumentStatus.RFQ, PurchaseDocumentStatus.QUOTED]

    def update_ui_states_based_on_status(self):
        can_edit_items_flag = self.can_edit_items()

        # Default states for editable fields
        vendor_combo_state = "readonly"
        notes_text_state = tk.NORMAL

        if self.document_data and self.document_data.status:
            current_status = self.document_data.status
            if current_status not in [PurchaseDocumentStatus.RFQ, PurchaseDocumentStatus.QUOTED]:
                vendor_combo_state = tk.DISABLED
            if current_status in [PurchaseDocumentStatus.PO_ISSUED, PurchaseDocumentStatus.RECEIVED, PurchaseDocumentStatus.CLOSED]:
                 notes_text_state = tk.DISABLED

        self.vendor_combobox.config(state=vendor_combo_state)
        self.notes_text.config(state=notes_text_state)

        self.add_item_button.config(state=tk.NORMAL if can_edit_items_flag else tk.DISABLED)

        selected_item = self.items_tree.selection()
        self.edit_item_button.config(state=tk.NORMAL if can_edit_items_flag and selected_item else tk.DISABLED)
        self.remove_item_button.config(state=tk.NORMAL if can_edit_items_flag and selected_item else tk.DISABLED)

    def add_item(self):
        if not self.document_data or self.document_data.id is None:
            messagebox.showwarning("No Document", "Please save the main document before adding items.", parent=self)
            return
        if not self.can_edit_items():
            messagebox.showwarning("Cannot Add Items", "Items cannot be added to a document with the current status.", parent=self)
            return
        from .purchase_document_item_popup import PurchaseDocumentItemPopup
        item_popup = PurchaseDocumentItemPopup(self, self.purchase_logic, self.product_logic, self.document_data.id)
        self.wait_window(item_popup)
        if hasattr(item_popup, 'item_saved') and item_popup.item_saved:
            self.load_items_for_document()

    def edit_item(self):
        selected_tree_item = self.items_tree.selection()
        if not selected_tree_item:
            messagebox.showwarning("No Selection", "Please select an item to edit.", parent=self)
            return
        item_id_str = selected_tree_item[0]
        try:
            item_id = int(item_id_str)
        except ValueError:
            messagebox.showerror("Error", "Invalid item selection.", parent=self)
            return
        item_to_edit_obj = self.purchase_logic.get_purchase_document_item_details(item_id)
        if not item_to_edit_obj:
            messagebox.showerror("Error", f"Could not load details for item ID: {item_id}.", parent=self)
            self.load_items_for_document()
            return
        if not self.can_edit_items():
            messagebox.showwarning("Cannot Edit", "Items cannot be edited for the current document status.", parent=self)
            return
        from .purchase_document_item_popup import PurchaseDocumentItemPopup
        item_data_dict = item_to_edit_obj.to_dict() if item_to_edit_obj else None
        edit_item_popup = PurchaseDocumentItemPopup(
            self,
            self.purchase_logic,
            self.product_logic,
            self.document_data.id,
            item_data=item_data_dict
        )
        self.wait_window(edit_item_popup)
        if hasattr(edit_item_popup, 'item_saved') and edit_item_popup.item_saved:
            self.load_items_for_document()
            new_doc_data = self.purchase_logic.get_purchase_document_details(self.document_id)
            if new_doc_data:
                self.document_data = new_doc_data
                self.status_var.set(self.document_data.status.value if self.document_data.status else "N/A")
                self.update_ui_states_based_on_status()

    def _update_document_subtotal(self):
        current_subtotal = 0.0
        for item in self.items_data:
            if item.total_price is not None:
                current_subtotal += item.total_price
        self.subtotal_var.set(f"${current_subtotal:.2f}")

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
                messagebox.showerror("Error", f"Failed to delete item: {e}", parent=self)

    def save_document(self):
        selected_vendor_name = self.vendor_combobox.get()
        if not selected_vendor_name or selected_vendor_name == NO_VENDOR_LABEL:
            messagebox.showerror("Validation Error", "Please select a vendor.", parent=self)
            return
        current_vendor_id = self.vendor_map.get(selected_vendor_name)
        if current_vendor_id is None:
            messagebox.showerror("Error", "Selected vendor is invalid.", parent=self)
            return
        notes_content = self.notes_text.get("1.0", tk.END).strip()
        try:
            if self.document_id is None:
                if current_vendor_id is None or selected_vendor_name == NO_VENDOR_LABEL:
                    messagebox.showerror("Validation Error", "A vendor must be selected to create an RFQ.", parent=self)
                    return
                new_doc = self.purchase_logic.create_rfq(
                    vendor_id=current_vendor_id,
                    notes=notes_content
                )
                if new_doc:
                    self.document_id = new_doc.id
                    self.document_data = new_doc
                    messagebox.showinfo("Success", f"RFQ {new_doc.document_number} created successfully.", parent=self)
                    self.load_document_and_items()
                    self.title(f"Edit Purchase Document - {new_doc.document_number}")
                    # self.notebook.select(self.items_tab) # No longer have notebook
                    if self.parent_controller and hasattr(self.parent_controller, 'load_documents'):
                         self.parent_controller.load_documents()
                else:
                    messagebox.showerror("Error", "Failed to create RFQ. Please check logs or input.", parent=self)
            else:
                updated = False
                if self.document_data and self.document_data.notes != notes_content:
                    self.purchase_logic.update_document_notes(self.document_id, notes_content)
                    updated = True
                if self.document_data and self.document_data.vendor_id != current_vendor_id:
                    if self.document_data.status == PurchaseDocumentStatus.RFQ:
                        messagebox.showwarning("Info", "Changing the vendor for an existing document is not supported in this version. Notes were saved if changed.", parent=self)
                    elif self.document_data.status:
                        messagebox.showwarning("Warning", f"Vendor cannot be changed for a document with status '{self.document_data.status.value}'. Notes were saved if changed.", parent=self)
                    else:
                        messagebox.showwarning("Warning", "Vendor cannot be changed for this document. Notes were saved if changed.", parent=self)
                if updated:
                    self.document_data = self.purchase_logic.get_purchase_document_details(self.document_id)
                    messagebox.showinfo("Success", f"Document {self.document_data.document_number} updated.", parent=self)
                    self.load_document_and_items()
                    if self.parent_controller and hasattr(self.parent_controller, 'load_documents'):
                        self.parent_controller.load_documents()
                else:
                    messagebox.showinfo("No Changes", "No changes were detected to save.", parent=self)
        except ValueError as ve:
            messagebox.showerror("Validation Error", str(ve), parent=self)
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}", parent=self)
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    class MockDBHandler:
        def get_all_accounts(self): return []
        def get_account_details(self, acc_id): return None
        def get_all_products(self): return []
        def get_product_details(self, prod_id): return None
        def get_product_category_name_by_id(self, cat_id): return None
        def get_all_product_categories_from_table(self): return []
        def get_all_product_units_of_measure_from_table(self): return []
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
            from shared.structs import Account, AccountType
            return [
                Account(account_id=101, name="Vendor A", account_type=AccountType.VENDOR),
                Account(account_id=102, name="Vendor B", account_type=AccountType.VENDOR),
                Account(account_id=201, name="Customer X", account_type=AccountType.CUSTOMER)
            ]
        def get_account_details(self, acc_id):
            if acc_id == 101: return Account(account_id=101, name="Vendor A", account_type=AccountType.VENDOR)
            return None

    class MockProductLogic:
        def __init__(self, db_handler): self.db = db_handler
        def get_all_products(self):
            from shared.structs import Product
            return [Product(product_id=1, name="Laptop"), Product(product_id=2, name="Mouse")]
        def get_product_details(self,pid): return None

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
        def add_item_to_document(self, doc_id, product_id, quantity, product_description_override=None, unit_price=None, total_price=None):
            from shared.structs import PurchaseDocumentItem
            print(f"Mock: Adding item (ProdID: {product_id}), qty {quantity} to doc {doc_id}")
            return PurchaseDocumentItem(item_id=123, purchase_document_id=doc_id, product_id=product_id,
                                        product_description=f"Mock Product {product_id}", quantity=quantity, unit_price=unit_price, total_price=total_price)
        def update_document_item(self, item_id, product_id, quantity, unit_price, product_description_override=None): # Mocked
             from shared.structs import PurchaseDocumentItem
             print(f"Mock: Updating item ID {item_id} (ProdID: {product_id}), qty {quantity}, price {unit_price}")
             return PurchaseDocumentItem(item_id=item_id, purchase_document_id=1, product_id=product_id,
                                        product_description=f"Mock Updated Product {product_id}", quantity=quantity, unit_price=unit_price)
        def delete_document_item(self, item_id): print(f"Mock: Deleting item {item_id}")

    root = tk.Tk()
    root.title("Popup Test")

    mock_db = MockDBHandler()
    mock_pl = MockPurchaseLogic(mock_db)
    mock_al = MockAccountLogic()
    mock_prod_l = MockProductLogic(mock_db)

    class MockParentController:
        def load_documents(self):
            print("MockParentController: load_documents() called!")

    mock_controller = MockParentController()

    def open_new():
        popup = PurchaseDocumentPopup(root, mock_pl, mock_al, mock_prod_l, parent_controller=mock_controller)
        root.wait_window(popup)

    def open_edit():
        # This needs to be adjusted for the current save_document logic in the popup
        # For now, we'll assume a document with ID 1 exists for editing in this mock scenario
        # In a real test, you'd create one first if needed, or pass a valid ID.
        # For simplicity, let's assume doc_id=1 is our target for edit test.
        # Or use the create_rfq from mock_pl for a more realistic test.
        doc = mock_pl.create_rfq(vendor_id=101, notes="Initial for edit")
        if doc:
            popup = PurchaseDocumentPopup(root, mock_pl, mock_al, mock_prod_l, document_id=doc.id, parent_controller=mock_controller)
            root.wait_window(popup)
        else:
            print("Failed to create mock document for editing.")

    ttk.Button(root, text="New Document", command=open_new).pack(pady=10)
    ttk.Button(root, text="Edit Document (ID 1)", command=open_edit).pack(pady=10)

    root.mainloop()
