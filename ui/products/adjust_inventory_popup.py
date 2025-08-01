import tkinter as tk
from tkinter import messagebox
from shared.structs import Product
from core.inventory_service import InventoryService


class AdjustInventoryPopup(tk.Toplevel):
    def __init__(self, master, inventory_service: InventoryService, product: Product, refresh_callback=None):
        super().__init__(master)
        self.inventory_service = inventory_service
        self.product = product
        self.refresh_callback = refresh_callback
        self.title(f"Adjust Inventory - {product.name}")
        self.geometry("300x180")

        tk.Label(self, text="Quantity Change:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.quantity_entry = tk.Entry(self, width=20)
        self.quantity_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self, text="Reference:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.reference_entry = tk.Entry(self, width=20)
        self.reference_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Button(self, text="Apply", command=self.apply_adjustment).grid(row=2, column=0, padx=5, pady=10, sticky="e")
        tk.Button(self, text="Cancel", command=self.destroy).grid(row=2, column=1, padx=5, pady=10, sticky="w")

    def apply_adjustment(self):
        qty_str = self.quantity_entry.get().strip()
        reference = self.reference_entry.get().strip() or None
        try:
            qty = float(qty_str)
        except ValueError:
            messagebox.showerror("Validation Error", "Quantity must be a number.", parent=self)
            return
        try:
            self.inventory_service.record_adjustment(self.product.product_id, qty, reference)
            messagebox.showinfo("Success", "Inventory adjusted.", parent=self)
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to adjust inventory: {e}", parent=self)
