"""Service for creating sample projects with pre-populated stitch data."""
import uuid

from stitch.database import db
from stitch.models.project import Project
from stitch.models.project_color import ProjectColor
from stitch.models.project_layer import ProjectLayer
from stitch.models.project_layer_cells import ProjectLayerCells
from stitch.models.project_layer_paths import ProjectLayerPaths
from stitch.models.color import Color
from stitch.services.project_service import ProjectService


# Sample project definition: a small 10x10 heart pattern using DMC colors.
# Cell keys are "x,y" coordinates. colorId is Color.id (database primary key).
_SAMPLE_COLOR_IDS = [14, 158, 351, 420]

_SAMPLE_CELLS = {
    "2,1": {"colorId": 14,  "stitch": "full"},
    "3,1": {"colorId": 14,  "stitch": "full"},
    "6,1": {"colorId": 14,  "stitch": "full"},
    "7,1": {"colorId": 14,  "stitch": "full"},
    "1,2": {"colorId": 14,  "stitch": "full"},
    "2,2": {"colorId": 14,  "stitch": "full"},
    "3,2": {"colorId": 14,  "stitch": "full"},
    "4,2": {"colorId": 14,  "stitch": "full"},
    "5,2": {"colorId": 14,  "stitch": "full"},
    "6,2": {"colorId": 14,  "stitch": "full"},
    "7,2": {"colorId": 14,  "stitch": "full"},
    "8,2": {"colorId": 14,  "stitch": "full"},
    "1,3": {"colorId": 14,  "stitch": "full"},
    "2,3": {"colorId": 14,  "stitch": "full"},
    "3,3": {"colorId": 14,  "stitch": "full"},
    "4,3": {"colorId": 14,  "stitch": "full"},
    "5,3": {"colorId": 158, "stitch": "full"},
    "6,3": {"colorId": 158, "stitch": "full"},
    "7,3": {"colorId": 158, "stitch": "full"},
    "8,3": {"colorId": 351, "stitch": "full"},
    "1,4": {"colorId": 14,  "stitch": "full"},
    "2,4": {"colorId": 14,  "stitch": "full"},
    "3,4": {"colorId": 14,  "stitch": "full"},
    "4,4": {"colorId": 158, "stitch": "full"},
    "5,4": {"colorId": 158, "stitch": "full"},
    "6,4": {"colorId": 351, "stitch": "full"},
    "7,4": {"colorId": 351, "stitch": "full"},
    "8,4": {"colorId": 420, "stitch": "full"},
    "2,5": {"colorId": 14,  "stitch": "full"},
    "3,5": {"colorId": 158, "stitch": "full"},
    "4,5": {"colorId": 158, "stitch": "full"},
    "5,5": {"colorId": 351, "stitch": "full"},
    "6,5": {"colorId": 420, "stitch": "full"},
    "7,5": {"colorId": 420, "stitch": "full"},
    "3,6": {"colorId": 351, "stitch": "full"},
    "4,6": {"colorId": 351, "stitch": "full"},
    "5,6": {"colorId": 420, "stitch": "full"},
    "6,6": {"colorId": 420, "stitch": "full"},
    "4,7": {"colorId": 420, "stitch": "full"},
    "5,7": {"colorId": 420, "stitch": "full"},
    "4,8": {"colorId": 420, "stitch": "three-quarter-br"},
    "5,8": {"colorId": 420, "stitch": "three-quarter-bl"},
}

_SAMPLE_PATHS = [
    # Heart outline using corner/intersection coordinates (clockwise).
    # Top of left bump
    {"colorId": 14, "startX": 2, "startY": 1, "endX": 4, "endY": 1, "stitch": "line"},
    # V-notch down
    {"colorId": 14, "startX": 4, "startY": 1, "endX": 5, "endY": 2, "stitch": "line"},
    # V-notch up
    {"colorId": 14, "startX": 5, "startY": 2, "endX": 6, "endY": 1, "stitch": "line"},
    # Top of right bump
    {"colorId": 14, "startX": 6, "startY": 1, "endX": 8, "endY": 1, "stitch": "line"},
    # Right bump diagonal down
    {"colorId": 14, "startX": 8, "startY": 1, "endX": 9, "endY": 2, "stitch": "line"},
    # Right side down
    {"colorId": 14, "startX": 9, "startY": 2, "endX": 9, "endY": 5, "stitch": "line"},
    # Right diagonal to bottom point
    {"colorId": 14, "startX": 9, "startY": 5, "endX": 5, "endY": 9, "stitch": "line"},
    # Left diagonal from bottom point
    {"colorId": 14, "startX": 5, "startY": 9, "endX": 1, "endY": 5, "stitch": "line"},
    # Left side up
    {"colorId": 14, "startX": 1, "startY": 5, "endX": 1, "endY": 2, "stitch": "line"},
    # Left bump diagonal up
    {"colorId": 14, "startX": 1, "startY": 2, "endX": 2, "endY": 1, "stitch": "line"},
]


class SampleProjectService:
    """Create sample projects with pre-populated stitch data."""

    @staticmethod
    def create_sample_project(user_id: str) -> Project:
        """
        Create a sample project with a pre-populated stitch pattern.

        Looks up colors from the catalog by Color.id, creates ProjectColor
        entries, remaps cell/path references, and persists everything via
        normalized tables.

        Args:
            user_id: User ID

        Returns:
            Created Project instance

        Raises:
            ValueError: If required colors are not found in the catalog
        """
        # Look up catalog colors by id and build Color.id → new ProjectColor UUID mapping
        color_id_to_uuid = {}  # Color.id → new ProjectColor UUID
        palette_colors = []  # (new_uuid, Color record, sort_order)

        for idx, color_id in enumerate(_SAMPLE_COLOR_IDS):
            color_record = Color.query.get(color_id)

            if not color_record:
                raise ValueError(
                    f"Catalog color id={color_id} not found. "
                    f"Ensure colors are seeded."
                )

            new_uuid = str(uuid.uuid4())
            color_id_to_uuid[color_id] = new_uuid
            palette_colors.append((new_uuid, color_record, idx))

        # Create project
        project = Project(
            user_id=user_id,
            name='Sample Project',
            description='A sample cross-stitch project to get you started.',
            width=10,
            height=10,
            cloth_color='#ffffff',
            difficulty=1,  # Beginner
        )
        db.session.add(project)
        db.session.flush()

        # Create ProjectColor entries
        for new_uuid, color_record, sort_order in palette_colors:
            pc = ProjectColor(
                id=new_uuid,
                project_id=project.id,
                color_id=color_record.id,
                symbol=ProjectService._generate_symbol(sort_order),
                sort_order=sort_order,
            )
            db.session.add(pc)

        # Convert sample cells: map Color.id → ProjectColor UUID for storage
        remapped_cells = {}
        for cell_key, cell_value in _SAMPLE_CELLS.items():
            pc_uuid = color_id_to_uuid.get(cell_value['colorId'])
            if pc_uuid:
                remapped_cells[cell_key] = [{
                    'color': pc_uuid,
                    'stitch': cell_value['stitch'],
                }]

        # Create layer
        layer_id = str(uuid.uuid4())
        layer = ProjectLayer(
            id=layer_id,
            project_id=project.id,
            layer_type='raster',
            name='Main stitches',
            visible=True,
            active_for_export=True,
            editable=True,
            sort_order=0,
        )
        db.session.add(layer)

        # Create layer cells
        layer_cells = ProjectLayerCells(
            layer_id=layer_id,
            data=remapped_cells,
        )
        db.session.add(layer_cells)

        # Convert sample paths: map Color.id → ProjectColor UUID for storage
        remapped_paths = []
        for path in _SAMPLE_PATHS:
            pc_uuid = color_id_to_uuid.get(path['colorId'])
            if pc_uuid:
                remapped_paths.append({
                    'color': pc_uuid,
                    'startX': path['startX'],
                    'startY': path['startY'],
                    'endX': path['endX'],
                    'endY': path['endY'],
                    'stitch': path['stitch'],
                })

        # Create layer paths
        layer_paths = ProjectLayerPaths(
            layer_id=layer_id,
            data=remapped_paths,
        )
        db.session.add(layer_paths)

        # Set active layer
        project.active_layer_id = layer_id

        db.session.commit()
        return project
