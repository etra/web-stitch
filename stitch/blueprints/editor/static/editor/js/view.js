/**
 * View Module
 * Handles UI component generation and management outside of canvas
 */

/**
 * StitchPicker Component
 * Dynamically generates visual stitch type buttons from registered stitches
 */
export class StitchPicker {
    constructor(renderer, toolManager) {
        this.renderer = renderer;
        this.toolManager = toolManager;
        this.container = null;
        this.selectedStitchType = 'full';
        this.stitchButtons = new Map();
    }

    /**
     * Create and render the stitch picker component
     * @param {HTMLElement|string} containerElement - Element or selector for container
     */
    render(containerElement) {
        // Get container element
        if (typeof containerElement === 'string') {
            this.container = document.querySelector(containerElement);
        } else {
            this.container = containerElement;
        }

        if (!this.container) {
            console.error('Stitch picker container not found');
            return;
        }

        // Clear container
        this.container.innerHTML = '';

        // Create card structure inside the container
        this.container.innerHTML = `
            <div class="card mb-3">
                <div class="card-header">Stitches</div>
                <div class="card-body p-2">
                    <div id="stitchPickerGrid" class="stitch-picker-grid"></div>
                </div>
            </div>
        `;

        // Get the grid element
        const gridElement = this.container.querySelector('#stitchPickerGrid');

        // Get all registered stitch instances
        const stitches = this.renderer.getRegisteredStitches();

        // Organize stitches into categories
        const categories = this.categorizeStitches(stitches);

        // Render each category
        for (const [categoryName, stitches] of Object.entries(categories)) {
            if (stitches.length === 0) continue;

            // Create category section
            const categorySection = document.createElement('div');
            categorySection.className = 'stitch-category mb-3';

            const categoryLabel = document.createElement('div');
            categoryLabel.className = 'stitch-category-label';
            categoryLabel.textContent = categoryName;
            categorySection.appendChild(categoryLabel);

            const categoryGrid = document.createElement('div');
            categoryGrid.className = 'stitch-category-grid';

            // Create button for each stitch
            for (const stitch of stitches) {
                const button = this.createStitchButton(stitch);
                categoryGrid.appendChild(button);
                this.stitchButtons.set(stitch.id, button);
            }

            categorySection.appendChild(categoryGrid);
            gridElement.appendChild(categorySection);
        }

        // Set initial selection
        this.setSelected(this.selectedStitchType);

        // Add CSS styles
        this.injectStyles();
    }

    /**
     * Categorize stitches for better organization
     * @param {BaseStitch[]} stitches - Array of stitch instances
     * @returns {Object} Categories mapped to stitch arrays
     */
    categorizeStitches(stitches) {
        const categories = {};

        for (const stitch of stitches) {
            const category = stitch.category || 'Other';
            if (!categories[category]) {
                categories[category] = [];
            }
            categories[category].push(stitch);
        }

        return categories;
    }

    /**
     * Create a visual button for a stitch
     * @param {BaseStitch} stitch - Stitch instance
     * @returns {HTMLElement} Button element
     */
    createStitchButton(stitch) {
        const button = document.createElement('button');
        button.className = 'stitch-visual-btn';
        button.dataset.stitchType = stitch.id;
        button.title = stitch.getDisplayName();

        // Create small canvas for stitch preview
        const canvas = document.createElement('canvas');
        canvas.width = 24;
        canvas.height = 24;
        const ctx = canvas.getContext('2d');

        // Draw the stitch preview
        this.drawStitchPreview(ctx, stitch, 24);

        button.appendChild(canvas);

        // Add click handler
        button.addEventListener('click', () => {
            this.handleStitchSelect(stitch.id);
        });

        return button;
    }

    /**
     * Draw a preview of the stitch on a small canvas
     * @param {CanvasRenderingContext2D} ctx - Canvas context
     * @param {BaseStitch} stitch - Stitch instance
     * @param {number} size - Preview size
     */
    drawStitchPreview(ctx, stitch, size) {
        // Clear canvas
        ctx.clearRect(0, 0, size, size);

        // Set up styling
        ctx.strokeStyle = '#333333';
        ctx.fillStyle = '#333333';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';

        try {
            // Use the stitch's drawPreview method
            stitch.drawPreview(ctx, size);
        } catch (error) {
            console.warn(`Error rendering preview for ${stitch.id}:`, error);
            // Fallback: draw a simple X
            ctx.beginPath();
            ctx.moveTo(2, 2);
            ctx.lineTo(size - 2, size - 2);
            ctx.moveTo(size - 2, 2);
            ctx.lineTo(2, size - 2);
            ctx.stroke();
        }
    }

    /**
     * Handle stitch selection
     */
    handleStitchSelect(stitchType) {
        this.selectedStitchType = stitchType;
        this.setSelected(stitchType);

        // Update tool manager
        this.toolManager.setStitchType(stitchType);

        // Dispatch custom event for other components to listen to
        const event = new CustomEvent('stitchTypeChanged', {
            detail: { stitchType }
        });
        document.dispatchEvent(event);
    }

    /**
     * Update visual selection state
     */
    setSelected(stitchType) {
        // Remove active class from all buttons
        this.stitchButtons.forEach((button) => {
            button.classList.remove('active');
        });

        // Add active class to selected button
        const selectedButton = this.stitchButtons.get(stitchType);
        if (selectedButton) {
            selectedButton.classList.add('active');
        }
    }

    /**
     * Inject CSS styles for the stitch picker
     */
    injectStyles() {
        // Check if styles already injected
        if (document.getElementById('stitch-picker-styles')) return;

        const style = document.createElement('style');
        style.id = 'stitch-picker-styles';
        style.textContent = `
            .stitch-picker-grid {
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
            }

            .stitch-category-label {
                font-size: 0.75rem;
                font-weight: 600;
                color: #666;
                margin-bottom: 0.25rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .stitch-category-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, 28px);
                gap: 4px;
            }

            .stitch-visual-btn {
                width: 28px;
                height: 28px;
                padding: 2px;
                border: 2px solid #ccc;
                background: white;
                cursor: pointer;
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.15s ease;
            }

            .stitch-visual-btn:hover {
                border-color: #007bff;
                background: #f8f9fa;
                transform: scale(1.1);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }

            .stitch-visual-btn.active {
                border-color: #007bff;
                background: #e7f3ff;
                border-width: 2px;
            }

            .stitch-visual-btn canvas {
                display: block;
                width: 24px;
                height: 24px;
            }
        `;

        document.head.appendChild(style);
    }

    /**
     * Refresh the picker (useful when new stitches are registered)
     */
    refresh() {
        if (this.container) {
            this.container.innerHTML = '';
            this.stitchButtons.clear();
            this.render(this.container);
        }
    }

    /**
     * Destroy the picker
     */
    destroy() {
        if (this.container) {
            this.container.innerHTML = '';
        }
        this.stitchButtons.clear();
    }
}
