"""Project service for CRUD operations"""
from stitch.models.project import Project, ProjectStatus
from stitch.database import db
from typing import Optional, List
import uuid


class ProjectService:
    """Service for managing projects"""

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
                'majorGridInterval': 10,
                'showGridNumbers': False,
                'defaultStitchType': 'full'
            }
        }

    @staticmethod
    def create_project(user_id: str, name: str, width: int, height: int, cloth_color: str = '#ffffff', description: str = None) -> Project:
        """
        Create a new project

        Args:
            user_id: User's ID
            name: Project name
            width: Grid width
            height: Grid height
            cloth_color: Cloth background color (hex)
            description: Optional project description

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
            state=initial_state
        )

        db.session.add(project)
        db.session.commit()

        return project

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

        # Update allowed fields
        for key in ['name', 'description', 'width', 'height', 'cloth_color', 'state']:
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

        # Create initial state with palette and layers
        initial_state = ProjectService.create_initial_state(width, height)
        initial_state['palette'] = palette

        # Layer 1: Reference layer (bottom) - read-only original image
        reference_layer_id = str(uuid.uuid4())
        reference_layer = {
            'id': reference_layer_id,
            'type': 'reference',
            'name': 'Reference (original)',
            'visible': True,
            'activeForExport': False,
            'editable': False,
            'cells': reference_cells,
            'opacity': 0.7
        }

        # Layer 2: Image layer (middle) - the quantized/DMC matched image
        image_layer_id = str(uuid.uuid4())
        image_layer = {
            'id': image_layer_id,
            'type': 'raster',
            'name': 'Image layer',
            'visible': True,
            'activeForExport': True,
            'editable': True,
            'cells': image_cells
        }

        # Layer 3: Edges layer (top) - outlines
        edges_layer_id = str(uuid.uuid4())
        edges_layer = {
            'id': edges_layer_id,
            'type': 'raster',
            'name': 'Edges (outlines)',
            'visible': False,
            'activeForExport': False,
            'editable': True,
            'cells': edge_cells
        }

        # Set layers in order (bottom to top)
        initial_state['layers'] = [reference_layer, image_layer, edges_layer]
        initial_state['activeLayerId'] = image_layer_id

        # Create project
        project = Project(
            user_id=user_id,
            name=name,
            width=width,
            height=height,
            cloth_color='#ffffff',
            state=initial_state
        )

        db.session.add(project)
        db.session.commit()

        # Return project with layer stats for flash message
        project.image_cells_count = len(image_cells)
        project.edge_cells_count = len(edge_cells)
        project.num_colors = processed_data['num_colors']

        return project
