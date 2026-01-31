# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## Project Overview

**Web-Stitch** is a web-based cross-stitch/bead chart editor inspired by MiniStitch. Users can create charts from scratch or with background images, draw with different stitch types (full, half, quarter, dots), work with multiple layers, and have their work automatically saved with version history.

**Target users:** Cross-stitch hobbyists, diamond painting users, and designers who want to create and refine stitch patterns with precise control over stitch types and layers.

**Key differentiator:** Support for multiple layers (image backgrounds + drawing layers) and different stitch types (not just solid color fills).

### Repository Structure

```
web-stitch/                 # Repository root
├── claude/                 # Documentation (this document)
├── stitch/                 # Main Python package
│   ├── __init__.py         # Flask app factory (create_app)
│   ├── config.py           # Configuration
│   ├── database.py         # Database setup
│   ├── blueprints/         # HTTP routes
│   ├── services/           # Business logic
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic contracts
│   └── utils/              # Shared utilities
├── migrations/             # Database migrations
├── tests/                  # Tests
├── requirements.txt        # Python dependencies
├── .gitignore              # Git ignore
├── .env                    # Environment variables
└── run.py                  # Application entry point
```

**Import pattern:** `from stitch import create_app`
