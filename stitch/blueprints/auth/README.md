# Auth Blueprint

Handles user authentication with email-only login (no password required).

## URL Prefix

`/auth`

## Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET, POST | `/auth/login` | `login` | Login page and authentication handler |
| GET | `/auth/logout` | `logout` | Logs out the current user |

## Route Details

### `GET /auth/login`

Displays the login form.

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

## Static Assets

None - this blueprint uses global static assets only.
