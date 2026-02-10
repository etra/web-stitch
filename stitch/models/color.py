"""
Color model and ColorVendor enum for storing thread/bead color reference data.

Colors are vendor-specific catalog entries (e.g., DMC floss, Hama beads).
This table replaces the static in-memory palettes previously loaded from
JSON files and hardcoded lists.

Seeded via scripts/seed_colors.py.
"""
from enum import Enum
from stitch.database import db


class ColorVendor(str, Enum):
    """
    Supported color vendors.

    Each member's value matches the string stored in the colors.vendor column.
    Use the properties to access display metadata for each vendor.

    Members:
        DMC     — DMC embroidery floss
        HAMA    — Hama fuse beads
        ARTKAL  — Artkal fuse beads
        NABBI   — Nabbi fuse beads
    """
    DMC = 'DMC'
    HAMA = 'Hama'
    ARTKAL = 'Artkal'
    NABBI = 'Nabbi'

    @property
    def full_name(self) -> str:
        return _VENDOR_META[self]['full_name']

    @property
    def description(self) -> str:
        return _VENDOR_META[self]['description']

    @property
    def vendor_type(self) -> str:
        return _VENDOR_META[self]['type']


_VENDOR_META = {
    ColorVendor.DMC: {
        'full_name': 'DMC Embroidery Floss',
        'description': 'Professional embroidery thread with 500+ colors',
        'type': 'embroidery',
    },
    ColorVendor.HAMA: {
        'full_name': 'HAMA Beads',
        'description': 'Popular fuse bead brand for pixel art',
        'type': 'beads',
    },
    ColorVendor.ARTKAL: {
        'full_name': 'ARTKAL Beads',
        'description': 'High-quality fuse beads for crafting',
        'type': 'beads',
    },
    ColorVendor.NABBI: {
        'full_name': 'NABBI Beads',
        'description': 'Fuse beads for creative projects',
        'type': 'beads',
    },
}


class Color(db.Model):
    """
    A single color entry in a vendor's catalog.

    Each row represents one purchasable thread or bead color.
    Colors belong to a vendor (e.g., 'DMC', 'Hama') and are identified
    by a vendor-specific code (e.g., '310', 'Blanc', 'H01').

    Fields:
        id:         Auto-increment primary key.
        vendor:     Vendor/brand name. Must be a ColorVendor value.
                    Indexed — most queries filter by vendor.
        code:       Vendor-specific color code (e.g., '310', 'Blanc').
        name:       Human-readable color name (e.g., 'Black', 'Ecru/off-white').
        hex:        Hex color value including '#' (e.g., '#000000').
        is_default: Whether this color is included in a default starter palette.
    """
    __tablename__ = 'colors'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vendor = db.Column(db.Enum(ColorVendor), nullable=False, index=True)
    code = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    hex = db.Column(db.String(7), nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Color {self.vendor}:{self.code} ({self.name})>'
