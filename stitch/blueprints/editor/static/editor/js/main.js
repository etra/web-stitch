/**
 * Main Editor Module
 * Entry point - initializes and coordinates all modules
 */

import { StateManager } from './state.js';
import { Viewport } from './viewport.js';
import { Renderer } from './renderer.js';
import { ToolManager } from './tools.js';
import { Storage } from './storage.js';
import { API } from './api.js';
import { StitchPicker } from './view.js';

class Editor {
    constructor(projectData) {
        this.projectData = projectData;
        this.canvas = document.getElementById('canvas');
        this.canvasWrapper = document.getElementById('canvasWrapper');

        // Initialize modules
        this.initCanvas();
        this.stateManager = new StateManager(projectData);
        this.viewport = new Viewport(
            this.canvas.width,
            this.canvas.height,
            projectData.width,
            projectData.height
        );
        this.renderer = new Renderer(this.canvas, this.viewport);
        this.toolManager = new ToolManager(this.stateManager, this.viewport);
        this.storage = new Storage(projectData.id);
        this.api = new API(projectData.id);

        // State
        this.isPanning = false;
        this.panStart = null;
        this.isDeleting = false;     // Track if right mouse is held (delete mode)
        this.currentMode = 'draw';   // Current mode: 'draw', 'pan', 'erase'
        this.lastSaveTime = Date.now();
        this.autoSaveInterval = 10000; // 10 seconds

        // Initialize UI components
        this.setupStitchPicker();

        // Initialize
        this.setupEventListeners();
        this.setupAutoSave();
        this.setupColorModal();
        this.updateUI();
        this.render();

        console.log('Editor initialized', projectData);
    }

    /**
     * Set the current drawing mode
     * @param {string} mode - 'draw', 'pan', or 'erase'
     */
    setMode(mode) {
        this.currentMode = mode;

        // Update button states
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        const activeBtn = mode === 'draw' ? 'drawModeBtn'
                        : mode === 'pan' ? 'panModeBtn'
                        : 'eraseModeBtn';
        document.getElementById(activeBtn)?.classList.add('active');

        // Update cursor
        this.updateCursor();
    }

    /**
     * Update cursor based on current mode
     */
    updateCursor() {
        if (this.isPanning) {
            this.canvas.style.cursor = 'grabbing';
        } else if (this.currentMode === 'pan') {
            this.canvas.style.cursor = 'grab';
        } else if (this.currentMode === 'erase' || this.isDeleting) {
            this.canvas.style.cursor = 'not-allowed';
        } else {
            this.canvas.style.cursor = 'crosshair';
        }
    }

    /**
     * Setup the visual stitch picker component
     */
    setupStitchPicker() {
        // Find the stitch picker container defined in HTML
        const pickerContainer = document.getElementById('stitchPickerContainer');

        if (!pickerContainer) {
            console.warn('Stitch picker container not found in HTML');
            return;
        }

        // Initialize and render the picker
        this.stitchPicker = new StitchPicker(this.renderer, this.toolManager);
        this.stitchPicker.render(pickerContainer);

        // Listen for stitch type changes from the picker
        document.addEventListener('stitchTypeChanged', (e) => {
            this.updateToolButtons();
            this.render();
        });
    }

    /**
     * Initialize canvas size
     */
    initCanvas() {
        const rect = this.canvasWrapper.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Canvas mouse events
        this.canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.onMouseUp.bind(this));
        this.canvas.addEventListener('mouseleave', this.onMouseLeave.bind(this));
        this.canvas.addEventListener('wheel', this.onWheel.bind(this));
        this.canvas.addEventListener('contextmenu', (e) => e.preventDefault()); // Prevent right-click menu

        // Keyboard events
        document.addEventListener('keydown', this.onKeyDown.bind(this));
        document.addEventListener('keyup', this.onKeyUp.bind(this));

        // Window resize
        window.addEventListener('resize', this.onResize.bind(this));

        // Toolbar buttons
        document.getElementById('undoBtn').addEventListener('click', () => {
            if (this.stateManager.undo()) {
                this.render();
                this.updateUI();
            }
        });

        document.getElementById('redoBtn').addEventListener('click', () => {
            if (this.stateManager.redo()) {
                this.render();
                this.updateUI();
            }
        });

        // Render mode buttons
        document.getElementById('renderColorBtn').addEventListener('click', () => {
            this.renderer.setRenderMode('color');
            this.updateRenderModeButtons();
            this.render();
        });

        document.getElementById('renderSymbolBtn').addEventListener('click', () => {
            this.renderer.setRenderMode('symbol');
            this.updateRenderModeButtons();
            this.render();
        });

        document.getElementById('renderBothBtn').addEventListener('click', () => {
            this.renderer.setRenderMode('both');
            this.updateRenderModeButtons();
            this.render();
        });

        document.getElementById('zoomInBtn').addEventListener('click', () => {
            this.viewport.zoomAt(
                this.canvas.width / 2,
                this.canvas.height / 2,
                1
            );
            this.updateUI();
            this.render();
        });

        document.getElementById('zoomOutBtn').addEventListener('click', () => {
            this.viewport.zoomAt(
                this.canvas.width / 2,
                this.canvas.height / 2,
                -1
            );
            this.updateUI();
            this.render();
        });

        document.getElementById('zoomResetBtn').addEventListener('click', () => {
            this.viewport.reset();
            this.updateUI();
            this.render();
        });

        document.getElementById('saveBtn').addEventListener('click', () => {
            this.saveToBackend();
        });

        // Tool selection buttons
        document.querySelectorAll('.tool-select').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tool = btn.dataset.tool;
                const stitch = btn.dataset.stitch;

                if (tool) {
                    this.toolManager.setTool(tool);
                }
                if (stitch) {
                    this.toolManager.setStitchType(stitch);
                }

                this.updateToolButtons();
            });
        });

        // Color management buttons
        document.getElementById('addColorBtnToolbar').addEventListener('click', () => {
            this.addColor();
        });

        document.getElementById('replaceColorBtn').addEventListener('click', () => {
            this.showReplaceColorModal();
        });

        document.getElementById('deleteColorBtn').addEventListener('click', () => {
            this.showDeleteColorModal();
        });

        // Add layer button
        document.getElementById('addLayerBtn').addEventListener('click', () => {
            this.addLayer();
        });

        // Mode switcher buttons
        document.getElementById('drawModeBtn').addEventListener('click', () => {
            this.setMode('draw');
        });
        document.getElementById('panModeBtn').addEventListener('click', () => {
            this.setMode('pan');
        });
        document.getElementById('eraseModeBtn').addEventListener('click', () => {
            this.setMode('erase');
        });

        // State changes
        this.stateManager.subscribe(() => {
            this.render();
            this.updateUI();
            this.saveToLocalStorage(); // Fire and forget - async in background
        });

        // Tool changes
        this.toolManager.onToolChangeCallback(() => {
            this.updateToolButtons();
            this.updatePaletteUI();
        });
    }

    /**
     * Mouse down event
     */
    onMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Middle mouse button - always pan
        if (e.button === 1) {
            this.isPanning = true;
            this.panStart = { x, y };
            this.updateCursor();
        }
        // Right mouse button - always delete
        else if (e.button === 2) {
            e.preventDefault(); // Prevent context menu
            this.isDeleting = true;
            this.updateCursor();

            const gridPos = this.viewport.screenToGrid(x, y);
            if (this.viewport.isValidGridPos(gridPos.x, gridPos.y)) {
                const state = this.stateManager.getState();
                const activeLayerId = state.state.activeLayerId;
                const activeLayer = state.state.layers.find(l => l.id === activeLayerId);

                if (activeLayer && activeLayer.editable) {
                    this.stateManager.updateCell(activeLayerId, gridPos.x, gridPos.y, null);
                }
            }
        }
        // Left mouse button - controlled by current mode
        else if (e.button === 0) {
            if (this.currentMode === 'pan') {
                // Pan mode - pan with left mouse
                this.isPanning = true;
                this.panStart = { x, y };
                this.updateCursor();
            } else if (this.currentMode === 'erase') {
                // Erase mode - delete cell
                const gridPos = this.viewport.screenToGrid(x, y);
                if (this.viewport.isValidGridPos(gridPos.x, gridPos.y)) {
                    const state = this.stateManager.getState();
                    const activeLayerId = state.state.activeLayerId;
                    const activeLayer = state.state.layers.find(l => l.id === activeLayerId);

                    if (activeLayer && activeLayer.editable) {
                        this.stateManager.updateCell(activeLayerId, gridPos.x, gridPos.y, null);
                    }
                }
            } else if (this.currentMode === 'draw') {
                // Draw mode - normal drawing
                this.toolManager.startDrawing(x, y);
            }
        }
    }

    /**
     * Mouse move event
     */
    onMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Right-click drag OR erase mode + left drag - delete cells
        if (this.isDeleting || (this.currentMode === 'erase' && e.buttons === 1)) {
            const gridPos = this.viewport.screenToGrid(x, y);
            if (this.viewport.isValidGridPos(gridPos.x, gridPos.y)) {
                const state = this.stateManager.getState();
                const activeLayerId = state.state.activeLayerId;
                const activeLayer = state.state.layers.find(l => l.id === activeLayerId);

                if (activeLayer && activeLayer.editable) {
                    this.stateManager.updateCell(activeLayerId, gridPos.x, gridPos.y, null);
                }
            }
            return; // Don't continue with other mouse move logic
        }

        if (this.isPanning && this.panStart) {
            const dx = x - this.panStart.x;
            const dy = y - this.panStart.y;
            this.viewport.pan(dx, dy);
            this.panStart = { x, y };
            this.render();
        } else {
            // Update hover
            const gridPos = this.viewport.screenToGrid(x, y);
            this.renderer.setHover(gridPos.x, gridPos.y);

            // Continue drawing if mouse is down
            this.toolManager.continueDrawing(x, y);

            this.render();
        }
    }

    /**
     * Mouse up event
     */
    onMouseUp(e) {
        if (this.isPanning) {
            this.isPanning = false;
            this.panStart = null;
            this.canvas.style.cursor = 'crosshair';
        } else {
            this.toolManager.stopDrawing();
        }

        // Exit delete mode
        if (this.isDeleting) {
            this.isDeleting = false;
            if (!this.isCtrlPressed && !this.isSpacePressed) {
                this.canvas.style.cursor = 'crosshair';
            }
        }
    }

    /**
     * Mouse leave event
     */
    onMouseLeave(e) {
        this.onMouseUp(e);
        this.isDeleting = false;
        this.renderer.setHover(null, null);
        this.render();
    }

    /**
     * Mouse wheel event (zoom)
     */
    onWheel(e) {
        e.preventDefault();

        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        this.viewport.zoomAt(x, y, e.deltaY > 0 ? -1 : 1);
        this.updateUI();
        this.render();
    }

    /**
     * Key down event
     */
    onKeyDown(e) {
        // Ctrl/Cmd + Z = Undo
        if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
            e.preventDefault();
            if (this.stateManager.undo()) {
                this.render();
                this.updateUI();
            }
        }

        // Ctrl/Cmd + Y or Ctrl/Cmd + Shift + Z = Redo
        if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
            e.preventDefault();
            if (this.stateManager.redo()) {
                this.render();
                this.updateUI();
            }
        }


        // Ctrl/Cmd + S = Save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            this.saveToBackend();
        }

        // Delete/Backspace = Clear hovered cell
        if (e.key === 'Delete' || e.key === 'Backspace') {
            if (this.renderer.hoverCell) {
                e.preventDefault();
                const { x, y } = this.renderer.hoverCell;
                const state = this.stateManager.getState();
                const activeLayerId = state.state.activeLayerId;
                const activeLayer = state.state.layers.find(l => l.id === activeLayerId);

                if (activeLayer && activeLayer.editable) {
                    // Clear the cell
                    this.stateManager.updateCell(activeLayerId, x, y, null);
                }
            }
        }
    }

    /**
     * Key up event
     */
    onKeyUp(e) {
        // No keyboard shortcuts for mode switching anymore
    }

    /**
     * Window resize event
     */
    onResize() {
        this.initCanvas();
        this.viewport.updateCanvasSize(this.canvas.width, this.canvas.height);
        this.render();
    }

    /**
     * Render the canvas
     */
    render() {
        const toolPreview = this.toolManager.getShapePreview();
        this.renderer.render(this.stateManager.getState(), toolPreview);
    }

    /**
     * Update UI (buttons, zoom level, etc.)
     */
    updateUI() {
        // Update zoom level
        document.getElementById('zoomLevel').textContent = `${this.viewport.getZoomPercent()}%`;

        // Update undo/redo buttons
        document.getElementById('undoBtn').disabled = !this.stateManager.canUndo();
        document.getElementById('redoBtn').disabled = !this.stateManager.canRedo();

        // Update palette
        this.updatePaletteUI();

        // Update layers
        this.updateLayersUI();
    }

    /**
     * Update tool buttons
     */
    updateToolButtons() {
        const currentTool = this.toolManager.getTool();
        const currentStitch = this.toolManager.getStitchType();

        document.querySelectorAll('.tool-select').forEach(btn => {
            const btnTool = btn.dataset.tool;
            const btnStitch = btn.dataset.stitch;

            if (btnTool === currentTool && (!btnStitch || btnStitch === currentStitch)) {
                btn.classList.remove('btn-outline-secondary');
                btn.classList.add('btn-primary');
            } else {
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-outline-secondary');
            }
        });
    }

    /**
     * Update render mode buttons
     */
    updateRenderModeButtons() {
        const renderMode = this.renderer.getRenderMode();

        document.getElementById('renderColorBtn').classList.toggle('active', renderMode === 'color');
        document.getElementById('renderSymbolBtn').classList.toggle('active', renderMode === 'symbol');
        document.getElementById('renderBothBtn').classList.toggle('active', renderMode === 'both');
    }

    /**
     * Update palette UI
     */
    updatePaletteUI() {
        const state = this.stateManager.getState();
        const palette = state.state.palette;
        const currentColorIndex = this.toolManager.getColorIndex();

        const paletteToolbar = document.getElementById('colorPaletteToolbar');
        paletteToolbar.innerHTML = '';

        if (palette.length === 0) {
            paletteToolbar.innerHTML = '<small class="text-muted" style="font-size: 0.75rem;">No colors - click + to add</small>';
            return;
        }

        palette.forEach((color, index) => {
            const colorEl = document.createElement('div');
            colorEl.className = 'color-square' + (index === currentColorIndex ? ' active' : '');
            colorEl.style.backgroundColor = color.rgbHex;

            // Build tooltip text
            let tooltipText = color.name;
            if (color.vendor || color.code) {
                tooltipText += ` (${color.vendor || ''} ${color.code || ''})`.trim();
            }
            colorEl.title = tooltipText;

            colorEl.addEventListener('click', () => {
                this.toolManager.setColorIndex(index);
                this.updatePaletteUI();
            });

            paletteToolbar.appendChild(colorEl);
        });
    }

    /**
     * Update layers UI
     */
    updateLayersUI() {
        const state = this.stateManager.getState();
        const layers = state.state.layers;
        const activeLayerId = state.state.activeLayerId;

        const layersList = document.getElementById('layersList');
        layersList.innerHTML = '';

        layers.forEach(layer => {
            const layerEl = document.createElement('div');
            layerEl.className = 'layer-item' + (layer.id === activeLayerId ? ' active' : '');
            layerEl.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <span style="cursor: pointer; flex: 1;">${layer.name}</span>
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-link p-0 visibility-toggle" data-layer-id="${layer.id}" style="text-decoration: none;">
                            ${layer.visible ? '👁' : '👁‍🗨'}
                        </button>
                        ${layers.length > 1 ? `
                            <button class="btn btn-sm btn-link p-0 text-danger delete-layer" data-layer-id="${layer.id}" style="text-decoration: none;">
                                🗑
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;

            // Set active layer on name click
            layerEl.querySelector('span').addEventListener('click', () => {
                this.stateManager.setActiveLayer(layer.id);
                this.updateLayersUI();
            });

            // Toggle visibility
            const visibilityBtn = layerEl.querySelector('.visibility-toggle');
            visibilityBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.stateManager.toggleLayerVisibility(layer.id);
                this.updateLayersUI();
                this.render();
            });

            // Delete layer
            const deleteBtn = layerEl.querySelector('.delete-layer');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (confirm(`Delete layer "${layer.name}"?`)) {
                        this.stateManager.deleteLayer(layer.id);
                        this.updateLayersUI();
                        this.render();
                    }
                });
            }

            layersList.appendChild(layerEl);
        });
    }

    /**
     * Add a new color to palette
     */
    /**
     * Setup color selection modal with select2
     */
    setupColorModal() {
        const modal = document.getElementById('addColorModal');
        const confirmBtn = document.getElementById('confirmAddColor');
        const colorSelect = $('#colorSelect');
        const previewDiv = document.getElementById('colorPreview');
        const previewSwatch = document.getElementById('previewSwatch');
        const previewName = document.getElementById('previewName');
        const previewCode = document.getElementById('previewCode');

        let selectedColor = null;

        // Initialize select2 when modal is shown
        modal.addEventListener('shown.bs.modal', async () => {
            // Load colors if not already loaded
            if (colorSelect.find('option').length <= 1) {
                const result = await this.api.getAvailableColors();
                if (result.success) {
                    result.colors.forEach(color => {
                        const option = new Option(color.text, color.id, false, false);
                        option.dataset.color = JSON.stringify(color);
                        colorSelect.append(option);
                    });
                }
            }

            // Initialize select2
            colorSelect.select2({
                theme: 'bootstrap-5',
                placeholder: 'Search for a thread color...',
                allowClear: true,
                dropdownParent: $(modal),
                width: '100%'
            });

            // Handle selection
            colorSelect.on('select2:select', function(e) {
                const colorData = JSON.parse(e.params.data.element.dataset.color);
                selectedColor = colorData;

                // Show preview
                previewSwatch.style.backgroundColor = colorData.hex;
                previewName.textContent = colorData.name;
                previewCode.textContent = `${colorData.vendor} ${colorData.code}`;
                previewDiv.style.display = 'block';
                confirmBtn.disabled = false;
            });

            colorSelect.on('select2:unselect', function() {
                selectedColor = null;
                previewDiv.style.display = 'none';
                confirmBtn.disabled = true;
            });
        });

        // Reset on modal close
        modal.addEventListener('hidden.bs.modal', () => {
            colorSelect.val(null).trigger('change');
            selectedColor = null;
            previewDiv.style.display = 'none';
            confirmBtn.disabled = true;
        });

        // Confirm button
        confirmBtn.addEventListener('click', () => {
            if (selectedColor) {
                const color = {
                    id: `c${Date.now()}`,
                    vendor: selectedColor.vendor,
                    code: selectedColor.code,
                    name: selectedColor.name,
                    rgbHex: selectedColor.hex,
                    symbol: String.fromCharCode(65 + this.stateManager.getState().state.palette.length),
                    sortIndex: this.stateManager.getState().state.palette.length
                };

                this.stateManager.addColor(color);
                bootstrap.Modal.getInstance(modal).hide();
            }
        });
    }

    addColor() {
        // Show the color selection modal
        const modal = new bootstrap.Modal(document.getElementById('addColorModal'));
        modal.show();
    }

    /**
     * Show replace color modal
     */
    showReplaceColorModal() {
        const state = this.stateManager.getState();
        const palette = state.state.palette;

        if (palette.length < 2) {
            alert('You need at least 2 colors in your palette to replace colors.');
            return;
        }

        const modal = document.getElementById('replaceColorModal');
        const colorFromSelect = document.getElementById('colorFrom');
        const colorToSelect = document.getElementById('colorTo');
        const confirmBtn = document.getElementById('confirmReplaceColor');

        // Populate dropdowns
        colorFromSelect.innerHTML = '<option value="">Select color to replace...</option>';
        colorToSelect.innerHTML = '<option value="">Select replacement color...</option>';

        palette.forEach((color, index) => {
            const optionFrom = document.createElement('option');
            optionFrom.value = index;
            optionFrom.textContent = `${color.name} ${color.vendor ? `(${color.vendor} ${color.code})` : ''}`;
            optionFrom.style.backgroundColor = color.rgbHex;
            optionFrom.style.color = this.getContrastColor(color.rgbHex);
            colorFromSelect.appendChild(optionFrom);

            const optionTo = document.createElement('option');
            optionTo.value = index;
            optionTo.textContent = `${color.name} ${color.vendor ? `(${color.vendor} ${color.code})` : ''}`;
            optionTo.style.backgroundColor = color.rgbHex;
            optionTo.style.color = this.getContrastColor(color.rgbHex);
            colorToSelect.appendChild(optionTo);
        });

        // Enable/disable confirm button
        const updateConfirmBtn = () => {
            const fromIndex = colorFromSelect.value;
            const toIndex = colorToSelect.value;
            confirmBtn.disabled = !fromIndex || !toIndex || fromIndex === toIndex;
        };

        colorFromSelect.addEventListener('change', updateConfirmBtn);
        colorToSelect.addEventListener('change', updateConfirmBtn);

        // Handle confirm
        confirmBtn.onclick = () => {
            const fromIndex = parseInt(colorFromSelect.value);
            const toIndex = parseInt(colorToSelect.value);
            this.replaceColor(fromIndex, toIndex);
            bootstrap.Modal.getInstance(modal).hide();
        };

        // Show modal
        new bootstrap.Modal(modal).show();
    }

    /**
     * Show delete color modal
     */
    showDeleteColorModal() {
        const state = this.stateManager.getState();
        const palette = state.state.palette;

        if (palette.length === 0) {
            alert('No colors in palette to delete.');
            return;
        }

        const modal = document.getElementById('deleteColorModal');
        const colorSelect = document.getElementById('colorToDelete');
        const confirmBtn = document.getElementById('confirmDeleteColor');

        // Populate dropdown
        colorSelect.innerHTML = '<option value="">Select a color...</option>';

        palette.forEach((color, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = `${color.name} ${color.vendor ? `(${color.vendor} ${color.code})` : ''}`;
            option.style.backgroundColor = color.rgbHex;
            option.style.color = this.getContrastColor(color.rgbHex);
            colorSelect.appendChild(option);
        });

        // Enable/disable confirm button
        colorSelect.addEventListener('change', () => {
            confirmBtn.disabled = !colorSelect.value;
        });

        // Handle confirm
        confirmBtn.onclick = () => {
            const colorIndex = parseInt(colorSelect.value);
            if (confirm(`Are you sure you want to delete this color? All stitches using this color will be removed!`)) {
                this.deleteColor(colorIndex);
                bootstrap.Modal.getInstance(modal).hide();
            }
        };

        // Show modal
        new bootstrap.Modal(modal).show();
    }

    /**
     * Replace all stitches using one color with another color
     */
    replaceColor(fromIndex, toIndex) {
        // Save undo snapshot
        this.stateManager.undoStack.push(JSON.parse(JSON.stringify(this.stateManager.state)));
        if (this.stateManager.undoStack.length > this.stateManager.maxUndoSteps) {
            this.stateManager.undoStack.shift();
        }
        this.stateManager.redoStack = [];

        const state = this.stateManager.getState();
        let cellsModified = 0;

        // Go through all layers
        state.state.layers.forEach(layer => {
            if (layer.type === 'raster' && layer.editable) {
                // Go through all cells in this layer
                for (const key in layer.cells) {
                    const cell = layer.cells[key];
                    if (cell && cell.paletteIndex === fromIndex) {
                        cell.paletteIndex = toIndex;
                        cellsModified++;
                    }
                }
            }
        });

        // Remove the "from" color from palette
        state.state.palette.splice(fromIndex, 1);

        // Update all palette indices greater than fromIndex
        state.state.layers.forEach(layer => {
            if (layer.type === 'raster') {
                for (const key in layer.cells) {
                    const cell = layer.cells[key];
                    if (cell && cell.paletteIndex > fromIndex) {
                        cell.paletteIndex--;
                    } else if (cell && cell.paletteIndex === toIndex && toIndex > fromIndex) {
                        // The toIndex has shifted down
                        cell.paletteIndex--;
                    }
                }
            }
        });

        // Trigger state update and notify listeners
        this.stateManager.isDirty = true;
        this.stateManager.notify();

        alert(`Replaced ${cellsModified} stitches and removed the original color from palette.`);
    }

    /**
     * Delete a color and all stitches using it
     */
    deleteColor(colorIndex) {
        // Save undo snapshot
        this.stateManager.undoStack.push(JSON.parse(JSON.stringify(this.stateManager.state)));
        if (this.stateManager.undoStack.length > this.stateManager.maxUndoSteps) {
            this.stateManager.undoStack.shift();
        }
        this.stateManager.redoStack = [];

        const state = this.stateManager.getState();
        let cellsDeleted = 0;

        // Go through all layers and delete cells using this color
        state.state.layers.forEach(layer => {
            if (layer.type === 'raster' && layer.editable) {
                for (const key in layer.cells) {
                    const cell = layer.cells[key];
                    if (cell && cell.paletteIndex === colorIndex) {
                        delete layer.cells[key];
                        cellsDeleted++;
                    }
                }
            }
        });

        // Remove the color from palette
        state.state.palette.splice(colorIndex, 1);

        // Update all palette indices greater than colorIndex
        state.state.layers.forEach(layer => {
            if (layer.type === 'raster') {
                for (const key in layer.cells) {
                    const cell = layer.cells[key];
                    if (cell && cell.paletteIndex > colorIndex) {
                        cell.paletteIndex--;
                    }
                }
            }
        });

        // Trigger state update and notify listeners
        this.stateManager.isDirty = true;
        this.stateManager.notify();

        alert(`Deleted ${cellsDeleted} stitches and removed the color from palette.`);
    }

    /**
     * Get contrasting color (black or white) for text on colored background
     */
    getContrastColor(hexColor) {
        // Convert hex to RGB
        const hex = hexColor.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);

        // Calculate luminance
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

        // Return black or white based on luminance
        return luminance > 0.5 ? '#000000' : '#ffffff';
    }

    /**
     * Add a new layer
     */
    addLayer() {
        const name = prompt('Layer name:', 'New Stitches Layer');
        if (!name) return;

        const layerId = this.stateManager.addLayer('raster');

        // Update the layer name
        this.stateManager.updateLayer(layerId, { name: name });

        this.updateLayersUI();
        this.render();
    }

    /**
     * Save to IndexedDB (async, runs in background)
     */
    async saveToLocalStorage() {
        try {
            await this.storage.save(
                this.stateManager.getState(),
                this.stateManager.undoStack,
                this.stateManager.redoStack
            );
        } catch (error) {
            console.error('Failed to save to IndexedDB:', error);
        }
    }

    /**
     * Save to backend
     */
    async saveToBackend() {
        const saveBtn = document.getElementById('saveBtn');
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';

        const result = await this.api.saveProject(this.stateManager.getState());

        if (result.success) {
            this.stateManager.markSaved();
            saveBtn.textContent = 'Saved!';
            setTimeout(() => {
                saveBtn.textContent = 'Save';
                saveBtn.disabled = false;
            }, 2000);
        } else {
            alert('Failed to save: ' + result.error);
            saveBtn.textContent = 'Save';
            saveBtn.disabled = false;
        }
    }

    /**
     * Setup auto-save
     */
    setupAutoSave() {
        setInterval(() => {
            if (this.stateManager.hasUnsavedChanges()) {
                this.saveToBackend();
            }
        }, this.autoSaveInterval);
    }
}

// Initialize editor when DOM is ready
if (window.PROJECT_DATA) {
    const editor = new Editor(window.PROJECT_DATA);
    window.editor = editor; // For debugging
}
