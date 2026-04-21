"""
SmartCart — Central Configuration
All app-wide settings live here. Edit this file to customise the app.
"""

# ── Store Info ────────────────────────────────────────────────────────────────
STORE_NAME    = "SmartCart"
STORE_TAGLINE = "Know your bill before billing"
STORE_ADDRESS = "Your Mall Name, City"
STORE_PHONE   = "+91 00000 00000"

# ── Tax ───────────────────────────────────────────────────────────────────────
GST_RATE      = 0.18          # 18%
CURRENCY      = "₹"
CURRENCY_CODE = "INR"

# ── Scanner ───────────────────────────────────────────────────────────────────
SCAN_COOLDOWN   = 3           # seconds before same barcode rescans
DEFAULT_CAM_IDX = 0           # default webcam index
CAM_WIDTH       = 640
CAM_HEIGHT      = 480
CAM_FPS_TARGET  = 30          # ms between GUI frame updates (30ms ≈ 33fps)

# ── Database ──────────────────────────────────────────────────────────────────
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "data", "products.db")

# ── Bill PDF export ───────────────────────────────────────────────────────────
BILLS_DIR = os.path.join(BASE_DIR, "bills")

# ── UI / Theme ────────────────────────────────────────────────────────────────
FONT_FAMILY   = "Helvetica"   # change to any installed font
WINDOW_TITLE  = "SmartCart — Smart Shopping Bill Tracker"
WINDOW_SIZE   = "1200x750"
WINDOW_MIN    = (1000, 680)

# Palette
CLR = {
    # Backgrounds
    "bg":          "#FFFFFF",   # white background
    "surface":     "#F8F9FA",   # light surface
    "surface2":    "#E9ECEF",   # elevated surface
    "border":      "#DEE2E6",   # subtle border
    "border_hi":   "#ADB5BD",   # highlighted border

    # Brand
    "accent":      "#6C63FF",   # primary purple
    "accent_dim":  "#4B45B5",   # darker accent
    "accent_glow": "#6C63FF",  # glow/tint

    # Semantic
    "ok":          "#10B981",   # green success
    "ok_dim":      "#064E3B",
    "warn":        "#F59E0B",   # amber warning
    "warn_dim":    "#78350F",
    "danger":      "#EF4444",   # red error
    "danger_dim":  "#7F1D1D",
    "info":        "#3B82F6",   # blue info

    # Text
    "text":        "#212529",   # primary text
    "text2":       "#6C757D",   # secondary text
    "text3":       "#ADB5BD",   # muted text

    # Special
    "cam_bg":      "#F8F9FA",   # camera canvas bg
    "highlight":   "#E7F3FF", # row highlight
    "selected":    "#CCE5FF", # selected row
}
