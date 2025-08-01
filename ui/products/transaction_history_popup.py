import tkinter as tk
from tkinter import ttk, messagebox
from core.inventory_service import InventoryService


class TransactionHistoryPopup(tk.Toplevel):
    def __init__(self, master, inventory_service: InventoryService, product_id: int):
        super().__init__(master)
        self.inventory_service = inventory_service
        self.product_id = product_id
        self.title("Transaction History")
        self.geometry("600x300")

        self.tree = ttk.Treeview(
            self,
            columns=("type", "qty", "reference", "timestamp"),
            show="headings",
        )
        self.tree.heading("type", text="Type")
        self.tree.heading("qty", text="Qty Change")
        self.tree.heading("reference", text="Reference")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.column("type", width=100)
        self.tree.column("qty", width=80)
        self.tree.column("reference", width=200)
        self.tree.column("timestamp", width=150)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.load_transactions()

    def load_transactions(self):
        self.tree.delete(*self.tree.get_children())
        try:
            transactions = self.inventory_service.inventory_repo.get_transactions(self.product_id)
            for t in transactions:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        t.get("transaction_type"),
                        t.get("quantity_change"),
                        t.get("reference", ""),
                        t.get("created_at"),
                    ),
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load transactions: {e}", parent=self)
