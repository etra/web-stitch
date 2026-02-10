"""Service for image-based layer operations: upload reference images, convert images to stitches."""
import uuid
import tempfile
from pathlib import Path

from flask import current_app

from stitch.models.color import Color, ColorVendor
from stitch.models.project import Project
from stitch.models.project_color import ProjectColor
from stitch.models.project_layer import ProjectLayer
from stitch.services.color_matcher import ColorMatcher
from stitch.services.image_processor import ImageProcessor
from stitch.services.image_service import ImageService


class LayerImageService:
    """Business logic for image-based layer creation and conversion."""

    @staticmethod
    def upload_reference_image(project: Project, image_file, name: str,
                               target_width: int, target_height: int) -> dict:
        """
        Upload an image as a reference layer.

        Validates, resizes to grid, stores on disk, and returns URL + dimensions.
        No DB writes -- the frontend incorporates the result and saves later.

        Args:
            project: Project instance.
            image_file: Werkzeug FileStorage object.
            name: Layer name.
            target_width: Target grid width in cells.
            target_height: Target grid height in cells.

        Returns:
            dict with imageUrl, originalWidth, originalHeight.

        Raises:
            ValueError: If file type is not allowed or image cannot be loaded.
        """
        if not ImageService.allowed_file(image_file.filename):
            raise ValueError('File type not allowed. Use JPG, PNG, or GIF.')

        # Save to temp file so ImageProcessor can load it
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            image_file.save(tmp.name)
            tmp_path = Path(tmp.name)

        try:
            image = ImageProcessor.load_image(tmp_path)
            original_height, original_width = image.shape[:2]

            image_rgb = ImageProcessor.remove_alpha(image)
            resized = ImageProcessor.resize_to_grid(image_rgb, target_width, target_height)

            # Save to project references directory
            image_uuid = uuid.uuid4().hex
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            ref_dir = Path(upload_folder) / 'projects' / str(project.id) / 'references'
            ref_dir.mkdir(parents=True, exist_ok=True)
            output_path = ref_dir / f'{image_uuid}.png'

            ImageProcessor.save_processed_image(resized, output_path)
        finally:
            tmp_path.unlink(missing_ok=True)

        image_url = f'/projects/{project.id}/reference-images/{image_uuid}'

        return {
            'imageUrl': image_url,
            'originalWidth': original_width,
            'originalHeight': original_height,
        }

    @staticmethod
    def convert_image_to_stitches(project: Project, image_file, name: str,
                                  max_colors: int, use_existing_colors_only: bool,
                                  target_width: int, target_height: int) -> dict:
        """
        Upload an image and convert it to a stitch layer.

        Processes image in memory, matches colors to palette, returns layer data
        and any new colors. No DB writes.

        Args:
            project: Project instance.
            image_file: Werkzeug FileStorage object.
            name: Layer name.
            max_colors: Maximum colors for quantization.
            use_existing_colors_only: If True, only use project's existing colors.
            target_width: Target grid width in cells.
            target_height: Target grid height in cells.

        Returns:
            dict with layer (LayerResponse-shaped) and newColors list.

        Raises:
            ValueError: If file type is not allowed or image cannot be loaded.
        """
        if not ImageService.allowed_file(image_file.filename):
            raise ValueError('File type not allowed. Use JPG, PNG, or GIF.')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            image_file.save(tmp.name)
            tmp_path = Path(tmp.name)

        try:
            image = ImageProcessor.load_image(tmp_path)
            image_rgb = ImageProcessor.remove_alpha(image)
            resized = ImageProcessor.resize_to_grid(image_rgb, target_width, target_height)
        finally:
            tmp_path.unlink(missing_ok=True)

        return LayerImageService._process_image_to_stitches(
            project, resized, name, max_colors, use_existing_colors_only, target_width
        )

    @staticmethod
    def convert_reference_to_stitches(project: Project, layer_id: str,
                                      max_colors: int,
                                      use_existing_colors_only: bool) -> dict:
        """
        Convert an existing reference layer's stored image to stitches.

        Loads the image from the ProjectLayerImage base64 data, then processes it.
        No DB writes.

        Args:
            project: Project instance.
            layer_id: ID of the reference layer to convert.
            max_colors: Maximum colors for quantization.
            use_existing_colors_only: If True, only use project's existing colors.

        Returns:
            dict with layer (LayerResponse-shaped) and newColors list.

        Raises:
            ValueError: If layer not found, wrong type, or missing image data.
        """
        from stitch.models.project_layer_image import ProjectLayerImage

        layer = ProjectLayer.query.get(layer_id)
        if not layer:
            raise ValueError('Layer not found.')
        if layer.project_id != project.id:
            raise ValueError('Layer does not belong to this project.')
        if layer.layer_type != 'reference':
            raise ValueError('Layer is not a reference layer.')

        layer_image = ProjectLayerImage.query.get(layer_id)
        if not layer_image or not layer_image.data:
            raise ValueError('Reference layer has no stored image data.')

        image = ImageProcessor.load_image_from_data_uri(layer_image.data)
        image = ImageProcessor.remove_alpha(image)
        height, width = image.shape[:2]

        result = LayerImageService._process_image_to_stitches(
            project, image, f'{layer.name} (stitches)', max_colors,
            use_existing_colors_only, width
        )

        # Reuse the reference layer's ID so the frontend replaces it in place
        result['layer']['id'] = layer.id

        return result

    @staticmethod
    def _process_image_to_stitches(project: Project, image, name: str,
                                   max_colors: int, use_existing_colors_only: bool,
                                   grid_width: int) -> dict:
        """
        Shared logic for converting a resized image array to stitch layer data.

        Args:
            project: Project instance.
            image: RGB numpy array already sized to the grid.
            name: Layer name.
            max_colors: Maximum colors for quantization.
            use_existing_colors_only: If True, only use project's existing colors.
            grid_width: Grid width for cell key calculation.

        Returns:
            dict with 'layer' and 'newColors'.
        """
        import numpy as np

        # Cap max_colors to available palette slots when adding new colors
        if not use_existing_colors_only:
            max_palette = current_app.config.get('MAX_PALETTE_COLORS', 32)
            existing_count = ProjectColor.query.filter_by(project_id=project.id).count()
            available = max_palette - existing_count
            if available <= 0:
                raise ValueError(
                    f"Palette is full ({existing_count}/{max_palette} colors). "
                    f"Remove colors or use existing colors only."
                )
            max_colors = min(max_colors, available)

        # Quantize
        quantized, raw_palette = ImageProcessor.quantize_colors(image, max_colors)
        height = quantized.shape[0]

        if use_existing_colors_only:
            return LayerImageService._match_existing_colors(
                project, quantized, raw_palette, name, grid_width, height
            )
        else:
            return LayerImageService._match_vendor_colors(
                project, quantized, raw_palette, name, grid_width, height
            )

    @staticmethod
    def _match_existing_colors(project, quantized, raw_palette, name,
                               grid_width, grid_height):
        """Map quantized colors to the project's existing palette colors."""
        import numpy as np

        project_colors = ProjectColor.query.filter_by(project_id=project.id).all()
        if not project_colors:
            raise ValueError('Project has no existing colors to match against.')

        # Build list of Color objects for matching
        existing_colors = []
        pc_by_color_id = {}
        for pc in project_colors:
            color = Color.query.get(pc.color_id)
            if color:
                existing_colors.append(color)
                pc_by_color_id[color.id] = pc

        # Map each quantized color to nearest existing ProjectColor
        quantized_to_pc = {}  # raw_palette index -> ProjectColor id
        for idx, q_color in enumerate(raw_palette):
            rgb = ColorMatcher.hex_to_rgb(q_color['rgbHex'])
            nearest_color, _ = ColorMatcher.find_nearest_palette_color(rgb, existing_colors)
            pc = pc_by_color_id[nearest_color.id]
            quantized_to_pc[idx] = pc.id

        # Build sparse cells
        cells = LayerImageService._build_cells(
            quantized, raw_palette, quantized_to_pc, grid_width
        )

        layer_id = str(uuid.uuid4())
        layer_data = {
            'id': layer_id,
            'type': 'raster',
            'name': name,
            'visible': True,
            'activeForExport': True,
            'editable': True,
            'opacity': None,
            'referenceImageData': None,
            'sortOrder': 0,
            'cells': cells,
            'paths': [],
        }

        return {
            'layer': layer_data,
            'newColors': [],
        }

    @staticmethod
    def _match_vendor_colors(project, quantized, raw_palette, name,
                             grid_width, grid_height):
        """Map quantized colors to vendor palette, generating new ProjectColor entries."""
        import numpy as np

        # Determine vendor from project's existing colors
        vendor = LayerImageService._determine_vendor(project)

        vendor_colors = Color.query.filter_by(vendor=vendor).all()
        if not vendor_colors:
            raise ValueError(f'No colors found for vendor {vendor.value}.')

        # Match each quantized color to nearest vendor color
        # Track unique matches to avoid duplicate new colors
        matched = {}  # Color.id -> (Color, new_pc_uuid, symbol)
        quantized_to_pc = {}  # raw_palette index -> new ProjectColor UUID
        symbol_idx = 0

        for idx, q_color in enumerate(raw_palette):
            rgb = ColorMatcher.hex_to_rgb(q_color['rgbHex'])
            nearest_color, _ = ColorMatcher.find_nearest_palette_color(rgb, vendor_colors)

            if nearest_color.id not in matched:
                new_pc_id = str(uuid.uuid4())
                symbol = ImageProcessor._get_symbol(symbol_idx)
                matched[nearest_color.id] = (nearest_color, new_pc_id, symbol)
                symbol_idx += 1

            _, new_pc_id, _ = matched[nearest_color.id]
            quantized_to_pc[idx] = new_pc_id

        # Build sparse cells
        cells = LayerImageService._build_cells(
            quantized, raw_palette, quantized_to_pc, grid_width
        )

        # Build newColors list
        new_colors = []
        for color, new_pc_id, symbol in matched.values():
            new_colors.append({
                'id': new_pc_id,
                'colorId': color.id,
                'symbol': symbol,
                'name': color.name,
                'rgbHex': color.hex,
                'vendor': color.vendor.value,
                'code': color.code,
            })

        layer_id = str(uuid.uuid4())
        layer_data = {
            'id': layer_id,
            'type': 'raster',
            'name': name,
            'visible': True,
            'activeForExport': True,
            'editable': True,
            'opacity': None,
            'referenceImageData': None,
            'sortOrder': 0,
            'cells': cells,
            'paths': [],
        }

        return {
            'layer': layer_data,
            'newColors': new_colors,
        }

    @staticmethod
    def _build_cells(quantized, raw_palette, quantized_to_pc, grid_width):
        """
        Build sparse cells dict from quantized image.

        Args:
            quantized: Quantized image array (H, W, 3).
            raw_palette: List of palette dicts from quantization (with 'rgb'/'rgbHex').
            quantized_to_pc: Mapping from raw_palette index to ProjectColor UUID.
            grid_width: Grid width for cell key calculation.

        Returns:
            dict of {str(key): {color: uuid, stitch: 'full'}}.
        """
        cells = {}
        height, width = quantized.shape[:2]

        # Build palette RGB lookup for matching pixels to palette indices
        palette_rgbs = []
        for p in raw_palette:
            if 'rgb' in p:
                palette_rgbs.append(p['rgb'])
            else:
                hex_color = p['rgbHex'].lstrip('#')
                palette_rgbs.append(tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)))

        for y in range(height):
            for x in range(width):
                pixel = quantized[y, x]
                r, g, b = int(pixel[0]), int(pixel[1]), int(pixel[2])

                # Skip near-white pixels
                if r > 250 and g > 250 and b > 250:
                    continue

                # Find matching palette index
                pixel_rgb = (r, g, b)
                best_idx = 0
                best_dist = float('inf')
                for i, pal_rgb in enumerate(palette_rgbs):
                    dist = sum((a - b_) ** 2 for a, b_ in zip(pixel_rgb, pal_rgb))
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = i
                    if dist == 0:
                        break

                pc_id = quantized_to_pc.get(best_idx)
                if pc_id:
                    key = f"{x},{y}"
                    cells[key] = [{'color': pc_id, 'stitch': 'full'}]

        return cells

    @staticmethod
    def _determine_vendor(project: Project) -> ColorVendor:
        """
        Determine the vendor to use based on the project's existing colors.

        Falls back to DMC if no colors exist.
        """
        pc = ProjectColor.query.filter_by(project_id=project.id).first()
        if pc:
            color = Color.query.get(pc.color_id)
            if color and color.vendor:
                return color.vendor
        return ColorVendor.DMC
