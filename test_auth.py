
import json
from pathlib import Path
from stitch import create_app
from stitch.database import db
from stitch.models.color import Color, ColorVendor

app = create_app()

with app.app_context():
    # Path to dmc.json
    dmc_path = Path('stitch/models/dmc.json')

    # Load DMC colors from JSON
    with open(dmc_path, 'r', encoding='utf-8') as f:
        dmc_data = json.load(f)

    colors = []

    # DMC colors from JSON
    for entry in dmc_data:
        colors.append(Color(
            vendor=ColorVendor.DMC,
            code=entry['code'],
            name=entry['name'],
            hex=entry['hex'],
            is_default=entry.get('default', False),
        ))

    # Hama colors
    hama = [
        ("H01", "White", "#eceded", True),
        ("H02", "Cream", "#f0e8b9", False),
        ("H03", "Yellow", "#f0b901", False),
        ("H04", "Orange", "#eb9534", False),
        ("H05", "Red", "#eb4034", False),
        ("H06", "Pink", "#f798ba", False),
        ("H07", "Brown", "#8b4a3b", False),
        ("H08", "Purple", "#9b4f96", False),
        ("H09", "Blue", "#0f68a8", False),
        ("H10", "Green", "#00a650", False),
        ("H18", "Black", "#1c1c1c", True),
    ]
    for code, name, hex_val, default in hama:
        colors.append(Color(vendor=ColorVendor.HAMA, code=code, name=name, hex=hex_val, is_default=default))

    # Artkal colors
    artkal = [
        ("A01", "White", "#ffffff", True),
        ("A02", "Cream", "#ffe4b5", False),
        ("A03", "Yellow", "#ffff00", False),
        ("A04", "Red", "#ff0000", False),
        ("A05", "Pink", "#ffc0cb", False),
        ("A06", "Brown", "#a52a2a", False),
        ("A07", "Blue", "#0000ff", False),
        ("A08", "Green", "#008000", False),
        ("A09", "Black", "#000000", True),
    ]
    for code, name, hex_val, default in artkal:
        colors.append(Color(vendor=ColorVendor.ARTKAL, code=code, name=name, hex=hex_val, is_default=default))

    # Nabbi colors
    nabbi = [
        ("N01", "White", "#ffffff", True),
        ("N02", "Cream", "#fffacd", False),
        ("N03", "Yellow", "#ffeb3b", False),
        ("N04", "Red", "#f44336", False),
        ("N05", "Pink", "#e91e63", False),
        ("N06", "Brown", "#795548", False),
        ("N07", "Blue", "#2196f3", False),
        ("N08", "Green", "#4caf50", False),
        ("N09", "Black", "#212121", True),
    ]
    for code, name, hex_val, default in nabbi:
        colors.append(Color(vendor=ColorVendor.NABBI, code=code, name=name, hex=hex_val, is_default=default))

    # Insert all
    db.session.add_all(colors)
    db.session.commit()
    print(f"Seeded {len(colors)} colors into the database.")
