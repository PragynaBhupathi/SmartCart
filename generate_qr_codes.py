#!/usr/bin/env python3
"""
Generate QR codes for all products in the database.
Saves a JPEG image with all QR codes arranged in a grid.
"""

import qrcode
from PIL import Image, ImageDraw, ImageFont
import math
from data.db import get_all_products, init_db

def generate_qr_codes():
    # Initialize database
    init_db()

    # Get all products
    products = get_all_products()

    # QR code settings
    qr_size = 150  # pixels per QR code
    margin = 20    # margin around each QR
    text_height = 40  # space for product name
    cols = 6  # number of columns
    rows = math.ceil(len(products) / cols)

    # Calculate image size
    img_width = cols * (qr_size + 2 * margin)
    img_height = rows * (qr_size + text_height + 2 * margin)

    # Create white background image
    img = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(img)

    # Try to load a font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()

    # Generate QR codes
    for i, product in enumerate(products):
        row = i // cols
        col = i % cols

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=5,
            border=2,
        )
        qr.add_data(product['barcode'])
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

        # Position
        x = col * (qr_size + 2 * margin) + margin
        y = row * (qr_size + text_height + 2 * margin) + margin

        # Paste QR code
        img.paste(qr_img, (x, y))

        # Draw product name below QR
        name = product['name']
        if len(name) > 20:
            name = name[:17] + "..."
        text_x = x + qr_size // 2
        text_y = y + qr_size + 5
        bbox = draw.textbbox((0, 0), name, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((text_x - text_width // 2, text_y), name, fill="black", font=font)

    # Save the image
    img.save('assets/qr_codes.jpg', 'JPEG', quality=95)
    print(f"Generated QR codes image with {len(products)} products: assets/qr_codes.jpg")

if __name__ == "__main__":
    generate_qr_codes()