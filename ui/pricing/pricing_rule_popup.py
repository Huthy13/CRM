import tkinter as tk
from tkinter import messagebox
from shared.structs import PricingRule

class PricingRulePopup(tk.Toplevel):
    def __init__(self, master, logic, rule_id=None):
        super().__init__(master)
        self.logic = logic
        self.rule_id = rule_id

        if self.rule_id is None:
            self.title("New Pricing Rule")
            self.rule = PricingRule()
        else:
            self.title("Edit Pricing Rule")
            self.rule = self.logic.get_pricing_rule(self.rule_id)

        self.name_entry = self._create_entry("Rule Name:", 0, self.rule.rule_name)
        self.markup_entry = self._create_entry("Markup %:", 1, self.rule.markup_percentage)
        self.fixed_price_entry = self._create_entry("Fixed Price:", 2, self.rule.fixed_price)

        save_button = tk.Button(self, text="Save", command=self.save_rule)
        save_button.grid(row=3, column=0, columnspan=2, pady=10)

    def _create_entry(self, label_text, row, initial_value=""):
        label = tk.Label(self, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky="e")
        entry = tk.Entry(self, width=40)
        if initial_value is not None:
            entry.insert(0, initial_value)
        entry.grid(row=row, column=1, padx=5, pady=5)
        return entry

    def save_rule(self):
        rule_name = self.name_entry.get()
        markup_str = self.markup_entry.get()
        fixed_price_str = self.fixed_price_entry.get()

        if not rule_name:
            messagebox.showerror("Error", "Rule name cannot be empty.")
            return

        markup = None
        if markup_str:
            try:
                markup = float(markup_str)
            except ValueError:
                messagebox.showerror("Error", "Markup percentage must be a number.")
                return

        fixed_price = None
        if fixed_price_str:
            try:
                fixed_price = float(fixed_price_str)
            except ValueError:
                messagebox.showerror("Error", "Fixed price must be a number.")
                return

        if markup is None and fixed_price is None:
            messagebox.showerror("Error", "Either markup or fixed price must be provided.")
            return

        if markup is not None and fixed_price is not None:
            messagebox.showerror("Error", "Provide either markup or fixed price, not both.")
            return

        self.rule.rule_name = rule_name
        self.rule.markup_percentage = markup
        self.rule.fixed_price = fixed_price

        if self.rule_id is None:
            self.logic.create_pricing_rule(self.rule.rule_name, self.rule.markup_percentage, self.rule.fixed_price)
        else:
            self.logic.update_pricing_rule(self.rule.rule_id, self.rule.rule_name, self.rule.markup_percentage, self.rule.fixed_price)

        self.destroy()
