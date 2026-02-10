"""API routes for project voting."""
from flask import jsonify, request, session
from pydantic import ValidationError

from stitch.blueprints.api import bp
from stitch.blueprints.api.vote.schema import VoteRequest, VoteResponse
from stitch.services.vote_service import VoteService


@bp.post('/projects/<project_id>/vote')
def cast_vote(project_id):
    """Cast or change a vote on a project. Requires login."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Login required'}), 401

    try:
        body = VoteRequest(**request.get_json(force=True))
    except (ValidationError, TypeError) as e:
        return jsonify({'error': 'value must be 1 or -1'}), 400

    result = VoteService.vote(project_id, user_id, body.value)
    return jsonify(VoteResponse(**result).model_dump())


@bp.delete('/projects/<project_id>/vote')
def remove_vote(project_id):
    """Remove a vote from a project. Requires login."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Login required'}), 401

    result = VoteService.remove_vote(project_id, user_id)
    return jsonify(VoteResponse(**result).model_dump())
