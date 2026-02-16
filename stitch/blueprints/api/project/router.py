"""API routes for project data."""
from datetime import datetime

from flask import current_app, jsonify, request, session
from pydantic import ValidationError

from stitch.blueprints.api import bp
from markupsafe import Markup

from stitch.blueprints.api.project.schema import (
    ActionsHtmlResponse,
    AddPaletteColorsRequest,
    AddPaletteColorsResponse,
    ConvertToStitchesRequest,
    FullProjectDataResponse,
    ImageToStitchesResponse,
    MergePaletteColorsRequest,
    MergePaletteColorsResponse,
    ProjectLayersResponse,
    ProjectsListResponse,
    ReferenceImageResponse,
    RemovePaletteColorsRequest,
    RemovePaletteColorsResponse,
    SaveProjectRequest,
    SaveProjectResponse,
)
from stitch.blueprints.auth.routes import login_required
from stitch.models.project_color import ProjectColor
from stitch.models.project_layer import ProjectLayer
from stitch.models.project_layer_cells import ProjectLayerCells
from stitch.models.project_layer_paths import ProjectLayerPaths
from stitch.models.project_layer_image import ProjectLayerImage
from stitch.services.layer_image_service import LayerImageService
from stitch.services.project_service import ProjectService


def _build_layers_data(project_id):
    """Build layers list with cells and paths from new tables."""
    project_layers = ProjectLayer.query.filter_by(project_id=project_id) \
        .order_by(ProjectLayer.sort_order).all()

    layers_data = []
    for layer in project_layers:
        layer_cells = ProjectLayerCells.query.get(layer.id)
        layer_paths = ProjectLayerPaths.query.get(layer.id)
        layer_image = ProjectLayerImage.query.get(layer.id)

        layers_data.append({
            'id': layer.id,
            'type': layer.layer_type,
            'name': layer.name,
            'visible': layer.visible,
            'activeForExport': layer.active_for_export,
            'editable': layer.editable,
            'opacity': layer.opacity,
            'referenceImageData': layer_image.data if layer_image else None,
            'sortOrder': layer.sort_order,
            'offsetX': layer.offset_x or 0,
            'offsetY': layer.offset_y or 0,
            'cells': layer_cells.cells.model_dump() if layer_cells else {},
            'paths': layer_paths.paths.model_dump() if layer_paths else [],
        })
    return layers_data


@bp.get('/projects')
@login_required
def get_projects():
    """Get all projects for the current user."""
    user_id = session.get('user_id')
    projects = ProjectService.get_user_projects(user_id)

    projects_data = [
        {
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'width': p.width,
            'height': p.height,
            'clothColor': p.cloth_color,
        }
        for p in projects
    ]

    response = ProjectsListResponse(projects=projects_data)
    return jsonify(response.model_dump())


@bp.get('/projects/<project_id>')
@login_required
def get_project_data(project_id):
    """Get full project data including state."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    colors = ProjectColor.query.filter_by(project_id=project_id).all()

    project_data = {
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'width': project.width,
        'height': project.height,
        'clothColor': project.cloth_color,
        'status': project.status,
        'activeLayerId': project.active_layer_id,
        'createdAt': project.created_at.isoformat() if project.created_at else None,
        'updatedAt': project.updated_at.isoformat() if project.updated_at else None,
        'colors': [
            {'id': c.id, 'colorId': c.color_id, 'symbol': c.symbol, 'vendor': c.color.vendor, 'code': c.color.code, 'name': c.color.name, 'rgbHex': c.color.hex}
            for c in colors
        ],
        'layers': _build_layers_data(project_id),
        'properties': {
            'majorGridInterval': current_app.config.get('MAJOR_GRID_INTERVAL', 5),
            'showGridNumbers': project.show_grid_numbers or False,
            'defaultStitchType': project.default_stitch_type or 'full',
        },
        'canvas': {
            'width': project.width,
            'height': project.height,
            'color': project.cloth_color,
        },
        'limits': {
            'maxPaletteColors': current_app.config.get('MAX_PALETTE_COLORS', 32),
        },
    }

    response = FullProjectDataResponse(project=project_data)
    return jsonify(response.model_dump())


@bp.post('/projects/<project_id>')
@login_required
def save_project_data(project_id):
    """Save project data from the editor."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    try:
        validated = SaveProjectRequest.model_validate(data)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400

    ProjectService.save_project_data(project, validated.model_dump())

    saved_at = datetime.utcnow().isoformat()
    response = SaveProjectResponse(success=True, savedAt=saved_at)
    return jsonify(response.model_dump())


@bp.get('/projects/<project_id>/layers')
@login_required
def get_project_layers(project_id):
    """Get layer data for a given project ID."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    response = ProjectLayersResponse(layers=_build_layers_data(project_id))
    return jsonify(response.model_dump())


@bp.post('/projects/<project_id>/layers/from-image-reference')
@login_required
def upload_reference_image(project_id):
    """Upload an image as a reference layer. Returns URL and dimensions."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']
    if not image_file.filename:
        return jsonify({'error': 'No image file selected'}), 400

    name = request.form.get('name', 'Reference layer')
    target_width = request.form.get('targetWidth', type=int)
    target_height = request.form.get('targetHeight', type=int)

    if not target_width or not target_height:
        return jsonify({'error': 'targetWidth and targetHeight are required'}), 400

    try:
        result = LayerImageService.upload_reference_image(
            project, image_file, name, target_width, target_height
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    response = ReferenceImageResponse(**result)
    return jsonify(response.model_dump())


@bp.post('/projects/<project_id>/layers/from-image-stitches')
@login_required
def convert_image_to_stitches(project_id):
    """Upload an image and convert it to a stitch layer."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']
    if not image_file.filename:
        return jsonify({'error': 'No image file selected'}), 400

    name = request.form.get('name', 'Image layer')
    max_colors = request.form.get('maxColors', type=int)
    use_existing_str = request.form.get('useExistingColorsOnly', 'false')
    use_existing_colors_only = use_existing_str.lower() == 'true'
    target_width = request.form.get('targetWidth', type=int)
    target_height = request.form.get('targetHeight', type=int)

    if not max_colors:
        return jsonify({'error': 'maxColors is required'}), 400
    if not target_width or not target_height:
        return jsonify({'error': 'targetWidth and targetHeight are required'}), 400

    try:
        result = LayerImageService.convert_image_to_stitches(
            project, image_file, name, max_colors,
            use_existing_colors_only, target_width, target_height
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    response = ImageToStitchesResponse(**result)
    return jsonify(response.model_dump())


@bp.post('/projects/<project_id>/layers/<layer_id>/convert-to-stitches')
@login_required
def convert_reference_to_stitches(project_id, layer_id):
    """Convert an existing reference layer's stored image to stitches."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    try:
        validated = ConvertToStitchesRequest.model_validate(data)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400

    try:
        result = LayerImageService.convert_reference_to_stitches(
            project, layer_id, validated.maxColors, validated.useExistingColorsOnly
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    response = ImageToStitchesResponse(**result)
    return jsonify(response.model_dump())


@bp.post('/projects/<project_id>/palette/colors')
@login_required
def add_palette_colors(project_id):
    """Add colors from the catalog to a project's palette."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    try:
        validated = AddPaletteColorsRequest.model_validate(data)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400

    try:
        added = ProjectService.add_palette_colors(project_id, validated.colorIds)
    except ValueError as e:
        return jsonify({'error': str(e)}), 422

    max_palette = current_app.config.get('MAX_PALETTE_COLORS', 32)
    palette_count = ProjectColor.query.filter_by(project_id=project_id).count()
    response = AddPaletteColorsResponse(
        colors=added,
        paletteCount=palette_count,
        maxPaletteColors=max_palette,
    )
    return jsonify(response.model_dump())


@bp.post('/projects/<project_id>/palette/colors/remove')
@login_required
def remove_palette_colors(project_id):
    """Remove colors from a project's palette."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    try:
        validated = RemovePaletteColorsRequest.model_validate(data)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400

    try:
        ProjectService.remove_palette_colors(project_id, validated.colorIds)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    response = RemovePaletteColorsResponse(success=True)
    return jsonify(response.model_dump())


@bp.post('/projects/<project_id>/palette/merge')
@login_required
def merge_palette_colors(project_id):
    """Merge palette colors: remap references from source to target."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    try:
        validated = MergePaletteColorsRequest.model_validate(data)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400

    merges_data = [m.model_dump() for m in validated.merges]
    try:
        ProjectService.merge_palette_colors(project_id, merges_data)
    except ValueError as e:
        error_msg = str(e)
        if 'Source and target must be different' in error_msg:
            return jsonify({'error': error_msg}), 422
        return jsonify({'error': error_msg}), 404

    response = MergePaletteColorsResponse(success=True)
    return jsonify(response.model_dump())


def _build_actions_html(project_id):
    """Build HTML fragment for project action buttons."""
    back_svg = (
        '<svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">'
        '<path fill-rule="evenodd" d="M15 8a.5.5 0 0 0-.5-.5H2.707l3.147-3.146'
        'a.5.5 0 1 0-.708-.708l-4 4a.5.5 0 0 0 0 .708l4 4a.5.5 0 0 0 .708-.708'
        'L2.707 8.5H14.5A.5.5 0 0 0 15 8z"/></svg>'
    )
    save_svg = (
        '<svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">'
        '<path d="M2 1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4.414'
        'A1 1 0 0 0 14.707 4L12 1.293A1 1 0 0 0 11.293 1H2zm0 1h1v3a.5.5 0 0 0'
        ' .5.5h7a.5.5 0 0 0 .5-.5V2h.293L14 4.414V14H2V2zm3 0v2.5h4V2H5zm3 7'
        'a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm0 1a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/></svg>'
    )
    print_svg = (
        '<svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">'
        '<path d="M2.5 8a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>'
        '<path d="M5 1a1 1 0 0 0-1 1v1H3.5A1.5 1.5 0 0 0 2 4.5v4A1.5 1.5 0 0 0'
        ' 3.5 10H4v2a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2h.5A1.5 1.5 0 0 0 14 8.5'
        'v-4A1.5 1.5 0 0 0 12.5 3H12V2a1 1 0 0 0-1-1H5zm6 1H5v1h6V2zm1 4H4v6h8'
        'V6zM3.5 4h9a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-.5.5H12V6a1 1 0 0 0-1-1H5'
        'a1 1 0 0 0-1 1v3H3.5a.5.5 0 0 1-.5-.5v-4a.5.5 0 0 1 .5-.5z"/></svg>'
    )

    back_url = Markup.escape('/projects/')
    print_url = Markup.escape(f'/print/{project_id}')

    return (
        '<div class="action-buttons__buttons">'
        f'<button class="action-buttons__btn" data-action="navigate" data-url="{back_url}" title="Back to projects">'
        f'{back_svg}</button>'
        f'<button class="action-buttons__btn action-buttons__btn--save" data-action="save" title="Save project">'
        f'{save_svg}<span class="action-buttons__indicator action-buttons__indicator--hidden"></span></button>'
        f'<button class="action-buttons__btn" data-action="navigate" data-url="{print_url}" title="Print pattern">'
        f'{print_svg}</button>'
        '</div>'
    )


@bp.get('/projects/<project_id>/actions')
@login_required
def get_project_actions(project_id):
    """Get action buttons HTML for a project."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    html = _build_actions_html(project_id)
    response = ActionsHtmlResponse(html=html)
    return jsonify(response.model_dump())
