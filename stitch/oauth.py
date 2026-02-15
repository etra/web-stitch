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

    # Discord — manual endpoint configuration
    if app.config.get('DISCORD_CLIENT_ID'):
        oauth.register(
            name='discord',
            client_id=app.config['DISCORD_CLIENT_ID'],
            client_secret=app.config['DISCORD_CLIENT_SECRET'],
            authorize_url='https://discord.com/oauth2/authorize',
            access_token_url='https://discord.com/api/oauth2/token',
            api_base_url='https://discord.com/api/v10/',
            client_kwargs={'scope': 'identify email'},
            token_endpoint_auth_method='client_secret_post',
        )
