"""Smart image conversion service — professional-grade image-to-stitch pipeline.

Applies CLAHE enhancement, bilateral filtering, LAB-space quantization,
Delta E 2000 vendor matching, edge-aware quarter stitches, despeckling,
and backstitch line generation.
"""
import uuid

import cv2
import numpy as np

from stitch.models.color import Color, ColorVendor
from stitch.models.project import Project
from stitch.services.color_matcher import ColorMatcher
from stitch.services.image_processor import ImageProcessor
from stitch.services.project_service import ProjectService


class SmartImageService:
    """Convert an image into a high-quality cross-stitch layer."""

    # Edge detail presets: (canny_low, canny_high)
    EDGE_PRESETS = {
        'low': (80, 200),
        'medium': (50, 150),
        'high': (30, 100),
    }

    # Despeckle presets: number of passes
    DESPECKLE_PRESETS = {
        'off': 0,
        'light': 1,
        'heavy': 3,
    }

    @staticmethod
    def convert_image_to_stitches(project: Project, image_file,
                                  max_colors: int,
                                  vendor: ColorVendor | None = None,
                                  backstitch: bool = True,
                                  edge_detail: str = 'medium',
                                  despeckle: str = 'light',
                                  dithering: str = 'off') -> dict:
        """
        Full smart pipeline: load → preprocess → quantize → match → build cells → despeckle → backstitch.

        Args:
            project: Project instance.
            image_file: Werkzeug FileStorage object.
            max_colors: Maximum colors for quantization.
            vendor: Vendor to match against (defaults to DMC).
            backstitch: Whether to generate backstitch line segments.
            edge_detail: Edge sensitivity preset — 'low', 'medium', or 'high'.
            despeckle: Despeckling strength — 'off', 'light', or 'heavy'.
            dithering: Dithering algorithm — 'off' or 'atkinson'.

        Returns:
            dict with 'layer' and 'newColors' (same shape as LayerImageService).
        """
        import tempfile
        from pathlib import Path
        from stitch.services.image_service import ImageService

        if not ImageService.allowed_file(image_file.filename):
            raise ValueError('File type not allowed. Use JPG, PNG, or GIF.')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            image_file.save(tmp.name)
            tmp_path = Path(tmp.name)

        try:
            image = ImageProcessor.load_image(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

        image_rgb = ImageProcessor.remove_alpha(image)
        grid_w, grid_h = project.width, project.height

        # --- pipeline ---
        preprocessed = SmartImageService._preprocess(image_rgb)

        # 1x grid image for quantization and edge detection
        image_1x = cv2.resize(preprocessed, (grid_w, grid_h), interpolation=cv2.INTER_AREA)

        labels, centers_lab, centers_rgb = SmartImageService._quantize_lab(image_1x, max_colors)

        if vendor is None:
            vendor = ColorVendor.DMC
        matched, palette_map = SmartImageService._match_vendor_de2000(centers_rgb, vendor)

        # 2x detail image for sub-cell sampling
        detail_image = cv2.resize(preprocessed, (grid_w * 2, grid_h * 2), interpolation=cv2.INTER_AREA)

        # Edge detection on 1x image
        canny_low, canny_high = SmartImageService.EDGE_PRESETS.get(edge_detail, (50, 150))
        gray_1x = cv2.cvtColor(image_1x, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray_1x, (5, 5), 1.4)
        edge_mask = cv2.Canny(blurred, threshold1=canny_low, threshold2=canny_high)

        if dithering == 'atkinson':
            # Dither first for smooth color transitions, then refine edges
            cells = SmartImageService._atkinson_dither(
                image_1x, matched, palette_map, grid_w, grid_h
            )
            SmartImageService._refine_edges(
                cells, edge_mask, detail_image, matched, grid_w, grid_h
            )
        else:
            cells = SmartImageService._build_cells_with_edges(
                image_1x, labels, palette_map, edge_mask, detail_image,
                matched, grid_w, grid_h
            )

        # Despeckle full-stitch confetti
        despeckle_passes = SmartImageService.DESPECKLE_PRESETS.get(despeckle, 1)
        if despeckle_passes > 0:
            cells = SmartImageService._despeckle(cells, grid_w, grid_h, passes=despeckle_passes)

        # Generate backstitch paths from edges
        if backstitch:
            paths = SmartImageService._generate_backstitch_paths(
                edge_mask, image_1x, labels, palette_map, matched, grid_w, grid_h
            )
        else:
            paths = []

        # Build layer
        layer_id = str(uuid.uuid4())
        layer_data = {
            'id': layer_id,
            'type': 'raster',
            'name': 'Smart Image',
            'visible': True,
            'activeForExport': True,
            'editable': True,
            'opacity': None,
            'referenceImageData': None,
            'sortOrder': 0,
            'cells': cells,
            'paths': paths,
        }

        # Build newColors list
        new_colors = []
        for color_obj, pc_id, symbol in matched:
            new_colors.append({
                'id': pc_id,
                'colorId': color_obj.id,
                'symbol': symbol,
                'name': color_obj.name,
                'rgbHex': color_obj.hex,
                'vendor': color_obj.vendor.value,
                'code': color_obj.code,
            })

        return {
            'layer': layer_data,
            'newColors': new_colors,
        }

    # ── Private pipeline stages ──────────────────────────────────

    @staticmethod
    def _preprocess(image: np.ndarray) -> np.ndarray:
        """Enhance image: CLAHE + bilateral filter + saturation boost."""
        # 1. CLAHE on L channel
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        image = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

        # 2. Bilateral filter — smooth noise, preserve edges
        # bilateralFilter works on BGR/RGB uint8 natively
        image = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)

        # 3. Saturation boost (12%)
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.12, 0, 255)
        image = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

        return image

    @staticmethod
    def _quantize_lab(image: np.ndarray, max_colors: int):
        """K-means in LAB space.

        Returns:
            (labels, centers_lab, centers_rgb)
            - labels: (H*W,) int32 cluster assignments
            - centers_lab: (K, 3) float32 LAB centers (OpenCV scale)
            - centers_rgb: list of (R, G, B) int tuples
        """
        lab_image = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        h, w = lab_image.shape[:2]
        pixels = lab_image.reshape(-1, 3).astype(np.float32)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers_lab = cv2.kmeans(
            pixels, max_colors, None,
            criteria, attempts=5, flags=cv2.KMEANS_PP_CENTERS
        )

        # Convert LAB centers → RGB for hex/display
        centers_rgb = []
        for lab_center in centers_lab:
            lab_px = np.uint8([[lab_center.astype(np.uint8)]])
            rgb_px = cv2.cvtColor(lab_px, cv2.COLOR_LAB2RGB)
            r, g, b = int(rgb_px[0, 0, 0]), int(rgb_px[0, 0, 1]), int(rgb_px[0, 0, 2])
            centers_rgb.append((r, g, b))

        return labels.flatten(), centers_lab, centers_rgb

    @staticmethod
    def _match_vendor_de2000(centers_rgb, vendor: ColorVendor):
        """Match each quantized center to nearest vendor color via Delta E 2000.

        Returns:
            (matched, palette_map)
            - matched: list of (Color, pc_uuid, symbol) — one per unique vendor color
            - palette_map: dict mapping cluster_index → pc_uuid
        """
        vendor_colors = Color.query.filter_by(vendor=vendor).all()
        if not vendor_colors:
            raise ValueError(f'No colors found for vendor {vendor.value}.')

        # Pre-compute LAB for all vendor colors (cache for batch performance)
        vendor_lab_cache = {}

        matched_by_color_id = {}  # Color.id → (Color, pc_uuid, symbol)
        palette_map = {}  # cluster index → pc_uuid
        symbol_idx = 0

        for idx, rgb in enumerate(centers_rgb):
            nearest, _ = ColorMatcher.find_nearest_color_de2000(
                rgb, vendor_colors, vendor_lab_cache
            )

            if nearest.id not in matched_by_color_id:
                pc_id = str(uuid.uuid4())
                symbol = ProjectService._generate_symbol(symbol_idx)
                matched_by_color_id[nearest.id] = (nearest, pc_id, symbol)
                symbol_idx += 1

            _, pc_id, _ = matched_by_color_id[nearest.id]
            palette_map[idx] = pc_id

        matched = list(matched_by_color_id.values())
        return matched, palette_map

    @staticmethod
    def _build_cells_with_edges(image_1x, labels, palette_map, edge_mask,
                                detail_image, matched, grid_w, grid_h):
        """Build sparse cells — full stitches for smooth areas, quarter stitches at edges."""
        labels_2d = labels.reshape(grid_h, grid_w)

        # Pre-build a lookup: pc_uuid → matched-list index (for nearest-color on detail pixels)
        # Also build vendor_rgb → pc_id for detail matching
        vendor_colors = []
        vendor_lab_cache = {}
        pc_id_by_color_id = {}
        for color_obj, pc_id, _symbol in matched:
            vendor_colors.append(color_obj)
            pc_id_by_color_id[color_obj.id] = pc_id

        cells = {}

        for y in range(grid_h):
            for x in range(grid_w):
                cluster_idx = int(labels_2d[y, x])
                pc_id = palette_map.get(cluster_idx)
                if not pc_id:
                    continue

                # Check near-white in 1x image
                r, g, b = int(image_1x[y, x, 0]), int(image_1x[y, x, 1]), int(image_1x[y, x, 2])
                if r > 250 and g > 250 and b > 250:
                    continue

                key = f"{x},{y}"

                if edge_mask[y, x] == 0:
                    # Non-edge: single full stitch
                    cells[key] = [{'color': pc_id, 'stitch': 'full'}]
                else:
                    # Edge cell: sample 4 quadrants from 2x detail image
                    dy, dx = y * 2, x * 2
                    quadrant_pixels = [
                        detail_image[dy, dx],         # top-left
                        detail_image[dy, dx + 1],     # top-right
                        detail_image[dy + 1, dx],     # bottom-left
                        detail_image[dy + 1, dx + 1], # bottom-right
                    ]

                    quadrant_pc_ids = []
                    for px in quadrant_pixels:
                        px_rgb = (int(px[0]), int(px[1]), int(px[2]))
                        nearest, _ = ColorMatcher.find_nearest_color_de2000(
                            px_rgb, vendor_colors, vendor_lab_cache
                        )
                        quadrant_pc_ids.append(pc_id_by_color_id[nearest.id])

                    # Check if all 4 quadrants are the same color
                    if len(set(quadrant_pc_ids)) == 1:
                        cells[key] = [{'color': quadrant_pc_ids[0], 'stitch': 'full'}]
                    else:
                        quarter_names = ['quarter-tl', 'quarter-tr', 'quarter-bl', 'quarter-br']
                        stitches = []
                        for qname, qpc in zip(quarter_names, quadrant_pc_ids):
                            stitches.append({'color': qpc, 'stitch': qname})
                        cells[key] = stitches

        return cells

    @staticmethod
    def _atkinson_dither(image_1x, matched, palette_map, grid_w, grid_h):
        """Apply Atkinson error-diffusion dithering.

        For each pixel: find nearest vendor color using vectorized redmean
        distance, compute error, distribute 1/8 of error to 6 Atkinson
        neighbors.  Returns cells dict with all full stitches.
        """
        # Build vendor RGB array (N, 3) and pc_id list for index lookup
        pc_ids = []
        vendor_list = []
        for color_obj, pc_id, _symbol in matched:
            vendor_list.append(ColorMatcher.hex_to_rgb(color_obj.hex))
            pc_ids.append(pc_id)
        vendor_arr = np.array(vendor_list, dtype=np.float64)  # (N, 3)

        img = image_1x.astype(np.float64)
        cells = {}

        for y in range(grid_h):
            for x in range(grid_w):
                r = max(0.0, min(255.0, img[y, x, 0]))
                g = max(0.0, min(255.0, img[y, x, 1]))
                b = max(0.0, min(255.0, img[y, x, 2]))

                if r > 250 and g > 250 and b > 250:
                    continue

                # Vectorized redmean distance against all vendor colors
                dr = r - vendor_arr[:, 0]
                dg = g - vendor_arr[:, 1]
                db = b - vendor_arr[:, 2]
                rmean = (r + vendor_arr[:, 0]) * 0.5
                dists = (2 + rmean / 256) * dr * dr + 4 * dg * dg + (2 + (255 - rmean) / 256) * db * db
                best_idx = int(np.argmin(dists))

                mr, mg, mb = vendor_arr[best_idx]

                # Distribute error/8 to 6 Atkinson neighbors (total 6/8 = 75%)
                err_r = (r - mr) * 0.125
                err_g = (g - mg) * 0.125
                err_b = (b - mb) * 0.125
                if x + 1 < grid_w:
                    img[y, x + 1, 0] += err_r
                    img[y, x + 1, 1] += err_g
                    img[y, x + 1, 2] += err_b
                if x + 2 < grid_w:
                    img[y, x + 2, 0] += err_r
                    img[y, x + 2, 1] += err_g
                    img[y, x + 2, 2] += err_b
                if y + 1 < grid_h:
                    if x - 1 >= 0:
                        img[y + 1, x - 1, 0] += err_r
                        img[y + 1, x - 1, 1] += err_g
                        img[y + 1, x - 1, 2] += err_b
                    img[y + 1, x, 0] += err_r
                    img[y + 1, x, 1] += err_g
                    img[y + 1, x, 2] += err_b
                    if x + 1 < grid_w:
                        img[y + 1, x + 1, 0] += err_r
                        img[y + 1, x + 1, 1] += err_g
                        img[y + 1, x + 1, 2] += err_b
                if y + 2 < grid_h:
                    img[y + 2, x, 0] += err_r
                    img[y + 2, x, 1] += err_g
                    img[y + 2, x, 2] += err_b

                cells[f"{x},{y}"] = [{'color': pc_ids[best_idx], 'stitch': 'full'}]

        return cells

    @staticmethod
    def _refine_edges(cells, edge_mask, detail_image, matched, grid_w, grid_h):
        """Replace dithered full stitches at edge cells with quarter stitches from 2x detail.

        Uses vectorized redmean distance for fast per-quadrant color matching.
        """
        pc_ids = []
        vendor_list = []
        for color_obj, pc_id, _symbol in matched:
            vendor_list.append(ColorMatcher.hex_to_rgb(color_obj.hex))
            pc_ids.append(pc_id)
        vendor_arr = np.array(vendor_list, dtype=np.float64)  # (N, 3)

        quarter_names = ['quarter-tl', 'quarter-tr', 'quarter-bl', 'quarter-br']

        for y in range(grid_h):
            for x in range(grid_w):
                if edge_mask[y, x] == 0:
                    continue
                key = f"{x},{y}"
                if key not in cells:
                    continue

                # Sample 4 quadrants from 2x detail image
                dy, dx = y * 2, x * 2
                quads = detail_image[dy:dy + 2, dx:dx + 2].reshape(4, 3).astype(np.float64)

                # Vectorized redmean: (4, N) distances
                dr = quads[:, 0:1] - vendor_arr[:, 0]  # (4, N)
                dg = quads[:, 1:2] - vendor_arr[:, 1]
                db = quads[:, 2:3] - vendor_arr[:, 2]
                rmean = (quads[:, 0:1] + vendor_arr[:, 0]) * 0.5
                dists = (2 + rmean / 256) * dr * dr + 4 * dg * dg + (2 + (255 - rmean) / 256) * db * db
                best_indices = np.argmin(dists, axis=1)

                quadrant_pc_ids = [pc_ids[i] for i in best_indices]

                if len(set(quadrant_pc_ids)) > 1:
                    stitches = [{'color': qpc, 'stitch': qname}
                                for qname, qpc in zip(quarter_names, quadrant_pc_ids)]
                    cells[key] = stitches

    @staticmethod
    def _despeckle(cells, grid_w, grid_h, passes=2):
        """Remove confetti: isolated full stitches surrounded by different colors."""
        for _pass in range(passes):
            changes = {}
            for key, stitches in cells.items():
                # Only despeckle single full stitches
                if len(stitches) != 1 or stitches[0]['stitch'] != 'full':
                    continue

                x, y = (int(v) for v in key.split(','))
                own_color = stitches[0]['color']

                # Count neighbor colors in 3x3 neighborhood
                neighbor_counts = {}
                for ny in range(max(0, y - 1), min(grid_h, y + 2)):
                    for nx in range(max(0, x - 1), min(grid_w, x + 2)):
                        if nx == x and ny == y:
                            continue
                        nkey = f"{nx},{ny}"
                        nstitches = cells.get(nkey)
                        if not nstitches:
                            continue
                        for ns in nstitches:
                            if ns['stitch'] == 'full':
                                c = ns['color']
                                neighbor_counts[c] = neighbor_counts.get(c, 0) + 1

                if not neighbor_counts:
                    continue

                own_neighbor_count = neighbor_counts.get(own_color, 0)
                if own_neighbor_count <= 1:
                    # Confetti — replace with most frequent neighbor
                    most_common = max(neighbor_counts, key=neighbor_counts.get)
                    changes[key] = most_common

            for key, new_color in changes.items():
                cells[key] = [{'color': new_color, 'stitch': 'full'}]

        return cells

    @staticmethod
    def _generate_backstitch_paths(edge_mask, image_1x, labels, palette_map,
                                   matched, grid_w, grid_h):
        """Generate backstitch line segments from edge contours."""
        contours, _ = cv2.findContours(edge_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        # Build color lookup: pc_id → Color object (for L comparison)
        color_by_pc_id = {}
        for color_obj, pc_id, _symbol in matched:
            color_by_pc_id[pc_id] = color_obj

        labels_2d = labels.reshape(grid_h, grid_w)
        paths = []

        for contour in contours:
            if len(contour) < 3:
                continue

            # Simplify contour
            simplified = cv2.approxPolyDP(contour, epsilon=1.0, closed=False)
            points = simplified.reshape(-1, 2)

            for i in range(len(points) - 1):
                x1, y1 = int(points[i][0]), int(points[i][1])
                x2, y2 = int(points[i + 1][0]), int(points[i + 1][1])

                # Skip short segments
                seg_len = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                if seg_len < 2:
                    continue

                # Sample midpoint for color
                mx = max(0, min(grid_w - 1, (x1 + x2) // 2))
                my = max(0, min(grid_h - 1, (y1 + y2) // 2))
                cluster_idx = int(labels_2d[my, mx])
                pc_id = palette_map.get(cluster_idx)
                if not pc_id:
                    continue

                # Pick the darker of neighboring colors (cross-stitch convention)
                # Check if adjacent cells have a different color; if so, use the darker one
                best_pc_id = pc_id
                best_L = float('inf')

                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        ny, nx = my + dy, mx + dx
                        if 0 <= ny < grid_h and 0 <= nx < grid_w:
                            ci = int(labels_2d[ny, nx])
                            neighbor_pc = palette_map.get(ci)
                            if neighbor_pc and neighbor_pc in color_by_pc_id:
                                c = color_by_pc_id[neighbor_pc]
                                lab = ColorMatcher.rgb_to_standard_lab(
                                    ColorMatcher.hex_to_rgb(c.hex)
                                )
                                if lab[0] < best_L:
                                    best_L = lab[0]
                                    best_pc_id = neighbor_pc

                # Clamp endpoints to valid corner range (0..W, 0..H inclusive)
                x1 = max(0, min(grid_w, x1))
                y1 = max(0, min(grid_h, y1))
                x2 = max(0, min(grid_w, x2))
                y2 = max(0, min(grid_h, y2))

                paths.append({
                    'startX': x1,
                    'startY': y1,
                    'endX': x2,
                    'endY': y2,
                    'color': best_pc_id,
                    'stitch': 'line',
                })

        return paths
