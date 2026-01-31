/**
 * Tools Module
 * Handles drawing tools (brush, eraser, etc.)
 */

export class ToolManager {
    constructor(stateManager, viewport) {
        this.stateManager = stateManager;
        this.viewport = viewport;

        this.currentTool = 'brush';
        this.currentStitchType = 'full';
        this.currentColorIndex = 0;
        this.isDrawing = false;
        this.lastDrawnCell = null;

        // For rectangle and line tools
        this.shapeStartCell = null;
        this.shapeEndCell = null;
    }

    /**
     * Set current tool
     */
    setTool(tool) {
        this.currentTool = tool;
        this.isDrawing = false;
        this.lastDrawnCell = null;
    }

    /**
     * Set current stitch type
     */
    setStitchType(stitchType) {
        this.currentStitchType = stitchType;
        if (this.currentTool !== 'brush') {
            this.currentTool = 'brush';
        }
    }

    /**
     * Set current color
     */
    setColorIndex(colorIndex) {
        this.currentColorIndex = colorIndex;
        if (this.currentTool === 'eraser') {
            this.currentTool = 'brush';
        }
    }

    /**
     * Get current tool
     */
    getTool() {
        return this.currentTool;
    }

    /**
     * Get current stitch type
     */
    getStitchType() {
        return this.currentStitchType;
    }

    /**
     * Get current color index
     */
    getColorIndex() {
        return this.currentColorIndex;
    }

    /**
     * Start drawing
     */
    startDrawing(screenX, screenY) {
        const { x, y } = this.viewport.screenToGrid(screenX, screenY);

        if (!this.viewport.isValidGridPos(x, y)) {
            return;
        }

        this.isDrawing = true;
        this.lastDrawnCell = { x, y };

        // For shape tools, set start point
        if (this.currentTool === 'rectangle' || this.currentTool === 'line') {
            this.shapeStartCell = { x, y };
            this.shapeEndCell = { x, y };
        } else {
            this.applyTool(x, y);
        }
    }

    /**
     * Continue drawing (mouse move)
     */
    continueDrawing(screenX, screenY) {
        if (!this.isDrawing) return;

        const { x, y } = this.viewport.screenToGrid(screenX, screenY);

        if (!this.viewport.isValidGridPos(x, y)) {
            return;
        }

        // For shape tools, update end point
        if (this.currentTool === 'rectangle' || this.currentTool === 'line') {
            this.shapeEndCell = { x, y };
            return;
        }

        // Check if this is a new cell
        if (this.lastDrawnCell &&
            this.lastDrawnCell.x === x &&
            this.lastDrawnCell.y === y) {
            return; // Same cell, don't draw again
        }

        this.lastDrawnCell = { x, y };
        this.applyTool(x, y);
    }

    /**
     * Stop drawing
     */
    stopDrawing() {
        // For shape tools, apply the shape on mouse up
        if (this.isDrawing && (this.currentTool === 'rectangle' || this.currentTool === 'line')) {
            if (this.shapeStartCell && this.shapeEndCell) {
                if (this.currentTool === 'rectangle') {
                    this.applyRectangle();
                } else if (this.currentTool === 'line') {
                    this.applyLine();
                }
            }
            this.shapeStartCell = null;
            this.shapeEndCell = null;
        }

        this.isDrawing = false;
        this.lastDrawnCell = null;
    }

    /**
     * Apply current tool at grid position
     */
    applyTool(gridX, gridY) {
        const state = this.stateManager.getState();
        const activeLayerId = state.state.activeLayerId;
        const activeLayer = state.state.layers.find(l => l.id === activeLayerId);

        if (!activeLayer || !activeLayer.editable) {
            return;
        }

        switch (this.currentTool) {
            case 'brush':
                this.applyBrush(activeLayerId, gridX, gridY);
                break;
            case 'eraser':
                this.applyEraser(activeLayerId, gridX, gridY);
                break;
            case 'eyedropper':
                this.applyEyedropper(activeLayerId, gridX, gridY);
                break;
        }
    }

    /**
     * Apply brush tool (place stitch)
     */
    applyBrush(layerId, gridX, gridY) {
        const cellData = {
            paletteIndex: this.currentColorIndex,
            stitchType: this.currentStitchType
        };

        this.stateManager.updateCell(layerId, gridX, gridY, cellData);
    }

    /**
     * Apply eraser tool (remove stitch)
     */
    applyEraser(layerId, gridX, gridY) {
        this.stateManager.updateCell(layerId, gridX, gridY, null);
    }

    /**
     * Apply eyedropper tool (pick color and stitch type)
     */
    applyEyedropper(layerId, gridX, gridY) {
        const cell = this.stateManager.getCell(layerId, gridX, gridY);

        if (cell) {
            this.currentColorIndex = cell.paletteIndex;
            this.currentStitchType = cell.stitchType;
            this.currentTool = 'brush';

            // Notify listeners (for UI update)
            this.onToolChange && this.onToolChange();
        }
    }

    /**
     * Apply rectangle border
     */
    applyRectangle() {
        const state = this.stateManager.getState();
        const activeLayerId = state.state.activeLayerId;
        const activeLayer = state.state.layers.find(l => l.id === activeLayerId);

        if (!activeLayer || !activeLayer.editable) return;

        const x0 = Math.min(this.shapeStartCell.x, this.shapeEndCell.x);
        const y0 = Math.min(this.shapeStartCell.y, this.shapeEndCell.y);
        const x1 = Math.max(this.shapeStartCell.x, this.shapeEndCell.x);
        const y1 = Math.max(this.shapeStartCell.y, this.shapeEndCell.y);

        const cellData = {
            paletteIndex: this.currentColorIndex,
            stitchType: this.currentStitchType
        };

        // Draw border: top, bottom, left, right
        for (let x = x0; x <= x1; x++) {
            this.stateManager.updateCell(activeLayerId, x, y0, cellData);
            this.stateManager.updateCell(activeLayerId, x, y1, cellData);
        }

        for (let y = y0 + 1; y < y1; y++) {
            this.stateManager.updateCell(activeLayerId, x0, y, cellData);
            this.stateManager.updateCell(activeLayerId, x1, y, cellData);
        }
    }

    /**
     * Apply line (draws stitches in a line)
     */
    applyLine() {
        const state = this.stateManager.getState();
        const activeLayerId = state.state.activeLayerId;
        const activeLayer = state.state.layers.find(l => l.id === activeLayerId);

        if (!activeLayer || !activeLayer.editable) return;

        const x0 = this.shapeStartCell.x;
        const y0 = this.shapeStartCell.y;
        const x1 = this.shapeEndCell.x;
        const y1 = this.shapeEndCell.y;

        const cellData = {
            paletteIndex: this.currentColorIndex,
            stitchType: this.currentStitchType
        };

        // Bresenham's line algorithm
        const dx = Math.abs(x1 - x0);
        const dy = Math.abs(y1 - y0);
        const sx = x0 < x1 ? 1 : -1;
        const sy = y0 < y1 ? 1 : -1;
        let err = dx - dy;

        let x = x0;
        let y = y0;

        while (true) {
            this.stateManager.updateCell(activeLayerId, x, y, cellData);

            if (x === x1 && y === y1) break;

            const e2 = 2 * err;
            if (e2 > -dy) {
                err -= dy;
                x += sx;
            }
            if (e2 < dx) {
                err += dx;
                y += sy;
            }
        }
    }

    /**
     * Get shape preview (for rendering)
     */
    getShapePreview() {
        if (!this.isDrawing || !this.shapeStartCell || !this.shapeEndCell) {
            return null;
        }

        if (this.currentTool === 'rectangle') {
            const x0 = Math.min(this.shapeStartCell.x, this.shapeEndCell.x);
            const y0 = Math.min(this.shapeStartCell.y, this.shapeEndCell.y);
            const x1 = Math.max(this.shapeStartCell.x, this.shapeEndCell.x);
            const y1 = Math.max(this.shapeStartCell.y, this.shapeEndCell.y);

            return { type: 'rectangle', x0, y0, x1, y1 };
        } else if (this.currentTool === 'line') {
            return {
                type: 'line',
                x0: this.shapeStartCell.x,
                y0: this.shapeStartCell.y,
                x1: this.shapeEndCell.x,
                y1: this.shapeEndCell.y
            };
        }

        return null;
    }

    /**
     * Register callback for tool changes
     */
    onToolChangeCallback(callback) {
        this.onToolChange = callback;
    }
}
