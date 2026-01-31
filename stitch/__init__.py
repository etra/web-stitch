from flask import Flask
from stitch.config import DevelopmentConfig, ProductionConfig
from stitch.database import db, init_db
from stitch.services.email_service import init_mail
from dotenv import load_dotenv
import os


def create_app():
    """Create and configure Flask application"""
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)

    # Load configuration
    if os.getenv('FLASK_ENV') == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # Initialize database
    init_db(app)

    # Initialize mail
    init_mail(app)

    # Register CLI commands
    from stitch import cli
    cli.register_commands(app)

    # Register blueprints
    from stitch.blueprints.main import bp as main_bp
    from stitch.blueprints.api import bp as api_bp
    from stitch.blueprints.auth import bp as auth_bp
    from stitch.blueprints.images import bp as images_bp
    from stitch.blueprints.projects import bp as projects_bp
    from stitch.blueprints.editor import bp as editor_bp
    from stitch.blueprints.pattern import bp as pattern_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(images_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(editor_bp)
    app.register_blueprint(pattern_bp)

    return app
