/**
 * Storage Module
 * Handles IndexedDB operations for crash recovery and auto-save
 * Uses IndexedDB instead of localStorage for much larger storage capacity (50MB+)
 */

export class Storage {
    constructor(projectId) {
        this.projectId = projectId;
        this.key = `project_${projectId}`;
        this.dbName = 'WebStitchDB';
        this.storeName = 'projects';
        this.db = null;
    }

    /**
     * Initialize/open the IndexedDB database
     * @returns {Promise<IDBDatabase>}
     */
    async initDB() {
        if (this.db) return this.db;

        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, 1);

            request.onerror = () => {
                console.error('Failed to open IndexedDB:', request.error);
                reject(request.error);
            };

            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            // Create object store if it doesn't exist
            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                if (!db.objectStoreNames.contains(this.storeName)) {
                    db.createObjectStore(this.storeName);
                }
            };
        });
    }

    /**
     * Save state to IndexedDB
     * @param {Object} state - Project state
     * @param {Array} undoStack - Undo history
     * @param {Array} redoStack - Redo history
     * @returns {Promise<boolean>}
     */
    async save(state, undoStack = [], redoStack = []) {
        try {
            const db = await this.initDB();

            const data = {
                state,
                undoStack,
                redoStack,
                timestamp: Date.now()
            };

            return new Promise((resolve, reject) => {
                const transaction = db.transaction([this.storeName], 'readwrite');
                const store = transaction.objectStore(this.storeName);
                const request = store.put(data, this.key);

                request.onsuccess = () => resolve(true);
                request.onerror = () => {
                    console.error('Failed to save to IndexedDB:', request.error);
                    reject(request.error);
                };
            });
        } catch (error) {
            console.error('Failed to save to IndexedDB:', error);
            return false;
        }
    }

    /**
     * Load state from IndexedDB
     * @returns {Promise<Object|null>}
     */
    async load() {
        try {
            const db = await this.initDB();

            return new Promise((resolve, reject) => {
                const transaction = db.transaction([this.storeName], 'readonly');
                const store = transaction.objectStore(this.storeName);
                const request = store.get(this.key);

                request.onsuccess = () => {
                    resolve(request.result || null);
                };

                request.onerror = () => {
                    console.error('Failed to load from IndexedDB:', request.error);
                    reject(request.error);
                };
            });
        } catch (error) {
            console.error('Failed to load from IndexedDB:', error);
            return null;
        }
    }

    /**
     * Clear IndexedDB data for this project
     * @returns {Promise<void>}
     */
    async clear() {
        try {
            const db = await this.initDB();

            return new Promise((resolve, reject) => {
                const transaction = db.transaction([this.storeName], 'readwrite');
                const store = transaction.objectStore(this.storeName);
                const request = store.delete(this.key);

                request.onsuccess = () => resolve();
                request.onerror = () => {
                    console.error('Failed to clear IndexedDB:', request.error);
                    reject(request.error);
                };
            });
        } catch (error) {
            console.error('Failed to clear IndexedDB:', error);
        }
    }

    /**
     * Check if IndexedDB has data for this project
     * @returns {Promise<boolean>}
     */
    async hasData() {
        try {
            const data = await this.load();
            return data !== null;
        } catch (error) {
            console.error('Failed to check IndexedDB data:', error);
            return false;
        }
    }

    /**
     * Get storage usage info (for debugging)
     * @returns {Promise<Object>}
     */
    async getStorageInfo() {
        if (!navigator.storage || !navigator.storage.estimate) {
            return { supported: false };
        }

        try {
            const estimate = await navigator.storage.estimate();
            return {
                supported: true,
                usage: estimate.usage,
                quota: estimate.quota,
                usageInMB: (estimate.usage / (1024 * 1024)).toFixed(2),
                quotaInMB: (estimate.quota / (1024 * 1024)).toFixed(2),
                percentUsed: ((estimate.usage / estimate.quota) * 100).toFixed(2)
            };
        } catch (error) {
            console.error('Failed to get storage info:', error);
            return { supported: false, error };
        }
    }
}
