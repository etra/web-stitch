# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## Data Flow

```
User edits canvas
    ↓
Update in-memory state
    ↓
Save to localStorage immediately (crash recovery)
    ↓
Mark dirty for backend sync
    ↓
Every 10s OR on mouse release
    ↓
Compute diff from last saved state
    ↓
POST diff to backend
    ↓
Backend applies diff + stores full current state
    ↓
Optional: Create snapshot for version history
```

## Key Implementation Details

### State Management (Frontend)

**In-memory state with layers:**
```javascript
{
  projectId: "uuid",
  name: "My Pattern",
  width: 100,           // grid width in stitches
  height: 100,          // grid height in stitches
  clothColor: "#ffffff", // background color

  palette: [
    {
      id: "c1",
      vendor: "DMC",       // "DMC", "Anchor", or null
      code: "310",         // vendor color code
      name: "Black",
      rgbHex: "#000000",
      symbol: "A",         // single character (ANSI unicode)
      sortIndex: 0
    },
    // ... more colors
  ],

  layers: [
    {
      id: "bg1",
      type: "image",       // Background image layer
      name: "Reference photo",
      visible: true,       // Show/hide in editor
      activeForExport: false,  // Don't include in PDF export
      editable: false,     // Read-only (original image reference)
      opacity: 0.5,        // 0.0 to 1.0
      imageData: "data:image/png;base64,..." // or blob URL
    },
    {
      id: "layer1",
      type: "raster",      // Drawing layer (stitches in cells)
      name: "Main stitches",
      visible: true,
      activeForExport: true,   // Include in PDF export
      editable: true,      // User can edit
      cells: [
        null,  // empty cell (shows cloth color)
        {
          paletteIndex: 1,         // index into palette array
          stitchType: "full"       // full cross stitch (X)
        },
        {
          paletteIndex: 2,
          stitchType: "half-slash" // half stitch /
        },
        {
          paletteIndex: 3,
          stitchType: "quarter-backslash" // quarter stitch \
        },
        {
          paletteIndex: 4,
          stitchType: "french-knot"        // French knot
        },
        // ... width * height cells (total: width × height)
      ]
    },
    {
      id: "layer2",
      type: "backstitch",  // Vector overlay layer (lines between cells)
      name: "Backstitches",
      visible: true,
      activeForExport: true,
      editable: true,
      lines: [
        {
          paletteIndex: 0,         // color
          strands: 2,              // 1, 2, or 3 strands (line thickness)
          x1: 5.5, y1: 3.0,       // start point (can be between cells)
          x2: 7.5, y2: 3.0        // end point
        },
        // ... array of backstitch lines
      ]
    },
    {
      id: "layer3",
      type: "raster",
      name: "Highlights",
      visible: true,
      activeForExport: true,
      editable: true,
      cells: [/* ... */]
    }
  ],

  activeLayerId: "layer1",  // which layer user is currently drawing on

  properties: {
    majorGridInterval: 10,  // Draw thicker grid lines every N cells (default: 10)
    showGridNumbers: true,  // Show row/column numbers on edges (v1.1)
    defaultStitchType: "full"  // Default stitch type for new cells
  }
}
```

**Cell structure:**
Each cell in a raster layer is either `null` (empty) or an object:
```javascript
{
  paletteIndex: 0-255,     // index into project palette
  stitchType: "full",      // type of stitch (see list below)
}
```

**Stitch types (v1):**
- `full` - Full cross stitch (X)
- `half-slash` - Half stitch (/) - bottom-left to top-right
- `half-backslash` - Half stitch (\\) - top-left to bottom-right
- `quarter-slash` - Quarter stitch (/) in corner
- `quarter-backslash` - Quarter stitch (\\) in corner
- `french-knot` - French knot (filled circle)

**Stitch types (v1.1):**
- `three-quarter` - Three-quarter stitch (half + quarter combination)
- `bead` - Diamond painting bead (circle or square)
- `long-stitch` - Stitch spanning multiple cells

**Layer types:**
- `image` - Background reference image (has `imageData`, `opacity`)
- `raster` - Grid-based stitches (has `cells` array)
- `backstitch` - Vector lines for outlines (has `lines` array with x1,y1,x2,y2 coordinates)

**Backstitch structure:**
Each backstitch is a line object:
```javascript
{
  paletteIndex: 0,      // color index
  strands: 2,           // 1, 2, or 3 (determines line thickness)
  x1: 5.5, y1: 3.0,    // start point (can be at cell edges/corners)
  x2: 7.5, y2: 3.0     // end point
}
```
Note: Backstitch coordinates can be fractional (e.g., 5.5 = edge between cell 5 and 6)

**Undo/redo:**
- Keep array of up to 50 previous states in memory
- Persist to localStorage on each edit
- Lost on page refresh if not in localStorage (acceptable for v1)
- Each undo state is a full clone of project state (including all layers)

**localStorage schema:**
```javascript
{
  state: {/* current project state with layers */},
  undoStack: [{/* previous states */}],
  timestamp: 1234567890
}
```

### Diff Format

When saving to backend, send only what changed:

```javascript
{
  changes: [
    {
      type: "cell",
      layerId: "layer1",
      index: 1523,
      from: null,                              // was empty
      to: {                                     // now has stitch
        paletteIndex: 5,
        stitchType: "full",
        rotation: 0
      }
    },
    {
      type: "cell",
      layerId: "layer1",
      index: 1524,
      from: { paletteIndex: 2, stitchType: "full", rotation: 0 },
      to: { paletteIndex: 5, stitchType: "half", rotation: 90 }
    },
    {
      type: "palette",
      palette: [...]                            // if palette changed
    },
    {
      type: "layer",
      action: "add",                            // "add" | "remove" | "update"
      layer: { id: "layer2", type: "raster", ... }
    },
    {
      type: "layer",
      action: "update",
      layerId: "layer1",
      updates: { visible: false }               // toggle visibility
    },
    {
      type: "clothColor",
      value: "#f0f0f0"
    }
  ],
  timestamp: 1234567890
}
```

Server applies diff and stores full current state (not cumulative diffs).

### Backend Storage

**projects table:**
- Stores full current state as JSONB (includes all layers, palette, metadata)
- Fast to load (no decompression needed for small/medium projects)
- For large projects: Can compress layer cell data as BYTEA if needed

**project_snapshots table:**
- Timestamped snapshots for version history
- Created every ~5 minutes or every ~10 saves (configurable)
- **Retention: Keep snapshots for 7 days** (auto-delete older ones)
- Optional: Store diff with each snapshot to show "what changed"
- Each snapshot is a full copy of project state at that point in time

### Multiple Tab Detection

**Not supported in v1. Detection strategy:**

```javascript
// Use BroadcastChannel API
const channel = new BroadcastChannel(`project_${projectId}`);

channel.addEventListener('message', (event) => {
  if (event.data.type === 'ping') {
    // Another tab detected - show warning and disable editing
    showError("Project open in another tab");
    disableEditing();
  }
});

// Announce presence on load
channel.postMessage({ type: 'ping' });
```
