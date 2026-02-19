"""Project service for CRUD operations and state management"""
from flask import current_app
from stitch.models.project import Project, ProjectStatus
from stitch.models.project_layer import ProjectLayer
from stitch.models.project_color import ProjectColor
from stitch.models.project_layer_cells import ProjectLayerCells
from stitch.models.project_layer_paths import ProjectLayerPaths
from stitch.models.project_layer_image import ProjectLayerImage
from stitch.models.color import Color
from stitch.database import db
from typing import Optional, List, Set
import uuid



# Chart symbols ordered by visual distinctiveness.
# Tier 1 (0–31): highly distinct geometric shapes — ideal for ≤32 color projects.
# Tier 2–4 (32–127): progressively less distinct — acceptable for large works.
CHART_SYMBOLS = [
    # Tier 1 — Highly distinct (0–31)
    # Note: '○' is reserved for french knots (rendered independently)
    '●', '■', '▲', '▼', '◆', '□', '△', '★',
    '☆', '◇', '▷', '◁', '⊙', '⊕', '⊗', '◐',
    '◑', '◒', '◓', '◧', '◨', '◩', '◪', '⊞',
    '⊟', '⊠', '⊡', '✦', '✧', '✚', '✖', '▽',
    # Tier 2 — Good (32–63)
    '▶', '◀', '⊘', '⊜', '⊚', '⦿', '⊝', '◰',
    '◱', '◲', '◳', '♠', '♣', '♥', '♦', '♤',
    '♧', '♡', '♢', '↑', '↓', '←', '→', '↗',
    '↘', '↙', '↖', '✶', '✸', '✹', '✺', '◎',
    # Tier 3 — Acceptable (64–95)
    '◍', '◌', '▪', '▫', '▴', '▵', '◢', '◣',
    '◤', '◥', '☀', '⚙', '⚡', '⬢', '⬡', '▸',
    '▹', '◂', '◃', '▾', '▿', '✻', '✼', '⬥',
    '⬦', '◈', '⟐', '⟡', '☂', '☁', '⌂', '✙',
    # Tier 4 — Filler (96–127)
    '✛', '✜', '✽', '✾', '❖', '⬖', '⬗', '⬘',
    '⬙', '⬠', '♩', '♪', '♫', '♬', '⚪', '⚫',
    '☼', '☾', '☽', '†', '‡', '§', '¶', '⌘',
    '※', '⁂', '⊶', '⊷', '‖', '∅', '∆', '⊛',
]


class ProjectService:
    """Service for managing projects"""

    @staticmethod
    def get_project_layers(project_id: str) -> List[dict]:
        """
        Get all layers for a project in assembled state format.

        Args:
            project_id: Project ID

        Returns:
            List of layer dicts
        """
        layers = ProjectLayer.query.filter_by(project_id=project_id) \
            .order_by(ProjectLayer.sort_order).all()
        assembled_layers = []
        # for layer in layers:



    @staticmethod
    def create_initial_state(width: int, height: int) -> dict:
        """
        Create initial empty project state

        Args:
            width: Grid width in stitches
            height: Grid height in stitches

        Returns:
            dict: Initial state with empty palette and one raster layer
        """
        layer_id = str(uuid.uuid4())
        return {
            'palette': [],
            'layers': [
                {
                    'id': layer_id,
                    'type': 'raster',
                    'name': 'Main stitches',
                    'visible': True,
                    'activeForExport': True,
                    'editable': True,
                    'cells': {}  # Use sparse object instead of pre-allocated array
                }
            ],
            'activeLayerId': layer_id,
            'properties': {
                'majorGridInterval': current_app.config.get('MAJOR_GRID_INTERVAL', 5),
                'showGridNumbers': False,
                'defaultStitchType': 'full'
            }
        }

    @staticmethod
    def assemble_state(project: Project) -> dict:
        """
        Reconstruct the full state dict from normalized tables.

        Queries ProjectLayer, ProjectLayerCells, ProjectLayerPaths, and
        ProjectColor rows for the project and assembles them into the
        JSON format expected by PatternRenderer and all downstream
        consumers (renderer, PDF, etc.).

        Cell data is read from ProjectLayerCells. Path data is read from
        ProjectLayerPaths. Both use UUID-based color references which are
        converted to positional paletteIndex values for downstream consumers.

        Cells are returned in {paletteIndex, stitchType} format where
        paletteIndex is the positional index into the palette array.

        Args:
            project: Project instance

        Returns:
            dict: Full state dict with palette, layers, activeLayerId, properties
        """
        layers = ProjectLayer.query.filter_by(project_id=project.id) \
            .order_by(ProjectLayer.sort_order).all()

        project_colors = ProjectColor.query.filter_by(project_id=project.id) \
            .order_by(ProjectColor.sort_order).all()

        # Batch-load all Color objects referenced by this project's palette
        color_ids = [pc.color_id for pc in project_colors]
        if color_ids:
            colors_by_id = {
                c.id: c for c in Color.query.filter(Color.id.in_(color_ids)).all()
            }
        else:
            colors_by_id = {}

        # Assemble palette and build ProjectColor UUID → palette index mapping
        palette = []
        color_id_to_index = {}
        for idx, pc in enumerate(project_colors):
            color = colors_by_id.get(pc.color_id)
            if color:
                rgb = ProjectService._hex_to_rgb(color.hex)
                palette.append({
                    'id': pc.id,
                    'vendor': color.vendor.value if color.vendor else None,
                    'code': color.code,
                    'name': color.name,
                    'rgbHex': color.hex,
                    'rgb': rgb,
                    'symbol': pc.symbol,
                    'sortIndex': pc.sort_order,
                    'count': 0
                })
                color_id_to_index[pc.id] = idx

        # Assemble layers
        assembled_layers = []
        for layer in layers:
            # Read cells from normalized ProjectLayerCells table
            layer_cells_row = ProjectLayerCells.query.get(layer.id)

            if layer_cells_row:
                # Convert {color: uuid, stitch: type} arrays
                # to [{paletteIndex: int, stitchType: str}, ...]
                raw = layer_cells_row.data or {}
                converted_cells = {}
                for cell_key, cell_value in raw.items():
                    # cell_value is a list of stitch dicts
                    stitches = cell_value if isinstance(cell_value, list) else [cell_value]
                    converted = []
                    for stitch in stitches:
                        color_uuid = stitch.get('color', '')
                        palette_idx = color_id_to_index.get(color_uuid)
                        if palette_idx is not None:
                            converted.append({
                                'paletteIndex': palette_idx,
                                'stitchType': stitch.get('stitch', 'full')
                            })
                    if converted:
                        converted_cells[cell_key] = converted
            else:
                converted_cells = {}

            # Read paths from normalized ProjectLayerPaths table
            layer_paths_row = ProjectLayerPaths.query.get(layer.id)

            if layer_paths_row:
                raw_paths = layer_paths_row.data or []
                converted_paths = []
                for path_entry in raw_paths:
                    palette_idx = color_id_to_index.get(
                        path_entry.get('color', ''))
                    if palette_idx is not None:
                        converted_paths.append({
                            'startX': path_entry['startX'],
                            'startY': path_entry['startY'],
                            'endX': path_entry['endX'],
                            'endY': path_entry['endY'],
                            'paletteIndex': palette_idx,
                            'stitchType': path_entry.get('stitch', 'line')
                        })
            else:
                converted_paths = []

            layer_dict = {
                'id': layer.id,
                'type': layer.layer_type,
                'name': layer.name,
                'visible': layer.visible,
                'activeForExport': layer.active_for_export,
                'editable': layer.editable,
                'offsetX': layer.offset_x or 0,
                'offsetY': layer.offset_y or 0,
                'cells': converted_cells,
                'paths': converted_paths
            }
            if layer.opacity is not None:
                layer_dict['opacity'] = layer.opacity
            assembled_layers.append(layer_dict)

        return {
            'palette': palette,
            'layers': assembled_layers,
            'activeLayerId': project.active_layer_id,
            'clothColor': project.cloth_color,
            'properties': {
                'majorGridInterval': current_app.config.get('MAJOR_GRID_INTERVAL', 5),
                'showGridNumbers': project.show_grid_numbers or False,
                'defaultStitchType': project.default_stitch_type or 'full'
            }
        }

    @staticmethod
    def save_state(project: Project, state_dict: dict) -> None:
        """
        Decompose a state dict into normalized tables.

        Deletes existing layers/colors for the project, then inserts new rows.
        Also updates project-level property columns.

        Uses flush() not commit() — caller is responsible for committing.

        Args:
            project: Project instance
            state_dict: Full state dict with palette, layers, activeLayerId, properties
        """
        # Get existing layer IDs to clean up cells and paths tables
        existing_layer_ids = [
            row[0] for row in
            db.session.query(ProjectLayer.id)
            .filter_by(project_id=project.id).all()
        ]

        # Delete existing normalized data (cells/paths/images first, then layers and colors)
        if existing_layer_ids:
            ProjectLayerCells.query.filter(
                ProjectLayerCells.layer_id.in_(existing_layer_ids)
            ).delete(synchronize_session=False)
            ProjectLayerPaths.query.filter(
                ProjectLayerPaths.layer_id.in_(existing_layer_ids)
            ).delete(synchronize_session=False)
            ProjectLayerImage.query.filter(
                ProjectLayerImage.layer_id.in_(existing_layer_ids)
            ).delete(synchronize_session=False)
        ProjectLayer.query.filter_by(project_id=project.id).delete()
        ProjectColor.query.filter_by(project_id=project.id).delete()

        # Save palette colors
        # Preserve palette 'id' so cell color references stay valid
        for idx, color_data in enumerate(state_dict.get('palette', [])):
            color_record = Color.query.filter_by(
                vendor=color_data.get('vendor'),
                code=color_data.get('code')
            ).first()
            if color_record:
                pc = ProjectColor(
                    id=color_data.get('id', str(uuid.uuid4())),
                    project_id=project.id,
                    color_id=color_record.id,
                    symbol=color_data.get('symbol', ''),
                    sort_order=color_data.get('sortIndex', idx)
                )
                db.session.add(pc)

        # Save layers with cells, paths, and images
        for idx, layer_data in enumerate(state_dict.get('layers', [])):
            layer_id = layer_data.get('id', str(uuid.uuid4()))
            layer = ProjectLayer(
                id=layer_id,
                project_id=project.id,
                layer_type=layer_data.get('type', 'raster'),
                name=layer_data.get('name', ''),
                visible=layer_data.get('visible', True),
                active_for_export=layer_data.get('activeForExport', True),
                editable=layer_data.get('editable', True),
                opacity=layer_data.get('opacity'),
                sort_order=idx,
                offset_x=layer_data.get('offsetX', 0),
                offset_y=layer_data.get('offsetY', 0)
            )
            db.session.add(layer)

            layer_cells = ProjectLayerCells(
                layer_id=layer_id,
                data=layer_data.get('cells', {})
            )
            db.session.add(layer_cells)

            layer_paths = ProjectLayerPaths(
                layer_id=layer_id,
                data=layer_data.get('paths', [])
            )
            db.session.add(layer_paths)

            ref_image_data = layer_data.get('referenceImageData')
            if ref_image_data:
                layer_image = ProjectLayerImage(
                    layer_id=layer_id,
                    data=ref_image_data
                )
                db.session.add(layer_image)

        # Update project-level properties
        properties = state_dict.get('properties', {})
        project.active_layer_id = state_dict.get('activeLayerId')
        project.show_grid_numbers = properties.get('showGridNumbers', False)
        project.default_stitch_type = properties.get('defaultStitchType', 'full')

        db.session.flush()

    @staticmethod
    def save_project_data(project: Project, data: dict) -> None:
        """
        Save project data from the editor API.

        Replaces all mutable project state (colors, layers, cells, paths,
        properties) with data from the save request. Uses delete-and-reinsert
        for layers and colors, writing cell and path data to the normalized
        ProjectLayerCells and ProjectLayerPaths tables.

        Commits the transaction.

        Args:
            project: Project instance (must already be verified for ownership).
            data: Validated request data dict with keys:
                  activeLayerId, colors, layers, properties.

        Side effects:
            Deletes and re-creates all ProjectColor, ProjectLayer,
            ProjectLayerCells, and ProjectLayerPaths rows for the project.
            Updates project-level properties. Commits the transaction.
        """
        # Get existing layer IDs to clean up cells and paths tables
        existing_layer_ids = [
            row[0] for row in
            db.session.query(ProjectLayer.id)
            .filter_by(project_id=project.id).all()
        ]

        # Delete existing data (cells/paths/images first, then layers and colors)
        if existing_layer_ids:
            ProjectLayerCells.query.filter(
                ProjectLayerCells.layer_id.in_(existing_layer_ids)
            ).delete(synchronize_session=False)
            ProjectLayerPaths.query.filter(
                ProjectLayerPaths.layer_id.in_(existing_layer_ids)
            ).delete(synchronize_session=False)
            ProjectLayerImage.query.filter(
                ProjectLayerImage.layer_id.in_(existing_layer_ids)
            ).delete(synchronize_session=False)
        ProjectLayer.query.filter_by(project_id=project.id).delete()
        ProjectColor.query.filter_by(project_id=project.id).delete()

        # Save colors
        for idx, color_data in enumerate(data.get('colors', [])):
            color_record = Color.query.filter_by(
                vendor=color_data['vendor'],
                code=color_data['code']
            ).first()
            if color_record:
                pc = ProjectColor(
                    id=color_data['id'],
                    project_id=project.id,
                    color_id=color_record.id,
                    symbol=color_data['symbol'],
                    sort_order=idx
                )
                db.session.add(pc)

        # Save layers with cells, paths, and images
        for layer_data in data.get('layers', []):
            layer = ProjectLayer(
                id=layer_data['id'],
                project_id=project.id,
                layer_type=layer_data['type'],
                name=layer_data['name'],
                visible=layer_data['visible'],
                active_for_export=layer_data['activeForExport'],
                editable=layer_data['editable'],
                opacity=layer_data.get('opacity'),
                sort_order=layer_data.get('sortOrder', 0),
                offset_x=layer_data.get('offsetX', 0),
                offset_y=layer_data.get('offsetY', 0)
            )
            db.session.add(layer)

            layer_cells = ProjectLayerCells(
                layer_id=layer_data['id'],
                data=layer_data.get('cells', {})
            )
            db.session.add(layer_cells)

            layer_paths = ProjectLayerPaths(
                layer_id=layer_data['id'],
                data=layer_data.get('paths', [])
            )
            db.session.add(layer_paths)

            ref_image_data = layer_data.get('referenceImageData')
            if ref_image_data:
                layer_image = ProjectLayerImage(
                    layer_id=layer_data['id'],
                    data=ref_image_data
                )
                db.session.add(layer_image)

        # Update project-level properties
        project.active_layer_id = data.get('activeLayerId')
        props = data.get('properties', {})
        project.show_grid_numbers = props.get('showGridNumbers', False)
        project.default_stitch_type = props.get('defaultStitchType', 'full')

        db.session.commit()

    @staticmethod
    def get_palette_color_count(project_id: str) -> int:
        """
        Get the number of palette colors for a project.

        Used by project list template to display color count without
        loading the full state.

        Args:
            project_id: Project ID

        Returns:
            Number of palette colors
        """
        return ProjectColor.query.filter_by(project_id=project_id).count()

    @staticmethod
    def create_project(user_id: str, name: str, width: int, height: int, cloth_color: str = '#ffffff', description: str = None, difficulty: int = None) -> Project:
        """
        Create a new project

        Args:
            user_id: User's ID
            name: Project name
            width: Grid width
            height: Grid height
            cloth_color: Cloth background color (hex)
            description: Optional project description
            difficulty: Optional difficulty level (1=Beginner, 2=Intermediate, 3=Advanced)

        Returns:
            Created Project object
        """
        # Create initial state
        initial_state = ProjectService.create_initial_state(width, height)

        # Create project
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
            width=width,
            height=height,
            cloth_color=cloth_color,
            difficulty=difficulty
        )

        db.session.add(project)
        db.session.flush()

        # Decompose state into normalized tables
        ProjectService.save_state(project, initial_state)

        db.session.commit()

        return project

    @staticmethod
    def clone_project(source_project: Project, user_id: str) -> Project:
        """
        Create a full copy of a project for the given user.

        Copies all colors, layers, cells, and paths with fresh UUIDs.
        Color references in cells and paths are remapped to the new UUIDs.

        Args:
            source_project: The project to clone
            user_id: The user who will own the clone

        Returns:
            The newly created Project
        """
        # Create new project with same properties
        clone = Project(
            user_id=user_id,
            name=f"{source_project.name} (copy)",
            description=source_project.description,
            width=source_project.width,
            height=source_project.height,
            cloth_color=source_project.cloth_color,
            difficulty=source_project.difficulty,
            show_grid_numbers=source_project.show_grid_numbers,
            default_stitch_type=source_project.default_stitch_type,
        )
        db.session.add(clone)
        db.session.flush()

        # Copy colors, building old UUID → new UUID mapping
        source_colors = ProjectColor.query.filter_by(
            project_id=source_project.id
        ).order_by(ProjectColor.sort_order).all()

        color_uuid_map = {}  # old_id → new_id
        for pc in source_colors:
            new_id = str(uuid.uuid4())
            color_uuid_map[pc.id] = new_id
            db.session.add(ProjectColor(
                id=new_id,
                project_id=clone.id,
                color_id=pc.color_id,
                symbol=pc.symbol,
                sort_order=pc.sort_order,
            ))

        # Copy layers with cells and paths
        source_layers = ProjectLayer.query.filter_by(
            project_id=source_project.id
        ).order_by(ProjectLayer.sort_order).all()

        layer_id_map = {}  # old_id → new_id
        for layer in source_layers:
            new_layer_id = str(uuid.uuid4())
            layer_id_map[layer.id] = new_layer_id

            db.session.add(ProjectLayer(
                id=new_layer_id,
                project_id=clone.id,
                layer_type=layer.layer_type,
                name=layer.name,
                visible=layer.visible,
                active_for_export=layer.active_for_export,
                editable=layer.editable,
                opacity=layer.opacity,
                sort_order=layer.sort_order,
            ))

            # Copy cells with remapped color UUIDs
            cells_row = ProjectLayerCells.query.get(layer.id)
            new_cells = {}
            if cells_row and cells_row.data:
                for cell_key, stitches in cells_row.data.items():
                    stitch_list = stitches if isinstance(stitches, list) else [stitches]
                    remapped = []
                    for s in stitch_list:
                        new_color = color_uuid_map.get(s.get('color', ''))
                        if new_color:
                            remapped.append({'color': new_color, 'stitch': s.get('stitch', 'full')})
                    if remapped:
                        new_cells[cell_key] = remapped

            db.session.add(ProjectLayerCells(layer_id=new_layer_id, data=new_cells))

            # Copy paths with remapped color UUIDs
            paths_row = ProjectLayerPaths.query.get(layer.id)
            new_paths = []
            if paths_row and paths_row.data:
                for p in paths_row.data:
                    new_color = color_uuid_map.get(p.get('color', ''))
                    if new_color:
                        new_paths.append({
                            'startX': p['startX'],
                            'startY': p['startY'],
                            'endX': p['endX'],
                            'endY': p['endY'],
                            'color': new_color,
                            'stitch': p.get('stitch', 'line'),
                        })

            db.session.add(ProjectLayerPaths(layer_id=new_layer_id, data=new_paths))

            # Copy reference image if present
            image_row = ProjectLayerImage.query.get(layer.id)
            if image_row and image_row.data:
                db.session.add(ProjectLayerImage(
                    layer_id=new_layer_id,
                    data=image_row.data,
                ))

        # Remap active layer ID
        clone.active_layer_id = layer_id_map.get(source_project.active_layer_id)

        db.session.commit()
        return clone

    @staticmethod
    def get_user_projects(user_id: str, include_deleted: bool = False) -> List[Project]:
        """
        Get all projects for a user

        Args:
            user_id: User's ID
            include_deleted: If True, include soft-deleted projects

        Returns:
            List of Project objects
        """
        query = Project.query.filter_by(user_id=user_id)

        if not include_deleted:
            query = query.filter(Project.status != ProjectStatus.DELETED)

        return query.order_by(Project.updated_at.desc()).all()

    @staticmethod
    def get_project(project_id: str, user_id: str = None, include_deleted: bool = False) -> Optional[Project]:
        """
        Get project by ID

        Args:
            project_id: Project ID
            user_id: Optional user ID to verify ownership
            include_deleted: If True, include soft-deleted projects

        Returns:
            Project object or None
        """
        query = Project.query.filter_by(id=project_id)

        if user_id:
            query = query.filter_by(user_id=user_id)

        if not include_deleted:
            query = query.filter(Project.status != ProjectStatus.DELETED)

        return query.first()

    @staticmethod
    def update_project(project_id: str, user_id: str, **kwargs) -> Optional[Project]:
        """
        Update project fields

        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)
            **kwargs: Fields to update (name, width, height, cloth_color, state)

        Returns:
            Updated Project object or None
        """
        project = ProjectService.get_project(project_id, user_id)
        if not project:
            return None

        # If state is provided, route through save_state
        if 'state' in kwargs:
            ProjectService.save_state(project, kwargs.pop('state'))

        # Update other allowed fields
        for key in ['name', 'description', 'width', 'height', 'cloth_color', 'difficulty']:
            if key in kwargs:
                setattr(project, key, kwargs[key])

        db.session.commit()
        return project

    @staticmethod
    def delete_project(project_id: str, user_id: str) -> bool:
        """
        Soft delete a project (sets status to DELETED)

        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)

        Returns:
            True if deleted, False if not found
        """
        project = ProjectService.get_project(project_id, user_id)
        if not project:
            return False

        project.status = ProjectStatus.DELETED
        db.session.commit()
        return True

    @staticmethod
    def restore_project(project_id: str, user_id: str) -> bool:
        """
        Restore a soft-deleted project

        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)

        Returns:
            True if restored, False if not found
        """
        project = ProjectService.get_project(project_id, user_id, include_deleted=True)
        if not project or project.status != ProjectStatus.DELETED:
            return False

        project.status = ProjectStatus.DEFAULT
        db.session.commit()
        return True

    @staticmethod
    def hard_delete_project(project_id: str, user_id: str) -> bool:
        """
        Permanently delete a project from database

        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)

        Returns:
            True if deleted, False if not found
        """
        project = ProjectService.get_project(project_id, user_id, include_deleted=True)
        if not project:
            return False

        # Delete related normalized data (cells/paths/images first, then layers and colors)
        existing_layer_ids = [
            row[0] for row in
            db.session.query(ProjectLayer.id)
            .filter_by(project_id=project.id).all()
        ]
        if existing_layer_ids:
            ProjectLayerCells.query.filter(
                ProjectLayerCells.layer_id.in_(existing_layer_ids)
            ).delete(synchronize_session=False)
            ProjectLayerPaths.query.filter(
                ProjectLayerPaths.layer_id.in_(existing_layer_ids)
            ).delete(synchronize_session=False)
            ProjectLayerImage.query.filter(
                ProjectLayerImage.layer_id.in_(existing_layer_ids)
            ).delete(synchronize_session=False)
        ProjectLayer.query.filter_by(project_id=project.id).delete()
        ProjectColor.query.filter_by(project_id=project.id).delete()

        db.session.delete(project)
        db.session.commit()
        return True

    @staticmethod
    def create_project_from_image(
        user_id: str,
        name: str,
        processed_data: dict,
        processed_image_path: str,
        original_image_path: str
    ) -> Project:
        """
        Create a new project from a processed image with layers.

        Args:
            user_id: User's ID
            name: Project name
            processed_data: Dict with width, height, palette, processing_params
            processed_image_path: Path to the processed (quantized) image
            original_image_path: Path to the original image

        Returns:
            Created Project object

        Side effects:
            Creates three layers: reference (original), image (quantized), edges
        """
        from stitch.services.image_processor import ImageProcessor

        width = processed_data['width']
        height = processed_data['height']
        palette = processed_data['palette']
        params = processed_data['processing_params']

        # Load the processed (quantized) image
        processed_image = ImageProcessor.load_image(processed_image_path)

        # Re-process original image to get edges and reference layer
        original_img = ImageProcessor.load_image(original_image_path)
        original_rgb = ImageProcessor.remove_alpha(original_img)
        original_resized = ImageProcessor.resize_to_grid(
            original_rgb,
            params['width'],
            params['height']
        )

        # Detect edges from the resized original
        edges = ImageProcessor.detect_edges(original_resized)

        # Convert processed image to layer cells (maps to final palette)
        image_cells = ImageProcessor.image_to_layer_cells(
            processed_image,
            palette,
            width,
            stitch_type='full'
        )

        # Convert original resized image to reference layer cells (with direct RGB colors)
        reference_cells = ImageProcessor.image_to_reference_cells(
            original_resized,
            width
        )

        # Convert edges to layer cells using colors from the processed image
        edge_cells = ImageProcessor.edges_with_image_colors(
            edges,
            processed_image,
            palette,
            width,
            stitch_type='full'
        )

        # Build state dict
        reference_layer_id = str(uuid.uuid4())
        image_layer_id = str(uuid.uuid4())
        edges_layer_id = str(uuid.uuid4())

        state_dict = {
            'palette': palette,
            'layers': [
                {
                    'id': reference_layer_id,
                    'type': 'reference',
                    'name': 'Reference (original)',
                    'visible': True,
                    'activeForExport': False,
                    'editable': False,
                    'cells': reference_cells,
                    'opacity': 0.7
                },
                {
                    'id': image_layer_id,
                    'type': 'raster',
                    'name': 'Image layer',
                    'visible': True,
                    'activeForExport': True,
                    'editable': True,
                    'cells': image_cells
                },
                {
                    'id': edges_layer_id,
                    'type': 'raster',
                    'name': 'Edges (outlines)',
                    'visible': False,
                    'activeForExport': False,
                    'editable': True,
                    'cells': edge_cells
                }
            ],
            'activeLayerId': image_layer_id,
            'properties': {
                'majorGridInterval': current_app.config.get('MAJOR_GRID_INTERVAL', 5),
                'showGridNumbers': False,
                'defaultStitchType': 'full'
            }
        }

        # Create project
        project = Project(
            user_id=user_id,
            name=name,
            width=width,
            height=height,
            cloth_color='#ffffff'
        )

        db.session.add(project)
        db.session.flush()

        # Decompose state into normalized tables
        ProjectService.save_state(project, state_dict)

        db.session.commit()

        # Return project with layer stats for flash message
        project.image_cells_count = len(image_cells)
        project.edge_cells_count = len(edge_cells)
        project.num_colors = processed_data['num_colors']

        return project

    @staticmethod
    def _generate_symbol(index: int) -> str:
        """
        Return chart symbol for the given index from CHART_SYMBOLS.

        Falls back to A-Z sequence for indices beyond the list.

        Args:
            index: Zero-based index

        Returns:
            Unicode symbol string
        """
        if index < len(CHART_SYMBOLS):
            return CHART_SYMBOLS[index]
        # Fallback for indices beyond the curated list
        overflow = index - len(CHART_SYMBOLS)
        result = ''
        while True:
            result = chr(65 + overflow % 26) + result
            overflow = overflow // 26 - 1
            if overflow < 0:
                break
        return result

    @staticmethod
    def add_palette_colors(project_id: str, color_ids: List[int]) -> List[dict]:
        """
        Add colors from the catalog to a project's palette.

        Skips colors already in the palette. Assigns unique symbols
        and sequential sort_order values.

        Args:
            project_id: Project ID
            color_ids: List of Color.id values to add

        Returns:
            List of dicts for newly added palette colors with keys:
            id, colorId, symbol, name, rgbHex, vendor, code

        Raises:
            ValueError: If any color_id does not exist in the colors table
        """
        # Validate all color_ids exist
        colors = Color.query.filter(Color.id.in_(color_ids)).all()
        found_ids = {c.id for c in colors}
        missing = set(color_ids) - found_ids
        if missing:
            raise ValueError(f"Color IDs not found: {sorted(missing)}")
        color_map = {c.id: c for c in colors}

        # Get existing palette entries
        existing = ProjectColor.query.filter_by(project_id=project_id).all()
        existing_color_ids: Set[int] = {pc.color_id for pc in existing}
        existing_symbols: Set[str] = {pc.symbol for pc in existing}

        # Determine max sort_order
        max_sort = max((pc.sort_order for pc in existing), default=-1)

        # Find unused symbols
        def next_symbols(count: int) -> List[str]:
            symbols = []
            i = 0
            while len(symbols) < count:
                candidate = ProjectService._generate_symbol(i)
                if candidate not in existing_symbols:
                    symbols.append(candidate)
                    existing_symbols.add(candidate)
                i += 1
            return symbols

        # Filter out duplicates (preserve input order)
        new_color_ids = []
        seen = set()
        for cid in color_ids:
            if cid not in existing_color_ids and cid not in seen:
                new_color_ids.append(cid)
                seen.add(cid)

        # Enforce palette color limit
        max_colors = current_app.config.get('MAX_PALETTE_COLORS', 32)
        existing_count = len(existing)
        if existing_count + len(new_color_ids) > max_colors:
            available = max_colors - existing_count
            raise ValueError(
                f"Palette color limit reached. "
                f"Current: {existing_count}, requested: {len(new_color_ids)}, "
                f"available slots: {available}, max: {max_colors}."
            )

        symbols = next_symbols(len(new_color_ids))

        added = []
        for idx, cid in enumerate(new_color_ids):
            color = color_map[cid]
            pc = ProjectColor(
                id=str(uuid.uuid4()),
                project_id=project_id,
                color_id=cid,
                symbol=symbols[idx],
                sort_order=max_sort + 1 + idx,
            )
            db.session.add(pc)
            added.append({
                'id': pc.id,
                'colorId': pc.color_id,
                'symbol': pc.symbol,
                'name': color.name,
                'rgbHex': color.hex,
                'vendor': color.vendor.value if color.vendor else None,
                'code': color.code,
            })

        db.session.commit()
        return added

    @staticmethod
    def remove_palette_colors(project_id: str, palette_color_ids: List[str]) -> None:
        """
        Remove colors from a project's palette and clean up references
        in layer cells and paths.

        Args:
            project_id: Project ID
            palette_color_ids: List of ProjectColor.id values to remove

        Raises:
            ValueError: If any palette_color_id not found or doesn't belong to project
        """
        # Validate all IDs exist and belong to this project
        to_remove = ProjectColor.query.filter(
            ProjectColor.id.in_(palette_color_ids),
            ProjectColor.project_id == project_id,
        ).all()
        found_ids = {pc.id for pc in to_remove}
        missing = set(palette_color_ids) - found_ids
        if missing:
            raise ValueError(f"Palette color IDs not found in project: {sorted(missing)}")

        removed_set = found_ids

        # Clean up layer cells and paths
        layers = ProjectLayer.query.filter_by(project_id=project_id).all()
        for layer in layers:
            # Clean cells (each cell is a list of stitches)
            layer_cells = ProjectLayerCells.query.get(layer.id)
            if layer_cells and layer_cells.data:
                cleaned = {}
                for k, v in layer_cells.data.items():
                    stitches = v if isinstance(v, list) else [v]
                    filtered = [s for s in stitches if s.get('color') not in removed_set]
                    if filtered:
                        cleaned[k] = filtered
                layer_cells.data = cleaned

            # Clean paths
            layer_paths = ProjectLayerPaths.query.get(layer.id)
            if layer_paths and layer_paths.data:
                cleaned = [
                    p for p in layer_paths.data
                    if p.get('color') not in removed_set
                ]
                layer_paths.data = cleaned

        # Delete the ProjectColor rows
        for pc in to_remove:
            db.session.delete(pc)

        db.session.commit()

    @staticmethod
    def merge_palette_colors(project_id: str, merges: List[dict]) -> None:
        """
        Merge palette colors: remap all cell/path references from source
        to target, then delete the source colors.

        Args:
            project_id: Project ID
            merges: List of dicts with 'sourceColorId' and 'targetColorId'
                    (both are ProjectColor.id values)

        Raises:
            ValueError: If any source/target not found, doesn't belong to
                        project, or source equals target
        """
        # Collect all referenced IDs
        all_ids = set()
        for m in merges:
            all_ids.add(m['sourceColorId'])
            all_ids.add(m['targetColorId'])

        # Validate all exist and belong to project
        palette_colors = ProjectColor.query.filter(
            ProjectColor.id.in_(all_ids),
            ProjectColor.project_id == project_id,
        ).all()
        found_ids = {pc.id for pc in palette_colors}
        missing = all_ids - found_ids
        if missing:
            raise ValueError(f"Palette color IDs not found in project: {sorted(missing)}")

        # Validate source != target
        for m in merges:
            if m['sourceColorId'] == m['targetColorId']:
                raise ValueError(
                    f"Source and target must be different: {m['sourceColorId']}"
                )

        # Build remap dict: source -> target
        remap = {m['sourceColorId']: m['targetColorId'] for m in merges}

        # Update layer cells and paths
        layers = ProjectLayer.query.filter_by(project_id=project_id).all()
        for layer in layers:
            # Remap cells (each cell is a list of stitches)
            layer_cells = ProjectLayerCells.query.get(layer.id)
            if layer_cells and layer_cells.data:
                updated = {}
                for k, v in layer_cells.data.items():
                    stitches = v if isinstance(v, list) else [v]
                    remapped = []
                    for s in stitches:
                        color = s.get('color', '')
                        if color in remap:
                            s = dict(s, color=remap[color])
                        remapped.append(s)
                    updated[k] = remapped
                layer_cells.data = updated

            # Remap paths
            layer_paths = ProjectLayerPaths.query.get(layer.id)
            if layer_paths and layer_paths.data:
                updated = []
                for p in layer_paths.data:
                    color = p.get('color', '')
                    if color in remap:
                        p = dict(p, color=remap[color])
                    updated.append(p)
                layer_paths.data = updated

        # Delete source ProjectColor rows
        source_ids = [m['sourceColorId'] for m in merges]
        ProjectColor.query.filter(
            ProjectColor.id.in_(source_ids),
            ProjectColor.project_id == project_id,
        ).delete(synchronize_session=False)

        db.session.commit()

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> list:
        """Convert hex color string to [r, g, b] list."""
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
