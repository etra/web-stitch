from flask import Blueprint

bp = Blueprint(
    'tryout',
    __name__,
    url_prefix='/tryout',
    template_folder='templates',
)

from stitch.blueprints.tryout import routes  # noqa: E402,F401
