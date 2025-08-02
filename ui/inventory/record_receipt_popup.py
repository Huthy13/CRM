import tkinter as tk
from tkinter import messagebox
from core.purchase_logic import PurchaseLogic
from shared.structs import PurchaseDocumentItem


class RecordReceiptPopup(tk.Toplevel):
    def __init__(self, master, purchase_logic: PurchaseLogic, item: PurchaseDocumentItem, refresh_callback=None):
        super().__init__(master)
        self.purchase_logic = purchase_logic
        self.item = item
        self.refresh_callback = refresh_callback

        self.title("Record Receipt")
        self.geometry("300x220")

        tk.Label(self, text=f"Product: {item.product_description}").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        tk.Label(self, text=f"Ordered: {item.quantity}").grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        tk.Label(self, text=f"Received: {item.received_quantity}").grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        remaining = item.quantity - item.received_quantity
        tk.Label(self, text=f"Remaining: {remaining}").grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        tk.Label(self, text="Quantity to Receive:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.qty_entry = tk.Entry(self, width=10)
        self.qty_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        tk.Button(self, text="Record", command=self.record_receipt).grid(row=5, column=0, padx=5, pady=10, sticky="e")
        tk.Button(self, text="Cancel", command=self.destroy).grid(row=5, column=1, padx=5, pady=10, sticky="w")

    def record_receipt(self):
        qty_str = self.qty_entry.get().strip()
        try:
            qty = float(qty_str)
        except ValueError:
            messagebox.showerror("Validation Error", "Quantity must be a number.", parent=self)
            return

        remaining = self.item.quantity - self.item.received_quantity
        if qty <= 0 or qty > remaining:
            messagebox.showerror("Validation Error", f"Quantity must be between 0 and {remaining}.", parent=self)
            return

        try:
            self.purchase_logic.record_item_receipt(self.item.id, qty)
            messagebox.showinfo("Success", "Receipt recorded.", parent=self)
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record receipt: {e}", parent=self)
