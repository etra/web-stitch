from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize Flask-SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()


def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    migrate.init_app(app, db)

    # Import all models to ensure they're registered with SQLAlchemy
    with app.app_context():
        from stitch.models import user, project, project_layer, project_layer_cells, project_layer_paths, project_layer_image, project_color, color, tag, project_tag, project_vote
