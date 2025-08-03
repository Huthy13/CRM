import tkinter as tk
from tkinter import messagebox
from core.sales_logic import SalesLogic
from shared.structs import SalesDocument, SalesDocumentItem
from core.packing_slip_generator import generate_packing_slip


class CreateShipmentPopup(tk.Toplevel):
    def __init__(self, master, sales_logic: SalesLogic, doc: SalesDocument, items: list[SalesDocumentItem], refresh_callback=None):
        super().__init__(master)
        self.sales_logic = sales_logic
        self.doc = doc
        self.items = items
        self.refresh_callback = refresh_callback
        self.entries = {}

        self.title("Create Shipment")
        self.geometry("400x300")

        tk.Label(self, text=f"Sales Order: {doc.document_number}").grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        tk.Label(self, text="Item").grid(row=1, column=0, padx=5, pady=5)
        tk.Label(self, text="Remaining").grid(row=1, column=1, padx=5, pady=5)
        tk.Label(self, text="Ship Qty").grid(row=1, column=2, padx=5, pady=5)

        row = 2
        for item in items:
            remaining = item.quantity - item.shipped_quantity
            if remaining <= 0:
                continue
            tk.Label(self, text=item.product_description).grid(row=row, column=0, padx=5, pady=2, sticky="w")
            tk.Label(self, text=str(remaining)).grid(row=row, column=1, padx=5, pady=2)
            entry = tk.Entry(self, width=10)
            entry.grid(row=row, column=2, padx=5, pady=2)
            self.entries[item.id] = (entry, item)
            row += 1

        tk.Button(self, text="Create", command=self.create_shipment).grid(row=row, column=0, padx=5, pady=10, sticky="e")
        tk.Button(self, text="Cancel", command=self.destroy).grid(row=row, column=1, padx=5, pady=10, sticky="w")

    def create_shipment(self):
        item_qty_map = {}
        shipped_items = []
        for item_id, (entry, item) in self.entries.items():
            qty_str = entry.get().strip()
            if not qty_str:
                continue
            try:
                qty = float(qty_str)
            except ValueError:
                messagebox.showerror("Validation Error", "Quantity must be a number.", parent=self)
                return
            remaining = item.quantity - item.shipped_quantity
            if qty <= 0 or qty > remaining:
                messagebox.showerror("Validation Error", f"Quantity for {item.product_description} must be between 0 and {remaining}.", parent=self)
                return
            item_qty_map[item_id] = qty
            shipped_items.append((item.product_description, qty))

        if not item_qty_map:
            messagebox.showerror("Validation Error", "Enter at least one quantity to ship.", parent=self)
            return

        try:
            self.sales_logic.create_shipment(self.doc.id, item_qty_map)
            updated_items = self.sales_logic.get_items_for_sales_document(self.doc.id)
            remaining_items = []
            for it in updated_items:
                rem = it.quantity - it.shipped_quantity
                if rem > 0:
                    remaining_items.append((it.product_description, rem))
            generate_packing_slip(self.sales_logic, self.doc.id, shipped_items, remaining_items)
            messagebox.showinfo("Success", "Packing slip generated.", parent=self)
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create shipment: {e}", parent=self)
