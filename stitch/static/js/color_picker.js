/**
 * Color Picker Component
 * Advanced color selection functionality for wizard
 */

(function() {
    'use strict';

    class ColorPickerModal {
        constructor(options = {}) {
            this.vendors = options.vendors || ['dmc', 'hama', 'artkal', 'nabbi'];
            this.onSelect = options.onSelect || null;
            this.currentVendor = 'dmc';
            this.modalEl = null;
        }

        /**
         * Show color picker modal
         */
        show() {
            this.createModal();
            this.loadVendorColors(this.currentVendor);
            this.modalEl.classList.add('show');
            this.modalEl.style.display = 'block';
            document.body.classList.add('modal-open');
        }

        /**
         * Hide modal
         */
        hide() {
            if (this.modalEl) {
                this.modalEl.classList.remove('show');
                this.modalEl.style.display = 'none';
                document.body.classList.remove('modal-open');
            }
        }

        /**
         * Create modal HTML
         */
        createModal() {
            if (this.modalEl) {
                return;
            }

            const modalHTML = `
                <div class="modal fade" id="colorPickerModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Select Color</h5>
                                <button type="button" class="btn-close" data-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="mb-3">
                                    <label class="form-label">Thread Vendor</label>
                                    <div class="btn-group w-100" role="group">
                                        ${this.vendors.map(v => `
                                            <button type="button" class="btn btn-outline-primary vendor-select-btn"
                                                    data-vendor="${v}">
                                                ${v.toUpperCase()}
                                            </button>
                                        `).join('')}
                                    </div>
                                </div>

                                <div class="mb-3">
                                    <input type="text" class="form-control" id="modal-color-search"
                                           placeholder="Search by code or name...">
                                </div>

                                <div id="color-picker-results" class="color-picker-grid">
                                    <div class="text-center py-4">
                                        <span class="loading-spinner"></span> Loading colors...
                                    </div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', modalHTML);
            this.modalEl = document.getElementById('colorPickerModal');

            this.initEventListeners();
        }

        /**
         * Initialize event listeners
         */
        initEventListeners() {
            // Vendor selection buttons
            this.modalEl.querySelectorAll('.vendor-select-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    this.currentVendor = e.target.dataset.vendor;
                    this.modalEl.querySelectorAll('.vendor-select-btn').forEach(b => {
                        b.classList.remove('active');
                    });
                    e.target.classList.add('active');
                    this.loadVendorColors(this.currentVendor);
                });
            });

            // Close buttons
            this.modalEl.querySelectorAll('[data-dismiss="modal"]').forEach(btn => {
                btn.addEventListener('click', () => this.hide());
            });

            // Search
            const searchInput = this.modalEl.querySelector('#modal-color-search');
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    this.filterColors(e.target.value);
                });
            }

            // Click outside to close
            this.modalEl.addEventListener('click', (e) => {
                if (e.target === this.modalEl) {
                    this.hide();
                }
            });
        }

        /**
         * Load colors for selected vendor
         */
        async loadVendorColors(vendor) {
            const resultsEl = this.modalEl.querySelector('#color-picker-results');
            resultsEl.innerHTML = '<div class="text-center py-4"><span class="loading-spinner"></span> Loading colors...</div>';

            try {
                // In a real implementation, this would fetch from an API
                // For now, we'll use a placeholder
                const colors = await this.fetchVendorColors(vendor);
                this.renderColors(colors);
            } catch (error) {
                resultsEl.innerHTML = '<div class="alert alert-danger">Failed to load colors</div>';
            }
        }

        /**
         * Fetch vendor colors (placeholder - would be API call in production)
         */
        async fetchVendorColors(vendor) {
            // This would be an actual API call to get colors
            // For now, return empty array as placeholder
            return [];
        }

        /**
         * Render color list
         */
        renderColors(colors) {
            const resultsEl = this.modalEl.querySelector('#color-picker-results');

            if (colors.length === 0) {
                resultsEl.innerHTML = '<div class="text-center text-muted py-4">No colors available</div>';
                return;
            }

            const colorHTML = colors.map(color => `
                <div class="color-picker-item" data-color-code="${color.code}">
                    <div class="color-swatch-visual" style="background-color: ${color.hex};"></div>
                    <div class="color-swatch-info">
                        <div class="color-swatch-code">${color.code}</div>
                        <div class="color-swatch-name">${color.name}</div>
                    </div>
                    <button type="button" class="btn btn-sm btn-primary select-color-btn"
                            data-color='${JSON.stringify(color)}'>
                        Select
                    </button>
                </div>
            `).join('');

            resultsEl.innerHTML = colorHTML;

            // Add click handlers for select buttons
            resultsEl.querySelectorAll('.select-color-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const colorData = JSON.parse(e.target.dataset.color);
                    if (this.onSelect) {
                        this.onSelect(colorData);
                    }
                    this.hide();
                });
            });
        }

        /**
         * Filter colors by search query
         */
        filterColors(query) {
            const items = this.modalEl.querySelectorAll('.color-picker-item');
            const queryLower = query.toLowerCase();

            items.forEach(item => {
                const code = item.dataset.colorCode?.toLowerCase() || '';
                const name = item.querySelector('.color-swatch-name')?.textContent.toLowerCase() || '';

                if (code.includes(queryLower) || name.includes(queryLower)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        }
    }

    // Bulk color selection helpers
    const BulkSelection = {
        selectAll: function() {
            document.querySelectorAll('.color-swatch-checkbox').forEach(cb => {
                cb.checked = true;
                cb.dispatchEvent(new Event('change'));
            });
        },

        deselectAll: function() {
            document.querySelectorAll('.color-swatch-checkbox').forEach(cb => {
                cb.checked = false;
                cb.dispatchEvent(new Event('change'));
            });
        },

        selectByRange: function(startIndex, endIndex) {
            const checkboxes = Array.from(document.querySelectorAll('.color-swatch-checkbox'));
            checkboxes.slice(startIndex, endIndex + 1).forEach(cb => {
                cb.checked = true;
                cb.dispatchEvent(new Event('change'));
            });
        }
    };

    // Color conversion utilities
    const ColorUtils = {
        hexToRgb: function(hex) {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? {
                r: parseInt(result[1], 16),
                g: parseInt(result[2], 16),
                b: parseInt(result[3], 16)
            } : null;
        },

        rgbToHex: function(r, g, b) {
            return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
        },

        getLuminance: function(hex) {
            const rgb = ColorUtils.hexToRgb(hex);
            if (!rgb) return 0;

            // Calculate relative luminance
            const [r, g, b] = [rgb.r, rgb.g, rgb.b].map(val => {
                val /= 255;
                return val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4);
            });

            return 0.2126 * r + 0.7152 * g + 0.0722 * b;
        },

        getContrastColor: function(hex) {
            const luminance = ColorUtils.getLuminance(hex);
            return luminance > 0.5 ? '#000000' : '#ffffff';
        }
    };

    // Export to global scope
    window.ColorPickerModal = ColorPickerModal;
    window.ColorUtils = ColorUtils;
    window.BulkSelection = BulkSelection;

})();
