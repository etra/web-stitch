from flask import request, session, render_template, redirect, url_for, flash
from stitch.blueprints.auth import bp
from stitch.services.auth_service import AuthService
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
    Login page with email-only authentication

    GET: Display login form
    POST: Process login (finds or creates user)
    """
    # If already logged in, redirect to projects
    if 'user_id' in session:
        return redirect(url_for('projects'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('auth/login.html')

        try:
            # Find or create user (email-only authentication)
            user = AuthService.find_or_create_user(email=email)

            # Set session
            session.permanent = True
            session['user_id'] = user.id
            session['user_email'] = user.email

            flash(f'Welcome, {user.email}!', 'success')
            return redirect(url_for('projects'))

        except Exception as e:
            flash('An error occurred. Please try again.', 'danger')
            return render_template('auth/login.html')

    # GET request - show login form
    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    """
    Logout current user
    """
    session.pop('user_id', None)
    session.pop('user_email', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
