"""
SmartCart — Bill Generation Module
Generates formatted text bills and exports them.
"""

import os
from datetime import datetime
from config import (
    STORE_NAME, STORE_TAGLINE, STORE_ADDRESS, STORE_PHONE,
    CURRENCY, GST_RATE, BILLS_DIR
)


def generate_text_bill(cart_dict: dict, bill_number: str = None) -> str:
    """Returns a fully formatted plain-text bill string."""
    now    = datetime.now()
    bn     = bill_number or f"SC{now.strftime('%Y%m%d%H%M%S')}"
    W      = 54   # bill width
    sep    = "─" * W
    sep2   = "═" * W

    def center(text):
        return text.center(W)

    def rrow(label, value, bold=False):
        gap = W - len(label) - len(value)
        return f"  {label}{' ' * max(gap - 4, 1)}{value}"

    lines = [
        sep2,
        center(f"  {STORE_NAME}  "),
        center(STORE_TAGLINE),
        center(STORE_ADDRESS),
        center(STORE_PHONE),
        sep2,
        f"  Bill No  : {bn}",
        f"  Date     : {now.strftime('%d %b %Y')}",
        f"  Time     : {now.strftime('%I:%M:%S %p')}",
        sep,
        f"  {'Item':<28} {'Qty':>4} {'Rate':>6} {'Amt':>9}",
        sep,
    ]

    for item in cart_dict["items"]:
        name    = item["name"][:28]
        qty     = item["qty"]
        price   = item["price"]
        sub     = item["subtotal"]
        lines.append(f"  {name:<28} {qty:>4} {CURRENCY}{price:>5.0f} {CURRENCY}{sub:>8.2f}")
        if item.get("unit") and item["unit"] != "piece":
            lines.append(f"    ({item['unit']})")

    lines += [
        sep,
        rrow("Items",           f"{cart_dict['item_count']}"),
        rrow("Subtotal",        f"{CURRENCY}{cart_dict['subtotal']:.2f}"),
        rrow(f"GST ({GST_RATE*100:.0f}%)", f"{CURRENCY}{cart_dict['gst']:.2f}"),
        sep2,
        rrow("GRAND TOTAL",     f"{CURRENCY}{cart_dict['grand_total']:.2f}"),
        sep2,
        "",
        center("Thank you for shopping!"),
        center("Please visit again  🛍"),
        "",
        sep,
    ]
    return "\n".join(lines)


def save_bill(cart_dict: dict, path: str = None) -> str:
    """Save bill to file. Returns the saved file path."""
    os.makedirs(BILLS_DIR, exist_ok=True)
    if not path:
        bn   = f"SC{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        path = os.path.join(BILLS_DIR, f"{bn}.txt")
    text = generate_text_bill(cart_dict)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def next_bill_number() -> str:
    """Auto-increment bill number based on existing files."""
    os.makedirs(BILLS_DIR, exist_ok=True)
    existing = [f for f in os.listdir(BILLS_DIR) if f.endswith(".txt")]
    return f"SC{len(existing) + 1:05d}"
