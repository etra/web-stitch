from flask import render_template

from stitch.blueprints.guide import bp


@bp.route('/')
def index():
    """Guide hub — links to all topics."""
    return render_template('guide/index.html')


@bp.route('/create-project')
def create_project():
    """How to create a project."""
    return render_template('guide/create-project.html')


@bp.route('/editor')
def editor():
    """Introduction to the editor."""
    return render_template('guide/editor.html')


@bp.route('/layers')
def layers():
    """Working with layers & image conversion."""
    return render_template('guide/layers.html')


@bp.route('/print')
def print_pattern():
    """Printing patterns & PDF export."""
    return render_template('guide/print.html')
