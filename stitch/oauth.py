from authlib.integrations.flask_client import OAuth

oauth = OAuth()


def init_oauth(app):
    """Initialize OAuth with the Flask app and register providers."""
    oauth.init_app(app)

    # Google — OpenID Connect with auto-discovery
    if app.config.get('GOOGLE_CLIENT_ID'):
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'},
        )

    # Facebook — manual endpoint configuration
    if app.config.get('FACEBOOK_CLIENT_ID'):
        oauth.register(
            name='facebook',
            client_id=app.config['FACEBOOK_CLIENT_ID'],
            client_secret=app.config['FACEBOOK_CLIENT_SECRET'],
            authorize_url='https://www.facebook.com/v19.0/dialog/oauth',
            access_token_url='https://graph.facebook.com/v19.0/oauth/access_token',
            api_base_url='https://graph.facebook.com/v19.0/',
            client_kwargs={'scope': 'email public_profile'},
        )
