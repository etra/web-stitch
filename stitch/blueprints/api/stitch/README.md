# Stitch Resource

API routes for stitch type definitions.

## Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/api/stitches` | `get_stitches` | Returns all available stitch types |

## `GET /api/stitches`

Returns all available stitch types.

**Inputs:** None

**Outputs:** JSON object with `stitches` array. Each stitch contains:
- `type` (str): Stitch type identifier (e.g. `full`, `half-slash`, `french-knot`)
- `name` (str): Human-readable name (e.g. `Full Cross`, `French Knot`)
- `category` (str): Category grouping (e.g. `Full Cross`, `Half Stitch`, `Special Stitch`)
- `icon` (str): Unicode icon representing the stitch
- `sort_order` (int): Sort position for UI display

**Response schema:** `StitchesListResponse` (see `schema.py`)

**Auth/session:** Not required

**Side effects:** None (read-only)

**Example response:**
```json
{
  "stitches": [
    {
      "type": "full",
      "name": "Full Cross",
      "category": "Full Cross",
      "icon": "\u2715",
      "sort_order": 0
    }
  ]
}
```
