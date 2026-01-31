# API Blueprint

JSON API endpoints for data access. These endpoints return JSON responses and are consumed by frontend JavaScript.

## URL Prefix

`/api`

## Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/api/colors` | `get_colors` | Returns all thread colors from all vendor palettes |

## Route Details

### `GET /api/colors`

Returns all available thread colors from all supported vendors.

**Inputs:** None

**Outputs:** JSON object with `colors` array. Each color contains:
- `id`: Unique identifier (`{vendor}_{code}`)
- `vendor`: Vendor name (uppercase)
- `code`: Vendor's color code
- `name`: Color name
- `hex`: Hex color value
- `text`: Display text for UI

**Side effects:** None (read-only)

**Auth/session:** Not required

**Example response:**
```json
{
  "colors": [
    {
      "id": "dmc_310",
      "vendor": "DMC",
      "code": "310",
      "name": "Black",
      "hex": "#000000",
      "text": "DMC 310 - Black"
    }
  ]
}
```

## Session Keys

None.

## Static Assets

None - this blueprint serves JSON only.
