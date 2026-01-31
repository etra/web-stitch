from flask import Blueprint

bp = Blueprint('images', __name__, url_prefix='/images', template_folder='templates')

from stitch.blueprints.images import routes
