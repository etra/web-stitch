# PDF Generation

This document describes how cross-stitch pattern PDFs are generated.

---

## Overview

The PDF generation system creates printable pattern documents from project data. Users can customize the output through a modal dialog before generating.

**Key Components:**
- `PatternPDFService` - Orchestrates PDF document creation
- `PatternRenderer` - Generates pattern images and legend data
- Routes handle user options and serve the PDF

---

## User Flow

1. User navigates to pattern view (`/print/<project_id>`)
2. Clicks "Download PDF" button
3. Modal opens with grid style options:
   - **Symbols Only** - Black symbols on white background
   - **Symbols with Color** - Symbols on colored backgrounds
4. User selects preferred style and clicks "Generate PDF"
5. PDF opens in new tab

---

## PDF Structure

The generated PDF contains the following pages:

| Page | Content |
|------|---------|
| 1 | **Overview** - Colored pattern preview, project info, tips |
| 2 | **Legend (By Color)** - Thread requirements table |
| 3 | **Legend (By Stitch Type)** - Thread requirements grouped by stitch category |
| 4+ | **Pattern Grids** - Symbol charts (50x50 stitches per page with 5-stitch overlap) |

---

## Files

```
stitch/
├── blueprints/print/
│   ├── routes.py                 # PDF route with options
│   └── templates/print/
│       └── view.html             # PDF options modal
└── services/
    ├── pattern_pdf_service.py    # PDF document generation
    └── pattern_renderer.py       # Image rendering & legend data
```

---

## Service: PatternPDFService

Location: `stitch/services/pattern_pdf_service.py`

Uses ReportLab to generate PDF documents.

### Main Method

```python
PatternPDFService.generate_pdf(
    project,                    # Project object
    logo_path: str = None,      # Path to logo for footer
    grid_style: str = 'symbols' # 'symbols' or 'colored'
) -> bytes
```

### Page Building Methods

| Method | Purpose |
|--------|---------|
| `_build_overview_page()` | Pattern preview + project info table |
| `_build_legend_page()` | Color legend with stitch icons, symbols, thread codes |
| `_build_legend_by_stitch_page()` | Legend grouped by stitch type category |
| `_build_pattern_page()` | Single pattern grid page |
| `_add_footer()` | Page footer with logo, URL, page numbers |

### PDF Metadata

Set via `SimpleDocTemplate` parameters:
- **title**: `{project.name} - ourstitch.com`
- **author**: `OurStitch`
- **subject**: `Cross-stitch pattern`
- **creator**: `OurStitch`

---

## Service: PatternRenderer

Location: `stitch/services/pattern_renderer.py`

Generates pattern images and legend data.

### Legend Generation

```python
# Returns list of entries, one per (color, stitch_type) combination
PatternRenderer.generate_legend(state, width, height) -> List[Dict]

# Entry structure:
{
    'paletteIndex': int,
    'stitchType': str,        # e.g., 'full', 'half-slash'
    'stitchCategory': str,    # e.g., 'Full Cross', 'Half Stitch'
    'stitchIcon': str,        # e.g., '✕', '/', '◸'
    'symbol': str,            # Unique symbol for this combination
    'rgbHex': str,
    'vendor': str,
    'code': str,
    'name': str,
    'count': int
}
```

### Symbol Assignment

Symbols are assigned per **(color + stitch type)** combination, not per color alone. This ensures each unique combination has a distinct symbol in the pattern chart.

```python
# Internal method generates symbol map
PatternRenderer._generate_symbol_map(state, width, height)
    -> Dict[Tuple[paletteIndex, stitchType], symbol]
```

Available symbols (in order of assignment):
```
A-Z, 1-9, 0, @, #, $, %, &, *, +, =, ~, a-z
```

### Pattern Image Rendering

```python
PatternRenderer.render_symbol_page(
    state, width, height,
    x_start, y_start,         # Region start coordinates
    x_end, y_end,             # Region end coordinates
    cell_size=20,
    colored_background=False  # True for colored grid style
) -> np.ndarray
```

**Grid Styles:**

| Style | Background | Symbol Color |
|-------|------------|--------------|
| `symbols` | White | Black |
| `colored` | Thread color | Adaptive (white on dark, black on light) |

### Contrast Calculation

For colored backgrounds, symbol color is determined by background luminance:

```python
PatternRenderer._get_luminance(rgb) -> float  # 0.0 (black) to 1.0 (white)
PatternRenderer._get_contrasting_color(rgb) -> (255,255,255) or (0,0,0)
```

Uses WCAG 2.0 relative luminance formula for accessibility.

---

## Route

Location: `stitch/blueprints/print/routes.py`

```python
@bp.route('/<project_id>/pdf')
def pdf(project_id):
    grid_style = request.args.get('grid_style', 'symbols')
    # ... generates and returns PDF
```

**Query Parameters:**
- `grid_style`: `'symbols'` (default) or `'colored'`

**Response:**
- Content-Type: `application/pdf`
- Content-Disposition: `inline; filename="{project.name}.pdf"`

---

## Pattern Page Layout

Pattern grids are paginated for printing:

- **Page size**: 50 x 50 stitches
- **Overlap**: 5 stitches between adjacent pages
- **Effective coverage**: 45 stitches per page (after overlap)

```python
PatternRenderer.calculate_pattern_pages(
    width, height,
    page_size=50,
    overlap=5
) -> List[Dict]

# Returns page definitions:
{
    'page_num': int,
    'row': int,           # Row index (1-based)
    'col': int,           # Column index (1-based)
    'total_rows': int,
    'total_cols': int,
    'x_start': int,
    'y_start': int,
    'x_end': int,
    'y_end': int,
    'label': str          # e.g., "(1-50, 1-50)"
}
```

---

## Stitch Icons

Icons match the JavaScript stitch definitions in `blueprints/editor/static/editor/js/stitches/`.

| Stitch Type | Icon |
|-------------|------|
| full | ✕ |
| half-slash | / |
| half-backslash | \ |
| quarter-tl | ◸ |
| quarter-tr | ◹ |
| quarter-bl | ◺ |
| quarter-br | ◿ |
| three-quarter-tl | ⟋ |
| three-quarter-tr | ⟍ |
| petite | ✕ |
| french-knot | • |
| long-vertical | \| |
| long-horizontal | ― |
| backstitch-horizontal | ─ |
| backstitch-vertical | │ |
| backstitch-slash | ╱ |
| backstitch-backslash | ╲ |

---

## Legend Table Columns

Both web and PDF legends use this column order:

| Column | Description |
|--------|-------------|
| Stitch | Stitch type icon |
| Symbol | Unique chart symbol |
| Color | Color swatch |
| Color Name | Thread color name + hex |
| Thread Code | Vendor + code (e.g., "DMC 321") |
| Stitches | Count of stitches |
| Skeins* | Estimated skeins needed |

**Skein Calculation:** `count / 200` (approximate for 14-count Aida)

---

## Dependencies

- **ReportLab** - PDF generation (`reportlab`)
- **OpenCV** - Image processing (`cv2`)
- **NumPy** - Image arrays (`numpy`)
- **PIL** - Image conversion (`Pillow`)

---

## Related Documentation

- [Editor Architecture](editor.md) - Project state structure
- [Services](service.md) - Service layer patterns
