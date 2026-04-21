"""
SmartCart — Products Management Panel
Full CRUD: browse, search, add, edit, delete products in the database.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import CLR, CURRENCY, FONT_FAMILY
from ui.widgets import (
    Card, SectionHeader, IconButton, FeedbackLabel,
    setup_treeview_style, F
)
from data import db


class ProductsPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=CLR["bg"], **kw)
        self._selected_barcode = None
        self._build()
        self._load()

    def _build(self):
        setup_treeview_style()

        # ── Toolbar ────────────────────────────────────────────────────────────
        tb = tk.Frame(self, bg=CLR["surface2"],
                      highlightthickness=1, highlightbackground=CLR["border"])
        tb.pack(fill="x", pady=(0, 1))
        inner = tk.Frame(tb, bg=CLR["surface2"])
        inner.pack(fill="x", padx=12, pady=8)

        tk.Label(inner, text="Products Database",
                 bg=CLR["surface2"], fg=CLR["text"],
                 font=F(13, bold=True)).pack(side="left")

        # Right-side toolbar buttons
        right = tk.Frame(inner, bg=CLR["surface2"])
        right.pack(side="right")
        for lbl, cmd, style in [
            ("Add Product", self._open_add,    "primary"),
            ("Edit",        self._open_edit,   "ghost"),
            ("Delete",      self._delete_row,  "red"),
        ]:
            IconButton(right, text=lbl, command=cmd,
                       style=style).pack(side="left", padx=(6, 0))

        tk.Frame(tb, bg=CLR["border"], height=1).pack(fill="x")

        # ── Search bar ────────────────────────────────────────────────────────
        search_card = Card(self)
        search_card.pack(fill="x", pady=1)
        sc = tk.Frame(search_card, bg=CLR["surface"])
        sc.pack(fill="x", padx=12, pady=8)

        tk.Label(sc, text="Search:", bg=CLR["surface"],
                 fg=CLR["text2"], font=F(10)).pack(side="left", padx=(0, 8))

        self.search_var = tk.StringVar()
        ent = tk.Entry(
            sc, textvariable=self.search_var,
            bg=CLR["surface2"], fg=CLR["text"],
            insertbackground=CLR["accent"],
            relief="flat", font=F(11), width=28,
            highlightthickness=1,
            highlightbackground=CLR["border"],
            highlightcolor=CLR["accent"],
        )
        ent.pack(side="left", ipady=5, padx=(0, 8))
        ent.bind("<KeyRelease>", lambda e: self._search())

        IconButton(sc, text="Search", command=self._search,
                   style="primary").pack(side="left", padx=(0, 8))
        IconButton(sc, text="Show All", command=self._load,
                   style="ghost").pack(side="left")

        self.count_lbl = tk.Label(sc, text="", bg=CLR["surface"],
                                  fg=CLR["text3"], font=F(9))
        self.count_lbl.pack(side="right")

        # ── Product table ─────────────────────────────────────────────────────
        tbl_card = Card(self)
        tbl_card.pack(fill="both", expand=True, pady=1)

        cols = ("barcode", "name", "category", "price", "unit")
        self.tree = ttk.Treeview(
            tbl_card, columns=cols, show="headings",
            selectmode="browse", height=16, style="SC.Treeview"
        )
        for col, hdr, w, anc in [
            ("barcode",  "Barcode",   150, "w"),
            ("name",     "Product Name", 240, "w"),
            ("category", "Category",  120, "w"),
            ("price",    "Price",      90, "e"),
            ("unit",     "Unit",       80, "center"),
        ]:
            self.tree.heading(col, text=hdr, anchor=anc)
            self.tree.column(col, width=w, anchor=anc, minwidth=50)

        vsb = ttk.Scrollbar(tbl_card, orient="vertical",
                             command=self.tree.yview)
        self.tree.config(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("odd",  background=CLR["surface"])
        self.tree.tag_configure("even", background=CLR["surface2"])
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._open_edit())

        # ── Bottom feedback ───────────────────────────────────────────────────
        self.fb = FeedbackLabel(self)
        self.fb.pack(fill="x", padx=4, pady=4)

    # ── Data loading ──────────────────────────────────────────────────────────
    def _load(self):
        rows = db.get_all_products()
        self._populate(rows)

    def _search(self):
        q = self.search_var.get().strip()
        rows = db.search_products(q) if q else db.get_all_products()
        self._populate(rows)

    def _populate(self, rows):
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            tag = "odd" if i % 2 == 0 else "even"
            self.tree.insert("", "end", iid=r["barcode"], tags=(tag,), values=(
                r["barcode"],
                r["name"],
                r["category"],
                f"{CURRENCY}{r['price']:.2f}",
                r["unit"],
            ))
        self.count_lbl.config(text=f"{len(rows)} products")
        self._selected_barcode = None

    def _on_select(self, _):
        sel = self.tree.selection()
        self._selected_barcode = sel[0] if sel else None

    # ── CRUD actions ──────────────────────────────────────────────────────────
    def _open_add(self):
        ProductForm(self, mode="add", on_save=self._after_save)

    def _open_edit(self):
        bc = self._selected_barcode
        if not bc:
            self.fb.show("Select a product row first.", "warn")
            return
        product = db.get_product(bc)
        if product:
            ProductForm(self, mode="edit", product=product, on_save=self._after_save)

    def _delete_row(self):
        bc = self._selected_barcode
        if not bc:
            self.fb.show("Select a product row first.", "warn")
            return
        product = db.get_product(bc)
        if not product:
            return
        if messagebox.askyesno("Delete product",
                               f"Delete  '{product['name']}'?\nThis cannot be undone.",
                               parent=self):
            db.delete_product(bc)
            self._load()
            self.fb.show(f"Deleted: {product['name']}", "warn")

    def _after_save(self, msg):
        self._load()
        self.fb.show(msg, "ok")


# ── Product Add / Edit Form ───────────────────────────────────────────────────
class ProductForm(tk.Toplevel):
    def __init__(self, parent, mode="add", product=None, on_save=None):
        super().__init__(parent)
        self.mode     = mode
        self.product  = product or {}
        self.on_save  = on_save
        self.title("Add Product" if mode == "add" else "Edit Product")
        self.geometry("460x440")
        self.resizable(False, False)
        self.configure(bg=CLR["bg"])
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text="Add Product" if self.mode == "add" else "Edit Product",
                 bg=CLR["bg"], fg=CLR["text"],
                 font=F(14, bold=True)).pack(anchor="w", padx=20, pady=(16, 12))

        form = tk.Frame(self, bg=CLR["surface"],
                        highlightthickness=1, highlightbackground=CLR["border"])
        form.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        inner = tk.Frame(form, bg=CLR["surface"])
        inner.pack(fill="both", padx=20, pady=16)

        self._fields = {}
        field_defs = [
            ("barcode",  "Barcode *",        self.product.get("barcode", ""),  False),
            ("name",     "Product Name *",   self.product.get("name", ""),     False),
            ("category", "Category *",       self.product.get("category", "Staples"), False),
            ("price",    "Price (₹) *",      str(self.product.get("price", "")), False),
            ("unit",     "Unit",             self.product.get("unit", "piece"), False),
        ]

        for key, label, default, _ in field_defs:
            tk.Label(inner, text=label, bg=CLR["surface"],
                     fg=CLR["text2"], font=F(9)).pack(anchor="w", pady=(6, 2))
            if key == "category":
                var = tk.StringVar(value=default)
                cats = db.get_categories() or ["Staples", "Dairy", "Beverages",
                                                "Snacks", "Personal Care", "Household"]
                cb = ttk.Combobox(inner, textvariable=var,
                                  values=cats, font=F(11), state="normal")
                cb.pack(fill="x", ipady=4)
                self._fields[key] = var
            else:
                e = tk.Entry(
                    inner, font=F(11),
                    bg=CLR["surface2"], fg=CLR["text"],
                    insertbackground=CLR["accent"],
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=CLR["border"],
                    highlightcolor=CLR["accent"],
                    state="disabled" if (key == "barcode" and self.mode == "edit") else "normal",
                )
                e.pack(fill="x", ipady=5)
                if default:
                    e.config(state="normal")
                    e.insert(0, default)
                    if key == "barcode" and self.mode == "edit":
                        e.config(state="disabled")
                self._fields[key] = e

        self.err_lbl = tk.Label(inner, text="", bg=CLR["surface"],
                                fg=CLR["danger"], font=F(9))
        self.err_lbl.pack(anchor="w", pady=(6, 0))

        btns = tk.Frame(self, bg=CLR["bg"])
        btns.pack(fill="x", padx=16, pady=(0, 16))
        IconButton(btns, text="Save", command=self._save,
                   style="primary").pack(side="left", padx=(0, 8))
        IconButton(btns, text="Cancel", command=self.destroy,
                   style="ghost").pack(side="left")

    def _get(self, key):
        f = self._fields[key]
        if isinstance(f, tk.StringVar):
            return f.get().strip()
        if f["state"] == "disabled":
            return self.product.get(key, "")
        return f.get().strip()

    def _save(self):
        bc   = self._get("barcode")
        name = self._get("name")
        cat  = self._get("category")
        prx  = self._get("price")
        unit = self._get("unit") or "piece"

        if not bc or not name or not cat or not prx:
            self.err_lbl.config(text="Please fill in all required fields.")
            return
        try:
            price = float(prx)
            assert price >= 0
        except Exception:
            self.err_lbl.config(text="Price must be a positive number.")
            return

        if self.mode == "add":
            if db.get_product(bc):
                self.err_lbl.config(text="Barcode already exists. Use Edit to update.")
                return
            db.add_product(bc, name, cat, price, unit)
            msg = f"Added: {name}"
        else:
            db.update_product(bc, name, cat, price, unit)
            msg = f"Updated: {name}"

        self.destroy()
        if self.on_save:
            self.on_save(msg)
