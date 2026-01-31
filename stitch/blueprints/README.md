# Blueprints

This directory contains all Flask blueprints for the Web-Stitch application.

Blueprints define **HTTP boundaries**: routing, validation, auth/session handling, and rendering.
They MUST NOT contain business logic or database access.

**Rule of thumb:**
> Routes validate and delegate. Services decide and execute.

---

## Blueprint Overview

| Blueprint | URL Prefix | Purpose |
|-----------|------------|---------|
| `main` | `/` (root) | Home page and uploaded resource serving |
| `api` | `/api` | JSON API endpoints for frontend data access |
| `auth` | `/auth` | User authentication (email-only MVP) |
| `images` | `/images` | Image upload and gallery management |
| `projects` | `/projects` | Project CRUD and listing |
| `editor` | `/editor` | Cross-stitch pattern editor |
| `pattern` | `/pattern` | Pattern preparation wizard |

---

## Adding a New Blueprint

See `claude/blueprints.md` for the complete checklist and rules.

Quick checklist:
- [ ] Create `stitch/blueprints/<name>/`
- [ ] Add `__init__.py` with `url_prefix` and `template_folder`
- [ ] Add `routes.py` (thin routes only)
- [ ] Add `schemas.py` (if validation needed)
- [ ] Add `templates/<name>/...` (namespaced)
- [ ] Add `static/<name>/...` (if blueprint-owned assets)
- [ ] Add `README.md` with routes table and details
- [ ] Register blueprint in `stitch/__init__.py`
- [ ] Update this README

---

## Update Rule

If you add, remove, rename, or repurpose a blueprint, **update this README in the same commit**.
