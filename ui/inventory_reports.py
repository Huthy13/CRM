import tkinter as tk
from tkinter import ttk, messagebox
from core.inventory_service import InventoryService
from core.purchase_logic import PurchaseLogic
from core.logic.product_management import ProductLogic
from shared.structs import PurchaseDocumentStatus


class InventoryReportPopup(tk.Toplevel):
    def __init__(self, master, product_logic: ProductLogic, inventory_service: InventoryService, purchase_logic: PurchaseLogic):
        super().__init__(master)
        self.product_logic = product_logic
        self.inventory_service = inventory_service
        self.purchase_logic = purchase_logic
        self.title("Inventory Reports")
        self.geometry("700x400")

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Low stock tab
        low_tab = tk.Frame(notebook)
        notebook.add(low_tab, text="Low Stock")
        self.low_tree = ttk.Treeview(
            low_tab,
            columns=("name", "on_hand", "reorder_point", "safety_stock"),
            show="headings",
        )
        self.low_tree.heading("name", text="Product")
        self.low_tree.heading("on_hand", text="On Hand")
        self.low_tree.heading("reorder_point", text="Reorder Point")
        self.low_tree.heading("safety_stock", text="Safety Stock")
        self.low_tree.column("name", width=200)
        self.low_tree.column("on_hand", width=80)
        self.low_tree.column("reorder_point", width=100)
        self.low_tree.column("safety_stock", width=100)
        self.low_tree.pack(fill=tk.BOTH, expand=True)

        # Open purchase orders tab
        po_tab = tk.Frame(notebook)
        notebook.add(po_tab, text="Open POs")
        self.po_tree = ttk.Treeview(
            po_tab,
            columns=("number", "status", "vendor"),
            show="headings",
        )
        self.po_tree.heading("number", text="PO Number")
        self.po_tree.heading("status", text="Status")
        self.po_tree.heading("vendor", text="Vendor ID")
        self.po_tree.column("number", width=150)
        self.po_tree.column("status", width=120)
        self.po_tree.column("vendor", width=100)
        self.po_tree.pack(fill=tk.BOTH, expand=True)

        # Transactions tab
        txn_tab = tk.Frame(notebook)
        notebook.add(txn_tab, text="Transactions")
        self.txn_tree = ttk.Treeview(
            txn_tab,
            columns=("product_id", "type", "qty", "reference", "timestamp"),
            show="headings",
        )
        self.txn_tree.heading("product_id", text="Product ID")
        self.txn_tree.heading("type", text="Type")
        self.txn_tree.heading("qty", text="Qty")
        self.txn_tree.heading("reference", text="Reference")
        self.txn_tree.heading("timestamp", text="Timestamp")
        self.txn_tree.column("product_id", width=80)
        self.txn_tree.column("type", width=100)
        self.txn_tree.column("qty", width=60)
        self.txn_tree.column("reference", width=200)
        self.txn_tree.column("timestamp", width=150)
        self.txn_tree.pack(fill=tk.BOTH, expand=True)

        self.populate_low_stock()
        self.populate_open_pos()
        self.populate_transactions()

    def populate_low_stock(self):
        try:
            products = self.product_logic.get_all_products()
            for p in products:
                if p.quantity_on_hand <= p.reorder_point or p.quantity_on_hand <= p.safety_stock:
                    self.low_tree.insert(
                        "",
                        "end",
                        values=(p.name, p.quantity_on_hand, p.reorder_point, p.safety_stock),
                    )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load low stock items: {e}", parent=self)

    def populate_open_pos(self):
        try:
            pos = self.purchase_logic.get_all_documents_by_criteria(status=PurchaseDocumentStatus.PO_ISSUED)
            for po in pos:
                status_val = po.status.value if po.status else ""
                self.po_tree.insert("", "end", values=(po.document_number, status_val, po.vendor_id))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load purchase orders: {e}", parent=self)

    def populate_transactions(self):
        try:
            txns = self.inventory_service.inventory_repo.get_transactions()
            for t in txns:
                self.txn_tree.insert(
                    "",
                    "end",
                    values=(
                        t.get("product_id"),
                        t.get("transaction_type"),
                        t.get("quantity_change"),
                        t.get("reference", ""),
                        t.get("created_at"),
                    ),
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load transactions: {e}", parent=self)
