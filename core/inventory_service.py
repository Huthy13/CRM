from __future__ import annotations

from typing import Optional

from core.repositories import InventoryRepository, ProductRepository
from shared.structs import InventoryTransactionType


class InventoryService:
    """Service layer for inventory adjustments and replenishment checks."""

    def __init__(self, inventory_repo: InventoryRepository, product_repo: ProductRepository):
        self.inventory_repo = inventory_repo
        self.product_repo = product_repo

    def adjust_stock(
        self,
        product_id: int,
        quantity_change: float,
        transaction_type: InventoryTransactionType,
        reference: Optional[str] = None,
    ) -> float:
        """Adjust stock, log transaction, and enqueue replenishment if needed.

        Returns the updated stock level.
        """
        self.inventory_repo.log_transaction(
            product_id, quantity_change, transaction_type.value, reference
        )
        stock_level = self.inventory_repo.get_stock_level(product_id)
        product = self.product_repo.get_product_details(product_id)
        if not product:
            return stock_level

        reorder_point = product.get("reorder_point") or 0
        reorder_qty = product.get("reorder_quantity") or 0
        safety_stock = product.get("safety_stock") or 0
        if stock_level <= reorder_point or stock_level <= safety_stock:
            qty_needed = reorder_qty or max(reorder_point - stock_level, 0)
            self.inventory_repo.add_replenishment_item(product_id, qty_needed)
        return stock_level

    def record_adjustment(
        self, product_id: int, quantity_change: float, reference: Optional[str] = None
    ) -> float:
        """Manually adjust inventory and log an adjustment transaction."""
        return self.adjust_stock(
            product_id, quantity_change, InventoryTransactionType.ADJUSTMENT, reference
        )

    def record_purchase_order(
        self, product_id: int, quantity: float, reference: Optional[str] = None
    ) -> float:
        """Log a purchase order quantity without affecting on-hand stock."""
        self.inventory_repo.log_transaction(
            product_id, quantity, InventoryTransactionType.PURCHASE_ORDER.value, reference
        )
        return self.inventory_repo.get_on_order_level(product_id)

    def get_on_order_level(self, product_id: int) -> float:
        """Return the quantity currently on order for a product."""
        return self.inventory_repo.get_on_order_level(product_id)

    def get_products_on_order(self) -> list[dict]:
        """Return products with aggregated on-order quantities and on-hand stock."""
        entries = self.inventory_repo.get_all_on_order_levels()
        result = []
        for entry in entries:
            pid = entry.get("product_id")
            product = self.product_repo.get_product_details(pid)
            if not product:
                continue
            result.append(
                {
                    "product_id": pid,
                    "name": product.get("name"),
                    "on_hand": product.get("quantity_on_hand", 0),
                    "on_order": entry.get("qty", 0),
                }
            )
        return result
