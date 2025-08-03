import tkinter as tk
from tkinter import messagebox
from typing import List

from core.purchase_logic import PurchaseLogic
from shared.structs import PurchaseDocumentItem


class RecordReceiptsPopup(tk.Toplevel):
    def __init__(
        self,
        master,
        purchase_logic: PurchaseLogic,
        doc_id: int,
        items: List[PurchaseDocumentItem],
        refresh_callback=None,
    ):
        super().__init__(master)
        self.purchase_logic = purchase_logic
        self.doc_id = doc_id
        self.items = items
        self.refresh_callback = refresh_callback

        self.title("Record Receipts")
        self.geometry("450x300")

        tk.Label(self, text="Enter quantities to receive:").grid(
            row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w"
        )

        headers = ["Product", "Remaining", "Receive Qty"]
        for col, text in enumerate(headers):
            tk.Label(self, text=text, font=("Arial", 10, "bold")).grid(
                row=1, column=col, padx=5, pady=5, sticky="w"
            )

        self.entries: dict[int, tuple[tk.Entry, float]] = {}
        for idx, item in enumerate(self.items, start=2):
            remaining = item.quantity - item.received_quantity
            tk.Label(self, text=item.product_description).grid(
                row=idx, column=0, padx=5, pady=2, sticky="w"
            )
            tk.Label(self, text=f"{remaining}").grid(
                row=idx, column=1, padx=5, pady=2, sticky="e"
            )
            entry = tk.Entry(self, width=10)
            entry.grid(row=idx, column=2, padx=5, pady=2, sticky="e")
            self.entries[item.id] = (entry, remaining)

        row = len(self.items) + 2
        tk.Button(self, text="Record", command=self.record_receipts).grid(
            row=row, column=1, padx=5, pady=10, sticky="e"
        )
        tk.Button(self, text="Cancel", command=self.destroy).grid(
            row=row, column=2, padx=5, pady=10, sticky="w"
        )

    def record_receipts(self):
        receipts: dict[int, float] = {}
        for item_id, (entry, remaining) in self.entries.items():
            qty_str = entry.get().strip()
            if not qty_str:
                continue
            try:
                qty = float(qty_str)
            except ValueError:
                messagebox.showerror(
                    "Validation Error", "Quantity must be a number.", parent=self
                )
                return
            if qty <= 0 or qty > remaining:
                messagebox.showerror(
                    "Validation Error",
                    f"Quantity for item {item_id} must be between 0 and {remaining}.",
                    parent=self,
                )
                return
            receipts[item_id] = qty

        if not receipts:
            messagebox.showwarning(
                "No Quantities", "Enter quantities to receive.", parent=self
            )
            return

        try:
            self.purchase_logic.record_receipts(self.doc_id, receipts)
            messagebox.showinfo("Success", "Receipts recorded.", parent=self)
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to record receipts: {e}", parent=self
            )
