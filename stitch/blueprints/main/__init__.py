from flask import Blueprint

bp = Blueprint(
    'main',
    __name__,
    url_prefix=None,
    template_folder='templates',
)

from stitch.blueprints.main import routes  # noqa: E402,F401
