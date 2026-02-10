# TODO

## Backend Change Required: Add Path Stitch Support to Layer Model

### Context

The frontend cross-stitch editor currently stores stitches as point-based cells in a sparse map per layer. Each cell is keyed by `String(y * width + x)` and contains a `paletteIndex` and `stitchType`.

We need to add support for path-based stitches (backstitch, long stitch) which have a start point and end point rather than occupying a single grid cell. These will be stored in a separate `paths` array on each layer, alongside the existing `cells` map.

### What Changes

The Layer object in the project state gains a new field: `paths`.

Current Layer structure:
```json
{
  "id": "layer-1",
  "name": "Layer 1",
  "type": "raster",
  "visible": true,
  "editable": true,
  "activeForExport": true,
  "cells": {
    "42": { "paletteIndex": 0, "stitchType": "full" },
    "105": { "paletteIndex": 2, "stitchType": "half" }
  }
}
```

New Layer structure:
```json
{
  "id": "layer-1",
  "name": "Layer 1",
  "type": "raster",
  "visible": true,
  "editable": true,
  "activeForExport": true,
  "cells": {
    "42": { "paletteIndex": 0, "stitchType": "full" },
    "105": { "paletteIndex": 2, "stitchType": "half" }
  },
  "paths": [
    {
      "startX": 2,
      "startY": 3,
      "endX": 5,
      "endY": 3,
      "paletteIndex": 1,
      "stitchType": "backstitch"
    }
  ]
}
```

### PathStitch Object Definition

| Field        | Type    | Description                               |
|--------------|---------|-------------------------------------------|
| startX       | integer | Grid X coordinate of path start           |
| startY       | integer | Grid Y coordinate of path start           |
| endX         | integer | Grid X coordinate of path end             |
| endY         | integer | Grid Y coordinate of path end             |
| paletteIndex | integer | Index into the layer's palette array      |
| stitchType   | string  | One of: "backstitch", "long", "special"   |

### Affected Endpoints

Both existing endpoints need to handle the new `paths` field:

- [ ] **GET /editor/{projectId}/api/state** — Response must include `paths` array in each layer (default to `[]` if none exist)
- [ ] **POST /editor/{projectId}/api/state** — Request body will include `paths` array in each layer, must be persisted

### Backwards Compatibility

- [ ] If `paths` is missing from a saved layer, treat it as `[]` (empty array)
- [ ] The `cells` map is unchanged — existing point stitches continue to work exactly as before
- [ ] No changes to any other fields in ProjectState, EditorConfig, or the save/load response format

### Database/Storage

- [ ] The `paths` array needs to be stored and retrieved per layer. How you persist it (JSON column, separate table, etc.) is up to you — the frontend only cares about the JSON shape above in the API request/response.

---

## Refactor APIs to Support New Normalized Models

### Context

Project state has been normalized from a monolithic `state` JSON column into `project_layers` and `project_palette_colors` tables. The current APIs still operate on the full state snapshot (assemble/decompose via `ProjectService.assemble_state()` / `save_state()`). Future work should add targeted endpoints.

### Planned Endpoints

- [ ] **GET /api/project/{projectId}** — Return full project 
- [ ] **PATCH /editor/{projectId}/api/layers/{layerId}** — Update a single layer's properties (name, visible, editable, etc.)
- [ ] **PATCH /editor/{projectId}/api/layers/{layerId}/cells** — Partial cell update (diff-based instead of full snapshot)
- [ ] **GET /editor/{projectId}/api/palette** — Return palette colors
- [ ] **PATCH /editor/{projectId}/api/palette/{colorRef}** — Update a single palette color

### Drop Legacy State Column

- [ ] Once verified stable in production, create a migration to drop `projects.state` column
- [ ] Remove the fallback code in `assemble_state()` that reads from the legacy column
