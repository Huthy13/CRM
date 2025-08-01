from __future__ import annotations

import datetime
from typing import List, Optional

from core.inventory_service import InventoryService
from core.repositories import PurchaseOrderRepository
from shared.structs import (
    InventoryTransactionType,
    PurchaseOrder,
    PurchaseOrderLineItem,
    PurchaseOrderStatus,
)


class PurchaseOrderService:
    """Service layer coordinating purchase orders and inventory updates."""

    def __init__(
        self,
        po_repo: PurchaseOrderRepository,
        inventory_service: InventoryService,
    ):
        self.po_repo = po_repo
        self.inventory_service = inventory_service

    def create_purchase_order(
        self,
        vendor_id: int,
        items: List[PurchaseOrderLineItem],
        expected_date: Optional[str] = None,
    ) -> PurchaseOrder:
        order_id = self.po_repo.add_purchase_order(
            vendor_id=vendor_id,
            order_date=datetime.date.today().isoformat(),
            status=PurchaseOrderStatus.OPEN.value,
            expected_date=expected_date,
        )
        for item in items:
            self.po_repo.add_line_item(
                purchase_order_id=order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
            )
        data = self.po_repo.get_purchase_order_by_id(order_id)
        return PurchaseOrder(
            id=data["id"],
            vendor_id=data["vendor_id"],
            order_date=data["order_date"],
            status=PurchaseOrderStatus(data["status"]),
            expected_date=data.get("expected_date"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def receive_purchase_order(self, order_id: int) -> PurchaseOrder:
        items = self.po_repo.get_line_items_for_order(order_id)
        for item in items:
            self.inventory_service.adjust_stock(
                item["product_id"],
                item["quantity"],
                InventoryTransactionType.PURCHASE,
                reference=f"PO#{order_id}",
            )
        self.po_repo.update_purchase_order_status(
            order_id, PurchaseOrderStatus.RECEIVED.value
        )
        data = self.po_repo.get_purchase_order_by_id(order_id)
        return PurchaseOrder(
            id=data["id"],
            vendor_id=data["vendor_id"],
            order_date=data["order_date"],
            status=PurchaseOrderStatus(data["status"]),
            expected_date=data.get("expected_date"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
