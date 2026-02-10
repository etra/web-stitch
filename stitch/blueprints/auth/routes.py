from flask import request, session, render_template, redirect, url_for, flash, current_app
from stitch.blueprints.auth import bp
from stitch.services.auth_service import AuthService
from stitch.services.email_service import EmailService
from stitch.oauth import oauth
from functools import wraps


def login_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
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
        return redirect(url_for('projects.list'))

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

    flash(f'Welcome, {user.email}!', 'success')
    return redirect(url_for('projects.list'))


@bp.route('/logout')
def logout():
    """
    Logout current user
    """
    session.pop('user_id', None)
    session.pop('user_email', None)
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

        flash(f'Welcome, {user.email}!', 'success')
        return redirect(url_for('projects.list'))

    except Exception as e:
        current_app.logger.error(f'Google OAuth error: {e}')
        flash('An error occurred during Google sign-in. Please try again.', 'danger')
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

        flash(f'Welcome, {user.email}!', 'success')
        return redirect(url_for('projects.list'))

    except Exception as e:
        current_app.logger.error(f'Facebook OAuth error: {e}')
        flash('An error occurred during Facebook sign-in. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
