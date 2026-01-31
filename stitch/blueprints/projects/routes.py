"""Project CRUD routes."""
from flask import render_template, request, redirect, url_for, flash, session

from stitch.blueprints.projects import bp
from stitch.blueprints.auth.routes import login_required
from stitch.services.project_service import ProjectService
from stitch.services.wizard_service import WizardService
from stitch.services.vendor_palette_service import VendorPaletteService


@bp.route('/')
@login_required
def list():
    """List all user projects."""
    user_id = session.get('user_id')
    projects = ProjectService.get_user_projects(user_id)
    return render_template('projects/list.html', projects=projects)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new project."""
    user_id = session.get('user_id')

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        width = request.form.get('width', type=int)
        height = request.form.get('height', type=int)
        cloth_color = request.form.get('cloth_color', '#ffffff')

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
                cloth_color=cloth_color
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
        cloth_color = request.form.get('cloth_color', '#ffffff')

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
                cloth_color=cloth_color
            )
            flash(f'Project "{name}" updated successfully!', 'success')
            return redirect(url_for('projects.list'))

        except Exception:
            flash('An error occurred while updating the project.', 'danger')
            return render_template('projects/form.html', project=project)

    # GET request - show form
    return render_template('projects/form.html', project=project)


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
    """Step 1: Configure name, description, size, and cloth color."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip() or None
        width = request.form.get('width', type=int)
        height = request.form.get('height', type=int)
        cloth_color = '#ffffff'  # Default cloth color

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
            'cloth_color': cloth_color
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
        vendor = request.form.get('vendor', '').lower()

        # Validation using service
        if not VendorPaletteService.is_valid_vendor(vendor):
            flash('Invalid vendor selection.', 'danger')
            return render_template('projects/new/vendor.html',
                                   vendors=VendorPaletteService.get_all_vendors())

        # Store vendor choice
        WizardService.update_wizard_data({'vendor': vendor})

        return redirect(url_for('projects.new_colors'))

    # GET request
    vendors = VendorPaletteService.get_all_vendors()
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

    if request.method == 'POST':
        color_codes = request.form.getlist('color_codes')

        # Build selected colors list using service
        selected_colors = []
        for code in color_codes:
            color = VendorPaletteService.get_color(vendor, code)
            if color:
                color['vendor'] = vendor
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
            palette = VendorPaletteService.get_palette_as_dict_list(vendor)
            return render_template('projects/new/colors.html',
                                   vendor=vendor,
                                   palette=palette,
                                   wizard_data=wizard_data)

    # GET request
    palette = VendorPaletteService.get_palette_as_dict_list(vendor)
    return render_template('projects/new/colors.html',
                           vendor=vendor,
                           palette=palette,
                           wizard_data=wizard_data)
