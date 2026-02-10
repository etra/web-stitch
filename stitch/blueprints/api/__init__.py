from flask import Blueprint

bp = Blueprint(
    'api',
    __name__,
    url_prefix='/api',
)

from stitch.blueprints.api.color import router as color_router  # noqa: E402,F401
from stitch.blueprints.api.stitch import router as stitch_router  # noqa: E402,F401
from stitch.blueprints.api.project import router as project_router  # noqa: E402,F401
from stitch.blueprints.api.tag import router as tag_router  # noqa: E402,F401
from stitch.blueprints.api.vote import router as vote_router  # noqa: E402,F401
