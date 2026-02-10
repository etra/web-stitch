# Color Resource

API routes for thread and bead color catalogs.

## Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/api/colors` | `get_colors` | Returns all thread colors from all vendors |
| GET | `/api/colors/vendors` | `get_vendors` | Returns all vendors with color counts |
| GET | `/api/colors/vendors/<vendor_key>` | `get_vendor_colors` | Returns all colors for a specific vendor |

## `GET /api/colors`

Returns all available thread colors from all supported vendors.

**Inputs:** None

**Outputs:** JSON object with `colors` array. Each color contains:
- `id` (str): Unique identifier (`{vendor}_{code}`)
- `vendor` (str): Vendor name (e.g. `DMC`, `Hama`)
- `code` (str): Vendor's color code
- `name` (str): Color name
- `hex` (str): Hex color value
- `text` (str): Display text for UI

**Response schema:** `ColorsListResponse` (see `schema.py`)

**Auth/session:** Not required

**Side effects:** None (read-only)

**Example response:**
```json
{
  "colors": [
    {
      "id": "DMC_310",
      "vendor": "DMC",
      "code": "310",
      "name": "Black",
      "hex": "#000000",
      "text": "DMC 310 - Black"
    }
  ]
}
```

## `GET /api/colors/vendors`

Returns all supported vendors with metadata and color counts.

**Inputs:** None

**Outputs:** JSON object with `vendors` array. Each vendor contains:
- `key` (str): Vendor identifier (e.g. `DMC`, `Hama`)
- `name` (str): Vendor display name
- `full_name` (str): Full vendor name (e.g. `DMC Embroidery Floss`)
- `description` (str): Short description
- `type` (str): `embroidery` or `beads`
- `color_count` (int): Number of colors in the database

**Response schema:** `VendorsListResponse` (see `schema.py`)

**Auth/session:** Not required

**Side effects:** None (read-only)

**Example response:**
```json
{
  "vendors": [
    {
      "key": "DMC",
      "name": "DMC",
      "full_name": "DMC Embroidery Floss",
      "description": "Most popular embroidery thread brand",
      "type": "embroidery",
      "color_count": 489
    }
  ]
}
```

## `GET /api/colors/vendors/<vendor_key>`

Returns all colors for a specific vendor.

**Inputs:**
- `vendor_key` (path parameter): Vendor identifier (e.g. `DMC`, `Hama`, `Artkal`, `Nabbi`)

**Outputs:** JSON object with `colors` array. Each color contains:
- `id` (int): Database primary key
- `vendor` (str): Vendor name
- `code` (str): Vendor-specific color code
- `name` (str): Color name
- `hex` (str): Hex color value
- `is_default` (bool): Whether this is a default starter color

**Response schema:** `VendorColorsListResponse` (see `schema.py`)

**Auth/session:** Not required

**Side effects:** None (read-only)

**Error responses:**
- `404` — Unknown vendor

**Example response:**
```json
{
  "colors": [
    {
      "id": 1,
      "vendor": "DMC",
      "code": "310",
      "name": "Black",
      "hex": "#000000",
      "is_default": false
    }
  ]
}
```
