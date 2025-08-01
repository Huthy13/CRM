from __future__ import annotations

from typing import Dict, List

from core.repositories import InventoryRepository, ProductRepository
from core.purchase_order_service import PurchaseOrderService
from shared.structs import PurchaseOrderLineItem


class ReplenishmentService:
    """Service for turning replenishment queue items into purchase orders."""

    def __init__(
        self,
        inventory_repo: InventoryRepository,
        product_repo: ProductRepository,
        po_service: PurchaseOrderService,
    ):
        self.inventory_repo = inventory_repo
        self.product_repo = product_repo
        self.po_service = po_service

    def process_queue(self) -> List[int]:
        """Group queued items by supplier and create purchase orders.

        Returns a list of created purchase order IDs.
        """
        queue_items = self.inventory_repo.get_replenishment_queue()
        grouped: Dict[int, List[dict]] = {}
        for item in queue_items:
            vendor_id = self.product_repo.get_default_vendor(item["product_id"])
            if vendor_id is None:
                continue
            grouped.setdefault(vendor_id, []).append(item)

        created_orders: List[int] = []
        for vendor_id, items in grouped.items():
            line_items = [
                PurchaseOrderLineItem(
                    product_id=q["product_id"],
                    quantity=q["quantity_needed"],
                )
                for q in items
            ]
            po = self.po_service.create_purchase_order(vendor_id, line_items)
            created_orders.append(po.id)
            for q in items:
                self.inventory_repo.remove_replenishment_item(q["id"])
        return created_orders
