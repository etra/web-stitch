"""State API routes - save and load project state"""
from flask import request, session, jsonify

from stitch.blueprints.editor import bp
from stitch.blueprints.auth.routes import login_required
from stitch.services.project_service import ProjectService


@bp.route('/<project_id>/api/state', methods=['GET'])
@login_required
def get_state(project_id):
    """
    Get project state.

    Returns full project data including state for editor initialization.
    """
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    return jsonify({
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'width': project.width,
        'height': project.height,
        'clothColor': project.cloth_color,
        'state': project.state
    })


@bp.route('/<project_id>/api/state', methods=['POST'])
@login_required
def save_state(project_id):
    """
    Save project state.

    Accepts JSON body with 'state' object containing layers, palette, etc.
    """
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    try:
        data = request.get_json()
        state = data.get('state')

        if not state:
            return jsonify({'error': 'No state provided'}), 400

        ProjectService.update_project(
            project_id=project_id,
            user_id=user_id,
            state=state
        )

        return jsonify({
            'success': True,
            'message': 'Project saved successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
