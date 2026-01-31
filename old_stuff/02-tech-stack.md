# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## Tech Stack

### Backend
- **Python 3.11+**
- **Flask** - REST API with blueprints (modular architecture)
- **Flask-SQLAlchemy** - Database ORM with automatic session management
- **Flask-Migrate** - Database migrations (Alembic wrapper)
- **PostgreSQL** - Primary database with connection pooling
- **Pydantic** - Contract models (API request/response validation)
- **OpenCV (cv2)** - Image processing and symbol rendering
- **NumPy** - Array operations for image processing
- **Pillow** - Image format conversion (not for symbol rendering)
- **Redis** (optional) - Caching + background job queue
- **Gunicorn** - Production WSGI server with connection pooling

### Frontend
- **Bootstrap 5** - UI framework (cards, buttons, layout with row/col)
- **Vanilla JavaScript** - No React, no frameworks - just plain ES6 modules
- **Canvas API** - Custom grid rendering (built from scratch)
- **Vite** (optional) - Dev server with hot reload (can start without it)
- **Zero runtime dependencies** - Bootstrap CSS + custom JS only

### Deployment & Storage
- **Self-hosted** - Local home server deployment
- **PostgreSQL** - Local database for all data (projects, users, snapshots, layers)
- **File system** - Store uploaded images and exports locally (no S3)
- **No cloud dependencies** - Everything runs locally
