"""Pattern routes for viewing and sharing cross-stitch patterns."""
import os
from flask import render_template, redirect, url_for, flash, session, make_response, current_app, request

from stitch.blueprints.pattern import bp
from stitch.blueprints.auth.routes import login_required
from stitch.services.project_service import ProjectService
from stitch.services.pattern_renderer import PatternRenderer
from stitch.services.pattern_pdf_service import PatternPDFService


@bp.route('/<project_id>')
@login_required
def view(project_id):
    """View pattern as printable pages with overview, legend, and pattern grids."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects.list'))

    try:
        # Page 1: Overview - scaled colored pattern
        overview_pattern = PatternRenderer.render_overview_pattern(
            project.state,
            project.width,
            project.height,
            max_size=500
        )
        overview_base64 = PatternRenderer.image_to_base64(overview_pattern)

        # Page 2: Legend with color/thread info
        legend = PatternRenderer.generate_legend(
            project.state,
            project.width,
            project.height
        )
        total_stitches = sum(color['count'] for color in legend)

        # Legend grouped by stitch type
        legend_by_stitch = PatternRenderer.generate_legend_by_stitch_type(
            project.state,
            project.width,
            project.height
        )

        # Pages 3+: Paginated symbol patterns (50x50 with 5 overlap)
        page_definitions = PatternRenderer.calculate_pattern_pages(
            project.width,
            project.height,
            page_size=50,
            overlap=5
        )

        pattern_pages = []
        for page_def in page_definitions:
            page_image = PatternRenderer.render_symbol_page(
                project.state,
                project.width,
                project.height,
                page_def['x_start'],
                page_def['y_start'],
                page_def['x_end'],
                page_def['y_end'],
                cell_size=18
            )
            pattern_pages.append({
                'page_num': page_def['page_num'],
                'row': page_def['row'],
                'col': page_def['col'],
                'total_rows': page_def['total_rows'],
                'total_cols': page_def['total_cols'],
                'label': page_def['label'],
                'image': PatternRenderer.image_to_base64(page_image)
            })

        # Total pages: 1 (overview) + 1 (legend) + pattern pages
        total_pages = 2 + len(pattern_pages)

        return render_template('pattern/view.html',
                               project=project,
                               overview_pattern=overview_base64,
                               legend=legend,
                               legend_by_stitch=legend_by_stitch,
                               total_stitches=total_stitches,
                               pattern_pages=pattern_pages,
                               total_pages=total_pages)

    except Exception as e:
        flash(f'Error generating pattern: {str(e)}', 'danger')
        return redirect(url_for('editor.canvas', project_id=project_id))


@bp.route('/<project_id>/api/page/<int:page_num>')
@login_required
def pattern_page_image(project_id, page_num):
    """Return a pattern page image as PNG with specified grid style."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return {'error': 'Project not found'}, 404

    try:
        grid_style = request.args.get('grid_style', 'symbols')
        colored = (grid_style == 'colored')

        # Calculate page definitions
        page_definitions = PatternRenderer.calculate_pattern_pages(
            project.width, project.height, page_size=50, overlap=5
        )

        # Find the requested page (1-indexed)
        if page_num < 1 or page_num > len(page_definitions):
            return {'error': 'Page not found'}, 404

        page_def = page_definitions[page_num - 1]

        # Render the page
        page_image = PatternRenderer.render_symbol_page(
            project.state,
            project.width,
            project.height,
            page_def['x_start'],
            page_def['y_start'],
            page_def['x_end'],
            page_def['y_end'],
            cell_size=18,
            colored_background=colored
        )

        # Convert to base64
        image_data = PatternRenderer.image_to_base64(page_image)

        return {'image': image_data}

    except Exception as e:
        return {'error': str(e)}, 500


@bp.route('/<project_id>/pdf')
@login_required
def pdf(project_id):
    """Generate and return pattern as PDF."""
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects.list'))

    try:
        # Get PDF options from query parameters
        grid_style = request.args.get('grid_style', 'symbols')  # 'symbols' or 'colored'

        # Get logo path for footer
        logo_path = os.path.join(
            current_app.root_path, 'static', 'img', 'logo_small.jpeg'
        )
        if not os.path.exists(logo_path):
            logo_path = None

        # Generate PDF with options
        pdf_bytes = PatternPDFService.generate_pdf(
            project,
            logo_path,
            grid_style=grid_style
        )

        # Create response
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{project.name}.pdf"'

        return response

    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('pattern.view', project_id=project_id))
