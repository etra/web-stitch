# Pattern Blueprint

Handles pattern viewing, printing, and sharing functionality.

## URL Prefix

`/pattern`

## Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/pattern/<project_id>` | `view` | View pattern with colored and symbol charts |

## Route Details

### `GET /pattern/<project_id>`

Renders a printable pattern view.

**Inputs:**
- `project_id` (path): Project ID

**Outputs:** HTML (`pattern/view.html`) with:
- Colored pattern (base64 image)
- Symbol chart (base64 image)
- Color legend with thread requirements

**Side effects:** None (read-only, generates images on-the-fly)

**Auth/session:** Requires login, reads `session.user_id`

### Features

**Colored Pattern:**
- Visual representation with thread colors
- 20px cell size for viewing

**Symbol Chart:**
- Traditional pattern chart with symbols for stitching
- 30px cell size for readability

**Color Legend:**
- Thread requirements with vendor codes
- Stitch counts per color
- Estimated strand count (~200 stitches per strand)

**Print Support:**
- Print-specific CSS styles
- Hidden UI elements in print mode
- Page break handling for large patterns

## Session Keys

| Key | Usage |
|-----|-------|
| `user_id` | Read to verify project ownership |

## Static Assets

Located in `stitch/blueprints/pattern/static/pattern/`:

| File | Purpose |
|------|---------|
| `pattern.css` | Pattern view styles and print media queries |

## Future Plans

- **Pattern Sharing** - Allow users to share patterns publicly or privately
- **Pattern Marketplace** - Enable buying/selling of patterns
- **PDF Export** - Generate downloadable PDF patterns
- **Multiple Formats** - Support different pattern layouts and formats
