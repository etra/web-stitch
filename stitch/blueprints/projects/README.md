# Projects Blueprint

Handles project CRUD operations and project creation wizard.

## URL Prefix

`/projects`

## Routes

### Core CRUD Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/projects/` | `list` | List all user projects |
| GET, POST | `/projects/create` | `create` | Create new project (simple form) |
| GET, POST | `/projects/<project_id>/edit` | `edit` | Edit project settings |
| POST | `/projects/<project_id>/delete` | `delete` | Delete a project |

### Project Creation Wizard (3 steps)

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET, POST | `/projects/new` | `new_setup` | Step 1: Name, description, size |
| GET, POST | `/projects/new/vendor` | `new_vendor` | Step 2: Select thread vendor |
| GET, POST | `/projects/new/colors` | `new_colors` | Step 3: Pick colors and create project |

## Route Details

### Core CRUD

#### `GET /projects/`

Lists all projects for the current user.

**Inputs:** None

**Outputs:** HTML (`projects/list.html`)

**Side effects:** None

**Auth/session:** Requires login, reads `session.user_id`

#### `GET, POST /projects/create`

Simple project creation form.

**Inputs (POST):**
- `name` (form): Project name (required)
- `width` (form): Canvas width 1-1000 (required)
- `height` (form): Canvas height 1-1000 (required)

**Outputs:** HTML form (GET) or redirect to list (POST success)

**Side effects:** Creates project in database (POST)

**Auth/session:** Requires login, reads `session.user_id`

#### `GET, POST /projects/<project_id>/edit`

Edit project metadata.

**Inputs:**
- `project_id` (path): Project ID
- Form fields same as create, plus:
- `difficulty` (form): Optional difficulty level (1=Beginner, 2=Intermediate, 3=Advanced)
- `tags` (form): Optional list of tag names

**Outputs:** HTML form (GET) or redirect to list (POST success)

**Side effects:** Updates project and tags in database (POST)

**Auth/session:** Requires login, reads `session.user_id`

#### `POST /projects/<project_id>/delete`

Delete a project.

**Inputs:**
- `project_id` (path): Project ID

**Outputs:** Redirect to list

**Side effects:** Deletes project from database

**Auth/session:** Requires login, reads `session.user_id`

### Project Creation Wizard

All wizard routes use `WizardService` to manage session state.

#### `GET, POST /projects/new`

Step 1: Configure project basics.

**Inputs (POST):**
- `name` (form): Project name (required)
- `description` (form): Optional description
- `width` (form): Canvas width 10-1000 (required)
- `height` (form): Canvas height 10-1000 (required)
- `difficulty` (form): Optional difficulty level (1=Beginner, 2=Intermediate, 3=Advanced)
- `tags` (form): Optional list of tag names

**Outputs:** HTML form (GET) or redirect to vendor step (POST)

**Side effects:** Initializes wizard session state

**Auth/session:** Requires login, writes `session.project_wizard`

#### `GET, POST /projects/new/vendor`

Step 2: Select thread vendor.

**Inputs (POST):**
- `vendor` (form): Vendor key (dmc|hama|artkal|nabbi)

**Outputs:** HTML form (GET) or redirect to colors step (POST)

**Side effects:** Updates wizard session state

**Auth/session:** Requires login, reads/writes `session.project_wizard`

#### `GET, POST /projects/new/colors`

Step 3: Pick colors and create project.

**Inputs (POST):**
- `color_codes` (form): List of selected color codes

**Outputs:** HTML form (GET) or redirect to list (POST success)

**Side effects:** Creates project in database, clears wizard session

**Auth/session:** Requires login, reads `session.user_id`, reads/clears `session.project_wizard`

## Session Keys

| Key | Usage |
|-----|-------|
| `user_id` | Read to identify current user for all operations |
| `project_wizard` | Wizard state storage (managed by `WizardService`) |

## Static Assets

Located in `stitch/blueprints/projects/static/projects/`:

| File | Purpose |
|------|---------|
| `projects.css` | Styles for project list, form, and wizard steps |
| `projects.js` | JavaScript for color picker sync, size preview, and color selection |

**CSS classes provided:**
- `.project-thumb` - Thumbnail container in project list
- `.size-preview-*` - Canvas size preview in setup wizard
- `.selected-colors-*` - Selected colors UI in colors wizard

**JavaScript functions provided:**
- `initColorPickerSync()` - Sync color picker with text input (form.html)
- `initSizePreview()` - Canvas size preview (setup.html)
- `initTagInput()` - Tag input with autocomplete and chips (setup.html, form.html)
- `initColorSelection()` - Color selection functionality (colors.html)

Templates also use global wizard styles from `stitch/static/css/wizard.css`.

## Related Blueprints

- **Editor Blueprint** (`/editor`) - Canvas editor for created projects
- **Pattern Blueprint** (`/pattern`) - Pattern creation from images (separate wizard flow)
