import tkinter as tk
from tkinter import ttk, messagebox
from shared.structs import CompanyInformation, Address
from core.database import DatabaseHandler # Required for type hinting if logic layer is not fully fleshed out yet.

class CompanyInfoTab:
    def __init__(self, master, db_handler: DatabaseHandler):
        self.frame = ttk.Frame(master)
        self.db_handler = db_handler
        self.company_info: CompanyInformation | None = None
        self.billing_address: Address | None = None
        self.shipping_address: Address | None = None

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
                billing_address_id=company_data_dict.get('billing_address_id'),
                shipping_address_id=company_data_dict.get('shipping_address_id')
            )
            if self.company_info.billing_address_id:
                addr_dict = self.db_handler.get_address(self.company_info.billing_address_id)
                if addr_dict: # street, city, state, zip, country
                    self.billing_address = Address(address_id=self.company_info.billing_address_id,
                                                   street=addr_dict[0], city=addr_dict[1],
                                                   state=addr_dict[2], zip_code=addr_dict[3], country=addr_dict[4])
            if self.company_info.shipping_address_id:
                addr_dict = self.db_handler.get_address(self.company_info.shipping_address_id)
                if addr_dict:
                    self.shipping_address = Address(address_id=self.company_info.shipping_address_id,
                                                    street=addr_dict[0], city=addr_dict[1],
                                                    state=addr_dict[2], zip_code=addr_dict[3], country=addr_dict[4])
        else:
            # Initialize with default empty objects if no data found
            self.company_info = CompanyInformation(name="My Company") # Default name
            self.db_handler.add_company_information(self.company_info.name, "", None, None)
            # Reload to get the ID
            self.load_company_data()


        if not self.billing_address:
            self.billing_address = Address()
        if not self.shipping_address:
            self.shipping_address = Address()


    def setup_ui(self):
        """Sets up the input fields and buttons for company information."""
        form_frame = ttk.LabelFrame(self.frame, text="Company Details", padding="10")
        form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Company Info Fields
        self.name_entry = self._create_entry(form_frame, "Company Name:", 0, self.company_info.name if self.company_info else "")
        self.phone_entry = self._create_entry(form_frame, "Phone:", 1, self.company_info.phone if self.company_info else "")

        # Billing Address Fields
        billing_frame = ttk.LabelFrame(self.frame, text="Billing Address", padding="10")
        billing_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.billing_street_entry = self._create_entry(billing_frame, "Street:", 0, self.billing_address.street)
        self.billing_city_entry = self._create_entry(billing_frame, "City:", 1, self.billing_address.city)
        self.billing_state_entry = self._create_entry(billing_frame, "State:", 2, self.billing_address.state)
        self.billing_zip_entry = self._create_entry(billing_frame, "Zip Code:", 3, self.billing_address.zip_code)
        self.billing_country_entry = self._create_entry(billing_frame, "Country:", 4, self.billing_address.country)

        # Shipping Address Fields
        shipping_frame = ttk.LabelFrame(self.frame, text="Shipping Address", padding="10")
        shipping_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.same_as_billing_var = tk.BooleanVar()
        self.same_as_billing_checkbox = ttk.Checkbutton(
            shipping_frame, text="Shipping address same as billing",
            variable=self.same_as_billing_var,
            command=self.toggle_shipping_fields
        )
        self.same_as_billing_checkbox.grid(row=0, column=0, columnspan=2, pady=5, sticky="w")

        self.shipping_street_entry = self._create_entry(shipping_frame, "Street:", 1, self.shipping_address.street)
        self.shipping_city_entry = self._create_entry(shipping_frame, "City:", 2, self.shipping_address.city)
        self.shipping_state_entry = self._create_entry(shipping_frame, "State:", 3, self.shipping_address.state)
        self.shipping_zip_entry = self._create_entry(shipping_frame, "Zip Code:", 4, self.shipping_address.zip_code)
        self.shipping_country_entry = self._create_entry(shipping_frame, "Country:", 5, self.shipping_address.country)

        # Initial check for same address (e.g. if both IDs are the same and not None)
        if self.company_info and self.company_info.billing_address_id and self.company_info.billing_address_id == self.company_info.shipping_address_id:
            self.same_as_billing_var.set(True)
            self.toggle_shipping_fields()


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

    def toggle_shipping_fields(self):
        """Enable/disable shipping fields based on checkbox and copy data if checked."""
        if self.same_as_billing_var.get():
            # Copy from billing and disable
            self.shipping_street_entry.delete(0, tk.END)
            self.shipping_street_entry.insert(0, self.billing_street_entry.get())
            self.shipping_street_entry.config(state=tk.DISABLED)

            self.shipping_city_entry.delete(0, tk.END)
            self.shipping_city_entry.insert(0, self.billing_city_entry.get())
            self.shipping_city_entry.config(state=tk.DISABLED)

            self.shipping_state_entry.delete(0, tk.END)
            self.shipping_state_entry.insert(0, self.billing_state_entry.get())
            self.shipping_state_entry.config(state=tk.DISABLED)

            self.shipping_zip_entry.delete(0, tk.END)
            self.shipping_zip_entry.insert(0, self.billing_zip_entry.get())
            self.shipping_zip_entry.config(state=tk.DISABLED)

            self.shipping_country_entry.delete(0, tk.END)
            self.shipping_country_entry.insert(0, self.billing_country_entry.get())
            self.shipping_country_entry.config(state=tk.DISABLED)
        else:
            # Enable fields and clear them (or load original shipping data if available)
            self.shipping_street_entry.config(state=tk.NORMAL)
            self.shipping_street_entry.delete(0, tk.END)
            self.shipping_street_entry.insert(0, self.shipping_address.street if self.shipping_address else "")

            self.shipping_city_entry.config(state=tk.NORMAL)
            self.shipping_city_entry.delete(0, tk.END)
            self.shipping_city_entry.insert(0, self.shipping_address.city if self.shipping_address else "")

            self.shipping_state_entry.config(state=tk.NORMAL)
            self.shipping_state_entry.delete(0, tk.END)
            self.shipping_state_entry.insert(0, self.shipping_address.state if self.shipping_address else "")

            self.shipping_zip_entry.config(state=tk.NORMAL)
            self.shipping_zip_entry.delete(0, tk.END)
            self.shipping_zip_entry.insert(0, self.shipping_address.zip_code if self.shipping_address else "")

            self.shipping_country_entry.config(state=tk.NORMAL)
            self.shipping_country_entry.delete(0, tk.END)
            self.shipping_country_entry.insert(0, self.shipping_address.country if self.shipping_address else "")


    def save_company_information(self):
        """Saves the company information to the database."""
        if not self.company_info or self.company_info.company_id is None:
            messagebox.showerror("Error", "Company data not loaded correctly. Cannot save.")
            return

        # Get billing address details
        billing_street = self.billing_street_entry.get()
        billing_city = self.billing_city_entry.get()
        billing_state = self.billing_state_entry.get()
        billing_zip = self.billing_zip_entry.get()
        billing_country = self.billing_country_entry.get()

        # Save or update billing address
        if self.billing_address and self.billing_address.address_id:
            self.db_handler.update_address(self.billing_address.address_id, billing_street, billing_city, billing_state, billing_zip, billing_country)
            billing_address_id = self.billing_address.address_id
        else:
            billing_address_id = self.db_handler.add_address(billing_street, billing_city, billing_state, billing_zip, billing_country)
        self.company_info.billing_address_id = billing_address_id


        # Get shipping address details
        if self.same_as_billing_var.get():
            shipping_address_id = billing_address_id
        else:
            shipping_street = self.shipping_street_entry.get()
            shipping_city = self.shipping_city_entry.get()
            shipping_state = self.shipping_state_entry.get()
            shipping_zip = self.shipping_zip_entry.get()
            shipping_country = self.shipping_country_entry.get()

            if self.shipping_address and self.shipping_address.address_id and self.shipping_address.address_id != billing_address_id : # Check if it's not the same as billing and exists
                self.db_handler.update_address(self.shipping_address.address_id, shipping_street, shipping_city, shipping_state, shipping_zip, shipping_country)
                shipping_address_id = self.shipping_address.address_id
            elif self.shipping_address and self.shipping_address.address_id and self.shipping_address.address_id == billing_address_id and not (shipping_street == billing_street and shipping_city == billing_city):
                # If it was same as billing, but now different, create new shipping address
                shipping_address_id = self.db_handler.add_address(shipping_street, shipping_city, shipping_state, shipping_zip, shipping_country)
            else: # New shipping address needed
                 shipping_address_id = self.db_handler.add_address(shipping_street, shipping_city, shipping_state, shipping_zip, shipping_country)
        self.company_info.shipping_address_id = shipping_address_id

        # Update company information
        self.company_info.name = self.name_entry.get()
        self.company_info.phone = self.phone_entry.get()

        self.db_handler.update_company_information(
            self.company_info.company_id,
            self.company_info.name,
            self.company_info.phone,
            self.company_info.billing_address_id,
            self.company_info.shipping_address_id
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

        self.billing_street_entry.delete(0, tk.END)
        self.billing_street_entry.insert(0, self.billing_address.street if self.billing_address else "")
        self.billing_city_entry.delete(0, tk.END)
        self.billing_city_entry.insert(0, self.billing_address.city if self.billing_address else "")
        self.billing_state_entry.delete(0, tk.END)
        self.billing_state_entry.insert(0, self.billing_address.state if self.billing_address else "")
        self.billing_zip_entry.delete(0, tk.END)
        self.billing_zip_entry.insert(0, self.billing_address.zip_code if self.billing_address else "")
        self.billing_country_entry.delete(0, tk.END)
        self.billing_country_entry.insert(0, self.billing_address.country if self.billing_address else "")

        if self.company_info and self.company_info.billing_address_id and self.company_info.billing_address_id == self.company_info.shipping_address_id:
            self.same_as_billing_var.set(True)
        else:
            self.same_as_billing_var.set(False)
        self.toggle_shipping_fields() # This will also populate shipping fields correctly

        if not self.same_as_billing_var.get():
            self.shipping_street_entry.delete(0, tk.END)
            self.shipping_street_entry.insert(0, self.shipping_address.street if self.shipping_address else "")
            self.shipping_city_entry.delete(0, tk.END)
            self.shipping_city_entry.insert(0, self.shipping_address.city if self.shipping_address else "")
            self.shipping_state_entry.delete(0, tk.END)
            self.shipping_state_entry.insert(0, self.shipping_address.state if self.shipping_address else "")
            self.shipping_zip_entry.delete(0, tk.END)
            self.shipping_zip_entry.insert(0, self.shipping_address.zip_code if self.shipping_address else "")
            self.shipping_country_entry.delete(0, tk.END)
            self.shipping_country_entry.insert(0, self.shipping_address.country if self.shipping_address else "")

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
