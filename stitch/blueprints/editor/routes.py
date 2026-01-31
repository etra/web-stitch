"""Editor page routes"""
from flask import render_template, redirect, url_for, flash, session

from stitch.blueprints.editor import bp
from stitch.blueprints.auth.routes import login_required
from stitch.services.project_service import ProjectService


@bp.route('/<project_id>')
@login_required
def canvas(project_id):
    """
    Canvas editor page.

    Loads the full editor interface with project data for JavaScript.
    """
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects.list'))

    project_data = {
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'width': project.width,
        'height': project.height,
        'clothColor': project.cloth_color,
        'state': project.state
    }

    return render_template('editor/canvas.html', project=project, project_data=project_data)


@bp.route('/<project_id>/test')
@login_required
def test_view(project_id):
    """
    Test view for the editor.

    A simplified view for testing purposes.
    """
    user_id = session.get('user_id')
    project = ProjectService.get_project(project_id, user_id)

    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('projects.list'))

    return render_template('editor/test.html', project=project)