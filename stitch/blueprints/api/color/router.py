"""API routes for color data."""
from flask import jsonify

from stitch.blueprints.api import bp
from stitch.blueprints.api.color.schema import (
    ColorsListResponse,
    VendorColorsListResponse,
    VendorsListResponse,
)
from stitch.models.color import ColorVendor
from stitch.services.color_service import ColorService


@bp.get('/colors')
def get_colors():
    """Get all available thread colors from all palettes."""
    colors = ColorService.get_all_colors()
    response = ColorsListResponse(colors=colors)
    return jsonify(response.model_dump())


@bp.get('/colors/vendors')
def get_vendors():
    """Get all supported vendors with color counts."""
    vendors = ColorService.get_vendors()
    response = VendorsListResponse(vendors=vendors)
    return jsonify(response.model_dump())


@bp.get('/colors/vendors/<vendor_key>')
def get_vendor_colors(vendor_key):
    """Get all colors for a specific vendor."""
    try:
        vendor = ColorVendor(vendor_key)
    except ValueError:
        return jsonify({'error': f'Unknown vendor: {vendor_key}'}), 404

    colors = ColorService.get_colors_by_vendor(vendor)
    response = VendorColorsListResponse(colors=colors)
    return jsonify(response.model_dump())
