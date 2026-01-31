# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## Canvas Rendering Strategy

**Custom HTML5 Canvas renderer (built from scratch):**

- Grid sizes can be large (no practical limit) - DOM would be too slow
- Canvas provides fast rendering with pan/zoom
- Full control over rendering different stitch types

### Grid Specifications

**Cell Size:**
- **Base cell size: 5×5 pixels** (before zoom)
- With zoom: `actualCellSize = 5 * zoomLevel`
- Example: At 2× zoom, cells are 10×10 pixels

**Grid Lines:**
- **Minor grid lines:** Every cell (thin, light gray `#ddd`)
- **Major grid lines:** Every 10th cell (thicker, darker gray `#999`)
  - Configurable in project properties (default: 10)
  - Makes it easier to count stitches
  - Common in cross-stitch patterns (10×10 blocks)

**Zoom Levels:**
- Minimum: 0.25× (very zoomed out)
- Default: 1× (5×5 pixel cells)
- Maximum: 10× (50×50 pixel cells for detailed work)
- Zoom with mouse wheel or zoom buttons

**Example:** 100×100 grid at 1× zoom
- Canvas size: 500×500 pixels
- 10 major grid lines vertical (at x=50, 100, 150, ...)
- 10 major grid lines horizontal (at y=50, 100, 150, ...)

### Render pipeline (layered):
```javascript
function render(ctx, project, viewport, zoom) {
  // 1. Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 2. Draw cloth color background
  ctx.fillStyle = project.clothColor;
  ctx.fillRect(...);

  // 3. Render each visible layer in order
  for (const layer of project.layers.filter(l => l.visible)) {
    if (layer.type === 'image') {
      // Draw background image with opacity
      ctx.globalAlpha = layer.opacity;
      ctx.drawImage(layer.image, ...);
      ctx.globalAlpha = 1.0;
    } else if (layer.type === 'raster') {
      // Draw stitches
      renderRasterLayer(ctx, layer, project.palette, viewport, zoom);
    }
  }

  // 4. Draw grid lines
  drawGridLines(ctx, viewport, zoom);

  // 5. Draw symbols (if symbol view enabled)
  if (showSymbols) {
    renderSymbols(ctx, project.layers, project.palette, viewport, zoom);
  }

  // 6. Draw selection/hover highlight
  drawHighlights(ctx, selection, hover);

  // 7. Draw tool preview (rectangle outline, etc.)
  drawToolPreview(ctx, currentTool);
}

function renderRasterLayer(ctx, layer, palette, viewport, zoom) {
  const cellSize = 20 * zoom; // pixels per cell

  for (let y = viewport.y0; y < viewport.y1; y++) {
    for (let x = viewport.x0; x < viewport.x1; x++) {
      const cell = layer.cells[y * width + x];
      if (!cell) continue; // empty cell

      const color = palette[cell.paletteIndex];
      drawStitch(ctx, x, y, cell, color, cellSize);
    }
  }
}

function drawStitch(ctx, x, y, cell, color, cellSize) {
  ctx.strokeStyle = color.rgbHex;
  ctx.lineWidth = 2;

  const px = x * cellSize;
  const py = y * cellSize;

  switch (cell.stitchType) {
    case 'full':
      // Draw X (full cross stitch)
      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(px + cellSize, py + cellSize);
      ctx.moveTo(px + cellSize, py);
      ctx.lineTo(px, py + cellSize);
      ctx.stroke();
      break;

    case 'half':
      // Draw / or \ based on rotation
      ctx.beginPath();
      if (cell.rotation === 0 || cell.rotation === 180) {
        ctx.moveTo(px, py + cellSize);
        ctx.lineTo(px + cellSize, py);
      } else {
        ctx.moveTo(px, py);
        ctx.lineTo(px + cellSize, py + cellSize);
      }
      ctx.stroke();
      break;

    case 'quarter':
      // Draw small diagonal in corner (depends on rotation)
      // Implementation details...
      break;

    case 'three-quarter':
      // Draw half + quarter (combination)
      // Implementation details...
      break;

    case 'dot':
    case 'bead':
      // Draw filled circle (French knot or bead)
      ctx.fillStyle = color.rgbHex;
      ctx.beginPath();
      ctx.arc(px + cellSize/2, py + cellSize/2, cellSize/4, 0, Math.PI * 2);
      ctx.fill();
      break;
  }
}
```

**View modes:**
- `stitches` - Render stitches as lines/shapes (default)
- `symbols` - Show symbols on cloth color background
- `both` - Stitches + symbols overlaid

**Performance optimizations:**
- Use `requestAnimationFrame` for smooth rendering at 60fps
- Viewport culling: Only render visible cells
- Dirty region tracking: Only redraw changed areas when possible
- Off-screen canvas for pre-rendering complex symbols
- Web Workers for large grid operations (optional v1.1)
