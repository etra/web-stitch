/**
 * Projects Blueprint JavaScript
 *
 * Scripts specific to the projects blueprint pages:
 * - Project form (color picker sync)
 * - Creation wizard (size preview, color selection)
 */

/* =============================================================================
   Wizard - Size Step (stitches <-> inches sync)
   ============================================================================= */

/**
 * Initialize the size step with two-panel stitches/inches sync.
 * Changing stitches updates inches, changing inches updates stitches,
 * changing Aida count recalculates inches from current stitches.
 */
function initSizeStep() {
    const widthInput = document.getElementById('width');
    const heightInput = document.getElementById('height');
    const inchWidthInput = document.getElementById('inchWidth');
    const inchHeightInput = document.getElementById('inchHeight');
    const aidaSelect = document.getElementById('aida');
    const preview = document.getElementById('sizePreview');
    const display = document.getElementById('sizeDisplay');

    if (!widthInput || !heightInput) return;

    function getAida() {
        return parseInt(aidaSelect.value) || 14;
    }

    function stitchesToInches(stitches, aida) {
        return Math.round((stitches / aida) * 10) / 10;
    }

    function inchesToStitches(inches, aida) {
        return Math.round(inches * aida);
    }

    function clampStitches(val) {
        return Math.max(10, Math.min(1000, val));
    }

    /** Update inches from current stitch values */
    function syncInchesFromStitches() {
        const aida = getAida();
        const w = parseInt(widthInput.value) || 70;
        const h = parseInt(heightInput.value) || 70;
        inchWidthInput.value = stitchesToInches(w, aida);
        inchHeightInput.value = stitchesToInches(h, aida);
    }

    /** Update the visual preview box and label */
    function updatePreview() {
        const w = parseInt(widthInput.value) || 70;
        const h = parseInt(heightInput.value) || 70;

        if (preview) {
            const maxSize = 140;
            const scale = Math.min(maxSize / Math.max(w, h), 2);
            preview.style.width = Math.max(20, Math.min(maxSize, w * scale)) + 'px';
            preview.style.height = Math.max(20, Math.min(maxSize, h * scale)) + 'px';
        }
        if (display) {
            display.textContent = w + ' \u00d7 ' + h + ' stitches';
        }
    }

    // Stitch inputs changed -> update inches + preview
    widthInput.addEventListener('input', function () {
        syncInchesFromStitches();
        updatePreview();
    });
    heightInput.addEventListener('input', function () {
        syncInchesFromStitches();
        updatePreview();
    });

    // Inch inputs changed -> update stitches + preview
    inchWidthInput.addEventListener('input', function () {
        const inches = parseFloat(inchWidthInput.value);
        if (!isNaN(inches) && inches > 0) {
            widthInput.value = clampStitches(inchesToStitches(inches, getAida()));
            updatePreview();
        }
    });
    inchHeightInput.addEventListener('input', function () {
        const inches = parseFloat(inchHeightInput.value);
        if (!isNaN(inches) && inches > 0) {
            heightInput.value = clampStitches(inchesToStitches(inches, getAida()));
            updatePreview();
        }
    });

    // Aida changed -> recalculate inches from current stitches
    aidaSelect.addEventListener('change', function () {
        syncInchesFromStitches();
    });

    // Initialize
    syncInchesFromStitches();
    updatePreview();
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

/* =============================================================================
   GA4 Event Tracking — Project Creation Funnel
   ============================================================================= */

function trackEvent(eventName, params) {
    if (typeof gtag === 'function') {
        gtag('event', eventName, params || {});
    }
}

/* =============================================================================
   Wizard Create Step - Creation Mode & Image Modal
   ============================================================================= */

/**
 * Initialize the create step with mode selection and from-image modal.
 * @param {Object} config - { gridWidth, gridHeight, maxPaletteColors }
 */
function initCreateStep(config) {
    const gridWidth = config.gridWidth;
    const gridHeight = config.gridHeight;
    const maxPaletteColors = config.maxPaletteColors;

    // DOM elements - mode cards
    const modeEmpty = document.getElementById('mode-empty');
    const modeImage = document.getElementById('mode-image');
    const modeSmartImage = document.getElementById('mode-smart-image');
    const creationModeInput = document.getElementById('creation-mode-input');
    const maxColorsInput = document.getElementById('max-colors-input');
    const imageConfigSummary = document.getElementById('image-config-summary');
    const imageFilenameEl = document.getElementById('image-filename');
    const imageMaxColorsEl = document.getElementById('image-max-colors');
    const reconfigureBtn = document.getElementById('reconfigure-image-btn');
    const createForm = document.getElementById('create-form');
    const createBtn = document.getElementById('create-btn');

    // DOM elements - smart image modal
    const swOverlay = document.getElementById('smart-wizard-overlay');
    const swTitle = document.getElementById('smart-wizard-title');
    const swCloseBtn = document.getElementById('smart-wizard-close');
    const swStepUpload = document.getElementById('sw-step-upload');
    const swStepPosition = document.getElementById('sw-step-position');
    const swStepPreview = document.getElementById('sw-step-preview');
    const swLoading = document.getElementById('sw-loading');
    const swResult = document.getElementById('sw-result');
    const swPreviewImg = document.getElementById('sw-preview-img');
    const swColorCount = document.getElementById('sw-color-count');
    const swCellCount = document.getElementById('sw-cell-count');
    const swMaxColors = document.getElementById('sw-max-colors');
    const swMaxColorsLabel = document.getElementById('sw-max-colors-label');
    const swBackBtn = document.getElementById('sw-back-btn');
    const swRefreshBtn = document.getElementById('sw-refresh-btn');
    const swNextBtn = document.getElementById('sw-next-btn');
    const swDropZone = document.getElementById('sw-drop-zone');
    const swFileInput = document.getElementById('sw-file-input');
    const swDropPrompt = document.getElementById('sw-drop-prompt');
    const swDropSelected = document.getElementById('sw-drop-selected');
    const swDropFilename = document.getElementById('sw-drop-filename');
    const swEdgeDetail = document.getElementById('sw-edge-detail');
    const swDespeckle = document.getElementById('sw-despeckle');
    const swBackstitch = document.getElementById('sw-backstitch');
    const swDithering = document.getElementById('sw-dithering');
    const swPosCanvas = document.getElementById('sw-positioner-canvas');
    const swPosScaleSlider = document.getElementById('sw-positioner-scale');
    const swPosScaleLabel = document.getElementById('sw-positioner-scale-label');
    const smartConfigSummary = document.getElementById('smart-config-summary');
    const smartConfigPreview = document.getElementById('smart-config-preview');
    const smartFilename = document.getElementById('smart-filename');
    const smartColorsSummary = document.getElementById('smart-colors-summary');
    const smartReconfigureBtn = document.getElementById('smart-reconfigure-btn');

    // DOM elements - from-image modal
    const overlay = document.getElementById('image-wizard-overlay');
    const modalTitle = document.getElementById('image-wizard-title');
    const closeBtn = document.getElementById('image-wizard-close');
    const stepUpload = document.getElementById('iw-step-upload');
    const stepPosition = document.getElementById('iw-step-position');
    const stepColors = document.getElementById('iw-step-colors');
    const backBtn = document.getElementById('iw-back-btn');
    const nextBtn = document.getElementById('iw-next-btn');
    const dropZone = document.getElementById('image-drop-zone');
    const fileInput = document.getElementById('image-file-input');
    const dropPrompt = document.getElementById('drop-zone-prompt');
    const dropSelected = document.getElementById('drop-zone-selected');
    const dropFilename = document.getElementById('drop-zone-filename');
    const posCanvas = document.getElementById('positioner-canvas');
    const posScaleSlider = document.getElementById('positioner-scale');
    const posScaleLabel = document.getElementById('positioner-scale-label');
    const iwMaxColors = document.getElementById('iw-max-colors');
    const iwMaxColorsLabel = document.getElementById('iw-max-colors-label');
    const iwQuantizedLabel = document.getElementById('iw-quantized-label');
    const iwPreviewOriginal = document.getElementById('iw-preview-original');
    const iwPreviewQuantized = document.getElementById('iw-preview-quantized');
    const configPreviewImg = document.getElementById('image-config-preview');

    // State - from-image
    let selectedFile = null;
    let composedBlob = null;
    let composedImageData = null; // ImageData from composed canvas for quantization
    let imageElement = null;
    let modalStep = 'upload'; // 'upload' | 'position' | 'colors'

    // Image positioner state
    let imgX = 0, imgY = 0, imgScale = 1.0;
    let isDragging = false, dragStartX = 0, dragStartY = 0, dragStartImgX = 0, dragStartImgY = 0;

    const MAX_CANVAS_DISPLAY = 380;

    // State - smart image modal
    let swFile = null;
    let swImageEl = null; // loaded Image element for positioner
    let swComposedBlob = null; // composed PNG blob at grid dimensions
    let swStep = 'upload'; // 'upload' | 'position' | 'preview'
    let swPreviewData = null; // base64 preview from server
    let swConfirmedMaxColors = 32;
    let swConfirmedEdgeDetail = 'medium';
    let swConfirmedDespeckle = 'off';
    let swConfirmedBackstitch = false;
    let swConfirmedDithering = 'atkinson';

    // Smart image positioner state
    let swImgX = 0, swImgY = 0, swImgScale = 1.0;
    let swIsDragging = false, swDragStartX = 0, swDragStartY = 0, swDragStartImgX = 0, swDragStartImgY = 0;

    // ---------------------------------------------------------------
    // Mode card selection
    // ---------------------------------------------------------------

    function selectMode(mode) {
        creationModeInput.value = mode;
        trackEvent('wizard_mode_select', { mode: mode });
        modeEmpty.classList.toggle('selected', mode === 'empty');
        modeImage.classList.toggle('selected', mode === 'image');
        if (modeSmartImage) modeSmartImage.classList.toggle('selected', mode === 'smart_image');

        if (mode === 'empty') {
            imageConfigSummary.style.display = 'none';
            smartConfigSummary.style.display = 'none';
            composedBlob = null;
        } else if (mode === 'image') {
            smartConfigSummary.style.display = 'none';
        } else if (mode === 'smart_image') {
            imageConfigSummary.style.display = 'none';
        }
    }

    modeEmpty.addEventListener('click', function() {
        selectMode('empty');
    });

    modeImage.addEventListener('click', function() {
        openModal();
    });

    if (reconfigureBtn) {
        reconfigureBtn.addEventListener('click', function() {
            openModal();
        });
    }

    // Smart Image mode card → open smart modal
    if (modeSmartImage) {
        modeSmartImage.addEventListener('click', function() {
            openSmartModal();
        });
    }

    // Smart Image "Change Settings" button
    if (smartReconfigureBtn) {
        smartReconfigureBtn.addEventListener('click', function() {
            openSmartModal();
        });
    }

    // ---------------------------------------------------------------
    // Smart Image Modal
    // ---------------------------------------------------------------

    function openSmartModal() {
        swOverlay.style.display = 'flex';
        showSmartStep('upload');
    }

    function closeSmartModal() {
        swOverlay.style.display = 'none';
    }

    swCloseBtn.addEventListener('click', closeSmartModal);
    swOverlay.addEventListener('click', function(e) {
        if (e.target === swOverlay) closeSmartModal();
    });

    function showSmartStep(step) {
        swStep = step;
        trackEvent('wizard_smart_step', { step: step });
        swStepUpload.style.display = step === 'upload' ? '' : 'none';
        swStepPosition.style.display = step === 'position' ? '' : 'none';
        swStepPreview.style.display = step === 'preview' ? '' : 'none';
        swBackBtn.style.display = step === 'upload' ? 'none' : '';
        swRefreshBtn.style.display = step === 'preview' ? '' : 'none';

        if (step === 'upload') {
            swTitle.textContent = 'Upload Image';
            swNextBtn.innerHTML = 'Next <i class="bi bi-arrow-right"></i>';
            swNextBtn.disabled = !swFile;
        } else if (step === 'position') {
            swTitle.textContent = 'Position Image';
            swNextBtn.innerHTML = 'Next <i class="bi bi-arrow-right"></i>';
            swNextBtn.disabled = false;
            initSwPositioner();
        } else if (step === 'preview') {
            swTitle.textContent = 'Preview';
            swNextBtn.innerHTML = '<i class="bi bi-check-lg"></i> Confirm';
            swNextBtn.disabled = true;
            composeSmartImage();
            fetchSmartPreview(swComposedBlob, parseInt(swMaxColors.value) || 32);
        }
    }

    swNextBtn.addEventListener('click', function() {
        if (swStep === 'upload') {
            showSmartStep('position');
        } else if (swStep === 'position') {
            showSmartStep('preview');
        } else if (swStep === 'preview') {
            // Confirm — store settings and close modal
            swConfirmedMaxColors = parseInt(swMaxColors.value) || 32;
            swConfirmedEdgeDetail = swEdgeDetail.value;
            swConfirmedDespeckle = swDespeckle.value;
            swConfirmedBackstitch = swBackstitch.checked;
            swConfirmedDithering = swDithering.value;
            trackEvent('wizard_smart_confirm', {
                max_colors: swConfirmedMaxColors,
                edge_detail: swConfirmedEdgeDetail,
                despeckle: swConfirmedDespeckle,
                backstitch: swConfirmedBackstitch ? 'on' : 'off',
                dithering: swConfirmedDithering,
            });
            selectMode('smart_image');
            smartConfigSummary.style.display = '';
            smartConfigPreview.src = swPreviewData || '';
            smartFilename.textContent = swFile ? swFile.name : '—';
            smartColorsSummary.textContent = swColorCount.textContent;
            closeSmartModal();
        }
    });

    swBackBtn.addEventListener('click', function() {
        if (swStep === 'position') {
            showSmartStep('upload');
        } else if (swStep === 'preview') {
            showSmartStep('position');
        }
    });

    // Smart modal drop zone
    swDropZone.addEventListener('click', function() {
        swFileInput.click();
    });

    swFileInput.addEventListener('change', function() {
        var file = swFileInput.files[0];
        if (file) handleSwFileSelected(file);
    });

    swDropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = 'copy';
        swDropZone.classList.add('active');
    });

    swDropZone.addEventListener('dragenter', function(e) {
        e.preventDefault();
        e.stopPropagation();
        swDropZone.classList.add('active');
    });

    swDropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        swDropZone.classList.remove('active');
    });

    swDropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        swDropZone.classList.remove('active');
        var file = e.dataTransfer.files[0];
        if (file) handleSwFileSelected(file);
    });

    function handleSwFileSelected(file) {
        swFile = file;
        swDropPrompt.style.display = 'none';
        swDropSelected.style.display = 'flex';
        swDropFilename.textContent = file.name;
        swNextBtn.disabled = false;

        // Load image element for positioner
        var objectUrl = URL.createObjectURL(file);
        var img = new Image();
        img.onload = function() {
            URL.revokeObjectURL(objectUrl);
            swImageEl = img;
            // Compute default fit and center
            var imgAspect = img.naturalWidth / img.naturalHeight;
            var gridAspect = gridWidth / gridHeight;
            if (imgAspect > gridAspect) {
                swImgX = 0;
                swImgY = (gridHeight - gridWidth / imgAspect) / 2;
            } else {
                swImgX = (gridWidth - gridHeight * imgAspect) / 2;
                swImgY = 0;
            }
            swImgScale = 1.0;
            swPosScaleSlider.value = '1.0';
            swPosScaleLabel.textContent = '100%';
        };
        img.src = objectUrl;
    }

    // ---------------------------------------------------------------
    // Smart Image Positioner
    // ---------------------------------------------------------------

    function swGetDisplayScale() {
        return MAX_CANVAS_DISPLAY / Math.max(gridWidth, gridHeight);
    }

    function swGetFitSize() {
        if (!swImageEl) return { w: 0, h: 0 };
        var imgAspect = swImageEl.naturalWidth / swImageEl.naturalHeight;
        var gridAspect = gridWidth / gridHeight;
        if (imgAspect > gridAspect) {
            return { w: gridWidth, h: gridWidth / imgAspect };
        } else {
            return { w: gridHeight * imgAspect, h: gridHeight };
        }
    }

    function initSwPositioner() {
        if (!swImageEl) return;
        drawSwPositionerCanvas();
    }

    function drawSwPositionerCanvas() {
        var ds = swGetDisplayScale();
        var cw = Math.round(gridWidth * ds);
        var ch = Math.round(gridHeight * ds);
        swPosCanvas.width = cw;
        swPosCanvas.height = ch;
        swPosCanvas.style.maxWidth = cw + 'px';

        var ctx = swPosCanvas.getContext('2d');
        if (!ctx) return;

        // Checkerboard background
        var checkSize = Math.max(4, Math.round(ds / 2));
        for (var y = 0; y < ch; y += checkSize) {
            for (var x = 0; x < cw; x += checkSize) {
                ctx.fillStyle = ((x / checkSize + y / checkSize) % 2 === 0) ? '#3a3a3a' : '#2a2a2a';
                ctx.fillRect(x, y, checkSize, checkSize);
            }
        }

        // Draw image
        if (swImageEl) {
            var fit = swGetFitSize();
            var drawW = fit.w * swImgScale;
            var drawH = fit.h * swImgScale;
            ctx.drawImage(swImageEl, swImgX * ds, swImgY * ds, drawW * ds, drawH * ds);
        }

        // Grid border
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 1;
        ctx.strokeRect(0.5, 0.5, cw - 1, ch - 1);

        // Crosshair lines
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.35)';
        ctx.lineWidth = 1;
        var midX = Math.round(cw / 2) + 0.5;
        var midY = Math.round(ch / 2) + 0.5;
        ctx.beginPath();
        ctx.moveTo(midX, 0);
        ctx.lineTo(midX, ch);
        ctx.moveTo(0, midY);
        ctx.lineTo(cw, midY);
        ctx.stroke();
        ctx.setLineDash([]);
    }

    // Canvas mouse drag
    swPosCanvas.addEventListener('mousedown', function(e) {
        e.preventDefault();
        swIsDragging = true;
        swDragStartX = e.clientX;
        swDragStartY = e.clientY;
        swDragStartImgX = swImgX;
        swDragStartImgY = swImgY;
        swPosCanvas.style.cursor = 'grabbing';
    });

    document.addEventListener('mousemove', function(e) {
        if (!swIsDragging) return;
        var ds = swGetDisplayScale();
        swImgX = swDragStartImgX + (e.clientX - swDragStartX) / ds;
        swImgY = swDragStartImgY + (e.clientY - swDragStartY) / ds;
        drawSwPositionerCanvas();
    });

    document.addEventListener('mouseup', function() {
        if (swIsDragging) {
            swIsDragging = false;
            swPosCanvas.style.cursor = 'grab';
        }
    });

    swPosCanvas.style.cursor = 'grab';

    // Scale slider
    swPosScaleSlider.addEventListener('input', function() {
        var newScale = parseFloat(swPosScaleSlider.value);
        if (!swImageEl) return;

        // Re-center around current image center
        var fit = swGetFitSize();
        var oldW = fit.w * swImgScale;
        var oldH = fit.h * swImgScale;
        var cx = swImgX + oldW / 2;
        var cy = swImgY + oldH / 2;

        var newW = fit.w * newScale;
        var newH = fit.h * newScale;
        swImgX = cx - newW / 2;
        swImgY = cy - newH / 2;
        swImgScale = newScale;

        swPosScaleLabel.textContent = Math.round(newScale * 100) + '%';
        drawSwPositionerCanvas();
    });

    // ---------------------------------------------------------------
    // Compose smart image (grid-size canvas → blob)
    // ---------------------------------------------------------------

    function dataUrlToBlobSw(dataUrl) {
        var parts = dataUrl.split(',');
        var mime = parts[0].match(/:(.*?);/)[1];
        var raw = atob(parts[1]);
        var arr = new Uint8Array(raw.length);
        for (var i = 0; i < raw.length; i++) {
            arr[i] = raw.charCodeAt(i);
        }
        return new Blob([arr], { type: mime });
    }

    function composeSmartImage() {
        var canvas = document.createElement('canvas');
        canvas.width = gridWidth;
        canvas.height = gridHeight;
        var ctx = canvas.getContext('2d');
        if (!ctx || !swImageEl) return;

        // White background
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, gridWidth, gridHeight);

        var fit = swGetFitSize();
        var drawW = fit.w * swImgScale;
        var drawH = fit.h * swImgScale;
        ctx.drawImage(swImageEl, swImgX, swImgY, drawW, drawH);

        var dataUrl = canvas.toDataURL('image/png');
        swComposedBlob = dataUrlToBlobSw(dataUrl);
    }

    // Smart modal slider → update label only
    swMaxColors.addEventListener('input', function() {
        swMaxColorsLabel.textContent = swMaxColors.value;
    });

    // Refresh button → re-compose and re-fetch preview
    swRefreshBtn.addEventListener('click', function() {
        composeSmartImage();
        fetchSmartPreview(swComposedBlob, parseInt(swMaxColors.value) || 32);
    });

    function fetchSmartPreview(blob, maxColors) {
        if (!blob) return;
        swLoading.style.display = '';
        swResult.style.display = 'none';
        swNextBtn.disabled = true;

        var fd = new FormData();
        fd.append('image', blob, 'composed.png');
        fd.append('max_colors', maxColors);
        fd.append('edge_detail', swEdgeDetail.value);
        fd.append('despeckle', swDespeckle.value);
        fd.append('backstitch', swBackstitch.checked ? 'true' : 'false');
        fd.append('dithering', swDithering.value);

        fetch('/projects/new/smart-preview', {
            method: 'POST',
            body: fd
        })
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
            if (data.error) {
                swLoading.style.display = 'none';
                swResult.style.display = '';
                swPreviewImg.style.display = 'none';
                swColorCount.textContent = '—';
                swCellCount.textContent = '—';
                alert(data.error);
                return;
            }
            swPreviewData = data.preview;
            swPreviewImg.src = data.preview;
            swPreviewImg.style.display = '';
            swColorCount.textContent = data.colorCount;
            swCellCount.textContent = data.cellCount;
            swLoading.style.display = 'none';
            swResult.style.display = '';
            swNextBtn.disabled = false;
        })
        .catch(function() {
            swLoading.style.display = 'none';
            swResult.style.display = '';
            alert('An error occurred while generating the preview.');
        });
    }

    // ---------------------------------------------------------------
    // Modal open/close
    // ---------------------------------------------------------------

    function openModal() {
        overlay.style.display = 'flex';
        showModalStep('upload');
    }

    function closeModal() {
        overlay.style.display = 'none';
    }

    closeBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) closeModal();
    });

    // ---------------------------------------------------------------
    // Modal step navigation
    // ---------------------------------------------------------------

    function showModalStep(step) {
        modalStep = step;
        trackEvent('wizard_image_step', { step: step });
        stepUpload.style.display = step === 'upload' ? '' : 'none';
        stepPosition.style.display = step === 'position' ? '' : 'none';
        stepColors.style.display = step === 'colors' ? '' : 'none';
        backBtn.style.display = step === 'upload' ? 'none' : '';

        if (step === 'upload') {
            modalTitle.textContent = 'Upload Image';
            nextBtn.textContent = 'Next ';
            nextBtn.innerHTML = 'Next <i class="bi bi-arrow-right"></i>';
            nextBtn.disabled = !selectedFile;
        } else if (step === 'position') {
            modalTitle.textContent = 'Position Image';
            nextBtn.innerHTML = 'Next <i class="bi bi-arrow-right"></i>';
            nextBtn.disabled = false;
            initPositioner();
        } else if (step === 'colors') {
            modalTitle.textContent = 'Color Settings';
            nextBtn.innerHTML = '<i class="bi bi-check-lg"></i> Confirm';
            nextBtn.disabled = false;
            updateQuantizedPreview();
        }
    }

    nextBtn.addEventListener('click', function() {
        if (modalStep === 'upload') {
            showModalStep('position');
        } else if (modalStep === 'position') {
            composeImage();
            showModalStep('colors');
        } else if (modalStep === 'colors') {
            // Confirm — store settings and close modal
            var mc = parseInt(iwMaxColors.value) || 16;
            mc = Math.max(2, Math.min(mc, maxPaletteColors));
            maxColorsInput.value = mc;

            // Draw quantized preview into summary thumbnail
            if (configPreviewImg && composedImageData) {
                var quantized = quantizeImageData(composedImageData, mc);
                drawPreviewCanvas(configPreviewImg, quantized);
            }

            trackEvent('wizard_image_confirm', { max_colors: mc });
            selectMode('image');
            imageConfigSummary.style.display = '';
            imageFilenameEl.textContent = selectedFile ? selectedFile.name : '—';
            imageMaxColorsEl.textContent = mc;
            closeModal();
        }
    });

    backBtn.addEventListener('click', function() {
        if (modalStep === 'position') {
            showModalStep('upload');
        } else if (modalStep === 'colors') {
            showModalStep('position');
        }
    });

    // ---------------------------------------------------------------
    // Drop zone
    // ---------------------------------------------------------------

    dropZone.addEventListener('click', function() {
        fileInput.click();
    });

    fileInput.addEventListener('change', function() {
        var file = fileInput.files[0];
        if (file) handleFileSelected(file);
    });

    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = 'copy';
        dropZone.classList.add('active');
    });

    dropZone.addEventListener('dragenter', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('active');
    });

    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('active');
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('active');
        var file = e.dataTransfer.files[0];
        if (file) handleFileSelected(file);
    });

    function handleFileSelected(file) {
        selectedFile = file;
        dropPrompt.style.display = 'none';
        dropSelected.style.display = 'flex';
        dropFilename.textContent = file.name;
        nextBtn.disabled = false;

        // Load image element for positioner
        var objectUrl = URL.createObjectURL(file);
        var img = new Image();
        img.onload = function() {
            URL.revokeObjectURL(objectUrl);
            imageElement = img;
            // Compute default fit and center
            var imgAspect = img.naturalWidth / img.naturalHeight;
            var gridAspect = gridWidth / gridHeight;
            var fitW, fitH;
            if (imgAspect > gridAspect) {
                fitW = gridWidth;
                fitH = gridWidth / imgAspect;
            } else {
                fitH = gridHeight;
                fitW = gridHeight * imgAspect;
            }
            imgX = (gridWidth - fitW) / 2;
            imgY = (gridHeight - fitH) / 2;
            imgScale = 1.0;
            posScaleSlider.value = '1.0';
            posScaleLabel.textContent = '100%';
        };
        img.src = objectUrl;
    }

    // ---------------------------------------------------------------
    // Image positioner (canvas)
    // ---------------------------------------------------------------

    function getDisplayScale() {
        return MAX_CANVAS_DISPLAY / Math.max(gridWidth, gridHeight);
    }

    function getFitSize() {
        if (!imageElement) return { w: 0, h: 0 };
        var imgAspect = imageElement.naturalWidth / imageElement.naturalHeight;
        var gridAspect = gridWidth / gridHeight;
        if (imgAspect > gridAspect) {
            return { w: gridWidth, h: gridWidth / imgAspect };
        } else {
            return { w: gridHeight * imgAspect, h: gridHeight };
        }
    }

    function initPositioner() {
        if (!imageElement) return;
        drawPositionerCanvas();
    }

    function drawPositionerCanvas() {
        var ds = getDisplayScale();
        var cw = Math.round(gridWidth * ds);
        var ch = Math.round(gridHeight * ds);
        posCanvas.width = cw;
        posCanvas.height = ch;
        posCanvas.style.maxWidth = cw + 'px';

        var ctx = posCanvas.getContext('2d');
        if (!ctx) return;

        // Checkerboard background
        var checkSize = Math.max(4, Math.round(ds / 2));
        for (var y = 0; y < ch; y += checkSize) {
            for (var x = 0; x < cw; x += checkSize) {
                ctx.fillStyle = ((x / checkSize + y / checkSize) % 2 === 0) ? '#3a3a3a' : '#2a2a2a';
                ctx.fillRect(x, y, checkSize, checkSize);
            }
        }

        // Draw image
        if (imageElement) {
            var fit = getFitSize();
            var drawW = fit.w * imgScale;
            var drawH = fit.h * imgScale;
            ctx.drawImage(imageElement, imgX * ds, imgY * ds, drawW * ds, drawH * ds);
        }

        // Grid border
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 1;
        ctx.strokeRect(0.5, 0.5, cw - 1, ch - 1);

        // Crosshair lines (center of grid)
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.35)';
        ctx.lineWidth = 1;
        var midX = Math.round(cw / 2) + 0.5;
        var midY = Math.round(ch / 2) + 0.5;
        ctx.beginPath();
        ctx.moveTo(midX, 0);
        ctx.lineTo(midX, ch);
        ctx.moveTo(0, midY);
        ctx.lineTo(cw, midY);
        ctx.stroke();
        ctx.setLineDash([]);
    }

    // Canvas mouse drag
    posCanvas.addEventListener('mousedown', function(e) {
        e.preventDefault();
        isDragging = true;
        dragStartX = e.clientX;
        dragStartY = e.clientY;
        dragStartImgX = imgX;
        dragStartImgY = imgY;
        posCanvas.style.cursor = 'grabbing';
    });

    document.addEventListener('mousemove', function(e) {
        if (!isDragging) return;
        var ds = getDisplayScale();
        imgX = dragStartImgX + (e.clientX - dragStartX) / ds;
        imgY = dragStartImgY + (e.clientY - dragStartY) / ds;
        drawPositionerCanvas();
    });

    document.addEventListener('mouseup', function() {
        if (isDragging) {
            isDragging = false;
            posCanvas.style.cursor = 'grab';
        }
    });

    posCanvas.style.cursor = 'grab';

    // Scale slider
    posScaleSlider.addEventListener('input', function() {
        var newScale = parseFloat(posScaleSlider.value);
        if (!imageElement) return;

        // Re-center around current image center
        var fit = getFitSize();
        var oldW = fit.w * imgScale;
        var oldH = fit.h * imgScale;
        var cx = imgX + oldW / 2;
        var cy = imgY + oldH / 2;

        var newW = fit.w * newScale;
        var newH = fit.h * newScale;
        imgX = cx - newW / 2;
        imgY = cy - newH / 2;
        imgScale = newScale;

        posScaleLabel.textContent = Math.round(newScale * 100) + '%';
        drawPositionerCanvas();
    });

    // ---------------------------------------------------------------
    // Compose final image (synchronous — no race condition)
    // ---------------------------------------------------------------

    function dataUrlToBlob(dataUrl) {
        var parts = dataUrl.split(',');
        var mime = parts[0].match(/:(.*?);/)[1];
        var raw = atob(parts[1]);
        var arr = new Uint8Array(raw.length);
        for (var i = 0; i < raw.length; i++) {
            arr[i] = raw.charCodeAt(i);
        }
        return new Blob([arr], { type: mime });
    }

    function composeImage() {
        var canvas = document.createElement('canvas');
        canvas.width = gridWidth;
        canvas.height = gridHeight;
        var ctx = canvas.getContext('2d');
        if (!ctx || !imageElement) return;

        // White background (avoids transparent PNG → white-after-alpha-removal issues)
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, gridWidth, gridHeight);

        var fit = getFitSize();
        var drawW = fit.w * imgScale;
        var drawH = fit.h * imgScale;
        ctx.drawImage(imageElement, imgX, imgY, drawW, drawH);

        // Store pixel data for quantization preview
        composedImageData = ctx.getImageData(0, 0, gridWidth, gridHeight);

        // Synchronous: toDataURL is instant, no race condition
        var dataUrl = canvas.toDataURL('image/png');
        composedBlob = dataUrlToBlob(dataUrl);

        // Draw original preview canvas
        drawPreviewCanvas(iwPreviewOriginal, composedImageData);

        // Draw quantized preview
        updateQuantizedPreview();
    }

    // ---------------------------------------------------------------
    // Preview canvases (original + quantized)
    // ---------------------------------------------------------------

    var PREVIEW_MAX = 160;

    function drawPreviewCanvas(canvasEl, imgData) {
        if (!canvasEl || !imgData) return;
        var sw = imgData.width, sh = imgData.height;
        var scale = Math.min(PREVIEW_MAX / sw, PREVIEW_MAX / sh, 1);
        // Use at least the source size so pixelated rendering looks crisp
        var dw = Math.round(sw * Math.max(scale, PREVIEW_MAX / Math.max(sw, sh)));
        var dh = Math.round(sh * Math.max(scale, PREVIEW_MAX / Math.max(sw, sh)));

        // Draw source data to a temp canvas at original size
        var tmp = document.createElement('canvas');
        tmp.width = sw;
        tmp.height = sh;
        tmp.getContext('2d').putImageData(imgData, 0, 0);

        // Draw scaled to display canvas
        canvasEl.width = dw;
        canvasEl.height = dh;
        var ctx = canvasEl.getContext('2d');
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(tmp, 0, 0, dw, dh);
    }

    /**
     * Median-cut color quantization on ImageData.
     * Returns a new ImageData with colors reduced to maxColors.
     */
    function quantizeImageData(srcData, maxColors) {
        var w = srcData.width, h = srcData.height;
        var src = srcData.data;
        var numPixels = w * h;

        // Collect all non-white pixels as [r, g, b, index]
        var pixels = [];
        for (var i = 0; i < numPixels; i++) {
            var off = i * 4;
            var r = src[off], g = src[off + 1], b = src[off + 2];
            if (r > 250 && g > 250 && b > 250) continue; // skip white
            pixels.push([r, g, b, i]);
        }

        if (pixels.length === 0) {
            return new ImageData(new Uint8ClampedArray(src), w, h);
        }

        // Median cut: split pixel list into buckets by widest channel range
        var buckets = [pixels];
        while (buckets.length < maxColors) {
            // Find bucket with widest channel range
            var bestIdx = 0, bestRange = -1, bestCh = 0;
            for (var bi = 0; bi < buckets.length; bi++) {
                var bk = buckets[bi];
                if (bk.length < 2) continue;
                for (var ch = 0; ch < 3; ch++) {
                    var lo = 255, hi = 0;
                    for (var pi = 0; pi < bk.length; pi++) {
                        var v = bk[pi][ch];
                        if (v < lo) lo = v;
                        if (v > hi) hi = v;
                    }
                    var range = hi - lo;
                    if (range > bestRange) {
                        bestRange = range;
                        bestIdx = bi;
                        bestCh = ch;
                    }
                }
            }
            if (bestRange <= 0) break;

            // Sort that bucket by the widest channel and split at median
            var toSplit = buckets[bestIdx];
            toSplit.sort(function(a, b) { return a[bestCh] - b[bestCh]; });
            var mid = Math.floor(toSplit.length / 2);
            buckets[bestIdx] = toSplit.slice(0, mid);
            buckets.push(toSplit.slice(mid));
        }

        // Compute average color per bucket
        var centers = [];
        for (var bi = 0; bi < buckets.length; bi++) {
            var bk = buckets[bi];
            var sr = 0, sg = 0, sb = 0;
            for (var pi = 0; pi < bk.length; pi++) {
                sr += bk[pi][0]; sg += bk[pi][1]; sb += bk[pi][2];
            }
            var n = bk.length;
            centers.push([Math.round(sr / n), Math.round(sg / n), Math.round(sb / n)]);
        }

        // Build output: map each non-white pixel to nearest center
        var out = new Uint8ClampedArray(src);
        for (var bi = 0; bi < buckets.length; bi++) {
            var c = centers[bi];
            var bk = buckets[bi];
            for (var pi = 0; pi < bk.length; pi++) {
                var off = bk[pi][3] * 4;
                out[off] = c[0]; out[off + 1] = c[1]; out[off + 2] = c[2];
            }
        }

        return new ImageData(out, w, h);
    }

    function updateQuantizedPreview() {
        if (!composedImageData) return;
        var mc = parseInt(iwMaxColors.value) || 16;
        mc = Math.max(2, Math.min(mc, maxPaletteColors));

        var quantized = quantizeImageData(composedImageData, mc);
        drawPreviewCanvas(iwPreviewQuantized, quantized);

        if (iwQuantizedLabel) iwQuantizedLabel.textContent = mc;
        if (iwMaxColorsLabel) iwMaxColorsLabel.textContent = mc + ' colors';
    }

    // Update quantized preview when slider changes
    iwMaxColors.addEventListener('input', function() {
        updateQuantizedPreview();
    });

    // ---------------------------------------------------------------
    // Form submission
    // ---------------------------------------------------------------

    createForm.addEventListener('submit', function(e) {
        var mode = creationModeInput.value;
        trackEvent('wizard_create', { mode: mode });

        if (mode === 'image') {
            e.preventDefault();

            if (!composedBlob) {
                alert('No image has been configured. Please select an image first.');
                return;
            }

            createBtn.disabled = true;
            createBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Creating...';

            var fd = new FormData(createForm);
            fd.set('creation_mode', 'image');
            fd.set('max_colors', maxColorsInput.value);
            fd.append('image', composedBlob, 'composed.png');

            fetch(createForm.action || window.location.href, {
                method: 'POST',
                body: fd,
                redirect: 'follow'
            }).then(function(resp) {
                window.location.href = resp.url;
            }).catch(function() {
                createBtn.disabled = false;
                createBtn.innerHTML = '<i class="bi bi-check-lg"></i> Create Project';
                alert('An error occurred. Please try again.');
            });
        } else if (mode === 'smart_image') {
            e.preventDefault();

            if (!swComposedBlob) {
                alert('Please select and position an image first.');
                return;
            }

            createBtn.disabled = true;
            createBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Creating...';

            var mc = Math.max(2, Math.min(swConfirmedMaxColors, maxPaletteColors));

            var fd = new FormData(createForm);
            fd.set('creation_mode', 'smart_image');
            fd.set('max_colors', mc);
            fd.set('edge_detail', swConfirmedEdgeDetail);
            fd.set('despeckle', swConfirmedDespeckle);
            fd.set('backstitch', swConfirmedBackstitch ? 'true' : 'false');
            fd.set('dithering', swConfirmedDithering);
            fd.append('image', swComposedBlob, 'composed.png');

            fetch(createForm.action || window.location.href, {
                method: 'POST',
                body: fd,
                redirect: 'follow'
            }).then(function(resp) {
                window.location.href = resp.url;
            }).catch(function() {
                createBtn.disabled = false;
                createBtn.innerHTML = '<i class="bi bi-check-lg"></i> Create Project';
                alert('An error occurred. Please try again.');
            });
        }
        // else: empty mode — let normal form submit proceed
    });
}
