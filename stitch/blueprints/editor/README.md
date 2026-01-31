# Editor Blueprint

Canvas editor for cross-stitch pattern editing.

## URL Prefix

`/editor`

## Structure

```
editor/
├── __init__.py          # Blueprint registration
├── routes.py            # Page routes
├── api/
│   ├── __init__.py      # API route registration
│   ├── state.py         # State operations (save/load)
│   ├── render.py        # Thumbnail generation
│   └── layers.py        # Layer operations (future)
├── static/editor/
│   └── js/
│       ├── main.js      # Editor entry point
│       ├── state.js     # State management
│       ├── renderer.js  # Canvas rendering
│       ├── tools.js     # Drawing tools
│       ├── viewport.js  # Pan/zoom
│       ├── api.js       # Backend API client
│       ├── storage.js   # IndexedDB storage
│       ├── view.js      # UI components
│       └── stitches/    # Stitch type definitions
├── templates/editor/
│   └── canvas.html      # Editor page template
└── README.md
```

## Routes

### Page Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/editor/<project_id>` | `canvas` | Editor page |

### API Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/editor/<project_id>/api/state` | `get_state` | Get project state |
| POST | `/editor/<project_id>/api/state` | `save_state` | Save project state |
| GET | `/editor/<project_id>/api/thumbnail` | `thumbnail` | Generate thumbnail PNG |

## Route Details

### `GET /editor/<project_id>`

Loads the full editor interface.

**Inputs:**
- `project_id` (path): Project ID

**Outputs:** HTML (`editor/canvas.html`) with project data embedded for JavaScript

**Auth/session:** Requires login, reads `session.user_id`

### `GET /editor/<project_id>/api/state`

Returns full project data including state.

**Response:**
```json
{
  "id": "project-uuid",
  "name": "My Project",
  "description": "Optional description",
  "width": 100,
  "height": 100,
  "clothColor": "#ffffff",
  "state": {
    "palette": [...],
    "layers": [...],
    "activeLayerId": "layer-uuid"
  }
}
```

### `POST /editor/<project_id>/api/state`

Saves project state.

**Request:**
```json
{
  "state": {
    "palette": [...],
    "layers": [...],
    "activeLayerId": "layer-uuid"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Project saved successfully"
}
```

### `GET /editor/<project_id>/api/thumbnail`

Generates PNG thumbnail of the project canvas.

**Response:** PNG image (3px cell size)

## Session Keys

| Key | Usage |
|-----|-------|
| `user_id` | Read to verify project ownership |

## Services Used

| Service | Methods |
|---------|---------|
| `ProjectService` | `get_project`, `update_project` |
| `PatternRenderer` | `render_colored_pattern` |

## JavaScript Client

The editor frontend uses `api.js` to communicate with these endpoints:

```javascript
const api = new API(projectId);
// Base URL: /editor/<projectId>/api

await api.saveProject(state);   // POST /api/state
await api.loadProject();        // GET /api/state
api.getThumbnail();             // GET /api/thumbnail
```

## Future API Routes (Planned)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/editor/<project_id>/api/layers` | Add new layer |
| DELETE | `/editor/<project_id>/api/layers/<layer_id>` | Delete layer |
| POST | `/editor/<project_id>/api/layers/from-image` | Add layers from uploaded image |
| PATCH | `/editor/<project_id>/api/layers/<layer_id>` | Update layer properties |
