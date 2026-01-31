# CLAUDE.md

## Project

* Name: Our stitch
* Website: https://ourstitch.com
* Title: OurStitch — Create and Share Cross-Stitch Patterns Together
* MetaDescription: OurStitch is a community-driven platform where cross stitchers create, design, and share cross-stitch patterns. Build patterns stitch by stitch and collaborate with fellow makers. 

## TL;DR (Always-Loaded Context)

This is a **web-based, community-driven cross-stitch pattern editor** built with Flask and a custom in-browser Canvas editor. Users create and edit patterns on a **grid of stitches (not pixels)**, optionally importing images for reference or conversion, and can share finished patterns with the community. The architecture enforces strict separation of concerns: **blueprints handle HTTP only**, **services contain all business logic**, **models manage persistence**, and **templates render UI**. If required behavior or data is unclear or undocumented, **stop and ask for clarification—do not guess**.

## 0. General Rule (Mandatory)

If information required to correctly design, implement, or modify code is missing, unclear, 
or contradictory, you must:
* Stop
* Request the missing documentation or clarification
* Do not guess or infer behavior
* Proceeding without proper documentation is not allowed.

This rule applies to:
* Human contributors
* Automated tools
* AI coding assistants

We take priority:
* on **correctness and clarity** over speed
* on **well-documented behavior** over assumptions
* on **explicit specifications** over inferred intent
* on **following best practices** over shortcuts
* on **reusability and maintainability** over quick fixes

### Responsibility of Code Agents (Important)

As a code agent, you are expected to follow all rules in this repository strictly whenever they apply.

However, rules are not dogma and may be questioned when they clearly hinder correctness, clarity, or maintainability.


## 1. Project Purpose

This project is a **web-based, community-driven cross-stitch pattern editor**.

Users can:
* Create cross-stitch patterns from scratch
* Import images as references or convert them into editable patterns
* Edit patterns stitch-by-stitch using a grid, palette, and stitch types
* Share finished patterns with the community

The application is best thought of as a Photoshop-like editor for cross-stitching, focused on stitches, grids, layers, and thread palettes rather than free-form pixels.

---

## 2. High‑Level Technical Overview

The application is a classic web app with a custom in‑browser editor.

### Backend

* **Language:** Python
* **Framework:** Flask
* **UI:** Server‑rendered templates using Bootstrap 5
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy

The backend is responsible for:

* User accounts
* Projects and patterns
* Persistence and storage
* Serving pages and APIs

### Editor

* Written in **pure JavaScript** (no frontend framework)
* Uses **HTML5 Canvas** for rendering
* Operates on a **grid of stitches** (stitches are the core unit, not pixels)

All interactive cross‑stitch editing happens inside this editor.

---

## 3. Documentation Structure

This file (`CLAUDE.md`) is intentionally **small and high‑level**.

Detailed technical and architectural documentation lives in the `claude/` directory.  
Those documents are the **source of truth** for their respective domains.

---

## 4. Project High-Level Architecture

This project uses a **clean, modular architecture with strict separation of concerns**.  
Each layer has a single responsibility and clear boundaries.

At a glance:
- **Blueprints** → HTTP routing and request/response handling
- **Services** → All business logic
- **Models** → Data persistence
- **Templates** → UI rendering (scoped to blueprints)
- **Utils / Exceptions** → Shared helpers and errors

---

### Repository Structure


```
web-stitch/                      # Repository root
├── stitch/                      # Main Python package
│   ├── __init__.py              # Flask app factory (create_app)
│   ├── config.py                # Configuration (dev, prod)
│   ├── database.py              # Database session, connection pooling
│   ├── static/                  # Global static files (CSS, JS)
│   │   └── ...                  # e.g. global styles, scripts
│   ├── templates/               # Global templates (base.html, layout)
│   │   └── ...                  # e.g. base.html, layout.html
│   │
│   ├── blueprints/              # HTTP routing layer only
│   │   ├── blueprint_name/
│   │   │   ├── templates/       # Blueprint-specific HTML templates
│   │   │   │   └── ...          # e.g. index.html
│   │   │   ├── static/          # Blueprint-specific static files
│   │   │   │   └── ...          # e.g. CSS, JS
│   │   │   ├── README.md        # Documentation 
│   │   │   ├── __init__.py      # Blueprint registration
│   │   │   ├── routes.py        # Route handlers (thin layer)
│   │   │   └── schemas.py       # Request/response contracts
│   │   └── README.md            # Blueprints documentation index
│   │
│   ├── services/                # Business logic (shared, reusable)
│   │   ├── README.md            # Services documentation index
│   │   ├── __init__.py
│   │   └── name_service.py      # Service example
│   │
│   ├── models/                  # Database models (SQLAlchemy)
│   │   ├── __init__.py
|   │   ├── README.md            # Models documentation index
│   │   ├── model.py             # Model example
│   │   └── static_data.py       # Static/reference data
│   │
│   ├── exceptions.py            # Custom exceptions
│   └── utils/                   # Shared utilities
│       ├── __init__.py
│       └── validators.py
│
├── migrations/                  # Database migrations (at root)
├── tests/                       # Tests (at root)
├── requirements.txt             # Python dependencies (at root)
├── .gitignore                   # Git ignore (at root)
├── .env                         # Environment variables (at root)
```

---

## How to Work With This Architecture

- **Adding or changing routes?**  
  Use a blueprint → see [blueprints.md](claude/blueprints.md)

- **Implementing behavior or rules?**  
  Use a service → see [service.md](claude/service.md)

- **Changing stored data or schema?**  
  Use models → see [database-models.md](claude/database-models.md)

- **Updating UI or pages?**  
  Edit templates inside the relevant blueprint

**Rule of thumb:**
> Routes stay thin. Logic lives in services. Data lives in models.
Business logic must not live in blueprints, templates, or models.

**Templates are presentation-only.**
> They MUST NOT contain business logic or database access. Any non-trivial behavior belongs in services (and is invoked via routes).

Static assets may be **global** (`stitch/static/`) or **blueprint-owned** (`stitch/blueprints/<name>/static/`); the rules for when to use each are defined in `claude/blueprints.md`.
