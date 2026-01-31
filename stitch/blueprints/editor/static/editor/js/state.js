/**
 * State Management Module
 * Handles application state, undo/redo, and state change notifications
 */

export class StateManager {
    constructor(initialState) {
        this.state = initialState;
        this.undoStack = [];
        this.redoStack = [];
        this.maxUndoSteps = 50;
        this.listeners = [];
        this.isDirty = false;
    }

    /**
     * Get current state
     */
    getState() {
        return this.state;
    }

    /**
     * Subscribe to state changes
     */
    subscribe(callback) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter(cb => cb !== callback);
        };
    }

    /**
     * Notify all listeners of state change
     */
    notify() {
        this.listeners.forEach(callback => callback(this.state));
    }

    /**
     * Update state (creates undo snapshot)
     */
    updateState(updates, createUndoSnapshot = true) {
        if (createUndoSnapshot) {
            // Save current state to undo stack
            this.undoStack.push(JSON.parse(JSON.stringify(this.state)));

            // Limit undo stack size
            if (this.undoStack.length > this.maxUndoSteps) {
                this.undoStack.shift();
            }

            // Clear redo stack on new action
            this.redoStack = [];
        }

        // Apply updates
        if (typeof updates === 'function') {
            this.state = updates(this.state);
        } else {
            this.state = { ...this.state, ...updates };
        }

        this.isDirty = true;
        this.notify();
    }

    /**
     * Undo last action
     */
    undo() {
        if (this.undoStack.length === 0) return false;

        // Save current state to redo stack
        this.redoStack.push(JSON.parse(JSON.stringify(this.state)));

        // Restore previous state
        this.state = this.undoStack.pop();

        this.isDirty = true;
        this.notify();
        return true;
    }

    /**
     * Redo last undone action
     */
    redo() {
        if (this.redoStack.length === 0) return false;

        // Save current state to undo stack
        this.undoStack.push(JSON.parse(JSON.stringify(this.state)));

        // Restore next state
        this.state = this.redoStack.pop();

        this.isDirty = true;
        this.notify();
        return true;
    }

    /**
     * Update a single cell in a layer
     */
    updateCell(layerId, x, y, cellData) {
        const layer = this.state.state.layers.find(l => l.id === layerId);
        if (!layer || layer.type !== 'raster') return;

        const key = `${y * this.state.width + x}`;

        this.updateState(state => {
            const newState = JSON.parse(JSON.stringify(state));
            const targetLayer = newState.state.layers.find(l => l.id === layerId);

            if (cellData === null) {
                delete targetLayer.cells[key];
            } else {
                targetLayer.cells[key] = cellData;
            }

            return newState;
        });
    }

    /**
     * Get cell data at position
     */
    getCell(layerId, x, y) {
        const layer = this.state.state.layers.find(l => l.id === layerId);
        if (!layer || layer.type !== 'raster') return null;

        const key = `${y * this.state.width + x}`;
        return layer.cells[key] || null;
    }

    /**
     * Update palette
     */
    updatePalette(newPalette) {
        this.updateState(state => {
            const newState = JSON.parse(JSON.stringify(state));
            newState.state.palette = newPalette;
            return newState;
        });
    }

    /**
     * Add color to palette
     */
    addColor(color) {
        this.updateState(state => {
            const newState = JSON.parse(JSON.stringify(state));
            newState.state.palette.push(color);
            return newState;
        });
    }

    /**
     * Update layer properties
     */
    updateLayer(layerId, updates) {
        this.updateState(state => {
            const newState = JSON.parse(JSON.stringify(state));
            const layer = newState.state.layers.find(l => l.id === layerId);
            if (layer) {
                Object.assign(layer, updates);
            }
            return newState;
        });
    }

    /**
     * Set active layer
     */
    setActiveLayer(layerId) {
        this.updateState({
            state: {
                ...this.state.state,
                activeLayerId: layerId
            }
        }, false); // Don't create undo snapshot for layer switching
    }

    /**
     * Add new layer
     */
    addLayer(layerType = 'raster') {
        const layerId = `layer_${Date.now()}`;
        const layerCount = this.state.state.layers.filter(l => l.type === layerType).length;

        const newLayer = {
            id: layerId,
            type: layerType,
            name: `${layerType === 'raster' ? 'Stitches' : 'Layer'} ${layerCount + 1}`,
            visible: true,
            activeForExport: true,
            editable: true,
            cells: {}
        };

        this.updateState(state => {
            const newState = JSON.parse(JSON.stringify(state));
            newState.state.layers.push(newLayer);
            newState.state.activeLayerId = layerId;
            return newState;
        });

        return layerId;
    }

    /**
     * Delete layer
     */
    deleteLayer(layerId) {
        this.updateState(state => {
            const newState = JSON.parse(JSON.stringify(state));
            const layerIndex = newState.state.layers.findIndex(l => l.id === layerId);

            if (layerIndex === -1) return state;

            // Don't allow deleting the last layer
            if (newState.state.layers.length === 1) {
                alert('Cannot delete the last layer');
                return state;
            }

            // Remove layer
            newState.state.layers.splice(layerIndex, 1);

            // Update active layer if needed
            if (newState.state.activeLayerId === layerId) {
                newState.state.activeLayerId = newState.state.layers[0].id;
            }

            return newState;
        });
    }

    /**
     * Toggle layer visibility
     */
    toggleLayerVisibility(layerId) {
        this.updateState(state => {
            const newState = JSON.parse(JSON.stringify(state));
            const layer = newState.state.layers.find(l => l.id === layerId);
            if (layer) {
                layer.visible = !layer.visible;
            }
            return newState;
        }, false); // Don't create undo snapshot for visibility toggle
    }

    /**
     * Mark as saved
     */
    markSaved() {
        this.isDirty = false;
    }

    /**
     * Check if state has unsaved changes
     */
    hasUnsavedChanges() {
        return this.isDirty;
    }

    /**
     * Can undo?
     */
    canUndo() {
        return this.undoStack.length > 0;
    }

    /**
     * Can redo?
     */
    canRedo() {
        return this.redoStack.length > 0;
    }
}
