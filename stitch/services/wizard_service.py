"""
Wizard service for managing project creation wizard state and logic.

This service handles the multi-step wizard for creating both blank projects
and pattern-based projects.
"""
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Dict, Optional
from flask import current_app, session
from stitch.models.project import Project
from stitch.services.project_service import ProjectService
from stitch.services.tag_service import TagService
from stitch.services.image_processor import ImageProcessor
from stitch.services.color_matcher import ColorMatcher


class WizardService:
    """Manage project creation wizard state and operations"""

    WIZARD_SESSION_KEY = 'project_wizard'
    WIZARD_TIMEOUT_SECONDS = 1800  # 30 minutes

    @staticmethod
    def init_wizard(wizard_type: str = 'blank') -> None:
        """
        Initialize wizard state in session.

        Args:
            wizard_type: Type of wizard ('blank' or 'from_pattern'), defaults to 'blank'
        """
        session[WizardService.WIZARD_SESSION_KEY] = {
            'type': wizard_type,
            'created_at': int(time.time())
        }

    @staticmethod
    def validate_wizard_state(wizard_type: Optional[str] = None) -> bool:
        """
        Check if wizard state is valid and not expired.

        Args:
            wizard_type: Expected wizard type (optional)

        Returns:
            True if valid, False otherwise
        """
        wizard_data = session.get(WizardService.WIZARD_SESSION_KEY)

        if not wizard_data:
            return False

        # Check type if specified
        if wizard_type and wizard_data.get('type') != wizard_type:
            return False

        # Check timeout
        created_at = wizard_data.get('created_at', 0)
        if int(time.time()) - created_at > WizardService.WIZARD_TIMEOUT_SECONDS:
            return False

        return True

    @staticmethod
    def clear_wizard() -> None:
        """Clear wizard state from session."""
        WizardService.cleanup_smart_temp()
        session.pop(WizardService.WIZARD_SESSION_KEY, None)

    # ------------------------------------------------------------------
    # Smart Image temp file management
    # ------------------------------------------------------------------

    @staticmethod
    def _get_temp_dir() -> Path:
        """Return the wizard temp upload base directory (absolute)."""
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        return Path(upload_folder).resolve() / 'wizard_temp'

    @staticmethod
    def save_smart_temp_image(image_file) -> Path:
        """Save uploaded image to a temp directory, store path in session.

        Args:
            image_file: Werkzeug FileStorage from request.files.

        Returns:
            Path to the saved file.
        """
        temp_id = str(uuid.uuid4())
        temp_dir = WizardService._get_temp_dir() / temp_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Preserve original extension
        ext = Path(image_file.filename).suffix.lower() if image_file.filename else '.png'
        file_path = temp_dir / f'original{ext}'
        image_file.save(str(file_path))

        WizardService.update_wizard_data({
            'smart_temp_id': temp_id,
            'smart_temp_file': str(file_path),
            # Clear stale data from previous runs so we don't reuse old results
            'diffusion_result_file': None,
            'diffusion_job_id': None,
            'smart_composed_file': None,
        })
        return file_path

    @staticmethod
    def save_smart_composed_image(image_file) -> Path:
        """Save composed (positioned) image, overwriting any previous.

        Args:
            image_file: Werkzeug FileStorage from request.files.

        Returns:
            Path to the saved composed file.
        """
        wizard_data = WizardService.get_wizard_data()
        temp_id = wizard_data.get('smart_temp_id')

        if not temp_id:
            # No temp dir yet — create one
            temp_id = str(uuid.uuid4())
            temp_dir = WizardService._get_temp_dir() / temp_id
            temp_dir.mkdir(parents=True, exist_ok=True)
            WizardService.update_wizard_data({'smart_temp_id': temp_id})
        else:
            temp_dir = WizardService._get_temp_dir() / temp_id
            temp_dir.mkdir(parents=True, exist_ok=True)

        file_path = temp_dir / 'composed.jpg'
        image_file.save(str(file_path))

        WizardService.update_wizard_data({
            'smart_composed_file': str(file_path),
        })
        return file_path

    @staticmethod
    def save_smart_composed_image_bytes(png_bytes: bytes) -> Path:
        """Save composed image from raw bytes (e.g. diffusion result).

        Args:
            png_bytes: Raw PNG image bytes.

        Returns:
            Path to the saved composed file.
        """
        wizard_data = WizardService.get_wizard_data()
        temp_id = wizard_data.get('smart_temp_id')

        if not temp_id:
            temp_id = str(uuid.uuid4())
            temp_dir = WizardService._get_temp_dir() / temp_id
            temp_dir.mkdir(parents=True, exist_ok=True)
            WizardService.update_wizard_data({'smart_temp_id': temp_id})
        else:
            temp_dir = WizardService._get_temp_dir() / temp_id
            temp_dir.mkdir(parents=True, exist_ok=True)

        file_path = temp_dir / 'composed.png'
        file_path.write_bytes(png_bytes)

        WizardService.update_wizard_data({
            'smart_composed_file': str(file_path),
        })
        return file_path

    @staticmethod
    def get_smart_temp_image_path() -> Optional[Path]:
        """Return path to the original temp image, or None."""
        wizard_data = WizardService.get_wizard_data()
        path_str = wizard_data.get('smart_temp_file')
        if path_str:
            p = Path(path_str)
            if p.exists():
                return p
        return None

    @staticmethod
    def get_smart_composed_image_path() -> Optional[Path]:
        """Return path to the composed temp image, or None."""
        wizard_data = WizardService.get_wizard_data()
        path_str = wizard_data.get('smart_composed_file')
        if path_str:
            p = Path(path_str)
            if p.exists():
                return p
        return None

    @staticmethod
    def save_diffusion_result_image(png_bytes: bytes) -> Path:
        """Save the diffusion pixel-art result PNG to the temp directory.

        Args:
            png_bytes: Raw PNG bytes from the diffusion service.

        Returns:
            Path to the saved file.
        """
        wizard_data = WizardService.get_wizard_data()
        temp_id = wizard_data.get('smart_temp_id')

        if not temp_id:
            temp_id = str(uuid.uuid4())
            temp_dir = WizardService._get_temp_dir() / temp_id
            temp_dir.mkdir(parents=True, exist_ok=True)
            WizardService.update_wizard_data({'smart_temp_id': temp_id})
        else:
            temp_dir = WizardService._get_temp_dir() / temp_id
            temp_dir.mkdir(parents=True, exist_ok=True)

        file_path = temp_dir / 'diffusion_result.png'
        file_path.write_bytes(png_bytes)

        WizardService.update_wizard_data({
            'diffusion_result_file': str(file_path),
        })
        return file_path

    @staticmethod
    def get_diffusion_result_image_path() -> Optional[Path]:
        """Return path to the diffusion result image, or None."""
        wizard_data = WizardService.get_wizard_data()
        path_str = wizard_data.get('diffusion_result_file')
        if path_str:
            p = Path(path_str)
            if p.exists():
                return p
        return None

    @staticmethod
    def cleanup_smart_temp() -> None:
        """Delete the temp directory for smart image uploads."""
        wizard_data = WizardService.get_wizard_data()
        temp_id = wizard_data.get('smart_temp_id')
        if temp_id:
            temp_dir = WizardService._get_temp_dir() / temp_id
            if temp_dir.exists():
                shutil.rmtree(str(temp_dir), ignore_errors=True)

    @staticmethod
    def get_wizard_data() -> Dict:
        """Get current wizard data from session."""
        return session.get(WizardService.WIZARD_SESSION_KEY, {})

    @staticmethod
    def update_wizard_data(data: Dict) -> None:
        """
        Update wizard data in session.

        Args:
            data: Dictionary of data to merge into wizard state
        """
        wizard_data = session.get(WizardService.WIZARD_SESSION_KEY, {})
        wizard_data.update(data)
        session[WizardService.WIZARD_SESSION_KEY] = wizard_data

    @staticmethod
    def create_blank_project(user_id: str) -> Project:
        """
        Create a blank project from wizard data.

        Args:
            user_id: User ID

        Returns:
            Created Project instance
        """
        wizard_data = WizardService.get_wizard_data()

        # Extract wizard parameters
        name = wizard_data.get('name')
        description = wizard_data.get('description')
        width = wizard_data.get('width')
        height = wizard_data.get('height')
        difficulty = wizard_data.get('difficulty')
        tag_names = wizard_data.get('tags', [])
        is_public = wizard_data.get('is_public', False)
        selected_colors = wizard_data.get('selected_colors', [])

        # Create base project
        project = ProjectService.create_project(
            user_id=user_id,
            name=name,
            description=description,
            width=width,
            height=height,
            difficulty=difficulty
        )

        # Set visibility
        if is_public:
            from stitch.models.project import ProjectStatus
            project.status = ProjectStatus.PUBLIC

        # Set project tags
        if tag_names:
            TagService.set_project_tags(project.id, tag_names)

        # Build palette from selected colors
        # Selected colors come from ColorService.get_color() with keys:
        # id, vendor, code, name, hex, is_default
        palette = []
        for idx, color in enumerate(selected_colors):
            palette.append({
                'id': f'c{idx}',
                'vendor': color.get('vendor'),
                'code': color.get('code'),
                'name': color.get('name'),
                'rgbHex': color.get('hex'),
                'rgb': ColorMatcher.hex_to_rgb(color.get('hex')),
                'symbol': ProjectService._generate_symbol(idx),
                'sortIndex': idx,
                'count': 0
            })

        # Update project state with palette via normalized save
        state = ProjectService.assemble_state(project)
        state['palette'] = palette
        ProjectService.save_state(project, state)

        from stitch.database import db
        db.session.commit()

        return project

    @staticmethod
    def create_project_from_image(user_id: str, image_file, max_colors: int) -> Project:
        """
        Create a project from wizard data with an uploaded image converted to stitches.

        Creates the base project, then uses LayerImageService to convert the image
        into a stitch layer with matched vendor colors.

        Args:
            user_id: User ID
            image_file: Uploaded image file (from request.files)
            max_colors: Maximum number of colors for conversion

        Returns:
            Created Project instance
        """
        from stitch.services.layer_image_service import LayerImageService
        from stitch.models.color import ColorVendor

        wizard_data = WizardService.get_wizard_data()

        name = wizard_data.get('name')
        description = wizard_data.get('description')
        width = wizard_data.get('width')
        height = wizard_data.get('height')
        difficulty = wizard_data.get('difficulty')
        tag_names = wizard_data.get('tags', [])
        is_public = wizard_data.get('is_public', False)
        vendor_key = wizard_data.get('vendor')

        # Resolve vendor enum from wizard selection
        vendor = None
        if vendor_key:
            try:
                vendor = ColorVendor(vendor_key)
            except ValueError:
                pass

        # Create base project (with empty state)
        project = ProjectService.create_project(
            user_id=user_id,
            name=name,
            description=description,
            width=width,
            height=height,
            difficulty=difficulty
        )

        # Set visibility
        if is_public:
            from stitch.models.project import ProjectStatus
            project.status = ProjectStatus.PUBLIC

        if tag_names:
            TagService.set_project_tags(project.id, tag_names)

        # Convert image to stitches using the layer image service
        result = LayerImageService.convert_image_to_stitches(
            project, image_file, 'Image',
            max_colors, False, width, height,
            vendor=vendor
        )

        # Build palette from the new colors returned by the conversion
        new_colors = result.get('newColors', [])
        palette = []
        for idx, color in enumerate(new_colors):
            palette.append({
                'id': color['id'],
                'vendor': color.get('vendor'),
                'code': color.get('code'),
                'name': color.get('name'),
                'rgbHex': color.get('rgbHex'),
                'rgb': ColorMatcher.hex_to_rgb(color.get('rgbHex')),
                'symbol': color.get('symbol', ProjectService._generate_symbol(idx)),
                'sortIndex': idx,
                'count': 0,
            })

        # Build the stitch layer from the result
        layer_data = result.get('layer', {})

        # Assemble the state and add palette + layer
        state = ProjectService.assemble_state(project)
        state['palette'] = palette
        state['layers'] = [layer_data]
        state['activeLayerId'] = layer_data.get('id')
        ProjectService.save_state(project, state)

        from stitch.database import db
        db.session.commit()

        return project

    @staticmethod
    def create_smart_image_project(user_id: str, image_file, max_colors: int,
                                   backstitch: bool = True,
                                   edge_detail: str = 'medium',
                                   despeckle: str = 'light',
                                   dithering: str = 'off',
                                   sharpness: str = 'medium',
                                   remove_bg: bool = False,
                                   smoothing: int = 50) -> Project:
        """
        Create a project using the smart image conversion pipeline.

        Args:
            user_id: User ID
            image_file: Uploaded image file (FileStorage or Path)
            max_colors: Maximum number of colors for conversion
            backstitch: Whether to generate backstitch lines.
            edge_detail: Edge sensitivity — 'low', 'medium', or 'high'.
            despeckle: Despeckling strength — 'off', 'light', or 'heavy'.
            dithering: Dithering algorithm — 'off' or 'atkinson'.
            sharpness: Sharpening strength — 'off', 'low', 'medium', or 'high'.
            remove_bg: Whether to remove image background before conversion.
            smoothing: Smoothing strength (0 to 100).

        Returns:
            Created Project instance
        """
        from stitch.services.smart_image_service import SmartImageService
        from stitch.models.color import ColorVendor

        wizard_data = WizardService.get_wizard_data()

        name = wizard_data.get('name')
        description = wizard_data.get('description')
        width = wizard_data.get('width')
        height = wizard_data.get('height')
        difficulty = wizard_data.get('difficulty')
        tag_names = wizard_data.get('tags', [])
        is_public = wizard_data.get('is_public', False)
        vendor_key = wizard_data.get('vendor')

        # Resolve vendor enum from wizard selection
        vendor = None
        if vendor_key:
            try:
                vendor = ColorVendor(vendor_key)
            except ValueError:
                pass

        # Create base project
        project = ProjectService.create_project(
            user_id=user_id,
            name=name,
            description=description,
            width=width,
            height=height,
            difficulty=difficulty
        )

        # Set visibility
        if is_public:
            from stitch.models.project import ProjectStatus
            project.status = ProjectStatus.PUBLIC

        if tag_names:
            TagService.set_project_tags(project.id, tag_names)

        # Convert image using smart pipeline
        result = SmartImageService.convert_image_to_stitches(
            project, image_file, max_colors, vendor=vendor,
            backstitch=backstitch, edge_detail=edge_detail, despeckle=despeckle,
            dithering=dithering, sharpness=sharpness, remove_bg=remove_bg,
            smoothing=smoothing,
        )

        # Build palette from the new colors
        new_colors = result.get('newColors', [])
        palette = []
        for idx, color in enumerate(new_colors):
            palette.append({
                'id': color['id'],
                'vendor': color.get('vendor'),
                'code': color.get('code'),
                'name': color.get('name'),
                'rgbHex': color.get('rgbHex'),
                'rgb': ColorMatcher.hex_to_rgb(color.get('rgbHex')),
                'symbol': color.get('symbol', ProjectService._generate_symbol(idx)),
                'sortIndex': idx,
                'count': 0,
            })

        # Build state
        layer_data = result.get('layer', {})
        state = ProjectService.assemble_state(project)
        state['palette'] = palette
        state['layers'] = [layer_data]
        state['activeLayerId'] = layer_data.get('id')
        ProjectService.save_state(project, state)

        from stitch.database import db
        db.session.commit()

        return project

    @staticmethod
    def create_pattern_project(user_id: str, name: str) -> Project:
        """
        Create a project from pattern image wizard data.

        Args:
            user_id: User ID
            name: Project name

        Returns:
            Created Project instance
        """
        wizard_data = WizardService.get_wizard_data()

        # Extract wizard parameters
        pattern_metadata = wizard_data.get('pattern_metadata', {})
        pattern_filename = wizard_data.get('pattern_image_filename')
        source_filename = wizard_data.get('source_image_filename')
        # Use thread palette if available (matched colors), otherwise use final palette (quantized colors)
        final_palette = wizard_data.get('thread_palette') or wizard_data.get('final_palette', [])

        width = pattern_metadata.get('width')
        height = pattern_metadata.get('height')

        # Create base project
        project = ProjectService.create_project(
            user_id=user_id,
            name=name,
            width=width,
            height=height,
        )

        # Load pattern image and create layers
        from stitch.services.image_service import ImageService
        import os

        upload_dir = ImageService.get_upload_dir(user_id)
        pattern_path = os.path.join(upload_dir, 'processed', pattern_filename)
        source_path = os.path.join(upload_dir, 'originals', source_filename)

        # Process images into layers
        processor = ImageProcessor()

        # Load processed pattern image (already resized with correct aspect ratio)
        import cv2
        pattern_img = cv2.imread(pattern_path)
        pattern_img = cv2.cvtColor(pattern_img, cv2.COLOR_BGR2RGB)

        # Use the processed pattern image for reference layer (maintains aspect ratio)
        reference_cells = processor.image_to_reference_cells(pattern_img, width)

        # Use same processed image for the image layer
        image_cells = processor.image_to_layer_cells(pattern_img, final_palette, width)

        # Create edges layer using the processed image
        edges = processor.detect_edges(pattern_img)
        edges_cells = processor.edges_with_image_colors(edges, pattern_img, final_palette, width)

        # Build layers
        ref_layer_id = str(uuid.uuid4())
        img_layer_id = str(uuid.uuid4())
        edges_layer_id = str(uuid.uuid4())

        layers = [
            {
                'id': ref_layer_id,
                'type': 'reference',
                'name': 'Reference (original)',
                'visible': True,
                'activeForExport': False,
                'editable': False,
                'cells': reference_cells,
                'opacity': 0.7
            },
            {
                'id': img_layer_id,
                'type': 'raster',
                'name': 'Image',
                'visible': True,
                'activeForExport': True,
                'editable': True,
                'cells': image_cells
            },
            {
                'id': edges_layer_id,
                'type': 'raster',
                'name': 'Edges',
                'visible': False,
                'activeForExport': False,
                'editable': True,
                'cells': edges_cells
            }
        ]

        # Update project state via normalized save
        state = ProjectService.assemble_state(project)
        state['palette'] = final_palette
        state['layers'] = layers
        state['activeLayerId'] = img_layer_id
        ProjectService.save_state(project, state)

        from stitch.database import db
        db.session.commit()

        return project
