# Main Blueprint

Core application routes for the home page and uploaded resource serving.

## URL Prefix

None (routes are at root level)

## Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/` | `index` | Home page - landing page for the application |
| GET | `/resource/<path:filepath>` | `serve_resource` | Serves uploaded files from the uploads directory |

## Route Details

### `GET /`

Renders the main landing page.

**Inputs:** None

**Outputs:** HTML (`main/index.html`)

**Side effects:** None

**Auth/session:** Reads `session.user_id` to show different CTAs for logged-in vs anonymous users

### `GET /resource/<path:filepath>`

Static file server for user-uploaded content.

**Inputs:**
- `filepath` (path param): Relative path to the file within uploads directory

**Outputs:** File content with appropriate MIME type

**Side effects:** None (read-only)

**Auth/session:** Not required

## Session Keys

| Key | Usage |
|-----|-------|
| `user_id` | Read in `index.html` template to determine logged-in state |

## Static Assets

None - this blueprint uses global static assets only (`stitch/static/`).
