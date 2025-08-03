import tkinter as tk
from tkinter import ttk, messagebox
from shared.structs import CompanyInformation, Address
from core.company_service import CompanyService

class CompanyInfoTab:
    def __init__(self, master, service: CompanyService):
        self.frame = ttk.Frame(master)
        self.service = service
        self.company_info: CompanyInformation | None = None
        self.load_company_data()
        self.setup_ui()

    def load_company_data(self):
        """Loads company information using the service layer."""
        self.company_info = self.service.load_company_information()


    def setup_ui(self):
        """Sets up the input fields and buttons for company information."""
        form_frame = ttk.LabelFrame(self.frame, text="Company Details", padding="10")
        form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Company Info Fields
        self.name_entry = self._create_entry(form_frame, "Company Name:", 0, self.company_info.name if self.company_info else "")
        self.phone_entry = self._create_entry(form_frame, "Phone:", 1, self.company_info.phone if self.company_info else "")

        # Addresses Frame
        addresses_frame = ttk.LabelFrame(self.frame, text="Addresses", padding="10")
        addresses_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.address_tree = ttk.Treeview(addresses_frame, columns=("type", "primary", "address"), show="headings")
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
        save_button = ttk.Button(self.frame, text="Save Company Information", command=self.save_company_information)
        save_button.grid(row=3, column=0, padx=10, pady=20, sticky="ew")

        self.frame.columnconfigure(0, weight=1)


    def _create_entry(self, parent, label_text, row_num, initial_value=""):
        label = ttk.Label(parent, text=label_text)
        label.grid(row=row_num, column=0, padx=5, pady=5, sticky="w")
        entry = ttk.Entry(parent, width=40)
        entry.insert(0, initial_value if initial_value is not None else "")
        entry.grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
        parent.columnconfigure(1, weight=1) # Make entry field expand
        return entry

    def populate_address_tree(self):
        for i in self.address_tree.get_children():
            self.address_tree.delete(i)
        if self.company_info and hasattr(self.company_info, 'addresses'):
            for i, addr in enumerate(self.company_info.addresses):
                address_str = f"{addr.street}, {addr.city}, {addr.state} {addr.zip_code}, {addr.country}"
                self.address_tree.insert("", "end", values=(addr.address_type, addr.is_primary, address_str), iid=i)

    def add_address(self):
        address_popup = AddressPopup(self.frame)
        self.frame.wait_window(address_popup)
        if hasattr(address_popup, 'address'):
            if not hasattr(address_popup.address, 'address_id'):
                address_popup.address.address_id = None
            if not hasattr(address_popup.address, 'address_type'):
                address_popup.address.address_type = ''
            if not hasattr(address_popup.address, 'is_primary'):
                address_popup.address.is_primary = False
            self.company_info.addresses.append(address_popup.address)
            self.populate_address_tree()

    def edit_address(self):
        selected_item = self.address_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select an address to edit.")
            return

        index = int(selected_item[0])
        address = self.company_info.addresses[index]
        address_popup = AddressPopup(self.frame, address)
        self.frame.wait_window(address_popup)
        self.populate_address_tree()

    def delete_address(self):
        selected_item = self.address_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select an address to delete.")
            return

        index = int(selected_item[0])
        del self.company_info.addresses[index]
        self.populate_address_tree()

    def save_company_information(self):
        """Saves the company information to the database."""
        if not self.company_info or self.company_info.company_id is None:
            messagebox.showerror("Error", "Company data not loaded correctly. Cannot save.")
            return

        # Update company information
        self.company_info.name = self.name_entry.get()
        self.company_info.phone = self.phone_entry.get()

        self.service.save_company_information(self.company_info)
        messagebox.showinfo("Success", "Company information updated successfully.")
        self.load_company_data()  # Reload to reflect changes and get fresh address objects
        self.refresh_ui_fields()

    def refresh_ui_fields(self):
        """Refreshes the UI fields with the current data."""
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, self.company_info.name if self.company_info else "")
        self.phone_entry.delete(0, tk.END)
        self.phone_entry.insert(0, self.company_info.phone if self.company_info else "")
        self.populate_address_tree()

class AddressPopup(tk.Toplevel):
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
        current_type = getattr(self.address, 'address_type', "")
        is_primary = getattr(self.address, 'is_primary', False)
        for i, atype in enumerate(address_types):
            row = 6 + i
            tk.Label(self, text=atype + ":").grid(row=row, column=0, sticky="e", padx=5, pady=2)
            type_var = tk.BooleanVar(value=current_type == atype)
            type_cb = tk.Checkbutton(self, variable=type_var, command=lambda a=atype: self._on_type_select(a))
            type_cb.grid(row=row, column=1, padx=5, pady=2)
            primary_var = tk.BooleanVar(value=current_type == atype and is_primary)
            primary_cb = tk.Checkbutton(self, variable=primary_var)
            primary_cb.grid(row=row, column=2, padx=5, pady=2)
            if not type_var.get():
                primary_cb.config(state="disabled")
            self.type_vars[atype] = type_var
            self.primary_vars[atype] = primary_var
            self.primary_checks[atype] = primary_cb

        tk.Button(self, text="Save", command=self.save).grid(row=9, column=0, columnspan=3, pady=5)

    def _create_entry(self, label_text, row, initial_value=""):
        label = tk.Label(self, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky="e")
        entry = tk.Entry(self, width=40)
        entry.insert(0, initial_value if initial_value is not None else "")
        entry.grid(row=row, column=1, padx=5, pady=5)
        return entry

    def save(self):
        self.address.street = self.street_entry.get()
        self.address.city = self.city_entry.get()
        self.address.state = self.state_entry.get()
        self.address.zip_code = self.zip_entry.get()
        self.address.country = self.country_entry.get()
        selected_type = next((t for t, v in self.type_vars.items() if v.get()), "")
        self.address.address_type = selected_type
        self.address.is_primary = self.primary_vars.get(selected_type, tk.BooleanVar(value=False)).get()
        self.destroy()

    def _on_type_select(self, selected):
        for atype, var in self.type_vars.items():
            if atype != selected:
                var.set(False)
                self.primary_vars[atype].set(False)
                self.primary_checks[atype].config(state="disabled")
            else:
                if var.get():
                    self.primary_checks[atype].config(state="normal")
                else:
                    self.primary_vars[atype].set(False)
                    self.primary_checks[atype].config(state="disabled")

if __name__ == '__main__':
    # This is example code for testing the tab independently.
    # You'll need to adjust it based on your actual application structure.
    root = tk.Tk()
    root.title("Company Info Tab Test")

    # Create dummy services for testing
    from core.database import DatabaseHandler
    from core.repositories import AddressRepository, AccountRepository
    from core.address_service import AddressService
    from core.company_repository import CompanyRepository

    try:
        db_handler = DatabaseHandler("test_company_info.db")  # Use a test DB
        address_service = AddressService(AddressRepository(db_handler), AccountRepository(db_handler))
        company_service = CompanyService(CompanyRepository(db_handler), address_service)
        tab = CompanyInfoTab(root, company_service)
        tab.frame.pack(expand=True, fill="both")
        root.geometry("600x650")  # Adjusted size
    except Exception as e:
        tk.Label(root, text=f"Could not initialize services: {e}").pack()
        db_handler = None

    root.mainloop()
    if db_handler:
        db_handler.close()
        import os
        print("Test DB closed. Consider removing test_company_info.db manually if needed.")
