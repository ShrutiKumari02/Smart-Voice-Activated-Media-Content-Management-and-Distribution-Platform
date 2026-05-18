document.addEventListener('DOMContentLoaded', async () => {
    // Check server
    checkServerStatus();
    
    // Init Modules
    initNavigation();
    initCharts();
    initVoice();
    
    // Initial data load
    loadDashboardData();
    loadVoiceCommandsRef();
    loadVoiceHistory();
    
    // Bind global events
    bindEvents();
});

// ──────────────── Navigation ────────────────
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');
    const title = document.getElementById('pageTitle');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPage = item.getAttribute('data-page');
            navigateTo(targetPage);
            
            // Close mobile sidebar
            if (window.innerWidth <= 768) {
                document.getElementById('sidebar').classList.remove('open');
            }
        });
    });

    document.getElementById('sidebarToggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('open');
    });
}

function navigateTo(pageId) {
    // Update Nav
    document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
    const activeNav = document.getElementById(`nav-${pageId}`);
    if (activeNav) activeNav.classList.add('active');

    // Update Page
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    const targetEl = document.getElementById(`page-${pageId}`);
    if (targetEl) targetEl.classList.add('active');

    // Update Title
    const titles = {
        'dashboard': 'Dashboard',
        'media': 'Media Library',
        'upload': 'Upload Media',
        'schedule': 'Task Scheduler',
        'analytics': 'Analytics',
        'voice': 'Voice AI'
    };
    document.getElementById('pageTitle').textContent = titles[pageId] || 'VoiceMedia AI';

    // Lazy load page data
    if (pageId === 'dashboard') loadDashboardData();
    if (pageId === 'media') loadMediaList();
    if (pageId === 'schedule') loadTasks();
    if (pageId === 'analytics') updateAnalyticsCharts();
    
    // Scroll top
    targetEl.scrollTop = 0;
}

// ──────────────── Server Status ────────────────
async function checkServerStatus() {
    const statusEl = document.getElementById('serverStatus');
    const statusText = statusEl.querySelector('.status-text');
    
    const res = await api.checkHealth();
    if (res.ok) {
        statusEl.classList.add('connected');
        statusEl.classList.remove('error');
        statusText.textContent = 'Server Connected';
    } else {
        statusEl.classList.add('error');
        statusEl.classList.remove('connected');
        statusText.textContent = 'Server Disconnected';
        showToast('Backend server is unreachable.', 'error');
    }
}

// ──────────────── Dashboard ────────────────
async function loadDashboardData() {
    const res = await api.getSummary();
    if (res.ok) {
        const d = res.data;
        document.getElementById('kv-files').textContent = d.total_files;
        document.getElementById('kb-files').textContent = `+${d.new_files_30d} this month`;
        
        document.getElementById('kv-views').textContent = d.total_views.toLocaleString();
        document.getElementById('kv-downloads').textContent = d.total_downloads.toLocaleString();
        document.getElementById('kv-voice').textContent = d.voice_commands.toLocaleString();
        document.getElementById('kv-storage').textContent = d.total_size_mb;
        document.getElementById('kv-tasks').textContent = d.pending_tasks;
    }
    
    updateDashboardCharts();
    loadTopMedia();
}

async function loadTopMedia() {
    const res = await api.getTopMedia();
    if (res.ok) {
        const tbody = document.getElementById('topMediaBody');
        tbody.innerHTML = '';
        
        if (res.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7">No media found.</td></tr>';
            return;
        }

        res.data.forEach((m, idx) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${idx + 1}</td>
                <td style="font-weight:500">${m.name}</td>
                <td><span style="text-transform:uppercase; font-size:0.8rem; background:rgba(255,255,255,0.1); padding:0.2rem 0.5rem; border-radius:4px">${m.type}</span></td>
                <td>${m.category}</td>
                <td>${m.views.toLocaleString()}</td>
                <td>${m.downloads.toLocaleString()}</td>
                <td>${m.uploaded_at}</td>
            `;
            tbody.appendChild(tr);
        });
    }
}

// ──────────────── Media Library ────────────────
async function loadMediaList() {
    const grid = document.getElementById('mediaGrid');
    grid.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading media…</p></div>';

    const filters = {
        search: document.getElementById('mediaSearch').value,
        type: document.getElementById('filterType').value,
        category: document.getElementById('filterCategory').value
    };

    const res = await api.getMediaList(filters);
    if (res.ok) {
        grid.innerHTML = '';
        if (res.data.length === 0) {
            grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 2rem; color: var(--text-muted)">No media files found matching criteria.</div>';
            return;
        }

        res.data.forEach(m => {
            const card = document.createElement('div');
            card.className = 'media-card';
            card.onclick = () => openMediaModal(m);
            
            // Emoji icons based on type
            const icons = { video: '🎬', audio: '🎵', image: '🖼️', document: '📄' };
            const icon = icons[m.type] || '📁';
            
            card.innerHTML = `
                <div class="mc-preview">${icon}</div>
                <div class="mc-info">
                    <div class="mc-title" title="${m.name}">${m.name}</div>
                    <div class="mc-meta">
                        <span>${m.category}</span>
                        <span>${(m.size_kb/1024).toFixed(1)} MB</span>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
    }
}

function openMediaModal(media) {
    document.getElementById('modalTitle').textContent = media.name;
    const body = document.getElementById('modalBody');
    body.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:0.5rem">
            <div><strong>Type:</strong> ${media.type.toUpperCase()}</div>
            <div><strong>Category:</strong> ${media.category}</div>
            <div><strong>Size:</strong> ${(media.size_kb/1024).toFixed(2)} MB</div>
            <div><strong>Uploaded:</strong> ${media.uploaded_at}</div>
            <div><strong>Views:</strong> ${media.views}</div>
            <div><strong>Downloads:</strong> ${media.downloads}</div>
            <div><strong>Status:</strong> <span style="color:${media.status==='active'?'var(--success)':'var(--warning)'}">${media.status}</span></div>
            ${media.description ? `<div><strong>Description:</strong> ${media.description}</div>` : ''}
            ${media.tags ? `<div><strong>Tags:</strong> ${media.tags}</div>` : ''}
        </div>
        <div style="margin-top:1.5rem">
            <a href="http://localhost:5000/api/media/file/${media.id}" target="_blank" class="btn-primary" style="text-decoration:none; display:inline-block">Download/View Raw</a>
        </div>
    `;
    
    document.getElementById('modalDeleteBtn').onclick = async () => {
        if(confirm('Are you sure you want to delete this file?')) {
            const res = await api.deleteMedia(media.id);
            if(res.ok) {
                showToast('File deleted successfully', 'success');
                closeMediaModal();
                loadMediaList();
                loadDashboardData();
            } else {
                showToast(res.message, 'error');
            }
        }
    };
    
    document.getElementById('mediaModal').style.display = 'flex';
}

function closeMediaModal() {
    document.getElementById('mediaModal').style.display = 'none';
}

// ──────────────── Upload ────────────────
let selectedFiles = [];

function handleFileSelect(e) {
    const files = e.target.files || e.dataTransfer.files;
    if(files.length > 0) {
        selectedFiles = Array.from(files);
        updateUploadQueue();
        document.getElementById('uploadBtn').disabled = false;
    }
}

function updateUploadQueue() {
    const queue = document.getElementById('uploadQueue');
    const list = document.getElementById('uploadQueueList');
    
    if(selectedFiles.length === 0) {
        queue.style.display = 'none';
        return;
    }
    
    queue.style.display = 'block';
    list.innerHTML = '';
    
    selectedFiles.forEach((file, index) => {
        const li = document.createElement('li');
        li.style.display = 'flex';
        li.style.justifyContent = 'space-between';
        li.style.padding = '0.5rem 0';
        li.style.borderBottom = '1px solid var(--border)';
        
        li.innerHTML = `
            <span>${file.name} ( ${(file.size/1024/1024).toFixed(2)} MB )</span>
            <button class="btn-ghost" style="padding:0.2rem 0.5rem" onclick="removeSelectedFile(${index})">✕</button>
        `;
        list.appendChild(li);
    });
}

window.removeSelectedFile = function(index) {
    selectedFiles.splice(index, 1);
    updateUploadQueue();
    if(selectedFiles.length === 0) {
        document.getElementById('uploadBtn').disabled = true;
    }
}

async function doUpload() {
    if(selectedFiles.length === 0) return;
    
    const btn = document.getElementById('uploadBtn');
    const progWrap = document.getElementById('uploadProgressWrap');
    const progBar = document.getElementById('uploadProgressBar');
    const resDiv = document.getElementById('uploadResult');
    
    const category = document.getElementById('uploadCategory').value;
    const tags = document.getElementById('uploadTags').value;
    const desc = document.getElementById('uploadDesc').value;
    
    btn.disabled = true;
    progWrap.style.display = 'block';
    progBar.style.width = '10%';
    resDiv.innerHTML = '';
    
    let successCount = 0;
    
    for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', category);
        formData.append('tags', tags);
        formData.append('description', desc);
        
        const res = await api.uploadMedia(formData);
        if (res.ok) {
            successCount++;
        } else {
            showToast(`Failed to upload ${file.name}: ${res.message}`, 'error');
        }
        
        progBar.style.width = `${((i+1)/selectedFiles.length)*100}%`;
    }
    
    setTimeout(() => {
        progWrap.style.display = 'none';
        progBar.style.width = '0%';
        if (successCount > 0) {
            resDiv.innerHTML = `<span style="color:var(--success)">Successfully uploaded ${successCount} files!</span>`;
            showToast(`Uploaded ${successCount} files`, 'success');
            selectedFiles = [];
            updateUploadQueue();
            
            // Clear form
            document.getElementById('uploadTags').value = '';
            document.getElementById('uploadDesc').value = '';
            
            // refresh data
            loadDashboardData();
        } else {
            btn.disabled = false;
        }
    }, 500);
}

// ──────────────── Scheduler ────────────────
async function loadTasks() {
    const list = document.getElementById('tasksList');
    list.innerHTML = '<div class="loading-spinner"><div class="spinner"></div></div>';
    
    const res = await api.getTasks();
    if (res.ok) {
        list.innerHTML = '';
        if(res.data.length === 0) {
            list.innerHTML = '<div style="padding:1rem; color:var(--text-muted)">No scheduled tasks found.</div>';
            return;
        }
        
        res.data.forEach(t => {
            const item = document.createElement('div');
            item.className = 'task-item';
            
            const actionColors = { publish: '#10b981', archive: '#f59e0b', notify: '#3b82f6', delete: '#ef4444' };
            const aColor = actionColors[t.action] || '#fff';
            
            item.innerHTML = `
                <div class="ti-main">
                    <div class="ti-title">${t.task_name}</div>
                    <div class="ti-meta">
                        <span style="color:${aColor}; text-transform:uppercase; font-size:0.75rem; font-weight:600">${t.action}</span>
                        <span>Date: ${t.scheduled_time}</span>
                        <span>Media ID: ${t.media_id || 'N/A'}</span>
                    </div>
                </div>
                <div>
                    <span class="ti-badge ${t.status}">${t.status.toUpperCase()}</span>
                </div>
            `;
            list.appendChild(item);
        });
    }
}

async function doSchedule() {
    const name = document.getElementById('sTaskName').value;
    const mediaId = document.getElementById('sMediaId').value;
    const action = document.getElementById('sAction').value;
    const dt = document.getElementById('sDateTime').value;
    const notes = document.getElementById('sNotes').value;
    
    if(!name || !dt) {
        showToast('Task name and scheduled time are required', 'error');
        return;
    }
    
    const payload = {
        task_name: name,
        action: action,
        scheduled_time: dt,
        notes: notes
    };
    if(mediaId) payload.media_id = parseInt(mediaId);
    
    const btn = document.getElementById('addTaskBtn');
    btn.disabled = true;
    
    const res = await api.addTask(payload);
    btn.disabled = false;
    
    if (res.ok) {
        showToast('Task scheduled successfully', 'success');
        // reset form
        document.getElementById('sTaskName').value = '';
        document.getElementById('sMediaId').value = '';
        document.getElementById('sDateTime').value = '';
        document.getElementById('sNotes').value = '';
        
        loadTasks();
    } else {
        showToast(res.message, 'error');
    }
}

// ──────────────── Utils & Events ────────────────
function bindEvents() {
    // Media Library
    document.getElementById('mediaSearchBtn').addEventListener('click', loadMediaList);
    document.getElementById('mediaSearch').addEventListener('keypress', (e) => { if(e.key==='Enter') loadMediaList() });
    document.getElementById('filterType').addEventListener('change', loadMediaList);
    document.getElementById('filterCategory').addEventListener('change', loadMediaList);
    
    // Media Modal
    document.getElementById('mediaModalClose').addEventListener('click', closeMediaModal);
    document.getElementById('mediaModalClose2').addEventListener('click', closeMediaModal);
    
    // Upload Drag & Drop
    const dropZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    
    document.getElementById('browseBtn').addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFileSelect(e);
    });
    
    document.getElementById('uploadBtn').addEventListener('click', doUpload);
    
    // Scheduler
    document.getElementById('addTaskBtn').addEventListener('click', doSchedule);
    document.getElementById('refreshTasksBtn').addEventListener('click', loadTasks);
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
