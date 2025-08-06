import tkinter as tk
from tkinter import messagebox, ttk
from ui.accounts.account_popup import AccountDetailsPopup
from shared.structs import Account, AccountType
from ui.base.tab_base import TabBase


class AccountTab(TabBase):
    def __init__(self, master, logic):
        super().__init__(master)
        self.logic = logic
        self.selected_account_id = None  # Initialize selected_account_id as None

        # Track which columns are visible in the treeview. "pricing_rule" and
        # "payment_term" default to hidden and can be toggled on later. The
        # order of insertion here determines the display order in the tree.
        self.column_vars: dict[str, tk.BooleanVar] = {
            "name": tk.BooleanVar(value=True),
            "phone": tk.BooleanVar(value=True),
            "description": tk.BooleanVar(value=True),
            "account_type": tk.BooleanVar(value=True),
            "pricing_rule": tk.BooleanVar(value=False),
            "payment_term": tk.BooleanVar(value=False),
        }

        # Setup account tab components
        self.setup_account_tab()
        self.load_accounts()

        # Bind the FocusIn event to reload the listbox each time the tab gains focus
        self.bind("<FocusIn>", lambda event: self.load_accounts())

    def setup_account_tab(self):
        """Setup the Accounts tab with account fields and account list."""
        tk.Label(self, text="Accounts").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        button_width = 20

        # Button bar
        button_frame = tk.Frame(self)
        button_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky="w")

        self.add_account_button = tk.Button(
            button_frame,
            text="New",
            command=self.create_new_account,
            width=button_width,
        )
        self.add_account_button.pack(side=tk.LEFT, padx=5)

        self.edit_account_button = tk.Button(
            button_frame,
            text="Edit",
            command=self.edit_existing_account,
            width=button_width,
        )
        self.edit_account_button.pack(side=tk.LEFT, padx=5)

        self.remove_account_button = tk.Button(
            button_frame,
            text="Delete",
            command=self.remove_account,
            width=button_width,
        )
        self.remove_account_button.pack(side=tk.LEFT, padx=5)

        # Treeview for displaying accounts. Include optional pricing rule and
        # payment term columns, but hide them by default via ``displaycolumns``.
        all_columns = ("id",) + tuple(self.column_vars.keys())
        display_columns = [c for c, var in self.column_vars.items() if var.get()]
        self.tree = ttk.Treeview(
            self,
            columns=all_columns,
            displaycolumns=display_columns,
            show="headings",
        )
        self.tree.column("id", width=0, stretch=False)  # Hidden ID column
        self.tree.heading("name", text="Account Name", command=lambda: self.sort_column("name", False))
        self.tree.heading("phone", text="Phone", command=lambda: self.sort_column("phone", False))
        self.tree.heading("description", text="Description", command=lambda: self.sort_column("description", False))
        self.tree.heading("account_type", text="Account Type", command=lambda: self.sort_column("account_type", False))
        self.tree.heading("pricing_rule", text="Pricing Rule", command=lambda: self.sort_column("pricing_rule", False))
        self.tree.heading("payment_term", text="Payment Term", command=lambda: self.sort_column("payment_term", False))

        self.tree.column("name", width=150)
        self.tree.column("phone", width=100)
        self.tree.column("description", width=150)
        self.tree.column("account_type", width=100)
        self.tree.column("pricing_rule", width=150)
        self.tree.column("payment_term", width=150)

        self.tree.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.select_account)

        # Configure the grid row and column containing the tree to expand
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

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
                self.load_accounts()  # Refresh list
            except Exception as e:  # Catch potential errors from logic/db layer
                messagebox.showerror("Error", f"Failed to delete account: {e}")
        else:
            messagebox.showinfo("Cancelled", "Account deletion cancelled.")

    def edit_existing_account(self):
        if not self.selected_account_id:
            messagebox.showwarning("No Selection", "Please select an account to edit.")
            return
        # Pass self.load_accounts as a callback to refresh after edit
        popup = AccountDetailsPopup(self, self.logic, self.selected_account_id)
        self.wait_window(popup)  # Wait for popup to close
        self.load_accounts()  # Then reload

    def create_new_account(self):
        # Pass self.load_accounts as a callback to refresh after add
        popup = AccountDetailsPopup(self, self.logic, None)
        self.wait_window(popup)  # Wait for popup to close
        self.load_accounts()  # Then reload

    def load_accounts(self):
        """Load accounts into the Tree"""

        # Clear the Treeview to start fresh
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Retrieve all accounts - logic.get_all_accounts() should now return Account objects
        accounts_obj_list = self.logic.get_all_accounts()

        for account_obj in accounts_obj_list:
            account_type_display = account_obj.account_type.value if account_obj.account_type else "N/A"

            pricing_rule_display = "N/A"
            if account_obj.pricing_rule_id:
                rule = self.logic.get_pricing_rule(account_obj.pricing_rule_id)
                if rule:
                    pricing_rule_display = rule.rule_name

            payment_term_display = "N/A"
            if account_obj.payment_term_id:
                term = self.logic.get_payment_term(account_obj.payment_term_id)
                if term:
                    payment_term_display = term.term_name

            self.tree.insert(
                "",
                "end",
                values=(
                    account_obj.account_id,
                    account_obj.name,
                    account_obj.phone,
                    account_obj.description or "N/A",
                    account_type_display,
                    pricing_rule_display,
                    payment_term_display,
                ),
            )

    def select_account(self, event=None):
        """Retrieve the Account_ID of the selected account."""
        selected_item = self.tree.selection()
        if selected_item:
            # First value in 'values' is the account_id
            self.selected_account_id = self.tree.item(selected_item[0], 'values')[0]
        else:
            self.selected_account_id = None
