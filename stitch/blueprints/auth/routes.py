import secrets
from functools import wraps
from urllib.parse import urlencode

import jwt as pyjwt
from jwt import PyJWKClient
from flask import request, session, render_template, redirect, url_for, flash, current_app
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from stitch.blueprints.auth import bp
from stitch.services.auth_service import AuthService
from stitch.services.email_service import EmailService
from stitch.oauth import oauth

APPLE_JWKS_URL = 'https://appleid.apple.com/auth/keys'


def _redirect_after_login():
    """Redirect to the stored 'next' URL (if any) or the projects list."""
    next_url = session.pop('next', None)
    if next_url:
        return redirect(next_url)
    return _redirect_after_login()


def login_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin privileges for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login page with magic link authentication

    GET: Display login form
    POST: Send magic link email to user
    """
    # If already logged in, redirect to projects
    if 'user_id' in session:
        return _redirect_after_login()

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('auth/login.html')

        try:
            # Find or create user
            user = AuthService.find_or_create_user(email=email)

            # Generate magic link
            token = AuthService.generate_magic_token(email)
            magic_link = url_for('auth.verify_magic_link', token=token, _external=True)

            # Send magic link email
            EmailService.send_magic_link(user, magic_link)

            # Log the link in debug mode for dev testing
            current_app.logger.debug(f'Magic link for {email}: {magic_link}')

            return render_template('auth/check_email.html', email=email)

        except Exception as e:
            current_app.logger.error(f'Magic link error: {e}')
            flash('An error occurred. Please try again.', 'danger')
            return render_template('auth/login.html')

    # GET request - show login form
    return render_template('auth/login.html')


@bp.route('/verify/<token>')
def verify_magic_link(token):
    """
    Verify magic link token and log the user in

    GET: Verify token, set session, redirect to projects
    """
    email = AuthService.verify_magic_token(token)

    if not email:
        flash('This link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.login'))

    user = AuthService.find_or_create_user(email=email)

    session.permanent = True
    session['user_id'] = user.id
    session['user_email'] = user.email
    session['is_admin'] = user.is_admin

    flash(f'Welcome, {user.email}!', 'success')
    return _redirect_after_login()


@bp.route('/logout')
def logout():
    """
    Logout current user
    """
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('is_admin', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


# --- Google OAuth ---

@bp.route('/login/google')
def login_google():
    """Redirect to Google consent screen"""
    google = oauth.create_client('google')
    if google is None:
        flash('Google login is not configured.', 'danger')
        return redirect(url_for('auth.login'))
    redirect_uri = url_for('auth.callback_google', _external=True)
    return google.authorize_redirect(redirect_uri)


@bp.route('/callback/google')
def callback_google():
    """Handle Google OAuth callback"""
    google = oauth.create_client('google')
    if google is None:
        flash('Google login is not configured.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        token = google.authorize_access_token()
        userinfo = token.get('userinfo')
        if not userinfo:
            flash('Could not retrieve account information from Google.', 'danger')
            return redirect(url_for('auth.login'))

        if not userinfo.get('email_verified'):
            flash('Your Google email is not verified.', 'danger')
            return redirect(url_for('auth.login'))

        email = userinfo['email']
        user = AuthService.find_or_create_user(email=email)

        session.permanent = True
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['is_admin'] = user.is_admin

        flash(f'Welcome, {user.email}!', 'success')
        return _redirect_after_login()

    except Exception as e:
        current_app.logger.error(f'Google OAuth error: {e}')
        flash('An error occurred during Google sign-in. Please try again.', 'danger')
        return redirect(url_for('auth.login'))


# --- Google One Tap ---

@bp.route('/callback/google-one-tap', methods=['POST'])
def callback_google_one_tap():
    """Handle Google One Tap credential callback (form POST from GIS library)"""
    # Verify CSRF double-submit cookie
    csrf_token_cookie = request.cookies.get('g_csrf_token')
    csrf_token_body = request.form.get('g_csrf_token')
    if not csrf_token_cookie or not csrf_token_body or csrf_token_cookie != csrf_token_body:
        flash('Sign-in failed: CSRF verification error.', 'danger')
        return redirect(url_for('auth.login'))

    credential = request.form.get('credential')
    if not credential:
        flash('Sign-in failed: no credential received.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        client_id = current_app.config.get('GOOGLE_CLIENT_ID')
        idinfo = id_token.verify_oauth2_token(
            credential, google_requests.Request(), client_id
        )

        if not idinfo.get('email_verified'):
            flash('Your Google email is not verified.', 'danger')
            return redirect(url_for('auth.login'))

        email = idinfo['email']
        user = AuthService.find_or_create_user(email=email)

        session.permanent = True
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['is_admin'] = user.is_admin

        flash(f'Welcome, {user.email}!', 'success')
        return _redirect_after_login()

    except Exception as e:
        current_app.logger.error(f'Google One Tap error: {e}')
        flash('An error occurred during Google sign-in. Please try again.', 'danger')
        return redirect(url_for('auth.login'))


# --- Apple Sign In ---

@bp.route('/login/apple')
def login_apple():
    """Redirect to Apple Sign In authorization page"""
    client_id = current_app.config.get('APPLE_CLIENT_ID')
    if not client_id:
        flash('Apple sign-in is not configured.', 'danger')
        return redirect(url_for('auth.login'))

    state = secrets.token_urlsafe(32)
    session['apple_auth_state'] = state

    redirect_uri = url_for('auth.callback_apple', _external=True)
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code id_token',
        'scope': 'email',
        'response_mode': 'form_post',
        'state': state,
    }
    apple_auth_url = f'https://appleid.apple.com/auth/authorize?{urlencode(params)}'
    return redirect(apple_auth_url)


@bp.route('/callback/apple', methods=['POST'])
def callback_apple():
    """Handle Apple Sign In callback (form POST from Apple with id_token)"""
    # Verify state matches what we stored in session
    state = request.form.get('state')
    expected_state = session.pop('apple_auth_state', None)
    if not state or not expected_state or state != expected_state:
        flash('Sign-in failed: state verification error.', 'danger')
        return redirect(url_for('auth.login'))

    id_token_str = request.form.get('id_token')
    if not id_token_str:
        flash('Sign-in failed: no identity token received.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        client_id = current_app.config.get('APPLE_CLIENT_ID')

        jwks_client = PyJWKClient(APPLE_JWKS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(id_token_str)
        payload = pyjwt.decode(
            id_token_str,
            signing_key.key,
            algorithms=['RS256'],
            audience=client_id,
            issuer='https://appleid.apple.com',
        )

        # Apple's email_verified can be a string "true" or boolean true
        email_verified = payload.get('email_verified')
        if email_verified not in (True, 'true'):
            flash('Your Apple email is not verified.', 'danger')
            return redirect(url_for('auth.login'))

        email = payload.get('email')
        if not email:
            flash('Could not retrieve email from Apple.', 'danger')
            return redirect(url_for('auth.login'))

        user = AuthService.find_or_create_user(email=email)

        session.permanent = True
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['is_admin'] = user.is_admin

        flash(f'Welcome, {user.email}!', 'success')
        return _redirect_after_login()

    except Exception as e:
        current_app.logger.error(f'Apple Sign In error: {e}')
        flash('An error occurred during Apple sign-in. Please try again.', 'danger')
        return redirect(url_for('auth.login'))


# --- Facebook OAuth ---

@bp.route('/login/facebook')
def login_facebook():
    """Redirect to Facebook consent screen"""
    facebook = oauth.create_client('facebook')
    if facebook is None:
        flash('Facebook login is not configured.', 'danger')
        return redirect(url_for('auth.login'))
    redirect_uri = url_for('auth.callback_facebook', _external=True)
    return facebook.authorize_redirect(redirect_uri)


@bp.route('/callback/facebook')
def callback_facebook():
    """Handle Facebook OAuth callback"""
    facebook = oauth.create_client('facebook')
    if facebook is None:
        flash('Facebook login is not configured.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        token = facebook.authorize_access_token()
        resp = facebook.get('me?fields=email')
        profile = resp.json()

        email = profile.get('email')
        if not email:
            flash('Could not retrieve email from Facebook. Please ensure your Facebook account has a verified email.', 'danger')
            return redirect(url_for('auth.login'))

        user = AuthService.find_or_create_user(email=email)

        session.permanent = True
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['is_admin'] = user.is_admin

        flash(f'Welcome, {user.email}!', 'success')
        return _redirect_after_login()

    except Exception as e:
        current_app.logger.error(f'Facebook OAuth error: {e}')
        flash('An error occurred during Facebook sign-in. Please try again.', 'danger')
        return redirect(url_for('auth.login'))


# --- Discord OAuth ---

@bp.route('/login/discord')
def login_discord():
    """Redirect to Discord consent screen"""
    discord = oauth.create_client('discord')
    if discord is None:
        flash('Discord login is not configured.', 'danger')
        return redirect(url_for('auth.login'))
    redirect_uri = url_for('auth.callback_discord', _external=True)
    return discord.authorize_redirect(redirect_uri)


@bp.route('/callback/discord')
def callback_discord():
    """Handle Discord OAuth callback"""
    discord = oauth.create_client('discord')
    if discord is None:
        flash('Discord login is not configured.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        token = discord.authorize_access_token()
        resp = discord.get('users/@me')
        profile = resp.json()

        email = profile.get('email')
        verified = profile.get('verified')
        if not email or not verified:
            flash('Could not retrieve a verified email from Discord. Please ensure your Discord account has a verified email.', 'danger')
            return redirect(url_for('auth.login'))

        user = AuthService.find_or_create_user(email=email)

        session.permanent = True
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['is_admin'] = user.is_admin

        flash(f'Welcome, {user.email}!', 'success')
        return _redirect_after_login()

    except Exception as e:
        current_app.logger.error(f'Discord OAuth error: {e}')
        flash('An error occurred during Discord sign-in. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
