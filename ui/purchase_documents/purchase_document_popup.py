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
        self.geometry("700x550")

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
            self._update_document_subtotal()
            self.update_ui_states_based_on_status()
            self.update_export_button_state() # Initial state

    def _setup_ui(self):
        self.content_frame = ttk.Frame(self, padding="10")
        self.content_frame.pack(expand=True, fill=tk.BOTH)

        self.doc_number_var = tk.StringVar()
        self.created_date_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.subtotal_var = tk.StringVar(value="$0.00")

        current_row = 0

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
        self.status_combobox = ttk.Combobox(self.content_frame, textvariable=self.status_var,
                                            values=[s.value for s in PurchaseDocumentStatus],
                                            state="readonly", width=37)
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
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_tree_select)  # Ensure event is bound
        self.items_tree.bind("<Double-1>", self.on_item_double_click) # Bind double-click
        items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(self.content_frame, text="Notes:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.NW)
        self.notes_text = tk.Text(self.content_frame, height=4, width=50)
        self.notes_text.grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.EW)
        current_row += 1

        ttk.Label(self.content_frame, text="Document Subtotal:").grid(row=current_row, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(self.content_frame, textvariable=self.subtotal_var, font=('TkDefaultFont', 10, 'bold')).grid(row=current_row, column=1, padx=5, pady=5, sticky=tk.E)
        current_row += 1

        self.content_frame.grid_columnconfigure(1, weight=1)

        bottom_button_frame = ttk.Frame(self)
        bottom_button_frame.pack(pady=10, padx=10, fill=tk.X, side=tk.BOTTOM)

        self.save_button = ttk.Button(bottom_button_frame, text="Save", command=self.save_document)
        self.save_button.pack(side=tk.RIGHT, padx=5)

        self.export_pdf_button = ttk.Button(bottom_button_frame, text="Export to PDF", command=self.export_to_pdf, state=tk.DISABLED)
        self.export_pdf_button.pack(side=tk.RIGHT, padx=5) # Placed before Close for typical Save/Export/Close order

        self.close_button = ttk.Button(bottom_button_frame, text="Close", command=self.destroy)
        self.close_button.pack(side=tk.RIGHT, padx=5)


    def update_export_button_state(self):
        if self.document_id:
            self.export_pdf_button.config(state=tk.NORMAL)
        else:
            self.export_pdf_button.config(state=tk.DISABLED)

    def export_to_pdf(self):
        if not self.document_id:
            messagebox.showwarning("No Document", "Please save the document first to obtain a document ID before exporting.", parent=self)
            return

        # Potentially use filedialog to ask user where to save
        # For now, it will save to the script's execution directory
        try:
            # Assuming generate_po_pdf.py is in the project root or accessible in PATH
            # Need to ensure generate_po_pdf can be called correctly
            # This might require adjusting how generate_po_pdf is invoked or making its function importable

            # Option 1: Make generate_po_pdf.generate_po_pdf importable
            # This requires generate_po_pdf.py to be structured to allow importing its main function.
            # And that the main project structure allows this import from ui.purchase_documents

            # PDF generation module is now part of the 'core' package
            from core.purchase_order_generator import generate_po_pdf as call_generate_po_pdf

            output_filename = f"purchase_order_{self.doc_number_var.get().replace('/', '_')}.pdf"
            # Consider using filedialog.asksaveasfilename here for better UX

            # Ensure the output directory exists or handle potential errors if it doesn't
            # For now, outputting to the current working directory of the main application

            call_generate_po_pdf(self.document_id, output_path=output_filename)
            messagebox.showinfo("PDF Exported", f"Document exported to {output_filename}", parent=self)

        except ImportError as ie:
            # This error might still occur if the overall project structure isn't correctly recognized by Python
            # when main.py is run, or if there are circular dependencies (less likely here).
            messagebox.showerror("Import Error", f"Could not load PDF generation module from core: {ie}\n"
                                 "Ensure the application is launched from the project root directory.", parent=self)
            import traceback # For more detailed debugging if needed by user
            traceback.print_exc()
        except Exception as e:
            messagebox.showerror("PDF Export Error", f"An error occurred during PDF export: {e}", parent=self)
            import traceback
            traceback.print_exc()


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
        # print("DEBUG: load_document_and_items called")
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
        self.load_items_for_document() # This calls update_ui_states_based_on_status and _update_document_subtotal
        self.update_export_button_state() # Update after loading

    def load_items_for_document(self):
        # print("DEBUG: load_items_for_document called")
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)
        if self.document_data and self.document_data.id:
            self.items_data = self.purchase_logic.get_items_for_document(self.document_data.id)
            # print(f"DEBUG: Loaded {len(self.items_data)} items for doc ID {self.document_data.id}")
            for item in self.items_data:
                self.items_tree.insert("", tk.END, values=(
                    item.product_description,
                    f"{item.quantity:.2f}",
                    f"{item.unit_price:.2f}" if item.unit_price is not None else "",
                    f"{item.total_price:.2f}" if item.total_price is not None else ""
                ), iid=str(item.id))
        self.on_item_tree_select(None)
        self._update_document_subtotal()
        self.update_ui_states_based_on_status()

    def on_item_tree_select(self, event):
        # print(f"DEBUG: on_item_tree_select: Event: {event}")
        selected = self.items_tree.selection()
        can_edit = self.can_edit_items()
        # print(f"DEBUG: on_item_tree_select: Selected items: {selected}, Can edit items: {can_edit}")
        can_edit_delete = bool(selected) and can_edit

        self.edit_item_button.config(state=tk.NORMAL if can_edit_delete else tk.DISABLED)
        self.remove_item_button.config(state=tk.NORMAL if can_edit_delete else tk.DISABLED)
        # print(f"DEBUG: on_item_tree_select: Edit button state: {self.edit_item_button.cget('state')}, Remove button state: {self.remove_item_button.cget('state')}")

    def on_item_double_click(self, event):
        print(f"DEBUG: on_item_double_click triggered. Event (x,y): ({event.x}, {event.y})")
        item_iid = self.items_tree.identify_row(event.y)
        print(f"DEBUG: item_iid from identify_row: '{item_iid}'")

        if not item_iid:
            print("DEBUG: on_item_double_click: item_iid is None or empty. Doing nothing.")
            return

        raw_state = self.edit_item_button.cget('state')
        print(f"DEBUG: on_item_double_click: repr(raw_state): {repr(raw_state)}")

        state_as_str = str(raw_state) # Explicitly convert Tcl_Obj to Python string
        print(f"DEBUG: on_item_double_click: repr(state_as_str): {repr(state_as_str)}")

        cleaned_state = state_as_str.strip()
        print(f"DEBUG: on_item_double_click: repr(cleaned_state) after strip: {repr(cleaned_state)}")
        print(f"DEBUG: on_item_double_click: cleaned_state value: '{cleaned_state}'")

        if cleaned_state == "normal":
            current_selection = self.items_tree.selection()
            print(f"DEBUG: on_item_double_click: current_selection before potential change: {current_selection}")

            if not (len(current_selection) == 1 and current_selection[0] == item_iid):
                print(f"DEBUG: on_item_double_click: Setting selection to '{item_iid}'")
                self.items_tree.selection_set(item_iid)

            print(f"DEBUG: on_item_double_click: Focusing item '{item_iid}'")
            self.items_tree.focus(item_iid)

            print("DEBUG: on_item_double_click: Attempting to call self.edit_item()")
            self.edit_item()
        else:
            print("DEBUG: on_item_double_click: Edit button not normal. Doing nothing.")

    def can_edit_items(self) -> bool:
        if not self.document_data or not self.document_data.status:
            # print("DEBUG: can_edit_items: True (new or no status)")
            return True
        can = self.document_data.status in [PurchaseDocumentStatus.RFQ, PurchaseDocumentStatus.QUOTED]
        # print(f"DEBUG: can_edit_items: Status {self.document_data.status.value}, Result: {can}")
        return can

    def update_ui_states_based_on_status(self):
        # print("DEBUG: update_ui_states_based_on_status called")
        can_edit_items_flag = self.can_edit_items()
        # print(f"DEBUG: update_ui_states_based_on_status: can_edit_items_flag: {can_edit_items_flag}")

        vendor_combo_state = "readonly"
        notes_text_state = tk.NORMAL
        status_combo_state = "readonly"

        if self.document_data and self.document_data.status:
            current_status = self.document_data.status
            # print(f"DEBUG: update_ui_states_based_on_status: current_status: {current_status.value}")
            if current_status not in [PurchaseDocumentStatus.RFQ, PurchaseDocumentStatus.QUOTED]:
                vendor_combo_state = tk.DISABLED
            if current_status in [PurchaseDocumentStatus.PO_ISSUED, PurchaseDocumentStatus.RECEIVED, PurchaseDocumentStatus.CLOSED]:
                 notes_text_state = tk.DISABLED
                 status_combo_state = tk.DISABLED

        self.vendor_combobox.config(state=vendor_combo_state)
        self.notes_text.config(state=notes_text_state)
        self.status_combobox.config(state=status_combo_state)

        self.add_item_button.config(state=tk.NORMAL if can_edit_items_flag else tk.DISABLED)
        # print(f"DEBUG: update_ui_states_based_on_status: Add Item button state: {self.add_item_button.cget('state')}")

        self.on_item_tree_select(None)

    def add_item(self):
        if not self.document_id: # Document is new
            if not self._ensure_document_exists():
                # _ensure_document_exists will show its own appropriate message (e.g. select vendor, or save failed)
                return

        # At this point, self.document_id and self.document_data should be populated if _ensure_document_exists succeeded.
        # Or, they were already populated for an existing document.

        if not self.document_data or self.document_data.id is None:
             # This case should ideally not be reached if _ensure_document_exists worked correctly for new docs,
             # but as a safeguard:
            messagebox.showwarning("No Document", "Document could not be prepared. Please save the document manually.", parent=self)
            return

        if not self.can_edit_items():
            messagebox.showwarning("Cannot Add Items", "Items cannot be added to a document with the current status.", parent=self)
            return

        from .purchase_document_item_popup import PurchaseDocumentItemPopup
        item_popup = PurchaseDocumentItemPopup(self, self.purchase_logic, self.product_logic, self.document_data.id)
        self.wait_window(item_popup)
        if hasattr(item_popup, 'item_saved') and item_popup.item_saved:
            self.load_items_for_document() # Refresh items and potentially document status/subtotal

    def _ensure_document_exists(self) -> bool:
        """
        Ensures the document exists (i.e., has an ID) before proceeding.
        If the document is new, it attempts to save it.
        Returns True if the document exists (or was successfully created), False otherwise.
        """
        if self.document_id and self.document_data: # Already exists and loaded
            return True

        # Attempt to save the document implicitly
        # The save_document method will handle vendor checks and actual creation.
        # We pass a flag to indicate this is an autosave for creating a draft.
        if self.save_document(is_autosave_for_draft=True):
            # save_document should set self.document_id and self.document_data on success
            if self.document_id and self.document_data:
                return True
            else:
                # This case implies save_document returned True but didn't set the ID, which would be a bug in save_document
                messagebox.showerror("Error", "Failed to retrieve document ID after save. Please try saving manually.", parent=self)
                return False
        else:
            # save_document returned False, meaning it failed (e.g., vendor not selected, or other validation error within save_document)
            # save_document itself should have shown an appropriate error message.
            return False

    def edit_item(self):
        print("DEBUG: edit_item called.")
        selected_tree_item = self.items_tree.selection()
        print(f"DEBUG: edit_item: selected_tree_item from self.items_tree.selection(): {selected_tree_item}")

        if not selected_tree_item:
            print("DEBUG: edit_item: No item selected. Showing warning and returning.")
            messagebox.showwarning("No Selection", "Please select an item to edit.", parent=self)
            return

        item_id_str = selected_tree_item[0]
        print(f"DEBUG: edit_item: item_id_str: {item_id_str}")
        item_id = -1 # Default to an invalid ID

        try:
            item_id = int(item_id_str)
            print(f"DEBUG: edit_item: item_id (int): {item_id}")
        except ValueError:
            print(f"DEBUG: edit_item: ValueError converting item_id_str '{item_id_str}' to int. Showing error and returning.")
            messagebox.showerror("Error", "Invalid item selection.", parent=self)
            return

        item_to_edit_obj = self.purchase_logic.get_purchase_document_item_details(item_id)
        if not item_to_edit_obj:
            print(f"DEBUG: edit_item: Could not load details for item ID: {item_id}. Showing error and returning.")
            messagebox.showerror("Error", f"Could not load details for item ID: {item_id}.", parent=self)
            self.load_items_for_document()
            return

        if not self.can_edit_items():
            print("DEBUG: edit_item: self.can_edit_items() is False. Showing warning and returning.")
            messagebox.showwarning("Cannot Edit", "Items cannot be edited for the current document status.", parent=self)
            return

        print("DEBUG: edit_item: All checks passed, proceeding to open PurchaseDocumentItemPopup.")
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

    def save_document(self, is_autosave_for_draft=False) -> bool:
        selected_vendor_name = self.vendor_combobox.get()
        # For autosave, we must have a vendor. For manual save, user is explicitly clicking.
        if not selected_vendor_name or selected_vendor_name == NO_VENDOR_LABEL:
            if is_autosave_for_draft:
                messagebox.showwarning("Vendor Required", "Please select a vendor before adding items.", parent=self)
            else: # Manual save
                messagebox.showerror("Validation Error", "Please select a vendor.", parent=self)
            return False

        current_vendor_id = self.vendor_map.get(selected_vendor_name)
        if current_vendor_id is None: # Should not happen if NO_VENDOR_LABEL check passed, but good for safety
            messagebox.showerror("Error", "Selected vendor is invalid.", parent=self)
            return False

        notes_content = self.notes_text.get("1.0", tk.END).strip()
        selected_status_str = self.status_var.get()
        selected_status_enum = None
        if selected_status_str:
            try:
                selected_status_enum = PurchaseDocumentStatus(selected_status_str)
            except ValueError:
                if not is_autosave_for_draft: # Only show error for manual save
                    messagebox.showerror("Validation Error", f"Invalid status selected: {selected_status_str}", parent=self)
                return False # Invalid status is a no-go for any save

        try:
            if self.document_id is None: # Creating a new document
                if current_vendor_id is None: # Should be caught by earlier check, but defensive
                    if not is_autosave_for_draft:
                        messagebox.showerror("Validation Error", "A vendor must be selected to create an RFQ.", parent=self)
                    return False

                new_doc = self.purchase_logic.create_rfq(
                    vendor_id=current_vendor_id,
                    notes=notes_content
                )
                if new_doc:
                    self.document_id = new_doc.id
                    self.document_data = new_doc # Crucial: update self.document_data
                    if not is_autosave_for_draft:
                        messagebox.showinfo("Success", f"RFQ {new_doc.document_number} created successfully.", parent=self)

                    # Common actions after new doc creation (for both auto and manual save)
                    self.load_document_and_items() # This will refresh UI, including items if any were virtually added then saved
                    self.title(f"Edit Purchase Document - {new_doc.document_number}")
                    if self.parent_controller and hasattr(self.parent_controller, 'load_documents'):
                         self.parent_controller.load_documents()
                    self.update_export_button_state() # Enable export after successful save
                    return True
                else:
                    if not is_autosave_for_draft:
                        messagebox.showerror("Error", "Failed to create RFQ. Please check logs or input.", parent=self)
                    return False
            else: # Updating an existing document
                # Document ID already exists, so export button should be appropriately set by load_document_and_items
                # or initial setup. We can re-call it to be sure, though not strictly necessary if already enabled.
                self.update_export_button_state()
                updated = False
                # Note: Vendor change is handled separately and not as part of a simple "updated" flag here.

                # Update Notes if changed
                if self.document_data and (self.document_data.notes or "") != notes_content:
                    self.purchase_logic.update_document_notes(self.document_id, notes_content)
                    updated = True

                # Update Status if changed (and valid enum)
                if self.document_data and selected_status_enum and self.document_data.status != selected_status_enum:
                    self.purchase_logic.update_document_status(self.document_id, selected_status_enum)
                    updated = True

                # Vendor change attempt (show warning, does not prevent other updates)
                if self.document_data and self.document_data.vendor_id != current_vendor_id:
                    # This logic typically only allows vendor change for RFQ, or not at all if status is advanced.
                    # For autosave, we probably wouldn't hit this if creating new, but for manual save on existing:
                    if not is_autosave_for_draft:
                        if self.document_data.status == PurchaseDocumentStatus.RFQ:
                            # Potentially allow vendor change for RFQ here if desired, or just warn.
                            # For now, sticking to warning that it's not part of this simple save.
                            messagebox.showwarning("Info", "Changing the vendor for an existing document is not supported via this save action. Other changes were saved if made.", parent=self)
                        elif self.document_data.status:
                             messagebox.showwarning("Warning", f"Vendor cannot be changed for a document with status '{self.document_data.status.value}'. Other changes were saved if made.", parent=self)
                        else: # Should not happen if status is always set
                             messagebox.showwarning("Warning", "Vendor cannot be changed for this document. Other changes were saved if made.", parent=self)
                    # `updated` flag is not set to true for vendor change attempt here, as it's not directly performed by this save action.

                if updated:
                    # Refresh document data from DB after updates
                    self.document_data = self.purchase_logic.get_purchase_document_details(self.document_id)
                    if not is_autosave_for_draft:
                        messagebox.showinfo("Success", f"Document {self.document_data.document_number} updated.", parent=self)
                    self.load_document_and_items() # Refresh UI
                    if self.parent_controller and hasattr(self.parent_controller, 'load_documents'):
                        self.parent_controller.load_documents()
                    return True
                else:
                    if not is_autosave_for_draft: # Only show "No Changes" for manual save
                        messagebox.showinfo("No Changes", "No changes were detected to save.", parent=self)
                    return True # Still counts as a successful "save" operation if no changes were needed
        except ValueError as ve:
            if not is_autosave_for_draft:
                messagebox.showerror("Error", str(ve), parent=self)
            return False
        except Exception as e:
            if not is_autosave_for_draft:
                messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}", parent=self)
                import traceback
                traceback.print_exc()
            return False

        return False # Should not be reached if logic is correct, but as a fallback

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
        def update_purchase_document_status(self, doc_id, status_val): pass

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
                 if hasattr(self.db, '_mock_status_override') and self.db._mock_status_override.get(doc_id):
                     data['status'] = self.db._mock_status_override[doc_id]
                 return PurchaseDocument(doc_id=data['id'], document_number=data['document_number'],
                                         vendor_id=data['vendor_id'], created_date=data['created_date'],
                                         status=PurchaseDocumentStatus(data['status']), notes=data['notes'])
            return None
        def get_items_for_document(self, doc_id): return []
        def update_document_notes(self, doc_id, notes): self.db.update_purchase_document_notes(doc_id, notes)
        def update_document_status(self, doc_id, new_status_enum: PurchaseDocumentStatus):
            print(f"MockPurchaseLogic: Updating status for doc {doc_id} to {new_status_enum.value}")
            if not hasattr(self.db, '_mock_status_override'): self.db._mock_status_override = {}
            self.db._mock_status_override[doc_id] = new_status_enum.value
            self.db.update_purchase_document_status(doc_id, new_status_enum.value)

        def add_item_to_document(self, doc_id, product_id, quantity, product_description_override=None, unit_price=None, total_price=None):
            from shared.structs import PurchaseDocumentItem
            print(f"Mock: Adding item (ProdID: {product_id}), qty {quantity} to doc {doc_id}")
            return PurchaseDocumentItem(item_id=123, purchase_document_id=doc_id, product_id=product_id,
                                        product_description=f"Mock Product {product_id}", quantity=quantity, unit_price=unit_price, total_price=total_price)
        def update_document_item(self, item_id, product_id, quantity, unit_price, product_description_override=None):
             from shared.structs import PurchaseDocumentItem
             print(f"Mock: Updating item ID {item_id} (ProdID: {product_id}), qty {quantity}, price {unit_price}")
             parent_doc = self.get_purchase_document_details(1)
             if parent_doc and parent_doc.status == PurchaseDocumentStatus.RFQ and unit_price is not None:
                 self.update_document_status(parent_doc.id, PurchaseDocumentStatus.QUOTED)
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
        doc = mock_pl.create_rfq(vendor_id=101, notes="Initial for edit")
        if doc:
            popup = PurchaseDocumentPopup(root, mock_pl, mock_al, mock_prod_l, document_id=doc.id, parent_controller=mock_controller)
            root.wait_window(popup)
        else:
            print("Failed to create mock document for editing.")

    ttk.Button(root, text="New Document", command=open_new).pack(pady=10)
    ttk.Button(root, text="Edit Document (ID 1)", command=open_edit).pack(pady=10)

    root.mainloop()
# [end of ui/purchase_documents/purchase_document_popup.py] # This was the duplicate marker causing issues.
