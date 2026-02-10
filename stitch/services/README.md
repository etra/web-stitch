# Services Layer

This directory contains **all business logic** for the Web-Stitch application.

Services are **framework-agnostic**, reusable, and shared across all blueprints.
They must not contain HTTP concerns (no Flask request/response handling, no rendering).

**Rule of thumb:**
> Routes validate and delegate. Services decide and execute.

---

## 📁 Service Overview

| Service File | Responsibility |
|--------------|----------------|
| `auth_service.py` | User authentication and session handling |
| `project_service.py` | Project lifecycle and state management |
| `wizard_service.py` | Multi-step workflow orchestration |
| `image_service.py` | Image upload, preparation, and import |
| `image_processor.py` | Low-level image transformations |
| `color_matcher.py` | Color matching and palette reduction |
| `color_service.py` | Query vendor color catalogs from the database |
| `pattern_renderer.py` | Rendering patterns as images |
| `pattern_pdf_service.py` | PDF generation for printable patterns |
| `tag_service.py` | Tag management and project-tag associations |
| `email_service.py` | Email sending (sync/async, templates) |
| `seo_service.py` | SEO metadata generation for pages |
| `vote_service.py` | Project voting (cast, remove, query) |
| `community_service.py` | Public pattern queries (latest, best, paginated) |

---

## 🔐 `auth_service.py`

**Purpose:**  
Handles user authentication logic for the MVP (email-only).

**Responsibilities:**
- Find or create users by email
- Initialize authentication sessions
- Validate authenticated user context

**Does NOT:**
- Render templates
- Handle HTTP requests directly
- Perform password or OAuth logic (future work)

**Used by:**
- `auth` blueprint
- Any service requiring authenticated user context

---

## 📦 `project_service.py`

**Purpose:**
Manages the full lifecycle of a project.

**Responsibilities:**
- Create new projects (empty or from prepared images)
- Load full project state
- Apply state diffs
- Persist project snapshots
- Update metadata (name, size, cloth color)
- Delete projects

**Key methods:**
- `create_project()` - Create new empty project
- `create_project_from_image()` - Create project from processed image with layers
- `get_project()` - Get project by ID
- `get_user_projects()` - List user's projects
- `update_project()` - Update project fields
- `delete_project()` - Delete project
- `create_initial_state()` - Generate initial empty project state
- `assemble_state()` - Reconstruct full state dict from normalized `ProjectLayer` and `ProjectColor` tables (compatibility bridge for frontend and downstream consumers)
- `save_state()` - Decompose a state dict into normalized tables (replace-all strategy: deletes then re-inserts)
- `get_palette_color_count()` - Get number of palette colors for a project (used by project list)
- `add_palette_colors()` - Add catalog colors to a project's palette (auto-assigns symbols, skips duplicates)
- `remove_palette_colors()` - Remove colors from palette and clean up cell/path references in all layers
- `merge_palette_colors()` - Remap cell/path references from source to target colors, then delete sources

**Key Concepts:**
- Project state is **normalized** into `ProjectLayer` and `ProjectColor` tables
- `assemble_state()` reconstructs the JSON state format from normalized tables
- `save_state()` decomposes state into normalized rows (uses flush, caller commits)
- No foreign key constraints (application-level integrity)

**Used by:**
- `projects` blueprint
- `images` blueprint
- `editor` blueprint
- `wizard_service`
- `pattern_renderer`

---

## 🧭 `wizard_service.py`

**Purpose:**  
Coordinates **multi-step workflows** that span multiple services.

**Responsibilities:**
- Orchestrate image preparation steps
- Maintain wizard state between steps
- Validate transitions between steps
- Commit final results (e.g. prepared image → project)

**Important:**
This service **does not perform image processing itself** — it delegates to:
- `image_service`
- `image_processor`
- `color_matcher`

**Used by:**
- Image preparation wizard routes
- Future guided workflows

---

## 🖼️ `image_service.py`

**Purpose:**
High-level image handling and orchestration.

**Responsibilities:**
- Handle image uploads
- Manage filesystem storage
- Coordinate image preparation
- Process images for pattern creation (resize, quantize)
- Import prepared images into projects
- Cache processed image artifacts

**Key methods:**
- `upload_image()` - Upload and save image with thumbnail
- `process_pattern_image()` - Process image for pattern creation (resize, quantize, save)
- `get_user_images()` - List user's uploaded images
- `get_processed_versions()` - List processed versions of an image
- `get_image_dimensions()` - Get width/height of an original image
- `generate_preview()` - Generate preview data for AJAX processing (base64 images)
- `load_processed_metadata()` - Load metadata for previously processed image
- `get_thumbnail_path()` - Get filesystem path to image thumbnail

**Delegates to:**
- `image_processor` for transformations
- `color_matcher` for palette reduction
- `color_service` for palette mapping

**Does NOT:**
- Contain OpenCV logic directly (delegates to `image_processor`)
- Perform pixel-level operations

---

## 🧪 `image_processor.py`

**Purpose:**  
Low-level image transformations.

**Responsibilities:**
- Resize images to grid dimensions
- Quantize images
- Edge detection
- Generate intermediate image layers

**Characteristics:**
- Pure, deterministic functions
- No database access
- No filesystem responsibility
- No business rules

**Used by:**
- `image_service`
- `wizard_service`

---

## 🎨 `color_matcher.py`

**Purpose:**
Reduce and normalize colors from images.

**Responsibilities:**
- Cluster image colors
- Match image colors to palette entries
- Return consistent color sets for patterns

**Key methods:**
- `match_palette_to_dmc()` - Match quantized palette to DMC colors
- `update_selection()` - Update color selection flags from form input
- `create_dmc_mapped_palette()` - Create final palette with DMC mappings
- `merge_similar_colors()` - Merge colors that map to same DMC color

**Important:**
This service is **vendor-agnostic**.
Vendor-specific color lookups live in `color_service.py`.

---

## 🏷️ `tag_service.py`

**Purpose:**
Manage tags and project-tag associations for categorizing projects.

**Responsibilities:**
- Normalize tag names (lowercase, strip, remove special chars)
- Create and look up tags
- Search tags by prefix for autocomplete
- Set/replace all tags for a project

**Key methods:**
- `normalize_tag_name()` - Normalize tag name string
- `get_or_create_tag()` - Find or create tag by normalized name
- `search_tags()` - Search tags by prefix (for autocomplete API)
- `set_project_tags()` - Replace all tags for a project
- `get_project_tags()` - Get all tags for a project
- `get_all_tags()` - Get all tags (for autocomplete pre-population)

**Used by:**
- `projects` blueprint (wizard and edit routes)
- `api` blueprint (tag autocomplete endpoint)
- `wizard_service` (during project creation)

---

## 📧 `email_service.py`

**Purpose:**
Send emails throughout the application.

**Responsibilities:**
- Send plain text and HTML emails
- Support synchronous and asynchronous sending
- Template-based email rendering
- Handle attachments

**Key methods:**
- `send()` - Send email with text/HTML body
- `send_template()` - Send email using template files
- `send_welcome()` - Welcome email for new users
- `send_magic_link()` - Passwordless authentication link
- `send_pattern_shared()` - Notification when pattern is shared
- `send_test()` - Test email configuration

**Configuration (environment variables):**
- `MAIL_SERVER` - SMTP server hostname
- `MAIL_PORT` - SMTP port (default: 587)
- `MAIL_USE_TLS` - Enable TLS (default: true)
- `MAIL_USERNAME` - SMTP username
- `MAIL_PASSWORD` - SMTP password
- `MAIL_DEFAULT_SENDER` - Default sender address

**Email templates location:** `stitch/templates/email/`

**Used by:**
- `auth` blueprint (magic link login)
- Future: pattern sharing, notifications

---

## 🔍 `seo_service.py`

**Purpose:**
Generate SEO metadata for pages throughout the application.

**Responsibilities:**
- Provide consistent title and description formatting
- Generate Open Graph and Twitter Card metadata
- Manage canonical URLs
- Define site-wide SEO defaults

**Key methods:**
- `get_index_metadata()` - SEO metadata for the home page
- `get_page_metadata()` - SEO metadata for generic static pages

**Key classes:**
- `SEOMetadata` - Dataclass container for SEO fields (title, description, canonical_url, og_image, keywords)

**Configuration:**
- `SITE_NAME` - "OurStitch"
- `SITE_URL` - "https://ourstitch.com"
- `DEFAULT_TITLE` - Default page title
- `DEFAULT_DESCRIPTION` - Default meta description

**Used by:**
- `main` blueprint (index page)
- Future: static pages, pattern pages, user profiles

---

## 🖨️ `pattern_renderer.py`

**Purpose:**
Render pattern images for display and export.

**Responsibilities:**
- Render colored patterns as images
- Render symbol charts as images
- Generate legend data with color statistics
- Support paginated rendering (50x50 grid sections)
- Draw grids, symbols, and coordinate numbers

**Key methods:**
- `render_colored_pattern()` - Full colored pattern image
- `render_symbol_pattern()` - Full symbol chart image
- `render_overview_pattern()` - Scaled down preview image
- `render_symbol_page()` - Paginated symbol chart (specific region)
- `calculate_pattern_pages()` - Calculate page layout for pagination
- `generate_legend()` - Color usage statistics
- `image_to_base64()` - Convert to base64 for HTML display

**Implementation details:**
- Uses OpenCV for image rendering
- Uses numpy arrays for image data
- Never modifies project state
- Read-only access to project data

**Used by:**
- `pattern` blueprint
- `pattern_pdf_service`

---

## 📄 `pattern_pdf_service.py`

**Purpose:**
Generate printable PDF documents for cross-stitch patterns.

**Responsibilities:**
- Generate multi-page PDF documents
- Page 1: Pattern overview with colored preview and project info
- Page 2: Color legend with thread requirements
- Pages 3+: Paginated symbol charts (50x50 with 5-stitch overlap)
- Add consistent footer with branding and page numbers

**Key methods:**
- `generate_pdf()` - Generate complete PDF as bytes

**Dependencies:**
- ReportLab for PDF generation
- PatternRenderer for image generation
- PIL/Pillow for image conversion

**Used by:**
- `pattern` blueprint (PDF download route)

---

## 🎨 `color_service.py`

**Purpose:**
Query vendor color catalogs stored in the `colors` database table.

**Responsibilities:**
- List all supported vendors with metadata and color counts
- Retrieve colors for a given vendor

**Key methods:**
- `get_all_colors()` - List all colors from all vendors
- `get_vendors()` - List all vendors with metadata (from `ColorVendor` enum) and color counts (from DB)
- `get_colors_by_vendor(vendor)` - Get all colors for a `ColorVendor` member
- `get_color(vendor_key, code)` - Get a specific color by vendor and code
- `is_valid_vendor(vendor_key)` - Check if a vendor key is valid

**Does NOT:**
- Modify color data (colors are seeded reference data)
- Perform color matching (see `color_matcher.py`)
- Handle HTTP concerns

**Used by:**
- `api` blueprint (colors endpoint)
- `projects` blueprint (wizard routes)
- Any service needing vendor color lookups

---

## 🗳️ `vote_service.py`

**Purpose:**
Manage Reddit-style voting on projects.

**Responsibilities:**
- Cast, change, or remove votes (+1 / -1)
- Toggle logic (voting same value removes vote, opposite switches)
- Maintain denormalized `Project.vote_score` cache
- Bulk-query user votes for multiple projects

**Key methods:**
- `vote()` - Cast or toggle a vote
- `remove_vote()` - Remove a vote
- `get_user_vote()` - Get single user vote
- `get_user_votes_bulk()` - Get user votes for multiple projects

**Used by:**
- `api` blueprint (vote endpoints)
- `main` blueprint (bulk vote queries for templates)

---

## 🌐 `community_service.py`

**Purpose:**
Query public community patterns for display.

**Responsibilities:**
- Fetch latest public patterns
- Fetch best-voted public patterns
- Paginated browsing with sort options

**Key methods:**
- `get_latest_patterns()` - Public projects by creation date
- `get_best_patterns()` - Public projects by vote score
- `get_patterns_page()` - Paginated results with sort

**Used by:**
- `main` blueprint (index page, patterns browse page)

---

## 🧠 Architectural Rules (Mandatory)

- Services **must not** import Flask request/response objects
- Services **must not** render templates
- Services **may call other services**
- Services **own business logic**
- Routes are thin, services are authoritative

If required data is missing or ambiguous:
1. **Stop**
2. **Request clarification**
3. **Do not guess**

---

## ✅ When to Add a New Service

Add a new service when:
- Logic is reused by multiple blueprints
- A workflow spans multiple domains
- Code becomes hard to test in a route
- Business rules grow beyond simple CRUD

Do **not** add services for:
- One-off glue code
- Pure data containers
- HTTP-specific logic

---

## 📌 Summary

The services layer is the **core of correctness** in this system.

If the services are correct:
- Routes stay simple
- UI stays replaceable
- The system stays maintainable

When in doubt — move logic **into a service**, not into a route.
