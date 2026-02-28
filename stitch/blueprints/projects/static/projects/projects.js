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
   Shared — Median-Cut Color Quantization
   ============================================================================= */

/**
 * Quantize an ImageData to at most maxColors using median-cut.
 * White-ish pixels (r,g,b > 250) are left untouched.
 * @param {ImageData} srcData
 * @param {number} maxColors
 * @returns {ImageData}
 */
function quantizeImageData(srcData, maxColors) {
    var w = srcData.width, h = srcData.height;
    var src = srcData.data;
    var numPixels = w * h;

    var pixels = [];
    for (var i = 0; i < numPixels; i++) {
        var off = i * 4;
        var r = src[off], g = src[off + 1], b = src[off + 2];
        if (r > 250 && g > 250 && b > 250) continue;
        pixels.push([r, g, b, i]);
    }

    if (pixels.length === 0) {
        return new ImageData(new Uint8ClampedArray(src), w, h);
    }

    var buckets = [pixels];
    while (buckets.length < maxColors) {
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

        var toSplit = buckets[bestIdx];
        toSplit.sort(function(a, b) { return a[bestCh] - b[bestCh]; });
        var mid = Math.floor(toSplit.length / 2);
        buckets[bestIdx] = toSplit.slice(0, mid);
        buckets.push(toSplit.slice(mid));
    }

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


/* =============================================================================
   Wizard Create Step - Creation Mode Selection
   ============================================================================= */

/**
 * Initialize the create step with mode selection.
 * From Image and Smart Image navigate to dedicated pages via links.
 */
function initCreateStep() {
    var modeEmpty = document.getElementById('mode-empty');
    var createForm = document.getElementById('create-form');

    if (!modeEmpty || !createForm) return;

    modeEmpty.addEventListener('click', function() {
        modeEmpty.classList.add('selected');
        trackEvent('wizard_mode_select', { mode: 'empty' });
    });

    createForm.addEventListener('submit', function() {
        trackEvent('wizard_create', { mode: 'empty' });
    });
}


/* =============================================================================
   From Image — Position Step
   ============================================================================= */

/**
 * Initialize the from-image position page.
 * Positioner canvas with drag + scale, side-by-side original/quantized preview,
 * max colors slider, and "Create Project" button that composes and submits.
 * @param {Object} config - { gridWidth, gridHeight, maxPaletteColors, tempImageUrl }
 */
function initImagePositionStep(config) {
    var gridWidth = config.gridWidth;
    var gridHeight = config.gridHeight;
    var tempImageUrl = config.tempImageUrl;
    var maxPaletteColors = config.maxPaletteColors || 128;

    var posCanvas = document.getElementById('positioner-canvas');
    var posScaleSlider = document.getElementById('positioner-scale');
    var posScaleLabel = document.getElementById('positioner-scale-label');
    var nextBtn = document.getElementById('position-next-btn');
    var positionForm = document.getElementById('position-form');
    var composedInput = document.getElementById('composed-image-input');

    // Max colors slider + preview pair
    var maxColorsSlider = document.getElementById('pos-max-colors');
    var maxColorsLabel = document.getElementById('pos-max-colors-label');
    var maxColorsHidden = document.getElementById('pos-max-colors-hidden');
    var originalPreviewCanvas = document.getElementById('pos-original-preview');
    var quantizedPreviewCanvas = document.getElementById('pos-quantized-preview');
    var quantizedCountLabel = document.getElementById('pos-quantized-count');

    var MAX_CANVAS_DISPLAY = 380;

    var imageEl = null;
    var imgX = 0, imgY = 0, imgScale = 1.0;
    var isDragging = false, dragStartX = 0, dragStartY = 0, dragStartImgX = 0, dragStartImgY = 0;

    // Load image from server
    var img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = function() {
        imageEl = img;
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
        drawCanvas();
        scheduleQuantizedPreview();
    };
    img.src = tempImageUrl;

    function getDisplayScale() {
        return MAX_CANVAS_DISPLAY / Math.max(gridWidth, gridHeight);
    }

    function getFitSize() {
        if (!imageEl) return { w: 0, h: 0 };
        var imgAspect = imageEl.naturalWidth / imageEl.naturalHeight;
        var gridAspect = gridWidth / gridHeight;
        if (imgAspect > gridAspect) {
            return { w: gridWidth, h: gridWidth / imgAspect };
        } else {
            return { w: gridHeight * imgAspect, h: gridHeight };
        }
    }

    function drawCanvas() {
        var ds = getDisplayScale();
        var cw = Math.round(gridWidth * ds);
        var ch = Math.round(gridHeight * ds);
        posCanvas.width = cw;
        posCanvas.height = ch;
        posCanvas.style.maxWidth = cw + 'px';

        var ctx = posCanvas.getContext('2d');
        if (!ctx) return;

        // Checkerboard
        var checkSize = Math.max(4, Math.round(ds / 2));
        for (var y = 0; y < ch; y += checkSize) {
            for (var x = 0; x < cw; x += checkSize) {
                ctx.fillStyle = ((x / checkSize + y / checkSize) % 2 === 0) ? '#3a3a3a' : '#2a2a2a';
                ctx.fillRect(x, y, checkSize, checkSize);
            }
        }

        if (imageEl) {
            var fit = getFitSize();
            var drawW = fit.w * imgScale;
            var drawH = fit.h * imgScale;
            ctx.drawImage(imageEl, imgX * ds, imgY * ds, drawW * ds, drawH * ds);
        }

        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 1;
        ctx.strokeRect(0.5, 0.5, cw - 1, ch - 1);

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
        drawCanvas();
    });

    document.addEventListener('mouseup', function() {
        if (isDragging) {
            isDragging = false;
            posCanvas.style.cursor = 'grab';
            scheduleQuantizedPreview();
        }
    });

    posCanvas.style.cursor = 'grab';

    posScaleSlider.addEventListener('input', function() {
        var newScale = parseFloat(posScaleSlider.value);
        if (!imageEl) return;

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
        drawCanvas();
        scheduleQuantizedPreview();
    });

    // Quantized preview — debounced
    var quantizeTimer = null;
    var QUANTIZE_DEBOUNCE = 400;

    function scheduleQuantizedPreview() {
        if (quantizeTimer) clearTimeout(quantizeTimer);
        quantizeTimer = setTimeout(updateQuantizedPreview, QUANTIZE_DEBOUNCE);
    }

    function drawPreviewToCanvas(targetCanvas, srcImageData) {
        var maxPreview = 160;
        var sw = srcImageData.width, sh = srcImageData.height;
        var ratio = Math.max(maxPreview / Math.max(sw, sh), 1);
        var dw = Math.round(sw * ratio);
        var dh = Math.round(sh * ratio);

        var tmp = document.createElement('canvas');
        tmp.width = sw;
        tmp.height = sh;
        tmp.getContext('2d').putImageData(srcImageData, 0, 0);

        targetCanvas.width = dw;
        targetCanvas.height = dh;
        var ctx = targetCanvas.getContext('2d');
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(tmp, 0, 0, dw, dh);
    }

    function updateQuantizedPreview() {
        if (!imageEl || !quantizedPreviewCanvas) return;

        // Compose at grid resolution
        var tmpCanvas = document.createElement('canvas');
        tmpCanvas.width = gridWidth;
        tmpCanvas.height = gridHeight;
        var tmpCtx = tmpCanvas.getContext('2d');
        if (!tmpCtx) return;

        tmpCtx.fillStyle = '#ffffff';
        tmpCtx.fillRect(0, 0, gridWidth, gridHeight);

        var fit = getFitSize();
        var drawW = fit.w * imgScale;
        var drawH = fit.h * imgScale;
        tmpCtx.drawImage(imageEl, imgX, imgY, drawW, drawH);

        var imgData = tmpCtx.getImageData(0, 0, gridWidth, gridHeight);

        // Draw original
        if (originalPreviewCanvas) {
            drawPreviewToCanvas(originalPreviewCanvas, imgData);
        }

        // Draw quantized version
        var mc = parseInt(maxColorsSlider.value) || 16;
        mc = Math.max(2, Math.min(mc, maxPaletteColors));
        var quantized = quantizeImageData(imgData, mc);
        drawPreviewToCanvas(quantizedPreviewCanvas, quantized);

        if (quantizedCountLabel) {
            quantizedCountLabel.textContent = mc;
        }
    }

    maxColorsSlider.addEventListener('input', function() {
        maxColorsLabel.textContent = maxColorsSlider.value;
        scheduleQuantizedPreview();
    });

    // Create button — compose at high resolution and submit
    nextBtn.addEventListener('click', function() {
        if (!imageEl) return;

        nextBtn.disabled = true;
        nextBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Creating...';

        var maxDim = Math.max(gridWidth, gridHeight);
        var composeFactor = Math.max(1, Math.min(8, Math.floor(2048 / maxDim)));

        var cw = gridWidth * composeFactor;
        var ch = gridHeight * composeFactor;

        var canvas = document.createElement('canvas');
        canvas.width = cw;
        canvas.height = ch;
        var ctx = canvas.getContext('2d');
        if (!ctx) return;

        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';

        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, cw, ch);

        var fit = getFitSize();
        var drawW = fit.w * imgScale * composeFactor;
        var drawH = fit.h * imgScale * composeFactor;
        ctx.drawImage(imageEl, imgX * composeFactor, imgY * composeFactor, drawW, drawH);

        canvas.toBlob(function(blob) {
            var dt = new DataTransfer();
            dt.items.add(new File([blob], 'composed.jpg', { type: 'image/jpeg' }));
            composedInput.files = dt.files;
            maxColorsHidden.value = maxColorsSlider.value;
            positionForm.submit();
        }, 'image/jpeg', 0.95);
    });
}


/* =============================================================================
   Smart Image — Upload Step
   ============================================================================= */

/**
 * Initialize the smart image upload page.
 */
function initSmartUploadStep() {
    var dropZone = document.getElementById('smart-drop-zone');
    var fileInput = document.getElementById('smart-file-input');
    var dropPrompt = document.getElementById('smart-drop-prompt');
    var dropSelected = document.getElementById('smart-drop-selected');
    var dropFilename = document.getElementById('smart-drop-filename');
    var nextBtn = document.getElementById('upload-next-btn');

    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', function() {
        fileInput.click();
    });

    fileInput.addEventListener('change', function() {
        if (fileInput.files[0]) showSelected(fileInput.files[0]);
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
        if (file) {
            // Set file on the hidden input via DataTransfer
            var dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
            showSelected(file);
        }
    });

    function showSelected(file) {
        dropPrompt.style.display = 'none';
        dropSelected.style.display = 'flex';
        dropFilename.textContent = file.name;
        nextBtn.disabled = false;
    }
}


/* =============================================================================
   Smart Image — Upload + Position Step (combined)
   ============================================================================= */

/**
 * Combined upload + position step for smart image flow.
 * User selects a file, positions/zooms it on the grid canvas, then submits
 * the composed image directly.
 * @param {Object} config - { gridWidth, gridHeight }
 */
function initSmartUploadPositionStep(config) {
    var gridWidth = config.gridWidth;
    var gridHeight = config.gridHeight;

    // Drop zone elements
    var dropZone = document.getElementById('smart-drop-zone');
    var fileInput = document.getElementById('smart-file-input');
    var dropPrompt = document.getElementById('smart-drop-prompt');
    var dropSelected = document.getElementById('smart-drop-selected');
    var dropFilename = document.getElementById('smart-drop-filename');
    var changeFileBtn = document.getElementById('smart-change-file');

    // Position section
    var positionSection = document.getElementById('smart-position-section');
    var posCanvas = document.getElementById('positioner-canvas');
    var posScaleSlider = document.getElementById('positioner-scale');
    var posScaleLabel = document.getElementById('positioner-scale-label');

    // Form elements
    var nextBtn = document.getElementById('upload-next-btn');
    var uploadForm = document.getElementById('upload-form');
    var composedInput = document.getElementById('composed-image-input');

    // Image adjustment sliders
    var brightnessSlider = document.getElementById('pos-brightness');
    var brightnessLabel = document.getElementById('pos-brightness-label');
    var contrastSlider = document.getElementById('pos-contrast');
    var contrastLabel = document.getElementById('pos-contrast-label');
    var saturationSlider = document.getElementById('pos-saturation');
    var saturationLabel = document.getElementById('pos-saturation-label');

    var MAX_CANVAS_DISPLAY = 380;
    var imageEl = null;
    var imgX = 0, imgY = 0, imgScale = 1.0;
    var isDragging = false, dragStartX = 0, dragStartY = 0, dragStartImgX = 0, dragStartImgY = 0;

    if (!dropZone || !fileInput || !posCanvas) return;

    // --- Drop zone logic ---
    dropZone.addEventListener('click', function(e) {
        if (e.target === changeFileBtn || changeFileBtn.contains(e.target)) return;
        fileInput.click();
    });

    changeFileBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        fileInput.click();
    });

    fileInput.addEventListener('change', function() {
        if (fileInput.files[0]) onFileSelected(fileInput.files[0]);
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
        if (file) {
            var dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
            onFileSelected(file);
        }
    });

    function onFileSelected(file) {
        dropPrompt.style.display = 'none';
        dropSelected.style.display = 'flex';
        dropFilename.textContent = file.name;
        nextBtn.disabled = false;

        // Show position section and load image locally
        positionSection.style.display = '';
        var url = URL.createObjectURL(file);
        var img = new Image();
        img.onload = function() {
            imageEl = img;
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
            posScaleSlider.value = 1.0;
            posScaleLabel.textContent = '100%';
            drawCanvas();
        };
        img.src = url;
    }

    // --- Canvas drawing ---
    function getDisplayScale() {
        return MAX_CANVAS_DISPLAY / Math.max(gridWidth, gridHeight);
    }

    function getFitSize() {
        if (!imageEl) return { w: 0, h: 0 };
        var imgAspect = imageEl.naturalWidth / imageEl.naturalHeight;
        var gridAspect = gridWidth / gridHeight;
        if (imgAspect > gridAspect) {
            return { w: gridWidth, h: gridWidth / imgAspect };
        } else {
            return { w: gridHeight * imgAspect, h: gridHeight };
        }
    }

    function buildFilterString() {
        var b = 1 + (parseInt(brightnessSlider.value) || 0) / 100;
        var c = 1 + (parseInt(contrastSlider.value) || 0) / 100;
        var s = 1 + (parseInt(saturationSlider.value) || 0) / 100;
        return 'brightness(' + b + ') contrast(' + c + ') saturate(' + s + ')';
    }

    function drawCanvas() {
        var ds = getDisplayScale();
        var cw = Math.round(gridWidth * ds);
        var ch = Math.round(gridHeight * ds);
        posCanvas.width = cw;
        posCanvas.height = ch;
        posCanvas.style.maxWidth = cw + 'px';

        var ctx = posCanvas.getContext('2d');
        if (!ctx) return;

        var checkSize = Math.max(4, Math.round(ds / 2));
        for (var y = 0; y < ch; y += checkSize) {
            for (var x = 0; x < cw; x += checkSize) {
                ctx.fillStyle = ((x / checkSize + y / checkSize) % 2 === 0) ? '#3a3a3a' : '#2a2a2a';
                ctx.fillRect(x, y, checkSize, checkSize);
            }
        }

        if (imageEl) {
            var fit = getFitSize();
            var drawW = fit.w * imgScale;
            var drawH = fit.h * imgScale;
            ctx.filter = buildFilterString();
            ctx.drawImage(imageEl, imgX * ds, imgY * ds, drawW * ds, drawH * ds);
            ctx.filter = 'none';
        }

        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 1;
        ctx.strokeRect(0.5, 0.5, cw - 1, ch - 1);

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

    // --- Drag to reposition ---
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
        drawCanvas();
    });
    document.addEventListener('mouseup', function() {
        if (isDragging) {
            isDragging = false;
            posCanvas.style.cursor = 'grab';
        }
    });
    posCanvas.style.cursor = 'grab';

    // --- Scale slider ---
    posScaleSlider.addEventListener('input', function() {
        var newScale = parseFloat(posScaleSlider.value);
        if (!imageEl) return;

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
        drawCanvas();
    });

    // --- Adjustment sliders ---
    brightnessSlider.addEventListener('input', function() {
        brightnessLabel.textContent = brightnessSlider.value;
        drawCanvas();
    });
    contrastSlider.addEventListener('input', function() {
        contrastLabel.textContent = contrastSlider.value;
        drawCanvas();
    });
    saturationSlider.addEventListener('input', function() {
        saturationLabel.textContent = saturationSlider.value;
        drawCanvas();
    });

    // --- Next button: compose and submit ---
    nextBtn.addEventListener('click', function() {
        if (!imageEl) return;

        nextBtn.disabled = true;
        nextBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Composing...';

        var maxDim = Math.max(gridWidth, gridHeight);
        var composeFactor = Math.max(1, Math.min(8, Math.floor(2048 / maxDim)));

        var cw = gridWidth * composeFactor;
        var ch = gridHeight * composeFactor;

        var canvas = document.createElement('canvas');
        canvas.width = cw;
        canvas.height = ch;
        var ctx = canvas.getContext('2d');
        if (!ctx) return;

        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';

        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, cw, ch);

        var fit = getFitSize();
        var drawW = fit.w * imgScale * composeFactor;
        var drawH = fit.h * imgScale * composeFactor;
        ctx.filter = buildFilterString();
        ctx.drawImage(imageEl, imgX * composeFactor, imgY * composeFactor, drawW, drawH);
        ctx.filter = 'none';

        canvas.toBlob(function(blob) {
            var dt = new DataTransfer();
            dt.items.add(new File([blob], 'composed.jpg', { type: 'image/jpeg' }));
            composedInput.files = dt.files;
            uploadForm.submit();
        }, 'image/jpeg', 0.95);
    });
}


/* =============================================================================
   Smart Image — Position Step
   ============================================================================= */

/**
 * Initialize the smart image position page.
 * @param {Object} config - { gridWidth, gridHeight, tempImageUrl }
 */
function initSmartPositionStep(config) {
    var gridWidth = config.gridWidth;
    var gridHeight = config.gridHeight;
    var tempImageUrl = config.tempImageUrl;

    var posCanvas = document.getElementById('positioner-canvas');
    var posScaleSlider = document.getElementById('positioner-scale');
    var posScaleLabel = document.getElementById('positioner-scale-label');
    var nextBtn = document.getElementById('position-next-btn');
    var positionForm = document.getElementById('position-form');
    var composedInput = document.getElementById('composed-image-input');

    // Image adjustment sliders
    var brightnessSlider = document.getElementById('pos-brightness');
    var brightnessLabel = document.getElementById('pos-brightness-label');
    var contrastSlider = document.getElementById('pos-contrast');
    var contrastLabel = document.getElementById('pos-contrast-label');
    var saturationSlider = document.getElementById('pos-saturation');
    var saturationLabel = document.getElementById('pos-saturation-label');

    // Max colors slider + preview pair
    var maxPaletteColors = config.maxPaletteColors || 128;
    var maxColorsSlider = document.getElementById('pos-max-colors');
    var maxColorsLabel = document.getElementById('pos-max-colors-label');
    var maxColorsHidden = document.getElementById('pos-max-colors-hidden');
    var originalPreviewCanvas = document.getElementById('pos-original-preview');
    var quantizedPreviewCanvas = document.getElementById('pos-quantized-preview');
    var quantizedCountLabel = document.getElementById('pos-quantized-count');

    var MAX_CANVAS_DISPLAY = 380;

    var imageEl = null;
    var imgX = 0, imgY = 0, imgScale = 1.0;
    var isDragging = false, dragStartX = 0, dragStartY = 0, dragStartImgX = 0, dragStartImgY = 0;

    // Load image from server
    var img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = function() {
        imageEl = img;
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
        drawCanvas();
        scheduleQuantizedPreview();
    };
    img.src = tempImageUrl;

    function getDisplayScale() {
        return MAX_CANVAS_DISPLAY / Math.max(gridWidth, gridHeight);
    }

    function getFitSize() {
        if (!imageEl) return { w: 0, h: 0 };
        var imgAspect = imageEl.naturalWidth / imageEl.naturalHeight;
        var gridAspect = gridWidth / gridHeight;
        if (imgAspect > gridAspect) {
            return { w: gridWidth, h: gridWidth / imgAspect };
        } else {
            return { w: gridHeight * imgAspect, h: gridHeight };
        }
    }

    function buildFilterString() {
        var b = 1 + (parseInt(brightnessSlider.value) || 0) / 100;
        var c = 1 + (parseInt(contrastSlider.value) || 0) / 100;
        var s = 1 + (parseInt(saturationSlider.value) || 0) / 100;
        return 'brightness(' + b + ') contrast(' + c + ') saturate(' + s + ')';
    }

    function drawCanvas() {
        var ds = getDisplayScale();
        var cw = Math.round(gridWidth * ds);
        var ch = Math.round(gridHeight * ds);
        posCanvas.width = cw;
        posCanvas.height = ch;
        posCanvas.style.maxWidth = cw + 'px';

        var ctx = posCanvas.getContext('2d');
        if (!ctx) return;

        // Checkerboard
        var checkSize = Math.max(4, Math.round(ds / 2));
        for (var y = 0; y < ch; y += checkSize) {
            for (var x = 0; x < cw; x += checkSize) {
                ctx.fillStyle = ((x / checkSize + y / checkSize) % 2 === 0) ? '#3a3a3a' : '#2a2a2a';
                ctx.fillRect(x, y, checkSize, checkSize);
            }
        }

        if (imageEl) {
            var fit = getFitSize();
            var drawW = fit.w * imgScale;
            var drawH = fit.h * imgScale;
            ctx.filter = buildFilterString();
            ctx.drawImage(imageEl, imgX * ds, imgY * ds, drawW * ds, drawH * ds);
            ctx.filter = 'none';
        }

        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 1;
        ctx.strokeRect(0.5, 0.5, cw - 1, ch - 1);

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
        drawCanvas();
    });

    document.addEventListener('mouseup', function() {
        if (isDragging) {
            isDragging = false;
            posCanvas.style.cursor = 'grab';
            scheduleQuantizedPreview();
        }
    });

    posCanvas.style.cursor = 'grab';

    posScaleSlider.addEventListener('input', function() {
        var newScale = parseFloat(posScaleSlider.value);
        if (!imageEl) return;

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
        drawCanvas();
        scheduleQuantizedPreview();
    });

    // Image adjustment slider listeners
    brightnessSlider.addEventListener('input', function() {
        brightnessLabel.textContent = brightnessSlider.value;
        drawCanvas();
        scheduleQuantizedPreview();
    });
    contrastSlider.addEventListener('input', function() {
        contrastLabel.textContent = contrastSlider.value;
        drawCanvas();
        scheduleQuantizedPreview();
    });
    saturationSlider.addEventListener('input', function() {
        saturationLabel.textContent = saturationSlider.value;
        drawCanvas();
        scheduleQuantizedPreview();
    });

    // Quantized preview — debounced
    var quantizeTimer = null;
    var QUANTIZE_DEBOUNCE = 400;

    function scheduleQuantizedPreview() {
        if (quantizeTimer) clearTimeout(quantizeTimer);
        quantizeTimer = setTimeout(updateQuantizedPreview, QUANTIZE_DEBOUNCE);
    }

    function drawPreviewToCanvas(targetCanvas, srcImageData) {
        var maxPreview = 160;
        var sw = srcImageData.width, sh = srcImageData.height;
        var ratio = Math.max(maxPreview / Math.max(sw, sh), 1);
        var dw = Math.round(sw * ratio);
        var dh = Math.round(sh * ratio);

        var tmp = document.createElement('canvas');
        tmp.width = sw;
        tmp.height = sh;
        tmp.getContext('2d').putImageData(srcImageData, 0, 0);

        targetCanvas.width = dw;
        targetCanvas.height = dh;
        var ctx = targetCanvas.getContext('2d');
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(tmp, 0, 0, dw, dh);
    }

    function updateQuantizedPreview() {
        if (!imageEl || !quantizedPreviewCanvas) return;

        // Compose at grid resolution with filters
        var tmpCanvas = document.createElement('canvas');
        tmpCanvas.width = gridWidth;
        tmpCanvas.height = gridHeight;
        var tmpCtx = tmpCanvas.getContext('2d');
        if (!tmpCtx) return;

        tmpCtx.fillStyle = '#ffffff';
        tmpCtx.fillRect(0, 0, gridWidth, gridHeight);

        var fit = getFitSize();
        var drawW = fit.w * imgScale;
        var drawH = fit.h * imgScale;
        tmpCtx.filter = buildFilterString();
        tmpCtx.drawImage(imageEl, imgX, imgY, drawW, drawH);
        tmpCtx.filter = 'none';

        var imgData = tmpCtx.getImageData(0, 0, gridWidth, gridHeight);

        // Draw adjusted original
        if (originalPreviewCanvas) {
            drawPreviewToCanvas(originalPreviewCanvas, imgData);
        }

        // Draw quantized version
        var mc = parseInt(maxColorsSlider.value) || 32;
        mc = Math.max(2, Math.min(mc, maxPaletteColors));
        var quantized = quantizeImageData(imgData, mc);
        drawPreviewToCanvas(quantizedPreviewCanvas, quantized);

        if (quantizedCountLabel) {
            quantizedCountLabel.textContent = mc;
        }
    }

    maxColorsSlider.addEventListener('input', function() {
        maxColorsLabel.textContent = maxColorsSlider.value;
        scheduleQuantizedPreview();
    });

    // Next button — compose at high resolution and submit
    nextBtn.addEventListener('click', function() {
        if (!imageEl) return;

        nextBtn.disabled = true;
        nextBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Composing...';

        var maxDim = Math.max(gridWidth, gridHeight);
        var composeFactor = Math.max(1, Math.min(8, Math.floor(2048 / maxDim)));

        var cw = gridWidth * composeFactor;
        var ch = gridHeight * composeFactor;

        var canvas = document.createElement('canvas');
        canvas.width = cw;
        canvas.height = ch;
        var ctx = canvas.getContext('2d');
        if (!ctx) return;

        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';

        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, cw, ch);

        var fit = getFitSize();
        var drawW = fit.w * imgScale * composeFactor;
        var drawH = fit.h * imgScale * composeFactor;
        ctx.filter = buildFilterString();
        ctx.drawImage(imageEl, imgX * composeFactor, imgY * composeFactor, drawW, drawH);
        ctx.filter = 'none';

        canvas.toBlob(function(blob) {
            // Create a File from the blob and set it on the hidden input
            var dt = new DataTransfer();
            dt.items.add(new File([blob], 'composed.jpg', { type: 'image/jpeg' }));
            composedInput.files = dt.files;
            maxColorsHidden.value = maxColorsSlider.value;
            positionForm.submit();
        }, 'image/jpeg', 0.95);
    });
}


/* =============================================================================
   Smart Image — Adjust Step
   ============================================================================= */

/**
 * Initialize the smart image adjust page.
 * @param {Object} config - { gridWidth, gridHeight, maxPaletteColors, previewUrl }
 */
function initSmartAdjustStep(config) {
    var previewUrl = config.previewUrl;

    var maxColorsValue = config.maxColors || 32;

    // Controls — sliders
    var smoothing = document.getElementById('sa-smoothing');
    var smoothingLabel = document.getElementById('sa-smoothing-label');

    // Controls — selects & checkboxes
    var sharpness = document.getElementById('sa-sharpness');
    var edgeDetail = document.getElementById('sa-edge-detail');
    var dithering = document.getElementById('sa-dithering');
    var despeckle = document.getElementById('sa-despeckle');
    var backstitch = document.getElementById('sa-backstitch');
    var removeBg = document.getElementById('sa-remove-bg');

    // Preview elements
    var loading = document.getElementById('sa-loading');
    var result = document.getElementById('sa-result');
    var previewImg = document.getElementById('sa-preview-img');
    var colorCount = document.getElementById('sa-color-count');
    var cellCount = document.getElementById('sa-cell-count');
    var paletteSection = document.getElementById('sa-palette-section');
    var paletteGrid = document.getElementById('sa-palette-grid');

    // Form + hidden inputs
    var adjustForm = document.getElementById('adjust-form');
    var createBtn = document.getElementById('sa-create-btn');

    // Debounce timer for auto-refresh
    var debounceTimer = null;
    var DEBOUNCE_MS = 600;
    var fetchAbort = null;

    function scheduleFetch() {
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function() {
            fetchPreview();
        }, DEBOUNCE_MS);
    }

    // Slider label updates + auto-refresh on change
    smoothing.addEventListener('input', function() {
        smoothingLabel.textContent = smoothing.value;
        scheduleFetch();
    });

    // Auto-refresh on select/checkbox changes (immediate, no debounce needed)
    sharpness.addEventListener('change', function() { fetchPreview(); });
    edgeDetail.addEventListener('change', function() { fetchPreview(); });
    dithering.addEventListener('change', function() { fetchPreview(); });
    despeckle.addEventListener('change', function() { fetchPreview(); });
    backstitch.addEventListener('change', function() { fetchPreview(); });
    removeBg.addEventListener('change', function() { fetchPreview(); });

    // Fetch preview
    function fetchPreview() {
        // Cancel any pending debounce
        if (debounceTimer) { clearTimeout(debounceTimer); debounceTimer = null; }

        // Abort previous in-flight request
        if (fetchAbort) fetchAbort.abort();
        fetchAbort = new AbortController();

        loading.style.display = '';
        result.style.display = 'none';

        var fd = new FormData();
        fd.append('max_colors', maxColorsValue);
        fd.append('sharpness', sharpness.value);
        fd.append('edge_detail', edgeDetail.value);
        fd.append('despeckle', despeckle.value);
        fd.append('backstitch', backstitch.checked ? 'true' : 'false');
        fd.append('dithering', dithering.value);
        fd.append('remove_bg', removeBg.checked ? 'true' : 'false');
        fd.append('smoothing', smoothing.value);

        fetch(previewUrl, {
            method: 'POST',
            body: fd,
            signal: fetchAbort.signal
        })
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
            loading.style.display = 'none';
            result.style.display = '';

            if (data.error) {
                previewImg.style.display = 'none';
                colorCount.textContent = '--';
                cellCount.textContent = '--';
                paletteSection.style.display = 'none';
                alert(data.error);
                return;
            }

            previewImg.src = data.preview;
            previewImg.style.display = '';
            colorCount.textContent = data.colorCount;
            cellCount.textContent = data.cellCount;

            // Render palette swatches
            if (data.palette && data.palette.length > 0) {
                paletteSection.style.display = '';
                paletteGrid.innerHTML = '';
                data.palette.forEach(function(c) {
                    var swatch = document.createElement('div');
                    swatch.className = 'smart-palette-swatch';
                    swatch.style.backgroundColor = c.rgbHex;
                    swatch.title = c.vendor.toUpperCase() + ' ' + c.code + ' — ' + c.name;
                    paletteGrid.appendChild(swatch);
                });
            } else {
                paletteSection.style.display = 'none';
            }
        })
        .catch(function(err) {
            if (err.name === 'AbortError') return; // superseded by newer request
            loading.style.display = 'none';
            result.style.display = '';
            alert('An error occurred while generating the preview.');
        });
    }

    // Auto-fetch initial preview on page load
    fetchPreview();

    // Sync hidden inputs on form submit
    adjustForm.addEventListener('submit', function() {
        document.getElementById('sa-max-colors-hidden').value = maxColorsValue;
        document.getElementById('sa-sharpness-hidden').value = sharpness.value;
        document.getElementById('sa-edge-detail-hidden').value = edgeDetail.value;
        document.getElementById('sa-despeckle-hidden').value = despeckle.value;
        document.getElementById('sa-backstitch-hidden').value = backstitch.checked ? 'true' : 'false';
        document.getElementById('sa-dithering-hidden').value = dithering.value;
        document.getElementById('sa-remove-bg-hidden').value = removeBg.checked ? 'true' : 'false';
        document.getElementById('sa-smoothing-hidden').value = smoothing.value;

        createBtn.disabled = true;
        createBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Creating...';
    });
}


/* =============================================================================
   Diffusion — Upload Step (wrapper for smart upload)
   ============================================================================= */

/**
 * Initialize the diffusion upload page (identical to smart upload).
 */
function initDiffusionUploadStep() {
    initSmartUploadStep();
}


/* =============================================================================
   Diffusion — Process Step (blur-to-reveal animation)
   ============================================================================= */

/**
 * Initialize the diffusion process page (job-based).
 *
 * @param {Object} config
 * @param {string} config.healthUrl     - GET URL for service health
 * @param {string} config.jobStartUrl   - POST URL to submit generation job
 * @param {string} config.jobStatusUrl  - GET URL to poll job status
 */
function initDiffusionProcessStep(config) {
    var originalImg = document.getElementById('diffusion-original');
    var resultImg = document.getElementById('diffusion-result');
    var overlay = document.getElementById('diffusion-overlay');
    var statusText = document.getElementById('diffusion-status-text');
    var errorDiv = document.getElementById('diffusion-error');
    var errorMsg = document.getElementById('diffusion-error-msg');
    var retryBtn = document.getElementById('diffusion-retry-btn');
    var nextBtn = document.getElementById('process-next-btn');

    if (!originalImg || !resultImg) return;

    function setStatus(msg) {
        if (statusText) statusText.textContent = msg;
    }

    function formatProgress(data) {
        if (!data.total || !data.step) return 'Generating pixel art...';
        var pct = Math.round((data.step / data.total) * 100);
        var msg = 'Generating pixel art — step ' + data.step + '/' + data.total + ' (' + pct + '%)';
        if (data.elapsed > 0 && data.step > 0) {
            var perStep = data.elapsed / data.step;
            var remaining = Math.round(perStep * (data.total - data.step));
            if (remaining > 0) msg += ' — ~' + remaining + 's remaining';
        }
        return msg;
    }

    var healthRetries = 0;
    var MAX_HEALTH_RETRIES = 30;

    function start() {
        // Reset UI
        errorDiv.style.display = 'none';
        overlay.classList.remove('hidden');
        resultImg.classList.remove('revealed');
        nextBtn.style.display = 'none';
        healthRetries = 0;
        setStatus('Checking service...');
        console.log('[Smart] Starting health check, url:', config.healthUrl);

        pollHealth();
    }

    function pollHealth() {
        healthRetries++;
        console.log('[Smart] Health check attempt', healthRetries);

        if (healthRetries > MAX_HEALTH_RETRIES) {
            showError('AI service appears to be offline. Please try again later or check that the service is running.');
            return;
        }

        fetch(config.healthUrl)
            .then(function(resp) {
                console.log('[Smart] Health response status:', resp.status);
                return resp.json();
            })
            .then(function(data) {
                console.log('[Smart] Health data:', JSON.stringify(data));
                if (data.status === 'ready') {
                    submitJob();
                } else if (data.status === 'offline') {
                    setStatus('AI service is offline. Retrying... (' + healthRetries + '/' + MAX_HEALTH_RETRIES + ')');
                    setTimeout(pollHealth, 5000);
                } else {
                    setStatus('Loading AI model... (' + data.status + ')');
                    setTimeout(pollHealth, 3000);
                }
            })
            .catch(function(err) {
                console.error('[Smart] Health check error:', err);
                setStatus('AI service is offline. Retrying... (' + healthRetries + '/' + MAX_HEALTH_RETRIES + ')');
                setTimeout(pollHealth, 5000);
            });
    }

    function submitJob() {
        setStatus('Starting generation...');
        console.log('[Smart] Submitting job, url:', config.jobStartUrl);

        // Start blur animation
        originalImg.classList.remove('sharpening');
        void originalImg.offsetWidth;
        originalImg.classList.add('sharpening');

        fetch(config.jobStartUrl, { method: 'POST' })
            .then(function(resp) {
                console.log('[Smart] Job start response status:', resp.status);
                return resp.json();
            })
            .then(function(data) {
                console.log('[Smart] Job start data:', JSON.stringify(data));
                if (data.error) {
                    showError(data.error);
                    return;
                }
                // Start polling the job
                setTimeout(pollJob, 2000);
            })
            .catch(function(err) {
                console.error('[Smart] Job start error:', err);
                showError('Network error: ' + err.message);
            });
    }

    function pollJob() {
        fetch(config.jobStatusUrl)
            .then(function(resp) { return resp.json(); })
            .then(function(data) {
                if (data.error && data.status !== 'running') {
                    showError(data.error);
                    return;
                }

                if (data.status === 'done') {
                    onComplete(data.result);
                    return;
                }

                if (data.status === 'error') {
                    showError(data.error || 'Generation failed.');
                    return;
                }

                // Still running — show progress
                setStatus(formatProgress(data));
                setTimeout(pollJob, 2000);
            })
            .catch(function() {
                // Transient error — keep polling
                setTimeout(pollJob, 3000);
            });
    }

    // Max colors controls
    var colorsSection = document.getElementById('process-colors-section');
    var colorsSlider = document.getElementById('process-colors-slider');
    var colorsLabel = document.getElementById('process-colors-label');
    var nextBaseHref = nextBtn ? nextBtn.href : '';

    function showCompleted() {
        nextBtn.style.display = '';
        if (colorsSection) colorsSection.style.display = '';
        updateNextHref();
    }

    function updateNextHref() {
        if (!nextBtn || !colorsSlider) return;
        var val = colorsSlider.value;
        var sep = nextBaseHref.indexOf('?') >= 0 ? '&' : '?';
        nextBtn.href = nextBaseHref + sep + 'max_colors=' + val;
    }

    if (colorsSlider) {
        colorsSlider.addEventListener('input', function() {
            if (colorsLabel) colorsLabel.textContent = colorsSlider.value;
            updateNextHref();
        });
    }

    function onComplete(resultDataUrl) {
        setStatus('Done!');
        resultImg.src = resultDataUrl;
        resultImg.onload = function() {
            overlay.classList.add('hidden');
            resultImg.classList.add('revealed');
            showCompleted();
        };
    }

    function showError(msg) {
        overlay.classList.add('hidden');
        errorDiv.style.display = 'block';
        errorMsg.textContent = msg;
    }

    retryBtn.addEventListener('click', function() {
        start();
    });

    // If result already exists (user navigated back), show it immediately
    if (config.existingResultUrl) {
        resultImg.src = config.existingResultUrl;
        resultImg.onload = function() {
            overlay.classList.add('hidden');
            resultImg.classList.add('revealed');
            showCompleted();
        };
    } else {
        start();
    }
}
