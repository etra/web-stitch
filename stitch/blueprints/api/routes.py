"""API routes for data endpoints."""
from flask import jsonify

from stitch.blueprints.api import bp
from stitch.services.vendor_palette_service import VendorPaletteService
from stitch.services.stitch_service import StitchService


@bp.get('/colors')
def get_colors():
    """Get all available thread colors from all palettes."""
    colors = VendorPaletteService.get_all_colors()
    return jsonify({'colors': colors})

@bp.get('/stitches')
def get_stitches():
    """Get all available stitch types."""
    stitches = StitchService.get_all_stitches()
    return jsonify({'stitches': stitches})