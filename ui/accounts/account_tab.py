import tkinter as tk
from tkinter import messagebox, ttk
from ui.accounts.account_popup import AccountDetailsPopup # Renamed file, relative import
from shared.structs import Account, AccountType # Moved to shared package, Import AccountType

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
        self.tree = ttk.Treeview(self.frame, columns=("id", "name", "phone", "description", "account_type"), show="headings")
        self.tree.column("id", width=0, stretch=False) # Hidden ID column
        self.tree.heading("name", text="Account Name", command=lambda: self.sort_column("name", False))
        self.tree.heading("phone", text="Phone", command=lambda: self.sort_column("phone", False))
        self.tree.heading("description", text="Description", command=lambda: self.sort_column("description", False))
        self.tree.heading("account_type", text="Account Type", command=lambda: self.sort_column("account_type", False))
        self.tree.column("name", width=150)
        self.tree.column("phone", width=100)
        self.tree.column("description", width=150)
        self.tree.column("account_type", width=100)
        self.tree.grid(row=7, column=0, columnspan=4, padx=5, pady=5, sticky="nsew") # Increased columnspan
        self.tree.bind("<<TreeviewSelect>>", self.select_account)

        # Configure the grid row and column containing the tree to expand
        self.frame.grid_rowconfigure(7, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)


    def sort_column(self, col, reverse):
        """Sort the Treeview column when clicked."""
        try:
            data = [(self.tree.set(k, col).lower(), k) for k in self.tree.get_children("")] # Convert to lowercase for case-insensitive sort
        except tk.TclError: # Happens if column has non-string sortable data, less likely with our current data
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
        # Add confirmation dialog
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete account ID: {self.selected_account_id}?")
        if confirm:
            try:
                self.logic.delete_account(self.selected_account_id)
                messagebox.showinfo("Success", "Account deleted successfully.")
                self.load_accounts() # Refresh list
            except Exception as e: # Catch potential errors from logic/db layer
                messagebox.showerror("Error", f"Failed to delete account: {e}")
        else:
            messagebox.showinfo("Cancelled", "Account deletion cancelled.")


    def edit_existing_account(self):
        if not self.selected_account_id:
            messagebox.showwarning("No Selection", "Please select an account to edit.")
            return
        # Pass self.load_accounts as a callback to refresh after edit
        popup = AccountDetailsPopup(self.frame, self.logic, self.selected_account_id)
        self.frame.wait_window(popup) # Wait for popup to close
        self.load_accounts() # Then reload

    def create_new_account(self):
        # Pass self.load_accounts as a callback to refresh after add
        popup = AccountDetailsPopup(self.frame, self.logic, None)
        self.frame.wait_window(popup) # Wait for popup to close
        self.load_accounts() # Then reload


    def load_accounts(self):
        """Load accounts into the Tree"""

        # Clear the Treeview to start fresh
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Retrieve all accounts - logic.get_all_accounts() should now return Account objects
        accounts_obj_list = self.logic.get_all_accounts()


        for account_obj in accounts_obj_list:
            account_type_display = account_obj.account_type.value if account_obj.account_type else "N/A"

            self.tree.insert("", "end", values=(
                account_obj.account_id,
                account_obj.name,
                account_obj.phone,
                account_obj.description or "N/A",
                account_type_display,
            ))


    def select_account(self, event=None):
        """Retrieve the Account_ID of the selected account."""
        selected_item = self.tree.selection()
        if selected_item:
            # First value in 'values' is the account_id
            self.selected_account_id = self.tree.item(selected_item[0], 'values')[0]
            # print(f"Selected Account_ID: {self.selected_account_id}") # For debugging
        else:
            self.selected_account_id = None
            # print("No account selected.") # For debugging
