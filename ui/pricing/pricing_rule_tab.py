import tkinter as tk
from tkinter import messagebox, ttk
from ui.pricing.pricing_rule_popup import PricingRulePopup
from shared.structs import PricingRule

class PricingRuleTab:
    def __init__(self, master, logic):
        self.frame = tk.Frame(master)
        self.logic = logic
        self.selected_rule_id = None

        self.setup_ui()
        self.load_rules()

        self.frame.bind("<FocusIn>", lambda event: self.load_rules())

    def setup_ui(self):
        tk.Label(self.frame, text="Pricing Rules").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        button_width = 20

        self.add_button = tk.Button(self.frame, text="New Rule", command=self.create_new_rule, width=button_width)
        self.add_button.grid(row=1, column=0, padx=5, pady=5)

        self.edit_button = tk.Button(self.frame, text="Edit Rule", command=self.edit_existing_rule, width=button_width)
        self.edit_button.grid(row=1, column=1, padx=5, pady=5)

        self.delete_button = tk.Button(self.frame, text="Delete Rule", command=self.delete_rule, width=button_width)
        self.delete_button.grid(row=1, column=2, padx=5, pady=5)

        self.tree = ttk.Treeview(self.frame, columns=("id", "name", "markup", "fixed_price"), show="headings")
        self.tree.column("id", width=0, stretch=False)
        self.tree.heading("name", text="Rule Name")
        self.tree.heading("markup", text="Markup %")
        self.tree.heading("fixed_price", text="Fixed Price")
        self.tree.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.select_rule)

        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

    def load_rules(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        rules = self.logic.list_pricing_rules()
        for rule in rules:
            self.tree.insert("", "end", values=(
                rule.rule_id,
                rule.rule_name,
                f"{rule.markup_percentage:.2f}" if rule.markup_percentage is not None else "N/A",
                f"${rule.fixed_price:.2f}" if rule.fixed_price is not None else "N/A",
            ))

    def select_rule(self, event=None):
        selected_item = self.tree.selection()
        if selected_item:
            self.selected_rule_id = self.tree.item(selected_item[0], 'values')[0]
        else:
            self.selected_rule_id = None

    def create_new_rule(self):
        popup = PricingRulePopup(self.frame, self.logic, None)
        self.frame.wait_window(popup)
        self.load_rules()

    def edit_existing_rule(self):
        if not self.selected_rule_id:
            messagebox.showwarning("No Selection", "Please select a rule to edit.")
            return
        popup = PricingRulePopup(self.frame, self.logic, self.selected_rule_id)
        self.frame.wait_window(popup)
        self.load_rules()

    def delete_rule(self):
        if not self.selected_rule_id:
            messagebox.showwarning("No Selection", "Please select a rule to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete rule ID: {self.selected_rule_id}?")
        if confirm:
            try:
                self.logic.delete_pricing_rule(int(self.selected_rule_id))
                messagebox.showinfo("Success", "Rule deleted successfully.")
                self.load_rules()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete rule: {e}")
