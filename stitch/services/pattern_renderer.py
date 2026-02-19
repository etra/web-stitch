"""Pattern rendering service for generating pattern images and charts"""
import cv2
import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import base64
from PIL import Image, ImageDraw, ImageFont

from flask import current_app

from stitch.models.stitch import STITCH_TYPES


def _stitch_category_order() -> List[str]:
    """Derive ordered unique categories from STITCH_TYPES by sort_order."""
    seen = set()
    order = []
    for defn in sorted(STITCH_TYPES.values(), key=lambda d: d['sort_order']):
        cat = defn['category']
        if cat not in seen:
            seen.add(cat)
            order.append(cat)
    return order


STITCH_CATEGORY_ORDER = _stitch_category_order()


def _compute_symbol_placement(stitch_type: str):
    """Derive symbol center and scale from a stitch type's path_data bounding box.

    Returns (cx, cy, scale) where cx/cy are normalized 0..1 center coordinates
    and scale is the bbox extent (max of width, height).
    Quarter stitches are centered (since only one stitch per cell).
    """
    defn = STITCH_TYPES.get(stitch_type)
    path_data = defn.get('path_data') if defn else None
    if not path_data:
        return (0.5, 0.5, 0.8)

    all_x = []
    all_y = []
    for segment in path_data:
        for point in segment:
            all_x.append(point[0])
            all_y.append(point[1])

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    scale = max(max_x - min_x, max_y - min_y)

    # Quarter stitches: place symbol at the quadrant center
    if defn.get('category') == 'Quarter Stitch':
        if stitch_type == 'quarter-tl':
            return (0.25, 0.25, scale)
        if stitch_type == 'quarter-tr':
            return (0.75, 0.25, scale)
        if stitch_type == 'quarter-bl':
            return (0.25, 0.75, scale)
        if stitch_type == 'quarter-br':
            return (0.75, 0.75, scale)
        return (0.5, 0.5, scale)

    # Three-quarter stitches: center symbol in the triangle centroid
    # Aligned with frontend: 0.33/0.67
    if defn.get('category') == 'Three-Quarter Stitch':
        if stitch_type == 'three-quarter-tl':
            return (0.33, 0.33, scale)
        if stitch_type == 'three-quarter-br':
            return (0.67, 0.67, scale)
        if stitch_type == 'three-quarter-tr':
            return (0.67, 0.33, scale)
        if stitch_type == 'three-quarter-bl':
            return (0.33, 0.67, scale)

    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    return (cx, cy, scale)


SYMBOL_PLACEMENTS = {
    st: _compute_symbol_placement(st) for st in STITCH_TYPES
}

# Font scale – ratio of cell_size that becomes font size.
# Same size for all stitch types; the fill polygon shape communicates stitch type.
_SYMBOL_FONT_SCALE = 0.6


def _symbol_font_size(cell_size: int, stitch_type: str) -> int:
    """Compute symbol font size based on cell size."""
    size = max(6, int(cell_size * _SYMBOL_FONT_SCALE))
    defn = STITCH_TYPES.get(stitch_type)
    category = defn.get('category', '') if defn else ''
    if category in ('Three-Quarter Stitch', 'Quarter Stitch'):
        size = 12
    return size


def _snap_bbox(stitch_type: str):
    """Snap a bounding box to clean cell edges.

    Returns (x0, y0, x1, y1) normalized 0..1.  Coords near the cell
    boundary (<=0.15 or >=0.85) snap to 0.0/1.0.
    """
    defn = STITCH_TYPES.get(stitch_type)
    path_data = defn.get('path_data') if defn else None
    if not path_data:
        return (0.0, 0.0, 1.0, 1.0)

    all_x = []
    all_y = []
    for segment in path_data:
        for point in segment:
            all_x.append(point[0])
            all_y.append(point[1])

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    if min_x <= 0.15:
        min_x = 0.0
    if min_y <= 0.15:
        min_y = 0.0
    if max_x >= 0.85:
        max_x = 1.0
    if max_y >= 0.85:
        max_y = 1.0

    return (min_x, min_y, max_x, max_y)


def _compute_fill_polygon(stitch_type: str):
    """Compute a fill polygon for a stitch type.

    Returns a list of (x, y) normalized coordinate tuples.
    - Half stitches: triangle on the stitch side of the diagonal
    - Three-quarter stitches: L-shape (full cell minus the opposite quadrant)
    - Quarter stitches: centered rectangle (same size as petite)
    - Full / line: full cell rectangle
    """
    defn = STITCH_TYPES.get(stitch_type)
    if not defn or not defn.get('path_data'):
        return [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]

    category = defn.get('category', '')

    # Quarter stitch → fill the actual quadrant
    if category == 'Quarter Stitch':
        if stitch_type == 'quarter-tl':
            return [(0, 0), (0.5, 0), (0.5, 0.5), (0, 0.5)]
        if stitch_type == 'quarter-tr':
            return [(0.5, 0), (1, 0), (1, 0.5), (0.5, 0.5)]
        if stitch_type == 'quarter-bl':
            return [(0, 0.5), (0.5, 0.5), (0.5, 1), (0, 1)]
        if stitch_type == 'quarter-br':
            return [(0.5, 0.5), (1, 0.5), (1, 1), (0.5, 1)]

    # Half stitch → triangle
    if category == 'Half Stitch':
        seg = defn['path_data'][0]
        # Slash (/): start_y > end_y → upper-left triangle
        if seg[0][1] > seg[-1][1]:
            return [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
        # Backslash (\): → upper-right triangle
        return [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]

    # Three-quarter → diagonal half of cell (two opposite three-quarters fill the whole cell)
    if category == 'Three-Quarter Stitch':
        if stitch_type == 'three-quarter-tl':    # slash / + quarter from TL → top-left triangle
            return [(0, 0), (1, 0), (0, 1)]
        if stitch_type == 'three-quarter-br':    # slash / + quarter from BR → bottom-right triangle
            return [(1, 0), (1, 1), (0, 1)]
        if stitch_type == 'three-quarter-tr':    # backslash \ + quarter from TR → top-right triangle
            return [(0, 0), (1, 0), (1, 1)]
        if stitch_type == 'three-quarter-bl':    # backslash \ + quarter from BL → bottom-left triangle
            return [(0, 0), (0, 1), (1, 1)]
        return [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]

    # Everything else: snapped bounding-box rectangle
    x0, y0, x1, y1 = _snap_bbox(stitch_type)
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


FILL_POLYGONS = {
    st: _compute_fill_polygon(st) for st in STITCH_TYPES
}


class PatternRenderer:
    _font_cache: Dict[int, ImageFont.FreeTypeFont] = {}

    @staticmethod
    def _get_symbol_font(size: int) -> ImageFont.FreeTypeFont:
        """Load the bundled symbol font at the given pixel size, with caching."""
        if size in PatternRenderer._font_cache:
            return PatternRenderer._font_cache[size]

        import os
        font_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static', 'fonts', 'NotoSansSymbols2-Regular.ttf'
        )

        try:
            font = ImageFont.truetype(font_path, size)
        except (IOError, OSError):
            font = ImageFont.load_default(size)

        PatternRenderer._font_cache[size] = font
        return font
    """Render cross-stitch patterns to images"""

    @staticmethod
    def render_colored_pattern(state: Dict, width: int, height: int,
                              cell_size: int = 20,
                              solid_fill: bool = False) -> np.ndarray:
        """
        Render pattern with colored stitches using stitch definitions.

        Supports both cell-based (path-mode) and linear-mode stitches.
        Background is filled with the project cloth color.

        Args:
            state: Project state with layers, palette, and optional clothColor
            width: Grid width
            height: Grid height
            cell_size: Size of each cell in pixels
            solid_fill: Fill stitch shapes with solid color instead of
                        drawing X lines / stitch paths. Uses FILL_POLYGONS
                        for correct per-stitch-type shapes.

        Returns:
            RGB numpy array of the rendered pattern
        """

        # Background: cloth color from state, default white
        bg_rgb = PatternRenderer._hex_to_rgb_tuple(
            state.get('clothColor', '#FFFFFF'))

        img_width = width * cell_size
        img_height = height * cell_size
        image = np.full((img_height, img_width, 3), bg_rgb, dtype=np.uint8)

        palette = state['palette']
        layers = state['layers']
        thickness = max(1, cell_size // 10)

        # Render only visible and exportable raster layers
        for layer in layers:
            if not layer.get('visible', True):
                continue
            if not layer.get('activeForExport', True):
                continue
            if layer['type'] != 'raster':
                continue

            # --- Cells (path-mode stitches) ---
            cells = layer.get('cells', {})

            for cell_key, cell_stitches in cells.items():
                x, y = cell_key.split(',')
                x, y = int(x), int(y)

                if x >= width or y >= height:
                    continue

                stitch_list = cell_stitches if isinstance(cell_stitches, list) else [cell_stitches]
                for cell_data in stitch_list:
                    palette_index = cell_data.get('paletteIndex', 0)
                    if palette_index >= len(palette):
                        continue

                    rgb = PatternRenderer._resolve_color(palette[palette_index])
                    stitch_type = cell_data.get('stitchType', 'full')

                    if solid_fill:
                        poly = FILL_POLYGONS.get(stitch_type,
                                                 [(0, 0), (1, 0), (1, 1), (0, 1)])
                        ox, oy = x * cell_size, y * cell_size
                        pts = np.array(
                            [[int(ox + px * cell_size),
                              int(oy + py * cell_size)]
                             for px, py in poly],
                            dtype=np.int32
                        )
                        cv2.fillPoly(image, [pts], rgb)
                    else:
                        defn = STITCH_TYPES.get(stitch_type)
                        path_data = defn.get('path_data') if defn else None

                        if path_data:
                            PatternRenderer._draw_stitch_paths(
                                image, x * cell_size, y * cell_size,
                                cell_size, rgb, path_data, thickness
                            )
                        else:
                            PatternRenderer._draw_cross_stitch(
                                image, x * cell_size, y * cell_size, cell_size, rgb
                            )

            # --- Paths (linear-mode stitches) ---
            paths = layer.get('paths', [])

            for path in paths:
                palette_index = path.get('paletteIndex', 0)
                if palette_index >= len(palette):
                    continue

                rgb = PatternRenderer._resolve_color(palette[palette_index])

                x1 = int(path['startX'] * cell_size)
                y1 = int(path['startY'] * cell_size)
                x2 = int(path['endX'] * cell_size)
                y2 = int(path['endY'] * cell_size)

                line_thickness = max(1, cell_size // 20)
                cv2.line(image, (x1, y1), (x2, y2), rgb, line_thickness,
                         cv2.LINE_AA)

        return image

    @staticmethod
    def render_symbol_pattern(state: Dict, width: int, height: int,
                             cell_size: int = 40) -> np.ndarray:
        """
        Render pattern with symbols instead of colors.

        Uses per-color symbols from the palette (matching professional
        cross-stitch convention: one symbol per thread color).
        Symbol placement and size are derived from the stitch type's path_data
        bounding box so quarter stitches get small symbols in their quadrant, etc.

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

        # Draw grid lines
        PatternRenderer._draw_grid(image, width, height, cell_size)

        # Draw grid numbers
        PatternRenderer._draw_grid_numbers(image, width, height, cell_size)

        # Draw symbols — pre-render unique stamps, then blit via numpy
        stamp_cache = {}
        symbol_color = (0, 0, 0)

        for layer in layers:
            if not layer.get('visible', True):
                continue
            if not layer.get('activeForExport', True):
                continue
            if layer['type'] != 'raster':
                continue

            cells = layer.get('cells', {})

            for cell_key, cell_stitches in cells.items():
                x, y = cell_key.split(',')
                x, y = int(x), int(y)

                if x >= width or y >= height:
                    continue

                stitch_list = cell_stitches if isinstance(cell_stitches, list) else [cell_stitches]
                for cell_data in stitch_list:
                    palette_index = cell_data.get('paletteIndex', 0)
                    if palette_index >= len(palette):
                        continue

                    symbol = palette[palette_index].get('symbol', '?')

                    stitch_type = cell_data.get('stitchType', 'full')
                    cx, cy, _scale = SYMBOL_PLACEMENTS.get(stitch_type, (0.5, 0.5, 0.8))
                    font_size = _symbol_font_size(cell_size, stitch_type)

                    cache_key = (symbol, symbol_color, font_size, stitch_type)
                    if cache_key not in stamp_cache:
                        stamp_cache[cache_key] = PatternRenderer._render_symbol_stamp(
                            symbol, symbol_color, font_size, cell_size, cx, cy
                        )

                    stamp, ox, oy = stamp_cache[cache_key]
                    PatternRenderer._blit_stamp(
                        image, stamp, x * cell_size + ox, y * cell_size + oy
                    )
        return image

    @staticmethod
    def _draw_cross_stitch(image: np.ndarray, x: int, y: int,
                          size: int, color: Tuple[int, int, int]) -> None:
        """Draw a colored cross stitch (X). Fills solid at small sizes."""
        # At small cell sizes, X lines with anti-aliasing appear washed out.
        # Fill the cell solid instead for clean thumbnails/overviews.
        if size <= 4:
            image[y:y + size, x:x + size] = color
            return

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
    def _hex_to_rgb_tuple(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color string to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def _resolve_color(color: Dict) -> Tuple[int, int, int]:
        """Resolve a palette color entry to an RGB tuple."""
        if 'rgb' in color:
            return tuple(color['rgb'])
        elif 'rgbHex' in color:
            return PatternRenderer._hex_to_rgb_tuple(color['rgbHex'])
        return (0, 0, 0)

    @staticmethod
    def _draw_stitch_paths(image: np.ndarray, x: int, y: int,
                           cell_size: int, color: Tuple[int, int, int],
                           path_data: list, thickness: int) -> None:
        """Draw stitch using normalized pathData within a cell.

        Each segment in path_data is a list of [x, y] points normalized
        to 0..1. Points are scaled by cell_size and offset by the cell
        origin (x, y).
        """
        for segment in path_data:
            if len(segment) < 2:
                continue
            for i in range(len(segment) - 1):
                pt1 = (int(x + segment[i][0] * cell_size),
                        int(y + segment[i][1] * cell_size))
                pt2 = (int(x + segment[i + 1][0] * cell_size),
                        int(y + segment[i + 1][1] * cell_size))
                cv2.line(image, pt1, pt2, color, thickness, cv2.LINE_AA)

    @staticmethod
    def _draw_symbol_pil(draw: ImageDraw.ImageDraw,
                         font: ImageFont.FreeTypeFont,
                         x: int, y: int, size: int,
                         symbol: str,
                         color: Tuple[int, int, int],
                         cx: float = 0.5,
                         cy: float = 0.5) -> None:
        """Draw a Unicode symbol at (cx, cy) within a cell using PIL.

        cx, cy are normalized 0..1 coordinates for the symbol center.
        Uses the actual glyph bounding box for precise visual centering
        rather than font baseline metrics. Draws a 1px contrasting outline
        so symbols remain visible on any background color.
        """
        center_x = x + cx * size
        center_y = y + cy * size

        # Get actual glyph bbox to compute visual center offset
        bbox = font.getbbox(symbol, anchor='lt')
        glyph_w = bbox[2] - bbox[0]
        glyph_h = bbox[3] - bbox[1]
        text_x = center_x - bbox[0] - glyph_w / 2
        text_y = center_y - bbox[1] - glyph_h / 2

        # 1px outline in contrasting color
        outline_color = (255, 255, 255) if sum(color) < 384 else (0, 0, 0)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((text_x + dx, text_y + dy), symbol, fill=outline_color, font=font, anchor='lt')

        draw.text((text_x, text_y), symbol, fill=color, font=font, anchor='lt')

    @staticmethod
    def _render_symbol_stamp(symbol: str, color: Tuple[int, int, int],
                             font_size: int, cell_size: int,
                             cx: float, cy: float) -> Tuple[np.ndarray, int, int]:
        """Pre-render a symbol with outline into an RGBA numpy stamp.

        Returns (stamp_rgba, offset_x, offset_y) where offsets are the
        top-left position within the cell where the stamp should be placed.
        """
        font = PatternRenderer._get_symbol_font(font_size)
        bbox = font.getbbox(symbol, anchor='lt')
        glyph_w = bbox[2] - bbox[0]
        glyph_h = bbox[3] - bbox[1]

        # Stamp size: glyph + 2px outline margin on each side
        margin = 2
        stamp_w = int(glyph_w) + margin * 2
        stamp_h = int(glyph_h) + margin * 2
        if stamp_w < 1 or stamp_h < 1:
            return np.zeros((1, 1, 4), dtype=np.uint8), 0, 0

        stamp_img = Image.new('RGBA', (stamp_w, stamp_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(stamp_img)

        # Draw position within stamp: margin offset minus glyph origin
        text_x = margin - bbox[0]
        text_y = margin - bbox[1]

        # 1px outline in contrasting color
        outline_color = (255, 255, 255) if sum(color) < 384 else (0, 0, 0)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((text_x + dx, text_y + dy), symbol,
                          fill=(*outline_color, 255), font=font, anchor='lt')

        draw.text((text_x, text_y), symbol,
                  fill=(*color, 255), font=font, anchor='lt')

        stamp_arr = np.array(stamp_img)

        # Calculate where to place the stamp within the cell
        center_x = cx * cell_size
        center_y = cy * cell_size
        offset_x = int(center_x - glyph_w / 2 - margin)
        offset_y = int(center_y - glyph_h / 2 - margin)

        return stamp_arr, offset_x, offset_y

    @staticmethod
    def _blit_stamp(image: np.ndarray, stamp: np.ndarray,
                    x: int, y: int) -> None:
        """Blit an RGBA stamp onto an RGB image at (x, y).

        Uses fast boolean masking since text stamps have binary alpha
        (fully opaque or fully transparent). No float math needed.
        """
        img_h, img_w = image.shape[:2]
        st_h, st_w = stamp.shape[:2]

        # Clip to image bounds
        src_x0 = max(0, -x)
        src_y0 = max(0, -y)
        dst_x0 = max(0, x)
        dst_y0 = max(0, y)
        dst_x1 = min(img_w, x + st_w)
        dst_y1 = min(img_h, y + st_h)
        src_x1 = src_x0 + (dst_x1 - dst_x0)
        src_y1 = src_y0 + (dst_y1 - dst_y0)

        if dst_x1 <= dst_x0 or dst_y1 <= dst_y0:
            return

        region = stamp[src_y0:src_y1, src_x0:src_x1]
        mask = region[:, :, 3] > 0
        image[dst_y0:dst_y1, dst_x0:dst_x1][mask] = region[:, :, :3][mask]

    @staticmethod
    def _draw_grid(image: np.ndarray, width: int, height: int,
                  cell_size: int) -> None:
        """Draw grid lines on the pattern"""
        img_height, img_width = image.shape[:2]
        major_interval = current_app.config.get('MAJOR_GRID_INTERVAL', 5)

        # Light gray for minor grid
        minor_color = (220, 220, 220)
        major_color = (150, 150, 150)

        # Vertical lines
        for x in range(width + 1):
            x_pos = x * cell_size
            color = major_color if x % major_interval == 0 else minor_color
            thickness = 2 if x % major_interval == 0 else 1
            cv2.line(image, (x_pos, 0), (x_pos, img_height), color, thickness)

        # Horizontal lines
        for y in range(height + 1):
            y_pos = y * cell_size
            color = major_color if y % major_interval == 0 else minor_color
            thickness = 2 if y % major_interval == 0 else 1
            cv2.line(image, (0, y_pos), (img_width, y_pos), color, thickness)

    @staticmethod
    def _draw_grid_numbers(image: np.ndarray, width: int, height: int,
                          cell_size: int) -> None:
        """Draw grid numbers at every major grid interval."""
        major_interval = current_app.config.get('MAJOR_GRID_INTERVAL', 5)
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
        for x in range(0, width + 1, major_interval):
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
        for y in range(0, height + 1, major_interval):
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

    @staticmethod
    def generate_legends(state: Dict, width: int, height: int) -> Tuple[List[Dict], Dict[str, List[Dict]]]:
        """
        Generate both legend formats in a single pass over all cells.

        Returns:
            (legend, legend_by_stitch) where:
            - legend: flat list of dicts with color info, stitch type, symbol, count
            - legend_by_stitch: dict mapping stitch category → list of color entries
        """
        palette = state['palette']
        layers = state['layers']

        # Single pass: count usage per (palette_index, stitch_type)
        combo_counts = {}

        for layer in layers:
            if not layer.get('visible', True):
                continue
            if not layer.get('activeForExport', True):
                continue
            if layer['type'] != 'raster':
                continue

            for cell_stitches in layer.get('cells', {}).values():
                stitch_list = cell_stitches if isinstance(cell_stitches, list) else [cell_stitches]
                for cell_data in stitch_list:
                    palette_index = cell_data.get('paletteIndex', 0)
                    stitch_type = cell_data.get('stitchType', 'full')
                    if palette_index < len(palette):
                        key = (palette_index, stitch_type)
                        combo_counts[key] = combo_counts.get(key, 0) + 1

            for path in layer.get('paths', []):
                palette_index = path.get('paletteIndex', 0)
                stitch_type = path.get('stitchType', 'line')
                if palette_index < len(palette):
                    key = (palette_index, stitch_type)
                    combo_counts[key] = combo_counts.get(key, 0) + 1

        # Build both outputs from the same counts
        legend = []
        grouped = {cat: [] for cat in STITCH_CATEGORY_ORDER}

        for (palette_index, stitch_type), count in combo_counts.items():
            if count == 0:
                continue

            color = palette[palette_index]
            symbol = color.get('symbol', '?')
            defn = STITCH_TYPES.get(stitch_type, {})
            category = defn.get('category', 'Full Cross')
            stitch_icon = defn.get('icon', '✕')

            entry = {
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
            }

            legend.append(entry)
            if category in grouped:
                grouped[category].append(entry)

        sort_key = lambda x: (x['vendor'] or '', x['code'] or '')
        legend.sort(key=sort_key)
        for category in grouped:
            grouped[category].sort(key=sort_key)

        # Remove empty categories
        grouped = {k: v for k, v in grouped.items() if v}

        return legend, grouped

    @staticmethod
    def generate_legend(state: Dict, width: int, height: int) -> List[Dict]:
        """Generate flat legend list. Delegates to generate_legends()."""
        legend, _ = PatternRenderer.generate_legends(state, width, height)
        return legend

    @staticmethod
    def generate_legend_by_stitch_type(state: Dict, width: int, height: int) -> Dict[str, List[Dict]]:
        """Generate legend grouped by stitch type. Delegates to generate_legends()."""
        _, grouped = PatternRenderer.generate_legends(state, width, height)
        return grouped

    @staticmethod
    def calculate_pattern_pages(width: int, height: int,
                                page_width: int = 30,
                                page_height: int = 40,
                                overlap: int = 3) -> List[Dict]:
        """
        Calculate page layout for paginated pattern display.

        Each page shows page_width/page_height content stitches plus
        ``overlap`` extra stitches extending past the boundary.  Pages
        step by page_width/page_height so the overlap zone appears on
        both the trailing edge of one page and the leading edge of the
        next (e.g. 0-33, 30-63 with overlap=3, page_width=30).

        Args:
            width: Pattern width in stitches
            height: Pattern height in stitches
            page_width: Content stitches per page horizontally (default 30)
            page_height: Content stitches per page vertically (default 40)
            overlap: Extra stitches beyond each page boundary (default 3)

        Returns:
            List of page definitions with start/end coordinates
        """
        cols = max(1, math.ceil(width / page_width))
        rows = max(1, math.ceil(height / page_height))

        pages = []
        for row in range(rows):
            for col in range(cols):
                x_start = col * page_width
                y_start = row * page_height
                x_end = min(x_start + page_width + overlap, width)
                y_end = min(y_start + page_height + overlap, height)

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
                    'label': f"({x_start}-{x_end - 1}, {y_start}-{y_end - 1})"
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
    def render_stitch_preview(stitch_type: str, rgb_hex: str, symbol: str,
                              size: int = 40) -> np.ndarray:
        """Render a single-cell stitch preview image.

        Produces a small RGB image showing the colored fill polygon, stitch
        paths, and symbol — exactly as seen on the editor canvas.

        Args:
            stitch_type: Stitch type key (e.g. 'full', 'three-quarter-tl')
            rgb_hex: Thread color as hex string (e.g. '#FF0000')
            symbol: Unicode symbol character for this color
            size: Image size in pixels (square)

        Returns:
            RGB numpy array of size×size
        """
        rgb = PatternRenderer._hex_to_rgb_tuple(rgb_hex)
        image = np.full((size, size, 3), 255, dtype=np.uint8)

        # Pass 1: Fill polygon with thread color
        poly = FILL_POLYGONS.get(stitch_type,
                                 [(0, 0), (1, 0), (1, 1), (0, 1)])
        pts = np.array(
            [[int(px * size), int(py * size)] for px, py in poly],
            dtype=np.int32
        )
        cv2.fillPoly(image, [pts], rgb)

        # Pass 2: Draw stitch paths in a contrasting shade
        defn = STITCH_TYPES.get(stitch_type)
        path_data = defn.get('path_data') if defn else None
        if path_data:
            stitch_color = PatternRenderer._get_contrasting_color(rgb)
            thickness = max(1, size // 12)
            PatternRenderer._draw_stitch_paths(
                image, 0, 0, size, stitch_color, path_data, thickness
            )

        # Pass 3: Draw symbol using PIL
        cx, cy, _scale = SYMBOL_PLACEMENTS.get(stitch_type, (0.5, 0.5, 0.8))
        font_size = _symbol_font_size(size, stitch_type)
        font = PatternRenderer._get_symbol_font(font_size)
        symbol_color = PatternRenderer._get_contrasting_color(rgb)

        pil_img = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_img)
        PatternRenderer._draw_symbol_pil(
            draw, font, 0, 0, size, symbol, symbol_color, cx, cy
        )
        image[:] = np.array(pil_img)

        return image

    @staticmethod
    def render_symbol_page(state: Dict, width: int, height: int,
                           x_start: int, y_start: int,
                           x_end: int, y_end: int,
                           cell_size: int = 40,
                           show_color: bool = False,
                           show_stitch: bool = False,
                           show_symbol: bool = True,
                           show_line: bool = True,
                           stamp_cache: dict = None) -> np.ndarray:
        """
        Render a specific region of the pattern with configurable display options.

        Uses per-color symbols from the palette.

        Args:
            state: Project state with layers and palette
            width: Full pattern width
            height: Full pattern height
            x_start: Start X coordinate (0-indexed)
            y_start: Start Y coordinate (0-indexed)
            x_end: End X coordinate (exclusive)
            y_end: End Y coordinate (exclusive)
            cell_size: Size of each cell in pixels
            show_color: Fill cell backgrounds with palette colors
            show_stitch: Draw stitch path shapes in cells
            show_symbol: Draw text symbols in cells
            show_line: Draw linear-mode stitch paths
            stamp_cache: Optional shared dict for pre-rendered symbol stamps.
                         Pass the same dict across multiple calls to avoid
                         redundant PIL text rendering.

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

        # Pass 1: Color backgrounds (before grid)
        if show_color:
            for layer in layers:
                if not layer.get('visible', True):
                    continue
                if not layer.get('activeForExport', True):
                    continue
                if layer['type'] != 'raster':
                    continue

                cells = layer.get('cells', {})

                for cell_key, cell_stitches in cells.items():
                    x, y = cell_key.split(',')
                    x, y = int(x), int(y)

                    if x < x_start or x >= x_end:
                        continue
                    if y < y_start or y >= y_end:
                        continue

                    # Calculate position relative to region
                    rel_x = (x - x_start) * cell_size
                    rel_y = (y - y_start) * cell_size

                    stitch_list = cell_stitches if isinstance(cell_stitches, list) else [cell_stitches]
                    for cell_data in stitch_list:
                        palette_index = cell_data.get('paletteIndex', 0)
                        if palette_index >= len(palette):
                            continue

                        rgb = PatternRenderer._resolve_color(palette[palette_index])

                        # Fill stitch region with color (polygon)
                        stitch_type = cell_data.get('stitchType', 'full')
                        poly = FILL_POLYGONS.get(stitch_type,
                            [(0, 0), (1, 0), (1, 1), (0, 1)])
                        pts = np.array(
                            [[int(rel_x + px * cell_size),
                              int(rel_y + py * cell_size)]
                             for px, py in poly],
                            dtype=np.int32
                        )
                        cv2.fillPoly(image, [pts], rgb)

        # Pass 2: Grid lines (always)
        PatternRenderer._draw_region_grid(
            image, region_width, region_height, cell_size,
            x_start, y_start
        )

        # Pass 3: Stitch shapes (cv2)
        line_thickness = max(1, cell_size // 12)
        stitch_thickness = max(2, line_thickness * 2)

        if show_stitch:
            for layer in layers:
                if not layer.get('visible', True):
                    continue
                if not layer.get('activeForExport', True):
                    continue
                if layer['type'] != 'raster':
                    continue

                for cell_key, cell_stitches in layer.get('cells', {}).items():
                    x, y = cell_key.split(',')
                    x, y = int(x), int(y)

                    if x < x_start or x >= x_end or y < y_start or y >= y_end:
                        continue

                    rel_x = (x - x_start) * cell_size
                    rel_y = (y - y_start) * cell_size

                    stitch_list = cell_stitches if isinstance(cell_stitches, list) else [cell_stitches]
                    for cell_data in stitch_list:
                        palette_index = cell_data.get('paletteIndex', 0)
                        stitch_type = cell_data.get('stitchType', 'full')
                        if palette_index >= len(palette):
                            continue

                        rgb = PatternRenderer._resolve_color(palette[palette_index])

                        defn = STITCH_TYPES.get(stitch_type)
                        path_data = defn.get('path_data') if defn else None

                        stitch_color = PatternRenderer._get_contrasting_color(rgb) if show_color else rgb

                        if path_data:
                            PatternRenderer._draw_stitch_paths(
                                image, rel_x, rel_y,
                                cell_size, stitch_color, path_data, stitch_thickness
                            )
                        else:
                            PatternRenderer._draw_cross_stitch(
                                image, rel_x, rel_y, cell_size, stitch_color
                            )

        # Pass 4: Symbols — pre-render unique stamps, then blit via numpy
        if show_symbol:
            if stamp_cache is None:
                stamp_cache = {}

            for layer in layers:
                if not layer.get('visible', True):
                    continue
                if not layer.get('activeForExport', True):
                    continue
                if layer['type'] != 'raster':
                    continue

                for cell_key, cell_stitches in layer.get('cells', {}).items():
                    x, y = cell_key.split(',')
                    x, y = int(x), int(y)

                    if x < x_start or x >= x_end or y < y_start or y >= y_end:
                        continue

                    rel_x = (x - x_start) * cell_size
                    rel_y = (y - y_start) * cell_size

                    stitch_list = cell_stitches if isinstance(cell_stitches, list) else [cell_stitches]
                    for cell_data in stitch_list:
                        palette_index = cell_data.get('paletteIndex', 0)
                        if palette_index >= len(palette):
                            continue

                        rgb = PatternRenderer._resolve_color(palette[palette_index])

                        symbol = palette[palette_index].get('symbol', '?')
                        symbol_color = PatternRenderer._get_contrasting_color(rgb) if show_color else (0, 0, 0)

                        stitch_type = cell_data.get('stitchType', 'full')
                        cx, cy, _scale = SYMBOL_PLACEMENTS.get(stitch_type, (0.5, 0.5, 0.8))
                        font_size = _symbol_font_size(cell_size, stitch_type)

                        cache_key = (symbol, symbol_color, font_size, stitch_type)
                        if cache_key not in stamp_cache:
                            stamp_cache[cache_key] = PatternRenderer._render_symbol_stamp(
                                symbol, symbol_color, font_size, cell_size, cx, cy
                            )

                        stamp, ox, oy = stamp_cache[cache_key]
                        PatternRenderer._blit_stamp(image, stamp, rel_x + ox, rel_y + oy)

        # Pass 5: Lines (linear-mode stitch paths)
        for layer in layers:
            if not layer.get('visible', True):
                continue
            if not layer.get('activeForExport', True):
                continue
            if layer['type'] != 'raster':
                continue

            if show_line:
                paths = layer.get('paths', [])

                for path in paths:
                    palette_index = path.get('paletteIndex', 0)
                    if palette_index >= len(palette):
                        continue

                    start_x = path.get('startX', 0)
                    start_y = path.get('startY', 0)
                    end_x = path.get('endX', 0)
                    end_y = path.get('endY', 0)

                    # Check if at least one endpoint is within the page region.
                    # Corner coordinates are inclusive (a corner can sit on the boundary).
                    if not ((x_start <= start_x <= x_end and y_start <= start_y <= y_end) or
                            (x_start <= end_x <= x_end and y_start <= end_y <= y_end)):
                        continue

                    path_rgb = PatternRenderer._resolve_color(palette[palette_index])

                    # Calculate pixel coordinates relative to region origin
                    x1 = int((start_x - x_start) * cell_size)
                    y1 = int((start_y - y_start) * cell_size)
                    x2 = int((end_x - x_start) * cell_size)
                    y2 = int((end_y - y_start) * cell_size)

                    cv2.line(image, (x1, y1), (x2, y2), path_rgb, line_thickness,
                             cv2.LINE_AA)

        # Pass 6: Grid numbers
        PatternRenderer._add_region_numbers(
            image, region_width, region_height, cell_size,
            x_start, y_start
        )

        return image

    @staticmethod
    def _draw_region_grid(image: np.ndarray, region_width: int,
                          region_height: int, cell_size: int,
                          x_offset: int, y_offset: int) -> None:
        """Draw grid lines for a pattern region with major lines at configured intervals."""
        img_height, img_width = image.shape[:2]
        major_interval = current_app.config.get('MAJOR_GRID_INTERVAL', 5)

        minor_color = (220, 220, 220)
        major_color = (150, 150, 150)

        # Vertical lines
        for x in range(region_width + 1):
            x_pos = x * cell_size
            global_x = x + x_offset
            color = major_color if global_x % major_interval == 0 else minor_color
            thickness = 2 if global_x % major_interval == 0 else 1
            cv2.line(image, (x_pos, 0), (x_pos, img_height), color, thickness)

        # Horizontal lines
        for y in range(region_height + 1):
            y_pos = y * cell_size
            global_y = y + y_offset
            color = major_color if global_y % major_interval == 0 else minor_color
            thickness = 2 if global_y % major_interval == 0 else 1
            cv2.line(image, (0, y_pos), (img_width, y_pos), color, thickness)

    @staticmethod
    def _add_region_numbers(image: np.ndarray, region_width: int,
                            region_height: int, cell_size: int,
                            x_offset: int, y_offset: int) -> None:
        """Add coordinate numbers on all four sides of a pattern region image."""
        major_interval = current_app.config.get('MAJOR_GRID_INTERVAL', 5)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.3, cell_size / 60)
        thickness = max(1, cell_size // 30)
        color = (100, 100, 100)

        padding_top = max(20, int(cell_size * 0.8))
        padding_left = max(30, int(cell_size * 1.2))
        padding_bottom = padding_top
        padding_right = padding_left

        img_height, img_width = image.shape[:2]
        new_image = np.full(
            (img_height + padding_top + padding_bottom,
             img_width + padding_left + padding_right, 3),
            255,
            dtype=np.uint8
        )

        new_image[padding_top:padding_top + img_height,
                  padding_left:padding_left + img_width] = image

        # Draw X-axis numbers (top and bottom)
        for x in range(region_width + 1):
            global_x = x + x_offset
            if global_x % major_interval == 0:
                x_pos = padding_left + x * cell_size
                text = str(global_x)
                (text_width, text_height), _ = cv2.getTextSize(
                    text, font, font_scale, thickness
                )
                text_x = x_pos - text_width // 2

                # Top
                cv2.putText(new_image, text, (text_x, padding_top - 5), font,
                           font_scale, color, thickness, cv2.LINE_AA)
                # Bottom
                cv2.putText(new_image, text,
                           (text_x, padding_top + img_height + text_height + 5),
                           font, font_scale, color, thickness, cv2.LINE_AA)

        # Draw Y-axis numbers (left and right)
        for y in range(region_height + 1):
            global_y = y + y_offset
            if global_y % major_interval == 0:
                y_pos = padding_top + y * cell_size
                text = str(global_y)
                (text_width, text_height), _ = cv2.getTextSize(
                    text, font, font_scale, thickness
                )
                text_y = y_pos + text_height // 2

                # Left
                cv2.putText(new_image, text,
                           (padding_left - text_width - 5, text_y),
                           font, font_scale, color, thickness, cv2.LINE_AA)
                # Right
                cv2.putText(new_image, text,
                           (padding_left + img_width + 5, text_y),
                           font, font_scale, color, thickness, cv2.LINE_AA)

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
    def render_thumbnail(state: Dict, width: int, height: int,
                         canvas_width: int = 450, canvas_height: int = 250) -> np.ndarray:
        """
        Render pattern with stitches and grid lines, fitted and centered on a
        fixed-size canvas.

        Args:
            state: Project state with layers, palette, and optional clothColor
            width: Grid width in stitches
            height: Grid height in stitches
            canvas_width: Output image width in pixels
            canvas_height: Output image height in pixels

        Returns:
            RGB numpy array of canvas_height x canvas_width
        """
        # Calculate cell size so the pattern fits inside the canvas
        cell_size = max(1, min(canvas_width // width, canvas_height // height))

        # Render the pattern at that cell size (no grid for clean thumbnail)
        pattern = PatternRenderer.render_colored_pattern(
            state, width, height, cell_size
        )

        # Build canvas filled with cloth color
        bg_rgb = PatternRenderer._hex_to_rgb_tuple(
            state.get('clothColor', '#FFFFFF'))
        canvas = np.full((canvas_height, canvas_width, 3), bg_rgb, dtype=np.uint8)

        # Center the pattern on the canvas
        pat_h, pat_w = pattern.shape[:2]
        y_offset = (canvas_height - pat_h) // 2
        x_offset = (canvas_width - pat_w) // 2
        canvas[y_offset:y_offset + pat_h, x_offset:x_offset + pat_w] = pattern

        return canvas

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
