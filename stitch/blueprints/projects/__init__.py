from flask import Blueprint

bp = Blueprint(
    'projects',
    __name__,
    url_prefix='/projects',
    template_folder='templates',
    static_folder='static',
)

from stitch.blueprints.projects import routes  # noqa: E402,F401
