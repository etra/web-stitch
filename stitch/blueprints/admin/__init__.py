from flask import Blueprint

bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/admin',
    template_folder='templates',
)

from stitch.blueprints.admin import routes  # noqa: E402,F401
