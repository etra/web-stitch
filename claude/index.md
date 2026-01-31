# Claude Docs Index

This folder contains the **minimum, authoritative documentation** that AI code agents (and humans) must follow when working in this repo.

## How to use these docs

1. Start with **Project context** (what we’re building).
2. Follow the **implementation rules** (how we structure code and docs).
3. If a requirement is missing or unclear: **stop and ask for clarification** (do not guess).

## Documents (read order)

### 1) Project context
- [project.md](project.md) — What the product is, what users can do, and the overall purpose.

### 2) Backend structure & routing
- [blueprints.md](blueprints.md) — How to add/modify Flask blueprints (folder structure, thin routes, templates namespacing, required README docs).

### 3) Editor architecture
- [editor.md](editor.md) — How the canvas editor works: frontend modules, state management, data flow from UI to backend, stitch types, and project state schema.

### 4) PDF generation
- [pdf-generation.md](pdf-generation.md) — How pattern PDFs are generated: document structure, legend tables, symbol assignment, grid styles, and rendering options.

### 5) Business logic rules
- [service.md](service.md) — Rules for services: required documentation for each service + each public method, and keeping `services/README.md` as the index.

### 6) Persistence rules
- [database-models.md](database-models.md) — Rules for database models: “state only”, no business logic in models, no DB-level foreign keys, required model documentation, and `models/README.md` as the index.

## Maintenance rule

This `index.md` must be updated whenever any doc is added, removed, renamed, or repurposed.
If the index is out of date, it is considered a bug.
