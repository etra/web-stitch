"""Editor blueprint - canvas editor and related APIs"""
from flask import Blueprint

bp = Blueprint(
    'editor',
    __name__,
    url_prefix='/editor',
    template_folder='templates',
    static_folder='static',
    static_url_path='/editor/static'
)

# Page routes
from stitch.blueprints.editor import routes  # noqa: E402,F401

# API routes
from stitch.blueprints.editor import api  # noqa: E402,F401
