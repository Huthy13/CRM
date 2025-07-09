import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from shared.structs import SalesDocument, SalesDocumentItem, Account, Product
from ui.sales_documents.sales_document_item_popup import SalesDocumentItemPopup

class SalesDocumentPopup(tk.Toplevel):
    def __init__(self, master, calling_tab, sales_logic, customer_logic, product_logic, document_id=None):
        super().__init__(master)
        self.calling_tab = calling_tab
        self.sales_logic = sales_logic
        self.customer_logic = customer_logic
        self.product_logic = product_logic
        self.document_id = document_id

        self.title(f"{'Edit' if document_id else 'New'} Sales Document")
        self.geometry("900x700")

        self.document_data = None
        self.line_items_data = []
        self.selected_line_item_iid = None
        self.available_products_for_item_popup = None

        self._setup_ui()

        if self.document_id:
            self._load_document_details()
        else:
            self.doc_date_entry.insert(0, datetime.date.today().isoformat())
            if self.status_combobox['values']:
                self.status_combobox.current(0)
            self._update_totals_display()

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        header_frame = ttk.LabelFrame(main_frame, text="Document Header", padding="10")
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.columnconfigure(1, weight=1)

        ttk.Label(header_frame, text="Customer:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.customer_combobox = ttk.Combobox(header_frame, state="readonly", width=40)
        self.customer_combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self._populate_customer_combobox()

        ttk.Label(header_frame, text="Doc Date:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.doc_date_entry = ttk.Entry(header_frame, width=40)
        self.doc_date_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(header_frame, text="Status:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.status_combobox = ttk.Combobox(header_frame, state="readonly", values=["Draft", "Sent", "Accepted", "Closed", "Cancelled"], width=38)
        self.status_combobox.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        items_frame = ttk.LabelFrame(main_frame, text="Line Items", padding="10")
        items_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.rowconfigure(1, weight=1)
        items_frame.columnconfigure(0, weight=1)

        item_columns = ("item_id_display", "product_name", "quantity", "unit_price", "line_total")
        self.items_tree = ttk.Treeview(items_frame, columns=item_columns, show="headings", selectmode="browse")

        self.items_tree.heading("item_id_display", text="Item ID")
        self.items_tree.heading("product_name", text="Product")
        self.items_tree.heading("quantity", text="Qty")
        self.items_tree.heading("unit_price", text="Unit Price")
        self.items_tree.heading("line_total", text="Total")

        self.items_tree.column("item_id_display", width=60, anchor=tk.W)
        self.items_tree.column("product_name", width=300)
        self.items_tree.column("quantity", width=80, anchor=tk.E)
        self.items_tree.column("unit_price", width=100, anchor=tk.E)
        self.items_tree.column("line_total", width=120, anchor=tk.E)

        self.items_tree.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        items_frame.rowconfigure(0, weight=1)
        items_frame.columnconfigure(0, weight=1)
        self.items_tree.bind("<<TreeviewSelect>>", self._on_line_item_select)
        self.items_tree.bind("<Double-1>", lambda e: self._edit_item_dialog())

        item_button_frame = ttk.Frame(items_frame)
        item_button_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        self.add_item_button = ttk.Button(item_button_frame, text="Add Item", command=self._add_item_dialog)
        self.add_item_button.pack(side=tk.LEFT, padx=5)
        self.edit_item_button = ttk.Button(item_button_frame, text="Edit Item", command=self._edit_item_dialog)
        self.edit_item_button.pack(side=tk.LEFT, padx=5)
        self.remove_item_button = ttk.Button(item_button_frame, text="Remove Item", command=self._remove_item)
        self.remove_item_button.pack(side=tk.LEFT, padx=5)

        totals_frame = ttk.Frame(main_frame, padding="5")
        totals_frame.grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Label(totals_frame, text="Document Total:").pack(side=tk.LEFT, padx=5)
        self.total_amount_label = ttk.Label(totals_frame, text="$0.00", font=("Arial", 12, "bold"))
        self.total_amount_label.pack(side=tk.LEFT, padx=5)

        action_button_frame = ttk.Frame(main_frame, padding="10")
        action_button_frame.grid(row=3, column=0, sticky="e", padx=5, pady=10)

        self.save_button = ttk.Button(action_button_frame, text="Save Document", command=self._save_document)
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ttk.Button(action_button_frame, text="Cancel", command=self.destroy)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.customers_map = {}
        self._load_available_products_for_item_popup()

    def _load_available_products_for_item_popup(self):
        try:
            self.available_products_for_item_popup = self.product_logic.get_all_products()
        except Exception as e:
            print(f"Error loading products for item popup: {e}")
            self.available_products_for_item_popup = []

    def _populate_customer_combobox(self):
        # TODO: Update this to filter for accounts specifically tagged as "customer"
        #       once the account tagging feature is implemented and available in customer_logic.
        #       For example, by calling something like:
        #       accounts = self.customer_logic.get_accounts_by_tag("customer")
        #       or if get_all_accounts can be filtered:
        #       accounts = self.customer_logic.get_all_accounts(tag="customer")
        try:
            accounts = self.customer_logic.get_all_accounts() # This currently returns list of tuples (id, name, ...)
            if accounts:
                # Assuming tuple structure is (account_id, account_name, ...)
                self.customers_map = {acc[1]: acc[0] for acc in accounts} # acc[1] is name, acc[0] is id
                self.customer_combobox['values'] = sorted(list(self.customers_map.keys()))
            else:
                self.customer_combobox['values'] = []
                self.customers_map = {} # Ensure map is also cleared
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load customers: {e}", parent=self)
            self.customer_combobox['values'] = []
            self.customers_map = {} # Ensure map is cleared on error too

    def _on_line_item_select(self, event=None):
        selected = self.items_tree.selection()
        if selected:
            self.selected_line_item_iid = selected[0]
        else:
            self.selected_line_item_iid = None

    def _load_document_details(self):
        self.document_data = self.sales_logic.get_sales_document_details(self.document_id)
        if not self.document_data:
            messagebox.showerror("Error", f"Could not load document ID: {self.document_id}", parent=self)
            self.destroy()
            return

        customer_id = self.document_data.customer_id
        customer_name_to_select = ""
        for name, c_id in self.customers_map.items():
            if c_id == customer_id:
                customer_name_to_select = name
                break
        if customer_name_to_select:
            self.customer_combobox.set(customer_name_to_select)
        else:
            acc_details = self.customer_logic.get_account_details(customer_id)
            if acc_details:
                 self.customer_combobox.set(acc_details.name)
            else:
                self.customer_combobox.set(f"ID: {customer_id}" if customer_id else "Unknown Customer")

        self.doc_date_entry.delete(0, tk.END)
        self.doc_date_entry.insert(0, self.document_data.document_date.isoformat() if self.document_data.document_date else "")

        if self.document_data.status in self.status_combobox['values']:
            self.status_combobox.set(self.document_data.status)
        else:
            current_statuses = list(self.status_combobox['values'])
            if self.document_data.status not in current_statuses:
                 current_statuses.append(self.document_data.status)
            self.status_combobox['values'] = current_statuses
            self.status_combobox.set(self.document_data.status)

        self.line_items_data = []
        if hasattr(self.document_data, 'items'):
            for item_struct in self.document_data.items:
                copied_item = SalesDocumentItem(
                    item_id=item_struct.item_id,
                    document_id=item_struct.document_id,
                    product_id=item_struct.product_id,
                    quantity=item_struct.quantity,
                    unit_price=item_struct.unit_price,
                    line_total=item_struct.line_total
                )
                if not hasattr(copied_item, 'product_name') or not copied_item.product_name:
                    prod_details = self.product_logic.get_product_details(copied_item.product_id)
                    copied_item.product_name = prod_details.name if prod_details else "Unknown Product"
                self.line_items_data.append(copied_item)

        self._refresh_line_items_tree()
        self._update_totals_display()

    def _refresh_line_items_tree(self):
        self.items_tree.delete(*self.items_tree.get_children())
        self.selected_line_item_iid = None
        for idx, item_struct in enumerate(self.line_items_data):
            product_name = getattr(item_struct, 'product_name', "Loading...")
            if product_name == "Loading...":
                prod_details = self.product_logic.get_product_details(item_struct.product_id)
                product_name = prod_details.name if prod_details else "Unknown Product"
                item_struct.product_name = product_name

            iid = str(idx)
            self.items_tree.insert("", "end", iid=iid, values=(
                item_struct.item_id if item_struct.item_id else "New",
                product_name,
                item_struct.quantity,
                f"${item_struct.unit_price:,.2f}",
                f"${item_struct.line_total:,.2f}"
            ))

    def _update_totals_display(self):
        current_total = sum(item.line_total for item in self.line_items_data if hasattr(item, 'line_total') and item.line_total is not None)
        self.total_amount_label.config(text=f"${current_total:,.2f}")

    def _add_item_dialog(self):
        item_popup = SalesDocumentItemPopup(
            self,
            self.product_logic,
            available_products=self.available_products_for_item_popup
        )
        result = item_popup.show()

        if result:
            new_item = SalesDocumentItem(
                item_id=None,
                document_id=self.document_id,
                product_id=result['product_id'],
                quantity=result['quantity'],
                unit_price=result['unit_price'],
                line_total=result['line_total']
            )
            new_item.product_name = result['product_name']

            self.line_items_data.append(new_item)
            self._refresh_line_items_tree()
            self._update_totals_display()

    def _edit_item_dialog(self):
        if not self.selected_line_item_iid:
            messagebox.showwarning("No Selection", "Please select an item to edit.", parent=self)
            return

        try:
            item_index = int(self.selected_line_item_iid)
            item_to_edit_struct = self.line_items_data[item_index]
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Invalid item selection.", parent=self)
            return

        existing_item_data_for_popup = {
            'product_id': item_to_edit_struct.product_id,
            'quantity': item_to_edit_struct.quantity,
            'item_id': item_to_edit_struct.item_id
        }

        item_popup = SalesDocumentItemPopup(
            self,
            self.product_logic,
            existing_item_data=existing_item_data_for_popup,
            available_products=self.available_products_for_item_popup
        )
        result = item_popup.show()

        if result:
            item_to_edit_struct.product_id = result['product_id']
            item_to_edit_struct.quantity = result['quantity']
            item_to_edit_struct.unit_price = result['unit_price']
            item_to_edit_struct.line_total = result['line_total']
            item_to_edit_struct.product_name = result['product_name']

            self._refresh_line_items_tree()
            self._update_totals_display()

    def _remove_item(self):
        if not self.selected_line_item_iid:
            messagebox.showwarning("No Selection", "Please select an item to remove.", parent=self)
            return

        try:
            item_index = int(self.selected_line_item_iid)
            del self.line_items_data[item_index]
            self._refresh_line_items_tree()
            self._update_totals_display()
            self.selected_line_item_iid = None
        except (ValueError, IndexError):
            messagebox.showerror("Error", "Invalid item selection for removal.", parent=self)


    def _save_document(self):
        selected_customer_name = self.customer_combobox.get()
        if not selected_customer_name or selected_customer_name not in self.customers_map:
            customer_id_from_text = self.customer_combobox.get()
            if customer_id_from_text.startswith("ID: "):
                 try:
                     customer_id = int(customer_id_from_text.replace("ID: ", ""))
                 except ValueError:
                     messagebox.showerror("Validation Error", "Invalid customer selection.", parent=self)
                     return
            else:
                messagebox.showerror("Validation Error", "Please select a valid customer.", parent=self)
                return
        else:
            customer_id = self.customers_map[selected_customer_name]


        doc_date_str = self.doc_date_entry.get().strip()
        try:
            doc_date = datetime.date.fromisoformat(doc_date_str)
        except ValueError:
            messagebox.showerror("Validation Error", "Invalid document date format. Use YYYY-MM-DD.", parent=self)
            return

        status = self.status_combobox.get()
        if not status:
            messagebox.showerror("Validation Error", "Please select a status.", parent=self)
            return

        if not self.line_items_data: # Check after attempting to convert items_for_logic
            messagebox.showwarning("Validation Error", "Cannot save a document with no line items.", parent=self)
            return

        items_for_logic = []
        for ui_item in self.line_items_data:
            if not all([hasattr(ui_item, 'product_id'), hasattr(ui_item, 'quantity')]):
                 messagebox.showerror("Save Error", "Corrupted line item data.", parent=self)
                 return
            items_for_logic.append({
                'product_id': ui_item.product_id,
                'quantity': ui_item.quantity,
                'item_id': ui_item.item_id
            })

        try:
            if self.document_id:
                success_items = self.sales_logic.update_sales_document_items(self.document_id, items_for_logic)
                if not success_items:
                    messagebox.showerror("Save Error", "Failed to update document items.", parent=self)
                    return

                updated_doc_data = self.sales_logic.get_sales_document_details(self.document_id)
                final_total_amount = updated_doc_data.total_amount if updated_doc_data and updated_doc_data.total_amount is not None else sum(item.line_total for item in self.line_items_data if hasattr(item, 'line_total'))

                # Use a dedicated SalesLogic method to update header
                update_header_success = self.sales_logic.update_sales_document_header(
                    document_id=self.document_id,
                    customer_id=customer_id,
                    document_date=doc_date, # Pass date object
                    status=status,
                    total_amount=final_total_amount
                )
                if not update_header_success:
                     messagebox.showerror("Save Error", "Failed to update document header details.", parent=self)
                     return
                messagebox.showinfo("Success", "Sales document updated successfully!", parent=self)

            else:
                new_doc_id = self.sales_logic.create_sales_document(
                    customer_id=customer_id,
                    document_date=doc_date, # Pass date object
                    status=status,
                    items_data=items_for_logic
                )
                if new_doc_id:
                    messagebox.showinfo("Success", f"Sales document created with ID: {new_doc_id}", parent=self)
                    self.document_id = new_doc_id
                else:
                    messagebox.showerror("Save Error", "Failed to create sales document.", parent=self)
                    return

            self.calling_tab.refresh_documents_list()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Save Error", f"An error occurred: {e}", parent=self)

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()

    class MockSalesLogic:
        def get_sales_document_details(self, doc_id):
            if doc_id == 1:
                doc = SalesDocument(document_id=1, customer_id=101, document_date=datetime.date(2023,1,10), status="Draft", total_amount=150.0)
                item1 = SalesDocumentItem(item_id=1, document_id=1, product_id=1001, quantity=2, unit_price=25.0, line_total=50.0)
                item1.product_name = "Product X" # For testing
                item2 = SalesDocumentItem(item_id=2, document_id=1, product_id=1002, quantity=1, unit_price=100.0, line_total=100.0)
                item2.product_name = "Product Y" # For testing
                doc.items = [item1, item2]
                return doc
            return None

        def create_sales_document(self, customer_id, document_date, status, items_data):
            print(f"MOCK: Create Sales Doc: CustID {customer_id}, Date {document_date}, Status {status}, Items: {len(items_data)}")
            calculated_total = 0
            for item in items_data:
                # Mock price fetching for total calculation
                mock_price = 10.0 # default mock price
                if item['product_id'] == 1001: mock_price = 25.0
                elif item['product_id'] == 1002: mock_price = 100.0
                calculated_total += item['quantity'] * mock_price
            print(f"Mock calculated total for new doc: {calculated_total}")
            return 999

        def update_sales_document_items(self, document_id, items_data):
            print(f"MOCK: Update Sales Doc Items: DocID {document_id}, Items: {len(items_data)}")
            return True

        def update_sales_document_header(self, document_id, customer_id, document_date, status, total_amount):
            print(f"MOCK: Update Sales Doc Header: DocID {document_id}, CustID {customer_id}, Date {document_date}, Status {status}, Total {total_amount}")
            return True


    class MockCustomerLogic:
        def get_all_accounts(self):
            class MockAcc:
                def __init__(self, id, name): self.account_id = id; self.name = name
            return [MockAcc(101, "Customer A"), MockAcc(102, "Customer B")]
        def get_account_details(self, account_id):
            if account_id == 101: return Account(account_id=101, name="Customer A")
            if account_id == 102: return Account(account_id=102, name="Customer B")
            return None


    class MockProductLogic:
        def get_all_products(self):
            return [
                Product(product_id=1001, name="Product X", cost=25.00),
                Product(product_id=1002, name="Product Y", cost=100.00),
                Product(product_id=1003, name="Product Z", cost=10.00)
            ]
        def get_product_details(self, product_id):
            for p in self.get_all_products():
                if p.product_id == product_id:
                    return p
            return None

    class MockCallingTab:
        def refresh_documents_list(self):
            print("MOCK: Calling tab refresh_documents_list called.")

    mock_sales_logic = MockSalesLogic()
    mock_customer_logic = MockCustomerLogic()
    mock_product_logic = MockProductLogic()
    mock_calling_tab = MockCallingTab()

    # Test Edit Document
    popup_edit = SalesDocumentPopup(root, mock_calling_tab, mock_sales_logic, mock_customer_logic, mock_product_logic, document_id=1)
    # Test New Document
    # popup_new = SalesDocumentPopup(root, mock_calling_tab, mock_sales_logic, mock_customer_logic, mock_product_logic, document_id=None)

    root.mainloop()
