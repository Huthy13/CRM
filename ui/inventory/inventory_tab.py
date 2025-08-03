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
from ui.inventory.record_shipping_popup import RecordShippingPopup


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
        self.selected_ready_item_id = None
        self.selected_ready_doc_id = None

        self.setup_to_order_section()
        self.setup_to_receive_section()
        self.setup_ready_to_ship_section()
        self.frame.bind("<FocusIn>", self.refresh_lists)

    # --- To Order Section ---
    def setup_to_order_section(self):
        tk.Label(self.frame, text="To Order").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.to_order_tree = ttk.Treeview(
            self.frame,
            columns=("product", "on_hand", "on_order", "to_order"),
            show="tree headings",
        )
        self.to_order_tree.heading("#0", text="SO Number")
        self.to_order_tree.heading("product", text="Product")
        self.to_order_tree.heading("on_hand", text="On Hand")
        self.to_order_tree.heading("on_order", text="On Order")
        self.to_order_tree.heading("to_order", text="To Order")
        self.to_order_tree.column("#0", width=100)
        self.to_order_tree.column("product", width=200)
        self.to_order_tree.column("on_hand", width=80, anchor=tk.E)
        self.to_order_tree.column("on_order", width=80, anchor=tk.E)
        self.to_order_tree.column("to_order", width=80, anchor=tk.E)
        self.to_order_tree.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

    # --- To Receive Section ---
    def setup_to_receive_section(self):
        tk.Label(self.frame, text="To Receive").grid(row=2, column=0, padx=5, pady=5, sticky="w")
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
        self.to_receive_tree.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.to_receive_tree.bind("<<TreeviewSelect>>", self.on_select_item)
        self.frame.grid_rowconfigure(3, weight=1)

        tk.Button(self.frame, text="Record Receipt", command=self.open_receipt_popup).grid(row=4, column=0, padx=5, pady=5, sticky="w")

    # --- Ready to Ship Section ---
    def setup_ready_to_ship_section(self):
        tk.Label(self.frame, text="Ready to Ship").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.ready_tree = ttk.Treeview(
            self.frame,
            columns=("product", "ordered", "shipped", "remaining", "on_hand"),
            show="tree headings",
        )
        self.ready_tree.heading("#0", text="SO Number")
        self.ready_tree.heading("product", text="Product")
        self.ready_tree.heading("ordered", text="Customer Ordered")
        self.ready_tree.heading("shipped", text="Shipped")
        self.ready_tree.heading("remaining", text="Remaining to Ship")
        self.ready_tree.heading("on_hand", text="On Hand")
        self.ready_tree.column("#0", width=100)
        self.ready_tree.column("product", width=200)
        self.ready_tree.column("ordered", width=80, anchor=tk.E)
        self.ready_tree.column("shipped", width=80, anchor=tk.E)
        self.ready_tree.column("remaining", width=120, anchor=tk.E)
        self.ready_tree.column("on_hand", width=80, anchor=tk.E)
        self.ready_tree.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.ready_tree.bind("<<TreeviewSelect>>", self.on_select_ready_item)
        self.frame.grid_rowconfigure(6, weight=1)

        tk.Button(self.frame, text="Record Shipping", command=self.open_shipping_popup).grid(row=7, column=0, padx=5, pady=5, sticky="w")

    def on_select_item(self, event=None):
        selection = self.to_receive_tree.selection()
        if selection:
            try:
                self.selected_item_id = int(selection[0])
            except ValueError:
                self.selected_item_id = None
        else:
            self.selected_item_id = None

    def on_select_ready_item(self, event=None):
        selection = self.ready_tree.selection()
        if selection:
            iid = selection[0]
            if iid.startswith("doc_"):
                try:
                    self.selected_ready_doc_id = int(iid.split("_")[1])
                except ValueError:
                    self.selected_ready_doc_id = None
                self.selected_ready_item_id = None
            else:
                try:
                    self.selected_ready_item_id = int(iid)
                except ValueError:
                    self.selected_ready_item_id = None
                self.selected_ready_doc_id = None
        else:
            self.selected_ready_item_id = None
            self.selected_ready_doc_id = None

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

    def open_shipping_popup(self):
        doc_id = None
        if self.selected_ready_doc_id:
            doc_id = self.selected_ready_doc_id
        elif self.selected_ready_item_id:
            item = self.sales_logic.get_sales_document_item_details(self.selected_ready_item_id)
            if not item:
                messagebox.showerror("Error", "Could not load item details.", parent=self.frame)
                return
            doc_id = item.sales_document_id
        else:
            messagebox.showwarning("No Selection", "Please select an order or item to ship.", parent=self.frame)
            return

        items = self.sales_logic.get_items_for_sales_document(doc_id)
        item_data = []
        for item in items:
            remaining = item.quantity - item.shipped_quantity
            if remaining <= 0:
                continue
            product = (
                self.product_logic.get_product_details(item.product_id)
                if item.product_id
                else None
            )
            on_hand = product.quantity_on_hand if product else 0
            item_data.append((item, on_hand))

        if not item_data:
            messagebox.showinfo("No Items", "No items remaining to ship.", parent=self.frame)
            return

        popup = RecordShippingPopup(
            self.frame.master, self.sales_logic, doc_id, item_data, self.refresh_lists
        )
        self.frame.master.wait_window(popup)

    def refresh_lists(self, event=None):
        self.refresh_to_order()
        self.refresh_to_receive()
        self.refresh_ready_to_ship()

    def refresh_to_order(self):
        expanded_docs = {
            iid
            for iid in self.to_order_tree.get_children()
            if self.to_order_tree.item(iid, "open")
        }
        self.to_order_tree.delete(*self.to_order_tree.get_children())
        orders = self.sales_logic.get_all_sales_documents_by_criteria(
            doc_type=SalesDocumentType.SALES_ORDER,
            status=SalesDocumentStatus.SO_OPEN,
        )
        for doc in orders:
            doc_iid = f"doc_{doc.id}"
            is_open = doc_iid in expanded_docs
            items = self.sales_logic.get_items_for_sales_document(doc.id)
            doc_inserted = False
            for item in items:
                product = (
                    self.product_logic.get_product_details(item.product_id)
                    if item.product_id
                    else None
                )
                on_hand = product.quantity_on_hand if product else 0
                on_order = (
                    self.purchase_logic.inventory_service.get_on_order_level(item.product_id)
                    if item.product_id
                    else 0
                )
                remaining_qty = item.quantity - item.shipped_quantity
                to_order = remaining_qty - (on_hand + on_order)
                if to_order > 0:
                    if not doc_inserted:
                        self.to_order_tree.insert(
                            "", "end", iid=doc_iid, text=doc.document_number, open=is_open
                        )
                        doc_inserted = True
                    self.to_order_tree.insert(
                        doc_iid,
                        "end",
                        iid=item.id,
                        text="",
                        values=(
                            item.product_description,
                            on_hand,
                            on_order,
                            to_order,
                        ),
                    )
    def refresh_to_receive(self):
        expanded_docs = {
            iid
            for iid in self.to_receive_tree.get_children()
            if self.to_receive_tree.item(iid, "open")
        }
        self.to_receive_tree.delete(*self.to_receive_tree.get_children())
        self.selected_item_id = None
        docs = self.purchase_logic.get_all_documents_by_criteria(
            status=PurchaseDocumentStatus.PO_ISSUED
        )
        for doc in docs:
            doc_iid = f"doc_{doc.id}"
            is_open = doc_iid in expanded_docs
            self.to_receive_tree.insert(
                "", "end", iid=doc_iid, text=doc.document_number, open=is_open
            )
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
        expanded_docs = {
            iid
            for iid in self.ready_tree.get_children()
            if self.ready_tree.item(iid, "open")
        }
        self.ready_tree.delete(*self.ready_tree.get_children())
        self.selected_ready_item_id = None
        orders = self.sales_logic.get_all_sales_documents_by_criteria(
            doc_type=SalesDocumentType.SALES_ORDER,
            status=SalesDocumentStatus.SO_OPEN,
        )
        for doc in orders:
            doc_iid = f"doc_{doc.id}"
            is_open = doc_iid in expanded_docs
            items = self.sales_logic.get_items_for_sales_document(doc.id)
            doc_inserted = False
            for item in items:
                remaining = item.quantity - item.shipped_quantity
                if remaining <= 0:
                    continue
                product = (
                    self.product_logic.get_product_details(item.product_id)
                    if item.product_id
                    else None
                )
                on_hand = product.quantity_on_hand if product else 0
                if not doc_inserted:
                    self.ready_tree.insert(
                        "",
                        "end",
                        iid=doc_iid,
                        text=doc.document_number,
                        open=is_open,
                    )
                    doc_inserted = True
                self.ready_tree.insert(
                    doc_iid,
                    "end",
                    iid=item.id,
                    text="",
                    values=(
                        item.product_description,
                        item.quantity,
                        item.shipped_quantity,
                        remaining,
                        on_hand,
                    ),
                )
