import tkinter as tk
from tkinter import ttk, messagebox
import datetime # Import datetime
# from .purchase_document_popup import PurchaseDocumentPopup # Will be created
# from core.purchase_logic import PurchaseLogic # Will be passed in
# from shared.structs import PurchaseDocument # For type hinting
# from core.logic.product_management import ProductLogic # For type hinting

class PurchaseDocumentTab:
    def __init__(self, master, purchase_logic, account_logic, product_logic): # Added product_logic
        self.frame = ttk.Frame(master)
        self.purchase_logic = purchase_logic
        self.account_logic = account_logic
        self.product_logic = product_logic # Store product_logic
        self.selected_document_id = None

        self._setup_ui()
        self.load_documents()

        # Bind FocusIn to reload data when tab is selected
        self.frame.bind("<FocusIn>", lambda event: self.load_documents())

    def _setup_ui(self):
        # Button frame
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=10, padx=10, fill=tk.X)

        self.add_button = ttk.Button(button_frame, text="New RFQ/PO", command=self.open_new_document_popup)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.edit_button = ttk.Button(button_frame, text="Edit Document", command=self.open_edit_document_popup, state=tk.DISABLED)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(button_frame, text="Delete Document", command=self.delete_selected_document, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        # Treeview for displaying documents
        columns = ("doc_number", "vendor_name", "created_date", "status", "notes")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("doc_number", text="Document #")
        self.tree.heading("vendor_name", text="Vendor")
        self.tree.heading("created_date", text="Created Date")
        self.tree.heading("status", text="Status")
        self.tree.heading("notes", text="Notes")

        self.tree.column("doc_number", width=150, anchor=tk.W)
        self.tree.column("vendor_name", width=200, anchor=tk.W)
        self.tree.column("created_date", width=150, anchor=tk.W)
        self.tree.column("status", width=100, anchor=tk.CENTER)
        self.tree.column("notes", width=300, anchor=tk.W)

        self.tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_document_double_click) # Bind double-click

        # TODO: Add scrollbar for treeview

    def on_document_double_click(self, event):
        """Handles double-click event on the document treeview."""
        item_iid = self.tree.identify_row(event.y) # Get item directly from click position
        if not item_iid:
            return # Click was not on an item

        # Ensure the selection is updated to this item before proceeding
        # This helps if the double-click happened fast and on_tree_select might not have fully processed
        # for the *exact* item if the selection was on a different item before the double click.
        current_selection = self.tree.selection()
        if not current_selection or current_selection[0] != item_iid:
            self.tree.selection_set(item_iid)
            # Forcing update of selected_document_id, normally handled by on_tree_select
            try:
                self.selected_document_id = int(item_iid)
            except ValueError:
                self.selected_document_id = None # Should not happen if iid is from tree

        if self.selected_document_id: # Check if a valid document is now considered selected
            self.open_edit_document_popup()
        # No need to check edit_button state here, open_edit_document_popup has its own guard.

    def load_documents(self):
        # Clear existing items
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Fetch all non-closed documents (example filter)
        # documents = self.purchase_logic.get_all_documents_by_criteria(status_not_closed=True) # Needs method adjustment
        documents = self.purchase_logic.get_all_documents_by_criteria() # Get all for now

        for doc in documents:
            vendor_name = "Unknown Vendor"
            if doc.vendor_id:
                vendor_account = self.account_logic.get_account_details(doc.vendor_id)
                if vendor_account:
                    vendor_name = vendor_account.name

            # Format created_date if it's an ISO string
            formatted_date = doc.created_date
            try:
                dt_obj = datetime.datetime.fromisoformat(doc.created_date)
                formatted_date = dt_obj.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pass # Keep original if not parsable

            self.tree.insert("", tk.END, values=(
                doc.document_number,
                vendor_name,
                formatted_date,
                doc.status.value if doc.status else "N/A",
                doc.notes or ""
            ), iid=str(doc.id)) # Use doc.id as item identifier (iid)

        self.on_tree_select(None) # Update button states

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            # The iid was set as str(doc.id) during insert.
            # selected_items[0] is the iid of the selected item.
            try:
                self.selected_document_id = int(selected_items[0])
                self.edit_button.config(state=tk.NORMAL)
                self.delete_button.config(state=tk.NORMAL)
            except ValueError:
                # This might happen if iid is not a valid int string, though it should be.
                print(f"Error: Could not parse document ID from tree selection: {selected_items[0]}")
                self.selected_document_id = None
                self.edit_button.config(state=tk.DISABLED)
                self.delete_button.config(state=tk.DISABLED)
        else:
            self.selected_document_id = None
            self.edit_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)

    def open_new_document_popup(self):
        from .purchase_document_popup import PurchaseDocumentPopup # Local import
        # Pass the tab instance (self) as the 'parent_controller'
        popup = PurchaseDocumentPopup(
            master=self.frame.winfo_toplevel(),
            purchase_logic=self.purchase_logic,
            account_logic=self.account_logic,
            product_logic=self.product_logic, # Pass product_logic
            document_id=None,
            parent_controller=self
        )
        self.frame.wait_window(popup)
        # self.load_documents() is now called by the popup via parent_controller


    def open_edit_document_popup(self):
        if not self.selected_document_id:
            messagebox.showwarning("No Selection", "Please select a document to edit.")
            return

        from .purchase_document_popup import PurchaseDocumentPopup # Local import for safety

        popup = PurchaseDocumentPopup(
            master=self.frame.winfo_toplevel(), # Use toplevel for proper window behavior
            purchase_logic=self.purchase_logic,
            account_logic=self.account_logic,
            product_logic=self.product_logic,
            document_id=self.selected_document_id,
            parent_controller=self # Pass the tab instance for callbacks
        )
        self.frame.wait_window(popup)
        # self.load_documents() # Refresh is handled by the popup via parent_controller callback


    def delete_selected_document(self):
        doc_id_to_delete = self.selected_document_id  # Store the ID locally

        if not doc_id_to_delete:
            messagebox.showwarning("No Selection", "Please select a document to delete.")
            return

        # Use the local variable for fetching details
        doc_to_delete = self.purchase_logic.get_purchase_document_details(doc_id_to_delete)
        if not doc_to_delete:
             messagebox.showerror("Error", "Document not found.")
             self.load_documents() # This might clear selection, but doc_id_to_delete is preserved
             return

        confirm = messagebox.askyesno("Confirm Delete",
                                      f"Are you sure you want to delete document {doc_to_delete.document_number}?")
        if confirm:
            try:
                # Use the local variable for the deletion call
                self.purchase_logic.delete_purchase_document(doc_id_to_delete)
                messagebox.showinfo("Success", f"Document {doc_to_delete.document_number} deleted successfully.")
                self.load_documents()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete document: {e}")

if __name__ == '__main__':
    # Example usage (for testing this tab standalone)
    # This requires mock objects for purchase_logic and account_logic
    class MockLogic:
        def get_all_documents_by_criteria(self, **kwargs): return []
        def get_account_details(self, acc_id): return None
        def delete_purchase_document(self, doc_id): pass
        def get_purchase_document_details(self, doc_id): return None

    root = tk.Tk()
    root.title("Purchase Document Tab Test")
    mock_purchase_logic = MockLogic()
    mock_account_logic = MockLogic() # AccountLogic might have different methods

    # Need to mock Account object for vendor_name if testing load_documents thoroughly
    # For now, this just shows the tab structure.

    tab = PurchaseDocumentTab(root, mock_purchase_logic, mock_account_logic)
    tab.frame.pack(expand=True, fill=tk.BOTH)
    root.geometry("800x600")
    root.mainloop()
