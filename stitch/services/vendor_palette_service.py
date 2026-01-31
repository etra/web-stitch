"""
Vendor palette service for managing thread vendor palettes.

This service provides utilities for accessing and searching color palettes
from different thread vendors (DMC, HAMA, ARTKAL, NABBI).
"""
from typing import List, Dict, Optional
from stitch.models.static_data import get_palette, Color, PALETTES


class VendorPaletteService:
    """Manage vendor palette operations"""

    # Vendor metadata
    VENDOR_INFO = {
        'dmc': {
            'name': 'DMC',
            'full_name': 'DMC Embroidery Floss',
            'description': 'Professional embroidery thread with 500+ colors',
            'type': 'embroidery'
        },
        'hama': {
            'name': 'HAMA',
            'full_name': 'HAMA Beads',
            'description': 'Popular fuse bead brand for pixel art',
            'type': 'beads'
        },
        'artkal': {
            'name': 'ARTKAL',
            'full_name': 'ARTKAL Beads',
            'description': 'High-quality fuse beads for crafting',
            'type': 'beads'
        },
        'nabbi': {
            'name': 'NABBI',
            'full_name': 'NABBI Beads',
            'description': 'Fuse beads for creative projects',
            'type': 'beads'
        }
    }

    @staticmethod
    def get_vendor_info(vendor_name: str) -> Dict:
        """
        Get vendor metadata.

        Args:
            vendor_name: Vendor identifier (e.g., 'dmc', 'hama')

        Returns:
            Dictionary with vendor info including color count
        """
        vendor_key = vendor_name.lower()
        info = VendorPaletteService.VENDOR_INFO.get(vendor_key, {})

        # Add color count
        try:
            palette = get_palette(vendor_key)
            info['color_count'] = len(palette)
        except ValueError:
            info['color_count'] = 0

        return info

    @staticmethod
    def get_all_vendors() -> List[Dict]:
        """
        Get all available vendors with metadata.

        Returns:
            List of vendor info dictionaries
        """
        vendors = []
        for vendor_key in PALETTES.keys():
            info = VendorPaletteService.get_vendor_info(vendor_key)
            info['key'] = vendor_key
            vendors.append(info)

        # Sort by name
        vendors.sort(key=lambda x: x.get('name', ''))
        return vendors

    @staticmethod
    def search_colors(vendor: str, query: str) -> List[Dict]:
        """
        Search colors by name or code in vendor palette.

        Args:
            vendor: Vendor identifier
            query: Search query (name or code)

        Returns:
            List of matching colors as dictionaries
        """
        try:
            palette = get_palette(vendor.lower())
        except ValueError:
            return []

        query_lower = query.lower().strip()

        if not query_lower:
            # Return all colors if no query
            return [color.to_dict() for color in palette]

        # Search by code or name
        matches = []
        for color in palette:
            if (query_lower in color.code.lower() or
                query_lower in color.name.lower()):
                matches.append(color.to_dict())

        return matches

    @staticmethod
    def get_palette_as_dict_list(vendor: str) -> List[Dict]:
        """
        Get full vendor palette as list of dictionaries.

        Args:
            vendor: Vendor identifier

        Returns:
            List of color dictionaries
        """
        try:
            palette = get_palette(vendor.lower())
            return [color.to_dict() for color in palette]
        except ValueError:
            return []

    @staticmethod
    def get_color(vendor: str, code: str) -> Optional[Dict]:
        """
        Get a specific color from vendor palette by code.

        Args:
            vendor: Vendor identifier
            code: Color code

        Returns:
            Color dictionary if found, None otherwise
        """
        try:
            palette = get_palette(vendor.lower())
            for color in palette:
                if color.code == code:
                    return color.to_dict()
        except ValueError:
            pass

        return None

    @staticmethod
    def validate_color_codes(vendor: str, codes: List[str]) -> bool:
        """
        Validate that all color codes exist in vendor palette.

        Args:
            vendor: Vendor identifier
            codes: List of color codes to validate

        Returns:
            True if all codes are valid, False otherwise
        """
        try:
            palette = get_palette(vendor.lower())
            valid_codes = {color.code for color in palette}
            return all(code in valid_codes for code in codes)
        except ValueError:
            return False

    @staticmethod
    def get_all_colors() -> List[Dict]:
        """
        Get all colors from all vendors formatted for API response.

        Returns:
            List of color dictionaries with id, vendor, code, name, hex, text

        Side effects:
            None (read-only)
        """
        colors = []
        for vendor, palette in PALETTES.items():
            for color in palette:
                colors.append({
                    'id': f'{vendor}_{color.code}',
                    'vendor': vendor.upper(),
                    'code': color.code,
                    'name': color.name,
                    'hex': color.hex,
                    'text': f'{vendor.upper()} {color.code} - {color.name}'
                })
        return colors

    @staticmethod
    def get_supported_vendors() -> List[str]:
        """
        Get list of supported vendor keys.

        Returns:
            List of vendor keys (lowercase)

        Side effects:
            None (read-only)
        """
        return list(PALETTES.keys())

    @staticmethod
    def is_valid_vendor(vendor: str) -> bool:
        """
        Check if vendor is supported.

        Args:
            vendor: Vendor key to check

        Returns:
            True if vendor is supported

        Side effects:
            None (read-only)
        """
        return vendor.lower() in PALETTES

    @staticmethod
    def match_colors_to_vendor(colors: List[Dict], vendor: str) -> List[Dict]:
        """
        Match a list of colors to the nearest colors in a vendor palette.

        Args:
            colors: List of color dicts with 'rgbHex' key
            vendor: Vendor key (e.g., 'dmc', 'hama')

        Returns:
            List of matched color dicts with vendor color info

        Side effects:
            None (read-only)

        Raises:
            ValueError: If vendor is not supported
        """
        from stitch.services.color_matcher import ColorMatcher

        thread_palette = get_palette(vendor.lower())
        matched_colors = []

        for idx, color in enumerate(colors):
            rgb = ColorMatcher.hex_to_rgb(color['rgbHex'])
            nearest_color, distance = ColorMatcher.find_nearest_palette_color(rgb, thread_palette)

            matched_colors.append({
                'id': color.get('id', f'c{idx}'),
                'vendor': vendor.upper(),
                'code': nearest_color.code,
                'name': nearest_color.name,
                'rgbHex': nearest_color.hex,
                'symbol': color.get('symbol', ''),
                'sortIndex': idx,
                'originalHex': color['rgbHex'],
                'distance': round(distance, 2)
            })

        return matched_colors
