"""
Color matching service for mapping quantized colors to thread palettes (DMC, etc.)
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple
from stitch.models.color import Color, ColorVendor


class ColorMatcher:
    """Match image colors to thread palette colors"""

    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_lab(rgb: Tuple[int, int, int]) -> np.ndarray:
        """Convert RGB to LAB color space for perceptual color difference"""
        # Create 1x1 image with the RGB color
        rgb_array = np.uint8([[rgb]])
        # Convert to LAB
        lab = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2LAB)
        return lab[0][0]

    @staticmethod
    def color_distance(color1_rgb: Tuple[int, int, int], color2_rgb: Tuple[int, int, int]) -> float:
        """
        Calculate perceptual color distance using Delta E (CIE76) in LAB space

        Returns:
            Distance value (lower = more similar)
        """
        lab1 = ColorMatcher.rgb_to_lab(color1_rgb)
        lab2 = ColorMatcher.rgb_to_lab(color2_rgb)

        # Delta E (CIE76) formula
        delta_e = np.sqrt(np.sum((lab1.astype(float) - lab2.astype(float)) ** 2))
        return float(delta_e)

    @staticmethod
    def find_nearest_palette_color(rgb: Tuple[int, int, int], palette: List[Color]) -> Tuple[Color, float]:
        """
        Find nearest color in palette using perceptual color distance

        Args:
            rgb: RGB tuple to match
            palette: List of Color objects to search

        Returns:
            Tuple of (nearest Color, distance)
        """
        min_distance = float('inf')
        nearest_color = None

        for palette_color in palette:
            palette_rgb = ColorMatcher.hex_to_rgb(palette_color.hex)
            distance = ColorMatcher.color_distance(rgb, palette_rgb)

            if distance < min_distance:
                min_distance = distance
                nearest_color = palette_color

        return nearest_color, min_distance

    @staticmethod
    def match_palette_to_dmc(quantized_palette: List[Dict], palette_name: str = 'dmc') -> List[Dict]:
        """
        Match quantized image palette to thread palette (DMC by default)

        Args:
            quantized_palette: List of color dicts from image quantization
            palette_name: Name of thread palette to match against

        Returns:
            List of matched colors with original and DMC mapping info
        """
        # Map lowercase palette names to ColorVendor enum values
        vendor_map = {v.value.lower(): v for v in ColorVendor}
        vendor = vendor_map.get(palette_name.lower())
        if not vendor:
            raise ValueError(
                f"Unknown palette: {palette_name}. "
                f"Available: {', '.join(vendor_map.keys())}"
            )
        thread_palette = Color.query.filter_by(vendor=vendor).all()
        matched_colors = []

        for idx, q_color in enumerate(quantized_palette):
            # Get RGB from hex
            rgb = ColorMatcher.hex_to_rgb(q_color['rgbHex'])

            # Find nearest DMC color
            nearest_dmc, distance = ColorMatcher.find_nearest_palette_color(rgb, thread_palette)

            matched_colors.append({
                'index': idx,
                'original': {
                    'rgbHex': q_color['rgbHex'],
                    'rgb': rgb,
                    'name': q_color.get('name', f'Color {idx + 1}'),
                    'symbol': q_color.get('symbol', '?'),
                    'count': q_color.get('count', 0)
                },
                'dmc': {
                    'code': nearest_dmc.code,
                    'name': nearest_dmc.name,
                    'hex': nearest_dmc.hex,
                    'rgb': ColorMatcher.hex_to_rgb(nearest_dmc.hex),
                    'distance': round(distance, 2)
                },
                'use_dmc': True,  # Default to using DMC color
                'selected': True   # Default to including this color
            })

        return matched_colors

    @staticmethod
    def create_dmc_mapped_palette(matched_colors: List[Dict], vendor_name: str = 'dmc') -> List[Dict]:
        """
        Create final palette for project using selected vendor colors

        Args:
            matched_colors: List of color matches with selection flags
            vendor_name: Vendor name (default: 'dmc')

        Returns:
            Final palette list ready for project creation
        """
        final_palette = []
        symbol_index = 0

        for match in matched_colors:
            if not match.get('selected', True):
                continue  # Skip unselected colors

            use_dmc = match.get('use_dmc', True)

            if use_dmc:
                color_info = {
                    'id': f'c{symbol_index}',
                    'vendor': vendor_name.upper(),
                    'code': match['dmc']['code'],
                    'name': match['dmc']['name'],
                    'rgbHex': match['dmc']['hex'],
                    'rgb': match['dmc']['rgb'],
                    'symbol': match['original']['symbol'],
                    'sortIndex': symbol_index,
                    'count': match['original']['count']
                }
            else:
                color_info = {
                    'id': f'c{symbol_index}',
                    'vendor': None,
                    'code': None,
                    'name': match['original']['name'],
                    'rgbHex': match['original']['rgbHex'],
                    'rgb': match['original']['rgb'],
                    'symbol': match['original']['symbol'],
                    'sortIndex': symbol_index,
                    'count': match['original']['count']
                }

            final_palette.append(color_info)
            symbol_index += 1

        return final_palette

    @staticmethod
    def update_selection(matched_colors: List[Dict], selected_indices: List[str],
                         use_dmc_indices: List[str]) -> List[Dict]:
        """
        Update matched colors with selection and use_dmc flags from form input.

        Args:
            matched_colors: List of color matches from match_palette_to_dmc
            selected_indices: List of index strings that are selected
            use_dmc_indices: List of index strings that should use DMC colors

        Returns:
            Updated matched_colors list
        """
        for match in matched_colors:
            idx_str = str(match['index'])
            match['selected'] = idx_str in selected_indices
            match['use_dmc'] = idx_str in use_dmc_indices

        return matched_colors

    @staticmethod
    def merge_similar_colors(matched_colors: List[Dict], merge_threshold: float = 10.0) -> List[Dict]:
        """
        Merge similar DMC colors to reduce palette size

        Args:
            matched_colors: List of color matches
            merge_threshold: Delta E threshold for merging (default 10.0)

        Returns:
            Updated matched_colors with merged colors
        """
        if len(matched_colors) <= 1:
            return matched_colors

        merged = []
        used_indices = set()

        for i, color1 in enumerate(matched_colors):
            if i in used_indices or not color1.get('use_dmc', True):
                merged.append(color1)
                continue

            # Find similar colors to merge
            similar_indices = [i]
            merged_count = color1['original']['count']

            for j, color2 in enumerate(matched_colors[i+1:], start=i+1):
                if j in used_indices or not color2.get('use_dmc', True):
                    continue

                # Check if DMC colors are the same or very similar
                if color1['dmc']['code'] == color2['dmc']['code']:
                    similar_indices.append(j)
                    merged_count += color2['original']['count']
                    used_indices.add(j)

            # Create merged color entry
            merged_color = color1.copy()
            merged_color['original']['count'] = merged_count
            merged.append(merged_color)

        return merged
