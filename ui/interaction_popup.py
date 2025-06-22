import tkinter as tk
from tkinter import ttk, messagebox
from core.logic import AddressBookLogic
from shared.structs import Interaction, InteractionType
import datetime

class InteractionPopup(tk.Toplevel):
    def __init__(self, parent, logic: AddressBookLogic, selected_account_id=None, selected_contact_id=None, success_callback=None):
        super().__init__(parent)
        self.logic = logic
        self.title("New Interaction")
        self.geometry("550x500") # Adjusted size
        self.transient(parent) # Keep popup on top of parent
        self.grab_set() # Modal behavior

        self.success_callback = success_callback # To refresh parent tab if needed

        self.selected_account_id = selected_account_id
        self.selected_contact_id = selected_contact_id

        self.accounts_map = {}
        self.contacts_map = {}

        self.interaction_type_var = tk.StringVar()
        self.date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d")) # Default to today
        self.time_var = tk.StringVar(value=datetime.datetime.now().strftime("%H:%M")) # Default to now
        self.subject_var = tk.StringVar()
        # Description will use a Text widget, no StringVar needed for the main content

        self._setup_widgets()
        self._load_dropdown_data()

        # Pre-select account/contact if passed
        if self.selected_account_id:
            for name, acc_id in self.accounts_map.items():
                if acc_id == self.selected_account_id:
                    self.account_combobox.set(name)
                    break

        if self.selected_contact_id:
            for name, con_id in self.contacts_map.items():
                if con_id == self.selected_contact_id:
                    self.contact_combobox.set(name)
                    break


    def _setup_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill="both")

        # Interaction Type
        ttk.Label(main_frame, text="Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.type_combobox = ttk.Combobox(main_frame, textvariable=self.interaction_type_var,
                                          values=[it.value for it in InteractionType], state="readonly")
        self.type_combobox.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        if self.type_combobox['values']: # Select first type by default
             self.type_combobox.current(0)


        # Date
        ttk.Label(main_frame, text="Date (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.date_entry = ttk.Entry(main_frame, textvariable=self.date_var, width=12)
        self.date_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Time
        ttk.Label(main_frame, text="Time (HH:MM):").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.time_entry = ttk.Entry(main_frame, textvariable=self.time_var, width=8)
        self.time_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        # Account (Company) Selection
        ttk.Label(main_frame, text="Account (Company):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.account_combobox = ttk.Combobox(main_frame, state="readonly", width=40)
        self.account_combobox.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        self.account_combobox.bind("<<ComboboxSelected>>", self._on_account_selected_popup)


        # Contact Selection
        ttk.Label(main_frame, text="Contact:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.contact_combobox = ttk.Combobox(main_frame, state="readonly", width=40)
        self.contact_combobox.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        self.contact_combobox.bind("<<ComboboxSelected>>", self._on_contact_selected_popup)


        # Subject
        ttk.Label(main_frame, text="Subject:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.subject_entry = ttk.Entry(main_frame, textvariable=self.subject_var)
        self.subject_entry.grid(row=4, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Description
        ttk.Label(main_frame, text="Description:").grid(row=5, column=0, padx=5, pady=5, sticky="nw")
        self.description_text = tk.Text(main_frame, height=8, width=50)
        self.description_text.grid(row=5, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        # Buttons Frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=6, column=0, columnspan=4, pady=10)

        self.save_button = ttk.Button(buttons_frame, text="Save", command=self._save_interaction)
        self.save_button.pack(side="left", padx=5)

        self.cancel_button = ttk.Button(buttons_frame, text="Cancel", command=self.destroy)
        self.cancel_button.pack(side="left", padx=5)

        main_frame.columnconfigure(1, weight=1) # Allow entry fields to expand a bit
        main_frame.columnconfigure(3, weight=1)


    def _load_dropdown_data(self):
        # Load Accounts
        self.accounts_map = {}
        accounts_data = self.logic.get_accounts() # Returns (id, name)
        account_names = []
        if accounts_data:
            for acc_id, acc_name in accounts_data:
                display_name = f"{acc_name} (ID: {acc_id})"
                account_names.append(display_name)
                self.accounts_map[display_name] = acc_id
        self.account_combobox['values'] = [""] + account_names # Add blank option

        # Load Contacts
        self.contacts_map = {}
        contacts_data = self.logic.get_all_contacts() # Returns list of Contact objects
        contact_names = []
        if contacts_data:
            for contact in contacts_data:
                display_name = f"{contact.name} (ID: {contact.contact_id})"
                contact_names.append(display_name)
                self.contacts_map[display_name] = contact.contact_id
        self.contact_combobox['values'] = [""] + contact_names # Add blank option

    def _on_account_selected_popup(self, event=None):
        # If an account is selected, we might want to clear the contact or filter contacts.
        # For now, just ensure it's a valid selection.
        # If we automatically select a contact, we'd need more complex logic.
        pass # No action needed to clear the other dropdown for now in popup

    def _on_contact_selected_popup(self, event=None):
        # If a contact is selected, we might want to auto-populate the account if not set.
        # For now, just ensure it's a valid selection.
        pass # No action needed to clear the other dropdown for now in popup

    def _save_interaction(self):
        try:
            interaction_type_str = self.interaction_type_var.get()
            if not interaction_type_str:
                messagebox.showerror("Validation Error", "Interaction Type is required.", parent=self)
                return
            interaction_type_enum = InteractionType(interaction_type_str)

            date_str = self.date_var.get()
            time_str = self.time_var.get()
            if not date_str or not time_str:
                messagebox.showerror("Validation Error", "Date and Time are required.", parent=self)
                return

            # Combine date and time strings then parse
            datetime_str = f"{date_str}T{time_str}:00" # Adding seconds for full ISO
            try:
                interaction_datetime = datetime.datetime.fromisoformat(datetime_str)
            except ValueError:
                messagebox.showerror("Validation Error", "Invalid Date or Time format. Use YYYY-MM-DD and HH:MM.", parent=self)
                return

            subject = self.subject_var.get()
            if not subject:
                messagebox.showerror("Validation Error", "Subject is required.", parent=self)
                return
            if len(subject) > 150:
                messagebox.showerror("Validation Error", "Subject cannot exceed 150 characters.", parent=self)
                return

            description = self.description_text.get("1.0", tk.END).strip() # Get all text from Text widget

            selected_account_name = self.account_combobox.get()
            account_id = self.accounts_map.get(selected_account_name)

            selected_contact_name = self.contact_combobox.get()
            contact_id = self.contacts_map.get(selected_contact_name)

            if not account_id and not contact_id:
                messagebox.showerror("Validation Error", "Either an Account or a Contact must be selected.", parent=self)
                return

            # created_by_user_id would ideally come from a logged-in user session.
            # For now, we'll fetch the default 'system_user' ID.
            # This logic is already in core.logic.save_interaction, so we can pass None or retrieve it here.
            # Let's assume logic layer handles setting default user if None is passed.

            interaction = Interaction(
                company_id=account_id,
                contact_id=contact_id,
                interaction_type=interaction_type_enum,
                date_time=interaction_datetime,
                subject=subject,
                description=description,
                created_by_user_id=None # Logic layer will set default if None
            )

            new_interaction_id = self.logic.save_interaction(interaction)

            if new_interaction_id:
                messagebox.showinfo("Success", "Interaction saved successfully!", parent=self)
                if self.success_callback:
                    self.success_callback()
                self.destroy()
            else:
                # This case might not be hit if save_interaction raises exceptions for errors
                messagebox.showerror("Save Error", "Failed to save interaction. Check logs.", parent=self)

        except ValueError as ve: # Catch validation errors from InteractionType enum or datetime parsing
            messagebox.showerror("Input Error", str(ve), parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self)
            # Log the full error: print(f"Error saving interaction: {e}\n{traceback.format_exc()}")


if __name__ == '__main__':
    # Example usage for testing the popup standalone
    class MockLogic:
        def get_accounts(self): return [(1, "Account Alpha"), (2, "Account Beta")]
        def get_all_contacts(self):
            from shared.structs import Contact
            return [Contact(contact_id=101, name="John Doe", account_id=1), Contact(contact_id=102, name="Jane Smith", account_id=2)]
        def save_interaction(self, interaction):
            print(f"Mock save: {interaction.to_dict()}")
            return True # Simulate success
        def get_user_id_by_username(self, username): return 1 # Mock user ID

    root = tk.Tk()
    root.withdraw() # Hide main window for popup test

    def on_success():
        print("Interaction saved successfully (callback)!")

    # Test with pre-selected account
    # popup = InteractionPopup(root, MockLogic(), selected_account_id=1, success_callback=on_success)

    # Test without pre-selection
    popup = InteractionPopup(root, MockLogic(), success_callback=on_success)

    root.mainloop()
