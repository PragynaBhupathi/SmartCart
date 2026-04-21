"""
SmartCart — Cart Panel
Right-side: cart table, bill summary, budget tracker, actions.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from config import CLR, CURRENCY, GST_RATE, FONT_FAMILY
from ui.widgets import (
    Card, SectionHeader, StatCard, IconButton,
    ProgressBar, HSep, FeedbackLabel, setup_treeview_style, F
)
from modules.bill import save_bill, generate_text_bill, next_bill_number


class CartPanel(tk.Frame):
    """
    Main cart view: table of scanned items + bill + budget.
    Receives the Cart object from parent.
    """

    def __init__(self, parent, cart, **kw):
        super().__init__(parent, bg=CLR["bg"], **kw)
        self.cart = cart
        self._build()

    def _build(self):
        setup_treeview_style()

        # ── Stat cards row ────────────────────────────────────────────────────
        stats = tk.Frame(self, bg=CLR["bg"])
        stats.pack(fill="x", pady=(0, 6))

        self.s_items  = StatCard(stats, "Items in cart",       "0")
        self.s_unique = StatCard(stats, "Unique products",     "0")
        self.s_sub    = StatCard(stats, "Subtotal",            f"{CURRENCY}0.00")
        self.s_total  = StatCard(stats, "Grand Total (+ GST)", f"{CURRENCY}0.00",
                                 color=CLR["ok"])
        for w in stats.winfo_children():
            w.pack(side="left", expand=True, fill="x", padx=(0, 6))
        stats.winfo_children()[-1].pack_configure(padx=0)

        # ── Cart table ────────────────────────────────────────────────────────
        tbl_card = Card(self)
        tbl_card.pack(fill="both", expand=True, pady=(0, 6))

        SectionHeader(tbl_card, title="Shopping Cart",
                      subtitle="Items scanned so far", icon="🛒").pack(fill="x")

        tree_frame = tk.Frame(tbl_card, bg=CLR["surface"])
        tree_frame.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        cols = ("name", "cat", "unit", "qty", "price", "sub")
        self.tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            selectmode="browse", height=11, style="SC.Treeview"
        )
        for col, hdr, w, anc in [
            ("name",  "Product",    230, "w"),
            ("cat",   "Category",   110, "w"),
            ("unit",  "Unit",        70, "center"),
            ("qty",   "Qty",         50, "center"),
            ("price", "Unit Price",  90, "e"),
            ("sub",   "Subtotal",   100, "e"),
        ]:
            self.tree.heading(col, text=hdr, anchor=anc)
            self.tree.column(col, width=w, anchor=anc, minwidth=40)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self.tree.yview, style="Vertical.TScrollbar")
        self.tree.config(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Alternating row colours
        self.tree.tag_configure("odd",  background=CLR["surface"])
        self.tree.tag_configure("even", background=CLR["surface2"])

        # Row actions
        row_btns = tk.Frame(tbl_card, bg=CLR["surface"])
        row_btns.pack(fill="x", padx=12, pady=(0, 10))
        for lbl, cmd, style in [
            ("+ Qty",       lambda: self._qty(+1), "primary"),
            ("− Qty",       lambda: self._qty(-1), "ghost"),
            ("Remove",      self._remove,           "red"),
            ("Clear Cart",  self._clear,            "ghost"),
        ]:
            IconButton(row_btns, text=lbl, command=cmd,
                       style=style).pack(side="left", padx=(0, 6))
        tk.Label(row_btns, text="← select a row first",
                 bg=CLR["surface"], fg=CLR["text3"], font=F(9)).pack(side="left")

        # ── Bill summary ──────────────────────────────────────────────────────
        bill_card = Card(self)
        bill_card.pack(fill="x", pady=(0, 6))
        bc = bill_card.inner(padx=16, pady=12)

        tk.Label(bc, text="Bill Summary", bg=CLR["surface"],
                 fg=CLR["text2"], font=F(9, bold=True)).pack(anchor="w", pady=(0, 6))

        self.b_sub  = self._bill_row(bc, "Subtotal",               f"{CURRENCY}0.00")
        self.b_gst  = self._bill_row(bc, f"GST ({GST_RATE*100:.0f}%)", f"{CURRENCY}0.00")
        HSep(bc).pack(fill="x", pady=6)
        self.b_tot  = self._bill_row(bc, "GRAND TOTAL",            f"{CURRENCY}0.00",
                                     bold=True, color=CLR["ok"])

        # ── Budget tracker ────────────────────────────────────────────────────
        bud_card = Card(self)
        bud_card.pack(fill="x", pady=(0, 6))
        bdc = bud_card.inner(padx=16, pady=12)

        row = tk.Frame(bdc, bg=CLR["surface"])
        row.pack(fill="x", pady=(0, 8))
        tk.Label(row, text="Budget", bg=CLR["surface"],
                 fg=CLR["text2"], font=F(9, bold=True)).pack(side="left")
        self.bud_status = tk.Label(row, text="", bg=CLR["surface"],
                                   fg=CLR["ok"], font=F(9, bold=True))
        self.bud_status.pack(side="right")

        entry_row = tk.Frame(bdc, bg=CLR["surface"])
        entry_row.pack(fill="x", pady=(0, 8))
        tk.Label(entry_row, text=f"{CURRENCY}", bg=CLR["surface"],
                 fg=CLR["text2"], font=F(12)).pack(side="left", padx=(0, 4))

        self.bud_var = tk.StringVar()
        bud_ent = tk.Entry(
            entry_row, textvariable=self.bud_var,
            width=12, font=F(12),
            bg=CLR["surface2"], fg=CLR["text"],
            insertbackground=CLR["accent"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=CLR["border"],
            highlightcolor=CLR["accent"],
        )
        bud_ent.pack(side="left", ipady=5)
        bud_ent.bind("<KeyRelease>", lambda e: self.refresh())

        self.prog = ProgressBar(bdc, height=6)
        self.prog.pack(fill="x", pady=(0, 4))

        prog_labels = tk.Frame(bdc, bg=CLR["surface"])
        prog_labels.pack(fill="x")
        self.prog_l = tk.Label(prog_labels, text="", bg=CLR["surface"],
                               fg=CLR["text3"], font=F(8))
        self.prog_r = tk.Label(prog_labels, text="", bg=CLR["surface"],
                               fg=CLR["text3"], font=F(8))
        self.prog_l.pack(side="left")
        self.prog_r.pack(side="right")

        # ── Action buttons ────────────────────────────────────────────────────
        act_row = tk.Frame(self, bg=CLR["bg"])
        act_row.pack(fill="x", pady=(0, 4))
        IconButton(act_row, text="Save Bill  ↓", style="success",
                   icon="💾", command=self._save_bill).pack(side="left", padx=(0, 8))
        IconButton(act_row, text="Preview Bill", style="ghost",
                   icon="🧾", command=self._preview_bill).pack(side="left")

        self.action_fb = FeedbackLabel(act_row)
        self.action_fb.pack(side="left", padx=12)

    # ── Refresh ───────────────────────────────────────────────────────────────
    def refresh(self):
        self._refresh_table()
        self._refresh_stats()
        self._refresh_bill()
        self._refresh_budget()

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for i, item in enumerate(self.cart.items()):
            tag = "odd" if i % 2 == 0 else "even"
            self.tree.insert("", "end", iid=item.barcode, tags=(tag,), values=(
                item.name,
                item.category,
                item.unit,
                item.qty,
                f"{CURRENCY}{item.price:.2f}",
                f"{CURRENCY}{item.subtotal:.2f}",
            ))

    def _refresh_stats(self):
        self.s_items.set(self.cart.total_items())
        self.s_unique.set(self.cart.unique_count())
        self.s_sub.set(f"{CURRENCY}{self.cart.subtotal():.2f}")
        tot = self.cart.grand_total()
        self.s_total.set(f"{CURRENCY}{tot:.2f}",
                         color=CLR["ok"] if tot > 0 else CLR["text2"])

    def _refresh_bill(self):
        self.b_sub.config( text=f"{CURRENCY}{self.cart.subtotal():.2f}")
        self.b_gst.config( text=f"{CURRENCY}{self.cart.gst_amount():.2f}")
        self.b_tot.config( text=f"{CURRENCY}{self.cart.grand_total():.2f}")

    def _refresh_budget(self):
        total = self.cart.grand_total()
        self.prog_l.config(text=f"{CURRENCY}{total:.2f} spent")
        try:
            budget = float(self.bud_var.get())
            assert budget > 0
        except Exception:
            self.prog.set(0.0)
            self.prog_r.config(text="")
            self.bud_status.config(text="")
            return

        pct = min(total / budget, 1.0)
        remaining = budget - total

        if total > budget:
            col = CLR["danger"]
            msg = f"⚠ Over by {CURRENCY}{abs(remaining):.2f}"
        elif pct > 0.80:
            col = CLR["warn"]
            msg = f"{CURRENCY}{remaining:.2f} remaining"
        else:
            col = CLR["ok"]
            msg = f"{CURRENCY}{remaining:.2f} remaining"

        self.prog.set(pct, color=col)
        self.prog_r.config(text=f"Budget: {CURRENCY}{budget:.2f}")
        self.bud_status.config(text=msg, fg=col)

    # ── Row actions ───────────────────────────────────────────────────────────
    def _sel(self):
        s = self.tree.selection()
        return s[0] if s else None

    def _qty(self, delta):
        bc = self._sel()
        if not bc:
            return
        item = self.cart.get_item(bc)
        if item:
            self.cart.set_qty(bc, item.qty + delta)
            self.refresh()

    def _remove(self):
        bc = self._sel()
        if bc:
            self.cart.remove(bc)
            self.refresh()

    def _clear(self):
        if self.cart.is_empty():
            return
        if messagebox.askyesno("Clear cart", "Remove all items from cart?",
                               parent=self):
            self.cart.clear()
            self.refresh()

    # ── Bill export ───────────────────────────────────────────────────────────
    def _save_bill(self):
        if self.cart.is_empty():
            self.action_fb.show("Cart is empty — scan items first.", "warn")
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".txt",
            filetypes=[("Text bill", "*.txt"), ("All files", "*.*")],
            initialfile=f"bill_{next_bill_number()}.txt",
            title="Save Bill",
        )
        if path:
            saved = save_bill(self.cart.to_dict(), path)
            self.action_fb.show(f"Bill saved: {saved}", "ok")

    def _preview_bill(self):
        if self.cart.is_empty():
            self.action_fb.show("Cart is empty — scan items first.", "warn")
            return
        text = generate_text_bill(self.cart.to_dict(), next_bill_number())
        PreviewWindow(self, text)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _bill_row(self, parent, label, value, bold=False, color=None):
        f = tk.Frame(parent, bg=CLR["surface"])
        f.pack(fill="x", pady=1)
        font = F(11, bold=True) if bold else F(10)
        tk.Label(f, text=label, bg=CLR["surface"],
                 fg=CLR["text2"], font=font).pack(side="left")
        lbl = tk.Label(f, text=value, bg=CLR["surface"],
                       fg=color or CLR["text"], font=font)
        lbl.pack(side="right")
        return lbl


# ── Bill Preview Window ───────────────────────────────────────────────────────
class PreviewWindow(tk.Toplevel):
    def __init__(self, parent, text):
        super().__init__(parent)
        self.title("Bill Preview")
        self.geometry("540x600")
        self.configure(bg=CLR["bg"])
        self.resizable(True, True)

        tk.Label(self, text="Bill Preview",
                 bg=CLR["bg"], fg=CLR["text"],
                 font=(FONT_FAMILY, 13, "bold")).pack(anchor="w", padx=16, pady=(14, 4))

        frame = tk.Frame(self, bg=CLR["surface"],
                         highlightthickness=1,
                         highlightbackground=CLR["border"])
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        txt = tk.Text(frame, bg=CLR["cam_bg"], fg=CLR["text"],
                      font=("Courier", 10), relief="flat", bd=0,
                      wrap="none", padx=12, pady=12)
        vsb = ttk.Scrollbar(frame, command=txt.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=txt.xview)
        txt.config(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", text)
        txt.config(state="disabled")

        IconButton(self, text="Close", style="ghost",
                   command=self.destroy).pack(pady=(0, 12))
