"""Main application routes."""
import math
from flask import render_template, send_from_directory, current_app, request, session, Response

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


@bp.route('/robots.txt')
def robots():
    """Serve robots.txt for search engine crawlers."""
    site_url = SEOService.SITE_URL
    lines = [
        'User-agent: *',
        'Allow: /',
        '',
        'Disallow: /auth/',
        'Disallow: /admin/',
        'Disallow: /api/',
        'Disallow: /projects/',
        '',
        f'Sitemap: {site_url}/sitemap.xml',
    ]
    return Response('\n'.join(lines), mimetype='text/plain')


@bp.route('/sitemap.xml')
def sitemap_index():
    """Sitemap index pointing to sub-sitemaps."""
    site_url = SEOService.SITE_URL
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <sitemap><loc>{site_url}/sitemap-pages.xml</loc></sitemap>\n'
        f'  <sitemap><loc>{site_url}/sitemap-patterns.xml</loc></sitemap>\n'
        '</sitemapindex>'
    )
    return Response(xml, mimetype='application/xml')


@bp.route('/sitemap-pages.xml')
def sitemap_pages():
    """Sitemap for static pages."""
    site_url = SEOService.SITE_URL

    static_pages = [
        ('/',                     'weekly',  '1.0'),
        ('/patterns',             'daily',   '0.9'),
        ('/guide/',               'monthly', '0.6'),
        ('/guide/create-project', 'monthly', '0.6'),
        ('/guide/smart-image',    'monthly', '0.7'),
        ('/guide/editor',         'monthly', '0.6'),
        ('/guide/layers',         'monthly', '0.6'),
        ('/guide/print',          'monthly', '0.6'),
        ('/privacy',              'yearly',  '0.3'),
        ('/imprint',              'yearly',  '0.3'),
    ]

    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for path, changefreq, priority in static_pages:
        xml_parts.append(
            f'  <url>'
            f'<loc>{site_url}{path}</loc>'
            f'<changefreq>{changefreq}</changefreq>'
            f'<priority>{priority}</priority>'
            f'</url>'
        )

    xml_parts.append('</urlset>')
    return Response('\n'.join(xml_parts), mimetype='application/xml')


@bp.route('/sitemap-patterns.xml')
def sitemap_patterns():
    """Sitemap for public pattern pages with image metadata."""
    from stitch.models.project import Project, ProjectStatus

    site_url = SEOService.SITE_URL

    public_projects = (
        Project.query
        .filter(Project.status == ProjectStatus.PUBLIC)
        .with_entities(Project.id, Project.name, Project.updated_at)
        .order_by(Project.updated_at.desc())
        .all()
    )

    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
        ' xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]

    for project_id, name, updated_at in public_projects:
        lastmod = updated_at.strftime('%Y-%m-%d') if updated_at else ''
        # Escape XML special characters in project name
        safe_name = (name or '').replace('&', '&amp;').replace('<', '&lt;').replace('"', '&quot;')
        img_url = f'{site_url}/projects/{project_id}/thumbnail-fill'

        xml_parts.append(
            f'  <url>'
            f'<loc>{site_url}/print/{project_id}</loc>'
            + (f'<lastmod>{lastmod}</lastmod>' if lastmod else '')
            + f'<changefreq>monthly</changefreq>'
            f'<priority>0.7</priority>'
            f'<image:image>'
            f'<image:loc>{img_url}</image:loc>'
            f'<image:title>{safe_name} — Free Cross-Stitch Pattern</image:title>'
            f'</image:image>'
            f'</url>'
        )

    xml_parts.append('</urlset>')
    return Response('\n'.join(xml_parts), mimetype='application/xml')
