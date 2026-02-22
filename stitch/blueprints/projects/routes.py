"""Project CRUD routes."""
import base64
import io
import logging
import types

from pathlib import Path

from flask import current_app, jsonify, render_template, request, redirect, url_for, flash, send_file, session

from stitch.blueprints.projects import bp
from stitch.blueprints.auth.routes import login_required
from stitch.models.project import ProjectStatus
from stitch.services.project_service import ProjectService
from stitch.services.sample_project_service import SampleProjectService
from stitch.services.wizard_service import WizardService
from stitch.services.color_service import ColorService
from stitch.services.tag_service import TagService
from stitch.models.color import ColorVendor


@bp.route('/<project_id>/editor')
@login_required
def editor(project_id):
    """Stitch editor page for a project."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects.list'))

    return render_template(
        'projects/editor.html',
        project=project,
        project_id=project.id,
        api_base_url='/api',
    )


@bp.route('/')
@login_required
def list():
    """List all user projects."""
    user_id = session.get('user_id')
    projects = ProjectService.get_user_projects(user_id)
    # Pre-compute palette color counts for display (avoids loading full state in template)
    color_counts = {p.id: ProjectService.get_palette_color_count(p.id) for p in projects}
    return render_template('projects/list.html', projects=projects, color_counts=color_counts)



@bp.route('/<project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(project_id):
    """Edit project."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects.list'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        width = request.form.get('width', type=int)
        height = request.form.get('height', type=int)

        # Difficulty (optional)
        difficulty = request.form.get('difficulty', type=int)
        if difficulty is not None and difficulty not in (1, 2, 3):
            difficulty = None

        # Tags (optional)
        tag_names = request.form.getlist('tags')

        # Validation
        if not name:
            flash('Project name is required.', 'danger')
            return render_template('projects/form.html', project=project)

        if not width or width < 1 or width > 1000:
            flash('Width must be between 1 and 1000.', 'danger')
            return render_template('projects/form.html', project=project)

        if not height or height < 1 or height > 1000:
            flash('Height must be between 1 and 1000.', 'danger')
            return render_template('projects/form.html', project=project)

        try:
            ProjectService.update_project(
                project_id=project_id,
                user_id=user_id,
                name=name,
                width=width,
                height=height,
                difficulty=difficulty
            )
            TagService.set_project_tags(project_id, tag_names)
            from stitch.database import db
            db.session.commit()
            flash(f'Project "{name}" updated successfully!', 'success')
            return redirect(url_for('projects.list'))

        except Exception:
            flash('An error occurred while updating the project.', 'danger')
            return render_template('projects/form.html', project=project)

    # GET request - show form
    return render_template('projects/form.html', project=project)


@bp.route('/<project_id>/thumbnail')
def thumbnail(project_id):
    """Generate thumbnail preview of project canvas as PNG.

    Accessible by project owner or anyone if the project is public.
    """
    from stitch.services.pattern_renderer import PatternRenderer
    import cv2

    project = ProjectService.get_project(project_id)
    if not project or (not project.is_public and project.user_id != session.get('user_id')):
        return '', 404

    try:
        state = ProjectService.assemble_state(project)
        thumbnail_image = PatternRenderer.render_colored_pattern(
            state,
            project.width,
            project.height,
            cell_size=3
        )

        thumbnail_bgr = cv2.cvtColor(thumbnail_image, cv2.COLOR_RGB2BGR)
        success, buffer = cv2.imencode('.png', thumbnail_bgr)

        if not success:
            return '', 500

        return send_file(
            io.BytesIO(buffer.tobytes()),
            mimetype='image/png',
            as_attachment=False
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return '', 500


@bp.route('/<project_id>/thumbnail-large')
def thumbnail_large(project_id):
    """Generate large thumbnail (450x250) with stitches, colors and grid lines.

    Accessible by project owner or anyone if the project is public.
    """
    from stitch.services.pattern_renderer import PatternRenderer
    import cv2

    project = ProjectService.get_project(project_id)
    if not project or (not project.is_public and project.user_id != session.get('user_id')):
        return '', 404

    try:
        state = ProjectService.assemble_state(project)
        thumb = PatternRenderer.render_thumbnail(
            state, project.width, project.height
        )

        thumb_bgr = cv2.cvtColor(thumb, cv2.COLOR_RGB2BGR)
        success, buffer = cv2.imencode('.png', thumb_bgr)

        if not success:
            return '', 500

        return send_file(
            io.BytesIO(buffer.tobytes()),
            mimetype='image/png',
            as_attachment=False
        )

    except Exception:
        return '', 500


@bp.route('/<project_id>/thumbnail-fill')
def thumbnail_fill(project_id):
    """Generate enhanced thumbnail with 4px per cell for crisp detail.

    Accessible by project owner or anyone if the project is public.
    """
    from stitch.services.pattern_renderer import PatternRenderer
    import cv2

    project = ProjectService.get_project(project_id)
    if not project or (not project.is_public and project.user_id != session.get('user_id')):
        return '', 404

    try:
        state = ProjectService.assemble_state(project)
        pattern = PatternRenderer.render_colored_pattern(
            state, project.width, project.height,
            cell_size=4, solid_fill=True
        )
        return _send_image(_render_thumbnail_canvas(pattern))
    except Exception:
        return '', 500


def _render_thumbnail_canvas(image, canvas_w=450, canvas_h=250):
    """Scale image to fit and center on a white canvas."""
    import cv2
    import numpy as np

    h, w = image.shape[:2]
    scale = min(canvas_w / w, canvas_h / h)
    if scale < 1:
        new_w, new_h = int(w * scale), int(h * scale)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        h, w = new_h, new_w

    canvas = np.full((canvas_h, canvas_w, 3), 255, dtype=np.uint8)
    y_off = (canvas_h - h) // 2
    x_off = (canvas_w - w) // 2
    canvas[y_off:y_off + h, x_off:x_off + w] = image
    return canvas


def _send_image(image):
    """Encode RGB numpy array as PNG and return a Flask response."""
    import cv2

    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    success, buffer = cv2.imencode('.png', image_bgr)
    if not success:
        return '', 500
    return send_file(
        io.BytesIO(buffer.tobytes()),
        mimetype='image/png',
        as_attachment=False
    )


THUMBNAIL_TYPES = {'small', 'large', 'fill', 'cross', 'symbol', 'symbolbw'}


@bp.route('/<project_id>/thumbnail-<state_hash>-<image_type>.png')
def cached_thumbnail(project_id, state_hash, image_type):
    """Cacheable thumbnail with content hash in URL.

    URL format: /projects/<id>/thumbnail-<hash>-<type>.png

    The state_hash parameter exists only for URL uniqueness — when project
    state changes the hash changes, busting Cloudflare's cache automatically.
    The hash is not validated server-side.

    Accessible by project owner or anyone if the project is public.
    """
    from stitch.services.pattern_renderer import PatternRenderer

    if image_type not in THUMBNAIL_TYPES:
        return '', 404

    project = ProjectService.get_project(project_id)
    if not project or (not project.is_public and project.user_id != session.get('user_id')):
        return '', 404

    try:
        state = ProjectService.assemble_state(project)

        if image_type == 'small':
            import cv2
            image = PatternRenderer.render_colored_pattern(
                state, project.width, project.height, cell_size=3
            )
            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            success, buffer = cv2.imencode('.png', image_bgr)
            if not success:
                return '', 500
            response = send_file(
                io.BytesIO(buffer.tobytes()),
                mimetype='image/png',
                as_attachment=False
            )
        elif image_type == 'large':
            thumb = PatternRenderer.render_thumbnail(
                state, project.width, project.height
            )
            response = _send_image(thumb)
        elif image_type == 'fill':
            pattern = PatternRenderer.render_colored_pattern(
                state, project.width, project.height,
                cell_size=4, solid_fill=True
            )
            response = _send_image(_render_thumbnail_canvas(pattern))
        elif image_type == 'cross':
            pattern = PatternRenderer.render_colored_pattern(
                state, project.width, project.height,
                cell_size=8, solid_fill=False
            )
            response = _send_image(_render_thumbnail_canvas(pattern))
        elif image_type == 'symbol':
            pattern = PatternRenderer.render_symbol_page(
                state, project.width, project.height,
                x_start=0, y_start=0,
                x_end=project.width, y_end=project.height,
                cell_size=10,
                show_color=True, show_symbol=True,
                show_stitch=False, show_line=True
            )
            response = _send_image(_render_thumbnail_canvas(pattern))
        else:  # symbolbw
            pattern = PatternRenderer.render_symbol_page(
                state, project.width, project.height,
                x_start=0, y_start=0,
                x_end=project.width, y_end=project.height,
                cell_size=10,
                show_color=False, show_symbol=True,
                show_stitch=False, show_line=True
            )
            response = _send_image(_render_thumbnail_canvas(pattern))

        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        return response

    except Exception:
        import traceback
        traceback.print_exc()
        return '', 500


@bp.route('/<project_id>/thumbnail-cross')
def thumbnail_cross(project_id):
    """Thumbnail with colored X stitches on 450x250 canvas."""
    from stitch.services.pattern_renderer import PatternRenderer

    project = ProjectService.get_project(project_id)
    if not project or (not project.is_public and project.user_id != session.get('user_id')):
        return '', 404

    try:
        state = ProjectService.assemble_state(project)
        pattern = PatternRenderer.render_colored_pattern(
            state, project.width, project.height,
            cell_size=8, solid_fill=False
        )
        return _send_image(_render_thumbnail_canvas(pattern))
    except Exception:
        return '', 500


@bp.route('/<project_id>/thumbnail-symbol')
def thumbnail_symbol(project_id):
    """Thumbnail with colored cells and symbols on 450x250 canvas."""
    from stitch.services.pattern_renderer import PatternRenderer

    project = ProjectService.get_project(project_id)
    if not project or (not project.is_public and project.user_id != session.get('user_id')):
        return '', 404

    try:
        state = ProjectService.assemble_state(project)
        pattern = PatternRenderer.render_symbol_page(
            state, project.width, project.height,
            x_start=0, y_start=0,
            x_end=project.width, y_end=project.height,
            cell_size=10,
            show_color=True, show_symbol=True,
            show_stitch=False, show_line=True
        )
        return _send_image(_render_thumbnail_canvas(pattern))
    except Exception:
        return '', 500


@bp.route('/<project_id>/thumbnail-symbol-bw')
def thumbnail_symbol_bw(project_id):
    """Thumbnail with B&W symbols on white grid on 450x250 canvas."""
    from stitch.services.pattern_renderer import PatternRenderer

    project = ProjectService.get_project(project_id)
    if not project or (not project.is_public and project.user_id != session.get('user_id')):
        return '', 404

    try:
        state = ProjectService.assemble_state(project)
        pattern = PatternRenderer.render_symbol_page(
            state, project.width, project.height,
            x_start=0, y_start=0,
            x_end=project.width, y_end=project.height,
            cell_size=10,
            show_color=False, show_symbol=True,
            show_stitch=False, show_line=True
        )
        return _send_image(_render_thumbnail_canvas(pattern))
    except Exception:
        return '', 500


@bp.route('/<project_id>/reference-images/<image_id>')
@login_required
def reference_image(project_id, image_id):
    """Serve a stored reference image PNG."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return '', 404

    # Sanitize image_id to prevent path traversal
    safe_id = Path(image_id).name
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    image_path = Path(upload_folder) / 'projects' / str(project_id) / 'references' / f'{safe_id}.png'

    if not image_path.exists():
        return '', 404

    return send_file(
        str(image_path),
        mimetype='image/png',
        as_attachment=False
    )


@bp.route('/sample', methods=['POST'])
@login_required
def create_sample():
    """Create a sample project with pre-populated stitch data."""
    user_id = session.get('user_id')

    try:
        project = SampleProjectService.create_sample_project(user_id)
        flash(f'Sample project "{project.name}" created!', 'success')
        return redirect(url_for('projects.editor', project_id=project.id))
    except ValueError as e:
        flash(f'Could not create sample project: {e}', 'danger')
    except Exception:
        flash('An error occurred while creating the sample project.', 'danger')

    return redirect(url_for('projects.list'))


@bp.route('/<project_id>/toggle-visibility', methods=['POST'])
@login_required
def toggle_visibility(project_id):
    """Toggle project between public and default (private) status."""
    from stitch.database import db

    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        flash('Project not found.', 'warning')
        return redirect(url_for('projects.list'))

    if project.is_public:
        project.status = ProjectStatus.DEFAULT
        flash(f'"{project.name}" is now private.', 'success')
    else:
        project.status = ProjectStatus.PUBLIC
        flash(f'"{project.name}" is now public.', 'success')

    db.session.commit()
    return redirect(url_for('projects.list'))


@bp.route('/<project_id>/delete', methods=['POST'])
@login_required
def delete(project_id):
    """Delete project."""
    user_id = session.get('user_id')

    if ProjectService.delete_project(project_id, user_id):
        flash('Project deleted successfully.', 'success')
    else:
        flash('Project not found.', 'warning')

    return redirect(url_for('projects.list'))


@bp.route('/<project_id>/clone', methods=['POST'])
@login_required
def clone(project_id):
    """Clone a project. Allowed for own projects or public projects."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id)

    if not project or project.is_deleted:
        flash('Project not found.', 'warning')
        return redirect(url_for('projects.list'))

    if not project.is_public and project.user_id != user_id:
        flash('Project not found.', 'warning')
        return redirect(url_for('projects.list'))

    try:
        clone = ProjectService.clone_project(project, user_id)
        flash(f'Project cloned as "{clone.name}".', 'success')
        return redirect(url_for('projects.editor', project_id=clone.id))
    except Exception as e:
        current_app.logger.error(f'Clone error: {e}')
        flash('An error occurred while cloning the project.', 'danger')
        return redirect(url_for('projects.list'))


# =============================================================================
# WIZARD ROUTES - Smart Image Preview
# =============================================================================

@bp.route('/new/smart-preview', methods=['POST'])
@login_required
def smart_preview():
    """Generate a preview of smart image conversion without creating a project.

    Reads image from temp file stored by smart_position (no upload needed).
    Also accepts an 'image' file upload for backward compatibility.
    Returns JSON with base64 preview PNG, color count, cell count, and palette.
    """
    from stitch.services.smart_image_service import SmartImageService
    from stitch.services.pattern_renderer import PatternRenderer
    from stitch.services.color_matcher import ColorMatcher
    import cv2

    # Try to read composed image from temp storage first
    composed_path = WizardService.get_smart_composed_image_path()
    image_file = request.files.get('image')

    if not composed_path and (not image_file or not image_file.filename):
        return jsonify({'error': 'No image available. Please upload and position an image first.'}), 400

    max_palette_colors = current_app.config.get('MAX_PALETTE_COLORS', 32)
    max_colors = request.form.get('max_colors', type=int) or 32
    max_colors = max(2, min(max_colors, max_palette_colors))

    backstitch = request.form.get('backstitch', 'true') == 'true'
    edge_detail = request.form.get('edge_detail', 'medium')
    if edge_detail not in ('low', 'medium', 'high'):
        edge_detail = 'medium'
    despeckle = request.form.get('despeckle', 'light')
    if despeckle not in ('off', 'light', 'heavy'):
        despeckle = 'light'
    dithering = request.form.get('dithering', 'off')
    if dithering not in ('off', 'atkinson'):
        dithering = 'off'
    sharpness = request.form.get('sharpness', 'medium')
    if sharpness not in ('off', 'low', 'medium', 'high'):
        sharpness = 'medium'
    remove_bg = request.form.get('remove_bg', 'false') == 'true'

    smoothing = request.form.get('smoothing', type=int)
    if smoothing is None:
        smoothing = 50
    smoothing = max(0, min(100, smoothing))

    wizard_data = WizardService.get_wizard_data()
    width = wizard_data.get('width', 70)
    height = wizard_data.get('height', 70)
    vendor_key = wizard_data.get('vendor')

    vendor = None
    if vendor_key:
        try:
            vendor = ColorVendor(vendor_key)
        except ValueError:
            pass

    fake_project = types.SimpleNamespace(width=width, height=height)

    # Use composed path if available, otherwise fall back to uploaded file
    source = composed_path if composed_path else image_file

    try:
        result = SmartImageService.convert_image_to_stitches(
            fake_project, source, max_colors, vendor=vendor,
            backstitch=backstitch, edge_detail=edge_detail, despeckle=despeckle,
            dithering=dithering, sharpness=sharpness, remove_bg=remove_bg,
            smoothing=smoothing,
        )
    except Exception as e:
        logging.exception('Smart preview processing error')
        return jsonify({'error': f'Image processing failed: {str(e)}'}), 500

    # Build palette in renderer-compatible format
    new_colors = result.get('newColors', [])
    color_id_to_index = {}
    palette = []
    for idx, color in enumerate(new_colors):
        color_id_to_index[color['id']] = idx
        palette.append({
            'rgbHex': color.get('rgbHex'),
            'rgb': ColorMatcher.hex_to_rgb(color.get('rgbHex')),
            'symbol': color.get('symbol', '?'),
        })

    # Convert cells from {color, stitch} to {paletteIndex, stitchType}
    layer_data = result.get('layer', {})
    raw_cells = layer_data.get('cells', {})
    converted_cells = {}
    cell_count = 0
    for key, stitch_list in raw_cells.items():
        converted = []
        for s in stitch_list:
            pi = color_id_to_index.get(s.get('color'), 0)
            converted.append({
                'paletteIndex': pi,
                'stitchType': s.get('stitch', 'full'),
            })
        converted_cells[key] = converted
        cell_count += len(converted)

    # Convert paths similarly
    raw_paths = layer_data.get('paths', [])
    converted_paths = []
    for p in raw_paths:
        pi = color_id_to_index.get(p.get('color'), 0)
        converted_paths.append({
            'paletteIndex': pi,
            'stitchType': p.get('stitch', 'line'),
            'startX': p.get('startX', 0),
            'startY': p.get('startY', 0),
            'endX': p.get('endX', 0),
            'endY': p.get('endY', 0),
        })

    state = {
        'palette': palette,
        'layers': [{
            'type': 'raster',
            'visible': True,
            'activeForExport': True,
            'cells': converted_cells,
            'paths': converted_paths,
        }],
    }

    pattern = PatternRenderer.render_colored_pattern(
        state, width, height, cell_size=4, solid_fill=True
    )
    thumb = _render_thumbnail_canvas(pattern)

    # Encode to base64 PNG
    thumb_bgr = cv2.cvtColor(thumb, cv2.COLOR_RGB2BGR)
    success, buffer = cv2.imencode('.png', thumb_bgr)
    if not success:
        return jsonify({'error': 'Failed to encode preview image.'}), 500

    b64 = base64.b64encode(buffer.tobytes()).decode('ascii')

    # Build palette info for display
    palette_info = []
    for color in new_colors:
        palette_info.append({
            'code': color.get('code', ''),
            'name': color.get('name', ''),
            'rgbHex': color.get('rgbHex', '#000000'),
            'vendor': color.get('vendor', ''),
        })

    return jsonify({
        'preview': f'data:image/png;base64,{b64}',
        'colorCount': len(new_colors),
        'cellCount': cell_count,
        'palette': palette_info,
    })


# =============================================================================
# WIZARD ROUTES - Project Creation Flow (4 steps)
# =============================================================================

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_name():
    """Step 1: Project name and optional metadata."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip() or None
        difficulty = request.form.get('difficulty', type=int)
        if difficulty is not None and difficulty not in (1, 2, 3):
            difficulty = None
        tag_names = request.form.getlist('tags')
        is_public = request.form.get('is_public') == '1'

        if not name:
            user_id = session.get('user_id')
            project_count = len(ProjectService.get_user_projects(user_id))
            name = f'Project #{project_count + 1}'

        WizardService.init_wizard()
        WizardService.update_wizard_data({
            'name': name,
            'description': description,
            'difficulty': difficulty,
            'tags': tag_names,
            'is_public': is_public,
        })

        return redirect(url_for('projects.new_size'))

    # GET request - clear any existing wizard state
    WizardService.clear_wizard()
    user_id = session.get('user_id')
    project_count = len(ProjectService.get_user_projects(user_id))
    return render_template('projects/new/name.html',
                           next_project_number=project_count + 1)


@bp.route('/new/size', methods=['GET', 'POST'])
@login_required
def new_size():
    """Step 2: Canvas size."""
    if not WizardService.validate_wizard_state():
        flash('Wizard session expired. Please start again.', 'warning')
        return redirect(url_for('projects.new_name'))

    if request.method == 'POST':
        width = request.form.get('width', type=int)
        height = request.form.get('height', type=int)

        if not width or width < 10 or width > 1000:
            flash('Width must be between 10 and 1000 stitches.', 'danger')
            return render_template('projects/new/size.html')

        if not height or height < 10 or height > 1000:
            flash('Height must be between 10 and 1000 stitches.', 'danger')
            return render_template('projects/new/size.html')

        WizardService.update_wizard_data({
            'width': width,
            'height': height,
        })

        return redirect(url_for('projects.new_vendor'))

    return render_template('projects/new/size.html')


@bp.route('/new/vendor', methods=['GET', 'POST'])
@login_required
def new_vendor():
    """Step 3: Select thread vendor."""
    if not WizardService.validate_wizard_state():
        flash('Wizard session expired. Please start again.', 'warning')
        return redirect(url_for('projects.new_name'))

    if request.method == 'POST':
        vendor = request.form.get('vendor', '')

        if not ColorService.is_valid_vendor(vendor):
            flash('Invalid vendor selection.', 'danger')
            return render_template('projects/new/vendor.html',
                                   vendors=ColorService.get_vendors())

        WizardService.update_wizard_data({'vendor': vendor})

        return redirect(url_for('projects.new_create'))

    vendors = ColorService.get_vendors()
    return render_template('projects/new/vendor.html', vendors=vendors)


@bp.route('/new/create', methods=['GET', 'POST'])
@login_required
def new_create():
    """Step 4: Choose creation mode (empty or from image) and create project."""
    if not WizardService.validate_wizard_state():
        flash('Wizard session expired. Please start again.', 'warning')
        return redirect(url_for('projects.new_name'))

    wizard_data = WizardService.get_wizard_data()

    if not wizard_data.get('vendor'):
        flash('No vendor selected.', 'danger')
        return redirect(url_for('projects.new_vendor'))

    user_id = session.get('user_id')
    max_palette_colors = current_app.config.get('MAX_PALETTE_COLORS', 32)

    if request.method == 'POST':
        try:
            project = WizardService.create_blank_project(user_id)
            WizardService.clear_wizard()
            flash(f'Project "{project.name}" created successfully!', 'success')
            return redirect(url_for('projects.editor', project_id=project.id))

        except Exception as e:
            logging.exception('Error creating project')
            flash(f'Error creating project: {str(e)}', 'danger')
            return render_template('projects/new/create.html',
                                   wizard_data=wizard_data,
                                   max_palette_colors=max_palette_colors)

    return render_template('projects/new/create.html',
                           wizard_data=wizard_data,
                           max_palette_colors=max_palette_colors)


# =============================================================================
# WIZARD ROUTES - From Image Sub-Flow (2 pages)
# =============================================================================

@bp.route('/new/image/upload', methods=['GET', 'POST'])
@login_required
def image_upload():
    """From Image step 1: Upload image file."""
    if not WizardService.validate_wizard_state():
        flash('Wizard session expired. Please start again.', 'warning')
        return redirect(url_for('projects.new_name'))

    wizard_data = WizardService.get_wizard_data()

    if request.method == 'POST':
        from stitch.services.image_service import ImageService

        image_file = request.files.get('image')
        if not image_file or not image_file.filename:
            flash('No image file provided.', 'danger')
            return render_template('projects/new/image/upload.html',
                                   wizard_data=wizard_data)

        if not ImageService.allowed_file(image_file.filename):
            flash('File type not allowed. Use JPG, PNG, or GIF.', 'danger')
            return render_template('projects/new/image/upload.html',
                                   wizard_data=wizard_data)

        WizardService.save_smart_temp_image(image_file)
        return redirect(url_for('projects.image_position'))

    return render_template('projects/new/image/upload.html',
                           wizard_data=wizard_data)


@bp.route('/new/image/position', methods=['GET', 'POST'])
@login_required
def image_position():
    """From Image step 2: Position image and create project."""
    if not WizardService.validate_wizard_state():
        flash('Wizard session expired. Please start again.', 'warning')
        return redirect(url_for('projects.new_name'))

    temp_path = WizardService.get_smart_temp_image_path()
    if not temp_path:
        flash('No image uploaded. Please upload an image first.', 'warning')
        return redirect(url_for('projects.image_upload'))

    wizard_data = WizardService.get_wizard_data()
    max_palette_colors = current_app.config.get('MAX_PALETTE_COLORS', 32)

    if request.method == 'POST':
        user_id = session.get('user_id')

        composed_file = request.files.get('composed_image')
        if not composed_file or not composed_file.filename:
            flash('Failed to compose image. Please try again.', 'danger')
            return render_template('projects/new/image/position.html',
                                   wizard_data=wizard_data,
                                   max_palette_colors=max_palette_colors)

        max_colors = request.form.get('max_colors', type=int) or 16
        max_colors = max(2, min(max_colors, max_palette_colors))

        try:
            project = WizardService.create_project_from_image(
                user_id, composed_file, max_colors
            )
            WizardService.clear_wizard()
            flash(f'Project "{project.name}" created successfully!', 'success')
            return redirect(url_for('print.view', project_id=project.id))

        except Exception as e:
            logging.exception('Error creating project from image')
            flash(f'Error creating project: {str(e)}', 'danger')
            return render_template('projects/new/image/position.html',
                                   wizard_data=wizard_data,
                                   max_palette_colors=max_palette_colors)

    return render_template('projects/new/image/position.html',
                           wizard_data=wizard_data,
                           max_palette_colors=max_palette_colors)


@bp.route('/new/image/temp-image')
@login_required
def image_temp_image():
    """Serve the uploaded temp image for the from-image positioner canvas."""
    import mimetypes

    temp_path = WizardService.get_smart_temp_image_path()
    if not temp_path:
        return '', 404

    mime = mimetypes.guess_type(str(temp_path))[0] or 'image/jpeg'

    return send_file(
        str(temp_path),
        mimetype=mime,
        as_attachment=False,
    )


# =============================================================================
# WIZARD ROUTES - Smart Image Sub-Flow (3 pages)
# =============================================================================

@bp.route('/new/smart/upload', methods=['GET', 'POST'])
@login_required
def smart_upload():
    """Smart Image step 1: Upload image file."""
    if not WizardService.validate_wizard_state():
        flash('Wizard session expired. Please start again.', 'warning')
        return redirect(url_for('projects.new_name'))

    wizard_data = WizardService.get_wizard_data()

    if request.method == 'POST':
        from stitch.services.image_service import ImageService

        image_file = request.files.get('image')
        if not image_file or not image_file.filename:
            flash('No image file provided.', 'danger')
            return render_template('projects/new/smart/upload.html',
                                   wizard_data=wizard_data)

        if not ImageService.allowed_file(image_file.filename):
            flash('File type not allowed. Use JPG, PNG, or GIF.', 'danger')
            return render_template('projects/new/smart/upload.html',
                                   wizard_data=wizard_data)

        WizardService.save_smart_temp_image(image_file)
        return redirect(url_for('projects.smart_position'))

    return render_template('projects/new/smart/upload.html',
                           wizard_data=wizard_data)


@bp.route('/new/smart/position', methods=['GET', 'POST'])
@login_required
def smart_position():
    """Smart Image step 2: Position and scale image on grid."""
    if not WizardService.validate_wizard_state():
        flash('Wizard session expired. Please start again.', 'warning')
        return redirect(url_for('projects.new_name'))

    temp_path = WizardService.get_smart_temp_image_path()
    if not temp_path:
        flash('No image uploaded. Please upload an image first.', 'warning')
        return redirect(url_for('projects.smart_upload'))

    wizard_data = WizardService.get_wizard_data()
    max_palette_colors = current_app.config.get('MAX_PALETTE_COLORS', 32)

    if request.method == 'POST':
        # Receive composed image from canvas
        composed_file = request.files.get('composed_image')
        if not composed_file or not composed_file.filename:
            flash('Failed to compose image. Please try again.', 'danger')
            return render_template('projects/new/smart/position.html',
                                   wizard_data=wizard_data,
                                   max_palette_colors=max_palette_colors)

        # Save max_colors chosen on position page
        max_colors = request.form.get('max_colors', type=int) or 32
        max_colors = max(2, min(max_colors, max_palette_colors))
        WizardService.update_wizard_data({'max_colors': max_colors})

        WizardService.save_smart_composed_image(composed_file)
        return redirect(url_for('projects.smart_adjust'))

    return render_template('projects/new/smart/position.html',
                           wizard_data=wizard_data,
                           max_palette_colors=max_palette_colors)


@bp.route('/new/smart/adjust', methods=['GET', 'POST'])
@login_required
def smart_adjust():
    """Smart Image step 3: Adjust settings, preview, and create project."""
    if not WizardService.validate_wizard_state():
        flash('Wizard session expired. Please start again.', 'warning')
        return redirect(url_for('projects.new_name'))

    composed_path = WizardService.get_smart_composed_image_path()
    if not composed_path:
        flash('No composed image. Please position your image first.', 'warning')
        return redirect(url_for('projects.smart_position'))

    wizard_data = WizardService.get_wizard_data()
    max_palette_colors = current_app.config.get('MAX_PALETTE_COLORS', 32)
    wizard_max_colors = wizard_data.get('max_colors', 32)

    if request.method == 'POST':
        user_id = session.get('user_id')

        max_colors = request.form.get('max_colors', type=int) or wizard_max_colors
        max_colors = max(2, min(max_colors, max_palette_colors))

        backstitch = request.form.get('backstitch', 'true') == 'true'
        edge_detail = request.form.get('edge_detail', 'medium')
        if edge_detail not in ('low', 'medium', 'high'):
            edge_detail = 'medium'
        despeckle = request.form.get('despeckle', 'light')
        if despeckle not in ('off', 'light', 'heavy'):
            despeckle = 'light'
        dithering = request.form.get('dithering', 'off')
        if dithering not in ('off', 'atkinson'):
            dithering = 'off'
        sharpness = request.form.get('sharpness', 'medium')
        if sharpness not in ('off', 'low', 'medium', 'high'):
            sharpness = 'medium'
        remove_bg = request.form.get('remove_bg', 'false') == 'true'

        smoothing = request.form.get('smoothing', type=int)
        if smoothing is None:
            smoothing = 50
        smoothing = max(0, min(100, smoothing))

        try:
            project = WizardService.create_smart_image_project(
                user_id, composed_path, max_colors,
                backstitch=backstitch,
                edge_detail=edge_detail,
                despeckle=despeckle,
                dithering=dithering,
                sharpness=sharpness,
                remove_bg=remove_bg,
                smoothing=smoothing,
            )
            WizardService.clear_wizard()
            flash(f'Project "{project.name}" created successfully!', 'success')
            return redirect(url_for('print.view', project_id=project.id))

        except Exception as e:
            logging.exception('Error creating smart image project')
            flash(f'Error creating project: {str(e)}', 'danger')
            return render_template('projects/new/smart/adjust.html',
                                   wizard_data=wizard_data,
                                   max_palette_colors=max_palette_colors,
                                   wizard_max_colors=wizard_max_colors)

    return render_template('projects/new/smart/adjust.html',
                           wizard_data=wizard_data,
                           max_palette_colors=max_palette_colors,
                           wizard_max_colors=wizard_max_colors)


@bp.route('/new/smart/temp-image')
@login_required
def smart_temp_image():
    """Serve the uploaded temp image for the smart positioner canvas."""
    import mimetypes

    temp_path = WizardService.get_smart_temp_image_path()
    if not temp_path:
        return '', 404

    mime = mimetypes.guess_type(str(temp_path))[0] or 'image/jpeg'

    return send_file(
        str(temp_path),
        mimetype=mime,
        as_attachment=False,
    )
