import tkinter as tk
from tkinter import messagebox
from shared.structs import Address, Account

class AccountDetailsPopup(tk.Toplevel):
    def __init__(self, master, logic, account_id=None):
        super().__init__(master)
        self.logic = logic
        self.account_id = account_id

        if self.account_id == None:
            self.active_account = Account()
            self.billing_address = Address()
            self.shipping_address = Address()
        else:
            self.active_account = self.logic.get_account_details(self.account_id)
            self.billing_address = self.logic.get_address_obj(self.active_account.billing_address_id)
            self.shipping_address = self.logic.get_address_obj(self.active_account.shipping_address_id)

        # Account details Fields
        self.name_entry = self._create_entry("Account Name:", 0, self.active_account.name)
        self.phone_entry = self._create_entry("Phone:", 1, self.active_account.phone)
        self.website_entry = self._create_entry("Website:", 2, self.active_account.website)
        self.description_entry = self._create_entry("Description:", 3, self.active_account.description)

        # Billing Address Fields
        tk.Label(self, text="Billing Address").grid(row=4, column=0, columnspan=2)
        self.billing_street_entry = self._create_entry("Street:", 5, self.billing_address.street)
        self.billing_city_entry = self._create_entry("City:", 6, self.billing_address.city)
        self.billing_state_entry = self._create_entry("State:", 7, self.billing_address.state)
        self.billing_zip_entry = self._create_entry("Zip:", 8, self.billing_address.zip_code)
        self.billing_country_entry = self._create_entry("Country:", 9, self.billing_address.country)

        self.same_as_billing_stat = tk.BooleanVar(value = self.active_account.is_billing_same_as_shipping())

        # Checkbox for "Same as Billing"
        self.same_as_billing_checkbox = tk.Checkbutton(
            self, text="Shipping address same as billing", 
            variable=self.same_as_billing_stat, 
            command=self.toggle_shipping_fields
        )
        self.same_as_billing_checkbox.grid(row=10, column=0, columnspan=2, pady=5)

        # Shipping Address Fields
        self.shipping_street_entry = self._create_entry("Street:", 12, self.shipping_address.street)
        self.shipping_city_entry = self._create_entry("City:", 13, self.shipping_address.city)
        self.shipping_state_entry = self._create_entry("State:", 14, self.shipping_address.state)
        self.shipping_zip_entry = self._create_entry("Zip:", 15, self.shipping_address.zip_code)
        self.shipping_country_entry = self._create_entry("Country:", 16, self.shipping_address.country)

        if self.same_as_billing_stat.get():
            self._copy_billing_to_shipping_and_disable()

        # Save Button
        save_button = tk.Button(self, text="Save", command=self.save_account)
        save_button.grid(row=17, column=0, columnspan=2, pady=10)

    def save_account(self):

        #Gathering account details
        self.active_account.name =  self.name_entry.get()
        self.active_account.phone = self.phone_entry.get()
        self.active_account.website = self.website_entry.get()
        self.active_account.description = self.description_entry.get()

        #Gathering billing address
        self.active_account.billing_address_id = self.logic.add_address(
            self.billing_street_entry.get(),
            self.billing_city_entry.get(),
            self.billing_state_entry.get(),
            self.billing_zip_entry.get(),
            self.billing_country_entry.get())

        #Gathering shipping address
        if  self.same_as_billing_stat.get():
            self.active_account.shipping_address_id = self.active_account.billing_address_id
        else:
            self.active_account.shipping_address_id = self.logic.add_address(
            self.shipping_street_entry.get(),
            self.shipping_city_entry.get(),
            self.shipping_state_entry.get(),
            self.shipping_zip_entry.get(),
            self.shipping_country_entry.get())

        #actually save data to DB
        self.logic.save_account(self.active_account)    

        self.destroy()

    def _create_entry(self, label_text, row, initial_value=""):
        label = tk.Label(self, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky="e")
        entry = tk.Entry(self, width=40)
        entry.insert(0, initial_value if initial_value is not None else "")
        entry.grid(row=row, column=1, padx=5, pady=5)
        return entry

    def toggle_shipping_fields(self):
        if self.same_as_billing_stat.get():
            self._copy_billing_to_shipping_and_disable()
            self.active_account.shipping_address_id = self.active_account.billing_address_id
        else:
            self.active_account.shipping_address_id = Address()
            for widget in [self.shipping_street_entry, self.shipping_city_entry, 
                           self.shipping_state_entry, self.shipping_zip_entry, 
                           self.shipping_country_entry]:
                widget.config(state=tk.NORMAL)


    def _copy_billing_to_shipping_and_disable(self):
        
        #clear text in fields
        self.shipping_street_entry.delete(0, tk.END)
        self.shipping_city_entry.delete(0, tk.END)
        self.shipping_state_entry.delete(0, tk.END)
        self.shipping_zip_entry.delete(0, tk.END)
        self.shipping_country_entry.delete(0, tk.END)
        
        #copy text from billing into fields
        self.shipping_street_entry.insert(0, self.billing_street_entry.get())
        self.shipping_city_entry.insert(0, self.billing_city_entry.get())
        self.shipping_state_entry.insert(0, self.billing_state_entry.get())
        self.shipping_zip_entry.insert(0, self.billing_zip_entry.get())
        self.shipping_country_entry.insert(0,  self.billing_country_entry.get())

        for widget in [self.shipping_street_entry, self.shipping_city_entry,
                    self.shipping_state_entry, self.shipping_zip_entry, 
                    self.shipping_country_entry]:
            widget.config(state=tk.DISABLED)
