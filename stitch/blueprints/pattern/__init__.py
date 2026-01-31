from flask import Blueprint

bp = Blueprint(
    'pattern',
    __name__,
    url_prefix='/pattern',
    template_folder='templates',
    static_folder='static',
)

from stitch.blueprints.pattern import routes  # noqa: E402,F401
