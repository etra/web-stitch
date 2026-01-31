"""Render API routes - thumbnails and image generation"""
import io

from flask import session, send_file

from stitch.blueprints.editor import bp
from stitch.blueprints.auth.routes import login_required
from stitch.services.project_service import ProjectService


@bp.route('/<project_id>/api/thumbnail')
@login_required
def thumbnail(project_id):
    """
    Generate thumbnail preview of project canvas.

    Returns PNG image with small cell size for quick previews.
    """
    from stitch.services.pattern_renderer import PatternRenderer
    import cv2

    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        return '', 404

    try:
        thumbnail_image = PatternRenderer.render_colored_pattern(
            project.state,
            project.width,
            project.height,
            cell_size=3
        )

        success, buffer = cv2.imencode('.png', thumbnail_image)

        if not success:
            return '', 500

        return send_file(
            io.BytesIO(buffer.tobytes()),
            mimetype='image/png',
            as_attachment=False
        )

    except Exception:
        return '', 500
