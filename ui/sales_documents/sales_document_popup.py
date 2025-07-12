import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from typing import Optional, List
import datetime

from shared.structs import (
    SalesDocument, SalesDocumentItem, SalesDocumentStatus, SalesDocumentType,
    AccountType
)

NO_CUSTOMER_LABEL = "<Select Customer>" # Changed from Vendor
DEFAULT_DOC_TYPE = SalesDocumentType.QUOTE # Default for new documents

class SalesDocumentPopup(Toplevel): # Changed from tk.Toplevel for directness
    def __init__(self, master, sales_logic, account_logic, product_logic, document_id=None, initial_doc_type: Optional[SalesDocumentType]=None, parent_controller=None):
        super().__init__(master)
        self.sales_logic = sales_logic # Changed from purchase_logic
        self.account_logic = account_logic
        self.product_logic = product_logic
        self.document_id = document_id
        self.parent_controller = parent_controller
        self.initial_doc_type = initial_doc_type if initial_doc_type else DEFAULT_DOC_TYPE

        # Determine window title and initial status based on new/edit and doc_type
        self.current_doc_type: Optional[SalesDocumentType] = None # Will be set during load or for new
        self.current_status: Optional[SalesDocumentStatus] = None # Will be set

        # UI Variables
        self.doc_number_var = tk.StringVar()
        self.created_date_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.doc_type_var = tk.StringVar()
        self.customer_var = tk.StringVar() # For customer combobox

        # Sales specific fields
        self.expiry_date_var = tk.StringVar() # For Quotes
        self.due_date_var = tk.StringVar()    # For Invoices
        self.subtotal_var = tk.StringVar(value="$0.00")
        self.taxes_var = tk.StringVar(value="$0.00") # New field for display
        self.total_amount_var = tk.StringVar(value="$0.00") # New field for display

        self.document_data: Optional[SalesDocument] = None
        self.items_data: List[SalesDocumentItem] = []
        self.customer_map = {} # Changed from vendor_map

        self._setup_ui() # Call after all vars are initialized

        if self.document_id:
            self.load_document_and_items()
        else: # New document
            self.current_doc_type = self.initial_doc_type
            self.doc_type_var.set(self.current_doc_type.value)
            self.doc_number_var.set("(Auto-generated)")
            self.created_date_var.set(datetime.date.today().isoformat())

            if self.current_doc_type == SalesDocumentType.QUOTE:
                self.status_var.set(SalesDocumentStatus.QUOTE_DRAFT.value)
                self.expiry_date_var.set((datetime.date.today() + datetime.timedelta(days=30)).isoformat())
            elif self.current_doc_type == SalesDocumentType.INVOICE:
                self.status_var.set(SalesDocumentStatus.INVOICE_DRAFT.value)
                self.due_date_var.set((datetime.date.today() + datetime.timedelta(days=30)).isoformat())

            self.populate_customer_dropdown() # Changed from vendor
            self.customer_combobox.set(NO_CUSTOMER_LABEL)
            self._update_document_totals_display()
            self.update_ui_states()
            self.update_export_button_state()
            self.title(f"New {self.current_doc_type.value}")


    def _setup_ui(self):
        self.content_frame = ttk.Frame(self, padding="10")
        self.content_frame.pack(expand=True, fill=tk.BOTH)
        self.geometry("750x650") # Adjusted size

        current_row = 0

        # Document Type (Non-editable if editing, Dropdown if new and type not pre-selected)
        ttk.Label(self.content_frame, text="Document Type:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.W)
        self.doc_type_combobox = ttk.Combobox(self.content_frame, textvariable=self.doc_type_var,
                                             values=[dt.value for dt in SalesDocumentType],
                                             width=37)
        self.doc_type_combobox.grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.EW)
        self.doc_type_combobox.bind("<<ComboboxSelected>>", self._on_doc_type_changed)
        current_row += 1

        ttk.Label(self.content_frame, text="Document #:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(self.content_frame, textvariable=self.doc_number_var, state=tk.DISABLED, width=40).grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.EW)
        current_row += 1

        ttk.Label(self.content_frame, text="Customer:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.W) # Changed from Vendor
        self.customer_combobox = ttk.Combobox(self.content_frame, textvariable=self.customer_var, state="readonly", width=37) # Changed from vendor_combobox
        self.customer_combobox.grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.EW)
        current_row += 1

        ttk.Label(self.content_frame, text="Created Date:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(self.content_frame, textvariable=self.created_date_var, state=tk.DISABLED, width=40).grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.EW)
        current_row += 1

        # Expiry Date (for Quotes) / Due Date (for Invoices)
        self.conditional_date_label = ttk.Label(self.content_frame, text="Expiry Date:") # Default text
        self.conditional_date_label.grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.W)
        self.conditional_date_entry = ttk.Entry(self.content_frame, textvariable=self.expiry_date_var, width=40) # Default var
        self.conditional_date_entry.grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.EW)
        # TODO: Add DatePicker for these dates
        current_row += 1

        ttk.Label(self.content_frame, text="Status:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.W)
        self.status_combobox = ttk.Combobox(self.content_frame, textvariable=self.status_var,
                                            state="readonly", width=37) # Values set dynamically
        self.status_combobox.grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.EW)
        current_row += 1

        items_label_frame = ttk.LabelFrame(self.content_frame, text="Document Items", padding="5")
        items_label_frame.grid(row=current_row, column=0, columnspan=2, padx=5, pady=(10,5), sticky=tk.NSEW)
        self.content_frame.grid_rowconfigure(current_row, weight=1)
        current_row += 1

        self.item_button_frame = ttk.Frame(items_label_frame)
        self.item_button_frame.pack(pady=5, fill=tk.X)
        self.add_item_button = ttk.Button(self.item_button_frame, text="Add Line Item", command=self.add_item)
        self.add_item_button.pack(side=tk.LEFT, padx=5)
        self.edit_item_button = ttk.Button(self.item_button_frame, text="Edit Line Item", command=self.edit_item, state=tk.DISABLED)
        self.edit_item_button.pack(side=tk.LEFT, padx=5)
        self.remove_item_button = ttk.Button(self.item_button_frame, text="Remove Line Item", command=self.remove_item, state=tk.DISABLED)
        self.remove_item_button.pack(side=tk.LEFT, padx=5)

        item_columns = ("desc", "qty", "unit_price", "discount", "line_total") # Added discount
        self.items_tree = ttk.Treeview(items_label_frame, columns=item_columns, show="headings", selectmode="browse", height=6)
        self.items_tree.heading("desc", text="Product/Service Description")
        self.items_tree.heading("qty", text="Quantity")
        self.items_tree.heading("unit_price", text="Unit Price")
        self.items_tree.heading("discount", text="Discount %") # New column
        self.items_tree.heading("line_total", text="Line Total")
        self.items_tree.column("desc", width=230)
        self.items_tree.column("qty", width=60, anchor=tk.E)
        self.items_tree.column("unit_price", width=80, anchor=tk.E)
        self.items_tree.column("discount", width=70, anchor=tk.E) # New column
        self.items_tree.column("line_total", width=90, anchor=tk.E)

        items_scrollbar = ttk.Scrollbar(items_label_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)
        self.items_tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_tree_select)
        self.items_tree.bind("<Double-1>", self.on_item_double_click)

        ttk.Label(self.content_frame, text="Notes:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.NW)
        self.notes_text = tk.Text(self.content_frame, height=3, width=50)
        self.notes_text.grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.EW)
        current_row += 1

        # Totals Section
        totals_frame = ttk.Frame(self.content_frame)
        totals_frame.grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.E)
        ttk.Label(totals_frame, text="Subtotal:").grid(row=0, column=0, sticky=tk.E)
        ttk.Label(totals_frame, textvariable=self.subtotal_var).grid(row=0, column=1, sticky=tk.E, padx=5)
        ttk.Label(totals_frame, text="Taxes:").grid(row=1, column=0, sticky=tk.E)
        ttk.Label(totals_frame, textvariable=self.taxes_var).grid(row=1, column=1, sticky=tk.E, padx=5)
        ttk.Label(totals_frame, text="Total:").grid(row=2, column=0, sticky=tk.E, pady=(5,0))
        ttk.Label(totals_frame, textvariable=self.total_amount_var, font=('TkDefaultFont', 10, 'bold')).grid(row=2, column=1, sticky=tk.E, padx=5, pady=(5,0))
        current_row += 1

        self.content_frame.grid_columnconfigure(1, weight=1)

        bottom_button_frame = ttk.Frame(self)
        bottom_button_frame.pack(pady=10, padx=10, fill=tk.X, side=tk.BOTTOM)
        self.save_button = ttk.Button(bottom_button_frame, text="Save", command=self.save_document)
        self.save_button.pack(side=tk.RIGHT, padx=5)
        self.export_pdf_button = ttk.Button(bottom_button_frame, text="Export to PDF", command=self.export_to_pdf, state=tk.DISABLED)
        self.export_pdf_button.pack(side=tk.RIGHT, padx=5)
        self.close_button = ttk.Button(bottom_button_frame, text="Close", command=self.destroy)
        self.close_button.pack(side=tk.RIGHT, padx=5)

    def _on_doc_type_changed(self, event=None):
        selected_type_str = self.doc_type_var.get()
        try:
            new_doc_type = SalesDocumentType(selected_type_str)
            if self.current_doc_type != new_doc_type:
                self.current_doc_type = new_doc_type
                # Update UI elements that depend on doc type (status list, date labels)
                if not self.document_id: # Only if creating new
                    if self.current_doc_type == SalesDocumentType.QUOTE:
                        self.status_var.set(SalesDocumentStatus.QUOTE_DRAFT.value)
                        self.expiry_date_var.set((datetime.date.today() + datetime.timedelta(days=30)).isoformat())
                        self.due_date_var.set("")
                    elif self.current_doc_type == SalesDocumentType.INVOICE:
                        self.status_var.set(SalesDocumentStatus.INVOICE_DRAFT.value)
                        self.due_date_var.set((datetime.date.today() + datetime.timedelta(days=30)).isoformat())
                        self.expiry_date_var.set("")
                self.update_ui_states() # Refresh date labels, status dropdown values etc.

        except ValueError:
            messagebox.showerror("Error", f"Invalid document type selected: {selected_type_str}", parent=self)

    def update_export_button_state(self):
        # PDF export enabled only if document exists and is of a type we can export (e.g. Quote or Invoice)
        can_export = self.document_id and self.document_data and \
                     self.document_data.document_type in [SalesDocumentType.QUOTE, SalesDocumentType.INVOICE]
        self.export_pdf_button.config(state=tk.NORMAL if can_export else tk.DISABLED)

    def export_to_pdf(self):
        if not self.document_id or not self.document_data:
            messagebox.showwarning("No Document", "Please save the document first.", parent=self)
            return

        doc_type = self.document_data.document_type
        generator_module = None
        if doc_type == SalesDocumentType.QUOTE:
            try:
                from core.quote_generator import generate_quote_pdf # Placeholder
                generator_module = generate_quote_pdf
            except ImportError:
                messagebox.showerror("Error", "Quote PDF generator not found.", parent=self)
                return
        elif doc_type == SalesDocumentType.INVOICE:
            try:
                from core.invoice_generator import generate_invoice_pdf # Placeholder
                generator_module = generate_invoice_pdf
            except ImportError:
                messagebox.showerror("Error", "Invoice PDF generator not found.", parent=self)
                return
        else:
            messagebox.showwarning("Not Supported", f"PDF export not supported for document type: {doc_type.value}", parent=self)
            return

        try:
            file_prefix = "quote" if doc_type == SalesDocumentType.QUOTE else "invoice"
            output_filename = f"{file_prefix}_{self.doc_number_var.get().replace('/', '_')}.pdf"
            # TODO: Use filedialog.asksaveasfilename for better UX

            generator_module(self.document_id, output_path=output_filename) # Call the specific generator
            messagebox.showinfo("PDF Exported", f"{doc_type.value} exported to {output_filename}", parent=self)
        except Exception as e:
            messagebox.showerror("PDF Export Error", f"An error occurred: {e}", parent=self)
            import traceback
            traceback.print_exc()


    def populate_customer_dropdown(self): # Changed from populate_vendor_dropdown
        self.customer_map.clear()
        customer_names = [NO_CUSTOMER_LABEL]
        # Assuming account_logic.get_all_accounts() returns list of Account objects or dicts
        all_accounts_raw = self.account_logic.get_all_accounts()

        for acc in all_accounts_raw:
            try:
                # Assuming acc is an Account object with attributes
                if acc.account_type == AccountType.CUSTOMER:
                    self.customer_map[acc.name] = acc.id
                    customer_names.append(acc.name)
            except (ValueError, AttributeError) as e:
                # Catching AttributeError as well in case the object structure is not as expected
                print(f"Warning: Skipping account due to error: {e}")


        self.customer_combobox['values'] = sorted(list(set(customer_names)))
        if self.document_data and self.document_data.customer_id:
            for name, c_id in self.customer_map.items():
                if c_id == self.document_data.customer_id:
                    self.customer_var.set(name) # Use self.customer_var
                    return
        self.customer_var.set(NO_CUSTOMER_LABEL)


    def load_document_and_items(self):
        if not self.document_id: return
        self.document_data = self.sales_logic.get_sales_document_details(self.document_id) # Use sales_logic
        if not self.document_data:
            messagebox.showerror("Error", f"Could not load sales document with ID {self.document_id}.", parent=self)
            self.destroy()
            return

        self.current_doc_type = self.document_data.document_type
        self.current_status = self.document_data.status

        self.title(f"Edit {self.current_doc_type.value} - {self.document_data.document_number}")
        self.doc_number_var.set(self.document_data.document_number)
        self.doc_type_var.set(self.current_doc_type.value if self.current_doc_type else "")
        self.created_date_var.set(self.document_data.created_date.split("T")[0] if self.document_data.created_date else "")

        if self.current_doc_type == SalesDocumentType.QUOTE:
            self.expiry_date_var.set(self.document_data.expiry_date.split("T")[0] if self.document_data.expiry_date else "")
            self.due_date_var.set("")
        elif self.current_doc_type == SalesDocumentType.INVOICE:
            self.due_date_var.set(self.document_data.due_date.split("T")[0] if self.document_data.due_date else "")
            self.expiry_date_var.set("")

        self.status_var.set(self.current_status.value if self.current_status else "N/A")
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", self.document_data.notes or "")

        self.populate_customer_dropdown() # Changed
        self.load_items_for_document() # Calls _update_document_totals_display and update_ui_states
        self.update_export_button_state()


    def load_items_for_document(self):
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)
        if self.document_data and self.document_data.id:
            self.items_data = self.sales_logic.get_items_for_sales_document(self.document_data.id) # Use sales_logic
            for item in self.items_data:
                self.items_tree.insert("", tk.END, values=(
                    item.product_description,
                    f"{item.quantity:.2f}",
                    f"${item.unit_price:.2f}" if item.unit_price is not None else "",
                    f"{item.discount_percentage:.1f}%" if item.discount_percentage is not None else "0.0%",
                    f"${item.line_total:.2f}" if item.line_total is not None else ""
                ), iid=str(item.id))
        self.on_item_tree_select(None) # Update button states
        self._update_document_totals_display()
        self.update_ui_states()


    def on_item_tree_select(self, event):
        selected = self.items_tree.selection()
        can_edit = self.can_edit_items()
        can_edit_delete = bool(selected) and can_edit
        self.edit_item_button.config(state=tk.NORMAL if can_edit_delete else tk.DISABLED)
        self.remove_item_button.config(state=tk.NORMAL if can_edit_delete else tk.DISABLED)

    def on_item_double_click(self, event):
        item_iid = self.items_tree.identify_row(event.y)
        if not item_iid: return
        if str(self.edit_item_button.cget('state')).strip() == "normal":
            current_selection = self.items_tree.selection()
            if not (len(current_selection) == 1 and current_selection[0] == item_iid):
                self.items_tree.selection_set(item_iid)
            self.items_tree.focus(item_iid)
            self.edit_item()

    def can_edit_items(self) -> bool:
        if not self.document_data or not self.current_status: # current_status set in load_document_and_items
            return True # New document or error loading

        editable_statuses = [
            SalesDocumentStatus.QUOTE_DRAFT,
            SalesDocumentStatus.INVOICE_DRAFT
        ]
        return self.current_status in editable_statuses

    def update_ui_states(self):
        """Updates UI element states (labels, comboboxes, entry fields) based on document type and status."""
        can_edit_items_flag = self.can_edit_items()
        is_new_document = not self.document_id

        # Document Type ComboBox
        self.doc_type_combobox.config(state=tk.DISABLED if not is_new_document else "readonly")

        # Customer ComboBox, Notes, Date Fields
        customer_combo_state = "readonly"
        notes_text_state = tk.NORMAL
        conditional_date_entry_state = tk.NORMAL # For expiry/due date

        if self.current_doc_type == SalesDocumentType.QUOTE:
            self.conditional_date_label.config(text="Expiry Date:")
            self.conditional_date_entry.config(textvariable=self.expiry_date_var)
            relevant_statuses = [s.value for s in SalesDocumentStatus if s.name.startswith("QUOTE_")]
            if self.current_status not in [SalesDocumentStatus.QUOTE_DRAFT]:
                customer_combo_state = tk.DISABLED
                notes_text_state = tk.DISABLED
                conditional_date_entry_state = tk.DISABLED
        elif self.current_doc_type == SalesDocumentType.INVOICE:
            self.conditional_date_label.config(text="Due Date:")
            self.conditional_date_entry.config(textvariable=self.due_date_var)
            relevant_statuses = [s.value for s in SalesDocumentStatus if s.name.startswith("INVOICE_")]
            if self.current_status not in [SalesDocumentStatus.INVOICE_DRAFT]:
                customer_combo_state = tk.DISABLED
                notes_text_state = tk.DISABLED
                conditional_date_entry_state = tk.DISABLED
        else: # Should not happen if type is always set
            relevant_statuses = [s.value for s in SalesDocumentStatus] # Show all as fallback

        self.status_combobox['values'] = relevant_statuses
        if self.status_var.get() not in relevant_statuses and relevant_statuses:
             self.status_var.set(relevant_statuses[0]) # Default to first if current is invalid for type

        self.customer_combobox.config(state=customer_combo_state)
        self.notes_text.config(state=notes_text_state)
        self.conditional_date_entry.config(state=conditional_date_entry_state)

        # Status combobox state
        status_combo_state = "readonly" # Generally allow changing status unless it's terminal like PAID/VOID/CLOSED
        if self.current_status in [SalesDocumentStatus.INVOICE_PAID, SalesDocumentStatus.INVOICE_VOID, SalesDocumentStatus.QUOTE_ACCEPTED, SalesDocumentStatus.QUOTE_REJECTED, SalesDocumentStatus.QUOTE_EXPIRED]:
            status_combo_state = tk.DISABLED # Lock status for these states
        self.status_combobox.config(state=status_combo_state)


        self.add_item_button.config(state=tk.NORMAL if can_edit_items_flag else tk.DISABLED)
        self.on_item_tree_select(None) # Updates edit/remove item buttons


    def add_item(self):
        if not self.document_id:
            if not self._ensure_document_exists_for_items(): return

        if not self.document_data or self.document_data.id is None:
            messagebox.showwarning("No Document", "Document could not be prepared.", parent=self)
            return
        if not self.can_edit_items():
            messagebox.showwarning("Cannot Add Items", f"Items cannot be added to a document with status '{self.current_status.value}'.", parent=self)
            return

        from .sales_document_item_popup import SalesDocumentItemPopup # Import sales version
        item_popup = SalesDocumentItemPopup(self, self.sales_logic, self.product_logic, self.document_data.id)
        self.wait_window(item_popup)
        if hasattr(item_popup, 'item_saved') and item_popup.item_saved:
            self.load_items_for_document()

    def _ensure_document_exists_for_items(self) -> bool:
        if self.document_id and self.document_data: return True
        if self.save_document(is_autosave_for_draft=True):
            return bool(self.document_id and self.document_data)
        return False

    def edit_item(self):
        selected_tree_item = self.items_tree.selection()
        if not selected_tree_item:
            messagebox.showwarning("No Selection", "Please select an item to edit.", parent=self)
            return
        item_id = int(selected_tree_item[0])

        item_to_edit_obj = self.sales_logic.get_sales_document_item_details(item_id) # Use sales_logic
        if not item_to_edit_obj:
            messagebox.showerror("Error", f"Could not load details for item ID: {item_id}.", parent=self)
            self.load_items_for_document() # Refresh list
            return
        if not self.can_edit_items():
            messagebox.showwarning("Cannot Edit", f"Items cannot be edited for status '{self.current_status.value}'.", parent=self)
            return

        from .sales_document_item_popup import SalesDocumentItemPopup # Import sales version
        item_data_dict = item_to_edit_obj.to_dict()
        edit_item_popup = SalesDocumentItemPopup(self, self.sales_logic, self.product_logic, self.document_data.id, item_data=item_data_dict)
        self.wait_window(edit_item_popup)
        if hasattr(edit_item_popup, 'item_saved') and edit_item_popup.item_saved:
            self.load_document_and_items() # Full reload to refresh doc status/totals potentially changed by item edit

    def _update_document_totals_display(self):
        if self.document_data:
            self.subtotal_var.set(f"${self.document_data.subtotal or 0.0:.2f}")
            self.taxes_var.set(f"${self.document_data.taxes or 0.0:.2f}")
            self.total_amount_var.set(f"${self.document_data.total_amount or 0.0:.2f}")
        else: # New document, defaults
            self.subtotal_var.set("$0.00")
            self.taxes_var.set("$0.00")
            self.total_amount_var.set("$0.00")

    def remove_item(self):
        selected = self.items_tree.selection()
        if not selected: return
        item_id = int(selected[0])
        item_to_delete = next((i for i in self.items_data if i.id == item_id), None)
        if not item_to_delete: return

        if not self.can_edit_items(): # Double check status
            messagebox.showwarning("Cannot Remove Items", f"Items cannot be removed from a document with status '{self.current_status.value}'.", parent=self)
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Delete item '{item_to_delete.product_description}'?")
        if confirm:
            try:
                self.sales_logic.delete_sales_document_item(item_id) # Use sales_logic
                self.load_items_for_document() # Reload items and recalculate totals
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete item: {e}", parent=self)

    def save_document(self, is_autosave_for_draft=False) -> bool:
        selected_customer_name = self.customer_var.get() # Use customer_var
        if not selected_customer_name or selected_customer_name == NO_CUSTOMER_LABEL:
            if not is_autosave_for_draft:
                messagebox.showerror("Validation Error", "Please select a customer.", parent=self)
            else: # Autosave for adding items
                 messagebox.showwarning("Customer Required", "Please select a customer before adding items.", parent=self)
            return False

        current_customer_id = self.customer_map.get(selected_customer_name)
        if current_customer_id is None:
            messagebox.showerror("Error", "Selected customer is invalid.", parent=self)
            return False

        notes_content = self.notes_text.get("1.0", tk.END).strip()

        # Document Type (already set in self.current_doc_type)
        if self.current_doc_type is None: # Should be set on init or _on_doc_type_changed
            messagebox.showerror("Error", "Document type is not set.", parent=self)
            return False

        # Status
        selected_status_str = self.status_var.get()
        try:
            selected_status_enum = SalesDocumentStatus(selected_status_str)
        except ValueError:
            if not is_autosave_for_draft:
                messagebox.showerror("Validation Error", f"Invalid status: {selected_status_str}", parent=self)
            return False

        # Dates (Expiry for Quote, Due for Invoice)
        expiry_date_iso = None
        due_date_iso = None
        if self.current_doc_type == SalesDocumentType.QUOTE:
            expiry_date_iso = self.expiry_date_var.get()
            if not expiry_date_iso and not is_autosave_for_draft: # Required for quotes if not autosaving
                messagebox.showerror("Validation Error", "Expiry Date is required for a Quote.", parent=self)
                return False
        elif self.current_doc_type == SalesDocumentType.INVOICE:
            due_date_iso = self.due_date_var.get()
            if not due_date_iso and not is_autosave_for_draft: # Required for invoices
                messagebox.showerror("Validation Error", "Due Date is required for an Invoice.", parent=self)
                return False

        try:
            if self.document_id is None: # Creating new document
                if self.current_doc_type == SalesDocumentType.QUOTE:
                    new_doc = self.sales_logic.create_quote(
                        customer_id=current_customer_id,
                        notes=notes_content,
                        expiry_date_iso=expiry_date_iso
                    )
                elif self.current_doc_type == SalesDocumentType.INVOICE:
                    # For now, direct invoice creation. Later, might only come from Quote conversion.
                    # This would require a create_invoice method in sales_logic similar to create_quote
                    # For simplicity, reusing create_quote logic path by adapting it for Invoice
                    # This implies add_sales_document in DB handler needs to handle both. Let's assume it does.
                    # Or, we need a dedicated create_invoice in SalesLogic

                    # Let's use a direct call to add_sales_document via a placeholder method for now
                    # Ideally, SalesLogic would have create_invoice
                    temp_invoice_number = self.sales_logic._generate_sales_document_number(SalesDocumentType.INVOICE)
                    created_date_iso = datetime.datetime.now().isoformat()
                    new_doc_id = self.sales_logic.db.add_sales_document(
                        doc_number=temp_invoice_number, customer_id=current_customer_id,
                        document_type=SalesDocumentType.INVOICE.value, created_date=created_date_iso,
                        status=selected_status_enum.value, notes=notes_content, due_date=due_date_iso
                    )
                    if new_doc_id:
                        new_doc = self.sales_logic.get_sales_document_details(new_doc_id)
                    else:
                        new_doc = None
                else: # Should not happen
                    messagebox.showerror("Error", "Unsupported document type for creation.", parent=self)
                    return False

                if new_doc:
                    self.document_id = new_doc.id
                    self.document_data = new_doc
                    if not is_autosave_for_draft:
                        messagebox.showinfo("Success", f"{new_doc.document_type.value} {new_doc.document_number} created.", parent=self)
                    self.load_document_and_items() # Refresh all fields including doc number
                    self.title(f"Edit {new_doc.document_type.value} - {new_doc.document_number}")
                    if self.parent_controller: self.parent_controller.load_documents()
                    self.update_export_button_state()
                    return True
                else:
                    if not is_autosave_for_draft:
                        messagebox.showerror("Error", f"Failed to create {self.current_doc_type.value}.", parent=self)
                    return False

            else: # Updating existing document
                updates = {}
                # Customer change is complex, usually not allowed or handled differently. For now, warn if attempted.
                if self.document_data.customer_id != current_customer_id:
                    if not is_autosave_for_draft:
                         messagebox.showwarning("Info", "Changing customer is not directly supported here. Other changes saved.", parent=self)

                if (self.document_data.notes or "") != notes_content:
                    updates["notes"] = notes_content

                if self.document_data.status != selected_status_enum:
                    # Use the dedicated status update method for potential logic/validation
                    self.sales_logic.update_sales_document_status(self.document_id, selected_status_enum)
                    # No need to add to 'updates' dict as it's handled separately

                if self.current_doc_type == SalesDocumentType.QUOTE and self.document_data.expiry_date != expiry_date_iso:
                    updates["expiry_date"] = expiry_date_iso
                elif self.current_doc_type == SalesDocumentType.INVOICE and self.document_data.due_date != due_date_iso:
                    updates["due_date"] = due_date_iso

                if updates:
                    self.sales_logic.db.update_sales_document(self.document_id, updates)

                # Reload data to reflect all changes (including status if it was changed by logic)
                self.load_document_and_items()
                if not is_autosave_for_draft:
                    messagebox.showinfo("Success", f"{self.document_data.document_type.value} {self.document_data.document_number} updated.", parent=self)
                if self.parent_controller: self.parent_controller.load_documents()
                return True

        except ValueError as ve:
            if not is_autosave_for_draft: messagebox.showerror("Error", str(ve), parent=self)
            return False
        except Exception as e:
            if not is_autosave_for_draft: messagebox.showerror("Unexpected Error", f"Error: {e}", parent=self)
            import traceback; traceback.print_exc()
            return False
        return False


if __name__ == '__main__':
    # Mock classes for standalone testing
    class MockDBHandler: # Simplified, needs expansion for full SalesLogic testing
        def get_all_accounts(self): return []
        def get_account_details(self, acc_id): return None
        def get_product_details(self, prod_id): return None
        def get_all_products(self): return []

        def add_sales_document(self, **kwargs): return 1 # Mock ID
        def get_sales_document_by_id(self, doc_id):
            if doc_id == 1:
                return {
                    "id": 1, "document_number": "QUO-TEST-001", "customer_id": 101,
                    "document_type": SalesDocumentType.QUOTE.value,
                    "created_date": datetime.datetime.now().isoformat(),
                    "status": SalesDocumentStatus.QUOTE_DRAFT.value, "notes": "Mock Quote",
                    "expiry_date": (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat(),
                    "subtotal": 0, "taxes": 0, "total_amount": 0
                }
            return None
        def get_items_for_sales_document(self, doc_id): return []
        def add_sales_document_item(self, **kwargs): return 10 # Mock item ID
        def update_sales_document(self, doc_id, updates): pass
        def get_all_sales_documents(self, **kwargs): return []


    class MockAccountLogic:
        def get_all_accounts(self):
            from shared.structs import Account # Local import for test
            # Simulating the tuple structure from DatabaseHandler.get_all_accounts
            return [
                (101, "Customer Alpha", "123-456", "desc", AccountType.CUSTOMER.value),
                (102, "Customer Beta", "789-012", "desc", AccountType.CUSTOMER.value),
                (201, "Vendor Gamma", "000-111", "desc", AccountType.VENDOR.value)
            ]
        def get_account_details(self, acc_id):
            if acc_id == 101: return {"id": 101, "name": "Customer Alpha", "account_type": AccountType.CUSTOMER.value}
            return None

    class MockProductLogic:
        def get_all_products(self):
            from shared.structs import Product # Local import for test
            return [Product(product_id=1, name="Laptop Pro", sale_price=1200.00), Product(product_id=2, name="Wireless Mouse", sale_price=25.00)]
        def get_product_details(self, pid):
            if pid == 1: return {"product_id":1, "name":"Laptop Pro", "sale_price":1200.00, "description":"High-end laptop"}
            if pid == 2: return {"product_id":2, "name":"Wireless Mouse", "sale_price":25.00, "description":"Ergonomic mouse"}
            return None

    class MockSalesLogic: # More comprehensive mock for SalesLogic
        def __init__(self, db_handler): self.db = db_handler
        def _generate_sales_document_number(self, doc_type): return f"{doc_type.value[:3].upper()}-MOCK-001"

        def create_quote(self, customer_id, notes, expiry_date_iso):
            doc_id = self.db.add_sales_document(
                document_number=self._generate_sales_document_number(SalesDocumentType.QUOTE),
                customer_id=customer_id, document_type=SalesDocumentType.QUOTE.value,
                created_date=datetime.datetime.now().isoformat(), status=SalesDocumentStatus.QUOTE_DRAFT.value,
                notes=notes, expiry_date=expiry_date_iso, subtotal=0, taxes=0, total_amount=0)
            return self.get_sales_document_details(doc_id)

        def get_sales_document_details(self, doc_id):
            data = self.db.get_sales_document_by_id(doc_id)
            if data:
                 return SalesDocument(doc_id=data['id'], document_number=data['document_number'],
                                         customer_id=data['customer_id'], document_type=SalesDocumentType(data['document_type']),
                                         created_date=data['created_date'], status=SalesDocumentStatus(data['status']),
                                         notes=data.get('notes'), expiry_date=data.get('expiry_date'),
                                         subtotal=data.get('subtotal'), taxes=data.get('taxes'), total_amount=data.get('total_amount'))
            return None
        def get_items_for_sales_document(self, doc_id): return []
        def update_document_notes(self, doc_id, notes): self.db.update_sales_document(doc_id, {"notes": notes})
        def update_sales_document_status(self, doc_id, new_status: SalesDocumentStatus):
            self.db.update_sales_document(doc_id, {"status": new_status.value})
        def add_item_to_sales_document(self, **kwargs): return SalesDocumentItem(item_id=123, **kwargs) # Simplified
        def update_sales_document_item(self, **kwargs): return SalesDocumentItem(item_id=kwargs.get('item_id'), **kwargs) # Simplified
        def delete_sales_document_item(self, item_id): pass
        def _recalculate_sales_document_totals(self, doc_id): pass


    root = tk.Tk()
    root.title("Sales Popup Test")

    mock_db_h = MockDBHandler()
    mock_sl = MockSalesLogic(mock_db_h)
    mock_al = MockAccountLogic()
    mock_prod_l = MockProductLogic()

    class MockParentController:
        def load_documents(self): print("MockParentController: load_documents() called!")
    mock_controller = MockParentController()

    def open_new_quote():
        popup = SalesDocumentPopup(root, mock_sl, mock_al, mock_prod_l, initial_doc_type=SalesDocumentType.QUOTE, parent_controller=mock_controller)
        root.wait_window(popup)

    def open_new_invoice():
        popup = SalesDocumentPopup(root, mock_sl, mock_al, mock_prod_l, initial_doc_type=SalesDocumentType.INVOICE, parent_controller=mock_controller)
        root.wait_window(popup)

    def open_edit_quote():
        # Create a mock quote first to get an ID
        mock_quote = mock_sl.create_quote(customer_id=101, notes="Initial quote for edit", expiry_date_iso=(datetime.date.today() + datetime.timedelta(days=30)).isoformat())
        if mock_quote:
            popup = SalesDocumentPopup(root, mock_sl, mock_al, mock_prod_l, document_id=mock_quote.id, parent_controller=mock_controller)
            root.wait_window(popup)
        else:
            print("Failed to create mock quote for editing.")

    ttk.Button(root, text="New Quote", command=open_new_quote).pack(pady=5)
    ttk.Button(root, text="New Invoice", command=open_new_invoice).pack(pady=5)
    ttk.Button(root, text="Edit Quote (ID 1)", command=open_edit_quote).pack(pady=5)
    root.mainloop()
