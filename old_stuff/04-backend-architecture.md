# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## Backend Architecture

### Flask Blueprint Structure

**Professional, modular architecture with clear separation of concerns:**

```
web-stitch/                      # Repository root
├── stitch/                      # Main Python package
│   ├── __init__.py              # Flask app factory (create_app)
│   ├── config.py                # Configuration (dev, prod)
│   │
│   ├── blueprints/              # HTTP routing layer only
│   │   ├── auth/
│   │   │   ├── __init__.py      # Blueprint registration
│   │   │   ├── routes.py        # Route handlers (thin layer)
│   │   │   └── schemas.py       # Request/response contracts
│   │   │
│   │   ├── projects/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py        # Project CRUD routes
│   │   │   └── schemas.py       # Request/response contracts
│   │   │
│   │   ├── images/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py        # Image upload routes
│   │   │   └── schemas.py       # Request/response contracts
│   │   │
│   │   ├── layers/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py        # Layer CRUD routes
│   │   │   └── schemas.py       # Request/response contracts
│   │   │
│   │   └── export/
│   │       ├── __init__.py
│   │       ├── routes.py        # Export endpoints
│   │       └── schemas.py       # Request/response contracts
│   │
│   ├── services/                # Business logic (shared, reusable)
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Authentication logic
│   │   ├── project_service.py   # Project management logic
│   │   ├── layer_service.py     # Layer operations logic
│   │   ├── image_service.py     # Image processing logic
│   │   │
│   │   ├── processors/          # Image processing modules
│   │   │   ├── __init__.py
│   │   │   ├── quantizer.py     # Color quantization
│   │   │   ├── edge_detector.py # Edge/line detection
│   │   │   └── layer_generator.py # Multi-layer creation
│   │   │
│   │   ├── export_service.py    # Export generation logic
│   │   └── renderers/           # Export renderers
│   │       ├── __init__.py
│   │       ├── png_renderer.py  # PNG export with symbols (OpenCV)
│   │       └── pdf_renderer.py  # PDF export
│   │
│   ├── models/                  # Database models (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   └── snapshot.py
│   │
│   ├── schemas/                 # Shared contract models (Pydantic)
│   │   ├── __init__.py
│   │   ├── project.py           # Project state contracts
│   │   ├── layer.py             # Layer contracts
│   │   └── palette.py           # Palette contracts
│   │
│   ├── database.py              # Database session, connection pooling
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
└── run.py                       # Application entry point (at root)
```

### Key Architectural Decision: Services are Shared, Not Scoped to Blueprints

**Critical:** Services are NOT nested inside blueprint directories. They live in `app/services/` and are shared across the entire application.

**Why this matters:**
- **Reusability:** Multiple blueprints can use the same service (e.g., auth service used by multiple endpoints)
- **Testability:** Services can be tested independently without Flask/HTTP overhead
- **Clear separation:** Blueprints = HTTP routing, Services = business logic, Models = data persistence
- **No duplication:** If two blueprints need similar logic, they import the same service
- **Services can call services:** Business logic can compose other business logic

**Flow:** Request → Blueprint (HTTP) → Service (Business Logic) → Model (Database) → Response

### Architecture Principles

**1. Blueprint Pattern (HTTP Layer Only)**
- Blueprints handle HTTP routing and request/response concerns only
- Blueprints are thin - they delegate to services for business logic
- Blueprints contain: routes, request validation, response formatting
- Easy to add/remove routes without affecting business logic

**2. Service Layer (Shared Business Logic)**
- Services live in `app/services/` - NOT inside blueprints
- Services contain all business logic and can be reused across blueprints
- Services are independent of HTTP/Flask - pure Python business logic
- Multiple blueprints can use the same service
- Services can call other services

**3. Contract Models (Pydantic)**
- **Database models** (SQLAlchemy) - How data is stored
- **Contract models** (Pydantic) - How data is transmitted (API contracts)
- Clear separation prevents tight coupling
- Automatic validation of requests/responses

**4. Database Management (Flask-SQLAlchemy)**
- Flask-SQLAlchemy for simplified database integration
- Automatic session management tied to Flask request lifecycle
- Connection pooling with automatic reconnection handling
- Configuration-based pool settings for reliability

### Example: Blueprint Structure

**`stitch/blueprints/projects/routes.py` (Thin HTTP layer):**
```python
from flask import Blueprint, request, jsonify
from stitch.services.project_service import ProjectService  # Import from shared services
from .schemas import CreateProjectRequest, ProjectResponse
from pydantic import ValidationError

bp = Blueprint('projects', __name__, url_prefix='/api/v1/projects')

@bp.route('', methods=['POST'])
def create_project():
    """Create new project - route only handles HTTP concerns"""
    try:
        # Validate request using Pydantic contract
        data = CreateProjectRequest(**request.get_json())

        # Business logic delegated to shared service
        project = ProjectService.create_project(
            user_id=get_current_user_id(),
            data=data
        )

        # Return response using contract
        return jsonify(ProjectResponse.from_orm(project).dict()), 201

    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.errors()}), 400
```

**`stitch/services/project_service.py` (Shared business logic):**
```python
from stitch.models.project import Project
from stitch.database import db
from stitch.schemas.project import CreateProjectRequest  # Import from shared schemas
import uuid

class ProjectService:
    @staticmethod
    def create_project(user_id: str, data: CreateProjectRequest):
        """Business logic for creating project"""
        # Create initial state
        initial_state = {
            'palette': data.palette or get_default_palette(),
            'layers': [
                {
                    'id': str(uuid.uuid4()),
                    'type': 'raster',
                    'name': 'Main stitches',
                    'visible': True,
                    'cells': [None] * (data.width * data.height)
                }
            ],
            'activeLayerId': None
        }

        # Create database record
        project = Project(
            user_id=user_id,
            name=data.name,
            width=data.width,
            height=data.height,
            cloth_color=data.cloth_color,
            state=initial_state
        )

        db.session.add(project)
        db.session.commit()

        return project

    @staticmethod
    def get_project(project_id: str):
        """Get project by ID"""
        return Project.query.filter_by(id=project_id).first()

    @staticmethod
    def update_project(project_id: str, state: dict):
        """Update project state"""
        project = Project.query.filter_by(id=project_id).first()
        if project:
            project.state = state
            db.session.commit()
        return project

    @staticmethod
    def delete_project(project_id: str):
        """Delete project"""
        project = Project.query.filter_by(id=project_id).first()
        if project:
            db.session.delete(project)
            db.session.commit()
        return True
```

**`stitch/blueprints/projects/schemas.py` (Contracts):**
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class CreateProjectRequest(BaseModel):
    """Contract for creating a project"""
    name: str = Field(..., min_length=1, max_length=255)
    width: int = Field(..., ge=1, le=1000)
    height: int = Field(..., ge=1, le=1000)
    cloth_color: str = Field(default='#ffffff', regex='^#[0-9a-fA-F]{6}$')
    palette: Optional[List[dict]] = None

class ProjectResponse(BaseModel):
    """Contract for project response"""
    id: str
    name: str
    width: int
    height: int
    cloth_color: str
    state: dict
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True  # Allows from_orm()
```

### Database Setup with Flask-SQLAlchemy

**`stitch/config.py` (Configuration with connection pooling):**
```python
import os

class Config:
    """Base configuration"""
    # Database URI
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:pass@localhost/webstitch'
    )

    # Disable modification tracking (saves resources)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool settings to prevent "server closed connection" errors
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,                    # Number of connections to maintain
        'pool_recycle': 3600,               # Recycle connections after 1 hour
        'pool_pre_ping': True,              # Test connections before using them
        'pool_timeout': 30,                 # Timeout for getting connection from pool
        'max_overflow': 20,                 # Max connections beyond pool_size
        'connect_args': {
            'connect_timeout': 10,          # Connection timeout in seconds
            'options': '-c statement_timeout=30000'  # 30 second query timeout
        }
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log all SQL statements

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
```

**`stitch/database.py` (Flask-SQLAlchemy setup):**
```python
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask-SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)

    with app.app_context():
        # Import all models to ensure they're registered
        import stitch.models

        # Create tables
        db.create_all()
```

**`stitch/__init__.py` (Flask app factory):**
```python
from flask import Flask
from stitch.config import DevelopmentConfig, ProductionConfig
from stitch.database import db, init_db
import os

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)

    # Load configuration
    if os.getenv('FLASK_ENV') == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # Initialize database
    init_db(app)

    # Register blueprints
    from stitch.blueprints.projects import bp as projects_bp
    from stitch.blueprints.images import bp as images_bp
    from stitch.blueprints.layers import bp as layers_bp
    from stitch.blueprints.export import bp as export_bp

    app.register_blueprint(projects_bp)
    app.register_blueprint(images_bp)
    app.register_blueprint(layers_bp)
    app.register_blueprint(export_bp)

    return app
```

**`stitch/models/project.py` (Example model - No Foreign Keys):**
```python
from stitch.database import db
from datetime import datetime
import uuid

class Project(db.Model):
    """Project model storing cross-stitch patterns."""
    __tablename__ = 'projects'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)  # Reference to users.id (no FK)
    name = db.Column(db.String(255), nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    cloth_color = db.Column(db.String(7), default='#ffffff')
    state = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to user (no database FK constraint)
    user = db.relationship('User',
                          primaryjoin='Project.user_id==User.id',
                          foreign_keys='[Project.user_id]',
                          back_populates='projects')

    def __repr__(self):
        return f'<Project {self.name}>'
```

**Important: No Foreign Key Constraints**
- This project does NOT use database-level foreign keys
- Reference columns (like `user_id`) are simple indexed columns
- Relationships are defined using SQLAlchemy's `db.relationship()` with explicit `primaryjoin`
- See `/claude/06-storage-and-database.md` for detailed explanation
```

**Key Benefits of Flask-SQLAlchemy:**

1. **Automatic Session Management:**
   - `db.session` is automatically created and managed per request
   - No need for manual session cleanup or teardown functions
   - Sessions are automatically committed or rolled back

2. **Connection Pool Reuse:**
   - `pool_pre_ping=True` ensures connections are valid before use
   - `pool_recycle=3600` prevents stale connections
   - `max_overflow=20` handles traffic spikes

3. **Query API:**
   - `Project.query.filter_by(id=project_id).first()`
   - `Project.query.all()`
   - Direct access to query methods on models

4. **Database Migrations (Flask-Migrate):**
```bash
# Initialize migrations
flask db init

# Create migration after model changes
flask db migrate -m "Add project table"

# Apply migrations
flask db upgrade

# Rollback
flask db downgrade
```
