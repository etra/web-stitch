# API Blueprint Rules

The `api` blueprint serves **JSON-only endpoints** consumed by frontend JavaScript.
It follows all general blueprint rules (see [blueprints.md](blueprints.md)) with the differences documented below.

---

## How the API Blueprint Differs

### 1. JSON-only — no templates, no static assets

The API blueprint returns JSON responses exclusively. It has:
- **No `templates/` directory** — no HTML rendering
- **No `static/` directory** — no CSS, JS, or images
- No `template_folder` or `static_folder` in the Blueprint constructor

### 2. Per-resource packages

Each resource is a **sub-package** inside `stitch/blueprints/api/` with a consistent internal structure:

```text
stitch/blueprints/api/
├── __init__.py             # Blueprint registration + imports all route modules
├── resource_name/          # One package per resource
│   ├── __init__.py         # Package marker (empty)
│   ├── schema.py           # Pydantic v2 response schemas
│   ├── router.py           # Route handlers
│   └── README.md           # Route docs for this resource
└── README.md               # Route inventory
```

#### Package contents

| File | Purpose |
|------|---------|
| `__init__.py` | Empty package marker |
| `schema.py` | Pydantic v2 response schemas that define the JSON contract |
| `router.py` | Route handlers — imports `bp` from the API blueprint and registers routes |
| `README.md` | Route documentation (inputs, outputs, auth, examples) |

#### Response models enforce contracts

Route handlers validate responses through Pydantic models before returning JSON:

```python
from stitch.blueprints.api.color.schema import ColorsListResponse

@bp.get('/colors')
def get_colors():
    colors = ColorService.get_all_colors()
    response = ColorsListResponse(colors=colors)
    return jsonify(response.model_dump())
```

This ensures that if a service returns unexpected data, Pydantic raises a clear validation error instead of silently passing bad data to the frontend.

### 3. Adding a new resource

To add routes for a new resource (e.g., `palette`):

1. Create `stitch/blueprints/api/palette/` directory
2. Add `__init__.py` (empty)
3. Add `schema.py` with Pydantic v2 response schemas
4. Add `router.py` — import `bp` from `stitch.blueprints.api` and define routes, validate responses through models
5. Add `README.md` with route documentation
6. Import the router in `stitch/blueprints/api/__init__.py`
7. Add a row to the Resources table in `stitch/blueprints/api/README.md` linking to the new resource's README

### 4. README structure

`stitch/blueprints/api/README.md` is a **simple index file**. It contains:
- A link to this file (`claude/api.md`) for architecture rules
- The URL prefix
- A Resources table with one row per resource, linking to its README

It must **not** contain route listings, file layouts, or architectural details — those belong in per-resource READMEs and this file respectively.

When adding a new resource, add a row to the Resources table:

```markdown
| [resource_name](resource_name/README.md) | Short description |
```

### 5. Consumed by frontend JS

API endpoints are called via `fetch()` / AJAX from the browser-side editor and other JavaScript. They are not meant to be visited directly in a browser.

---

## Rules That Still Apply

Everything in [blueprints.md](blueprints.md) applies unless overridden above:
- Routes must be thin (call services, return JSON)
- No database access or business logic in route handlers
- `README.md` must list all routes and stay up to date
