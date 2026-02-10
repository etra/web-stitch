/**
 * Project Creation Wizard JavaScript
 * Handles navigation, validation, and interactive features
 */

(function() {
    'use strict';

    // Wizard navigation helpers
    const WizardNav = {
        /**
         * Confirm before leaving wizard if data exists
         */
        confirmExit: function() {
            const message = 'Are you sure you want to leave? Your progress will be lost.';
            return confirm(message);
        },

        /**
         * Handle cancel button clicks
         */
        initCancelButtons: function() {
            document.querySelectorAll('[data-wizard-cancel]').forEach(button => {
                button.addEventListener('click', (e) => {
                    if (!WizardNav.confirmExit()) {
                        e.preventDefault();
                    }
                });
            });
        },

        /**
         * Disable form submission if invalid
         */
        validateForm: function(form) {
            if (!form.checkValidity()) {
                form.classList.add('was-validated');
                return false;
            }
            return true;
        }
    };

    // Vendor selection
    const VendorSelection = {
        init: function() {
            const vendorCards = document.querySelectorAll('.vendor-card');

            vendorCards.forEach(card => {
                card.addEventListener('click', function() {
                    // Remove selected from all
                    vendorCards.forEach(c => c.classList.remove('selected'));
                    // Add to clicked
                    this.classList.add('selected');
                    // Check radio
                    const radio = this.querySelector('input[type="radio"]');
                    if (radio) {
                        radio.checked = true;
                    }
                });
            });
        }
    };

    // Color picker with search
    const ColorPicker = {
        selectedCount: 0,

        init: function() {
            const searchInput = document.querySelector('#color-search');
            const colorItems = document.querySelectorAll('.color-picker-item, .color-grid-cell');
            const checkboxes = document.querySelectorAll('.color-swatch-checkbox, .color-grid-checkbox');
            const statsEl = document.querySelector('.color-picker-stats strong');

            // Search functionality
            if (searchInput) {
                searchInput.addEventListener('input', function() {
                    const query = this.value.toLowerCase();

                    colorItems.forEach(item => {
                        const code = item.dataset.colorCode?.toLowerCase() || '';
                        const name = (item.dataset.colorName || item.querySelector('.color-swatch-name')?.textContent || '').toLowerCase();

                        if (code.includes(query) || name.includes(query)) {
                            item.style.display = '';
                        } else {
                            item.style.display = 'none';
                        }
                    });
                });
            }

            // Selection functionality
            if (checkboxes.length > 0) {
                ColorPicker.updateStats();

                checkboxes.forEach(checkbox => {
                    checkbox.addEventListener('change', function() {
                        const item = this.closest('.color-picker-item, .color-grid-cell');
                        if (this.checked) {
                            item.classList.add('selected');
                        } else {
                            item.classList.remove('selected');
                        }
                        ColorPicker.updateStats();
                    });
                });

                // Click anywhere in item to toggle
                colorItems.forEach(item => {
                    item.addEventListener('click', function(e) {
                        if (e.target.tagName !== 'INPUT') {
                            const checkbox = this.querySelector('.color-swatch-checkbox, .color-grid-checkbox');
                            if (checkbox) {
                                checkbox.checked = !checkbox.checked;
                                checkbox.dispatchEvent(new Event('change'));
                            }
                        }
                    });
                });
            }
        },

        updateStats: function() {
            const checkboxes = document.querySelectorAll('.color-swatch-checkbox:checked, .color-grid-checkbox:checked');
            const statsEl = document.querySelector('.color-picker-stats strong');

            if (statsEl) {
                statsEl.textContent = checkboxes.length;
            }
        },

        validateSelection: function() {
            const checkboxes = document.querySelectorAll('.color-swatch-checkbox:checked, .color-grid-checkbox:checked');
            if (checkboxes.length === 0) {
                alert('Please select at least one color.');
                return false;
            }
            return true;
        }
    };

    // Image selection
    const ImageSelection = {
        init: function() {
            const imageItems = document.querySelectorAll('.image-gallery-item');
            const selectedInput = document.querySelector('#selected_image, #selected_background');

            imageItems.forEach(item => {
                item.addEventListener('click', function() {
                    // Remove selected from all
                    imageItems.forEach(i => i.classList.remove('selected'));
                    // Add to clicked
                    this.classList.add('selected');
                    // Set hidden input (works for both selected_image and selected_background)
                    if (selectedInput) {
                        selectedInput.value = this.dataset.filename;
                    }
                });
            });
        }
    };

    // Form validation before submit
    const FormValidation = {
        init: function() {
            const forms = document.querySelectorAll('.wizard-form');

            forms.forEach(form => {
                form.addEventListener('submit', function(e) {
                    // Standard HTML5 validation
                    if (!this.checkValidity()) {
                        e.preventDefault();
                        this.classList.add('was-validated');
                        return false;
                    }

                    // Custom validations (color selection is optional)

                    // Show loading state
                    const submitBtn = this.querySelector('[type="submit"]');
                    if (submitBtn) {
                        submitBtn.disabled = true;
                        submitBtn.innerHTML = '<span class="loading-spinner"></span> Processing...';
                    }

                    return true;
                });
            });
        }
    };

    // Color replacement modal
    const ColorReplacement = {
        init: function() {
            const replaceButtons = document.querySelectorAll('[data-replace-color]');

            replaceButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const colorIndex = this.dataset.replaceColor;
                    ColorReplacement.showModal(colorIndex);
                });
            });
        },

        showModal: function(colorIndex) {
            // This would open a modal with vendor palette selection
            // Implementation depends on your modal system (Bootstrap Modal, etc.)
            console.log('Replace color at index:', colorIndex);
        }
    };

    // Initialize all on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        WizardNav.initCancelButtons();
        VendorSelection.init();
        ColorPicker.init();
        ImageSelection.init();
        FormValidation.init();
        ColorReplacement.init();
    });

    // Expose utilities globally if needed
    window.WizardUtils = {
        ColorPicker: ColorPicker,
        VendorSelection: VendorSelection
    };

})();
