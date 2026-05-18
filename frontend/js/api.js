const API_BASE = 'http://localhost:5000/api';

const api = {
    async request(endpoint, options = {}) {
        try {
            const res = await fetch(`${API_BASE}${endpoint}`, options);
            const data = await res.json();
            return { ok: res.ok, status: res.status, data: data.data, message: data.message };
        } catch (error) {
            console.error('API Error:', error);
            return { ok: false, status: 500, message: 'Network error or server down.' };
        }
    },

    async checkHealth() {
        return this.request('/health');
    },

    // Voice
    async processVoice(text) {
        return this.request('/voice/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
    },
    async getVoiceCommands() {
        return this.request('/voice/commands');
    },
    async getVoiceHistory(limit = 10) {
        return this.request(`/voice/history?limit=${limit}`);
    },

    // Media
    async uploadMedia(formData) {
        return this.request('/media/upload', {
            method: 'POST',
            body: formData
        });
    },
    async getMediaList(filters = {}) {
        const params = new URLSearchParams();
        if (filters.search) params.append('search', filters.search);
        if (filters.type) params.append('type', filters.type);
        if (filters.category) params.append('category', filters.category);
        return this.request(`/media/list?${params.toString()}`);
    },
    async getMediaDetail(id) {
        return this.request(`/media/${id}`);
    },
    async deleteMedia(id) {
        return this.request(`/media/${id}`, { method: 'DELETE' });
    },

    // Scheduler
    async getTasks() {
        return this.request('/schedule/tasks');
    },
    async addTask(taskData) {
        return this.request('/schedule/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
    },

    // Analytics
    async getSummary() { return this.request('/analytics/summary'); },
    async getMediaType() { return this.request('/analytics/media-by-type'); },
    async getMediaCategory() { return this.request('/analytics/media-by-category'); },
    async getUploads(days = 30) { return this.request(`/analytics/uploads-over-time?days=${days}`); },
    async getViewsDownloads() { return this.request('/analytics/views-vs-downloads'); },
    async getVoiceStats() { return this.request('/analytics/voice-stats'); },
    async getActivity(days = 30) { return this.request(`/analytics/activity?days=${days}`); },
    async getTopMedia() { return this.request('/analytics/top-media'); },
    async getStorage() { return this.request('/analytics/storage'); }
};
