from flask import Blueprint

bp = Blueprint(
    'print',
    __name__,
    url_prefix='/print',
    template_folder='templates',
    static_folder='static',
)

from stitch.blueprints.print import routes  # noqa: E402,F401
