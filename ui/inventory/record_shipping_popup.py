import tkinter as tk
from tkinter import messagebox
from typing import List, Tuple

from core.sales_logic import SalesLogic
from core.packing_slip_generator import generate_packing_slip_pdf
from shared.structs import SalesDocumentItem


class RecordShippingPopup(tk.Toplevel):
    def __init__(
        self,
        master,
        sales_logic: SalesLogic,
        doc_id: int,
        items: List[Tuple[SalesDocumentItem, float]],
        refresh_callback=None,
    ):
        super().__init__(master)
        self.sales_logic = sales_logic
        self.doc_id = doc_id
        self.items = items
        self.refresh_callback = refresh_callback
        self.last_shipments: dict[int, float] | None = None
        self.last_shipment_number: str | None = None

        self.title("Record Shipping")
        self.geometry("480x300")

        tk.Label(self, text="Enter quantities to ship:").grid(
            row=0, column=0, columnspan=4, padx=5, pady=5, sticky="w"
        )

        headers = ["Product", "Remaining", "On Hand", "Ship Qty"]
        for col, text in enumerate(headers):
            tk.Label(self, text=text, font=("Arial", 10, "bold")).grid(
                row=1, column=col, padx=5, pady=5, sticky="w"
            )

        self.entries: dict[int, tuple[tk.Entry, float, float]] = {}
        for idx, (item, on_hand) in enumerate(self.items, start=2):
            remaining = item.quantity - item.shipped_quantity
            tk.Label(self, text=item.product_description).grid(
                row=idx, column=0, padx=5, pady=2, sticky="w"
            )
            tk.Label(self, text=f"{remaining}").grid(
                row=idx, column=1, padx=5, pady=2, sticky="e"
            )
            tk.Label(self, text=f"{on_hand}").grid(
                row=idx, column=2, padx=5, pady=2, sticky="e"
            )
            entry = tk.Entry(self, width=10)
            entry.grid(row=idx, column=3, padx=5, pady=2, sticky="e")
            self.entries[item.id] = (entry, remaining, on_hand)

        row = len(self.items) + 2
        self.export_button = tk.Button(
            self, text="Export", state="disabled", command=self.export_packing_slip
        )
        self.export_button.grid(row=row, column=1, padx=5, pady=10, sticky="e")
        tk.Button(self, text="Record", command=self.record_shipping).grid(
            row=row, column=2, padx=5, pady=10, sticky="e"
        )
        tk.Button(self, text="Exit", command=self.destroy).grid(
            row=row, column=3, padx=5, pady=10, sticky="w"
        )

    def record_shipping(self):
        shipments: dict[int, float] = {}
        for item_id, (entry, remaining, on_hand) in self.entries.items():
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
            if qty > on_hand:
                messagebox.showerror(
                    "Validation Error",
                    f"Cannot ship more than on-hand ({on_hand}).",
                    parent=self,
                )
                return
            shipments[item_id] = qty

        if not shipments:
            messagebox.showwarning(
                "No Quantities", "Enter quantities to ship.", parent=self
            )
            return

        try:
            shipment_number = self.sales_logic.record_shipment(
                self.doc_id, shipments
            )
            self.last_shipments = shipments
            self.last_shipment_number = shipment_number
            self.export_button.config(state="normal")
            messagebox.showinfo("Success", "Shipment recorded.", parent=self)
            if self.refresh_callback:
                self.refresh_callback()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record shipment: {e}", parent=self)

    def export_packing_slip(self):
        if not self.last_shipments or not self.last_shipment_number:
            messagebox.showwarning(
                "No Shipment", "Record a shipment before exporting.", parent=self
            )
            return
        try:
            generate_packing_slip_pdf(
                self.doc_id, self.last_shipments, self.last_shipment_number
            )
            messagebox.showinfo("Success", "Packing slip generated.", parent=self)
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to generate packing slip: {e}", parent=self
            )
