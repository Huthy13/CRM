import tkinter as tk
from tkinter import messagebox, ttk
from ui.payment_terms.payment_term_popup import PaymentTermPopup
from shared.structs import PaymentTerm

class PaymentTermTab:
    def __init__(self, master, logic):
        self.frame = tk.Frame(master)
        self.logic = logic
        self.selected_term_id = None

        self.setup_ui()
        self.load_terms()

        self.frame.bind("<FocusIn>", lambda event: self.load_terms())

    def setup_ui(self):
        tk.Label(self.frame, text="Payment Terms").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        button_width = 20
        button_frame = tk.Frame(self.frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky="w")

        self.add_button = tk.Button(button_frame, text="New", command=self.create_new_term, width=button_width)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.edit_button = tk.Button(button_frame, text="Edit", command=self.edit_existing_term, width=button_width)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = tk.Button(button_frame, text="Delete", command=self.delete_term, width=button_width)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        self.tree = ttk.Treeview(self.frame, columns=("id", "name", "days"), show="headings")
        self.tree.column("id", width=0, stretch=False)
        self.tree.heading("name", text="Term Name")
        self.tree.heading("days", text="Days")
        self.tree.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.select_term)

        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

    def load_terms(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        terms = self.logic.list_payment_terms()
        for term in terms:
            self.tree.insert("", "end", values=(
                term.term_id,
                term.term_name,
                term.days if term.days is not None else "N/A",
            ))

    def select_term(self, event=None):
        selected_item = self.tree.selection()
        if selected_item:
            self.selected_term_id = self.tree.item(selected_item[0], 'values')[0]
        else:
            self.selected_term_id = None

    def create_new_term(self):
        popup = PaymentTermPopup(self.frame, self.logic, None)
        self.frame.wait_window(popup)
        self.load_terms()

    def edit_existing_term(self):
        if not self.selected_term_id:
            messagebox.showwarning("No Selection", "Please select a term to edit.")
            return
        popup = PaymentTermPopup(self.frame, self.logic, self.selected_term_id)
        self.frame.wait_window(popup)
        self.load_terms()

    def delete_term(self):
        if not self.selected_term_id:
            messagebox.showwarning("No Selection", "Please select a term to delete.")
            return
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete term ID: {self.selected_term_id}?")
        if confirm:
            try:
                self.logic.delete_payment_term(int(self.selected_term_id))
                messagebox.showinfo("Success", "Term deleted successfully.")
                self.load_terms()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete term: {e}")
