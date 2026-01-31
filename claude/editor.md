# Editor Architecture

This document describes the cross-stitch pattern editor, a web-based Canvas application with a Flask backend.

---

## Overview

The editor is a **web-based canvas editor for cross-stitch patterns** with strict separation of concerns:

- **Backend (Python/Flask):** HTTP routing, authentication, persistence, API endpoints
- **Frontend (JavaScript):** State management, canvas rendering, user interaction, local caching
- **Database (PostgreSQL):** Project persistence with JSON state
- **Browser Storage (IndexedDB):** Local caching for crash recovery and undo history

**Key Design Principle:** Stateless backend that stores full snapshots. The JavaScript editor maintains the source of truth for the current session.

---

## File Structure

```
stitch/blueprints/editor/
├── __init__.py              # Blueprint registration (url_prefix='/editor')
├── routes.py                # Page route (canvas/editor.html)
├── schemas.py               # Pydantic validation schemas
├── templates/
│   └── editor/
│       └── canvas.html      # Full editor UI template
├── api/
│   ├── __init__.py
│   ├── state.py             # GET/POST state endpoints
│   ├── render.py            # Thumbnail generation
│   └── layers.py            # Layer operations (future)
└── static/
    └── editor/
        ├── css/
        │   └── editor.css   # Editor-specific styles
        └── js/
            ├── main.js      # Editor class + event handling
            ├── state.js     # StateManager (undo/redo)
            ├── renderer.js  # Canvas rendering
            ├── viewport.js  # Pan/zoom/coordinates
            ├── tools.js     # Drawing tools
            ├── api.js       # Backend communication
            ├── storage.js   # IndexedDB persistence
            ├── view.js      # UI components (StitchPicker)
            └── stitches/    # Stitch type definitions
                ├── base.js
                ├── full.js
                ├── half.js
                ├── quarter.js
                └── index.js
```

---

## Backend

### Routes

| Method | Path | Handler | Purpose |
|--------|------|---------|---------|
| GET | `/editor/<project_id>` | `canvas()` | Load editor page with project data |
| GET | `/editor/<project_id>/api/state` | `get_state()` | Fetch full project state |
| POST | `/editor/<project_id>/api/state` | `save_state()` | Save project state |
| GET | `/editor/<project_id>/api/thumbnail` | `thumbnail()` | Generate PNG thumbnail |

### Page Loading Flow

1. User navigates to `/editor/<project_id>`
2. `routes.canvas()` loads project via `ProjectService.get_project()`
3. Verifies user ownership
4. Passes project data as JSON to template
5. Template embeds data: `window.PROJECT_DATA = {{ project_data | tojson | safe }}`

### Services Used

**ProjectService** (`stitch/services/project_service.py`):
- `get_project(project_id, user_id)` - Load project
- `update_project(project_id, user_id, state=...)` - Save state
- `create_initial_state(width, height)` - Create empty project state

**PatternRenderer** (`stitch/services/pattern_renderer.py`):
- `render_colored_pattern()` - Generate colored preview image
- Used by thumbnail endpoint

---

## Frontend Architecture

### Core Modules

#### Editor (`main.js`)

Main orchestrator that initializes all sub-systems:

```javascript
class Editor {
    constructor(projectData) {
        this.stateManager = new StateManager(projectData);
        this.viewport = new Viewport(...);
        this.renderer = new Renderer(canvas, viewport);
        this.toolManager = new ToolManager(stateManager, viewport);
        this.storage = new Storage(projectId);  // IndexedDB
        this.api = new API(projectId);          // Backend communication
    }
}
```

#### StateManager (`state.js`)

Single source of truth for application state:

```javascript
class StateManager {
    state       // Current project state
    undoStack   // History (max 50 snapshots)
    redoStack   // Redo history
    isDirty     // Unsaved changes flag
    listeners   // Change subscribers

    // Core operations
    updateState(updates, createUndoSnapshot)
    updateCell(layerId, x, y, cellData)
    updatePalette(newPalette)

    // Layer operations
    addLayer(layerType)
    deleteLayer(layerId)
    setActiveLayer(layerId)

    // Undo/Redo
    undo()
    redo()

    // Subscriptions
    subscribe(callback)
    notify()
}
```

#### Renderer (`renderer.js`)

Handles all Canvas rendering:

```javascript
class Renderer {
    renderMode  // 'color', 'symbol', 'both'
    stitches    // Stitch type registry

    render(state, toolPreview)
    renderRasterLayer(layer, palette, gridWidth, gridHeight)
    drawStitch(gridX, gridY, cell, palette, cellSize)
    drawGrid(gridWidth, gridHeight)
    drawHoverHighlight(gridX, gridY)

    registerStitch(stitch)
    setRenderMode(mode)
}
```

**Render Modes:**
- **Color:** Colored cross stitches (default)
- **Symbol:** Text symbols on white background
- **Both:** Colored background with symbol overlay

#### Viewport (`viewport.js`)

Handles pan, zoom, and coordinate conversions:

```javascript
class Viewport {
    zoom        // Current zoom level
    offsetX/Y   // Pan offset in pixels
    baseCellSize = 20

    screenToGrid(screenX, screenY)  // Screen → grid coords
    gridToScreen(gridX, gridY)      // Grid → screen coords
    getCellSize()                   // baseCellSize * zoom

    pan(dx, dy)
    zoomAt(screenX, screenY, delta)
    getVisibleBounds()              // For viewport culling
}
```

#### ToolManager (`tools.js`)

Manages drawing tools and brush behavior:

```javascript
class ToolManager {
    currentTool       // 'brush', 'eraser', 'eyedropper', 'rectangle', 'line'
    currentStitchType // 'full', 'half-slash', etc.
    currentColorIndex // Index into palette

    setTool(tool)
    setStitchType(type)
    setColorIndex(index)

    startDrawing(screenX, screenY)
    continueDrawing(screenX, screenY)
    stopDrawing()

    applyBrush(layerId, x, y)     // Place stitch
    applyEraser(layerId, x, y)    // Delete stitch
    applyEyedropper(layerId, x, y)// Pick color/stitch
}
```

#### API (`api.js`)

HTTP client for backend communication:

```javascript
class API {
    async saveProject(state)    // POST /editor/<id>/api/state
    async loadProject()         // GET /editor/<id>/api/state
    async getAvailableColors()  // GET /api/colors
}
```

#### Storage (`storage.js`)

IndexedDB wrapper for crash recovery:

```javascript
class Storage {
    async save(state, undoStack, redoStack)
    async load()  // Returns {state, undoStack, redoStack, timestamp}
}
```

---

## Data Flow

### Drawing a Stitch

```
User clicks canvas
    ↓
canvas.onMouseDown → Editor.onMouseDown()
    ↓
ToolManager.startDrawing(screenX, screenY)
    ↓
    converts screen → grid coords
    ToolManager.applyBrush(layerId, gridX, gridY)
        ↓
        StateManager.updateCell(layerId, x, y, cellData)
            ↓
            saves undo snapshot
            mutates state.layers[layer].cells[key]
            sets isDirty = true
            calls notify()
    ↓
StateManager.notify()
    ↓
    Renderer.render(state)
    Editor.updateUI()
    Storage.save() (async to IndexedDB)
```

### Auto-Save to Backend

```
Every 10 seconds:
    if StateManager.isDirty:
        API.saveProject(state)
            ↓
            POST /editor/<id>/api/state
            ↓
            ProjectService.update_project(id, user_id, state=...)
            ↓
            Saves to PostgreSQL
        ↓
        StateManager.markSaved()
```

### Undo/Redo

```
User presses Ctrl+Z
    ↓
StateManager.undo()
    ↓
    push current state to redoStack
    pop from undoStack → current state
    notify()
    ↓
Renderer re-renders
```

---

## Project State Schema

```json
{
  "palette": [
    {
      "id": "c1234567890",
      "vendor": "DMC",
      "code": "321",
      "name": "Red",
      "rgbHex": "#ff0000",
      "symbol": "A",
      "sortIndex": 0
    }
  ],
  "layers": [
    {
      "id": "layer-uuid",
      "type": "raster",
      "name": "Main stitches",
      "visible": true,
      "activeForExport": true,
      "editable": true,
      "cells": {
        "1050": {
          "paletteIndex": 0,
          "stitchType": "full"
        }
      }
    }
  ],
  "activeLayerId": "layer-uuid",
  "properties": {
    "majorGridInterval": 10,
    "showGridNumbers": false,
    "defaultStitchType": "full"
  }
}
```

### Cell Storage

Cells are stored **sparsely** - only occupied cells exist in the `cells` object.

**Cell Key Format:** `"${y * width + x}"` (linear index)

**Cell Data:**
- `paletteIndex`: Index into palette array
- `stitchType`: Registered stitch type ID (e.g., "full", "half-slash")

---

## Stitch Types

Stitch types are defined as classes extending `BaseStitch`:

```javascript
class BaseStitch {
    id          // e.g., 'full', 'half-slash'
    name        // Display name
    category    // Grouping: 'Full & Half', 'Quarter', etc.
    icon        // Unicode symbol

    draw(ctx, x, y, size, color)  // Render on canvas
    getSymbol()                    // For symbol mode
}
```

**Available Stitch Types:**

| Category | Stitches |
|----------|----------|
| Full & Half | Full, Half Slash, Half Backslash |
| Quarter | Quarter TL, TR, BL, BR |
| Three-Quarter | 3/4 TL, TR, BL, BR |
| Long | Long Vertical, Long Horizontal |
| Backstitch | Backstitch H, V, Slash, Backslash |
| Special | Petite, French Knot |

---

## Key Architectural Decisions

### Backend
- Routes are thin (validation + delegation only)
- All business logic in services
- State stored as JSON in PostgreSQL
- Stateless: no session memory of editor state

### Frontend
- Single source of truth: `StateManager`
- Unidirectional data flow (action → state change → render)
- Efficient viewport culling (only render visible cells)
- Sparse cell storage (only occupied cells)
- Undo history in memory (up to 50 snapshots)

### Persistence
- POST sends full state to backend (no diffing)
- Backend stores snapshot
- IndexedDB provides local crash recovery
- Auto-save every 10 seconds if dirty

### Performance
- Canvas culling prevents rendering off-screen cells
- Cell size responsive to zoom level
- Grid numbers only drawn at sufficient zoom
- Stitch registration uses Map for O(1) lookup

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Z / Cmd+Z | Undo |
| Ctrl+Y / Cmd+Shift+Z | Redo |
| Ctrl+S / Cmd+S | Save |
| Delete / Backspace | Clear hovered cell |

---

## Related Documentation

- [Blueprints](blueprints.md) - Blueprint architecture
- [Services](service.md) - Service layer patterns
- [Database Models](database-models.md) - Project model schema
