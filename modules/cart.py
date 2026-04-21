"""
SmartCart — Cart Module
Pure business logic: no UI dependencies.
"""

from config import GST_RATE, CURRENCY
from datetime import datetime


class CartItem:
    def __init__(self, barcode, name, category, price, unit, qty=1):
        self.barcode  = barcode
        self.name     = name
        self.category = category
        self.price    = price
        self.unit     = unit
        self.qty      = qty

    @property
    def subtotal(self):
        return round(self.price * self.qty, 2)

    def to_dict(self):
        return {
            "barcode":  self.barcode,
            "name":     self.name,
            "category": self.category,
            "price":    self.price,
            "unit":     self.unit,
            "qty":      self.qty,
            "subtotal": self.subtotal,
        }


class Cart:
    def __init__(self):
        self._items: dict[str, CartItem] = {}  # barcode → CartItem

    # ── Add / Remove ─────────────────────────────────────────────────────────
    def add(self, product: dict, qty: int = 1) -> tuple[bool, str]:
        """
        product = dict from db.get_product().
        Returns (success, message).
        """
        bc = product["barcode"]
        if bc in self._items:
            self._items[bc].qty += qty
        else:
            self._items[bc] = CartItem(
                barcode  = bc,
                name     = product["name"],
                category = product["category"],
                price    = product["price"],
                unit     = product.get("unit", "piece"),
                qty      = qty,
            )
        item = self._items[bc]
        return True, f"{item.name}  ×{item.qty}  — {CURRENCY}{item.subtotal:.2f}"

    def set_qty(self, barcode: str, qty: int):
        if qty <= 0:
            self._items.pop(barcode, None)
        elif barcode in self._items:
            self._items[barcode].qty = qty

    def remove(self, barcode: str):
        self._items.pop(barcode, None)

    def clear(self):
        self._items.clear()

    # ── Totals ───────────────────────────────────────────────────────────────
    def subtotal(self) -> float:
        return round(sum(i.subtotal for i in self._items.values()), 2)

    def gst_amount(self) -> float:
        return round(self.subtotal() * GST_RATE, 2)

    def grand_total(self) -> float:
        return round(self.subtotal() + self.gst_amount(), 2)

    def total_items(self) -> int:
        return sum(i.qty for i in self._items.values())

    def unique_count(self) -> int:
        return len(self._items)

    # ── Accessors ────────────────────────────────────────────────────────────
    def items(self):
        return list(self._items.values())

    def get_item(self, barcode):
        return self._items.get(barcode)

    def is_empty(self) -> bool:
        return len(self._items) == 0

    # ── Serialisation ────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "items":       [i.to_dict() for i in self._items.values()],
            "subtotal":    self.subtotal(),
            "gst":         self.gst_amount(),
            "grand_total": self.grand_total(),
            "item_count":  self.total_items(),
            "timestamp":   datetime.now().isoformat(),
        }
