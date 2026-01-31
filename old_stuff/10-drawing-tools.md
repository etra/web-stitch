# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## Drawing Tools

These are the main tools for creating cross-stitch patterns. Each tool is a button in the toolbar.

### Stitch Tools (v1)
Individual stitch types that can be placed on the grid:

1. **Full Stitch** - Complete cross stitch (X)
   - Renders as two diagonal lines forming an X

2. **Half Stitch /** - Diagonal stitch (bottom-left to top-right)
   - Renders as single diagonal line /

3. **Half Stitch \\** - Diagonal stitch (top-left to bottom-right)
   - Renders as single diagonal line \

4. **Quarter Stitch /** - Small diagonal stitch in corner (/)
   - Renders as small diagonal from corner

5. **Quarter Stitch \\** - Small diagonal stitch in corner (\\)
   - Renders as small diagonal from corner

**Usage:** Click to select stitch type, then click/drag on canvas to place stitches

### Shape Tools (v1)
Fill shapes with selected stitch type:

1. **Rectangle Fill** - Click two corners to fill rectangle
   - All cells in rectangle get the selected stitch type

2. **Circle Fill** - Click two corners (bounding box) to fill circle/oval
   - Cells inside ellipse get the selected stitch type

**Usage:** Select tool, select stitch type, select color, then click-drag to define shape

### Line Tools (v1)
Backstitch tools for outlines and details:

1. **Backstitch (1 strand)** - Thin line
   - Renders as thin line between cells

2. **Backstitch (2 strands)** - Medium line
   - Renders as medium-weight line between cells

3. **Backstitch (3 strands)** - Thick line
   - Renders as thick line between cells

**Note:** Backstitches are vector overlays (not cell-based), drawn on top of stitches

**Usage:** Click start point, click end point to draw backstitch line

### Detail Tools (v1)
Special decorative elements:

1. **French Knot** - Small decorative knot (dot)
   - Renders as filled circle in cell center
   - Used for eyes, flower centers, texture

**Usage:** Click to select, then click cells to place French knots

### Utility Tools (v1)
Additional tools for editing:

- **Eyedropper** - Click to pick color and stitch type from canvas
- **Eraser** - Remove stitches (set cells to empty)
- **Pan tool** - Click and drag to move viewport (or hold spacebar)
- **Zoom** - Mouse wheel or zoom buttons

### Layer Controls (v1)
- **Add raster layer** - Create new drawing layer
- **Add image layer** - Upload background reference image
- **Delete layer** - Remove selected layer
- **Toggle visibility** - Show/hide individual layers
- **Reorder layers** - Drag to change stacking order
- **Opacity slider** - For image layers (0-100%)

### Future Tools (v1.1)
- **Three-quarter stitch** - Combination of half + quarter
- **Long stitch** - Spans multiple cells
- **Bead** - For diamond painting
- **Markup mode** - Mark cells as completed (progress tracking)
- **Pattern fill** - Fill area with repeating pattern
