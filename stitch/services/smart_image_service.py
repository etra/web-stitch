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

    # Edge detail presets: (canny_low, canny_high, detail_boost)
    # detail_boost: weight multiplier for high-gradient pixels during majority
    # voting — thin features (whiskers, eye outlines) get more votes so they
    # survive downscaling instead of being averaged away by surrounding pixels.
    EDGE_PRESETS = {
        'low': (80, 200, 2),
        'medium': (50, 150, 4),
        'high': (30, 100, 8),
    }

    # Despeckle presets: number of passes
    DESPECKLE_PRESETS = {
        'off': 0,
        'light': 1,
        'heavy': 3,
    }

    # Sharpness presets: (gaussian_sigma, strength)
    # Applied as unsharp mask before downscaling to preserve edges.
    SHARPNESS_PRESETS = {
        'off': None,
        'low': (1.5, 0.3),
        'medium': (2.5, 0.5),
        'high': (3.5, 0.8),
    }

    @staticmethod
    def convert_image_to_stitches(project: Project, image_file,
                                  max_colors: int,
                                  vendor: ColorVendor | None = None,
                                  backstitch: bool = True,
                                  edge_detail: str = 'medium',
                                  despeckle: str = 'light',
                                  dithering: str = 'off',
                                  sharpness: str = 'medium',
                                  remove_bg: bool = False,
                                  brightness: int = 0,
                                  contrast: int = 0,
                                  saturation: int = 0,
                                  smoothing: int = 50) -> dict:
        """
        Full smart pipeline: load → [remove bg] → preprocess → sharpen → quantize → match → build cells → despeckle → backstitch.

        Args:
            project: Project instance.
            image_file: Werkzeug FileStorage object or Path to an image file.
            max_colors: Maximum colors for quantization.
            vendor: Vendor to match against (defaults to DMC).
            backstitch: Whether to generate backstitch line segments.
            edge_detail: Edge sensitivity preset — 'low', 'medium', or 'high'.
            despeckle: Despeckling strength — 'off', 'light', or 'heavy'.
            dithering: Dithering algorithm — 'off' or 'atkinson'.
            sharpness: Sharpening strength — 'off', 'low', 'medium', or 'high'.
            remove_bg: Whether to remove the image background before conversion.
            brightness: Brightness adjustment (-100 to 100, default 0).
            contrast: Contrast adjustment (-100 to 100, default 0).
            saturation: Saturation adjustment (-100 to 100, default 0).
            smoothing: Smoothing strength (0 to 100, default 50).

        Returns:
            dict with 'layer' and 'newColors' (same shape as LayerImageService).
        """
        import tempfile
        from pathlib import Path
        from stitch.services.image_service import ImageService

        if isinstance(image_file, Path):
            # Read directly from disk
            image = ImageProcessor.load_image(image_file)
        else:
            # Werkzeug FileStorage — save to temp file first
            if not ImageService.allowed_file(image_file.filename):
                raise ValueError('File type not allowed. Use JPG, PNG, or GIF.')

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                image_file.save(tmp.name)
                tmp_path = Path(tmp.name)

            try:
                image = ImageProcessor.load_image(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)

        # Optional background removal — produces RGBA with background transparent
        if remove_bg:
            from stitch.services.background_remover import BackgroundRemover
            image_rgb_for_bg = ImageProcessor.remove_alpha(image)
            image = BackgroundRemover.remove_background(image_rgb_for_bg)

        # Blend transparent areas to white (background or original alpha)
        image_rgb = ImageProcessor.remove_alpha(image)
        grid_w, grid_h = project.width, project.height

        # --- pipeline ---
        preprocessed = SmartImageService._preprocess(
            image_rgb,
            brightness=brightness, contrast=contrast,
            saturation=saturation, smoothing=smoothing,
        )

        # Sharpen before downscaling to preserve edges through the resize
        sharp_params = SmartImageService.SHARPNESS_PRESETS.get(sharpness)
        if sharp_params is not None:
            preprocessed = SmartImageService._sharpen(preprocessed, *sharp_params)

        # Quantize at higher resolution to eliminate interpolation artifacts.
        # Colors are assigned BEFORE any grid-level downscaling, then
        # majority-vote downsampled — each stitch gets the dominant color
        # from its source block rather than a blended average.
        src_h, src_w = preprocessed.shape[:2]
        quant_factor = max(2, min(4, src_w // max(grid_w, 1), src_h // max(grid_h, 1)))
        quant_w = grid_w * quant_factor
        quant_h = grid_h * quant_factor
        image_quant = SmartImageService._progressive_resize(preprocessed, quant_w, quant_h)

        labels_quant, centers_lab, centers_rgb = SmartImageService._quantize_lab(
            image_quant, max_colors
        )
        labels_quant_2d = labels_quant.reshape(quant_h, quant_w)

        if vendor is None:
            vendor = ColorVendor.DMC
        matched, palette_map = SmartImageService._match_vendor_de2000(centers_rgb, vendor)

        # Compute importance map — high-gradient pixels (whiskers, eye outlines,
        # fine details) get higher weight during majority voting so they survive
        # the downscale instead of being averaged away by surrounding pixels.
        edge_preset = SmartImageService.EDGE_PRESETS.get(edge_detail, (50, 150, 4))
        canny_low, canny_high, detail_boost = edge_preset
        importance = SmartImageService._compute_importance(image_quant)
        weights = 1.0 + importance * detail_boost

        # Weighted majority-vote downsample to 1× grid
        labels_1x = SmartImageService._weighted_majority_vote(
            labels_quant_2d, weights, grid_w, grid_h, quant_factor
        )
        # Weighted majority-vote downsample to 2× for edge quadrant detail
        labels_2x = SmartImageService._weighted_majority_vote(
            labels_quant_2d, weights, grid_w * 2, grid_h * 2, quant_factor // 2
        )

        # Edge detection at 4× resolution for finer detail, then downsample
        gray_4x = cv2.cvtColor(image_quant, cv2.COLOR_RGB2GRAY)
        blurred_4x = cv2.GaussianBlur(gray_4x, (5, 5), 1.4)
        edge_mask_4x = cv2.Canny(blurred_4x, threshold1=canny_low, threshold2=canny_high)

        # Downsample edge mask: cell is an edge if ANY pixel in its block is
        edge_mask = (edge_mask_4x.reshape(grid_h, quant_factor, grid_w, quant_factor)
                     .max(axis=(1, 3))).astype(np.uint8)

        # 1× image for white-pixel check and dithering
        image_1x = cv2.resize(image_quant, (grid_w, grid_h), interpolation=cv2.INTER_AREA)

        if dithering == 'atkinson':
            # Dither first for smooth color transitions, then refine edges
            cells = SmartImageService._atkinson_dither(
                image_1x, matched, palette_map, grid_w, grid_h
            )
            SmartImageService._refine_edges(
                cells, edge_mask, labels_2x, palette_map, grid_w, grid_h
            )
        else:
            cells = SmartImageService._build_cells_with_edges(
                image_1x, labels_1x, palette_map, edge_mask, labels_2x,
                grid_w, grid_h
            )

        # Despeckle full-stitch confetti
        despeckle_passes = SmartImageService.DESPECKLE_PRESETS.get(despeckle, 1)
        if despeckle_passes > 0:
            cells = SmartImageService._despeckle(cells, grid_w, grid_h, passes=despeckle_passes)

        # Generate backstitch paths from high-res edge mask for smoother lines
        if backstitch:
            paths = SmartImageService._generate_backstitch_paths(
                edge_mask_4x, labels_1x, palette_map, matched,
                grid_w, grid_h, quant_factor
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
    def _preprocess(image: np.ndarray,
                    brightness: int = 0,
                    contrast: int = 0,
                    saturation: int = 0,
                    smoothing: int = 50) -> np.ndarray:
        """Enhance image: CLAHE + brightness/contrast + bilateral filter + saturation.

        Args:
            image: RGB uint8 array.
            brightness: -100..100 (0 = no change).
            contrast: -100..100 (0 = no change).
            saturation: -100..100 (0 = no change; old default was ~12).
            smoothing: 0..100 (0 = skip, 50 = previous defaults, 100 = heavy).
        """
        # Clamp inputs
        brightness = max(-100, min(100, brightness))
        contrast = max(-100, min(100, contrast))
        saturation = max(-100, min(100, saturation))
        smoothing = max(0, min(100, smoothing))

        # 1. CLAHE on L channel
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        image = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

        # 2. Brightness + contrast adjustment
        #    alpha = 1 + contrast/100  (0.0 .. 2.0)
        #    beta  = brightness * 1.275 (-127.5 .. 127.5)
        if brightness != 0 or contrast != 0:
            alpha = 1.0 + contrast / 100.0
            beta = brightness * 1.275
            image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

        # 3. Bilateral filter — smooth noise, preserve edges
        #    smoothing 0 = skip, 50 = d=9/sigmaColor=50, 100 = d=15/sigmaColor=90
        if smoothing > 0:
            t = smoothing / 100.0
            d = int(5 + t * 10)           # 5..15
            if d % 2 == 0:
                d += 1                     # must be odd or -1
            sigma_color = 20 + t * 70      # 20..90
            sigma_space = 20 + t * 70
            image = cv2.bilateralFilter(image, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)

        # 4. Saturation adjustment
        #    factor = 1 + saturation/100  (0.0 .. 2.0)
        if saturation != 0:
            factor = 1.0 + saturation / 100.0
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
            image = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

        return image

    @staticmethod
    def _sharpen(image: np.ndarray, sigma: float, strength: float) -> np.ndarray:
        """Apply unsharp mask to amplify edges before downscaling.

        Edges that would otherwise be averaged away during extreme
        downscaling (e.g. 800px → 100px) survive because their
        contrast is boosted beforehand.

        Args:
            image: RGB uint8 array.
            sigma: Gaussian blur radius — larger = broader edge halos.
            strength: Boost factor (0.3 = subtle, 0.8 = aggressive).
        """
        blurred = cv2.GaussianBlur(image, (0, 0), sigma)
        # sharpened = image + strength * (image - blurred)
        sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)
        return np.clip(sharpened, 0, 255).astype(np.uint8)

    @staticmethod
    def _progressive_resize(image: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
        """Downscale in ~2× steps to preserve detail, then Lanczos for the final step.

        Single-step extreme downscaling (e.g. 40×) causes significant
        detail loss. Progressive 2× steps let each interpolation pass
        work at a ratio where it performs well.
        """
        h, w = image.shape[:2]
        # Intermediate steps use INTER_AREA (best anti-aliasing for 2× down)
        while w // target_w > 2 or h // target_h > 2:
            new_w = max(w // 2, target_w)
            new_h = max(h // 2, target_h)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            h, w = image.shape[:2]
        # Final step with Lanczos for sharper result at small ratios
        if w != target_w or h != target_h:
            image = cv2.resize(image, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        return image

    @staticmethod
    def _majority_vote(labels_2d: np.ndarray, target_w: int, target_h: int,
                       block_size: int) -> np.ndarray:
        """Downsample cluster labels by picking the most common value per block.

        Instead of interpolating pixel colors (which creates blended
        intermediate colors that don't exist in the palette), this counts
        cluster labels in each block and picks the winner.  The result is
        clean color regions without interpolation artifacts.
        """
        result = np.zeros((target_h, target_w), dtype=np.int32)
        for y in range(target_h):
            sy = y * block_size
            for x in range(target_w):
                sx = x * block_size
                block = labels_2d[sy:sy + block_size, sx:sx + block_size].ravel()
                result[y, x] = np.argmax(np.bincount(block))
        return result

    @staticmethod
    def _weighted_majority_vote(labels_2d, weights_2d, target_w, target_h, block_size):
        """Downsample cluster labels using importance-weighted voting.

        Like _majority_vote, but pixels with high gradient (edges, thin lines)
        count for more.  A whisker pixel with weight 8 effectively counts as
        8 votes against surrounding fur pixels with weight 1, so thin features
        survive the downscale.
        """
        result = np.zeros((target_h, target_w), dtype=np.int32)
        for y in range(target_h):
            sy = y * block_size
            for x in range(target_w):
                sx = x * block_size
                block_labels = labels_2d[sy:sy + block_size, sx:sx + block_size].ravel()
                block_weights = weights_2d[sy:sy + block_size, sx:sx + block_size].ravel()
                counts = np.bincount(block_labels, weights=block_weights)
                result[y, x] = np.argmax(counts)
        return result

    @staticmethod
    def _compute_importance(image):
        """Compute gradient-based importance weights for detail preservation.

        Returns a float32 array (same size as image) where pixels at strong
        color transitions get higher weights.  Flat areas get weight 1.0.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
        # Normalize to 0-1 range
        mag_max = magnitude.max()
        if mag_max > 1e-6:
            magnitude /= mag_max
        return magnitude

    @staticmethod
    def _quantize_lab(image: np.ndarray, max_colors: int):
        """K-means in LAB space, excluding near-white pixels.

        Near-white pixels (R>250, G>250, B>250) are excluded from clustering
        so they don't consume a color slot — these cells are skipped during
        cell building anyway.  All pixels still receive a label afterwards.

        Returns:
            (labels, centers_lab, centers_rgb)
            - labels: (H*W,) int32 cluster assignments
            - centers_lab: (K, 3) float32 LAB centers (OpenCV scale)
            - centers_rgb: list of (R, G, B) int tuples
        """
        lab_image = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        h, w = lab_image.shape[:2]
        all_pixels = lab_image.reshape(-1, 3).astype(np.float32)

        # Mask out near-white pixels (same threshold as cell building)
        rgb_flat = image.reshape(-1, 3)
        keep = ~((rgb_flat[:, 0] > 250) & (rgb_flat[:, 1] > 250) & (rgb_flat[:, 2] > 250))
        fg_pixels = all_pixels[keep]

        # Fallback if not enough foreground pixels
        if len(fg_pixels) < max_colors:
            fg_pixels = all_pixels

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, _, centers_lab = cv2.kmeans(
            fg_pixels, max_colors, None,
            criteria, attempts=5, flags=cv2.KMEANS_PP_CENTERS
        )

        # Assign ALL pixels to nearest center (including white — skipped later).
        # Memory-efficient loop avoids building a large (N, K, 3) array.
        n = len(all_pixels)
        best_dist = np.full(n, np.inf, dtype=np.float32)
        labels = np.zeros(n, dtype=np.int32)
        for i, center in enumerate(centers_lab):
            d = np.sum((all_pixels - center) ** 2, axis=1)
            closer = d < best_dist
            best_dist[closer] = d[closer]
            labels[closer] = i

        # Convert LAB centers → RGB for hex/display
        centers_rgb = []
        for lab_center in centers_lab:
            lab_px = np.uint8([[lab_center.astype(np.uint8)]])
            rgb_px = cv2.cvtColor(lab_px, cv2.COLOR_LAB2RGB)
            r, g, b = int(rgb_px[0, 0, 0]), int(rgb_px[0, 0, 1]), int(rgb_px[0, 0, 2])
            centers_rgb.append((r, g, b))

        return labels, centers_lab, centers_rgb

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
    def _edge_cell_stitches(quadrant_pc_ids):
        """Choose max-2 stitches for an edge cell given its 4 quadrant colors.

        Args:
            quadrant_pc_ids: [tl, tr, bl, br] palette color IDs.

        Returns:
            List of stitch dicts (1 or 2 entries).

        Strategy:
            - All same color → single full stitch.
            - Clean vertical split (TL==BL, TR==BR) → two opposite three-quarters.
            - Clean horizontal split (TL==TR, BL==BR) → two opposite three-quarters.
            - Otherwise → dominant gets three-quarter, secondary gets quarter
              in the first corner where it appears.
        """
        tl, tr, bl, br = quadrant_pc_ids

        # All same → full stitch
        if tl == tr == bl == br:
            return [{'color': tl, 'stitch': 'full'}]

        # Vertical split: left vs right → two opposite three-quarters
        if tl == bl and tr == br and tl != tr:
            return [
                {'color': tl, 'stitch': 'three-quarter-tl'},
                {'color': tr, 'stitch': 'three-quarter-br'},
            ]

        # Horizontal split: top vs bottom → two opposite three-quarters
        if tl == tr and bl == br and tl != bl:
            return [
                {'color': tl, 'stitch': 'three-quarter-tr'},
                {'color': bl, 'stitch': 'three-quarter-bl'},
            ]

        # General case: dominant three-quarter + secondary quarter
        counts = {}
        for pc in quadrant_pc_ids:
            counts[pc] = counts.get(pc, 0) + 1
        dominant = max(counts, key=counts.get)

        # Map corner → opposite three-quarter name
        opposite_tq = {
            'tl': 'three-quarter-br',
            'tr': 'three-quarter-bl',
            'bl': 'three-quarter-tr',
            'br': 'three-quarter-tl',
        }
        corners = ['tl', 'tr', 'bl', 'br']

        # Find first corner with a non-dominant color
        for i, (corner, pc) in enumerate(zip(corners, quadrant_pc_ids)):
            if pc != dominant:
                return [
                    {'color': dominant, 'stitch': opposite_tq[corner]},
                    {'color': pc, 'stitch': f'quarter-{corner}'},
                ]

        # Fallback (shouldn't reach here)
        return [{'color': dominant, 'stitch': 'full'}]

    @staticmethod
    def _build_cells_with_edges(image_1x, labels_1x, palette_map, edge_mask,
                                labels_2x, grid_w, grid_h):
        """Build sparse cells — full stitches for smooth areas, edge cells get max 2 stitches.

        Uses pre-quantized labels (majority-voted) instead of raw pixel colors,
        eliminating interpolation artifacts at color boundaries.
        """
        cells = {}

        for y in range(grid_h):
            for x in range(grid_w):
                cluster_idx = int(labels_1x[y, x])
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
                    # Edge cell: sample 4 quadrants from 2× quantized labels
                    dy, dx = y * 2, x * 2
                    quadrant_labels = [
                        int(labels_2x[dy, dx]),         # top-left
                        int(labels_2x[dy, dx + 1]),     # top-right
                        int(labels_2x[dy + 1, dx]),     # bottom-left
                        int(labels_2x[dy + 1, dx + 1]), # bottom-right
                    ]
                    quadrant_pc_ids = [palette_map.get(cl, pc_id) for cl in quadrant_labels]
                    cells[key] = SmartImageService._edge_cell_stitches(quadrant_pc_ids)

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
    def _refine_edges(cells, edge_mask, labels_2x, palette_map, grid_w, grid_h):
        """Replace dithered full stitches at edge cells with three-quarter + quarter from 2× labels.

        Uses pre-quantized labels instead of raw pixel matching for cleaner
        and faster edge detail.  Produces max 2 stitches per cell.
        """
        for y in range(grid_h):
            for x in range(grid_w):
                if edge_mask[y, x] == 0:
                    continue
                key = f"{x},{y}"
                if key not in cells:
                    continue

                # Sample 4 quadrants from 2× quantized labels
                dy, dx = y * 2, x * 2
                quadrant_labels = [
                    int(labels_2x[dy, dx]),
                    int(labels_2x[dy, dx + 1]),
                    int(labels_2x[dy + 1, dx]),
                    int(labels_2x[dy + 1, dx + 1]),
                ]
                quadrant_pc_ids = [palette_map.get(cl) for cl in quadrant_labels]

                # Only replace if all quadrants resolved and have different colors
                if None in quadrant_pc_ids:
                    continue
                if len(set(quadrant_pc_ids)) > 1:
                    cells[key] = SmartImageService._edge_cell_stitches(quadrant_pc_ids)

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
    def _generate_backstitch_paths(edge_mask_hires, labels_1x, palette_map,
                                   matched, grid_w, grid_h, scale=1):
        """Generate backstitch line segments from edge contours.

        Args:
            edge_mask_hires: Edge mask, possibly at higher resolution than grid.
            labels_1x: (grid_h, grid_w) cluster label array at grid resolution.
            palette_map: Cluster index → palette color ID mapping.
            matched: List of (Color, pc_uuid, symbol) tuples.
            grid_w, grid_h: Grid dimensions.
            scale: Ratio of edge mask resolution to grid resolution (e.g. 4 for 4×).
        """
        contours, _ = cv2.findContours(edge_mask_hires, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        # Build color lookup: pc_id → Color object (for L comparison)
        color_by_pc_id = {}
        for color_obj, pc_id, _symbol in matched:
            color_by_pc_id[pc_id] = color_obj

        labels_2d = labels_1x
        paths = []

        # Simplification epsilon scales with resolution
        epsilon = max(1.0, scale * 0.5)
        # Min segment length in grid units
        min_seg_grid = 1.5

        for contour in contours:
            if len(contour) < 3:
                continue

            # Simplify contour at high-res, then scale points to grid coords
            simplified = cv2.approxPolyDP(contour, epsilon=epsilon, closed=False)
            points = simplified.reshape(-1, 2).astype(np.float64) / scale

            for i in range(len(points) - 1):
                x1, y1 = points[i][0], points[i][1]
                x2, y2 = points[i + 1][0], points[i + 1][1]

                # Skip short segments (in grid units)
                seg_len = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                if seg_len < min_seg_grid:
                    continue

                # Snap to nearest grid corner (integer coordinates)
                x1, y1 = round(x1), round(y1)
                x2, y2 = round(x2), round(y2)

                # Sample midpoint for color (in grid-cell space)
                mx = max(0, min(grid_w - 1, (x1 + x2) // 2))
                my = max(0, min(grid_h - 1, (y1 + y2) // 2))
                cluster_idx = int(labels_2d[my, mx])
                pc_id = palette_map.get(cluster_idx)
                if not pc_id:
                    continue

                # Pick the darker of neighboring colors (cross-stitch convention)
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
