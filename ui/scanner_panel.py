"""
SmartCart — Scanner Panel
Left-side camera feed with barcode detection controls.
"""

import tkinter as tk
from datetime import datetime
from config import CLR
from ui.widgets import (
    Card, SectionHeader, IconButton, LogBox, FeedbackLabel, F
)


class ScannerPanel(tk.Frame):
    """
    Left panel: live webcam feed + scan log.
    Communicates with parent via on_scan_result callback.
    """

    def __init__(self, parent, scanner, on_scan_result, **kw):
        super().__init__(parent, bg=CLR["bg"], **kw)
        self.scanner        = scanner
        self.on_scan_result = on_scan_result
        self._cam_active    = False

        self._build()

    def _build(self):
        # ── Header ───────────────────────────────────────────────────────────
        SectionHeader(
            self, title="Camera Scanner",
            subtitle="Point at any barcode or QR code",
            icon="◉"
        ).pack(fill="x", pady=(0, 1))

        # ── Camera canvas ─────────────────────────────────────────────────────
        cam_card = Card(self)
        cam_card.pack(fill="x", padx=0, pady=1)

        self.canvas = tk.Canvas(
            cam_card, bg=CLR["cam_bg"],
            highlightthickness=0,
            width=360, height=270,
        )
        self.canvas.pack(padx=0, pady=0)
        self._draw_placeholder()

        # Status strip under canvas
        status_strip = tk.Frame(cam_card, bg=CLR["surface2"])
        status_strip.pack(fill="x")
        tk.Frame(status_strip, bg=CLR["border"], height=1).pack(fill="x")
        inner = tk.Frame(status_strip, bg=CLR["surface2"])
        inner.pack(fill="x", padx=12, pady=5)

        self.status_dot = tk.Label(inner, text="●", bg=CLR["surface2"],
                                   fg=CLR["text3"], font=F(8))
        self.status_dot.pack(side="left")
        self.status_lbl = tk.Label(inner, text="Camera inactive",
                                   bg=CLR["surface2"], fg=CLR["text3"], font=F(9))
        self.status_lbl.pack(side="left", padx=(4, 0))

        self.fps_lbl = tk.Label(inner, text="", bg=CLR["surface2"],
                                fg=CLR["text3"], font=F(9))
        self.fps_lbl.pack(side="right")

        # ── Camera controls ────────────────────────────────────────────────────
        ctrl_card = Card(self)
        ctrl_card.pack(fill="x", pady=1)
        ctrl = tk.Frame(ctrl_card, bg=CLR["surface"])
        ctrl.pack(fill="x", padx=12, pady=10)

        self.cam_btn = IconButton(
            ctrl, text="Start Camera", style="success", icon="▶",
            command=self._toggle_camera
        )
        self.cam_btn.pack(side="left", padx=(0, 8))

        # Camera index picker
        idx_f = tk.Frame(ctrl, bg=CLR["surface"])
        idx_f.pack(side="left")
        tk.Label(idx_f, text="Cam:", bg=CLR["surface"],
                 fg=CLR["text2"], font=F(9)).pack(side="left", padx=(0, 4))
        self.cam_idx = tk.IntVar(value=0)
        for i in range(4):
            rb = tk.Radiobutton(
                idx_f, text=str(i), variable=self.cam_idx, value=i,
                bg=CLR["surface"], fg=CLR["text2"],
                activebackground=CLR["surface"], activeforeground=CLR["accent"],
                selectcolor=CLR["surface2"], font=F(9),
                indicatoron=True,
            )
            rb.pack(side="left", padx=2)

        # ── Manual barcode entry ───────────────────────────────────────────────
        manual_card = Card(self)
        manual_card.pack(fill="x", pady=1)
        mc = manual_card.inner(padx=12, pady=10)

        tk.Label(mc, text="Manual entry", bg=CLR["surface"],
                 fg=CLR["text2"], font=F(9, bold=True)).pack(anchor="w", pady=(0, 6))

        row = tk.Frame(mc, bg=CLR["surface"])
        row.pack(fill="x")

        self.entry_var = tk.StringVar()
        ent = tk.Entry(
            row, textvariable=self.entry_var,
            bg=CLR["surface2"], fg=CLR["text"],
            insertbackground=CLR["accent"],
            relief="flat", font=F(11),
            highlightthickness=1,
            highlightbackground=CLR["border"],
            highlightcolor=CLR["accent"],
        )
        ent.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        ent.bind("<Return>", lambda e: self._manual_scan())

        IconButton(row, text="Add", style="primary",
                   command=self._manual_scan).pack(side="left")

        self.manual_fb = FeedbackLabel(mc)
        self.manual_fb.pack(fill="x", pady=(4, 0))

        # ── Scan log ───────────────────────────────────────────────────────────
        log_card = Card(self)
        log_card.pack(fill="both", expand=True, pady=1)
        log_inner = log_card.inner(padx=12, pady=10)

        tk.Label(log_inner, text="Scan history",
                 bg=CLR["surface"], fg=CLR["text2"],
                 font=F(9, bold=True)).pack(anchor="w", pady=(0, 6))

        self.log = LogBox(log_inner, height=8)
        self.log.pack(fill="both", expand=True)

    # ── Camera toggle ─────────────────────────────────────────────────────────
    def _toggle_camera(self):
        if not self._cam_active:
            self._start_camera()
        else:
            self._stop_camera()

    def _start_camera(self):
        self._cam_active = True
        self.cam_btn.config(text="  ■  Stop Camera", bg=CLR["danger"])
        self._set_status("Starting…", CLR["warn"])
        self.scanner.on_scan = self._on_scan
        self.scanner.start_scanning(camera_index=self.cam_idx.get())
        self._feed_loop()

    def _stop_camera(self):
        self._cam_active = False
        self.scanner.stop()
        self.cam_btn.config(text="  ▶  Start Camera", bg=CLR["ok"])
        self._set_status("Camera inactive", CLR["text3"])
        self.fps_lbl.config(text="")
        self._draw_placeholder()

    def _feed_loop(self):
        if not self._cam_active:
            return
        frame = self.scanner.get_frame()
        if frame is not None:
            try:
                from PIL import Image, ImageTk
                import cv2
                rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w = rgb.shape[:2]
                cw   = self.canvas.winfo_width()  or 360
                ch   = self.canvas.winfo_height() or 270
                scale = min(cw / w, ch / h)
                nw, nh = int(w * scale), int(h * scale)
                img = Image.fromarray(rgb).resize((nw, nh), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self.canvas.delete("all")
                self.canvas.create_image(cw // 2, ch // 2,
                                         image=tk_img, anchor="center")
                self.canvas._img = tk_img
                self._set_status("Scanning…", CLR["ok"])
                if self.scanner.fps:
                    self.fps_lbl.config(text=f"{self.scanner.fps:.0f} fps")
            except ImportError:
                self._set_status("pip install Pillow", CLR["danger"])
        else:
            self._set_status("Waiting for camera…", CLR["warn"])
        self.after(30, self._feed_loop)

    # ── Scan handling ─────────────────────────────────────────────────────────
    def _on_scan(self, barcode):
        """Called from scanner thread — dispatch to main thread."""
        self.after(0, lambda bc=barcode: self._fire(bc))

    def _manual_scan(self):
        bc = self.entry_var.get().strip()
        if bc:
            self._fire(bc)
            self.entry_var.set("")

    def _fire(self, barcode):
        result = self.on_scan_result(barcode)
        ts = datetime.now().strftime("%H:%M:%S")
        if result["ok"]:
            self.log.append(ts, f"✓  {result['message']}", "ok")
            self.manual_fb.show(f"✓  {result['message']}", "ok")
        else:
            self.log.append(ts, f"✗  {result['message']}", "err")
            self.manual_fb.show(f"✗  {result['message']}", "err")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _set_status(self, text, color):
        dot_colors = {
            CLR["ok"]:    CLR["ok"],
            CLR["warn"]:  CLR["warn"],
            CLR["danger"]: CLR["danger"],
            CLR["text3"]: CLR["text3"],
        }
        self.status_lbl.config(text=f" {text}")
        self.status_dot.config(fg=color)

    def _draw_placeholder(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()  or 360
        h = self.canvas.winfo_height() or 270
        # Dark grid pattern
        for x in range(0, w, 30):
            self.canvas.create_line(x, 0, x, h, fill="#1A1D27", width=1)
        for y in range(0, h, 30):
            self.canvas.create_line(0, y, w, y, fill="#1A1D27", width=1)
        # Center icon
        self.canvas.create_text(
            w // 2, h // 2 - 24,
            text="◉", fill=CLR["border"],
            font=(FONT_FAMILY, 36), anchor="center"
        )
        self.canvas.create_text(
            w // 2, h // 2 + 24,
            text="Press  ▶ Start Camera",
            fill=CLR["text3"], font=F(11), anchor="center"
        )

    def shutdown(self):
        """Call before closing the window."""
        if self._cam_active:
            self._stop_camera()


# Avoid circular import
from config import FONT_FAMILY
