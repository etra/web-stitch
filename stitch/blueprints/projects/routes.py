"""Project CRUD routes."""
import io
import logging

from pathlib import Path

from flask import current_app, render_template, request, redirect, url_for, flash, send_file, session

from stitch.blueprints.projects import bp
from stitch.blueprints.auth.routes import login_required
from stitch.utils.decorators import deprecated
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


@bp.route('/create', methods=['GET', 'POST'])
@login_required
@deprecated("Replaced by wizard flow: new_setup -> new_vendor -> new_colors")
def create():
    """Create new project."""
    user_id = session.get('user_id')

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        width = request.form.get('width', type=int)
        height = request.form.get('height', type=int)

        # Validation
        if not name:
            flash('Project name is required.', 'danger')
            return render_template('projects/form.html')

        if not width or width < 1 or width > 1000:
            flash('Width must be between 1 and 1000.', 'danger')
            return render_template('projects/form.html')

        if not height or height < 1 or height > 1000:
            flash('Height must be between 1 and 1000.', 'danger')
            return render_template('projects/form.html')

        try:
            project = ProjectService.create_project(
                user_id=user_id,
                name=name,
                width=width,
                height=height,
            )
            flash(f'Project "{project.name}" created successfully!', 'success')
            return redirect(url_for('projects.list'))

        except Exception:
            flash('An error occurred while creating the project.', 'danger')
            return render_template('projects/form.html')

    # GET request - show form
    return render_template('projects/form.html')


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


# =============================================================================
# WIZARD ROUTES - Simplified Project Creation Flow (3 steps)
# =============================================================================

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_setup():
    """Step 1: Configure name, description, and size."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip() or None
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
            return render_template('projects/new/setup.html')

        if not width or width < 10 or width > 1000:
            flash('Width must be between 10 and 1000 stitches.', 'danger')
            return render_template('projects/new/setup.html')

        if not height or height < 10 or height > 1000:
            flash('Height must be between 10 and 1000 stitches.', 'danger')
            return render_template('projects/new/setup.html')

        # Initialize wizard and store data
        WizardService.init_wizard()
        WizardService.update_wizard_data({
            'name': name,
            'description': description,
            'width': width,
            'height': height,
            'difficulty': difficulty,
            'tags': tag_names,
        })

        return redirect(url_for('projects.new_vendor'))

    # GET request - clear any existing wizard state
    WizardService.clear_wizard()
    return render_template('projects/new/setup.html')


@bp.route('/new/vendor', methods=['GET', 'POST'])
@login_required
def new_vendor():
    """Step 2: Select thread vendor."""
    if not WizardService.validate_wizard_state():
        flash('Wizard session expired. Please start again.', 'warning')
        return redirect(url_for('projects.new_setup'))

    if request.method == 'POST':
        vendor = request.form.get('vendor', '')

        # Validation using service
        if not ColorService.is_valid_vendor(vendor):
            flash('Invalid vendor selection.', 'danger')
            return render_template('projects/new/vendor.html',
                                   vendors=ColorService.get_vendors())

        # Store vendor choice
        WizardService.update_wizard_data({'vendor': vendor})

        return redirect(url_for('projects.new_colors'))

    # GET request
    vendors = ColorService.get_vendors()
    return render_template('projects/new/vendor.html', vendors=vendors)


@bp.route('/new/colors', methods=['GET', 'POST'])
@login_required
def new_colors():
    """Step 3: Pick colors and create project."""
    if not WizardService.validate_wizard_state():
        flash('Wizard session expired. Please start again.', 'warning')
        return redirect(url_for('projects.new_setup'))

    wizard_data = WizardService.get_wizard_data()
    vendor = wizard_data.get('vendor')

    if not vendor:
        flash('No vendor selected.', 'danger')
        return redirect(url_for('projects.new_vendor'))

    user_id = session.get('user_id')

    max_palette_colors = current_app.config.get('MAX_PALETTE_COLORS', 32)

    if request.method == 'POST':
        color_codes = request.form.getlist('color_codes')

        # Enforce palette color limit
        if len(color_codes) > max_palette_colors:
            flash(f'Too many colors selected ({len(color_codes)}). Maximum is {max_palette_colors}.', 'danger')
            palette = ColorService.get_colors_by_vendor(ColorVendor(vendor))
            return render_template('projects/new/colors.html',
                                   vendor=vendor,
                                   palette=palette,
                                   wizard_data=wizard_data,
                                   max_palette_colors=max_palette_colors)

        # Build selected colors list using service
        selected_colors = []
        for code in color_codes:
            color = ColorService.get_color(vendor, code)
            if color:
                selected_colors.append(color)

        # Store selected colors
        WizardService.update_wizard_data({'selected_colors': selected_colors})

        try:
            # Create project
            project = WizardService.create_blank_project(user_id)

            # Clear wizard state
            WizardService.clear_wizard()

            flash(f'Project "{project.name}" created successfully!', 'success')
            return redirect(url_for('projects.list'))

        except Exception as e:
            flash(f'Error creating project: {str(e)}', 'danger')
            palette = ColorService.get_colors_by_vendor(ColorVendor(vendor))
            return render_template('projects/new/colors.html',
                                   vendor=vendor,
                                   palette=palette,
                                   wizard_data=wizard_data,
                                   max_palette_colors=max_palette_colors)

    # GET request
    palette = ColorService.get_colors_by_vendor(ColorVendor(vendor))
    return render_template('projects/new/colors.html',
                           vendor=vendor,
                           palette=palette,
                           wizard_data=wizard_data,
                           max_palette_colors=max_palette_colors)
