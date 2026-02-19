"""Pattern routes for viewing and sharing cross-stitch patterns."""
import logging
import os
import time

from flask import render_template, redirect, url_for, flash, session, make_response, current_app, request

from stitch.blueprints.print import bp
from stitch.services.project_service import ProjectService
from stitch.services.pattern_renderer import PatternRenderer
from stitch.services.pattern_pdf_service import PatternPDFService


def _parse_render_mode(args):
    """Parse display flags from query params (?color=1&symbol=1&stitch=0&line=1)."""
    return {
        'show_color': args.get('color', '0') == '1',
        'show_stitch': args.get('stitch', '0') == '1',
        'show_symbol': args.get('symbol', '1') == '1',
        'show_line': args.get('line', '1') == '1',
    }


def _get_accessible_project(project_id):
    """Load a project if it's public or owned by the current user. Returns None otherwise."""
    project = ProjectService.get_project(project_id)
    if not project:
        return None
    if project.is_public or project.user_id == session.get('user_id'):
        return project
    return None


@bp.route('/<project_id>')
def view(project_id):
    """View pattern as printable pages with overview, legend, and pattern grids."""
    project = _get_accessible_project(project_id)

    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('main.index'))

    try:
        logger = logging.getLogger(__name__)
        t_total = time.perf_counter()

        t0 = time.perf_counter()
        state = ProjectService.assemble_state(project)
        logger.info('[print/view] assemble_state: %.3fs', time.perf_counter() - t0)

        # Page 1: Overview - scaled colored pattern
        t0 = time.perf_counter()
        overview_pattern = PatternRenderer.render_overview_pattern(
            state,
            project.width,
            project.height,
            max_size=500
        )
        overview_base64 = PatternRenderer.image_to_base64(overview_pattern)
        logger.info('[print/view] overview render + base64: %.3fs', time.perf_counter() - t0)

        # Page 2: Legend with color/thread info (single pass)
        t0 = time.perf_counter()
        legend, legend_by_stitch = PatternRenderer.generate_legends(
            state, project.width, project.height
        )
        total_stitches = sum(color['count'] for color in legend)

        # Color legend aggregated by palette index (one row per color)
        color_agg = {}
        for entry in legend:
            pi = entry['paletteIndex']
            if pi not in color_agg:
                color_agg[pi] = {
                    'symbol': entry['symbol'],
                    'rgbHex': entry['rgbHex'],
                    'name': entry['name'],
                    'vendor': entry.get('vendor'),
                    'code': entry.get('code'),
                    'count': 0,
                }
            color_agg[pi]['count'] += entry['count']
        legend_by_color = sorted(
            color_agg.values(),
            key=lambda x: (x['vendor'] or '', x['code'] or '')
        )
        logger.info('[print/view] legend generation: %.3fs', time.perf_counter() - t0)
        # Stitch preview rendering disabled — by-stitch tables are commented out.
        # To re-enable, uncomment the block below.
        # for category, colors in legend_by_stitch.items():
        #     for color in colors:
        #         preview = PatternRenderer.render_stitch_preview(
        #             color['stitchType'], color['rgbHex'], color['symbol']
        #         )
        #         color['stitchPreview'] = PatternRenderer.image_to_base64(preview)

        # Pages 3+: Calculate page definitions only (images loaded lazily via AJAX)
        page_definitions = PatternRenderer.calculate_pattern_pages(
            project.width,
            project.height,
        )

        total_pages = 2 + len(page_definitions)
        logger.info('[print/view] TOTAL: %.3fs (%d pages for %dx%d, %d colors)',
                     time.perf_counter() - t_total, total_pages,
                     project.width, project.height, len(legend))

        return render_template('print/view.html',
                               project=project,
                               overview_pattern=overview_base64,
                               legend=legend,
                               legend_by_color=legend_by_color,
                               legend_by_stitch=legend_by_stitch,
                               total_stitches=total_stitches,
                               page_definitions=page_definitions,
                               total_pages=total_pages)

    except Exception as e:
        flash(f'Error generating pattern: {str(e)}', 'danger')
        return redirect(url_for('main.index'))


@bp.route('/<project_id>/api/page/<int:page_num>')
def pattern_page_image(project_id, page_num):
    """Return a pattern page image as PNG with specified grid style."""
    project = _get_accessible_project(project_id)

    if not project:
        return {'error': 'Project not found'}, 404

    try:
        render_mode = _parse_render_mode(request.args)

        state = ProjectService.assemble_state(project)

        # Calculate page definitions
        page_definitions = PatternRenderer.calculate_pattern_pages(
            project.width, project.height
        )

        # Find the requested page (1-indexed)
        if page_num < 1 or page_num > len(page_definitions):
            return {'error': 'Page not found'}, 404

        page_def = page_definitions[page_num - 1]

        # Render the page
        page_image = PatternRenderer.render_symbol_page(
            state,
            project.width,
            project.height,
            page_def['x_start'],
            page_def['y_start'],
            page_def['x_end'],
            page_def['y_end'],
            cell_size=30,
            **render_mode
        )

        # Convert to base64
        image_data = PatternRenderer.image_to_base64(page_image)

        return {'image': image_data}

    except Exception as e:
        return {'error': str(e)}, 500


@bp.route('/<project_id>/pdf')
def pdf(project_id):
    """Generate and return pattern as PDF."""
    project = _get_accessible_project(project_id)

    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('main.index'))

    try:
        logger = logging.getLogger(__name__)
        t_total = time.perf_counter()

        # Get display options from query parameters
        render_mode = _parse_render_mode(request.args)

        # Get logo path for footer
        logo_path = os.path.join(
            current_app.root_path, 'static', 'img', 'logo_small.jpeg'
        )
        if not os.path.exists(logo_path):
            logo_path = None

        # Generate PDF with options
        logger.info('[print/pdf] starting PDF generation for %dx%d pattern...',
                     project.width, project.height)
        pdf_bytes = PatternPDFService.generate_pdf(
            project,
            logo_path,
            render_mode=render_mode
        )
        logger.info('[print/pdf] TOTAL: %.3fs (%.1f KB)',
                     time.perf_counter() - t_total, len(pdf_bytes) / 1024)

        # Create response
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        # ASCII-safe filename for latin-1 header + UTF-8 filename* for modern browsers
        from urllib.parse import quote
        safe_name = project.name.encode('ascii', 'replace').decode('ascii')
        utf8_name = quote(project.name)
        response.headers['Content-Disposition'] = (
            f'inline; filename="{safe_name}.pdf"; '
            f"filename*=UTF-8''{utf8_name}.pdf"
        )

        return response

    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('print.view', project_id=project_id))
