"""Layer API routes - layer management operations"""
from flask import request, session, jsonify

from stitch.blueprints.editor import bp
from stitch.blueprints.auth.routes import login_required
from stitch.services.project_service import ProjectService


# Placeholder for future layer operations
# These will handle:
# - Add layer from uploaded image
# - Layer reordering
# - Layer merging
# - etc.
