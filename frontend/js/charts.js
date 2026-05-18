Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Inter', sans-serif";

const chartInstances = {};

function initCharts() {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: { grid: { color: '#475569', drawBorder: false } },
            y: { grid: { color: '#475569', drawBorder: false } }
        }
    };

    // Activity Overview
    const ctxActivity = document.getElementById('chartActivity').getContext('2d');
    chartInstances.activity = new Chart(ctxActivity, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
            ...commonOptions,
            plugins: { legend: { display: true, position: 'top' } },
            interaction: { mode: 'index', intersect: false },
        }
    });

    // Media Types
    const ctxTypes = document.getElementById('chartTypes').getContext('2d');
    chartInstances.types = new Chart(ctxTypes, {
        type: 'doughnut',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'right' } },
            cutout: '70%'
        }
    });

    // Uploads
    const ctxUploads = document.getElementById('chartUploads').getContext('2d');
    chartInstances.uploads = new Chart(ctxUploads, {
        type: 'bar',
        data: { labels: [], datasets: [] },
        options: commonOptions
    });

    // Category
    const ctxCategory = document.getElementById('chartCategory').getContext('2d');
    chartInstances.category = new Chart(ctxCategory, {
        type: 'bar',
        data: { labels: [], datasets: [] },
        options: {
            ...commonOptions,
            indexAxis: 'y'
        }
    });

    // Views vs Downloads
    const ctxVD = document.getElementById('chartViewsDownloads').getContext('2d');
    chartInstances.viewsDownloads = new Chart(ctxVD, {
        type: 'bar',
        data: { labels: [], datasets: [] },
        options: {
            ...commonOptions,
            plugins: { legend: { display: true, position: 'top' } }
        }
    });

    // Storage
    const ctxStorage = document.getElementById('chartStorage').getContext('2d');
    chartInstances.storage = new Chart(ctxStorage, {
        type: 'pie',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'right' } }
        }
    });

    // Voice Intents
    const ctxVoiceIntents = document.getElementById('chartVoiceIntents').getContext('2d');
    chartInstances.voiceIntents = new Chart(ctxVoiceIntents, {
        type: 'polarArea',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'right' } }
        }
    });

    // Voice Langs
    const ctxVoiceLangs = document.getElementById('chartVoiceLangs').getContext('2d');
    chartInstances.voiceLangs = new Chart(ctxVoiceLangs, {
        type: 'doughnut',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'bottom' } },
            cutout: '60%'
        }
    });
}

const colors = {
    primary: '#3b82f6',
    primaryAlpha: 'rgba(59, 130, 246, 0.5)',
    accent: '#8b5cf6',
    accentAlpha: 'rgba(139, 92, 246, 0.5)',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    palette: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899']
};

async function updateDashboardCharts() {
    // Activity
    const actRes = await api.getActivity();
    if (actRes.ok) {
        chartInstances.activity.data = {
            labels: actRes.data.labels,
            datasets: [
                { label: 'Uploads', data: actRes.data.uploads, borderColor: colors.primary, backgroundColor: colors.primaryAlpha, fill: true, tension: 0.4 },
                { label: 'Views', data: actRes.data.views, borderColor: colors.success, backgroundColor: 'rgba(16,185,129,0.1)', fill: true, tension: 0.4 },
                { label: 'Voice Commands', data: actRes.data.voice, borderColor: colors.accent, backgroundColor: 'transparent', borderDash: [5, 5], tension: 0.4 }
            ]
        };
        chartInstances.activity.update();
    }

    // Media Types
    const typeRes = await api.getMediaType();
    if (typeRes.ok) {
        chartInstances.types.data = {
            labels: typeRes.data.labels,
            datasets: [{
                data: typeRes.data.values,
                backgroundColor: colors.palette,
                borderWidth: 0
            }]
        };
        chartInstances.types.update();
    }
}

async function updateAnalyticsCharts() {
    // Uploads
    const upRes = await api.getUploads();
    if (upRes.ok) {
        chartInstances.uploads.data = {
            labels: upRes.data.labels,
            datasets: [{
                label: 'Uploads',
                data: upRes.data.values,
                backgroundColor: colors.primary,
                borderRadius: 4
            }]
        };
        chartInstances.uploads.update();
    }

    // Category
    const catRes = await api.getMediaCategory();
    if (catRes.ok) {
        chartInstances.category.data = {
            labels: catRes.data.labels,
            datasets: [{
                label: 'Files',
                data: catRes.data.values,
                backgroundColor: colors.accent,
                borderRadius: 4
            }]
        };
        chartInstances.category.update();
    }

    // Views vs Downloads
    const vdRes = await api.getViewsDownloads();
    if (vdRes.ok) {
        chartInstances.viewsDownloads.data = {
            labels: vdRes.data.labels,
            datasets: [
                { label: 'Views', data: vdRes.data.views, backgroundColor: colors.primary, borderRadius: 4 },
                { label: 'Downloads', data: vdRes.data.downloads, backgroundColor: colors.success, borderRadius: 4 }
            ]
        };
        chartInstances.viewsDownloads.update();
    }

    // Storage
    const stRes = await api.getStorage();
    if (stRes.ok) {
        chartInstances.storage.data = {
            labels: stRes.data.labels,
            datasets: [{
                data: stRes.data.values,
                backgroundColor: colors.palette,
                borderWidth: 0
            }]
        };
        chartInstances.storage.update();
    }

    // Voice Stats
    const vsRes = await api.getVoiceStats();
    if (vsRes.ok) {
        const d = vsRes.data;
        
        chartInstances.voiceIntents.data = {
            labels: d.intents.labels,
            datasets: [{
                data: d.intents.values,
                backgroundColor: colors.palette.map(c => c + '80'), // Add transparency
                borderColor: colors.palette,
                borderWidth: 1
            }]
        };
        chartInstances.voiceIntents.update();

        chartInstances.voiceLangs.data = {
            labels: d.languages.labels,
            datasets: [{
                data: d.languages.values,
                backgroundColor: colors.palette,
                borderWidth: 0
            }]
        };
        chartInstances.voiceLangs.update();

        // Update metrics strip
        document.getElementById('vm-accuracy').textContent = d.avg_confidence + '%';
        document.getElementById('vm-total').textContent = d.total_commands;
        document.getElementById('vm-success').textContent = d.success_rate + '%';
    }
}
