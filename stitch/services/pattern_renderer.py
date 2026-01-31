"""Pattern rendering service for generating pattern images and charts"""
import cv2
import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import base64


class PatternRenderer:
    """Render cross-stitch patterns to images"""

    @staticmethod
    def render_colored_pattern(state: Dict, width: int, height: int,
                              cell_size: int = 20) -> np.ndarray:
        """
        Render pattern with colored cross stitches

        Args:
            state: Project state with layers and palette
            width: Grid width
            height: Grid height
            cell_size: Size of each cell in pixels

        Returns:
            RGB numpy array of the rendered pattern
        """
        # Create white canvas
        img_width = width * cell_size
        img_height = height * cell_size
        image = np.full((img_height, img_width, 3), 255, dtype=np.uint8)

        palette = state['palette']
        layers = state['layers']

        # Render only visible and exportable layers
        for layer in layers:
            if not layer.get('visible', True):
                continue
            if not layer.get('activeForExport', True):
                continue
            if layer['type'] != 'raster':
                continue

            cells = layer.get('cells', {})

            for cell_key, cell_data in cells.items():
                # Parse cell position from key
                cell_index = int(cell_key)
                y = cell_index // width
                x = cell_index % width

                if x >= width or y >= height:
                    continue

                palette_index = cell_data.get('paletteIndex', 0)
                if palette_index >= len(palette):
                    continue

                color = palette[palette_index]

                # Get RGB color
                if 'rgb' in color:
                    rgb = color['rgb']
                elif 'rgbHex' in color:
                    hex_color = color['rgbHex'].lstrip('#')
                    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                else:
                    rgb = (0, 0, 0)

                # Draw cross stitch (X pattern)
                PatternRenderer._draw_cross_stitch(
                    image, x * cell_size, y * cell_size, cell_size, rgb
                )

        return image

    @staticmethod
    def render_symbol_pattern(state: Dict, width: int, height: int,
                             cell_size: int = 30) -> np.ndarray:
        """
        Render pattern with symbols instead of colors.

        Each unique (color, stitch_type) combination gets a unique symbol.

        Args:
            state: Project state with layers and palette
            width: Grid width
            height: Grid height
            cell_size: Size of each cell in pixels

        Returns:
            RGB numpy array of the rendered symbol pattern
        """
        # Create white canvas
        img_width = width * cell_size
        img_height = height * cell_size
        image = np.full((img_height, img_width, 3), 255, dtype=np.uint8)

        palette = state['palette']
        layers = state['layers']

        # Generate symbol map for (color, stitch_type) combinations
        symbol_map = PatternRenderer._generate_symbol_map(state, width, height)

        # Draw grid lines
        PatternRenderer._draw_grid(image, width, height, cell_size)

        # Draw grid numbers
        PatternRenderer._draw_grid_numbers(image, width, height, cell_size)

        # Render only visible and exportable layers
        for layer in layers:
            if not layer.get('visible', True):
                continue
            if not layer.get('activeForExport', True):
                continue
            if layer['type'] != 'raster':
                continue

            cells = layer.get('cells', {})

            for cell_key, cell_data in cells.items():
                # Parse cell position from key
                cell_index = int(cell_key)
                y = cell_index // width
                x = cell_index % width

                if x >= width or y >= height:
                    continue

                palette_index = cell_data.get('paletteIndex', 0)
                stitch_type = cell_data.get('stitchType', 'full')

                if palette_index >= len(palette):
                    continue

                # Get symbol for this (color, stitch_type) combination
                symbol = symbol_map.get((palette_index, stitch_type), '?')

                # Draw symbol
                PatternRenderer._draw_symbol(
                    image, x * cell_size, y * cell_size, cell_size, symbol
                )

        return image

    @staticmethod
    def _draw_cross_stitch(image: np.ndarray, x: int, y: int,
                          size: int, color: Tuple[int, int, int]) -> None:
        """Draw a colored cross stitch (X)"""
        padding = int(size * 0.15)
        thickness = max(1, size // 10)

        # Draw X pattern
        cv2.line(
            image,
            (x + padding, y + padding),
            (x + size - padding, y + size - padding),
            color,
            thickness,
            cv2.LINE_AA
        )
        cv2.line(
            image,
            (x + size - padding, y + padding),
            (x + padding, y + size - padding),
            color,
            thickness,
            cv2.LINE_AA
        )

    @staticmethod
    def _draw_symbol(image: np.ndarray, x: int, y: int,
                    size: int, symbol: str) -> None:
        """Draw a symbol in a cell (black text)"""
        PatternRenderer._draw_symbol_colored(image, x, y, size, symbol, (0, 0, 0))

    @staticmethod
    def _draw_symbol_colored(image: np.ndarray, x: int, y: int,
                             size: int, symbol: str,
                             color: Tuple[int, int, int]) -> None:
        """Draw a symbol in a cell with specified color"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = size / 40  # Scale font based on cell size
        thickness = max(1, size // 20)

        # Get text size for centering
        (text_width, text_height), baseline = cv2.getTextSize(
            symbol, font, font_scale, thickness
        )

        # Center the text
        text_x = x + (size - text_width) // 2
        text_y = y + (size + text_height) // 2

        cv2.putText(
            image,
            symbol,
            (text_x, text_y),
            font,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA
        )

    @staticmethod
    def _draw_grid(image: np.ndarray, width: int, height: int,
                  cell_size: int) -> None:
        """Draw grid lines on the pattern"""
        img_height, img_width = image.shape[:2]

        # Light gray for minor grid
        minor_color = (220, 220, 220)
        # Dark gray for major grid (every 10 cells)
        major_color = (150, 150, 150)

        # Vertical lines
        for x in range(width + 1):
            x_pos = x * cell_size
            color = major_color if x % 10 == 0 else minor_color
            thickness = 2 if x % 10 == 0 else 1
            cv2.line(image, (x_pos, 0), (x_pos, img_height), color, thickness)

        # Horizontal lines
        for y in range(height + 1):
            y_pos = y * cell_size
            color = major_color if y % 10 == 0 else minor_color
            thickness = 2 if y % 10 == 0 else 1
            cv2.line(image, (0, y_pos), (img_width, y_pos), color, thickness)

    @staticmethod
    def _draw_grid_numbers(image: np.ndarray, width: int, height: int,
                          cell_size: int) -> None:
        """Draw grid numbers at every 10th cell"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.3, cell_size / 50)
        thickness = max(1, cell_size // 30)
        color = (100, 100, 100)  # Dark gray

        # Add padding for numbers (expand canvas)
        padding_top = max(20, cell_size)
        padding_left = max(30, cell_size)

        # Create new image with padding
        img_height, img_width = image.shape[:2]
        new_image = np.full(
            (img_height + padding_top, img_width + padding_left, 3),
            255,
            dtype=np.uint8
        )

        # Copy original image to padded image
        new_image[padding_top:, padding_left:] = image

        # Draw numbers along top edge (X axis)
        for x in range(0, width + 1, 10):
            x_pos = padding_left + x * cell_size
            text = str(x)
            (text_width, text_height), _ = cv2.getTextSize(
                text, font, font_scale, thickness
            )
            text_x = x_pos - text_width // 2
            text_y = padding_top - 5

            cv2.putText(
                new_image,
                text,
                (text_x, text_y),
                font,
                font_scale,
                color,
                thickness,
                cv2.LINE_AA
            )

        # Draw numbers along left edge (Y axis)
        for y in range(0, height + 1, 10):
            y_pos = padding_top + y * cell_size
            text = str(y)
            (text_width, text_height), _ = cv2.getTextSize(
                text, font, font_scale, thickness
            )
            text_x = padding_left - text_width - 5
            text_y = y_pos + text_height // 2

            cv2.putText(
                new_image,
                text,
                (text_x, text_y),
                font,
                font_scale,
                color,
                thickness,
                cv2.LINE_AA
            )

        # Copy back to original image array (modify in place)
        image.resize(new_image.shape, refcheck=False)
        image[:] = new_image

    # Stitch type categories for grouping
    STITCH_CATEGORIES = {
        'full': 'Full Cross',
        'half-slash': 'Half Stitch',
        'half-backslash': 'Half Stitch',
        'quarter-tl': 'Quarter Stitch',
        'quarter-tr': 'Quarter Stitch',
        'quarter-bl': 'Quarter Stitch',
        'quarter-br': 'Quarter Stitch',
        'three-quarter-tl': 'Three-Quarter Stitch',
        'three-quarter-tr': 'Three-Quarter Stitch',
        'three-quarter-bl': 'Three-Quarter Stitch',
        'three-quarter-br': 'Three-Quarter Stitch',
        'petite': 'Special Stitch',
        'french-knot': 'Special Stitch',
        'long-vertical': 'Long Stitch',
        'long-horizontal': 'Long Stitch',
        'backstitch-horizontal': 'Backstitch',
        'backstitch-vertical': 'Backstitch',
        'backstitch-slash': 'Backstitch',
        'backstitch-backslash': 'Backstitch',
    }

    # Stitch type icons (matching JS stitch definitions)
    STITCH_ICONS = {
        'full': '✕',
        'half-slash': '/',
        'half-backslash': '\\',
        'quarter-tl': '◸',
        'quarter-tr': '◹',
        'quarter-bl': '◺',
        'quarter-br': '◿',
        'three-quarter-tl': '⟋',
        'three-quarter-tr': '⟍',
        'three-quarter-bl': '⟍',
        'three-quarter-br': '⟋',
        'petite': '✕',
        'french-knot': '•',
        'long-vertical': '|',
        'long-horizontal': '―',
        'backstitch-horizontal': '─',
        'backstitch-vertical': '│',
        'backstitch-slash': '╱',
        'backstitch-backslash': '╲',
    }

    STITCH_CATEGORY_ORDER = [
        'Full Cross',
        'Half Stitch',
        'Quarter Stitch',
        'Three-Quarter Stitch',
        'Special Stitch',
        'Long Stitch',
        'Backstitch',
    ]

    # Available symbols for pattern charts (easily distinguishable)
    SYMBOLS = [
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
        '@', '#', '$', '%', '&', '*', '+', '=', '~',
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    ]

    @staticmethod
    def _generate_symbol_map(state: Dict, width: int, height: int) -> Dict[Tuple[int, str], str]:
        """
        Generate unique symbols for each (color, stitch_type) combination.

        Args:
            state: Project state with layers and palette
            width: Grid width
            height: Grid height

        Returns:
            Dict mapping (paletteIndex, stitchType) tuples to unique symbols
        """
        palette = state['palette']
        layers = state['layers']

        # Find all unique (color, stitch_type) combinations used
        used_combinations = set()

        for layer in layers:
            if not layer.get('visible', True):
                continue
            if not layer.get('activeForExport', True):
                continue
            if layer['type'] != 'raster':
                continue

            cells = layer.get('cells', {})

            for cell_data in cells.values():
                palette_index = cell_data.get('paletteIndex', 0)
                stitch_type = cell_data.get('stitchType', 'full')

                if palette_index < len(palette):
                    used_combinations.add((palette_index, stitch_type))

        # Sort for consistent symbol assignment (by palette index, then stitch type)
        sorted_combinations = sorted(used_combinations, key=lambda x: (x[0], x[1]))

        # Assign symbols
        symbol_map = {}
        for i, combo in enumerate(sorted_combinations):
            if i < len(PatternRenderer.SYMBOLS):
                symbol_map[combo] = PatternRenderer.SYMBOLS[i]
            else:
                # Fallback for many combinations: use index
                symbol_map[combo] = str(i)

        return symbol_map

    @staticmethod
    def generate_legend(state: Dict, width: int, height: int) -> List[Dict]:
        """
        Generate legend data with color and stitch type usage statistics.

        Each unique (color, stitch_type) combination gets its own symbol and entry.

        Args:
            state: Project state with layers and palette
            width: Grid width
            height: Grid height

        Returns:
            List of dicts with color info, stitch type, symbol, and usage count
        """
        palette = state['palette']
        layers = state['layers']

        # Generate symbol map for all combinations
        symbol_map = PatternRenderer._generate_symbol_map(state, width, height)

        # Count usage per (color, stitch_type) combination
        combo_counts = {}

        for layer in layers:
            if not layer.get('visible', True):
                continue
            if not layer.get('activeForExport', True):
                continue
            if layer['type'] != 'raster':
                continue

            cells = layer.get('cells', {})

            for cell_data in cells.values():
                palette_index = cell_data.get('paletteIndex', 0)
                stitch_type = cell_data.get('stitchType', 'full')

                if palette_index < len(palette):
                    key = (palette_index, stitch_type)
                    combo_counts[key] = combo_counts.get(key, 0) + 1

        # Build legend entries
        legend = []
        for (palette_index, stitch_type), count in combo_counts.items():
            if count == 0:
                continue

            color = palette[palette_index]
            symbol = symbol_map.get((palette_index, stitch_type), '?')
            category = PatternRenderer.STITCH_CATEGORIES.get(stitch_type, 'Full Cross')
            stitch_icon = PatternRenderer.STITCH_ICONS.get(stitch_type, '✕')

            legend.append({
                'paletteIndex': palette_index,
                'stitchType': stitch_type,
                'stitchCategory': category,
                'stitchIcon': stitch_icon,
                'symbol': symbol,
                'rgbHex': color.get('rgbHex', '#000000'),
                'rgb': color.get('rgb', (0, 0, 0)),
                'vendor': color.get('vendor'),
                'code': color.get('code'),
                'name': color.get('name', f'Color {palette_index + 1}'),
                'count': count
            })

        # Sort by usage (most used first)
        legend.sort(key=lambda x: x['count'], reverse=True)

        return legend

    @staticmethod
    def generate_legend_by_stitch_type(state: Dict, width: int, height: int) -> Dict[str, List[Dict]]:
        """
        Generate legend data grouped by stitch type category.

        Each unique (color, stitch_type) combination gets its own symbol.

        Args:
            state: Project state with layers and palette
            width: Grid width
            height: Grid height

        Returns:
            Dict mapping stitch category names to lists of color entries
        """
        palette = state['palette']
        layers = state['layers']

        # Generate symbol map for all combinations
        symbol_map = PatternRenderer._generate_symbol_map(state, width, height)

        # Count usage per (color, stitch_type) combination
        color_stitch_counts = {}

        for layer in layers:
            if not layer.get('visible', True):
                continue
            if not layer.get('activeForExport', True):
                continue
            if layer['type'] != 'raster':
                continue

            cells = layer.get('cells', {})

            for cell_data in cells.values():
                palette_index = cell_data.get('paletteIndex', 0)
                stitch_type = cell_data.get('stitchType', 'full')

                if palette_index < len(palette):
                    key = (palette_index, stitch_type)
                    color_stitch_counts[key] = color_stitch_counts.get(key, 0) + 1

        # Group by stitch category
        grouped = {cat: [] for cat in PatternRenderer.STITCH_CATEGORY_ORDER}

        for (palette_index, stitch_type), count in color_stitch_counts.items():
            if count == 0:
                continue

            color = palette[palette_index]
            symbol = symbol_map.get((palette_index, stitch_type), '?')
            category = PatternRenderer.STITCH_CATEGORIES.get(stitch_type, 'Full Cross')
            stitch_icon = PatternRenderer.STITCH_ICONS.get(stitch_type, '✕')

            entry = {
                'paletteIndex': palette_index,
                'stitchType': stitch_type,
                'stitchIcon': stitch_icon,
                'symbol': symbol,
                'rgbHex': color.get('rgbHex', '#000000'),
                'rgb': color.get('rgb', (0, 0, 0)),
                'vendor': color.get('vendor'),
                'code': color.get('code'),
                'name': color.get('name', f'Color {palette_index + 1}'),
                'count': count
            }

            if category in grouped:
                grouped[category].append(entry)

        # Sort each category by count (most used first)
        for category in grouped:
            grouped[category].sort(key=lambda x: x['count'], reverse=True)

        # Remove empty categories
        grouped = {k: v for k, v in grouped.items() if v}

        return grouped

    @staticmethod
    def calculate_pattern_pages(width: int, height: int,
                                page_size: int = 50,
                                overlap: int = 5) -> List[Dict]:
        """
        Calculate page layout for paginated pattern display.

        Args:
            width: Pattern width in stitches
            height: Pattern height in stitches
            page_size: Stitches per page (default 50x50)
            overlap: Overlap between pages for continuity (default 5)

        Returns:
            List of page definitions with start/end coordinates
        """
        effective_size = page_size - overlap
        cols = max(1, math.ceil(width / effective_size))
        rows = max(1, math.ceil(height / effective_size))

        pages = []
        for row in range(rows):
            for col in range(cols):
                x_start = col * effective_size
                y_start = row * effective_size
                x_end = min(x_start + page_size, width)
                y_end = min(y_start + page_size, height)

                pages.append({
                    'page_num': len(pages) + 1,
                    'row': row + 1,
                    'col': col + 1,
                    'total_rows': rows,
                    'total_cols': cols,
                    'x_start': x_start,
                    'y_start': y_start,
                    'x_end': x_end,
                    'y_end': y_end,
                    'label': f"({x_start + 1}-{x_end}, {y_start + 1}-{y_end})"
                })

        return pages

    @staticmethod
    def _get_luminance(rgb: Tuple[int, int, int]) -> float:
        """
        Calculate relative luminance of a color.

        Uses the formula for relative luminance per WCAG 2.0.
        Returns a value between 0 (black) and 1 (white).
        """
        r, g, b = rgb
        # Convert to sRGB
        r = r / 255.0
        g = g / 255.0
        b = b / 255.0

        # Apply gamma correction
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4

        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    @staticmethod
    def _get_contrasting_color(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Get a contrasting color (black or white) for text on the given background.
        """
        luminance = PatternRenderer._get_luminance(rgb)
        # Use white text on dark backgrounds, black on light
        return (255, 255, 255) if luminance < 0.5 else (0, 0, 0)

    @staticmethod
    def render_symbol_page(state: Dict, width: int, height: int,
                           x_start: int, y_start: int,
                           x_end: int, y_end: int,
                           cell_size: int = 20,
                           colored_background: bool = False) -> np.ndarray:
        """
        Render a specific region of the pattern with symbols.

        Each unique (color, stitch_type) combination gets a unique symbol.

        Args:
            state: Project state with layers and palette
            width: Full pattern width
            height: Full pattern height
            x_start: Start X coordinate (0-indexed)
            y_start: Start Y coordinate (0-indexed)
            x_end: End X coordinate (exclusive)
            y_end: End Y coordinate (exclusive)
            cell_size: Size of each cell in pixels
            colored_background: If True, draw colored backgrounds with adaptive symbol colors

        Returns:
            RGB numpy array of the rendered pattern region
        """
        region_width = x_end - x_start
        region_height = y_end - y_start

        # Create white canvas
        img_width = region_width * cell_size
        img_height = region_height * cell_size
        image = np.full((img_height, img_width, 3), 255, dtype=np.uint8)

        palette = state['palette']
        layers = state['layers']

        # Generate symbol map for (color, stitch_type) combinations
        symbol_map = PatternRenderer._generate_symbol_map(state, width, height)

        # If colored background, draw cell backgrounds first (before grid)
        if colored_background:
            for layer in layers:
                if not layer.get('visible', True):
                    continue
                if not layer.get('activeForExport', True):
                    continue
                if layer['type'] != 'raster':
                    continue

                cells = layer.get('cells', {})

                for cell_key, cell_data in cells.items():
                    cell_index = int(cell_key)
                    y = cell_index // width
                    x = cell_index % width

                    if x < x_start or x >= x_end:
                        continue
                    if y < y_start or y >= y_end:
                        continue

                    palette_index = cell_data.get('paletteIndex', 0)
                    if palette_index >= len(palette):
                        continue

                    color = palette[palette_index]

                    # Get RGB color
                    if 'rgbHex' in color:
                        hex_color = color['rgbHex'].lstrip('#')
                        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    else:
                        rgb = (200, 200, 200)

                    # Calculate position relative to region
                    rel_x = (x - x_start) * cell_size
                    rel_y = (y - y_start) * cell_size

                    # Fill cell with color
                    cv2.rectangle(
                        image,
                        (rel_x, rel_y),
                        (rel_x + cell_size - 1, rel_y + cell_size - 1),
                        rgb,
                        -1  # Filled
                    )

        # Draw grid lines
        PatternRenderer._draw_region_grid(
            image, region_width, region_height, cell_size,
            x_start, y_start
        )

        # Render only visible and exportable layers
        for layer in layers:
            if not layer.get('visible', True):
                continue
            if not layer.get('activeForExport', True):
                continue
            if layer['type'] != 'raster':
                continue

            cells = layer.get('cells', {})

            for cell_key, cell_data in cells.items():
                cell_index = int(cell_key)
                y = cell_index // width
                x = cell_index % width

                # Check if cell is in this region
                if x < x_start or x >= x_end:
                    continue
                if y < y_start or y >= y_end:
                    continue

                palette_index = cell_data.get('paletteIndex', 0)
                stitch_type = cell_data.get('stitchType', 'full')

                if palette_index >= len(palette):
                    continue

                # Get symbol for this (color, stitch_type) combination
                symbol = symbol_map.get((palette_index, stitch_type), '?')

                # Calculate position relative to region
                rel_x = (x - x_start) * cell_size
                rel_y = (y - y_start) * cell_size

                # Determine symbol color based on background
                if colored_background:
                    color = palette[palette_index]
                    if 'rgbHex' in color:
                        hex_color = color['rgbHex'].lstrip('#')
                        bg_rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    else:
                        bg_rgb = (200, 200, 200)
                    symbol_color = PatternRenderer._get_contrasting_color(bg_rgb)
                else:
                    symbol_color = (0, 0, 0)  # Black on white

                PatternRenderer._draw_symbol_colored(
                    image, rel_x, rel_y, cell_size, symbol, symbol_color
                )

        # Add grid numbers
        PatternRenderer._add_region_numbers(
            image, region_width, region_height, cell_size,
            x_start, y_start
        )

        return image

    @staticmethod
    def _draw_region_grid(image: np.ndarray, region_width: int,
                          region_height: int, cell_size: int,
                          x_offset: int, y_offset: int) -> None:
        """Draw grid lines for a pattern region with major lines at 10-cell intervals."""
        img_height, img_width = image.shape[:2]

        minor_color = (220, 220, 220)
        major_color = (150, 150, 150)

        # Vertical lines
        for x in range(region_width + 1):
            x_pos = x * cell_size
            global_x = x + x_offset
            color = major_color if global_x % 10 == 0 else minor_color
            thickness = 2 if global_x % 10 == 0 else 1
            cv2.line(image, (x_pos, 0), (x_pos, img_height), color, thickness)

        # Horizontal lines
        for y in range(region_height + 1):
            y_pos = y * cell_size
            global_y = y + y_offset
            color = major_color if global_y % 10 == 0 else minor_color
            thickness = 2 if global_y % 10 == 0 else 1
            cv2.line(image, (0, y_pos), (img_width, y_pos), color, thickness)

    @staticmethod
    def _add_region_numbers(image: np.ndarray, region_width: int,
                            region_height: int, cell_size: int,
                            x_offset: int, y_offset: int) -> None:
        """Add coordinate numbers to a pattern region image."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.3, cell_size / 60)
        thickness = max(1, cell_size // 30)
        color = (100, 100, 100)

        padding_top = max(20, int(cell_size * 0.8))
        padding_left = max(30, int(cell_size * 1.2))

        img_height, img_width = image.shape[:2]
        new_image = np.full(
            (img_height + padding_top, img_width + padding_left, 3),
            255,
            dtype=np.uint8
        )

        new_image[padding_top:, padding_left:] = image

        # Draw X-axis numbers (top)
        for x in range(region_width + 1):
            global_x = x + x_offset
            if global_x % 10 == 0:
                x_pos = padding_left + x * cell_size
                text = str(global_x)
                (text_width, text_height), _ = cv2.getTextSize(
                    text, font, font_scale, thickness
                )
                text_x = x_pos - text_width // 2
                text_y = padding_top - 5

                cv2.putText(new_image, text, (text_x, text_y), font,
                           font_scale, color, thickness, cv2.LINE_AA)

        # Draw Y-axis numbers (left)
        for y in range(region_height + 1):
            global_y = y + y_offset
            if global_y % 10 == 0:
                y_pos = padding_top + y * cell_size
                text = str(global_y)
                (text_width, text_height), _ = cv2.getTextSize(
                    text, font, font_scale, thickness
                )
                text_x = padding_left - text_width - 5
                text_y = y_pos + text_height // 2

                cv2.putText(new_image, text, (text_x, text_y), font,
                           font_scale, color, thickness, cv2.LINE_AA)

        # Resize original image to new dimensions
        image.resize(new_image.shape, refcheck=False)
        image[:] = new_image

    @staticmethod
    def render_overview_pattern(state: Dict, width: int, height: int,
                                max_size: int = 400) -> np.ndarray:
        """
        Render a scaled-down colored pattern for overview display.

        Args:
            state: Project state with layers and palette
            width: Grid width
            height: Grid height
            max_size: Maximum dimension in pixels

        Returns:
            RGB numpy array of the scaled pattern
        """
        # Calculate cell size to fit within max_size
        cell_size = max(1, min(max_size // width, max_size // height))
        cell_size = min(cell_size, 20)  # Cap at 20px per cell

        return PatternRenderer.render_colored_pattern(state, width, height, cell_size)

    @staticmethod
    def image_to_base64(image: np.ndarray) -> str:
        """Convert numpy image to base64 PNG data URI"""
        # Convert RGB to BGR for OpenCV
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Encode as PNG
        _, buffer = cv2.imencode('.png', image_bgr)

        # Convert to base64
        img_str = base64.b64encode(buffer).decode()
        return f'data:image/png;base64,{img_str}'
