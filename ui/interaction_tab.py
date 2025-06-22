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
        self.clear_button.grid(row=0, column=2, padx=5, pady=5, sticky="e")

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
        self._load_contacts()

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

    def _load_contacts(self):
        self.contacts_map = {} # Reset map
        contacts = self.logic.get_all_contacts() # This returns list of Contact objects
        if contacts:
            contact_names = []
            for contact in contacts:
                display_name = f"{contact.name} (ID: {contact.contact_id})"
                contact_names.append(display_name)
                self.contacts_map[display_name] = contact.contact_id
            self.contact_combobox['values'] = contact_names
        else:
            self.contact_combobox['values'] = []
        self.contact_combobox.set('') # Clear current selection


    def _on_account_selected(self, event=None):
        self.contact_combobox.set('') # Clear contact selection
        # selected_account_name = self.account_combobox.get()
        # account_id = self.accounts_map.get(selected_account_name)
        # if account_id:
        #     interactions = self.logic.get_all_interactions(company_id=account_id)
        selected_account_name = self.account_combobox.get()
        account_id = self.accounts_map.get(selected_account_name)
        if account_id:
            interactions = self.logic.get_all_interactions(company_id=account_id)
            self._display_interactions(interactions)
        else:
            self._clear_interaction_display() # Clear display if selection is invalid or no account selected

    def _on_contact_selected(self, event=None):
        self.account_combobox.set('') # Clear account selection
        selected_contact_name = self.contact_combobox.get()
        contact_id = self.contacts_map.get(selected_contact_name)
        if contact_id:
            interactions = self.logic.get_all_interactions(contact_id=contact_id)
            self._display_interactions(interactions)
        else:
            self._clear_interaction_display() # Clear display if selection is invalid or no contact selected

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
        self.contact_combobox.set('')
        self._clear_interaction_display()
        # Potentially reload all interactions or a default view if desired, e.g.
        # all_interactions = self.logic.get_all_interactions()
        # self._display_interactions(all_interactions)

if __name__ == '__main__':
    # Example usage for testing the tab standalone
    # This requires a mock or real logic handler
    class MockLogic:
        def get_accounts(self): return []
        def get_all_contacts(self): return []
        def get_all_interactions(self, company_id=None, contact_id=None): return []

    root = tk.Tk()
    root.title("Interaction Log Tab Test")
    mock_logic = MockLogic()
    tab = InteractionLogTab(root, mock_logic)
    tab.pack(expand=True, fill="both")
    root.mainloop()
