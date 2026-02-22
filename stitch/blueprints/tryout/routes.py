"""Tryout blueprint — anonymous image-to-PDF conversion.

Lets visitors upload an image and download a cross-stitch PDF without
signing up or creating a database project. Uses Flask session + temp files
only — no database writes.

Flow:
  /tryout         → Size + upload (step 1)
  /tryout/image   → Position + adjust (step 2), POST saves composed image
  /tryout/result  → Result page with [Download PDF] + [Save to Projects]
  /tryout/pdf     → Generates and serves PDF (opens in new tab)
  /tryout/save    → Creates real DB project (requires login)
"""
import logging
import mimetypes
import os
import types
from datetime import datetime

from flask import (
    current_app, flash, make_response, redirect, render_template,
    request, session, url_for,
)

from stitch.blueprints.tryout import bp
from stitch.services.wizard_service import WizardService


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Step 1: Size + Upload
# ---------------------------------------------------------------------------

@bp.route('/', methods=['GET', 'POST'])
def index():
    """Size + image upload page."""
    if request.method == 'POST':
        from stitch.services.image_service import ImageService

        # Validate dimensions
        width = request.form.get('width', type=int)
        height = request.form.get('height', type=int)

        if not width or not height or width < 10 or width > 999 or height < 10 or height > 999:
            flash('Width and height must be between 10 and 999.', 'danger')
            return render_template('tryout/index.html')

        # Validate image
        image_file = request.files.get('image')
        if not image_file or not image_file.filename:
            flash('Please upload an image.', 'danger')
            return render_template('tryout/index.html')

        if not ImageService.allowed_file(image_file.filename):
            flash('File type not allowed. Use JPG, PNG, or GIF.', 'danger')
            return render_template('tryout/index.html')

        # Init wizard session and store dimensions
        WizardService.init_wizard(wizard_type='tryout')
        WizardService.update_wizard_data({
            'width': width,
            'height': height,
        })

        # Save temp image
        WizardService.save_smart_temp_image(image_file)

        return redirect(url_for('tryout.image'))

    return render_template('tryout/index.html')


# ---------------------------------------------------------------------------
# Step 2: Position + Adjust
# ---------------------------------------------------------------------------

@bp.route('/image', methods=['GET', 'POST'])
def image():
    """Position image on grid, adjust settings."""
    if not WizardService.validate_wizard_state(wizard_type='tryout'):
        flash('Session expired. Please start again.', 'warning')
        return redirect(url_for('tryout.index'))

    temp_path = WizardService.get_smart_temp_image_path()
    if not temp_path:
        flash('No image uploaded. Please upload an image first.', 'warning')
        return redirect(url_for('tryout.index'))

    wizard_data = WizardService.get_wizard_data()
    max_palette_colors = current_app.config.get('MAX_PALETTE_COLORS', 128)

    if request.method == 'POST':
        # Receive composed image from canvas
        composed_file = request.files.get('composed_image')
        if not composed_file or not composed_file.filename:
            flash('Failed to compose image. Please try again.', 'danger')
            return render_template('tryout/image.html',
                                   wizard_data=wizard_data,
                                   max_palette_colors=max_palette_colors)

        max_colors = request.form.get('max_colors', type=int) or 32
        max_colors = max(2, min(max_colors, max_palette_colors))

        # Save composed image and settings to session
        WizardService.save_smart_composed_image(composed_file)
        WizardService.update_wizard_data({
            'max_colors': max_colors,
        })

        return redirect(url_for('tryout.result'))

    return render_template('tryout/image.html',
                           wizard_data=wizard_data,
                           max_palette_colors=max_palette_colors)


# ---------------------------------------------------------------------------
# Step 3: Result page
# ---------------------------------------------------------------------------

@bp.route('/result')
def result():
    """Result page with Download PDF and Save to Projects buttons."""
    if not WizardService.validate_wizard_state(wizard_type='tryout'):
        flash('Session expired. Please start again.', 'warning')
        return redirect(url_for('tryout.index'))

    composed_path = WizardService.get_smart_composed_image_path()
    if not composed_path:
        flash('No image data. Please start again.', 'warning')
        return redirect(url_for('tryout.index'))

    wizard_data = WizardService.get_wizard_data()

    return render_template('tryout/result.html',
                           wizard_data=wizard_data)


# ---------------------------------------------------------------------------
# PDF generation (opens in new tab)
# ---------------------------------------------------------------------------

@bp.route('/pdf')
def pdf():
    """Generate and serve the PDF inline (new tab)."""
    if not WizardService.validate_wizard_state(wizard_type='tryout'):
        flash('Session expired. Please start again.', 'warning')
        return redirect(url_for('tryout.index'))

    composed_path = WizardService.get_smart_composed_image_path()
    if not composed_path:
        flash('No image data. Please start again.', 'warning')
        return redirect(url_for('tryout.index'))

    wizard_data = WizardService.get_wizard_data()
    max_colors = wizard_data.get('max_colors', 32)
    render_mode_value = request.args.get('render_mode', 'symbol_color')

    try:
        pdf_bytes = _generate_tryout_pdf(
            wizard_data, composed_path, max_colors, render_mode_value,
        )
    except Exception:
        logger.exception('Error generating tryout PDF')
        flash('Error generating PDF. Please try again.', 'danger')
        return redirect(url_for('tryout.result'))

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = (
        'inline; filename="cross-stitch-pattern.pdf"; '
        "filename*=UTF-8''cross-stitch-pattern.pdf"
    )
    return response


# ---------------------------------------------------------------------------
# Temp image serving (for positioner canvas)
# ---------------------------------------------------------------------------

@bp.route('/temp-image')
def temp_image():
    """Serve the uploaded temp image for the positioner canvas."""
    from flask import send_file

    if not WizardService.validate_wizard_state(wizard_type='tryout'):
        return '', 404

    temp_path = WizardService.get_smart_temp_image_path()
    if not temp_path:
        return '', 404

    mime = mimetypes.guess_type(str(temp_path))[0] or 'image/jpeg'
    return send_file(str(temp_path), mimetype=mime, as_attachment=False)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _generate_tryout_pdf(wizard_data: dict, composed_path, max_colors: int,
                         render_mode_value: str) -> bytes:
    """Run smart image conversion and generate PDF entirely in memory."""
    from stitch.models.color import ColorVendor
    from stitch.services.color_matcher import ColorMatcher
    from stitch.services.pattern_pdf_service import PatternPDFService
    from stitch.services.project_service import ProjectService
    from stitch.services.smart_image_service import SmartImageService

    width = wizard_data['width']
    height = wizard_data['height']

    # Mock project for SmartImageService (needs .width, .height)
    mock_project = types.SimpleNamespace(
        id='tryout',
        name='Cross-Stitch Pattern',
        width=width,
        height=height,
        description='',
        created_at=datetime.utcnow(),
    )

    # Convert image to stitches using smart pipeline with sensible defaults
    result = SmartImageService.convert_image_to_stitches(
        mock_project, composed_path, max_colors,
        vendor=ColorVendor.DMC,
        backstitch=False,
        edge_detail='medium',
        despeckle='light',
        dithering='off',
        sharpness='medium',
        remove_bg=False,
        smoothing=50,
    )

    # Build palette and a color-ID → palette-index map.
    # SmartImageService returns DB-format data ({color: uuid, stitch: type})
    # but the renderer expects assembled-state format ({paletteIndex, stitchType}).
    new_colors = result.get('newColors', [])
    palette = []
    color_id_to_index = {}
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
        color_id_to_index[color['id']] = idx

    # Convert layer cells from DB format to assembled-state format
    layer_data = result.get('layer', {})

    raw_cells = layer_data.get('cells', {})
    converted_cells = {}
    for cell_key, cell_value in raw_cells.items():
        stitches = cell_value if isinstance(cell_value, list) else [cell_value]
        converted = []
        for stitch in stitches:
            palette_idx = color_id_to_index.get(stitch.get('color', ''))
            if palette_idx is not None:
                converted.append({
                    'paletteIndex': palette_idx,
                    'stitchType': stitch.get('stitch', 'full'),
                })
        if converted:
            converted_cells[cell_key] = converted

    # Convert layer paths from DB format to assembled-state format
    raw_paths = layer_data.get('paths', [])
    converted_paths = []
    for path_entry in raw_paths:
        palette_idx = color_id_to_index.get(path_entry.get('color', ''))
        if palette_idx is not None:
            converted_paths.append({
                'startX': path_entry['startX'],
                'startY': path_entry['startY'],
                'endX': path_entry['endX'],
                'endY': path_entry['endY'],
                'paletteIndex': palette_idx,
                'stitchType': path_entry.get('stitch', 'line'),
            })

    layer_data['cells'] = converted_cells
    layer_data['paths'] = converted_paths

    # Build state dict
    state = {
        'palette': palette,
        'layers': [layer_data],
        'activeLayerId': layer_data.get('id'),
        'properties': {
            'majorGridInterval': 5,
            'showGridNumbers': False,
            'defaultStitchType': 'full',
        },
    }

    # Resolve render mode flags
    if render_mode_value == 'bw_symbols':
        render_mode = {
            'show_color': False,
            'show_stitch': False,
            'show_symbol': True,
            'show_line': True,
        }
    else:
        # symbol_color (default)
        render_mode = {
            'show_color': True,
            'show_stitch': False,
            'show_symbol': True,
            'show_line': True,
        }

    # Get logo path
    logo_path = os.path.join(
        current_app.root_path, 'static', 'img', 'logo_small.jpeg'
    )
    if not os.path.exists(logo_path):
        logo_path = None

    return PatternPDFService.generate_pdf(
        mock_project, logo_path, render_mode=render_mode, state=state,
    )
