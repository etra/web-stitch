# Web Stitch - Cross-Stitch Pattern Editor

A web-based cross-stitch and pixel-bead pattern editor with image import and export capabilities.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL

### Setup

1. **Install dependencies:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. **Create database:**
```bash
createdb webstitch
```

4. **Run migrations:**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. **Start server:**
```bash
python run.py
```

6. **Visit the application:**
Open your browser and go to `http://localhost:5000`

You can now:
- Browse the home page
- Click "Login" to access the application
- Enter your email to create an account or login
- Access your projects and images

## Documentation

All detailed documentation is in the `/claude/` directory:

- **[00-overview.md](old_stuff/00-overview.md)** - Product overview and features
- **[02-tech-stack.md](old_stuff/02-tech-stack.md)** - Technology choices
- **[04-backend-architecture.md](old_stuff/04-backend-architecture.md)** - Flask architecture and patterns
- **[11-security-and-performance.md](old_stuff/11-security-and-performance.md)** - Authentication strategy and security
- **[12-dev-commands-and-routes.md](old_stuff/12-dev-commands-and-routes.md)** - Development commands and API routes

## Current Status

✅ **Implemented:**
- Email-only authentication (MVP for local use)
- Flask application with blueprint architecture
- PostgreSQL with Flask-Migrate
- Session-based authentication

🚧 **To Be Implemented:**
- Image upload and processing
- Project management
- Canvas editor
- Pattern export

```
docker build -t ourstitch:latest .
```