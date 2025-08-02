import tkinter as tk
from tkinter import messagebox
from shared.structs import PaymentTerm
from ui.base.popup_base import PopupBase

class PaymentTermPopup(PopupBase):
    def __init__(self, master, logic, term_id=None):
        super().__init__(master)
        self.logic = logic
        self.term_id = term_id

        if self.term_id is None:
            self.title("New Payment Term")
            self.term = PaymentTerm()
        else:
            self.title("Edit Payment Term")
            self.term = self.logic.get_payment_term(self.term_id)

        self.name_entry = self._create_entry("Term Name:", 0, self.term.term_name)
        self.days_entry = self._create_entry("Days:", 1, self.term.days)

        save_button = tk.Button(self, text="Save", command=self.save_term)
        save_button.grid(row=2, column=0, columnspan=2, pady=10)

    def save_term(self):
        term_name = self.name_entry.get()
        if not self.validate_not_empty(term_name, "Term name"):
            return
        days_str = self.days_entry.get()
        days = None
        if days_str:
            try:
                days = int(days_str)
            except ValueError:
                messagebox.showerror("Error", "Days must be an integer.")
                return
        self.term.term_name = term_name
        self.term.days = days
        if self.term_id is None:
            self.logic.create_payment_term(self.term.term_name, self.term.days)
        else:
            self.logic.update_payment_term(self.term.term_id, self.term.term_name, self.term.days)
        self.destroy()
