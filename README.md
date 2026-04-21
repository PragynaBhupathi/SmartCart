# 🛒 SmartCart — Smart Shopping Bill Tracker

Know your total before you reach the billing counter.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Features
- Live camera barcode & QR code scanning (OpenCV)
- Real-time cart with GST (18%) calculation  
- Budget tracker with visual progress bar
- Product database with full CRUD (add / edit / delete)
- Bill preview & export as .txt
- Professional dark-theme UI with sidebar navigation

## Structure
```
smartcart/
├── main.py              ← Entry point
├── config.py            ← All settings (GST, theme, store info)
├── requirements.txt
├── data/
│   ├── db.py            ← SQLite database layer
│   └── products.db      ← Auto-created on first run
├── modules/
│   ├── cart.py          ← Cart business logic
│   ├── scanner.py       ← OpenCV camera + barcode thread
│   └── bill.py          ← Bill generation & export
├── ui/
│   ├── widgets.py       ← Reusable themed components
│   ├── scanner_panel.py ← Camera + scan log panel
│   ├── cart_panel.py    ← Cart table + bill + budget
│   └── products_panel.py← Product management CRUD
└── bills/               ← Saved bills go here
```

## Testing
A QR codes image is available at `assets/qr_codes.jpg` containing QR codes for all sample products. Print this or display it on another device to test the scanner functionality.
