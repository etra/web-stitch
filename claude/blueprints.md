# Blueprint Rules (Backend)

Blueprints define **HTTP boundaries**: routing, validation, auth/session handling, and rendering.
They MUST NOT contain business logic or database access.

---

## 1. Blueprint folder structure

Each blueprint lives in: `stitch/blueprints/<name>/`

```text
stitch/blueprints/<name>/
├── README.md           # Required: blueprint docs + route inventory
├── __init__.py         # Blueprint instance (url_prefix, template_folder)
├── routes.py           # HTTP handlers (thin)
├── schemas.py          # Optional: request/response contracts (Pydantic)
├── templates/
│   └── <name>/         # Required template namespace
│       └── *.html
└── static/
    └── <name>/         # Required static namespace (JS/CSS/assets)
        └── ...
```

**Static files (JS/CSS/images) that are owned by a blueprint MUST live inside that blueprint’s `static/<name>/` folder.**

---

## 2. What belongs in a blueprint (allowed)

Blueprint routes MAY:
- Parse inputs (path params, query params, JSON, form data)
- Validate inputs (Pydantic or manual validation)
- Read/write session or cookies if needed
- Call services
- Render templates or return JSON responses
- Map service errors to HTTP responses (4xx/5xx)

Blueprint routes MUST be thin: glue code only.

---

## 3. What must NOT be in a blueprint (forbidden)

Blueprint routes MUST NOT:
- Query database models directly
- Create/update/delete database records directly
- Call `db.session.*` (commit/flush/rollback)
- Contain business rules (decisions, invariants, workflows)
- Perform heavy computation (image processing, complex math, etc.)

If a route needs logic, move it to a service.

---

## 4. Services are global and required for behavior

All business behavior lives in: `stitch/services/`

Rules:
- Do NOT create `services/` inside a blueprint.
- Routes call service methods.
- Services may call models and other services.
- Services are the only layer allowed to perform DB writes.

---

## 5. Template namespacing rule (mandatory)

Flask templates are effectively global, so templates MUST be namespaced per blueprint.

✅ Correct:
- `stitch/blueprints/auth/templates/auth/login.html`
- `render_template("auth/login.html")`

❌ Incorrect:
- `stitch/blueprints/auth/templates/login.html` (collision risk)

---

## 6. Static asset namespacing rule (mandatory)

Blueprint-owned static assets MUST be namespaced per blueprint to avoid collisions.

✅ Correct:
- `stitch/blueprints/editor/static/editor/editor.js`
- `stitch/blueprints/editor/static/editor/editor.css`

Templates should reference these via `url_for("<blueprint_name>.static", filename="editor/editor.js")`
(or the equivalent pattern used in this repo).

❌ Incorrect:
- `stitch/blueprints/editor/static/editor.js` (not namespaced)
- A shared global `static/` dumping ground for blueprint-owned assets

If a static asset is genuinely shared across multiple blueprints, it should live in a clearly named shared location (and be documented).

---

## 7. Implementation pattern (required)

### `__init__.py`
- Must set `url_prefix`
- Must set `template_folder="templates"`
- Must set `static_folder="static"` if using per-blueprint static
- Must import routes so handlers register

Example:

```python
from flask import Blueprint

bp = Blueprint(
    "analytics",
    __name__,
    url_prefix="/analytics",
    template_folder="templates",
    static_folder="static",
)

from . import routes  # noqa: E402,F401
```

### `routes.py`
Routes must follow this structure:
1) validate/parse input
2) call a service
3) format response (HTML/JSON)

Example:

```python
from flask import render_template, request, jsonify
from . import bp
from .schemas import AnalyticsReportRequest
from stitch.services.analytics_service import AnalyticsService

@bp.get("/dashboard/<project_id>")
def dashboard(project_id: str):
    stats = AnalyticsService.get_project_stats(project_id)
    return render_template("analytics/dashboard.html", stats=stats)

@bp.post("/api/report")
def generate_report():
    data = AnalyticsReportRequest(**request.json)
    report = AnalyticsService.generate_report(data)
    return jsonify(report.model_dump())
```

---

## 8. Blueprint README.md is mandatory

Each blueprint MUST include `stitch/blueprints/<name>/README.md`.
It is the single source of truth for what the blueprint exposes.

Required sections:

1. **Title + purpose**
2. **URL prefix**
3. **Routes table**
4. **Route details** (inputs, outputs, side effects, auth/session usage)
5. **Session keys** (only if applicable)
6. **Static assets** (if applicable; include entrypoints like `editor.js` and build/output notes)

Routes table format:

```md
| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET    | `/analytics/dashboard/<project_id>` | `dashboard` | Render analytics dashboard |
| POST   | `/analytics/api/report`             | `generate_report` | Generate analytics report |
```

If a route changes, the README MUST change in the same commit.

---

## 9. Registering blueprints

Blueprints must be registered in the app factory (e.g. `stitch/__init__.py`):

```python
from stitch.blueprints.analytics import bp as analytics_bp
app.register_blueprint(analytics_bp)
```

---

## 10. Checklist (for humans + AI agents)

For a new blueprint:
- [ ] Create `stitch/blueprints/<name>/`
- [ ] Add `__init__.py` with `url_prefix` and `template_folder="templates"`
- [ ] If blueprint has its own assets, set `static_folder="static"` and add `static/<name>/...`
- [ ] Add `routes.py` (thin routes only)
- [ ] Add `schemas.py` (if validation/contracts needed)
- [ ] Add `templates/<name>/...` (namespaced)
- [ ] Add `README.md` with routes table + route details (+ static assets if any)
- [ ] Register blueprint in app factory
- [ ] Ensure all DB access + business logic is in `stitch/services/`

---
## 11. UI & styling rules (Bootstrap 5)

The project uses **Bootstrap 5** as the primary UI framework.
UI code must prioritize consistency, readability, and reuse over custom styling.

---

### 11.1 Bootstrap-first rule

When building UI:
- Prefer **default Bootstrap 5 components and utilities**
- Use Bootstrap layout, spacing, and typography utilities before writing custom CSS
- Avoid reimplementing components that Bootstrap already provides

Custom UI behavior or styling is allowed **only when Bootstrap cannot reasonably achieve the result**.

---

### 11.2 Static asset location (blueprint perspective)

Blueprint-related CSS and JS MUST follow the project’s static asset rules:

- **Blueprint-owned assets**  
  Live in:  
  `stitch/blueprints/<name>/static/<name>/`

  Use this for assets tightly coupled to a single blueprint (e.g. editor JS).

- **Shared/global assets**  
  Live in:  
  `stitch/static/`

  Use this only for assets reused across multiple blueprints.

Blueprints MUST NOT introduce new, undocumented static locations.

---

### 11.3 CSS rules

CSS MUST:
- Live in dedicated `.css` files
- Be placed either in:
    - the blueprint’s `static/<name>/` directory (blueprint-specific), or
    - `stitch/static/` (shared)
- Be loaded via the base template/layout (or documented entrypoint)

CSS MUST NOT:
- Be written inline in HTML templates (`style=""`)
- Be embedded in `<style>` blocks inside templates

---

### 11.4 Template responsibilities

Templates SHOULD:
- Focus on structure and semantics
- Use Bootstrap classes for layout and appearance
- Avoid complex styling logic

Templates MUST NOT:
- Contain layout-specific CSS logic
- Become a substitute for proper CSS files

If a template requires non-trivial styling:
- Create or update a CSS file
- Document the reason in the commit or template comment

---

### 11.5 Exceptions

Inline styles or embedded `<style>` blocks are allowed **only** when:
- Required by a third-party library
- Used for quick prototyping (must be removed before merge)
- Explicitly documented with a comment explaining why
