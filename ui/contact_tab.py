import tkinter as tk
from tkinter import messagebox, ttk
from ui.contact_popup import ContactDetailsPopup # Renamed file, relative import
# Import Contact if needed for type hinting, though logic layer currently returns Contact objects
from shared.structs import Contact # Moved to shared package

class ContactTab:
    def __init__(self, master, logic):
        self.frame = tk.Frame(master)
        self.logic = logic
        self.selected_contact_id = None

        self.setup_contact_tab()
        self.load_contacts()

        # Consider binding to a more appropriate event if FocusIn causes too frequent reloads
        # Or implement a specific refresh button if preferred.
        self.frame.bind("<FocusIn>", self.load_contacts)

    def setup_contact_tab(self):
        tk.Label(self.frame, text="Contact Management").grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        button_width = 20
        button_frame = tk.Frame(self.frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=5)

        self.add_contact_button = tk.Button(
            button_frame, text="Add New Contact",
            command=self.create_new_contact, width=button_width)
        self.add_contact_button.pack(side=tk.LEFT, padx=5)

        self.edit_contact_button = tk.Button(
            button_frame, text="Edit Contact",
            command=self.edit_existing_contact, width=button_width)
        self.edit_contact_button.pack(side=tk.LEFT, padx=5)

        self.remove_contact_button = tk.Button(
            button_frame, text="Remove Contact",
            command=self.remove_contact, width=button_width)
        self.remove_contact_button.pack(side=tk.LEFT, padx=5)

        # Treeview for displaying contacts
        # Columns: "id" (hidden), "name", "phone", "email", "role", "account_name"
        self.tree = ttk.Treeview(self.frame, columns=("id", "name", "phone", "email", "role", "account_name"), show="headings")

        self.tree.column("id", width=0, stretch=False) # Hidden ID column
        self.tree.heading("name", text="Contact Name", command=lambda: self.sort_column("name", False))
        self.tree.heading("phone", text="Phone", command=lambda: self.sort_column("phone", False))
        self.tree.heading("email", text="Email", command=lambda: self.sort_column("email", False))
        self.tree.heading("role", text="Role", command=lambda: self.sort_column("role", False))
        self.tree.heading("account_name", text="Account", command=lambda: self.sort_column("account_name", False))

        self.tree.column("name", width=150, anchor=tk.W)
        self.tree.column("phone", width=100, anchor=tk.W)
        self.tree.column("email", width=180, anchor=tk.W)
        self.tree.column("role", width=100, anchor=tk.W)
        self.tree.column("account_name", width=120, anchor=tk.W)

        self.tree.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.on_contact_select)

    def sort_column(self, col, reverse):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try: # Attempt numeric sort for relevant columns if possible, else string sort
            data.sort(key=lambda item: float(item[0]), reverse=reverse)
        except ValueError:
            data.sort(key=lambda item: str(item[0]).lower(), reverse=reverse)

        for index, (val, k) in enumerate(data):
            self.tree.move(k, "", index)
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def on_contact_select(self, event=None):
        selected_items = self.tree.selection()
        if selected_items:
            # item_id is the contact_id because we set iid=contact_id during insert
            self.selected_contact_id = selected_items[0]
        else:
            self.selected_contact_id = None

    def remove_contact(self):
        if not self.selected_contact_id:
            messagebox.showwarning("No Selection", "Please select a contact to delete.")
            return

        # Step 1: Capture the selected ID into a new local variable immediately.
        id_to_process = self.selected_contact_id

        # Step 2: Use this captured ID in the confirmation dialog.
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the selected contact (ID: {id_to_process})?"
        )

        if confirm:
            try:
                # Step 3: Use the captured ID for the deletion logic.
                self.logic.delete_contact(id_to_process)

                # Step 4: Refresh the contact list.
                self.load_contacts()

                # Step 5: Use the captured ID in the success message.
                messagebox.showinfo(
                    "Success",
                    f"Contact (ID: {id_to_process}) deleted successfully."
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete contact: {e}")

            # Step 6: Reset selection (safeguard, as load_contacts should also do it).
            self.selected_contact_id = None

    def edit_existing_contact(self):
        if not self.selected_contact_id:
            messagebox.showwarning("No Selection", "Please select a contact to edit.")
            return
        # The ContactDetailsPopup now handles fetching the contact details by ID
        popup = ContactDetailsPopup(self.frame.master, self, self.logic, contact_id=self.selected_contact_id)
        self.frame.master.wait_window(popup) # Wait for popup to close
        self.load_contacts() # Refresh list after potential edit

    def create_new_contact(self):
        popup = ContactDetailsPopup(self.frame.master, self, self.logic, contact_id=None)
        self.frame.master.wait_window(popup)
        self.load_contacts()

    def load_contacts(self, event=None): # event parameter for binding
        self.tree.delete(*self.tree.get_children())
        self.selected_contact_id = None # Reset selection

        try:
            contacts = self.logic.get_all_contacts() # Returns list of Contact objects
            for contact in contacts:
                account_name_display = "N/A"
                if contact.account_id:
                    account = self.logic.get_account_details(contact.account_id)
                    if account:
                        account_name_display = account.name

                self.tree.insert("", "end", iid=contact.contact_id, values=(
                    contact.contact_id, # Stored in hidden "id" column, accessed by iid
                    contact.name,
                    contact.phone,
                    contact.email,
                    contact.role,
                    account_name_display
                ))
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load contacts: {e}")
            print(f"Error in load_contacts: {e}") # For console debugging

    def refresh_contacts_list(self): # Added method for popup to call
        self.load_contacts()

# Example of how to integrate into a main application (for testing)
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Contact Management Tab Test")

    # Mock Logic class for testing
    class MockLogic:
        def get_all_contacts(self):
            print("MockLogic: get_all_contacts called")
            # Simulate Contact objects (or dicts if logic layer changes)
            # from src.structs import Contact # Already imported above or ensure it's available
            return [
                Contact(contact_id=1, name="John Doe", phone="123-456-7890", email="john.doe@example.com", account_id=101),
                Contact(contact_id=2, name="Jane Smith", phone="987-654-3210", email="jane.smith@example.com", account_id=102),
                Contact(contact_id=3, name="Alice Brown", phone="555-555-5555", email="alice.brown@example.com", account_id=101)
            ]

        def get_account_details(self, account_id):
            print(f"MockLogic: get_account_details called for {account_id}")
            from shared.structs import Account # For mock objects
            if account_id == 101:
                return Account(account_id=101, name="Alpha Corp")
            if account_id == 102:
                return Account(account_id=102, name="Beta LLC")
            return None

        def delete_contact(self, contact_id):
            print(f"MockLogic: delete_contact called for {contact_id}")
            messagebox.showinfo("Mock Delete", f"Contact {contact_id} would be deleted.")
            return True # Simulate success

        def get_contact_details(self, contact_id): # Needed by ContactDetailsPopup
            print(f"MockLogic: get_contact_details called for {contact_id}")
            # from src.structs import Contact # Already imported above or ensure it's available
            if contact_id == 1:
                 return Contact(contact_id=1, name="John Doe", phone="123-456-7890", email="john.doe@example.com", account_id=101)
            return None

        def save_contact(self, contact): # Needed by ContactDetailsPopup
            print(f"MockLogic: save_contact called for {contact.name if contact else 'None'}")

        def get_all_accounts(self): # Needed by ContactDetailsPopup
            print("MockLogic: get_all_accounts called")
            return [(101, "Alpha Corp"), (102, "Beta LLC")]


    mock_logic = MockLogic()
    app_tab = ContactTab(root, mock_logic)
    app_tab.frame.pack(expand=True, fill=tk.BOTH)
    root.geometry("700x400")
    root.mainloop()
