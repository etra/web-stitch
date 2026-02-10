"""
Color service for querying vendor color catalogs from the database.

Responsible for:
- Listing all colors across all vendors
- Listing available vendors with color counts
- Retrieving colors by vendor

Does NOT:
- Modify color data (colors are seeded, not user-editable)
- Handle HTTP concerns
- Perform color matching (see color_matcher.py)

Provides all vendor color catalog queries (vendor listing, palette retrieval,
single-color lookup, vendor validation).
"""
from typing import Dict, List, Optional

from sqlalchemy import func

from stitch.database import db
from stitch.models.color import Color, ColorVendor


class ColorService:
    """
    Read-only service for querying the colors table.

    All vendor metadata comes from the ColorVendor enum.
    All color data comes from the colors table.
    """

    @staticmethod
    def get_all_colors() -> List[Dict]:
        """
        Return all colors from all vendors, formatted for API response.

        Returns:
            List of dicts, each containing:
                - id: unique identifier ('{vendor}_{code}')
                - vendor: vendor display name (e.g. 'DMC')
                - code: vendor-specific color code
                - name: human-readable color name
                - hex: hex color value (e.g. '#000000')
                - text: display text for UI (e.g. 'DMC 310 - Black')

        Side effects:
            None (read-only query).
        """
        colors = (
            Color.query
            .order_by(Color.vendor, Color.code)
            .all()
        )
        return [
            {
                'id': f'{c.vendor.value}_{c.code}',
                'vendor': c.vendor.value,
                'code': c.code,
                'name': c.name,
                'hex': c.hex,
                'text': f'{c.vendor.value} {c.code} - {c.name}',
            }
            for c in colors
        ]

    @staticmethod
    def get_vendors() -> List[Dict]:
        """
        Return all supported vendors with metadata and color counts.

        Returns:
            List of dicts, each containing:
                - key: vendor enum value (str used in DB)
                - name: vendor display name (same as key)
                - full_name: e.g. 'DMC Embroidery Floss'
                - description: short description
                - type: 'embroidery' or 'beads'
                - color_count: number of colors in the database

        Side effects:
            None (read-only query).
        """
        # Query color counts grouped by vendor
        rows = (
            db.session.query(Color.vendor, func.count(Color.id))
            .group_by(Color.vendor)
            .all()
        )
        count_by_vendor = {vendor: count for vendor, count in rows}

        vendors = []
        for member in ColorVendor:
            vendors.append({
                'key': member.value,
                'name': member.value,
                'full_name': member.full_name,
                'description': member.description,
                'type': member.vendor_type,
                'color_count': count_by_vendor.get(member.value, 0),
            })

        return vendors

    @staticmethod
    def get_colors_by_vendor(vendor: ColorVendor) -> List[Dict]:
        """
        Return all colors for a given vendor.

        Args:
            vendor: A ColorVendor enum member.

        Returns:
            List of color dicts, each containing:
                - id: database primary key
                - vendor: vendor string
                - code: vendor-specific color code
                - name: human-readable color name
                - hex: hex color value (e.g. '#000000')
                - is_default: whether this is a default starter color

        Side effects:
            None (read-only query).
        """
        colors = (
            Color.query
            .filter_by(vendor=vendor.value)
            .order_by(Color.code)
            .all()
        )
        return [
            {
                'id': c.id,
                'vendor': c.vendor,
                'code': c.code,
                'name': c.name,
                'hex': c.hex,
                'is_default': c.is_default,
            }
            for c in colors
        ]

    @staticmethod
    def get_color(vendor_key: str, code: str) -> Optional[Dict]:
        """
        Get a specific color by vendor and code.

        Args:
            vendor_key: Vendor enum value string (e.g. 'DMC', 'Hama').
            code: Vendor-specific color code (e.g. '310', 'Blanc').

        Returns:
            Color dict if found, None otherwise.

        Side effects:
            None (read-only query).
        """
        color = Color.query.filter_by(vendor=vendor_key, code=code).first()
        if not color:
            return None
        return {
            'id': color.id,
            'vendor': color.vendor.value,
            'code': color.code,
            'name': color.name,
            'hex': color.hex,
            'is_default': color.is_default,
        }

    @staticmethod
    def is_valid_vendor(vendor_key: str) -> bool:
        """
        Check if a vendor key corresponds to a valid ColorVendor.

        Args:
            vendor_key: Vendor enum value string to check.

        Returns:
            True if vendor_key is a valid ColorVendor value.

        Side effects:
            None.
        """
        try:
            ColorVendor(vendor_key)
            return True
        except ValueError:
            return False
