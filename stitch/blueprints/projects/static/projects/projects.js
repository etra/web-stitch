/**
 * Projects Blueprint JavaScript
 *
 * Scripts specific to the projects blueprint pages:
 * - Project form (color picker sync)
 * - Creation wizard (size preview, color selection)
 */

/* =============================================================================
   Project Form - Color Picker Sync
   ============================================================================= */

/**
 * Initialize color picker synchronization between color input and text display.
 * Call this on pages with the project form (create/edit).
 */
function initColorPickerSync() {
    const colorInput = document.getElementById('cloth_color');
    const colorText = document.getElementById('cloth_color_text');

    if (colorInput && colorText) {
        colorInput.addEventListener('input', function(e) {
            colorText.value = e.target.value;
        });
    }
}

/* =============================================================================
   Wizard Setup - Size Preview
   ============================================================================= */

/**
 * Initialize the canvas size preview on the setup wizard step.
 * Updates the visual preview box and text display when width/height change.
 */
function initSizePreview() {
    const widthInput = document.getElementById('width');
    const heightInput = document.getElementById('height');
    const preview = document.getElementById('sizePreview');
    const display = document.getElementById('sizeDisplay');

    if (!widthInput || !heightInput || !preview || !display) {
        return;
    }

    function updateSizePreview() {
        const width = parseInt(widthInput.value) || 100;
        const height = parseInt(heightInput.value) || 100;

        // Calculate preview dimensions (max 200px, proportional)
        const maxSize = 200;
        const scale = Math.min(maxSize / Math.max(width, height), 2);
        const previewWidth = Math.max(20, Math.min(maxSize, width * scale));
        const previewHeight = Math.max(20, Math.min(maxSize, height * scale));

        preview.style.width = previewWidth + 'px';
        preview.style.height = previewHeight + 'px';

        display.textContent = width + ' x ' + height + ' stitches';
    }

    widthInput.addEventListener('input', updateSizePreview);
    heightInput.addEventListener('input', updateSizePreview);

    // Initialize preview
    updateSizePreview();
}

/* =============================================================================
   Wizard Colors - Color Selection
   ============================================================================= */

/**
 * Initialize the color selection functionality on the colors wizard step.
 * Handles adding/removing colors, search filtering, and form submission.
 */
function initColorSelection() {
    const selectedGrid = document.getElementById('selected-colors-grid');
    const selectedInputs = document.getElementById('selected-inputs');
    const selectedCount = document.getElementById('selected-count');
    const noColorsMsg = document.getElementById('no-colors-msg');
    const clearAllBtn = document.getElementById('clear-all-btn');
    const availableGrid = document.getElementById('available-colors-grid');
    const searchInput = document.getElementById('color-search');

    if (!selectedGrid || !availableGrid) {
        return;
    }

    const selectedColors = new Map(); // code -> {code, name, hex}

    function updateUI() {
        // Update count
        if (selectedCount) {
            selectedCount.textContent = selectedColors.size;
        }

        // Show/hide no colors message and clear button
        if (selectedColors.size === 0) {
            if (noColorsMsg) noColorsMsg.style.display = 'inline';
            if (clearAllBtn) clearAllBtn.style.display = 'none';
        } else {
            if (noColorsMsg) noColorsMsg.style.display = 'none';
            if (clearAllBtn) clearAllBtn.style.display = 'inline-block';
        }

        // Rebuild selected colors chips
        const chips = selectedGrid.querySelectorAll('.selected-color-chip');
        chips.forEach(chip => chip.remove());

        selectedColors.forEach((color, code) => {
            const chip = document.createElement('div');
            chip.className = 'selected-color-chip';
            chip.dataset.colorCode = code;
            chip.innerHTML = `
                <span class="color-swatch" style="background-color: ${color.hex};"></span>
                <span>${code}</span>
                <i class="bi bi-x remove-icon"></i>
            `;
            chip.addEventListener('click', () => removeColor(code));
            selectedGrid.appendChild(chip);
        });

        // Rebuild hidden inputs
        if (selectedInputs) {
            selectedInputs.innerHTML = '';
            selectedColors.forEach((color, code) => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'color_codes';
                input.value = code;
                selectedInputs.appendChild(input);
            });
        }

        // Update available grid (mark selected as dimmed)
        availableGrid.querySelectorAll('.color-grid-cell').forEach(cell => {
            const code = cell.dataset.colorCode;
            if (selectedColors.has(code)) {
                cell.classList.add('selected');
            } else {
                cell.classList.remove('selected');
            }
        });
    }

    function addColor(code, name, hex) {
        if (!selectedColors.has(code)) {
            selectedColors.set(code, { code, name, hex });
            updateUI();
        }
    }

    function removeColor(code) {
        selectedColors.delete(code);
        updateUI();
    }

    // Handle click on available colors
    availableGrid.addEventListener('click', function(e) {
        const cell = e.target.closest('.color-grid-cell');
        if (cell && !cell.classList.contains('selected')) {
            const code = cell.dataset.colorCode;
            const name = cell.dataset.colorName;
            const hex = cell.dataset.colorHex;
            addColor(code, name, hex);
        }
    });

    // Handle clear all
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function() {
            selectedColors.clear();
            updateUI();
        });
    }

    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            availableGrid.querySelectorAll('.color-grid-cell').forEach(cell => {
                const code = cell.dataset.colorCode.toLowerCase();
                const name = cell.dataset.colorName.toLowerCase();
                if (query === '' || code.includes(query) || name.includes(query)) {
                    cell.style.display = '';
                } else {
                    cell.style.display = 'none';
                }
            });
        });
    }

    // Pre-select default colors on load
    availableGrid.querySelectorAll('.color-grid-cell[data-color-default="true"]').forEach(cell => {
        const code = cell.dataset.colorCode;
        const name = cell.dataset.colorName;
        const hex = cell.dataset.colorHex;
        addColor(code, name, hex);
    });
}
