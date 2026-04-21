"""
SmartCart — Custom Widget Library
Reusable, themed tkinter components.
"""

import tkinter as tk
from tkinter import ttk
from config import CLR, FONT_FAMILY


def F(size=11, bold=False, mono=False):
    """Font shorthand."""
    family = "Courier" if mono else FONT_FAMILY
    weight = "bold" if bold else "normal"
    return (family, size, weight)


# ── Base Card ──────────────────────────────────────────────────────────────
class Card(tk.Frame):
    def __init__(self, parent, padx=0, pady=0, **kw):
        super().__init__(
            parent,
            bg=CLR["surface"],
            highlightthickness=1,
            highlightbackground=CLR["border"],
            **kw
        )
        self._pad = (padx, pady)

    def inner(self, padx=16, pady=12):
        f = tk.Frame(self, bg=CLR["surface"])
        f.pack(fill="both", expand=True, padx=padx, pady=pady)
        return f


# ── Section Header ──────────────────────────────────────────────────────────
class SectionHeader(tk.Frame):
    def __init__(self, parent, title, subtitle=None, icon="", **kw):
        super().__init__(parent, bg=CLR["surface2"], **kw)
        row = tk.Frame(self, bg=CLR["surface2"])
        row.pack(fill="x", padx=16, pady=(10, 8))

        if icon:
            tk.Label(row, text=icon, bg=CLR["surface2"],
                     fg=CLR["accent"], font=F(16)).pack(side="left", padx=(0, 10))

        col = tk.Frame(row, bg=CLR["surface2"])
        col.pack(side="left")
        tk.Label(col, text=title, bg=CLR["surface2"],
                 fg=CLR["text"], font=F(13, bold=True)).pack(anchor="w")
        if subtitle:
            tk.Label(col, text=subtitle, bg=CLR["surface2"],
                     fg=CLR["text2"], font=F(9)).pack(anchor="w")

        # Accent underline
        tk.Frame(self, bg=CLR["border"], height=1).pack(fill="x")


# ── Stat Card ───────────────────────────────────────────────────────────────
class StatCard(tk.Frame):
    def __init__(self, parent, label, initial="0", color=None, **kw):
        super().__init__(
            parent, bg=CLR["surface"],
            highlightthickness=1, highlightbackground=CLR["border"],
            **kw
        )
        inner = tk.Frame(self, bg=CLR["surface"])
        inner.pack(padx=16, pady=10)
        tk.Label(inner, text=label, bg=CLR["surface"],
                 fg=CLR["text2"], font=F(9)).pack(anchor="w")
        self._lbl = tk.Label(inner, text=initial, bg=CLR["surface"],
                              fg=color or CLR["text"], font=F(22, bold=True))
        self._lbl.pack(anchor="w")

    def set(self, value, color=None):
        self._lbl.config(text=str(value))
        if color:
            self._lbl.config(fg=color)


# ── Icon Button ─────────────────────────────────────────────────────────────
class IconButton(tk.Button):
    def __init__(self, parent, text, command=None,
                 style="primary", icon="", **kw):
        STYLES = {
            "primary": (CLR["accent"],     CLR["text"],  CLR["accent_dim"]),
            "success": (CLR["ok"],         CLR["text"],  CLR["ok_dim"]),
            "danger":  (CLR["danger"],     CLR["text"],  CLR["danger_dim"]),
            "warn":    (CLR["warn"],       "#000",        CLR["warn_dim"]),
            "ghost":   (CLR["surface2"],   CLR["text2"], CLR["border"]),
            "red":     (CLR["danger_dim"], CLR["danger"],CLR["danger_dim"]),
        }
        bg, fg, hover = STYLES.get(style, STYLES["ghost"])
        label = f"{icon}  {text}" if icon else text
        super().__init__(
            parent,
            text=label,
            command=command,
            bg=bg, fg=fg,
            font=F(10, bold=True),
            relief="flat",
            cursor="hand2",
            activebackground=hover,
            activeforeground=fg,
            padx=14, pady=7,
            bd=0,
            **kw
        )
        self._bg    = bg
        self._hover = hover
        self.bind("<Enter>", lambda e: self.config(bg=self._hover))
        self.bind("<Leave>", lambda e: self.config(bg=self._bg))


# ── Styled Entry ─────────────────────────────────────────────────────────────
class StyledEntry(tk.Entry):
    def __init__(self, parent, placeholder="", **kw):
        self._ph = placeholder
        self._ph_active = False
        super().__init__(
            parent,
            bg=CLR["surface2"],
            fg=CLR["text"],
            insertbackground=CLR["accent"],
            relief="flat",
            font=F(11),
            highlightthickness=1,
            highlightbackground=CLR["border"],
            highlightcolor=CLR["accent"],
            **kw
        )
        if placeholder:
            self._show_placeholder()
            self.bind("<FocusIn>",  self._on_focus_in)
            self.bind("<FocusOut>", self._on_focus_out)

    def _show_placeholder(self):
        self.insert(0, self._ph)
        self.config(fg=CLR["text3"])
        self._ph_active = True

    def _on_focus_in(self, _):
        if self._ph_active:
            self.delete(0, "end")
            self.config(fg=CLR["text"])
            self._ph_active = False

    def _on_focus_out(self, _):
        if not self.get():
            self._show_placeholder()

    def get_value(self):
        if self._ph_active:
            return ""
        return self.get()


# ── Log Box ──────────────────────────────────────────────────────────────────
class LogBox(tk.Frame):
    def __init__(self, parent, height=8, **kw):
        super().__init__(parent, bg=CLR["surface"], **kw)
        self.txt = tk.Text(
            self, height=height,
            bg=CLR["cam_bg"], fg=CLR["text2"],
            font=F(9, mono=True),
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground=CLR["border"],
            state="disabled", wrap="word",
            selectbackground=CLR["accent_glow"],
        )
        vsb = ttk.Scrollbar(self, command=self.txt.yview)
        self.txt.config(yscrollcommand=vsb.set)
        self.txt.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Tags
        self.txt.tag_config("ok",   foreground=CLR["ok"])
        self.txt.tag_config("err",  foreground=CLR["danger"])
        self.txt.tag_config("info", foreground=CLR["accent"])
        self.txt.tag_config("ts",   foreground=CLR["text3"])

    def append(self, timestamp, message, tag="ok"):
        self.txt.config(state="normal")
        self.txt.insert("1.0", "\n")
        self.txt.insert("1.0", f" {message}\n", tag)
        self.txt.insert("1.0", f" {timestamp}\n", "ts")
        self.txt.config(state="disabled")


# ── Progress Bar ─────────────────────────────────────────────────────────────
class ProgressBar(tk.Frame):
    def __init__(self, parent, height=8, **kw):
        super().__init__(parent, bg=CLR["border"], height=height, **kw)
        self.pack_propagate(False)
        self._fill = tk.Frame(self, bg=CLR["ok"], height=height)
        self._fill.place(x=0, y=0, relheight=1.0, relwidth=0.0)

    def set(self, fraction: float, color: str = None):
        fraction = max(0.0, min(1.0, fraction))
        self._fill.place(relwidth=fraction)
        if color:
            self._fill.config(bg=color)


# ── Separator ─────────────────────────────────────────────────────────────────
class HSep(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=CLR["border"], height=1, **kw)


# ── Themed Treeview setup ─────────────────────────────────────────────────────
def setup_treeview_style():
    style = ttk.Style()
    style.theme_use("clam")

    style.configure("SC.Treeview",
        background=CLR["surface"],
        foreground=CLR["text"],
        fieldbackground=CLR["surface"],
        borderwidth=0,
        rowheight=32,
        font=(FONT_FAMILY, 10),
    )
    style.configure("SC.Treeview.Heading",
        background=CLR["surface2"],
        foreground=CLR["text2"],
        font=(FONT_FAMILY, 9, "bold"),
        relief="flat",
        borderwidth=0,
    )
    style.map("SC.Treeview",
        background=[("selected", CLR["accent_dim"])],
        foreground=[("selected", CLR["text"])],
    )
    style.map("SC.Treeview.Heading",
        background=[("active", CLR["border"])],
    )

    style.configure("Vertical.TScrollbar",
        background=CLR["surface2"],
        troughcolor=CLR["surface"],
        arrowcolor=CLR["text3"],
        borderwidth=0,
    )


# ── Feedback Label ────────────────────────────────────────────────────────────
class FeedbackLabel(tk.Label):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=CLR["surface"],
                         fg=CLR["ok"], font=F(10),
                         anchor="w", **kw)
        self._after_id = None

    def show(self, msg, tag="ok", autohide=4000):
        colors = {"ok": CLR["ok"], "err": CLR["danger"],
                  "warn": CLR["warn"], "info": CLR["accent"]}
        self.config(text=f"  {msg}", fg=colors.get(tag, CLR["text"]))
        if self._after_id:
            self.after_cancel(self._after_id)
        if autohide:
            self._after_id = self.after(autohide, lambda: self.config(text=""))
