/**
 * Viewport Module
 * Handles pan, zoom, and coordinate conversions between screen and grid space
 */

export class Viewport {
    constructor(canvasWidth, canvasHeight, gridWidth, gridHeight) {
        this.canvas = { width: canvasWidth, height: canvasHeight };
        this.grid = { width: gridWidth, height: gridHeight };

        // Viewport state
        this.zoom = 1.0;
        this.minZoom = 0.25;
        this.maxZoom = 10.0;

        // Pan offset (in screen pixels)
        this.offsetX = 0;
        this.offsetY = 0;

        // Base cell size (before zoom)
        this.baseCellSize = 20;

        // Center the grid initially
        this.center();
    }

    /**
     * Get current cell size (with zoom applied)
     */
    getCellSize() {
        return this.baseCellSize * this.zoom;
    }

    /**
     * Center the grid in viewport
     */
    center() {
        const cellSize = this.getCellSize();
        const gridPixelWidth = this.grid.width * cellSize;
        const gridPixelHeight = this.grid.height * cellSize;

        this.offsetX = (this.canvas.width - gridPixelWidth) / 2;
        this.offsetY = (this.canvas.height - gridPixelHeight) / 2;
    }

    /**
     * Update canvas size (when window resizes)
     */
    updateCanvasSize(width, height) {
        this.canvas.width = width;
        this.canvas.height = height;
    }

    /**
     * Convert screen coordinates to grid coordinates
     */
    screenToGrid(screenX, screenY) {
        const cellSize = this.getCellSize();
        const gridX = Math.floor((screenX - this.offsetX) / cellSize);
        const gridY = Math.floor((screenY - this.offsetY) / cellSize);

        return { x: gridX, y: gridY };
    }

    /**
     * Convert grid coordinates to screen coordinates
     */
    gridToScreen(gridX, gridY) {
        const cellSize = this.getCellSize();
        const screenX = gridX * cellSize + this.offsetX;
        const screenY = gridY * cellSize + this.offsetY;

        return { x: screenX, y: screenY };
    }

    /**
     * Check if grid coordinates are valid
     */
    isValidGridPos(gridX, gridY) {
        return gridX >= 0 && gridX < this.grid.width &&
               gridY >= 0 && gridY < this.grid.height;
    }

    /**
     * Get visible grid bounds (for viewport culling)
     */
    getVisibleBounds() {
        const topLeft = this.screenToGrid(0, 0);
        const bottomRight = this.screenToGrid(this.canvas.width, this.canvas.height);

        return {
            x0: Math.max(0, topLeft.x),
            y0: Math.max(0, topLeft.y),
            x1: Math.min(this.grid.width, bottomRight.x + 1),
            y1: Math.min(this.grid.height, bottomRight.y + 1)
        };
    }

    /**
     * Pan by screen pixels
     */
    pan(dx, dy) {
        this.offsetX += dx;
        this.offsetY += dy;
    }

    /**
     * Zoom in/out around a point
     */
    zoomAt(screenX, screenY, delta) {
        const oldZoom = this.zoom;

        // Update zoom level
        if (delta > 0) {
            this.zoom = Math.min(this.maxZoom, this.zoom * 1.1);
        } else {
            this.zoom = Math.max(this.minZoom, this.zoom / 1.1);
        }

        // Adjust pan offset to zoom around the mouse position
        const zoomRatio = this.zoom / oldZoom;
        this.offsetX = screenX - (screenX - this.offsetX) * zoomRatio;
        this.offsetY = screenY - (screenY - this.offsetY) * zoomRatio;

        return this.zoom;
    }

    /**
     * Set zoom level and center
     */
    setZoom(zoom) {
        this.zoom = Math.max(this.minZoom, Math.min(this.maxZoom, zoom));
        this.center();
        return this.zoom;
    }

    /**
     * Get zoom percentage
     */
    getZoomPercent() {
        return Math.round(this.zoom * 100);
    }

    /**
     * Reset zoom and pan
     */
    reset() {
        this.zoom = 1.0;
        this.center();
    }
}
