from flask import Flask
from stitch.config import DevelopmentConfig, ProductionConfig
from stitch.database import db, init_db
from stitch.services.email_service import init_mail
from stitch.oauth import init_oauth
from stitch.utils.logging import init_logging
from dotenv import load_dotenv
import os


def create_app(config_name=None):
    """Create and configure Flask application"""
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)

    # Load configuration
    if config_name == 'production':
        app.config.from_object(ProductionConfig)

        # Trust X-Forwarded-* headers from the load balancer so that
        # url_for(_external=True) generates https:// URLs.
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    else:
        app.config.from_object(DevelopmentConfig)

    # Initialize logging (before other init calls)
    init_logging(app)

    # Initialize database
    init_db(app)

    # Initialize mail
    init_mail(app)

    # Initialize OAuth
    init_oauth(app)

    # Register CLI commands
    from stitch import cli
    cli.register_commands(app)

    # Register blueprints
    from stitch.blueprints.main import bp as main_bp
    from stitch.blueprints.api import bp as api_bp
    from stitch.blueprints.auth import bp as auth_bp
    from stitch.blueprints.projects import bp as projects_bp
    from stitch.blueprints.print import bp as print_bp
    from stitch.blueprints.guide import bp as guide_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(print_bp)
    app.register_blueprint(guide_bp)

    return app
