/**
 * Base Stitch Class
 * All stitch types extend from this base class
 */

export class BaseStitch {
    constructor() {
        this.id = '';              // Unique identifier (e.g., 'full', 'half-slash')
        this.name = '';            // Display name (e.g., 'Full Cross', 'Half Stitch')
        this.category = '';        // Category for grouping (e.g., 'Full & Half', 'Quarter')
        this.description = '';     // Short description of usage
        this.icon = '';            // Unicode symbol for button (optional)
        this.shortcut = '';        // Keyboard shortcut (optional, for future)
        this.tags = [];            // Tags for search/filtering (optional, for future)
    }

    /**
     * Draw the stitch on the canvas
     * Must be implemented by subclasses
     *
     * @param {CanvasRenderingContext2D} ctx - Canvas context
     * @param {number} x - X position
     * @param {number} y - Y position
     * @param {number} size - Cell size
     * @param {string} color - Stitch color (hex)
     */
    draw(ctx, x, y, size, color) {
        throw new Error(`draw() must be implemented by ${this.constructor.name}`);
    }

    /**
     * Draw a preview of the stitch (for palette buttons)
     * Can be overridden for custom preview rendering
     *
     * @param {CanvasRenderingContext2D} ctx - Canvas context
     * @param {number} size - Preview size
     */
    drawPreview(ctx, size) {
        // Default implementation - just call draw with default color
        this.draw(ctx, 0, 0, size, '#333333');
    }

    /**
     * Get the symbol representation for symbol rendering mode
     * Can be overridden for custom symbols
     *
     * @returns {string} Symbol character
     */
    getSymbol() {
        return this.icon || '?';
    }

    /**
     * Get formatted display name
     * @returns {string}
     */
    getDisplayName() {
        return this.name || this.id;
    }

    /**
     * Check if this stitch belongs to a category
     * @param {string} category
     * @returns {boolean}
     */
    isInCategory(category) {
        return this.category === category;
    }

    /**
     * Get metadata object
     * @returns {object}
     */
    getMetadata() {
        return {
            id: this.id,
            name: this.name,
            category: this.category,
            description: this.description,
            icon: this.icon,
            shortcut: this.shortcut,
            tags: this.tags
        };
    }
}
