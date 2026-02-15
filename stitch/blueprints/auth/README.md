# Auth Blueprint

Handles user authentication with magic link email verification and optional social login (Google, Apple, Facebook, Discord).

## URL Prefix

`/auth`

## Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET, POST | `/auth/login` | `login` | Login page; POST sends magic link email |
| GET | `/auth/verify/<token>` | `verify_magic_link` | Verifies magic link token and logs user in |
| GET | `/auth/logout` | `logout` | Logs out the current user |
| GET | `/auth/login/google` | `login_google` | Redirects to Google consent screen |
| GET | `/auth/callback/google` | `callback_google` | Handles Google OAuth callback |
| POST | `/auth/callback/google-one-tap` | `callback_google_one_tap` | Handles Google One Tap credential POST |
| GET | `/auth/login/apple` | `login_apple` | Redirects to Apple Sign In |
| POST | `/auth/callback/apple` | `callback_apple` | Handles Apple Sign In callback POST |
| GET | `/auth/login/facebook` | `login_facebook` | Redirects to Facebook consent screen |
| GET | `/auth/callback/facebook` | `callback_facebook` | Handles Facebook OAuth callback |
| GET | `/auth/login/discord` | `login_discord` | Redirects to Discord consent screen |
| GET | `/auth/callback/discord` | `callback_discord` | Handles Discord OAuth callback |

## Route Details

### `GET /auth/login`

Displays the login form. Shows social login buttons when OAuth providers are configured, with email form always available as fallback.

**Inputs:** None

**Outputs:** HTML (`auth/login.html`)

**Side effects:** None

**Auth/session:** If already logged in, redirects to projects list

### `POST /auth/login`

Sends a magic link email for authentication.

**Inputs:**
- `email` (form): User's email address (required)

**Outputs:** Renders `auth/check_email.html` (success) or login form with error (failure)

**Side effects:**
- Creates user in database if not exists
- Generates a signed token (15-min expiry) and sends magic link email
- In debug mode, logs the magic link URL to the console

**Auth/session:** No session changes (login completes via `/auth/verify/<token>`)

### `GET /auth/verify/<token>`

Verifies a magic link token and logs the user in.

**Inputs:**
- `token` (URL path): Signed URL-safe token containing user email

**Outputs:** Redirect to projects list (valid token) or login page with error (invalid/expired)

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

### `POST /auth/callback/google-one-tap`

Handles the Google One Tap credential POST. Google's Identity Services library auto-submits a form POST with `credential` (JWT) and `g_csrf_token` fields. The route verifies the CSRF double-submit cookie, validates the JWT against Google's public keys, extracts the email, and creates a session.

**Inputs:**
- `credential` (form): Google ID token JWT
- `g_csrf_token` (form): CSRF token (must match `g_csrf_token` cookie)

**Outputs:** Redirect to projects list (success) or login page with error (failure)

**Side effects:**
- Creates user in database if not exists
- Sets session variables (`user_id`, `user_email`, `is_admin`)
- Sets `session.permanent = True`

**Auth/session:** Writes `session.user_id`, `session.user_email`, `session.is_admin`

### `GET /auth/login/apple`

Generates a random `state` token (stored in session for CSRF), then redirects the user to Apple's authorization page (`https://appleid.apple.com/auth/authorize`) with `response_mode=form_post`. Only available when `APPLE_CLIENT_ID` is configured.

**Inputs:** None

**Outputs:** Redirect to Apple Sign In

**Side effects:** Stores `apple_auth_state` in session

### `POST /auth/callback/apple`

Handles the form POST from Apple after Sign In. Verifies the `state` parameter against the session, then decodes and validates the `id_token` JWT using Apple's JWKS (`https://appleid.apple.com/auth/keys`). Extracts the email, finds or creates the user, and sets the session.

**Inputs:**
- `id_token` (form): Apple identity token JWT
- `code` (form): Authorization code (present but unused)
- `state` (form): CSRF state token (must match `session['apple_auth_state']`)

**Outputs:** Redirect to projects list (success) or login page with error (failure)

**Side effects:**
- Creates user in database if not exists
- Sets session variables (`user_id`, `user_email`, `is_admin`)
- Sets `session.permanent = True`

**Auth/session:** Writes `session.user_id`, `session.user_email`, `session.is_admin`

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

### `GET /auth/login/discord`

Redirects the user to Discord's OAuth consent screen. Only available when `DISCORD_CLIENT_ID` is configured.

**Inputs:** None

**Outputs:** Redirect to Discord OAuth

**Side effects:** None

### `GET /auth/callback/discord`

Handles the redirect back from Discord after consent. Fetches the user's email via `/users/@me` API, checks that the email is verified, finds or creates the user, and sets the session.

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
| `APPLE_CLIENT_ID` | Enables Apple login button (Apple Services ID) |
| `DISCORD_CLIENT_ID` | Enables Discord login button |
| `DISCORD_CLIENT_SECRET` | Discord OAuth secret |

When no OAuth credentials are configured, the login page shows only the email form.

## Static Assets

None - this blueprint uses global static assets only.
