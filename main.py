"""
SmartCart — Main Entry Point
Launches the application window with sidebar navigation.

Run:  python main.py
"""

import sys
import os

# ── Path setup ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Dependency check ─────────────────────────────────────────────────────────
def check_deps():
    missing = []
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")
    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")
    if missing:
        print("\n" + "─" * 50)
        print("  SmartCart — Missing Dependencies")
        print("─" * 50)
        print("  Install with:")
        print(f"    pip install {' '.join(missing)}")
        print("─" * 50 + "\n")
        sys.exit(1)

check_deps()

# ── Imports ──────────────────────────────────────────────────────────────────
import tkinter as tk
from tkinter import ttk

from config import (
    CLR, STORE_NAME, STORE_TAGLINE,
    WINDOW_TITLE, WINDOW_SIZE, WINDOW_MIN, FONT_FAMILY
)
from data.db       import init_db
from modules.cart  import Cart
from modules.scanner import ScannerThread
from ui.widgets    import F, setup_treeview_style
from ui.scanner_panel  import ScannerPanel
from ui.cart_panel     import CartPanel
from ui.products_panel import ProductsPanel


# ── Application ───────────────────────────────────────────────────────────────
class SmartCartApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Core objects
        self.cart    = Cart()
        self.scanner = ScannerThread(on_scan=self._noop)

        # Window setup
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(*WINDOW_MIN)
        self.configure(bg=CLR["bg"])
        self.protocol("WM_DELETE_WINDOW", self._quit)

        setup_treeview_style()
        self._build()

    def _noop(self, *_): pass

    # ── Layout ───────────────────────────────────────────────────────────────
    def _build(self):
        # ── Sidebar ──────────────────────────────────────────────────────────
        self.sidebar = tk.Frame(self, bg=CLR["surface"],
                                width=200,
                                highlightthickness=1,
                                highlightbackground=CLR["border"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # ── Main content area ────────────────────────────────────────────────
        self.content = tk.Frame(self, bg=CLR["bg"])
        self.content.pack(side="left", fill="both", expand=True)

        # ── Scanner page: left cam + right cart ──────────────────────────────
        self.scanner_page = tk.Frame(self.content, bg=CLR["bg"])
        self.cart_page    = tk.Frame(self.content, bg=CLR["bg"])
        self.products_page = tk.Frame(self.content, bg=CLR["bg"])

        # Scanner panel (camera side)
        self.scanner_panel = ScannerPanel(
            self.scanner_page,
            scanner=self.scanner,
            on_scan_result=self._on_scan,
        )
        self.scanner_panel.pack(side="left", fill="y",
                                padx=(8, 4), pady=8)

        tk.Frame(self.scanner_page, bg=CLR["border"],
                 width=1).pack(side="left", fill="y", pady=8)

        # Cart panel (right side of scanner page)
        self.cart_panel = CartPanel(self.scanner_page, cart=self.cart)
        self.cart_panel.pack(side="left", fill="both", expand=True,
                             padx=(4, 8), pady=8)

        # Full-page cart view (sidebar nav)
        self.cart_panel_full = CartPanel(self.cart_page, cart=self.cart)
        self.cart_panel_full.pack(fill="both", expand=True, padx=8, pady=8)

        # Products page
        self.products_panel = ProductsPanel(self.products_page)
        self.products_panel.pack(fill="both", expand=True, padx=8, pady=8)

        # Show default page
        self._navigate("scanner")

    def _build_sidebar(self):
        # Logo
        logo = tk.Frame(self.sidebar, bg=CLR["surface"])
        logo.pack(fill="x", pady=(20, 8))
        tk.Label(logo, text="🛒", bg=CLR["surface"],
                 fg=CLR["accent"], font=(FONT_FAMILY, 28)).pack()
        tk.Label(logo, text=STORE_NAME, bg=CLR["surface"],
                 fg=CLR["text"], font=F(14, bold=True)).pack()
        tk.Label(logo, text=STORE_TAGLINE, bg=CLR["surface"],
                 fg=CLR["text3"], font=F(8)).pack()

        tk.Frame(self.sidebar, bg=CLR["border"], height=1).pack(
            fill="x", pady=12, padx=16)

        # Nav items
        self._nav_btns = {}
        nav_items = [
            ("scanner",  "◉  Scanner",         "Scan & Cart"),
            ("cart",     "☰  Cart View",        "Full bill view"),
            ("products", "⊞  Product Database", "Add / edit products"),
        ]
        for key, label, sub in nav_items:
            btn = self._nav_btn(key, label, sub)
            self._nav_btns[key] = btn

        # Bottom: live cart summary in sidebar
        tk.Frame(self.sidebar, bg=CLR["border"], height=1).pack(
            fill="x", padx=16, pady=(12, 8))

        self.sb_items = self._sidebar_stat("Items", "0")
        self.sb_total = self._sidebar_stat("Total", "₹0.00", color=CLR["ok"])

        # Version
        tk.Label(self.sidebar, text="SmartCart v1.0",
                 bg=CLR["surface"], fg=CLR["text3"],
                 font=F(8)).pack(side="bottom", pady=12)

    def _nav_btn(self, key, label, subtitle):
        f = tk.Frame(self.sidebar, bg=CLR["surface"], cursor="hand2")
        f.pack(fill="x", padx=8, pady=2)

        inner = tk.Frame(f, bg=CLR["surface"])
        inner.pack(fill="x", padx=8, pady=8)
        tk.Label(inner, text=label, bg=CLR["surface"],
                 fg=CLR["text"], font=F(10, bold=True),
                 anchor="w").pack(fill="x")
        tk.Label(inner, text=subtitle, bg=CLR["surface"],
                 fg=CLR["text3"], font=F(8),
                 anchor="w").pack(fill="x")

        def on_click(_=None):
            self._navigate(key)

        for w in [f, inner] + inner.winfo_children():
            w.bind("<Button-1>", on_click)
            w.bind("<Enter>", lambda e, fw=f: fw.config(bg=CLR["surface2"]))
            w.bind("<Leave>", lambda e, fw=f: fw.config(
                bg=CLR["accent_glow"] if fw._active else CLR["surface"]))

        f._active = False
        return f

    def _navigate(self, key):
        # Hide all pages
        for page in [self.scanner_page, self.cart_page, self.products_page]:
            page.pack_forget()

        # Reset nav btn styles
        for k, btn in self._nav_btns.items():
            btn.config(bg=CLR["surface"])
            btn._active = False

        # Show selected + highlight
        self._nav_btns[key].config(bg=CLR["accent_glow"])
        self._nav_btns[key]._active = True

        if key == "scanner":
            self.scanner_page.pack(fill="both", expand=True)
        elif key == "cart":
            self.cart_panel_full.refresh()
            self.cart_page.pack(fill="both", expand=True)
        elif key == "products":
            self.products_page.pack(fill="both", expand=True)

    # ── Scan handler ─────────────────────────────────────────────────────────
    def _on_scan(self, barcode: str) -> dict:
        """Called by ScannerPanel. Looks up product and adds to cart."""
        from data.db import get_product
        product = get_product(barcode)
        if not product:
            return {"ok": False, "message": f"Unknown barcode: {barcode}"}

        ok, msg = self.cart.add(product)
        self.cart_panel.refresh()
        self._update_sidebar_stats()
        return {"ok": ok, "message": msg}

    def _update_sidebar_stats(self):
        self.sb_items.config(text=str(self.cart.total_items()))
        total = self.cart.grand_total()
        self.sb_total.config(text=f"₹{total:.2f}",
                             fg=CLR["ok"] if total > 0 else CLR["text3"])

    def _sidebar_stat(self, label, value, color=None):
        f = tk.Frame(self.sidebar, bg=CLR["surface"])
        f.pack(fill="x", padx=16, pady=2)
        tk.Label(f, text=label, bg=CLR["surface"],
                 fg=CLR["text3"], font=F(9)).pack(side="left")
        lbl = tk.Label(f, text=value, bg=CLR["surface"],
                       fg=color or CLR["text2"], font=F(10, bold=True))
        lbl.pack(side="right")
        return lbl

    # ── Shutdown ──────────────────────────────────────────────────────────────
    def _quit(self):
        try:
            self.scanner_panel.shutdown()
        except Exception:
            pass
        self.destroy()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("SmartCart — Initialising database…")
    init_db()
    print("SmartCart — Starting UI…")
    app = SmartCartApp()
    app.mainloop()
