"""Main application routes."""
from flask import render_template, send_from_directory, current_app

from stitch.blueprints.main import bp
from stitch.services.seo_service import SEOService


@bp.route('/')
def index():
    """Home page."""
    seo = SEOService.get_index_metadata()
    return render_template('main/index.html', seo=seo)


@bp.route('/privacy')
def privacy():
    """Privacy policy page."""
    seo = SEOService.get_page_metadata(
        page_title="Privacy Policy",
        description="Learn how OurStitch collects, uses, and protects your personal information.",
        canonical_path="/privacy"
    )
    return render_template('main/privacy.html', seo=seo)


@bp.route('/imprint')
def imprint():
    """Imprint / legal notice page."""
    seo = SEOService.get_page_metadata(
        page_title="Imprint",
        description="Legal information and contact details for OurStitch.",
        canonical_path="/imprint"
    )
    return render_template('main/imprint.html', seo=seo)


@bp.route('/resource/<path:filepath>')
def serve_resource(filepath):
    """Serve uploaded files (images, thumbnails)."""
    uploads_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    return send_from_directory(uploads_dir, filepath)
