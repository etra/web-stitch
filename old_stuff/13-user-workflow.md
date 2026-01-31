# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## User Workflow

### Phase 1: Registration & Login

**Route: `/auth/register` and `/auth/login`**

1. User visits home page `/`
2. Clicks "Register" → `/auth/register`
   - Enter email
   - Backend creates user (no password for MVP)
3. Or clicks "Login" → `/auth/login`
   - Enter email
   - Backend finds user by email
4. Redirect to `/projects` (project list)

---

### Phase 2: Image Preparation (Optional)

**Route: `/images` → `/images/prepare/<filename>`**

This is a **separate workflow** before creating projects. Users can prepare images in advance.

#### Step 1: Upload to Image Gallery (`/images`)
1. User goes to "Image Gallery" (`/images`)
2. Sees list of previously uploaded images (read from filesystem)
3. Clicks "Upload New Image"
4. Selects JPG/PNG file
5. Backend:
   - Saves original image to filesystem: `/uploads/<user_id>/originals/<filename>`
   - Generates thumbnail: `/uploads/<user_id>/thumbnails/<filename>_thumb.jpg`
   - NO database record created (images are listed by reading filesystem)
6. Redirect back to `/images` gallery

#### Step 2: Prepare Image (`/images/prepare/<filename>`)

**Multi-step process (Flask + Bootstrap):**

1. **Select Image:**
   - User clicks "Prepare" on an image in gallery
   - Route: `/images/prepare/<filename>` (original image filename)

2. **Step 1: Resize**
   - Preview current dimensions
   - Enter target dimensions (width × height in stitches)
   - Usually larger than final project (will resize again later)
   - Click "Next"

3. **Step 2: Color Reduction**
   - Preview with different color counts
   - Slider: Max colors (10-100)
   - Live preview updates as slider moves
   - Click "Next"

4. **Step 3: Palette Selection**
   - View quantized result
   - Option: "Map to DMC colors" checkbox
   - If checked: Shows DMC color names/codes
   - Click "Next"

5. **Step 4: Final Review**
   - Preview all layers:
     - Original
     - Processed (color-quantized)
     - Lines/edges (edge detection)
   - Toggle layer visibility
   - Click "Save Prepared Image"

6. **Backend creates:**
   - `prepared_images` database record
   - Stores ONLY configuration (JSONB):
     - Target dimensions (width, height)
     - Max colors
     - Edge detection settings
     - Original filename reference
   - Does NOT store processed images (regenerated on-demand)

7. Redirect to `/images` gallery
   - Prepared images have "Ready" badge
   - Can import into projects

**Note:** This entire preparation phase is done in Flask + Bootstrap (traditional web forms/pages).

---

### Phase 3: Project Creation

**Route: `/projects`**

1. User goes to "Projects" (`/projects`)
2. Sees list of existing projects
3. Clicks "Create New Project"

#### Option A: Empty Project
- Enter project name
- Enter grid dimensions (width × height)
- Select cloth color
- Click "Create"
- Backend creates project with one empty raster layer
- Redirect to `/project/edit/<id>`

#### Option B: From Prepared Image
- Enter project name
- Click "Import from prepared image"
- Modal shows gallery of prepared images
- Select prepared image
- Backend:
  - Creates project
  - Sets dimensions from prepared image (or resize to fit)
  - Imports 3 layers: original, processed, lines
  - Copies palette
- Redirect to `/project/edit/<id>`

---

### Phase 4: Editing (Main Working Area)

**Route: `/project/edit/<id>` - JavaScript + Canvas**

This is the **only JavaScript/Canvas page** - the main editor.

#### UI Layout

**Left Sidebar (Bootstrap cards):**
- **Tools Card:**
  - Stitch tools (Full, Half /, Half \, Quarter /, Quarter \)
  - Shape tools (Rectangle Fill, Circle Fill)
  - Line tools (Backstitch 1/2/3 strands)
  - Detail tools (French Knot)
  - Utility (Eyedropper, Eraser)

- **Palette Card:**
  - Color swatches with symbols
  - Click to select active color
  - Add/remove colors

**Center: Canvas**
- Grid with stitches
- Pan/zoom (mouse drag, wheel)
- 5×5 pixel cells (base size)
- Major grid lines every 10 cells
- Click/drag to draw

**Right Sidebar:**
- **Layers Panel:**
  - List of layers
  - Checkbox: visible/hidden
  - **Checkbox: "Active for export"** ← Important!
  - Opacity slider (image layers)
  - Drag to reorder
  - Add/delete buttons

- **Version History Panel:**
  - List of saves (timestamps)
  - Click to load previous version
  - "Current" indicator

**Top Toolbar:**
- Undo/Redo buttons
- View mode (stitches/symbols/both)
- Zoom controls
- Save button (manual save)
- "Back to Projects" link

**Bottom Status Bar:**
- Cursor position (X, Y)
- Grid size
- Save status ("Saved" / "Saving..." / "Unsaved")

#### Editing Actions

1. **Drawing:**
   - Select stitch type from left sidebar
   - Select color from palette
   - Select tool (e.g., Full Stitch)
   - Click/drag on canvas
   - Changes save to localStorage immediately
   - Backend save every 10s + on mouse release

2. **Importing Prepared Image (during editing):**
   - Click "Import Layer" button
   - Modal shows prepared images
   - Select one
   - Backend adds 3 layers to current project
   - Canvas updates

3. **Layer Management:**
   - Toggle visibility (eye icon)
   - **Mark "Active for export"** (checkbox) ← User decides which layers to export
   - Reorder by dragging
   - Delete layer

4. **Version History:**
   - Every backend save creates snapshot (if 5+ min since last)
   - Right sidebar shows list
   - Click timestamp to preview
   - Click "Restore" to load that version

5. **Save:**
   - Auto-save every 10s + mouse release
   - Manual save button (immediate)
   - Status indicator updates

---

### Phase 5: Export

**Route: `/project/export/<id>` - Flask (server-side)**

1. User clicks "Export PDF" button in editor
2. Redirects to `/project/export/<id>`
3. Backend:
   - Loads project
   - Filters layers: **only those marked "Active for export"**
   - Renders using OpenCV:
     - Grid with stitches
     - Symbols overlay
     - Grid numbers (row/column labels)
   - Generates PDF:
     - Pattern pages
     - Color key (palette with DMC codes/symbols)
     - Project info (name, dimensions, stitch count)
4. Returns PDF file for download
5. User clicks "Back to Projects"

---

## Page-by-Page Technology Breakdown

| Page/Route | Technology | Purpose |
|------------|------------|---------|
| `/` | Flask + Bootstrap | Landing page |
| `/auth/*` | Flask + Bootstrap | Login/register forms |
| `/images` | Flask + Bootstrap | Image gallery (table/cards, read from filesystem) |
| `/images/prepare/<filename>` | Flask + Bootstrap | Multi-step form wizard (original image filename) |
| `/projects` | Flask + Bootstrap | Project list (table/cards) |
| `/project/edit/<id>` | **JavaScript + Canvas** | Interactive editor (project UUID) |
| `/project/export/<id>` | Flask (backend) | PDF generation (project UUID) |

**Key insight:** Only one page uses JavaScript/Canvas - the editor. Everything else is traditional Flask templates with Bootstrap.
