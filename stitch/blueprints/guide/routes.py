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


@bp.route('/smart-image')
def smart_image():
    """How to create a cross-stitch pattern from an image."""
    return render_template('guide/smart-image.html')


@bp.route('/how-smart-image-works')
def how_smart_image_works():
    """How the Smart Image AI conversion works."""
    return render_template('guide/how-smart-image-works.html')


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
