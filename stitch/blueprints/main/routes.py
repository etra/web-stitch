"""Main application routes."""
import math
from flask import render_template, send_from_directory, current_app, request, session

from stitch.blueprints.main import bp
from stitch.utils.decorators import deprecated
from stitch.services.seo_service import SEOService
from stitch.services.community_service import CommunityService
from stitch.services.vote_service import VoteService


@bp.route('/')
def index():
    """Home page with community pattern sections."""
    seo = SEOService.get_index_metadata()

    latest_patterns = CommunityService.get_latest_patterns(6)
    best_patterns = CommunityService.get_best_patterns(6)

    # Bulk-fetch user votes if logged in
    user_votes = {}
    user_id = session.get('user_id')
    if user_id:
        all_ids = list({p.id for p in latest_patterns + best_patterns})
        user_votes = VoteService.get_user_votes_bulk(all_ids, user_id)

    return render_template('main/index.html',
                           seo=seo,
                           latest_patterns=latest_patterns,
                           best_patterns=best_patterns,
                           user_votes=user_votes)


@bp.route('/patterns')
def patterns():
    """Browse community patterns with pagination and sorting."""
    sort = request.args.get('sort', 'latest')
    if sort not in ('latest', 'popular'):
        sort = 'latest'

    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    per_page = 12
    projects, total = CommunityService.get_patterns_page(sort, page, per_page)
    total_pages = math.ceil(total / per_page) if total > 0 else 1

    # Bulk-fetch user votes if logged in
    user_votes = {}
    user_id = session.get('user_id')
    if user_id:
        project_ids = [p.id for p in projects]
        user_votes = VoteService.get_user_votes_bulk(project_ids, user_id)

    seo = SEOService.get_page_metadata(
        page_title="Community Patterns",
        description="Browse cross-stitch patterns shared by the OurStitch community.",
        canonical_path="/patterns"
    )

    return render_template('main/patterns.html',
                           seo=seo,
                           patterns=projects,
                           total=total,
                           sort=sort,
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages,
                           user_votes=user_votes)


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
@deprecated("Unreferenced; each blueprint serves its own static files")
def serve_resource(filepath):
    """Serve uploaded files (images, thumbnails)."""
    uploads_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    return send_from_directory(uploads_dir, filepath)
