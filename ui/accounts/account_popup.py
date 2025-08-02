import tkinter as tk
from tkinter import messagebox, ttk  # Import ttk
from shared.structs import Address, Account, AccountType  # Import AccountType
from ui.base.popup_base import PopupBase

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

        # Pricing Rule Dropdown
        tk.Label(self, text="Pricing Rule:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.pricing_rule_var = tk.StringVar(self)
        self.pricing_rule_dropdown = ttk.Combobox(self, textvariable=self.pricing_rule_var, state="disabled", width=37)
        self.pricing_rule_dropdown.grid(row=5, column=1, padx=5, pady=5)
        self.load_pricing_rules()
        self.toggle_pricing_rule_dropdown()


        # Addresses Frame
        addresses_frame = tk.LabelFrame(self, text="Addresses")
        addresses_frame.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

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

        # Save Button
        save_button = tk.Button(self, text="Save", command=self.save_account)
        save_button.grid(row=18, column=0, columnspan=2, pady=10)

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
            self.address_tree.insert(
                "",
                "end",
                values=(
                    addr.address_type,
                    "true" if getattr(addr, "is_primary", False) else "false",
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
            if not hasattr(address_popup.address, 'address_type'):
                address_popup.address.address_type = ''
            if not hasattr(address_popup.address, 'is_primary'):
                address_popup.address.is_primary = False
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
        tk.Label(self, text="Type:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.type_var = tk.StringVar(self)
        self.type_dropdown = ttk.Combobox(
            self,
            textvariable=self.type_var,
            values=["Billing", "Shipping", "Remittance"],
            state="readonly",
            width=37,
        )
        if hasattr(self.address, 'address_type'):
            self.type_dropdown.set(self.address.address_type)
        self.type_dropdown.grid(row=5, column=1, padx=5, pady=5)
        self.primary_var = tk.BooleanVar(value=self.address.is_primary if hasattr(self.address, 'is_primary') else False)
        self.primary_check = tk.Checkbutton(self, text="Primary", variable=self.primary_var)
        self.primary_check.grid(row=6, column=0, columnspan=2)
        tk.Button(self, text="Save", command=self.save).grid(row=7, column=0, columnspan=2)

    def save(self):
        self.address.street = self.street_entry.get()
        self.address.city = self.city_entry.get()
        self.address.state = self.state_entry.get()
        self.address.zip_code = self.zip_entry.get()
        self.address.country = self.country_entry.get()
        self.address.address_type = self.type_var.get()
        self.address.is_primary = self.primary_var.get()
        if self.address.is_primary:
            for addr in getattr(self.master, "active_account", Account()).addresses:
                if addr is not self.address and getattr(addr, "address_type", None) == self.address.address_type:
                    addr.is_primary = False
        self.destroy()
