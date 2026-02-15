import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Secret key for session management
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database URI
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:pass@localhost/webstitch'
    )
    print(SQLALCHEMY_DATABASE_URI)
    # Disable modification tracking (saves resources)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool settings to prevent "server closed connection" errors
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'max_overflow': 20,
        'connect_args': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'
        }
    }

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Palette color limit per project
    MAX_PALETTE_COLORS = 128

    # Major grid line interval (every N stitches)
    MAJOR_GRID_INTERVAL = 5
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')

    # OAuth configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    FACEBOOK_CLIENT_ID = os.getenv('FACEBOOK_CLIENT_ID')
    FACEBOOK_CLIENT_SECRET = os.getenv('FACEBOOK_CLIENT_SECRET')
    DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
    DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')

    # Mail configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'no-reply@ourstitch.com')

    # Magic link token expiration (seconds)
    MAGIC_LINK_EXPIRATION = 900  # 15 minutes


class DevelopmentConfig(Config):
    """Development configuration"""
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log all SQL statements
    SESSION_COOKIE_SECURE = False  # Allow HTTP for local development

    # Suppress actual email sending in development
    MAIL_SUPPRESS_SEND = os.getenv('MAIL_SUPPRESS_SEND', 'true').lower() == 'true'


class ProductionConfig(Config):
    """Production configuration"""
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING')
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS in production
