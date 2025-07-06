import tkinter as tk
from tkinter import ttk
from core.logic import AddressBookLogic
from shared.structs import Interaction, Account, Contact # Assuming these might be needed for type hinting or direct use

class InteractionLogTab(ttk.Frame):
    def __init__(self, parent, logic: AddressBookLogic):
        super().__init__(parent)
        self.logic = logic
        self.accounts_map = {} # To map display names to account IDs
        self.contacts_map = {} # To map display names to contact IDs

        # Configure grid layout
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=3) # Give more weight to the interaction display
        self.rowconfigure(1, weight=1)    # Allow interaction display to expand

        self._setup_widgets()

    def _setup_widgets(self):
        # Account selection
        ttk.Label(self, text="Select Account:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.account_combobox = ttk.Combobox(self, state="readonly", width=30)
        self.account_combobox.grid(row=0, column=0, padx=(100,5), pady=5, sticky="ew")
        self.account_combobox.bind("<<ComboboxSelected>>", self._on_account_selected)

        # Contact selection
        ttk.Label(self, text="Select Contact:").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.contact_combobox = ttk.Combobox(self, state="readonly", width=30)
        self.contact_combobox.grid(row=0, column=1, padx=(100,5), pady=5, sticky="ew")
        self.contact_combobox.bind("<<ComboboxSelected>>", self._on_contact_selected)

        # Clear selection button
        self.clear_button = ttk.Button(self, text="Clear Filters", command=self._clear_filters)
        self.clear_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # New Interaction button
        self.new_interaction_button = ttk.Button(self, text="New Interaction", command=self._open_new_interaction_popup)
        self.new_interaction_button.grid(row=0, column=2, padx=(90,5), pady=5, sticky="e") # Adjusted padding slightly

        # Interactions display area (using Treeview for structured data)
        interaction_frame = ttk.LabelFrame(self, text="Interactions")
        interaction_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        interaction_frame.columnconfigure(0, weight=1)
        interaction_frame.rowconfigure(0, weight=1)

        columns = ("type", "datetime", "subject", "description")
        self.interactions_tree = ttk.Treeview(interaction_frame, columns=columns, show="headings")

        self.interactions_tree.heading("type", text="Type")
        self.interactions_tree.heading("datetime", text="Date/Time")
        self.interactions_tree.heading("subject", text="Subject")
        self.interactions_tree.heading("description", text="Description")

        self.interactions_tree.column("type", width=80, stretch=tk.NO)
        self.interactions_tree.column("datetime", width=150, stretch=tk.NO)
        self.interactions_tree.column("subject", width=200)
        self.interactions_tree.column("description", width=300)

        self.interactions_tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar for the treeview
        scrollbar = ttk.Scrollbar(interaction_frame, orient=tk.VERTICAL, command=self.interactions_tree.yview)
        self.interactions_tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self._load_accounts()
        self._load_contacts() # Initial load of all contacts

    def _load_accounts(self):
        self.accounts_map = {} # Reset map
        accounts = self.logic.get_accounts()  # This returns list of (id, name) tuples
        if accounts:
            account_names = []
            for acc_id, acc_name in accounts:
                display_name = f"{acc_name} (ID: {acc_id})"
                account_names.append(display_name)
                self.accounts_map[display_name] = acc_id
            self.account_combobox['values'] = account_names
        else:
            self.account_combobox['values'] = []
        self.account_combobox.set('') # Clear current selection

    def _load_contacts(self, account_id=None):
        self.contacts_map = {} # Reset map
        self.contact_combobox.set('') # Clear current selection first

        if account_id:
            contacts = self.logic.get_contacts_by_account(account_id) # List of Contact objects
        else:
            contacts = self.logic.get_all_contacts() # List of Contact objects

        if contacts:
            contact_names = []
            for contact in contacts:
                display_name = f"{contact.name} (ID: {contact.contact_id})"
                contact_names.append(display_name)
                self.contacts_map[display_name] = contact.contact_id
            self.contact_combobox['values'] = contact_names
        else:
            self.contact_combobox['values'] = []
        # self.contact_combobox.set('') # Already cleared at the beginning of _load_contacts


    def _on_account_selected(self, event=None):
        self._clear_interaction_display()

        selected_account_name = self.account_combobox.get()
        account_id = self.accounts_map.get(selected_account_name)

        self._load_contacts(account_id=account_id) # Filters contacts and clears contact selection

        if account_id:
            # Display interactions for the selected account overall
            interactions = self.logic.get_all_interactions(company_id=account_id, contact_id=None)
            self._display_interactions(interactions)
        # If account_id is None (selection cleared), contacts are loaded (all), and interactions remain cleared.

    def _on_contact_selected(self, event=None):
        self._clear_interaction_display()

        selected_contact_name = self.contact_combobox.get()
        contact_id = self.contacts_map.get(selected_contact_name)

        if contact_id:
            # Display interactions for the selected contact.
            # Account selection (if any) is kept to indicate context of the contact list.
            interactions = self.logic.get_all_interactions(contact_id=contact_id)
            self._display_interactions(interactions)
        # If contact selection is cleared, interactions are already cleared.

    def _display_interactions(self, interactions: list[Interaction]):
        # Clear existing items in the treeview
        for item in self.interactions_tree.get_children():
            self.interactions_tree.delete(item)

        if interactions:
            for interaction in interactions:
                # Ensure datetime is formatted nicely if it's a datetime object
                dt_display = ""
                if interaction.date_time:
                    try:
                        # Assuming interaction.date_time is a datetime object
                        dt_display = interaction.date_time.strftime("%Y-%m-%d %H:%M:%S")
                    except AttributeError: # If it's already a string (e.g. from older data or different source)
                        dt_display = str(interaction.date_time)

                interaction_type_val = interaction.interaction_type.value if interaction.interaction_type else "N/A"

                self.interactions_tree.insert("", tk.END, values=(
                    interaction_type_val,
                    dt_display,
                    interaction.subject,
                    interaction.description
                ))
        # else: No interactions to display (already cleared)

    def _clear_interaction_display(self):
        for item in self.interactions_tree.get_children():
            self.interactions_tree.delete(item)

    def _clear_filters(self):
        self.account_combobox.set('')
        # This will trigger _on_account_selected, which then calls:
        # - self._clear_interaction_display()
        # - self._load_contacts(account_id=None) -> which clears contact_combobox.set('')
        # So, the lines below are mostly redundant if _on_account_selected works as expected.
        # However, explicit calls ensure the state is correctly reset.
        self.contact_combobox.set('') # Explicitly clear contact selection
        self._load_contacts(account_id=None) # Ensure contact list is full
        self._clear_interaction_display() # Ensure interactions are cleared

    def _open_new_interaction_popup(self):
        selected_account_id = None
        selected_account_name = self.account_combobox.get()
        if selected_account_name:
            selected_account_id = self.accounts_map.get(selected_account_name)

        selected_contact_id = None
        selected_contact_name = self.contact_combobox.get()
        if selected_contact_name:
            selected_contact_id = self.contacts_map.get(selected_contact_name)

        from .interaction_popup import InteractionPopup # Local import

        popup = InteractionPopup(
            self, # Parent window
            self.logic,
            selected_account_id=selected_account_id,
            selected_contact_id=selected_contact_id,
            success_callback=self._refresh_log_after_save
        )
        # Popup is modal (grab_set) and will manage its own lifecycle.

    def _refresh_log_after_save(self):
        # This method is called after a new interaction is successfully saved in the popup.
        # It should refresh the current view in the interaction log.

        # Option 1: Re-apply current filter
        current_account_selection = self.account_combobox.get()
        current_contact_selection = self.contact_combobox.get()

        if current_account_selection:
            self._on_account_selected() # This will fetch and display for the selected account
        elif current_contact_selection:
            self._on_contact_selected() # This will fetch and display for the selected contact
        else:
            # If no filter was active, maybe clear the list or show all (though showing all might be too much)
            # For now, just clearing or doing nothing if no filter is set.
            # Users would typically have a filter active or will apply one.
            self._clear_interaction_display()
            # Or, to show all interactions (if desired, but could be slow/long):
            # all_interactions = self.logic.get_all_interactions()
            # self._display_interactions(all_interactions)


if __name__ == '__main__':
    # Example usage for testing the tab standalone
    # This requires a mock or real logic handler
    class MockLogic:
        _interactions = [] # Store mock interactions to simulate DB

        def __init__(self):
            from shared.structs import InteractionType # Local import for enum
            import datetime
            # Pre-populate some interactions
            self._interactions = [
                Interaction(interaction_id=1, company_id=1, interaction_type=InteractionType.CALL, date_time=datetime.datetime.now()-datetime.timedelta(days=2), subject="Initial Call", description="Discussed needs for Account Alpha.", created_by_user_id=1),
                Interaction(interaction_id=2, contact_id=101, interaction_type=InteractionType.EMAIL, date_time=datetime.datetime.now()-datetime.timedelta(days=1), subject="Follow-up with John", description="Sent proposal.", created_by_user_id=1),
                Interaction(interaction_id=3, company_id=1, contact_id=101, interaction_type=InteractionType.MEETING, date_time=datetime.datetime.now(), subject="Meeting with John (Alpha)", description="Finalized deal.", created_by_user_id=1),
                Interaction(interaction_id=4, company_id=2, interaction_type=InteractionType.VISIT, date_time=datetime.datetime.now()-datetime.timedelta(hours=5), subject="Site Visit Beta", description="On-site check.", created_by_user_id=1),
            ]


        def get_accounts(self):
            return [(1, "Account Alpha"), (2, "Account Beta")]

        def get_all_contacts(self):
            # Ensure Contact is defined for mock, or import it
            from shared.structs import Contact
            return [
                Contact(contact_id=101, name="John Doe (Alpha)", account_id=1),
                Contact(contact_id=102, name="Jane Smith (Beta)", account_id=2),
                Contact(contact_id=103, name="Peter Jones (Alpha)", account_id=1)
            ]

        def get_all_interactions(self, company_id=None, contact_id=None):
            if company_id:
                return [i for i in self._interactions if i.company_id == company_id]
            if contact_id:
                return [i for i in self._interactions if i.contact_id == contact_id]
            return list(self._interactions) # Return a copy

        def save_interaction(self, interaction_obj: Interaction):
            print(f"Mock saving interaction: {interaction_obj.subject} for company {interaction_obj.company_id} / contact {interaction_obj.contact_id}")
            # Simulate adding to DB and getting a new ID
            new_id = (max(i.interaction_id for i in self._interactions) + 1) if self._interactions else 1
            interaction_obj.interaction_id = new_id
            # Ensure default user ID if not set (logic layer would do this)
            if interaction_obj.created_by_user_id is None:
                 interaction_obj.created_by_user_id = self.get_user_id_by_username("mock_user")
            self._interactions.append(interaction_obj)
            print(f"Saved. New list: {[str(i.subject) for i in self._interactions]}")
            return new_id

        def get_user_id_by_username(self, username): # Mocked
            return 1


    root = tk.Tk()
    root.title("Interaction Log Tab Test")
    mock_logic = MockLogic()
    tab = InteractionLogTab(root, mock_logic)
    tab.pack(expand=True, fill="both")
    root.mainloop()
