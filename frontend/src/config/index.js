// src/config/index.js
export const config = {
    api: {
        baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
        timeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 10000
    }
};