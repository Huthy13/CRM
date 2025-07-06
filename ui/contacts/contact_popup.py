import tkinter as tk
from tkinter import ttk, messagebox
from shared.structs import Contact  # Import Contact
from core.address_book_logic import AddressBookLogic # Assuming this is how logic is passed

NO_ACCOUNT_LABEL = "<No Account>"

class ContactDetailsPopup(tk.Toplevel):
    def __init__(self, master_window, contact_tab_controller, logic: AddressBookLogic, contact_id=None):
        self.contact_tab_controller = contact_tab_controller
        super().__init__(master_window)
        self.logic = logic
        self.contact_id = contact_id
        self.title(f"{'Edit' if contact_id else 'Add'} Contact")
        self.geometry("400x250")

        self.contact_data = None # To store loaded contact data if editing

        # --- UI Elements ---
        tk.Label(self, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = tk.Entry(self, width=40)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self, text="Phone:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.phone_entry = tk.Entry(self, width=40)
        self.phone_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self, text="Email:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.email_entry = tk.Entry(self, width=40)
        self.email_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(self, text="Role:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.role_entry = tk.Entry(self, width=40)
        self.role_entry.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(self, text="Account:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.account_combobox = ttk.Combobox(self, width=37, state="readonly")
        self.account_combobox.grid(row=4, column=1, padx=5, pady=5)
        self.populate_accounts_dropdown()

        # Save and Cancel Buttons
        self.save_button = tk.Button(self, text="Save", command=self.save_contact)
        self.save_button.grid(row=5, column=0, padx=5, pady=10, sticky="e")

        self.cancel_button = tk.Button(self, text="Cancel", command=self.destroy)
        self.cancel_button.grid(row=5, column=1, padx=5, pady=10, sticky="w")

        if self.contact_id:
            self.load_contact_details()

    def populate_accounts_dropdown(self):
        accounts_data = self.logic.get_all_accounts()  # Expected: list of (id, name, phone, desc) tuples

        self.account_map = {}  # Stores name: id
        account_names_for_list = []

        if accounts_data: # Check if accounts_data is not None and not empty
            for account_item in accounts_data:
                if len(account_item) >= 2: # Ensure item has at least id and name
                    acc_id = account_item[0]    # ID is the first element
                    acc_name = account_item[1]  # Name is the second element
                    self.account_map[acc_name] = acc_id
                    account_names_for_list.append(acc_name)
                else:
                    # Handle unexpected item structure, e.g., log a warning
                    print(f"Warning: Unexpected account item structure: {account_item}")

        # Sort account names alphabetically for consistent order in dropdown
        sorted_account_names = sorted(account_names_for_list)

        # Prepend the "No Account" option
        display_values = [NO_ACCOUNT_LABEL] + sorted_account_names

        self.account_combobox['values'] = display_values

        # Set default combobox value to NO_ACCOUNT_LABEL if it's a new contact (contact_id is None)
        # This check should ideally be done once after initial population.
        # If load_contact_details runs later for an existing contact, it will override this.
        if self.contact_id is None:
            self.account_combobox.set(NO_ACCOUNT_LABEL)

    def load_contact_details(self):
        # This method needs to be implemented in address_book_logic.py
        # For now, assume it returns a dictionary or a Contact object
        contact_details = self.logic.get_contact_details(self.contact_id)
        if contact_details:
            self.contact_data = contact_details # Store for saving
            self.name_entry.insert(0, contact_details.name if contact_details.name else "")
            self.phone_entry.insert(0, contact_details.phone if contact_details.phone else "")
            self.email_entry.insert(0, contact_details.email if contact_details.email else "")
            self.role_entry.insert(0, contact_details.role if contact_details.role else "")

            # Set combobox
            account_id = contact_details.account_id # This line was from the previous plan for attribute access
            if account_id is None:
                self.account_combobox.set(NO_ACCOUNT_LABEL)
            else:
                # Find the account name for the given account_id
                account_name_to_set = None
                for name, id_val in self.account_map.items():
                    if id_val == account_id:
                        account_name_to_set = name
                        break
                if account_name_to_set:
                    self.account_combobox.set(account_name_to_set)
                else:
                    # Account ID exists but not in map, or map is empty.
                    # Set to "No Account" as a fallback.
                    self.account_combobox.set(NO_ACCOUNT_LABEL)
                    # Optionally, log a warning if an account_id is present but not found in the map.
                    print(f"Warning: Contact has account_id {account_id} but it was not found in the available accounts. Setting to '{NO_ACCOUNT_LABEL}'.")
        else:
            messagebox.showerror("Error", f"Could not load details for contact ID: {self.contact_id}")
            self.destroy()

    def save_contact(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        email = self.email_entry.get().strip()
        role = self.role_entry.get().strip()

        if not name:
            messagebox.showerror("Validation Error", "Name cannot be empty.")
            return

        selected_account_display_name = self.account_combobox.get() # Get current value from combobox

        if not selected_account_display_name or selected_account_display_name == NO_ACCOUNT_LABEL:
            account_id = None
        else:
            account_id = self.account_map.get(selected_account_display_name)
            # If account_id is not found in the map (e.g. map is empty or bad data),
            # account_id will be None here. This is acceptable for an optional account.
            if account_id is None:
                 print(f"Warning: Account name '{selected_account_display_name}' selected in combobox but not found in account_map. Treating as no account.")

        contact_obj = Contact(
            contact_id=self.contact_id, # Will be None for new contacts
            name=name,
            phone=phone,
            email=email,
            role=role,
            account_id=account_id
        )

        # This method needs to be implemented in address_book_logic.py
        # It should handle both adding a new contact and updating an existing one
        try:
            self.logic.save_contact(contact_obj)
            messagebox.showinfo("Success", "Contact saved successfully!")
            self.contact_tab_controller.refresh_contacts_list() # Assuming the master view has this method
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save contact: {e}")

if __name__ == '__main__':
    # This is for testing purposes
    class MockLogic:
        def get_all_accounts(self):
            print("Mock: get_all_accounts called")
            return [(1, "Account Alpha"), (2, "Account Beta"), (3, "Account Gamma")]

        def get_contact_details(self, contact_id):
            print(f"Mock: get_contact_details called for ID: {contact_id}")
            if contact_id == 1:
                # Ensure this mock return matches the structure expected by load_contact_details
                # It should be a Contact object if logic.get_contact_details returns an object
                # For now, assuming it's a dict-like object or an object with attributes
                mock_contact = Contact(contact_id=1, name="Test User", phone="1234567890", email="test@example.com", account_id=2)
                return mock_contact
            return None

        def save_contact(self, contact):
            print(f"Mock: save_contact called with: {contact.name if contact else 'None'}") # Updated to access name attribute

    class MockMaster(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Mock Master")
            self.geometry("200x100")
            # These buttons are for testing the popup directly, so they might need a mock contact_tab_controller
            # For simplicity, I'm omitting a full mock controller here.
            tk.Button(self, text="Open Add Contact", command=self.open_add_contact).pack(pady=5)
            tk.Button(self, text="Open Edit Contact", command=self.open_edit_contact).pack(pady=5)

        def open_add_contact(self):
            # A mock contact_tab_controller would be needed if refresh_contacts_list is called.
            mock_controller = self # Or a more dedicated mock
            popup = ContactDetailsPopup(self, mock_controller, MockLogic())
            self.wait_window(popup)

        def open_edit_contact(self):
            mock_controller = self # Or a more dedicated mock
            popup = ContactDetailsPopup(self, mock_controller, MockLogic(), contact_id=1) # example contact_id
            self.wait_window(popup)

        def refresh_contacts_list(self):
            print("MockMaster: refresh_contacts_list called")

    app = MockMaster()
    app.mainloop()
