import tkinter as tk
from tkinter import messagebox
from core.sales_logic import SalesLogic
from shared.structs import SalesDocumentItem


class RecordShippingPopup(tk.Toplevel):
    def __init__(self, master, sales_logic: SalesLogic, item: SalesDocumentItem, on_hand: float, refresh_callback=None):
        super().__init__(master)
        self.sales_logic = sales_logic
        self.item = item
        self.on_hand = on_hand
        self.refresh_callback = refresh_callback

        self.title("Record Shipping")
        self.geometry("300x240")

        tk.Label(self, text=f"Product: {item.product_description}").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        tk.Label(self, text=f"Ordered: {item.quantity}").grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        tk.Label(self, text=f"Shipped: {item.shipped_quantity}").grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        tk.Label(self, text=f"On Hand: {on_hand}").grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        remaining = item.quantity - item.shipped_quantity
        tk.Label(self, text=f"Remaining: {remaining}").grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        tk.Label(self, text="Quantity to Ship:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.qty_entry = tk.Entry(self, width=10)
        self.qty_entry.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        tk.Button(self, text="Record", command=self.record_shipping).grid(row=6, column=0, padx=5, pady=10, sticky="e")
        tk.Button(self, text="Cancel", command=self.destroy).grid(row=6, column=1, padx=5, pady=10, sticky="w")

    def record_shipping(self):
        qty_str = self.qty_entry.get().strip()
        try:
            qty = float(qty_str)
        except ValueError:
            messagebox.showerror("Validation Error", "Quantity must be a number.", parent=self)
            return

        remaining = self.item.quantity - self.item.shipped_quantity
        if qty <= 0 or qty > remaining:
            messagebox.showerror("Validation Error", f"Quantity must be between 0 and {remaining}.", parent=self)
            return

        if qty > self.on_hand:
            messagebox.showerror(
                "Validation Error",
                f"Cannot ship more than on-hand ({self.on_hand}).",
                parent=self,
            )
            return

        try:
            self.sales_logic.record_item_shipment(self.item.id, qty)
            messagebox.showinfo("Success", "Shipment recorded.", parent=self)
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record shipment: {e}", parent=self)
