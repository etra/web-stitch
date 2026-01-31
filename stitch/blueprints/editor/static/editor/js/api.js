/**
 * API Module
 * Handles communication with backend
 */

export class API {
    constructor(projectId) {
        this.projectId = projectId;
        this.baseUrl = `/editor/${projectId}/api`;
    }

    /**
     * Save project state to backend
     */
    async saveProject(state) {
        try {
            const response = await fetch(`${this.baseUrl}/state`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    state: state.state
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return { success: true, data };
        } catch (error) {
            console.error('Failed to save project:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Load project state from backend
     */
    async loadProject() {
        try {
            const response = await fetch(`${this.baseUrl}/state`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return { success: true, data };
        } catch (error) {
            console.error('Failed to load project:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Get project thumbnail
     */
    async getThumbnail() {
        return `${this.baseUrl}/thumbnail`;
    }

    /**
     * Get available thread colors from all palettes
     */
    async getAvailableColors() {
        try {
            const response = await fetch('/api/colors');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return { success: true, colors: data.colors };
        } catch (error) {
            console.error('Failed to load colors:', error);
            return { success: false, error: error.message };
        }
    }
}
