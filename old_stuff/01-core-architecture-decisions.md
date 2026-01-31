# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## Core Architecture Decisions

### Simplified Persistence Model

**We deliberately chose a simpler architecture than typical collaborative editors:**

- **Frontend-heavy:** All editing happens in-memory with immediate localStorage backup
- **Periodic backend sync:** Save diffs to backend every 10s or on mouse release
- **Single window only:** Multiple tabs not supported - detect and warn users
- **Client-side undo/redo:** In-memory stack (max 50 states) persisted to localStorage
- **Version history:** Backend keeps timestamped snapshots for 7 days

This is simpler and faster to build than event-sourcing with operational transforms. We can add complexity later if needed.

### Custom Canvas Renderer

**We build our own grid renderer from scratch** - no existing library fits our needs:

- **Why not Fabric.js/Konva.js?** Designed for free-form graphics, not grid-constrained cross-stitch
- **Why not ag-Grid/Handsontable?** Spreadsheet libraries, wrong paradigm
- **Why not pixel art editors?** Don't support stitch types (full/half/quarter), layers, or DMC palettes

**Our approach:**
- React for UI components (palette, tools, layers panel)
- Vite for build tooling
- Custom Canvas rendering (300-400 lines) for grid, stitches, layers
- Full control over rendering different stitch types (X, /, \, •, etc.)

### Layers System

Projects support multiple layers:
- **Image layers:** Background reference photos (uploaded by user)
- **Raster layers:** Drawing layers with stitches (can have multiple)
- **Layer controls:** Toggle visibility, reorder, delete
- **Export:** Select which layers to include in final output

### Authentication Strategy (MVP)

**Email-only for MVP** - No password required:
- User enters email → backend finds or creates user by email
- Future: Add proper auth (password, OAuth) in v1.1
- This is for local/personal use only - not production-ready security
