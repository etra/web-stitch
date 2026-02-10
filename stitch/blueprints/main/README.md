# Main Blueprint

Core application routes for the home page, community patterns, and static pages.

## URL Prefix

None (routes are at root level)

## Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/` | `index` | Home page - hero + latest/best community patterns |
| GET | `/patterns` | `patterns` | Browse community patterns with pagination and sorting |
| GET | `/privacy` | `privacy` | Privacy policy page |
| GET | `/imprint` | `imprint` | Imprint / legal notice page |
| GET | `/resource/<path:filepath>` | `serve_resource` | (Deprecated) Serves uploaded files from the uploads directory |

## Route Details

### `GET /`

Renders the main landing page with hero section and community pattern rows.

**Inputs:** None

**Outputs:** HTML (`main/index.html`)

**Side effects:** None

**Auth/session:** Reads `session.user_id` to show different CTAs and to bulk-fetch user votes for displayed patterns.

**Template data:**
- `latest_patterns` — up to 6 most recent public projects
- `best_patterns` — up to 6 highest-voted public projects
- `user_votes` — dict mapping project_id to user's vote value (if logged in)

### `GET /patterns`

Browse community patterns with sorting and pagination.

**Inputs:**
- `sort` (query param): `latest` (default) or `popular`
- `page` (query param): page number, default 1

**Outputs:** HTML (`main/patterns.html`)

**Side effects:** None

**Auth/session:** Reads `session.user_id` to bulk-fetch user votes.

**Template data:**
- `patterns` — list of public projects for current page
- `total` — total count of public projects
- `sort`, `page`, `per_page`, `total_pages` — pagination state
- `user_votes` — dict mapping project_id to user's vote value (if logged in)

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
| `user_id` | Read in index and patterns routes to determine logged-in state and fetch user votes |

## Static Assets

None - this blueprint uses global static assets only (`stitch/static/`).
