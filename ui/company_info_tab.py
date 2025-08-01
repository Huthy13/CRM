import tkinter as tk
from tkinter import ttk, messagebox
from shared.structs import CompanyInformation, Address
from core.database import DatabaseHandler # Required for type hinting if logic layer is not fully fleshed out yet.
from shared.utils import ensure_single_primary

class CompanyInfoTab:
    def __init__(self, master, db_handler: DatabaseHandler):
        self.frame = ttk.Frame(master)
        self.db_handler = db_handler
        self.company_info: CompanyInformation | None = None
        self.load_company_data()
        self.setup_ui()

    def load_company_data(self):
        """Loads company information and associated addresses from the database."""
        company_data_dict = self.db_handler.get_company_information()
        if company_data_dict:
            self.company_info = CompanyInformation(
                company_id=company_data_dict.get('company_id'),
                name=company_data_dict.get('name'),
                phone=company_data_dict.get('phone'),
                addresses=[]
            )
            addresses_data = self.db_handler.get_company_addresses(self.company_info.company_id)
            for addr_data in addresses_data:
                address = Address(
                    address_id=addr_data['address_id'],
                    street=addr_data['street'],
                    city=addr_data['city'],
                    state=addr_data['state'],
                    zip_code=addr_data['zip'],
                    country=addr_data['country']
                )
                address.address_type = addr_data['address_type']
                address.is_primary = addr_data['is_primary']
                self.company_info.addresses.append(address)
        else:
            # Initialize with default empty objects if no data found
            self.company_info = CompanyInformation(name="My Company", addresses=[]) # Default name
            self.db_handler.add_company_information(self.company_info.name, "")
            # Reload to get the ID
            self.load_company_data()


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

        # Enforce single primary address
        ensure_single_primary(self.company_info.addresses)

        # Clear existing addresses and add the new ones
        self.db_handler.cursor.execute("DELETE FROM company_addresses WHERE company_id = ?", (self.company_info.company_id,))
        for address in self.company_info.addresses:
            if address.address_id:
                self.db_handler.update_address(address.address_id, address.street, address.city, address.state, address.zip_code, address.country)
                self.db_handler.add_company_address(self.company_info.company_id, address.address_id, address.address_type, address.is_primary)
            else:
                address_id = self.db_handler.add_address(address.street, address.city, address.state, address.zip_code, address.country)
                self.db_handler.add_company_address(self.company_info.company_id, address_id, address.address_type, address.is_primary)

        self.db_handler.update_company_information(
            self.company_info.company_id,
            self.company_info.name,
            self.company_info.phone
        )
        messagebox.showinfo("Success", "Company information updated successfully.")
        self.load_company_data() # Reload to reflect changes and get fresh address objects
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
        tk.Label(self, text="Type:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.type_var = tk.StringVar(self)
        self.type_dropdown = ttk.Combobox(self, textvariable=self.type_var, values=["Billing", "Shipping"], state="readonly", width=37)
        if hasattr(self.address, 'address_type'):
            self.type_dropdown.set(self.address.address_type)
        self.type_dropdown.grid(row=5, column=1, padx=5, pady=5)
        self.primary_var = tk.BooleanVar(value=self.address.is_primary if hasattr(self.address, 'is_primary') else False)
        self.primary_check = tk.Checkbutton(self, text="Primary", variable=self.primary_var)
        self.primary_check.grid(row=6, column=0, columnspan=2)
        tk.Button(self, text="Save", command=self.save).grid(row=7, column=0, columnspan=2)

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
        self.address.address_type = self.type_var.get()
        self.address.is_primary = self.primary_var.get()
        self.destroy()

if __name__ == '__main__':
    # This is example code for testing the tab independently.
    # You'll need to adjust it based on your actual application structure.
    root = tk.Tk()
    root.title("Company Info Tab Test")

    # Create a dummy db_handler for testing
    # In a real app, this would be your actual DatabaseHandler instance
    # For simplicity, we might mock it or use a real one if setup is easy
    try:
        db_handler = DatabaseHandler("test_company_info.db") # Use a test DB
    except Exception as e:
        print(f"Failed to initialize DB Handler for test: {e}")
        db_handler = None # Or a mock object

    if db_handler:
        tab = CompanyInfoTab(root, db_handler)
        tab.frame.pack(expand=True, fill="both")
        root.geometry("600x650") # Adjusted size
    else:
        tk.Label(root, text="Could not initialize DatabaseHandler for testing.").pack()

    root.mainloop()
    if db_handler:
        db_handler.close()
        import os
        # os.remove("test_company_info.db") # Clean up test DB
        print("Test DB closed. Consider removing test_company_info.db manually if needed.")
