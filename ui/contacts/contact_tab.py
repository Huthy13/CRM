import tkinter as tk
from tkinter import messagebox, ttk
from ui.contacts.contact_popup import ContactDetailsPopup
from shared.structs import Contact
from ui.base.tab_base import TabBase


class ContactTab(TabBase):
    def __init__(self, master, logic):
        super().__init__(master)
        self.logic = logic
        self.selected_contact_id = None

        self.setup_contact_tab()
        self.load_contacts()
        self.bind("<FocusIn>", self.load_contacts)

    def setup_contact_tab(self):
        tk.Label(self, text="Contact Management").grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        button_width = 20
        button_frame = tk.Frame(self)
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

        self.tree = ttk.Treeview(self, columns=("id", "name", "phone", "email", "role", "account_name"), show="headings")

        self.tree.column("id", width=0, stretch=False)  # Hidden ID column
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
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.on_contact_select)

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

        id_to_process = self.selected_contact_id
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the selected contact (ID: {id_to_process})?",
        )

        if confirm:
            try:
                self.logic.delete_contact(id_to_process)
                self.load_contacts()
                messagebox.showinfo(
                    "Success",
                    f"Contact (ID: {id_to_process}) deleted successfully.",
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete contact: {e}")
            self.selected_contact_id = None

    def edit_existing_contact(self):
        if not self.selected_contact_id:
            messagebox.showwarning("No Selection", "Please select a contact to edit.")
            return
        popup = ContactDetailsPopup(self.master, self, self.logic, contact_id=self.selected_contact_id)
        self.master.wait_window(popup)
        self.load_contacts()

    def create_new_contact(self):
        popup = ContactDetailsPopup(self.master, self, self.logic, contact_id=None)
        self.master.wait_window(popup)
        self.load_contacts()

    def load_contacts(self, event=None):  # event parameter for binding
        self.tree.delete(*self.tree.get_children())
        self.selected_contact_id = None  # Reset selection

        try:
            contacts = self.logic.get_all_contacts()  # Returns list of Contact objects
            for contact in contacts:
                account_name_display = "N/A"
                if contact.account_id:
                    account = self.logic.get_account_details(contact.account_id)
                    if account:
                        account_name_display = account.name

                self.tree.insert("", "end", iid=contact.contact_id, values=(
                    contact.contact_id,  # Stored in hidden "id" column, accessed by iid
                    contact.name,
                    contact.phone,
                    contact.email,
                    contact.role,
                    account_name_display
                ))
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load contacts: {e}")
            print(f"Error in load_contacts: {e}")  # For console debugging

    def refresh_contacts_list(self):  # Added method for popup to call
        self.load_contacts()
