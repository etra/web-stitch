# Project Resource

API routes for project data and layers.

## Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/api/projects` | `get_projects` | Returns all projects for the current user |
| GET | `/api/projects/<project_id>` | `get_project_data` | Returns basic project metadata |
| GET | `/api/projects/<project_id>/layers` | `get_project_layers` | Returns layer data for a project |
| POST | `/api/projects/<project_id>/palette/colors` | `add_palette_colors` | Add colors from catalog to project palette |
| POST | `/api/projects/<project_id>/palette/colors/remove` | `remove_palette_colors` | Remove colors from project palette |
| POST | `/api/projects/<project_id>/palette/merge` | `merge_palette_colors` | Merge palette colors (remap and delete source) |

## `GET /api/projects`

Returns all projects for the current user (metadata only).

**Inputs:** None

**Outputs:** JSON object with `projects` array. Each project contains:
- `id` (str): Project UUID
- `name` (str): Project name
- `description` (str | null): Project description
- `width` (int): Grid width in stitches
- `height` (int): Grid height in stitches
- `clothColor` (str): Cloth background color (hex)

**Response schema:** `ProjectsListResponse` (see `schema.py`)

**Auth/session:** Login required. Uses `session['user_id']` to filter projects.

**Side effects:** None (read-only)

**Example response:**
```json
{
  "projects": [
    {
      "id": "abc-123",
      "name": "My Pattern",
      "description": null,
      "width": 100,
      "height": 80,
      "clothColor": "#ffffff"
    }
  ]
}
```

## `GET /api/projects/<project_id>`

Returns full project data including colors, layers (with cells and paths), and properties.

**Inputs:**
- `project_id` (path parameter): Project UUID

**Outputs:** JSON object with `project` containing:
- `id` (str): Project UUID
- `name` (str): Project name
- `description` (str | null): Project description
- `width` (int): Grid width in stitches
- `height` (int): Grid height in stitches
- `clothColor` (str): Cloth background color (hex)
- `status` (int): Project status (-1 deleted, 0 default, 1 public, 2 private)
- `activeLayerId` (str | null): Currently active layer UUID
- `createdAt` (str | null): ISO 8601 timestamp
- `updatedAt` (str | null): ISO 8601 timestamp
- `colors` (array): Project colors from `project_colors` (see `ProjectColorResponse`)
- `layers` (array): Layers with cells and paths (see `LayerResponse`)
- `properties` (object): Editor properties (majorGridInterval, showGridNumbers, defaultStitchType)

**Response schema:** `FullProjectDataResponse` (see `schema.py`)

**Auth/session:** Login required. Uses `session['user_id']` to verify ownership.

**Side effects:** None (read-only)

**Error responses:**
- `404` — Project not found or not owned by current user

**Example response:**
```json
{
  "project": {
    "id": "abc-123",
    "name": "My Pattern",
    "description": null,
    "width": 100,
    "height": 80,
    "clothColor": "#ffffff",
    "status": 0,
    "activeLayerId": "layer-uuid",
    "createdAt": "2025-01-15T12:00:00",
    "updatedAt": "2025-01-15T14:30:00",
    "colors": [
      {"id": "color-uuid", "colorId": 42, "symbol": "A"}
    ],
    "layers": [
      {
        "id": "layer-uuid",
        "type": "raster",
        "name": "Main stitches",
        "visible": true,
        "activeForExport": true,
        "editable": true,
        "opacity": null,
        "sortOrder": 0,
        "cells": {
          "0": {"color": "color-uuid", "stitch": "full"}
        },
        "paths": [
          {"startX": 2, "startY": 3, "endX": 5, "endY": 3, "color": "color-uuid", "stitch": "backstitch"}
        ]
      }
    ],
    "properties": {
      "majorGridInterval": 10,
      "showGridNumbers": false,
      "defaultStitchType": "full"
    },
}
}
```

## `GET /api/projects/<project_id>/layers`

Returns layer data for a project.

**Inputs:**
- `project_id` (path parameter): Project UUID

**Outputs:** JSON object with `layers` array. Each layer contains:
- `id` (str): Layer UUID
- `type` (str): Layer type (`raster` or `reference`)
- `name` (str): Layer name
- `visible` (bool): Whether layer is visible
- `activeForExport` (bool): Whether to include in exports
- `editable` (bool): Whether layer can be edited
- `opacity` (float | null): Opacity value (only for reference layers)
- `cells` (object): Sparse cell data `{"cellIndex": {"paletteIndex": int, "stitchType": str}}`

**Response schema:** `ProjectLayersResponse` (see `schema.py`)

**Auth/session:** Login required. Uses `session['user_id']` to verify ownership.

**Side effects:** None (read-only)

**Error responses:**
- `404` — Project not found or not owned by current user

**Example response:**
```json
{
  "layers": [
    {
      "id": "layer-uuid",
      "type": "raster",
      "name": "Main stitches",
      "visible": true,
      "activeForExport": true,
      "editable": true,
      "opacity": null,
      "cells": {
        "0": {"paletteIndex": 3, "stitchType": "full"}
      }
    }
  ]
}
```

## `POST /api/projects/<project_id>/palette/colors`

Add colors from the catalog to a project's palette. Duplicates (colors already in the palette) are silently skipped. Symbols are auto-assigned using the A-Z, AA-AZ, BA-BZ... sequence, skipping symbols already in use.

**Inputs:**
- `project_id` (path parameter): Project UUID
- JSON body:
  - `colorIds` (array of int): Color IDs from the `colors` table to add

**Outputs:** JSON object with `colors` array of newly added palette entries. Each entry contains:
- `id` (str): ProjectColor UUID
- `colorId` (int): Reference to colors.id
- `symbol` (str): Assigned chart symbol
- `name` (str): Color name
- `rgbHex` (str): Hex color value
- `vendor` (str): Vendor name
- `code` (str): Vendor-specific color code

**Request schema:** `AddPaletteColorsRequest` (see `schema.py`)

**Response schema:** `AddPaletteColorsResponse` (see `schema.py`)

**Auth/session:** Login required. Uses `session['user_id']` to verify ownership.

**Side effects:** Creates `ProjectColor` rows. Commits transaction.

**Error responses:**
- `404` — Project not found or not owned by current user
- `422` — One or more color IDs not found in the colors table

**Example request:**
```json
{
  "colorIds": [42, 105, 310]
}
```

**Example response:**
```json
{
  "colors": [
    {"id": "uuid-1", "colorId": 42, "symbol": "A", "name": "Black", "rgbHex": "#000000", "vendor": "DMC", "code": "310"},
    {"id": "uuid-2", "colorId": 105, "symbol": "B", "name": "White", "rgbHex": "#ffffff", "vendor": "DMC", "code": "Blanc"}
  ]
}
```

## `POST /api/projects/<project_id>/palette/colors/remove`

Remove colors from a project's palette. Also removes all cell and path references to the deleted colors from all layers.

**Inputs:**
- `project_id` (path parameter): Project UUID
- JSON body:
  - `colorIds` (array of str): ProjectColor UUIDs to remove

**Outputs:** JSON object:
- `success` (bool): Always `true` on success

**Request schema:** `RemovePaletteColorsRequest` (see `schema.py`)

**Response schema:** `RemovePaletteColorsResponse` (see `schema.py`)

**Auth/session:** Login required. Uses `session['user_id']` to verify ownership.

**Side effects:** Deletes `ProjectColor` rows. Removes matching cell and path entries from `ProjectLayerCells` and `ProjectLayerPaths`. Commits transaction.

**Error responses:**
- `404` — Project not found, not owned by current user, or palette color IDs not found in project

**Example request:**
```json
{
  "colorIds": ["uuid-1", "uuid-2"]
}
```

**Example response:**
```json
{
  "success": true
}
```

## `POST /api/projects/<project_id>/palette/merge`

Merge palette colors by remapping all cell and path references from source colors to target colors, then deleting the source colors.

**Inputs:**
- `project_id` (path parameter): Project UUID
- JSON body:
  - `merges` (array of objects): Each object contains:
    - `sourceColorId` (str): ProjectColor UUID to merge from (will be deleted)
    - `targetColorId` (str): ProjectColor UUID to merge into (will be kept)

**Outputs:** JSON object:
- `success` (bool): Always `true` on success

**Request schema:** `MergePaletteColorsRequest` (see `schema.py`)

**Response schema:** `MergePaletteColorsResponse` (see `schema.py`)

**Auth/session:** Login required. Uses `session['user_id']` to verify ownership.

**Side effects:** Remaps color references in `ProjectLayerCells` and `ProjectLayerPaths`. Deletes source `ProjectColor` rows. Commits transaction.

**Error responses:**
- `404` — Project not found, not owned by current user, or palette color IDs not found in project
- `422` — Source and target are the same color

**Example request:**
```json
{
  "merges": [
    {"sourceColorId": "uuid-old", "targetColorId": "uuid-keep"}
  ]
}
```

**Example response:**
```json
{
  "success": true
}
```
