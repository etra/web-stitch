"""API routes for tag data."""
from flask import jsonify, request

from stitch.blueprints.api import bp
from stitch.blueprints.api.tag.schema import TagResponse, TagsListResponse
from stitch.services.tag_service import TagService


@bp.get('/tags')
def search_tags():
    """Search tags for autocomplete, or return all tags if no query."""
    query = request.args.get('q', '').strip()
    if len(query) < 1:
        tags = TagService.get_all_tags()
    else:
        tags = TagService.search_tags(query)

    response = TagsListResponse(
        tags=[TagResponse(id=t.id, name=t.name) for t in tags]
    )
    return jsonify(response.model_dump())
