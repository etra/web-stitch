from flask import Blueprint

bp = Blueprint(
    'guide',
    __name__,
    url_prefix='/guide',
    template_folder='templates',
    static_folder='static',
)

from stitch.blueprints.guide import routes  # noqa: E402,F401
