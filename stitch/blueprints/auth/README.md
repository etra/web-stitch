# Auth Blueprint

Handles user authentication with email-only login and optional social login (Google, Facebook).

## URL Prefix

`/auth`

## Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET, POST | `/auth/login` | `login` | Login page and email authentication handler |
| GET | `/auth/logout` | `logout` | Logs out the current user |
| GET | `/auth/login/google` | `login_google` | Redirects to Google consent screen |
| GET | `/auth/callback/google` | `callback_google` | Handles Google OAuth callback |
| GET | `/auth/login/facebook` | `login_facebook` | Redirects to Facebook consent screen |
| GET | `/auth/callback/facebook` | `callback_facebook` | Handles Facebook OAuth callback |

## Route Details

### `GET /auth/login`

Displays the login form. Shows social login buttons when OAuth providers are configured, with email form always available as fallback.

**Inputs:** None

**Outputs:** HTML (`auth/login.html`)

**Side effects:** None

**Auth/session:** If already logged in, redirects to projects list

### `POST /auth/login`

Processes login form submission.

**Inputs:**
- `email` (form): User's email address (required)

**Outputs:** Redirect to projects list (success) or login form with error (failure)

**Side effects:**
- Creates user in database if not exists
- Sets session variables (`user_id`, `user_email`)
- Sets `session.permanent = True`

**Auth/session:** Writes `session.user_id`, `session.user_email`

### `GET /auth/login/google`

Redirects the user to Google's OAuth consent screen. Only available when `GOOGLE_CLIENT_ID` is configured.

**Inputs:** None

**Outputs:** Redirect to Google OAuth

**Side effects:** None

### `GET /auth/callback/google`

Handles the redirect back from Google after consent. Extracts the verified email from the ID token, finds or creates the user, and sets the session.

**Inputs:** OAuth callback query parameters (handled by Authlib)

**Outputs:** Redirect to projects list (success) or login page with error (failure)

**Side effects:**
- Creates user in database if not exists
- Sets session variables (`user_id`, `user_email`)

**Auth/session:** Writes `session.user_id`, `session.user_email`

### `GET /auth/login/facebook`

Redirects the user to Facebook's OAuth consent screen. Only available when `FACEBOOK_CLIENT_ID` is configured.

**Inputs:** None

**Outputs:** Redirect to Facebook OAuth

**Side effects:** None

### `GET /auth/callback/facebook`

Handles the redirect back from Facebook after consent. Fetches the user's email via Graph API, finds or creates the user, and sets the session.

**Inputs:** OAuth callback query parameters (handled by Authlib)

**Outputs:** Redirect to projects list (success) or login page with error (failure)

**Side effects:**
- Creates user in database if not exists
- Sets session variables (`user_id`, `user_email`)

**Auth/session:** Writes `session.user_id`, `session.user_email`

### `GET /auth/logout`

Clears session data and redirects to home page.

**Inputs:** None

**Outputs:** Redirect to home page with flash message

**Side effects:** Clears `session.user_id` and `session.user_email`

**Auth/session:** Clears session

## Utilities

### `login_required` Decorator

A decorator function that can be applied to any route to require authentication.
If the user is not logged in, they are redirected to the login page with a flash message.

```python
from stitch.blueprints.auth.routes import login_required

@bp.route('/protected')
@login_required
def protected_route():
    # Only accessible to logged-in users
    pass
```

## Session Keys

| Key | Usage |
|-----|-------|
| `user_id` | Database ID of the logged-in user |
| `user_email` | Email address of the logged-in user |

## Configuration

Social login buttons are conditionally rendered based on whether OAuth credentials are set:

| Config Key | Purpose |
|------------|---------|
| `GOOGLE_CLIENT_ID` | Enables Google login button |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret |
| `FACEBOOK_CLIENT_ID` | Enables Facebook login button |
| `FACEBOOK_CLIENT_SECRET` | Facebook OAuth secret |

When no OAuth credentials are configured, the login page shows only the email form.

## Static Assets

None - this blueprint uses global static assets only.
