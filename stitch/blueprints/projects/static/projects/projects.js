/**
 * Projects Blueprint JavaScript
 *
 * Scripts specific to the projects blueprint pages:
 * - Project form (color picker sync)
 * - Creation wizard (size preview, color selection)
 */

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
   Tag Input - Autocomplete with Chips
   ============================================================================= */

/**
 * Initialize the tag input with autocomplete and chip display.
 * @param {string} inputId - ID of the text input element
 * @param {string} hiddenContainerId - ID of the container for hidden form inputs
 * @param {string} chipsContainerId - ID of the container for tag badge chips
 * @param {string} suggestionsId - ID of the autocomplete suggestions dropdown
 * @param {string[]} [initialTags=[]] - Pre-populated tag names
 */
function initTagInput(inputId, hiddenContainerId, chipsContainerId, suggestionsId, initialTags) {
    const input = document.getElementById(inputId);
    const hiddenContainer = document.getElementById(hiddenContainerId);
    const chipsContainer = document.getElementById(chipsContainerId);
    const suggestionsContainer = document.getElementById(suggestionsId);

    if (!input || !hiddenContainer || !chipsContainer) {
        return;
    }

    const tags = new Set();
    let debounceTimer = null;

    function normalizeTag(name) {
        return name.trim().toLowerCase().replace(/[^a-z0-9\s\-]/g, '').replace(/\s+/g, ' ').substring(0, 50);
    }

    function renderChips() {
        chipsContainer.innerHTML = '';
        hiddenContainer.innerHTML = '';

        tags.forEach(function(tag) {
            // Badge chip
            var chip = document.createElement('span');
            chip.className = 'tag-chip badge bg-secondary me-1 mb-1';
            chip.innerHTML = tag + ' <i class="bi bi-x tag-chip-remove"></i>';
            chip.querySelector('.tag-chip-remove').addEventListener('click', function() {
                tags.delete(tag);
                renderChips();
            });
            chipsContainer.appendChild(chip);

            // Hidden input for form submission
            var hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = 'tags';
            hidden.value = tag;
            hiddenContainer.appendChild(hidden);
        });
    }

    function addTag(name) {
        var normalized = normalizeTag(name);
        if (normalized && !tags.has(normalized)) {
            tags.add(normalized);
            renderChips();
        }
        input.value = '';
        hideSuggestions();
    }

    function hideSuggestions() {
        if (suggestionsContainer) {
            suggestionsContainer.innerHTML = '';
            suggestionsContainer.style.display = 'none';
        }
    }

    function showSuggestions(tagList) {
        if (!suggestionsContainer) return;
        suggestionsContainer.innerHTML = '';

        var filtered = tagList.filter(function(t) { return !tags.has(t.name); });
        if (filtered.length === 0) {
            hideSuggestions();
            return;
        }

        filtered.forEach(function(tag) {
            var item = document.createElement('div');
            item.className = 'tag-suggestion-item';
            item.textContent = tag.name;
            item.addEventListener('mousedown', function(e) {
                e.preventDefault();
                addTag(tag.name);
            });
            suggestionsContainer.appendChild(item);
        });

        suggestionsContainer.style.display = 'block';
    }

    function fetchSuggestions(query) {
        var url = '/api/tags';
        if (query) {
            url += '?q=' + encodeURIComponent(query);
        }

        fetch(url)
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.tags) {
                    showSuggestions(data.tags);
                }
            })
            .catch(function() {
                hideSuggestions();
            });
    }

    // Handle keyboard events
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            var value = input.value.trim();
            if (value) {
                addTag(value);
            }
        }
    });

    // Debounced autocomplete on input
    input.addEventListener('input', function() {
        var value = input.value.trim();
        clearTimeout(debounceTimer);

        if (value.length === 0) {
            hideSuggestions();
            return;
        }

        debounceTimer = setTimeout(function() {
            fetchSuggestions(value);
        }, 200);
    });

    // Hide suggestions on blur
    input.addEventListener('blur', function() {
        setTimeout(hideSuggestions, 150);
    });

    // Pre-populate initial tags
    if (initialTags && initialTags.length > 0) {
        initialTags.forEach(function(tag) {
            var normalized = normalizeTag(tag);
            if (normalized) {
                tags.add(normalized);
            }
        });
        renderChips();
    }
}

/* =============================================================================
   Wizard Colors - Color Selection
   ============================================================================= */

/**
 * Initialize the color selection functionality on the colors wizard step.
 * Handles adding/removing colors, search filtering, and form submission.
 */
function initColorSelection(maxColors) {
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

    // Default to 32 if not provided
    const maxPaletteColors = maxColors || 32;
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

        const atLimit = selectedColors.size >= maxPaletteColors;

        // Update available grid (mark selected as dimmed, disable when at limit)
        availableGrid.querySelectorAll('.color-grid-cell').forEach(cell => {
            const code = cell.dataset.colorCode;
            if (selectedColors.has(code)) {
                cell.classList.add('selected');
                cell.classList.remove('at-limit');
            } else if (atLimit) {
                cell.classList.remove('selected');
                cell.classList.add('at-limit');
            } else {
                cell.classList.remove('selected');
                cell.classList.remove('at-limit');
            }
        });
    }

    function addColor(code, name, hex) {
        if (selectedColors.size >= maxPaletteColors) {
            return; // Palette limit reached
        }
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
        if (cell && !cell.classList.contains('selected') && !cell.classList.contains('at-limit')) {
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
