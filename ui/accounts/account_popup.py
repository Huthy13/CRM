import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from shared.structs import Address, Account, AccountType
from shared import AccountDocument
from ui.base.popup_base import PopupBase
import os
import shutil
import datetime
import subprocess
import sys
import uuid
from pathlib import Path
from core.preferences import load_preferences

class AccountDetailsPopup(PopupBase):
    def __init__(self, master, logic, account_id=None):
        super().__init__(master)
        self.logic = logic
        self.account_id = account_id

        if self.account_id == None:
            self.active_account = Account()
        else:
            self.active_account = self.logic.get_account_details(self.account_id)

        # Account details Fields
        self.name_entry = self._create_entry("Account Name:", 0, self.active_account.name)
        self.phone_entry = self._create_entry("Phone:", 1, self.active_account.phone)
        self.website_entry = self._create_entry("Website:", 2, self.active_account.website)

        # Account Type Dropdown
        tk.Label(self, text="Account Type:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.account_type_var = tk.StringVar(self)
        account_type_options = [atype.value for atype in AccountType]
        self.account_type_dropdown = ttk.Combobox(self, textvariable=self.account_type_var, values=account_type_options, state="readonly", width=37)
        if self.active_account.account_type:
            self.account_type_dropdown.set(self.active_account.account_type.value)
        self.account_type_dropdown.grid(row=3, column=1, padx=5, pady=5)

        self.account_type_dropdown.bind("<<ComboboxSelected>>", self.toggle_pricing_rule_dropdown)

        self.description_entry = self._create_entry("Description:", 4, self.active_account.description)

        # Payment Terms Dropdown
        tk.Label(self, text="Payment Terms:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.payment_term_var = tk.StringVar(self)
        self.payment_term_dropdown = ttk.Combobox(self, textvariable=self.payment_term_var, state="readonly", width=37)
        self.payment_term_dropdown.grid(row=5, column=1, padx=5, pady=5)
        self.load_payment_terms()

        # Pricing Rule Dropdown
        tk.Label(self, text="Pricing Rule:").grid(row=6, column=0, padx=5, pady=5, sticky="e")
        self.pricing_rule_var = tk.StringVar(self)
        self.pricing_rule_dropdown = ttk.Combobox(self, textvariable=self.pricing_rule_var, state="disabled", width=37)
        self.pricing_rule_dropdown.grid(row=6, column=1, padx=5, pady=5)
        self.load_pricing_rules()
        self.toggle_pricing_rule_dropdown()


        # Addresses Frame
        addresses_frame = tk.LabelFrame(self, text="Addresses")
        addresses_frame.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.address_tree = ttk.Treeview(addresses_frame, columns=("type", "primary", "address"), show="headings", height=5)
        self.address_tree.heading("type", text="Type")
        self.address_tree.heading("primary", text="Primary")
        self.address_tree.heading("address", text="Address")
        self.address_tree.pack(side="top", fill="x", expand=True)

        self.populate_address_tree()

        address_button_frame = tk.Frame(addresses_frame)
        address_button_frame.pack(side="bottom", fill="x", expand=True)
        tk.Button(address_button_frame, text="Add", command=self.add_address).pack(side="left")
        tk.Button(address_button_frame, text="Edit", command=self.edit_address).pack(side="left")
        tk.Button(address_button_frame, text="Delete", command=self.delete_address).pack(side="left")

        # Documents Frame
        documents_frame = tk.LabelFrame(self, text="Documents")
        documents_frame.grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.document_tree = ttk.Treeview(
            documents_frame,
            columns=("type", "filename", "expiry"),
            show="headings",
            height=5,
        )
        self.document_tree.heading("type", text="Type")
        self.document_tree.heading("filename", text="Filename")
        self.document_tree.heading("expiry", text="Expiry")
        self.document_tree.pack(side="top", fill="x", expand=True)

        doc_button_frame = tk.Frame(documents_frame)
        doc_button_frame.pack(side="bottom", fill="x", expand=True)
        tk.Button(doc_button_frame, text="Upload", command=self.upload_document).pack(side="left")
        tk.Button(doc_button_frame, text="Open", command=self.open_document).pack(side="left")
        tk.Button(doc_button_frame, text="Delete", command=self.delete_document).pack(side="left")

        self.refresh_documents()

        # Save Button
        save_button = tk.Button(self, text="Save", command=self.save_account)
        save_button.grid(row=18, column=0, columnspan=2, pady=10)

    def load_payment_terms(self):
        self.payment_terms = self.logic.list_payment_terms()
        term_names = [term.term_name for term in self.payment_terms]
        self.payment_term_dropdown['values'] = [""] + term_names
        if self.active_account.payment_term_id:
            for term in self.payment_terms:
                if term.term_id == self.active_account.payment_term_id:
                    self.payment_term_dropdown.set(term.term_name)
                    break

    def load_pricing_rules(self):
        self.pricing_rules = self.logic.list_pricing_rules()
        rule_names = [rule.rule_name for rule in self.pricing_rules]
        self.pricing_rule_dropdown['values'] = [""] + rule_names # Add empty option for no rule
        if self.active_account.pricing_rule_id:
            for rule in self.pricing_rules:
                if rule.rule_id == self.active_account.pricing_rule_id:
                    self.pricing_rule_dropdown.set(rule.rule_name)
                    break

    def toggle_pricing_rule_dropdown(self, event=None):
        if self.account_type_var.get() == AccountType.CUSTOMER.value:
            self.pricing_rule_dropdown['state'] = 'readonly'
        else:
            self.pricing_rule_dropdown['state'] = 'disabled'
            self.pricing_rule_var.set("") # Clear selection

    def populate_address_tree(self):
        for i in self.address_tree.get_children():
            self.address_tree.delete(i)
        for i, addr in enumerate(self.active_account.addresses):
            address_str = f"{addr.street}, {addr.city}, {addr.state} {addr.zip_code}, {addr.country}"
            types = getattr(addr, "address_types", [])
            if not types and getattr(addr, "address_type", ""):
                types = [addr.address_type]
            type_str = ", ".join([t for t in types if t])
            primary_types = getattr(addr, "primary_types", [])
            if not primary_types and getattr(addr, "is_primary", False) and getattr(addr, "address_type", ""):
                primary_types = [addr.address_type]
            primary_str = ", ".join(primary_types)
            self.address_tree.insert(
                "",
                "end",
                values=(
                    type_str,
                    primary_str,
                    address_str,
                ),
                iid=i,
            )

    def add_address(self):
        address_popup = AddressPopup(self)
        self.wait_window(address_popup)
        if hasattr(address_popup, 'address'):
            if not hasattr(address_popup.address, 'address_id'):
                address_popup.address.address_id = None
            if not hasattr(address_popup.address, 'address_types'):
                address_popup.address.address_types = []
            if not hasattr(address_popup.address, 'primary_types'):
                address_popup.address.primary_types = []
            if not hasattr(address_popup.address, 'address_type'):
                address_popup.address.address_type = (
                    address_popup.address.address_types[0] if address_popup.address.address_types else ""
                )
            if not hasattr(address_popup.address, 'is_primary'):
                address_popup.address.is_primary = (
                    address_popup.address.address_type in address_popup.address.primary_types
                )
            self.active_account.addresses.append(address_popup.address)
            self.populate_address_tree()

    def edit_address(self):
        selected_item = self.address_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select an address to edit.")
            return

        index = int(selected_item[0])
        address = self.active_account.addresses[index]
        address_popup = AddressPopup(self, address)
        self.wait_window(address_popup)
        self.populate_address_tree()

    def delete_address(self):
        selected_item = self.address_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select an address to delete.")
            return

        index = int(selected_item[0])
        del self.active_account.addresses[index]
        self.populate_address_tree()

    def refresh_documents(self):
        self.documents = []
        if self.active_account.account_id:
            self.documents = self.logic.get_account_documents(self.active_account.account_id)
        self.populate_document_tree()

    def populate_document_tree(self):
        for item in self.document_tree.get_children():
            self.document_tree.delete(item)
        self.document_map = {}
        for doc in getattr(self, "documents", []):
            filename = os.path.basename(doc.file_path)
            expiry = doc.expires_at.strftime("%Y-%m-%d") if doc.expires_at else ""
            iid = str(doc.document_id)
            self.document_tree.insert("", "end", iid=iid, values=(doc.document_type, filename, expiry))
            self.document_map[iid] = doc

    def upload_document(self):
        if self.active_account.account_id is None:
            messagebox.showerror("Error", "Save the account before uploading documents.")
            return
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        document_type = os.path.splitext(file_path)[1].lstrip(".").upper() or "FILE"
        prefs = load_preferences()
        base_dir = Path(prefs.get("document_storage_path", "uploaded_documents")).expanduser()
        storage_dir = base_dir / str(self.active_account.account_id)
        storage_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex}{Path(file_path).suffix}"
        dest_path = (storage_dir / unique_name).resolve()
        shutil.copy(file_path, dest_path)

        doc = AccountDocument(
            account_id=self.active_account.account_id,
            document_type=document_type,
            file_path=str(dest_path),
            uploaded_at=datetime.datetime.now(),
        )
        self.logic.save_account_document(doc)
        self.refresh_documents()

    def open_document(self):
        selected = self.document_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a document to open.")
            return
        doc = self.document_map.get(selected[0])
        if not doc or not os.path.exists(doc.file_path):
            messagebox.showerror("Error", "File not found.")
            return
        try:
            if os.name == "nt":
                os.startfile(doc.file_path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.call(["open", doc.file_path])
            else:
                subprocess.call(["xdg-open", doc.file_path])
        except Exception as e:
            messagebox.showerror("Error", f"Unable to open file: {e}")

    def delete_document(self):
        selected = self.document_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a document to delete.")
            return
        doc = self.document_map.get(selected[0])
        if not doc:
            return
        if not messagebox.askyesno("Confirm", "Delete selected document?"):
            return
        self.logic.delete_account_document(doc)
        self.refresh_documents()

    def save_account(self):
        #Gathering account details
        self.active_account.name =  self.name_entry.get()
        self.active_account.phone = self.phone_entry.get()
        self.active_account.website = self.website_entry.get()
        self.active_account.description = self.description_entry.get()

        selected_account_type_str = self.account_type_var.get()
        if selected_account_type_str:
            try:
                self.active_account.account_type = AccountType(selected_account_type_str)
            except ValueError:
                messagebox.showerror("Error", f"Invalid account type: {selected_account_type_str}")
                return
        else:
            self.active_account.account_type = None

        selected_term_name = self.payment_term_var.get()
        if selected_term_name:
            selected_term = next((term for term in self.payment_terms if term.term_name == selected_term_name), None)
            if selected_term:
                self.active_account.payment_term_id = selected_term.term_id
            else:
                self.active_account.payment_term_id = None
        else:
            self.active_account.payment_term_id = None

        selected_rule_name = self.pricing_rule_var.get()
        if selected_rule_name:
            selected_rule = next((rule for rule in self.pricing_rules if rule.rule_name == selected_rule_name), None)
            if selected_rule:
                self.active_account.pricing_rule_id = selected_rule.rule_id
            else:
                self.active_account.pricing_rule_id = None
        else:
            self.active_account.pricing_rule_id = None

        # The addresses are already in self.active_account.addresses
        # so we just need to save the account
        self.logic.save_account(self.active_account)

        self.destroy()

class AddressPopup(PopupBase):
    def __init__(self, master, address=None):
        super().__init__(master)
        self.address = address if address else Address()
        self.title("Address")
        # Add address fields here
        self.street_entry = self._create_entry("Street:", 0, self.address.street)
        self.city_entry = self._create_entry("City:", 1, self.address.city)
        self.state_entry = self._create_entry("State:", 2, self.address.state)
        self.zip_entry = self._create_entry("Zip:", 3, self.address.zip_code)
        self.country_entry = self._create_entry("Country:", 4, self.address.country)

        tk.Label(self, text="Type").grid(row=5, column=0, padx=5, pady=(10, 5))
        tk.Label(self, text="Use").grid(row=5, column=1, padx=5, pady=(10, 5))
        tk.Label(self, text="Primary").grid(row=5, column=2, padx=5, pady=(10, 5))

        self.type_vars: dict[str, tk.BooleanVar] = {}
        self.primary_vars: dict[str, tk.BooleanVar] = {}
        self.primary_checks: dict[str, tk.Checkbutton] = {}
        address_types = ["Billing", "Shipping", "Remittance"]
        current_types = getattr(self.address, 'address_types', [])
        if not current_types and getattr(self.address, 'address_type', ""):
            current_types = [self.address.address_type]
        primary_types = getattr(self.address, 'primary_types', [])
        if not primary_types and getattr(self.address, 'is_primary', False) and getattr(self.address, 'address_type', ""):
            primary_types = [self.address.address_type]
        for i, atype in enumerate(address_types):
            row = 6 + i
            tk.Label(self, text=atype + ":").grid(row=row, column=0, sticky="e", padx=5, pady=2)
            type_var = tk.BooleanVar(value=atype in current_types)
            type_cb = tk.Checkbutton(self, variable=type_var, command=lambda a=atype: self._on_type_toggle(a))
            type_cb.grid(row=row, column=1, padx=5, pady=2)
            primary_var = tk.BooleanVar(value=atype in primary_types)
            primary_cb = tk.Checkbutton(self, variable=primary_var)
            primary_cb.grid(row=row, column=2, padx=5, pady=2)
            if not type_var.get():
                primary_cb.config(state="disabled")
            self.type_vars[atype] = type_var
            self.primary_vars[atype] = primary_var
            self.primary_checks[atype] = primary_cb

        tk.Button(self, text="Save", command=self.save).grid(row=9, column=0, columnspan=3, pady=5)

    def save(self):
        self.address.street = self.street_entry.get()
        self.address.city = self.city_entry.get()
        self.address.state = self.state_entry.get()
        self.address.zip_code = self.zip_entry.get()
        self.address.country = self.country_entry.get()
        selected_types = [t for t, v in self.type_vars.items() if v.get()]
        primary_types = [t for t in selected_types if self.primary_vars[t].get()]
        self.address.address_types = selected_types
        self.address.primary_types = primary_types
        self.address.address_type = selected_types[0] if selected_types else ""
        self.address.is_primary = self.address.address_type in primary_types
        if self.address.is_primary:
            for addr in getattr(self.master, "active_account", Account()).addresses:
                if addr is not self.address and getattr(addr, "address_type", None) == self.address.address_type:
                    addr.is_primary = False
        self.destroy()

    def _on_type_toggle(self, atype):
        if self.type_vars[atype].get():
            self.primary_checks[atype].config(state="normal")
        else:
            self.primary_vars[atype].set(False)
            self.primary_checks[atype].config(state="disabled")
