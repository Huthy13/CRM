import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from shared.structs import SalesDocumentType, SalesDocumentStatus, AccountType # Import for sales

class SalesDocumentTab:
    def __init__(self, master, sales_logic, account_logic, product_logic): # Renamed purchase_logic to sales_logic
        self.frame = ttk.Frame(master)
        self.sales_logic = sales_logic # Use sales_logic
        self.account_logic = account_logic
        self.product_logic = product_logic
        self.selected_document_id = None

        self._setup_ui()
        self.load_documents()

        self.frame.bind("<FocusIn>", lambda event: self.load_documents())

    def _setup_ui(self):
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=10, padx=10, fill=tk.X)

        # Updated button text for sales context
        self.add_button = ttk.Button(button_frame, text="New Quote/Invoice", command=self.open_new_document_popup)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.edit_button = ttk.Button(button_frame, text="View/Edit Document", command=self.open_edit_document_popup, state=tk.DISABLED)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(button_frame, text="Delete Document", command=self.delete_selected_document, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        # Adapted columns for sales documents
        columns = ("doc_number", "doc_type", "customer_name", "created_date", "status", "total_amount", "notes")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("doc_number", text="Document #")
        self.tree.heading("doc_type", text="Type")
        self.tree.heading("customer_name", text="Customer") # Changed from Vendor
        self.tree.heading("created_date", text="Created Date")
        self.tree.heading("status", text="Status")
        self.tree.heading("total_amount", text="Total Amount")
        self.tree.heading("notes", text="Notes")

        self.tree.column("doc_number", width=150, anchor=tk.W)
        self.tree.column("doc_type", width=80, anchor=tk.W)
        self.tree.column("customer_name", width=180, anchor=tk.W) # Changed from Vendor
        self.tree.column("created_date", width=120, anchor=tk.W)
        self.tree.column("status", width=120, anchor=tk.CENTER)
        self.tree.column("total_amount", width=100, anchor=tk.E)
        self.tree.column("notes", width=250, anchor=tk.W)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(expand=True, fill=tk.BOTH, padx=(10,0), pady=10) # Adjust padx to accommodate scrollbar

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_document_double_click)

    def on_document_double_click(self, event):
        item_iid = self.tree.identify_row(event.y)
        if not item_iid:
            return
        current_selection = self.tree.selection()
        if not current_selection or current_selection[0] != item_iid:
            self.tree.selection_set(item_iid)
            try:
                self.selected_document_id = int(item_iid)
            except ValueError:
                self.selected_document_id = None
        if self.selected_document_id:
            self.open_edit_document_popup()

    def load_documents(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Use sales_logic to get sales documents
        documents = self.sales_logic.get_all_sales_documents_by_criteria()

        for doc in documents:
            customer_name = "Unknown Customer"
            if doc.customer_id: # Changed from vendor_id
                customer_account = self.account_logic.get_account_details(doc.customer_id)
                if customer_account:
                    customer_name = customer_account.get('name', "Error: Name not found")


            formatted_date = doc.created_date
            try:
                dt_obj = datetime.datetime.fromisoformat(doc.created_date)
                formatted_date = dt_obj.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pass

            doc_type_display = doc.document_type.value if doc.document_type else "N/A"
            status_display = doc.status.value if doc.status else "N/A"
            total_amount_display = f"${doc.total_amount:.2f}" if doc.total_amount is not None else "$0.00"

            self.tree.insert("", tk.END, values=(
                doc.document_number,
                doc_type_display,
                customer_name,
                formatted_date,
                status_display,
                total_amount_display,
                doc.notes or ""
            ), iid=str(doc.id))

        self.on_tree_select(None)

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            try:
                self.selected_document_id = int(selected_items[0])
                self.edit_button.config(state=tk.NORMAL)
                self.delete_button.config(state=tk.NORMAL)
            except ValueError:
                self.selected_document_id = None
                self.edit_button.config(state=tk.DISABLED)
                self.delete_button.config(state=tk.DISABLED)
        else:
            self.selected_document_id = None
            self.edit_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)

    def open_new_document_popup(self):
        # Import SalesDocumentPopup locally
        from .sales_document_popup import SalesDocumentPopup
        popup = SalesDocumentPopup(
            master=self.frame.winfo_toplevel(),
            sales_logic=self.sales_logic, # Pass sales_logic
            account_logic=self.account_logic,
            product_logic=self.product_logic,
            document_id=None,
            parent_controller=self
        )
        self.frame.wait_window(popup)
        # self.load_documents() # Reload handled by popup via parent_controller

    def open_edit_document_popup(self):
        if not self.selected_document_id:
            messagebox.showwarning("No Selection", "Please select a document to view/edit.")
            return
        # Import SalesDocumentPopup locally
        from .sales_document_popup import SalesDocumentPopup
        popup = SalesDocumentPopup(
            master=self.frame.winfo_toplevel(),
            sales_logic=self.sales_logic, # Pass sales_logic
            account_logic=self.account_logic,
            product_logic=self.product_logic,
            document_id=self.selected_document_id,
            parent_controller=self
        )
        self.frame.wait_window(popup)
        # self.load_documents() # Reload handled by popup via parent_controller

    def delete_selected_document(self):
        doc_id_to_delete = self.selected_document_id
        if not doc_id_to_delete:
            messagebox.showwarning("No Selection", "Please select a document to delete.")
            return

        doc_to_delete = self.sales_logic.get_sales_document_details(doc_id_to_delete) # Use sales_logic
        if not doc_to_delete:
             messagebox.showerror("Error", "Document not found.")
             self.load_documents()
             return

        confirm = messagebox.askyesno("Confirm Delete",
                                      f"Are you sure you want to delete {doc_to_delete.document_type.value} {doc_to_delete.document_number}?")
        if confirm:
            try:
                self.sales_logic.delete_sales_document(doc_id_to_delete) # Use sales_logic
                messagebox.showinfo("Success", f"{doc_to_delete.document_type.value} {doc_to_delete.document_number} deleted.")
                self.load_documents()
            except ValueError as ve: # Catch specific ValueErrors from logic (e.g., cannot delete paid invoice)
                messagebox.showerror("Deletion Error", str(ve))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete document: {e}")
                import traceback
                traceback.print_exc()

if __name__ == '__main__':
    # Mock classes for standalone testing
    class MockAccountLogic:
        def get_account_details(self, acc_id):
            if acc_id == 1: return {'name': 'Customer Alpha', 'account_type': AccountType.CUSTOMER.value}
            return None
        def get_all_accounts(self): # Needed by popup
            from shared.structs import Account
            return [Account(account_id=1, name="Customer Alpha", account_type=AccountType.CUSTOMER)]


    class MockProductLogic: # Needed by popup
        def get_all_products(self): return []
        def get_product_details(self, pid): return None

    class MockSalesLogic:
        def get_all_sales_documents_by_criteria(self, **kwargs):
            from shared.structs import SalesDocument, SalesDocumentType, SalesDocumentStatus
            return [
                SalesDocument(doc_id=1, document_number="QUO-20230101-0001", customer_id=1, document_type=SalesDocumentType.QUOTE, created_date=datetime.datetime.now().isoformat(), status=SalesDocumentStatus.QUOTE_DRAFT, total_amount=100.0, notes="Test Quote 1"),
                SalesDocument(doc_id=2, document_number="INV-20230102-0001", customer_id=1, document_type=SalesDocumentType.INVOICE, created_date=datetime.datetime.now().isoformat(), status=SalesDocumentStatus.INVOICE_SENT, total_amount=250.50, notes="Test Invoice 1")
            ]
        def get_sales_document_details(self, doc_id):
             from shared.structs import SalesDocument, SalesDocumentType, SalesDocumentStatus
             if doc_id == 1:
                return SalesDocument(doc_id=1, document_number="QUO-20230101-0001", customer_id=1, document_type=SalesDocumentType.QUOTE, created_date=datetime.datetime.now().isoformat(), status=SalesDocumentStatus.QUOTE_DRAFT, total_amount=100.0)
             return None
        def delete_sales_document(self, doc_id): print(f"Mock: Deleting sales doc {doc_id}")

    root = tk.Tk()
    root.title("Sales Document Tab Test")

    mock_sales_logic = MockSalesLogic()
    mock_account_logic = MockAccountLogic()
    mock_product_logic = MockProductLogic()

    # Need to ensure the popup can be imported for the test to run the open_new/edit methods
    # This requires sales_document_popup.py to exist or these test buttons to be disabled/removed
    # For now, we assume it will exist for full testing.
    # To make this testable standalone without the popup yet, one might need to mock the popup import.

    tab = SalesDocumentTab(root, mock_sales_logic, mock_account_logic, mock_product_logic)
    tab.frame.pack(expand=True, fill=tk.BOTH)
    root.geometry("900x600") # Adjusted width for more columns
    root.mainloop()
