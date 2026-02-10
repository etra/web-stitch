"""API routes for stitch type data."""
from flask import jsonify

from stitch.blueprints.api import bp
from stitch.blueprints.api.stitch.schema import StitchesListResponse
from stitch.services.stitch_service import StitchService


@bp.get('/stitches')
def get_stitches():
    """Get all available stitch types."""
    stitches = StitchService.get_all_stitches()
    response = StitchesListResponse(stitches=stitches)
    return jsonify(response.model_dump())
