import tkinter as tk
from tkinter import ttk, messagebox
from core.purchase_logic import PurchaseLogic
from core.logic.product_management import ProductLogic
from core.sales_logic import SalesLogic
from shared.structs import (
    PurchaseDocumentStatus,
    SalesDocumentStatus,
    SalesDocumentType,
)
from ui.inventory.record_receipt_popup import RecordReceiptPopup


class InventoryTab:
    def __init__(
        self,
        master,
        purchase_logic: PurchaseLogic,
        product_logic: ProductLogic,
        sales_logic: SalesLogic,
    ):
        self.frame = tk.Frame(master)
        self.purchase_logic = purchase_logic
        self.product_logic = product_logic
        self.sales_logic = sales_logic
        self.selected_item_id = None

        self.setup_to_receive_section()
        self.setup_ready_to_ship_section()
        self.frame.bind("<FocusIn>", self.refresh_lists)

    # --- To Receive Section ---
    def setup_to_receive_section(self):
        tk.Label(self.frame, text="To Receive").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.to_receive_tree = ttk.Treeview(
            self.frame,
            columns=("product", "ordered", "received", "remaining"),
            show="tree headings",
        )
        self.to_receive_tree.heading("#0", text="PO Number")
        self.to_receive_tree.heading("product", text="Product")
        self.to_receive_tree.heading("ordered", text="Ordered")
        self.to_receive_tree.heading("received", text="Received")
        self.to_receive_tree.heading("remaining", text="Remaining")
        self.to_receive_tree.column("#0", width=100)
        self.to_receive_tree.column("product", width=200)
        self.to_receive_tree.column("ordered", width=80, anchor=tk.E)
        self.to_receive_tree.column("received", width=80, anchor=tk.E)
        self.to_receive_tree.column("remaining", width=80, anchor=tk.E)
        self.to_receive_tree.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.to_receive_tree.bind("<<TreeviewSelect>>", self.on_select_item)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        tk.Button(self.frame, text="Record Receipt", command=self.open_receipt_popup).grid(row=2, column=0, padx=5, pady=5, sticky="w")

    # --- Ready to Ship Section ---
    def setup_ready_to_ship_section(self):
        tk.Label(self.frame, text="Ready to Ship").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.ready_tree = ttk.Treeview(
            self.frame,
            columns=("doc", "product", "ordered", "on_hand"),
            show="headings",
        )
        self.ready_tree.heading("doc", text="SO Number")
        self.ready_tree.heading("product", text="Product")
        self.ready_tree.heading("ordered", text="Ordered")
        self.ready_tree.heading("on_hand", text="On Hand")
        self.ready_tree.column("doc", width=100)
        self.ready_tree.column("product", width=200)
        self.ready_tree.column("ordered", width=80, anchor=tk.E)
        self.ready_tree.column("on_hand", width=80, anchor=tk.E)
        self.ready_tree.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.frame.grid_rowconfigure(4, weight=1)

    def on_select_item(self, event=None):
        selection = self.to_receive_tree.selection()
        if selection:
            try:
                self.selected_item_id = int(selection[0])
            except ValueError:
                self.selected_item_id = None
        else:
            self.selected_item_id = None

    def open_receipt_popup(self):
        if not self.selected_item_id:
            messagebox.showwarning("No Selection", "Please select an item to receive.", parent=self.frame)
            return
        item = self.purchase_logic.get_purchase_document_item_details(self.selected_item_id)
        if not item:
            messagebox.showerror("Error", "Could not load item details.", parent=self.frame)
            return
        popup = RecordReceiptPopup(self.frame.master, self.purchase_logic, item, self.refresh_lists)
        self.frame.master.wait_window(popup)

    def refresh_lists(self, event=None):
        self.refresh_to_receive()
        self.refresh_ready_to_ship()

    def refresh_to_receive(self):
        self.to_receive_tree.delete(*self.to_receive_tree.get_children())
        self.selected_item_id = None
        docs = self.purchase_logic.get_all_documents_by_criteria(status=PurchaseDocumentStatus.PO_ISSUED)
        for doc in docs:
            doc_iid = f"doc_{doc.id}"
            self.to_receive_tree.insert("", "end", iid=doc_iid, text=doc.document_number, open=False)
            items = self.purchase_logic.get_items_for_document(doc.id)
            for item in items:
                remaining = item.quantity - item.received_quantity
                if remaining > 0:
                    self.to_receive_tree.insert(
                        doc_iid,
                        "end",
                        iid=item.id,
                        text="",
                        values=(
                            item.product_description,
                            item.quantity,
                            item.received_quantity,
                            remaining,
                        ),
                    )

    def refresh_ready_to_ship(self):
        self.ready_tree.delete(*self.ready_tree.get_children())
        orders = self.sales_logic.get_all_sales_documents_by_criteria(
            doc_type=SalesDocumentType.SALES_ORDER,
            status=SalesDocumentStatus.SO_OPEN,
        )
        for doc in orders:
            items = self.sales_logic.get_items_for_sales_document(doc.id)
            for item in items:
                product = (
                    self.product_logic.get_product_details(item.product_id)
                    if item.product_id
                    else None
                )
                on_hand = product.quantity_on_hand if product else 0
                self.ready_tree.insert(
                    "",
                    "end",
                    iid=item.id,
                    values=(
                        doc.document_number,
                        item.product_description,
                        item.quantity,
                        on_hand,
                    ),
                )
