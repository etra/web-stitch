# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## Development Commands

**Project structure:**
- Repository root: `web-stitch/`
- Python package: `stitch/`
- All commands run from repository root (`web-stitch/`)

**Backend (from repository root `web-stitch/`):**
```bash
# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run dev server
python run.py
# or
flask run --debug

# Run tests
pytest
```

## Database Management

### Flask-Migrate Commands (Production-Ready)

**Initial setup:**
```bash
# Initialize migrations (only once per project)
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migrations to database
flask db upgrade
```

**After modifying models:**
```bash
# 1. Make changes to models (e.g., add field to User)

# 2. Generate migration from model changes
flask db migrate -m "Add username field to User"

# 3. Review generated migration in migrations/versions/

# 4. Apply migration to database
flask db upgrade
```

**Other migration commands:**
```bash
# Rollback last migration
flask db downgrade

# Show current migration version
flask db current

# Show migration history
flask db history

# Downgrade to specific version
flask db downgrade <revision>

# Upgrade to specific version
flask db upgrade <revision>
```

### Custom Database Commands (Development Only)

**Quick database operations (bypasses migrations):**
```bash
# Create all tables from current models
flask db-commands create

# Drop all tables (prompts for confirmation)
flask db-commands drop

# Reset database (drop + create)
flask db-commands reset
```

**When to use:**
- `flask db migrate/upgrade` - Production, team projects, version control
- `flask db-commands create` - Quick local dev setup, prototyping
- `flask db-commands reset` - Clean slate during rapid iteration

**⚠️ Important:** Custom commands bypass migration tracking. Use Flask-Migrate for production.

## Application Routes

### Web Pages (Server-Rendered HTML)

| Route | Purpose | Auth Required | Status |
|-------|---------|---------------|--------|
| `/` | Home/landing page | No | ✅ Implemented |
| `/auth/login` | Login page (GET/POST) | No | ✅ Implemented |
| `/auth/logout` | Logout (redirect to home) | Yes | ✅ Implemented |
| `/projects` | Projects list page | Yes | ✅ Implemented (placeholder) |
| `/images` | Image gallery page | Yes | ✅ Implemented (placeholder) |

### Future Web Pages (To Be Implemented)

| Route | Purpose | Technology |
|-------|---------|------------|
| `/` | Home/landing page | Flask + Bootstrap |
| `/images` | Image gallery (uploaded originals) | Flask + Bootstrap |
| `/images/prepare/<filename>` | Multi-step image preparation | Flask + Bootstrap |
| `/projects` | List/create projects | Flask + Bootstrap |

### JavaScript Canvas Routes (Interactive Editor - To Be Implemented)

| Route | Purpose | Technology |
|-------|---------|------------|
| `/project/edit/<id>` | Canvas editor (main working area) | JavaScript + Canvas |
| `/project/export/<id>` | Export to PDF | Flask (server-side rendering) |

---
