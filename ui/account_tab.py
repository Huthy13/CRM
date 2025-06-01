import tkinter as tk
from tkinter import messagebox, ttk
from ui.account_popup import AccountDetailsPopup # Renamed file, relative import
from shared.structs import Account # Moved to shared package

class AccountTab:
    def __init__(self, master, logic):
        self.frame = tk.Frame(master)
        self.logic = logic
        self.selected_account_id = None  # Initialize selected_account_id as None

        # Setup account tab components
        self.setup_account_tab()
        self.load_accounts()

        # Bind the FocusIn event to reload the listbox each time the tab gains focus
        self.frame.bind("<FocusIn>", lambda event: self.load_accounts())

    def setup_account_tab(self):
        """Setup the Account Administration tab with account fields and account list."""
        tk.Label(self.frame, text="Accounts").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        button_width = 20

        # Add account buttons
        self.add_account_button = tk.Button(
            self.frame, text="Add New Account",
            command=lambda: self.create_new_account(), width=button_width)
        self.add_account_button.grid(row=3, column=0, padx=5, pady=5)

        self.edit_account_button = tk.Button(
            self.frame, text="Edit Account",
            command=self.edit_existing_account, width=button_width)
        self.edit_account_button.grid(row=3, column=1, padx=5, pady=5)

        self.remove_account_button = tk.Button(
            self.frame, text="Remove Account",
            command=self.remove_account, width=button_width)
        self.remove_account_button.grid(row=3, column=2, padx=5, pady=5)


        # Treeview for displaying accounts
        self.tree = ttk.Treeview(self.frame, columns=("id", "name", "phone", "description"), show="headings")
        self.tree.column("id", width=0, stretch=False)
        self.tree.heading("name", text="Account Name", command=lambda: self.sort_column("name", False))
        self.tree.heading("phone", text="Phone", command=lambda: self.sort_column("phone", False))
        self.tree.heading("description", text="Description", command=lambda: self.sort_column("description", False))
        self.tree.column("name", width=150)
        self.tree.column("phone", width=100)
        self.tree.column("description", width=150)
        self.tree.grid(row=7, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.select_account)

    def sort_column(self, col, reverse):
        """Sort the Treeview column when clicked."""
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        data.sort(reverse=reverse)

        # Rearrange items in sorted positions
        for index, (val, k) in enumerate(data):
            self.tree.move(k, "", index)

        # Toggle sort direction for next time
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def remove_account(self):
        if not self.selected_account_id:
                messagebox.showwarning("No Selection", "Please select an account to delete.")
                return
        else:
            self.logic.delete_account(self.selected_account_id)
            self.load_accounts()

    def edit_existing_account(self):
        AccountDetailsPopup(self.frame, self.logic, self.selected_account_id)

    def create_new_account(self):
        AccountDetailsPopup(self.frame, self.logic, None)

    def load_accounts(self):
        """Load accounts into the Tree"""

        # Clear the Treeview to start fresh
        self.tree.delete(*self.tree.get_children())

        # Retrieve all contacts if toggle is set to show all
        accounts = self.logic.get_all_accounts()

        # Insert contacts into the Treeview, with contact_id as the first value in each row
        for account in accounts:
            account_id, account_name, account_phone, account_description = account

            # Insert into Treeview with contact_id as the first hidden value
            self.tree.insert("", "end", values=(
                account_id,            # Hidden id (used for identification)
                account_name,          # Visible Contact name
                account_phone,         # Visible Contact phone
                account_description or "N/A", # Visible account name
            ))


    def select_account(self, event=None):
        """Retrieve the Account_ID of the selected account."""
        selected_item = self.tree.selection()  # Get selected item(s)
        if selected_item:
            account_id = self.tree.item(selected_item[0], 'values')[0]  # Assuming the Account_ID is in the first column
            print(f"Selected Account_ID: {account_id}")
            self.selected_account_id = account_id
        else:
            print("No account selected.")
            return None
