# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## API Endpoints

**Base path:** `/api/v1`

### Authentication (Email-only for MVP)
- `POST /auth/login` - Find or create user by email, return session/JWT
  - Body: `{ email: "user@example.com" }`
  - Response: `{ userId: "uuid", email: "..." }`
- `GET /auth/me` - Get current user (from session/JWT)

### Projects
- `POST /projects` - Create new project
  - Body: `{ name: "My Pattern", width: 100, height: 100, clothColor: "#fff" }`
  - Creates project with one empty raster layer
- `GET /projects` - List user's projects (paginated)
- `GET /projects/{id}` - Get full project state (all layers, palette, etc.)
- `PUT /projects/{id}` - Save diff (returns success + timestamp)
  - Body: `{ changes: [...], timestamp: 123456 }`
- `DELETE /projects/{id}` - Delete project
- `PATCH /projects/{id}` - Update metadata (name, dimensions, cloth color)

### Layers
- `POST /projects/{id}/layers` - Add new layer (raster or image)
  - Body: `{ type: "raster"|"image", name: "...", imageData: "..." }`
- `PATCH /projects/{id}/layers/{layerId}` - Update layer (rename, visibility, opacity)
- `DELETE /projects/{id}/layers/{layerId}` - Remove layer
- `POST /projects/{id}/layers/reorder` - Reorder layers
  - Body: `{ layerIds: ["id1", "id2", "id3"] }` (new order)

### Palette
- `POST /projects/{id}/palette` - Add color to palette
- `PATCH /projects/{id}/palette/{colorId}` - Update color (symbol, sort order)
- `DELETE /projects/{id}/palette/{colorId}` - Remove color from palette

### Image Import
- `POST /projects/{id}/import` - Upload image + settings `{maxColors}` (synchronous)
  - Generates initial palette and creates image layer
  - Returns updated project state

### Version History
- `GET /projects/{id}/versions` - List snapshots (last 7 days, paginated)
- `GET /projects/{id}/versions/{snapshotId}` - Get specific snapshot
- `POST /projects/{id}/restore/{snapshotId}` - Restore from snapshot

### Export
- `POST /projects/{id}/export/png` - Export as PNG
  - Body: `{ mode: "blocks"|"symbols"|"both", layerIds: ["id1", "id2"] }`
  - Returns PNG file
- `POST /projects/{id}/export/pdf` - Export as PDF (v1.1)

### Resize/Scale
- `POST /projects/{id}/resize` - Create resized copy (v1: nearest-neighbor scaling)
  - Body: `{ width: 200, height: 200 }`
  - Returns new project with scaled pattern
