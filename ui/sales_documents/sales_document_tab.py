import tkinter as tk
from tkinter import messagebox, ttk
import datetime
# Assuming SalesDocumentPopup will be created for adding/editing
from ui.sales_documents.sales_document_popup import SalesDocumentPopup
from shared.structs import SalesDocument # Assuming SalesDocument struct is available

class SalesDocumentTab:
    def __init__(self, master, sales_logic, customer_logic, product_logic): # Added product_logic
        self.frame = tk.Frame(master)
        self.sales_logic = sales_logic
        self.customer_logic = customer_logic
        self.product_logic = product_logic # Store product_logic
        self.selected_document_id = None

        self.setup_ui()
        self.load_documents()

        # Bind FocusIn to reload data when tab is selected
        self.frame.bind("<FocusIn>", self.load_documents)

    def setup_ui(self):
        tk.Label(self.frame, text="Sales Quotes & Orders", font=("Arial", 16)).grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="w")

        button_frame = tk.Frame(self.frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=5, sticky="w", padx=10)

        button_width = 22

        self.add_button = tk.Button(
            button_frame, text="New Sales Document",
            command=self.add_new_document, width=button_width)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.edit_button = tk.Button(
            button_frame, text="View/Edit Document",
            command=self.edit_selected_document, width=button_width)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = tk.Button(
            button_frame, text="Delete Document",
            command=self.delete_selected_document, width=button_width)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        # Treeview for displaying sales documents
        columns = ("doc_id", "customer_name", "doc_date", "status", "total_amount")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings")

        self.tree.heading("doc_id", text="Doc ID", command=lambda: self.sort_column("doc_id", False))
        self.tree.heading("customer_name", text="Customer", command=lambda: self.sort_column("customer_name", False))
        self.tree.heading("doc_date", text="Date", command=lambda: self.sort_column("doc_date", False))
        self.tree.heading("status", text="Status", command=lambda: self.sort_column("status", False))
        self.tree.heading("total_amount", text="Total", command=lambda: self.sort_column("total_amount", False))

        self.tree.column("doc_id", width=80, anchor=tk.W)
        self.tree.column("customer_name", width=200, anchor=tk.W)
        self.tree.column("doc_date", width=100, anchor=tk.CENTER)
        self.tree.column("status", width=100, anchor=tk.W)
        self.tree.column("total_amount", width=100, anchor=tk.E)

        # Store actual document ID in a hidden first column if preferred, or use tree.item(iid, "values")[0]
        # For simplicity, we'll use the iid of the tree item as the document_id if it's directly set.

        self.tree.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_columnconfigure(0, weight=1) # Allow tree to expand

        self.tree.bind("<<TreeviewSelect>>", self.on_document_select)
        self.tree.bind("<Double-1>", self.edit_selected_document) # Double click to edit

    def sort_column(self, col, reverse):
        try:
            data_to_sort = []
            for item_id in self.tree.get_children(""):
                value = self.tree.set(item_id, col)
                # Attempt to convert to a more sortable type if possible
                if col == "doc_id" or col == "total_amount":
                    try:
                        value = float(value.replace("$", "").replace(",", "")) # Handle currency
                    except ValueError:
                        pass # Keep as string if not convertible
                elif col == "doc_date":
                    try:
                        value = datetime.datetime.strptime(value, "%Y-%m-%d").date()
                    except ValueError:
                        pass # Keep as string
                data_to_sort.append((value, item_id))

            # Define a sort key that handles mixed types gracefully
            def sort_key(item):
                val = item[0]
                if isinstance(val, (int, float, datetime.date)):
                    return (0, val) # Type 0 for numbers/dates
                return (1, str(val).lower()) # Type 1 for strings

            data_to_sort.sort(key=sort_key, reverse=reverse)

            for index, (val, item_id) in enumerate(data_to_sort):
                self.tree.move(item_id, "", index)

            self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))
        except Exception as e:
            print(f"Error sorting column {col}: {e}")
            # messagebox.showerror("Sort Error", f"Could not sort column {col}.")


    def on_document_select(self, event=None):
        selected_items = self.tree.selection()
        if selected_items:
            # Assuming the IID of the tree item is the document_id
            self.selected_document_id = int(selected_items[0])
        else:
            self.selected_document_id = None

    def load_documents(self, event=None):
        self.tree.delete(*self.tree.get_children())
        self.selected_document_id = None
        try:
            documents_structs = self.sales_logic.get_all_sales_documents()
            for doc_struct in documents_structs:
                # The sales_logic.get_all_sales_documents might return dicts from DB or SalesDocument structs
                # The DB method get_all_sales_documents returns dicts with 'customer_name'
                # Let's assume sales_logic.get_all_sales_documents passes this through or reconstructs it.
                # For now, we'll expect a dictionary-like object or a struct with necessary fields.

                doc_id = doc_struct.document_id
                # Fetch customer name using customer_logic if not directly available in doc_struct
                # This depends on what get_all_sales_documents from sales_logic returns.
                # The DB layer's get_all_sales_documents joins with accounts for customer_name.
                # So, if sales_logic passes that through, it's available.

                # Assuming doc_struct is a SalesDocument, and we need to get customer_name
                # This is an N+1 query problem if sales_logic.get_all_sales_documents doesn't provide it.
                # The DB layer `get_all_sales_documents` already joins and provides `customer_name`.
                # So, `doc_struct` (if it's the dict from DB) will have `customer_name`.
                # If `sales_logic` converts it to `SalesDocument` struct, it should ideally carry `customer_name`.

                # Let's adjust based on the sales_logic `get_all_sales_documents` which returns list[SalesDocument]
                # and SalesDocument struct does not have customer_name.
                # The DB method `get_all_sales_documents` in `database.py` *does* fetch `customer_name`.
                # The `SalesLogic.get_all_sales_documents` currently creates SalesDocument structs *without* customer_name.
                # This needs reconciliation. For now, I'll try to fetch it. This is inefficient.
                # OPTION 1: Modify SalesLogic to include customer_name in its returned objects. (Preferred)
                # OPTION 2: Fetch here (N+1 problem). (Less preferred)

                # Assuming for now that SalesLogic.get_all_sales_documents was enhanced
                # or we are working with the direct dict output from the DB layer for the list view.
                # Let's assume sales_logic.get_all_sales_documents returns a list of dicts with 'customer_name'.
                # This means the SalesLogic.get_all_sales_documents should be:
                # def get_all_sales_documents(self, customer_id: int = None) -> list[dict]:
                # return self.db.get_all_sales_documents(customer_id=customer_id)

                # If sales_logic.get_all_sales_documents() returns SalesDocument instances:
                customer_name = "N/A"
                if doc_struct.customer_id and self.customer_logic:
                    customer_account = self.customer_logic.get_account_details(doc_struct.customer_id) # AccountLogic needed
                    if customer_account:
                        customer_name = customer_account.name # Assuming Account struct has name

                # If sales_logic.get_all_sales_documents() returns dicts from DB that include 'customer_name':
                # customer_name = doc_struct.get('customer_name', "N/A")


                doc_date_str = doc_struct.document_date.isoformat() if doc_struct.document_date else "N/A"
                total_str = f"${doc_struct.total_amount:,.2f}" if doc_struct.total_amount is not None else "N/A"

                self.tree.insert("", "end", iid=str(doc_id), values=(
                    doc_id,
                    customer_name, # This needs to be resolved based on SalesLogic output
                    doc_date_str,
                    doc_struct.status,
                    total_str
                ))
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load sales documents: {e}")
            print(f"Error in load_documents: {e}") # For console debugging

    def add_new_document(self):
        # Pass self.frame.master (the main window or notebook) as parent for the popup
        # Pass self (the tab instance) as the calling_tab to allow refresh
        popup = SalesDocumentPopup(self.frame.master, self, self.sales_logic, self.customer_logic, self.product_logic, document_id=None)
        self.frame.master.wait_window(popup) # Wait for the popup to close
        self.load_documents() # Refresh list

    def edit_selected_document(self, event=None): # event=None for double-click
        if not self.selected_document_id:
            messagebox.showwarning("No Selection", "Please select a document to view/edit.")
            return
        popup = SalesDocumentPopup(self.frame.master, self, self.sales_logic, self.customer_logic, self.product_logic, document_id=self.selected_document_id)
        self.frame.master.wait_window(popup)
        self.load_documents()

    def delete_selected_document(self):
        if not self.selected_document_id:
            messagebox.showwarning("No Selection", "Please select a document to delete.")
            return

        doc_id_to_delete = self.selected_document_id
        # Optionally, retrieve document details to show in confirmation
        # doc_details = self.sales_logic.get_sales_document_details(doc_id_to_delete)
        # customer_name = doc_details.customer_name if doc_details else "N/A"
        # confirm_msg = f"Are you sure you want to delete Sales Document ID: {doc_id_to_delete} for {customer_name}?"

        confirm_msg = f"Are you sure you want to delete Sales Document ID: {doc_id_to_delete}?"

        if messagebox.askyesno("Confirm Delete", confirm_msg):
            try:
                success = self.sales_logic.delete_sales_document(doc_id_to_delete)
                if success:
                    messagebox.showinfo("Success", f"Sales Document ID: {doc_id_to_delete} deleted successfully.")
                    self.load_documents()
                else:
                    messagebox.showerror("Error", f"Failed to delete document ID: {doc_id_to_delete}.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while deleting: {e}")
        self.selected_document_id = None # Clear selection

    def refresh_documents_list(self):
        self.load_documents()

# Example of how to integrate (for testing this tab standalone)
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Sales Document Tab Test")
    root.geometry("800x600")

    # Mock SalesLogic
    class MockSalesLogic:
        def get_all_sales_documents(self, customer_id=None):
            print("MockSalesLogic: get_all_sales_documents called")
            # Return list of SalesDocument like objects or dicts
            docs = [
                SalesDocument(document_id=1, customer_id=1, document_date=datetime.date(2023, 1, 15), status="Draft", total_amount=1500.75),
                SalesDocument(document_id=2, customer_id=2, document_date=datetime.date(2023, 2, 20), status="Sent", total_amount=899.00),
                SalesDocument(document_id=3, customer_id=1, document_date=datetime.date(2023, 3, 10), status="Accepted", total_amount=2250.50)
            ]
            if customer_id:
                return [d for d in docs if d.customer_id == customer_id]
            return docs

        def delete_sales_document(self, doc_id):
            print(f"MockSalesLogic: delete_sales_document for ID {doc_id}")
            return True

        def get_sales_document_details(self, doc_id): # Needed by popup
            print(f"MockSalesLogic: get_sales_document_details for ID {doc_id}")
            if doc_id == 1:
                doc = SalesDocument(document_id=1, customer_id=1, document_date=datetime.date(2023,1,15), status="Draft", total_amount=1500.75)
                doc.items = [] # Mock items
                return doc
            return None

        # Add other methods like add_sales_document, update_sales_document as needed by popup
        def create_sales_document(self, customer_id, document_date, status, items_data):
            print("MockSalesLogic: create_sales_document called")
            return 123 # mock new document ID

        def update_sales_document_items(self, document_id, items_data):
            print(f"MockSalesLogic: update_sales_document_items for {document_id}")
            return True

    # Mock CustomerLogic (AccountLogic)
    class MockCustomerLogic:
        def get_account_details(self, account_id):
            print(f"MockCustomerLogic: get_account_details for Account ID {account_id}")
            if account_id == 1:
                # Mock an Account-like object/struct
                class MockAccount: pass
                acc = MockAccount()
                acc.account_id = 1
                acc.name = "Customer Alpha"
                return acc
            if account_id == 2:
                class MockAccount: pass
                acc = MockAccount()
                acc.account_id = 2
                acc.name = "Customer Beta"
                return acc
            return None

        def get_all_accounts(self): # For customer dropdown in popup
            print("MockCustomerLogic: get_all_accounts called")
            class MockAccount:
                def __init__(self, id, name):
                    self.account_id = id
                    self.name = name
            return [MockAccount(1, "Customer Alpha"), MockAccount(2, "Customer Beta")]

    mock_sales_logic = MockSalesLogic()
    mock_customer_logic = MockCustomerLogic()

    # The SalesDocumentPopup would also need a mock product_logic for product selection
    # For now, we are just testing the tab.

    app_tab = SalesDocumentTab(root, mock_sales_logic, mock_customer_logic)
    app_tab.frame.pack(expand=True, fill=tk.BOTH)

    root.mainloop()
