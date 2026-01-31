/**
 * Renderer Module
 * Handles all canvas rendering - grid, stitches, layers
 */

import { registerAllStitches } from './stitches/index.js';

export class Renderer {
    constructor(canvas, viewport) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.viewport = viewport;
        this.hoverCell = null;
        this.renderMode = 'color'; // 'color', 'symbol', or 'both'

        // Stitch registry - maps stitch ID to stitch instance
        this.stitches = new Map();

        // Register all default stitch types from external module
        registerAllStitches(this);
    }

    /**
     * Register a stitch instance
     * @param {BaseStitch} stitch - Stitch instance to register
     */
    registerStitch(stitch) {
        if (!stitch || !stitch.id) {
            console.error('Invalid stitch instance:', stitch);
            return;
        }
        this.stitches.set(stitch.id, stitch);
    }

    /**
     * Register a custom stitch renderer (legacy compatibility)
     * @param {string} stitchType - The stitch type identifier
     * @param {function} renderFunc - Function(x, y, size, color) that renders the stitch
     */
    registerStitchRenderer(stitchType, renderFunc) {
        // Create a simple stitch object wrapper for legacy support
        const legacyStitch = {
            id: stitchType,
            name: stitchType,
            category: 'Custom',
            description: 'Custom stitch',
            draw: renderFunc,
            drawPreview: function(ctx, size) {
                renderFunc(0, 0, size, '#333333');
            }
        };
        this.stitches.set(stitchType, legacyStitch);
    }

    /**
     * Unregister a stitch
     * @param {string} stitchId - The stitch ID to remove
     */
    unregisterStitch(stitchId) {
        this.stitches.delete(stitchId);
    }

    /**
     * Get a stitch instance by ID
     * @param {string} stitchId - The stitch ID
     * @returns {BaseStitch|null} The stitch instance or null
     */
    getStitch(stitchId) {
        return this.stitches.get(stitchId) || null;
    }

    /**
     * Get all registered stitches
     * @returns {BaseStitch[]} Array of stitch instances
     */
    getRegisteredStitches() {
        return Array.from(this.stitches.values());
    }

    /**
     * Get all registered stitch types (IDs)
     * @returns {string[]} Array of stitch IDs
     */
    getRegisteredStitchTypes() {
        return Array.from(this.stitches.keys());
    }

    /**
     * Set render mode
     */
    setRenderMode(mode) {
        this.renderMode = mode;
    }

    /**
     * Get render mode
     */
    getRenderMode() {
        return this.renderMode;
    }

    /**
     * Main render function
     */
    render(state, toolPreview = null) {
        const { width, height, clothColor, state: projectState } = state;
        const { palette, layers, activeLayerId } = projectState;

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw background
        this.drawBackground();

        // Draw cloth color
        this.drawClothBackground(clothColor, width, height);

        // Render each visible layer
        for (const layer of layers) {
            if (!layer.visible) continue;

            // Set layer opacity if specified
            const layerOpacity = layer.opacity !== undefined ? layer.opacity : 1.0;
            this.ctx.globalAlpha = layerOpacity;

            if (layer.type === 'raster') {
                this.renderRasterLayer(layer, palette, width, height);
            } else if (layer.type === 'reference') {
                this.renderReferenceLayer(layer, width, height);
            }

            // Reset opacity
            this.ctx.globalAlpha = 1.0;
        }

        // Draw grid lines
        this.drawGrid(width, height);

        // Draw grid numbers
        this.drawGridNumbers(width, height);

        // Draw hover highlight
        if (this.hoverCell) {
            this.drawHoverHighlight(this.hoverCell.x, this.hoverCell.y);
        }

        // Draw tool preview
        if (toolPreview) {
            this.drawToolPreview(toolPreview);
        }
    }

    /**
     * Draw gray background
     */
    drawBackground() {
        this.ctx.fillStyle = '#e0e0e0';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    /**
     * Draw cloth color background
     */
    drawClothBackground(clothColor, gridWidth, gridHeight) {
        const cellSize = this.viewport.getCellSize();
        const { x, y } = this.viewport.gridToScreen(0, 0);

        this.ctx.fillStyle = clothColor;
        this.ctx.fillRect(
            x,
            y,
            gridWidth * cellSize,
            gridHeight * cellSize
        );
    }

    /**
     * Draw grid lines
     */
    drawGrid(gridWidth, gridHeight) {
        const cellSize = this.viewport.getCellSize();
        const bounds = this.viewport.getVisibleBounds();
        const startPos = this.viewport.gridToScreen(0, 0);

        // Only draw grid if cells are large enough
        if (cellSize < 4) return;

        this.ctx.lineWidth = 1;

        // Minor grid lines
        this.ctx.strokeStyle = '#ddd';
        this.ctx.beginPath();

        for (let x = bounds.x0; x <= bounds.x1; x++) {
            const screenX = startPos.x + x * cellSize;
            this.ctx.moveTo(screenX, startPos.y);
            this.ctx.lineTo(screenX, startPos.y + gridHeight * cellSize);
        }

        for (let y = bounds.y0; y <= bounds.y1; y++) {
            const screenY = startPos.y + y * cellSize;
            this.ctx.moveTo(startPos.x, screenY);
            this.ctx.lineTo(startPos.x + gridWidth * cellSize, screenY);
        }

        this.ctx.stroke();

        // Major grid lines (every 10 cells)
        if (cellSize >= 8) {
            this.ctx.strokeStyle = '#999';
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();

            for (let x = 0; x <= gridWidth; x += 10) {
                if (x < bounds.x0 || x > bounds.x1) continue;
                const screenX = startPos.x + x * cellSize;
                this.ctx.moveTo(screenX, startPos.y);
                this.ctx.lineTo(screenX, startPos.y + gridHeight * cellSize);
            }

            for (let y = 0; y <= gridHeight; y += 10) {
                if (y < bounds.y0 || y > bounds.y1) continue;
                const screenY = startPos.y + y * cellSize;
                this.ctx.moveTo(startPos.x, screenY);
                this.ctx.lineTo(startPos.x + gridWidth * cellSize, screenY);
            }

            this.ctx.stroke();
        }
    }

    /**
     * Draw grid numbers at every 10th cell
     */
    drawGridNumbers(gridWidth, gridHeight) {
        const cellSize = this.viewport.getCellSize();
        const startPos = this.viewport.gridToScreen(0, 0);

        // Only draw numbers if cells are large enough to read
        if (cellSize < 8) return;

        this.ctx.font = `${Math.max(10, cellSize * 0.8)}px Arial`;
        this.ctx.fillStyle = '#666';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';

        // Draw numbers along top edge (X axis)
        for (let x = 0; x <= gridWidth; x += 10) {
            const screenX = startPos.x + x * cellSize;
            const screenY = startPos.y - 15; // Above the grid

            // Draw number
            this.ctx.fillText(x.toString(), screenX, screenY);
        }

        // Draw numbers along left edge (Y axis)
        this.ctx.textAlign = 'right';
        for (let y = 0; y <= gridHeight; y += 10) {
            const screenX = startPos.x - 15; // Left of the grid
            const screenY = startPos.y + y * cellSize;

            // Draw number
            this.ctx.fillText(y.toString(), screenX, screenY);
        }
    }

    /**
     * Render a raster layer (stitches)
     */
    renderRasterLayer(layer, palette, gridWidth, gridHeight) {
        const cellSize = this.viewport.getCellSize();
        const bounds = this.viewport.getVisibleBounds();

        for (let y = bounds.y0; y < bounds.y1; y++) {
            for (let x = bounds.x0; x < bounds.x1; x++) {
                const key = `${y * gridWidth + x}`;
                const cell = layer.cells[key];

                if (cell) {
                    this.drawStitch(x, y, cell, palette, cellSize);
                }
            }
        }
    }

    /**
     * Render a reference layer (filled rectangles with direct colors)
     */
    renderReferenceLayer(layer, gridWidth, gridHeight) {
        const cellSize = this.viewport.getCellSize();
        const bounds = this.viewport.getVisibleBounds();

        for (let y = bounds.y0; y < bounds.y1; y++) {
            for (let x = bounds.x0; x < bounds.x1; x++) {
                const key = `${y * gridWidth + x}`;
                const cell = layer.cells[key];

                if (cell && cell.color) {
                    const { x: screenX, y: screenY } = this.viewport.gridToScreen(x, y);

                    // Draw filled rectangle with the cell's color
                    this.ctx.fillStyle = cell.color;
                    this.ctx.fillRect(screenX, screenY, cellSize, cellSize);
                }
            }
        }
    }

    /**
     * Draw a single stitch
     */
    drawStitch(gridX, gridY, cell, palette, cellSize) {
        const color = palette[cell.paletteIndex];
        if (!color) return;

        const { x, y } = this.viewport.gridToScreen(gridX, gridY);

        // Draw based on render mode
        if (this.renderMode === 'symbol') {
            // Symbol only mode - draw symbol on white background
            this.ctx.fillStyle = '#ffffff';
            this.ctx.fillRect(x, y, cellSize, cellSize);
            this.drawSymbol(x, y, cellSize, color.symbol || '?', '#000000');
        } else if (this.renderMode === 'both') {
            // Both mode - draw colored background with symbol overlay
            this.ctx.fillStyle = color.rgbHex || '#cccccc';
            this.ctx.fillRect(x, y, cellSize, cellSize);
            this.drawSymbol(x, y, cellSize, color.symbol || '?', '#000000');
        } else {
            // Color mode - draw colored cross stitch (default)
            const strokeColor = color.rgbHex;

            this.ctx.strokeStyle = strokeColor;
            this.ctx.lineWidth = Math.max(1, cellSize / 10);
            this.ctx.lineCap = 'round';

            // Get the stitch instance and draw
            const stitch = this.stitches.get(cell.stitchType);
            if (stitch) {
                stitch.draw(this.ctx, x, y, cellSize, strokeColor);
            } else {
                console.warn(`Unknown stitch type: ${cell.stitchType}`);
                // Fallback to full stitch if type not found
                const fullStitch = this.stitches.get('full');
                if (fullStitch) {
                    fullStitch.draw(this.ctx, x, y, cellSize, strokeColor);
                }
            }
        }
    }

    /**
     * Draw a symbol in a cell
     */
    drawSymbol(x, y, size, symbol, color = '#000000') {
        if (size < 8) return; // Don't draw symbols if too small

        this.ctx.font = `bold ${Math.max(8, size * 0.6)}px Arial`;
        this.ctx.fillStyle = color;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';

        this.ctx.fillText(symbol, x + size / 2, y + size / 2);
    }

    /**
     * Draw hover highlight
     */
    drawHoverHighlight(gridX, gridY) {
        if (!this.viewport.isValidGridPos(gridX, gridY)) return;

        const cellSize = this.viewport.getCellSize();
        const { x, y } = this.viewport.gridToScreen(gridX, gridY);

        this.ctx.strokeStyle = '#007bff';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(x, y, cellSize, cellSize);
    }

    /**
     * Set hover cell
     */
    setHover(gridX, gridY) {
        if (gridX === null || gridY === null) {
            this.hoverCell = null;
        } else {
            this.hoverCell = { x: gridX, y: gridY };
        }
    }

    /**
     * Draw tool preview (for rectangle, line, etc.)
     */
    drawToolPreview(preview) {
        const cellSize = this.viewport.getCellSize();

        if (preview.type === 'rectangle') {
            const { x0, y0, x1, y1 } = preview;
            const startPos = this.viewport.gridToScreen(x0, y0);
            const endPos = this.viewport.gridToScreen(x1 + 1, y1 + 1);

            this.ctx.strokeStyle = '#007bff';
            this.ctx.lineWidth = 2;
            this.ctx.setLineDash([5, 5]);
            this.ctx.strokeRect(
                startPos.x,
                startPos.y,
                endPos.x - startPos.x,
                endPos.y - startPos.y
            );
            this.ctx.setLineDash([]);
        } else if (preview.type === 'line') {
            const { x0, y0, x1, y1 } = preview;
            const start = this.viewport.gridToScreen(x0, y0);
            const end = this.viewport.gridToScreen(x1, y1);

            this.ctx.strokeStyle = '#007bff';
            this.ctx.lineWidth = 2;
            this.ctx.setLineDash([5, 5]);
            this.ctx.beginPath();
            this.ctx.moveTo(start.x + cellSize / 2, start.y + cellSize / 2);
            this.ctx.lineTo(end.x + cellSize / 2, end.y + cellSize / 2);
            this.ctx.stroke();
            this.ctx.setLineDash([]);
        }
    }
}
