// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileListContainer = document.getElementById('file-list-container');
const progressContainer = document.getElementById('progress-container');
const clipboardText = document.getElementById('clipboard-text');
const sendClipboardBtn = document.getElementById('send-clipboard-btn');
const copyClipboardBtn = document.getElementById('copy-clipboard-btn');
const toast = document.getElementById('toast');
const toastText = document.getElementById('toast-text');
const toastIcon = document.getElementById('toast-icon');

// Lock Screen Elements
const lockScreen = document.getElementById('lock-screen');
const mainApp = document.getElementById('main-app');
const pinInput = document.getElementById('pin-input');
const verifyPinBtn = document.getElementById('verify-pin-btn');
const lockError = document.getElementById('lock-error');

// Modal Elements
const previewModal = document.getElementById('preview-modal');
const previewTitle = document.getElementById('preview-title');
const previewBody = document.getElementById('preview-body');
const closePreviewBtn = document.getElementById('close-preview-btn');

// Clipboard History Elements
const clipboardHistoryList = document.getElementById('clipboard-history-list');

// Stream Sync Elements
// State variables
let sharedFiles = [];
let clipboardInterval;
let isLocked = false;
let cachedHistoryJson = '';
let closePreviewTimeout = null;

// Lock Screen Handling
function showLockScreen() {
    if (isLocked) return;
    isLocked = true;
    lockScreen.style.display = 'flex';
    mainApp.style.display = 'none';
    pinInput.value = '';
    pinInput.focus();
    lockError.style.display = 'none';
}

function hideLockScreen() {
    isLocked = false;
    lockScreen.style.display = 'none';
    mainApp.style.display = ''; // Revert to CSS default (display: flex)
    lockError.style.display = 'none';
}

function showBlockedScreen() {
    isLocked = true;
    lockScreen.style.display = 'flex';
    mainApp.style.display = 'none';

    const lockCard = document.querySelector('.lock-card');
    if (lockCard && !lockCard.classList.contains('blocked-state')) {
        lockCard.classList.add('blocked-state');
        lockCard.innerHTML = `
            <div class="logo-container" style="justify-content: center; margin-bottom: 20px; text-align: left;">
                <div class="logo-icon" style="background-color: rgba(239, 68, 68, 0.1); color: var(--error);">
                    <i class="fa-solid fa-ban"></i>
                </div>
                <div class="logo-text">
                    <h1 style="color: var(--error);">PyTransfer</h1>
                    <p>Erişim Engellendi</p>
                </div>
            </div>
            <p class="lock-message" style="color: var(--error); font-weight: 600;">Bu bilgisayara erişiminiz engellenmiştir.</p>
            <p style="font-size: 11px; color: var(--text-muted);">Lütfen sistem yöneticisi ile iletişime geçin.</p>
        `;
    }
}

function showPinError(message) {
    lockError.textContent = message;
    lockError.style.display = 'block';
}

async function verifyPin(pin) {
    try {
        const response = await fetch('/api/verify-pin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pin })
        });
        if (response.status === 403) {
            showBlockedScreen();
            return false;
        }
        const data = await response.json();
        if (response.status === 200 && data.status === 'success') {
            hideLockScreen();
            fetchSharedFiles();
            fetchClipboard();
            fetchClipboardHistory();
            showToast('Bağlantı başarılı!');
            return true;
        } else {
            showPinError(data.message || 'Geçersiz PIN kodu!');
            return false;
        }
    } catch (error) {
        showPinError('Sunucuya bağlanılamadı!');
        return false;
    }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    // Check URL parameters for PIN code
    const urlParams = new URLSearchParams(window.location.search);
    const pinParam = urlParams.get('pin');
    if (pinParam) {
        // Clear PIN parameter from URL bar to hide it
        const newUrl = window.location.protocol + "//" + window.location.host + window.location.pathname;
        window.history.replaceState({ path: newUrl }, '', newUrl);
    }

    // Initial fetch requests
    fetchSharedFiles();
    fetchClipboard();
    fetchClipboardHistory();
    // Periodically fetch files and clipboard updates
    setInterval(() => {
        fetchSharedFiles();
    }, 3000);
    clipboardInterval = setInterval(() => {
        if (!isLocked) {
            fetchClipboard();
            fetchClipboardHistory();
        }
    }, 3000);

    // Bind Lock Screen Event Listeners
    verifyPinBtn.addEventListener('click', () => {
        const pin = pinInput.value.trim();
        if (pin) {
            verifyPin(pin);
        } else {
            showPinError('Lütfen PIN kodunu girin.');
        }
    });

    pinInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            verifyPinBtn.click();
        }
    });

    // Modal Events
    closePreviewBtn.addEventListener('click', closePreview);
    previewModal.addEventListener('click', (e) => {
        if (e.target === previewModal) {
            closePreview();
        }
    });

    const downloadAllBtn = document.getElementById('download-all-btn');
    if (downloadAllBtn) {
        downloadAllBtn.addEventListener('click', () => {
            window.location.href = '/api/download_all';
            showToast("Toplu indirme başlatılıyor...", "success");
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (previewModal.classList.contains('show')) closePreview();
        }
    });
});

// Toast Notification helper
function showToast(message, type = 'success') {
    toastText.textContent = message;
    if (type === 'success') {
        toastIcon.className = 'fa-solid fa-circle-check toast-icon';
        toastIcon.style.color = 'var(--success)';
    } else {
        toastIcon.className = 'fa-solid fa-circle-exclamation toast-icon';
        toastIcon.style.color = 'var(--warning)';
    }
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Get file type icon class
function getFileTypeIcon(ext) {
    const icons = {
        '.zip': 'fa-file-zipper', '.rar': 'fa-file-zipper', '.7z': 'fa-file-zipper',
        '.pdf': 'fa-file-pdf',
        '.doc': 'fa-file-word', '.docx': 'fa-file-word',
        '.xls': 'fa-file-excel', '.xlsx': 'fa-file-excel',
        '.ppt': 'fa-file-powerpoint', '.pptx': 'fa-file-powerpoint',
        '.jpg': 'fa-file-image', '.jpeg': 'fa-file-image', '.png': 'fa-file-image', '.gif': 'fa-file-image', '.svg': 'fa-file-image',
        '.mp4': 'fa-file-video', '.mkv': 'fa-file-video', '.avi': 'fa-file-video', '.mov': 'fa-file-video',
        '.mp3': 'fa-file-audio', '.wav': 'fa-file-audio', '.flac': 'fa-file-audio',
        '.txt': 'fa-file-lines', '.md': 'fa-file-lines', '.json': 'fa-file-code', '.html': 'fa-file-code', '.js': 'fa-file-code', '.py': 'fa-file-code'
    };
    return icons[ext] || 'fa-file';
}

// Check if extension is previewable
function isPreviewable(ext) {
    const previewTypes = {
        image: ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'],
        video: ['.mp4', '.webm', '.ogg'],
        audio: ['.mp3', '.wav', '.ogg', '.aac', '.m4a'],
        pdf: ['.pdf']
    };
    if (previewTypes.image.includes(ext)) return 'image';
    if (previewTypes.video.includes(ext)) return 'video';
    if (previewTypes.audio.includes(ext)) return 'audio';
    if (previewTypes.pdf.includes(ext)) return 'pdf';
    return null;
}

// Format file sizes
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Fetch shared files from server
async function fetchSharedFiles() {
    try {
        const response = await fetch('/api/files');
        if (response.status === 401) {
            showLockScreen();
            return;
        }
        if (response.status === 403) {
            showBlockedScreen();
            return;
        }

        hideLockScreen();

        const files = await response.json();

        // Compare to prevent flickering if nothing changed
        if (JSON.stringify(files) === JSON.stringify(sharedFiles)) {
            return;
        }

        sharedFiles = files;
        renderFileList();
    } catch (error) {
        console.error('Error fetching files:', error);
        document.getElementById('connection-status').textContent = 'Bağlantı Yok';
        document.getElementById('connection-status').parentElement.style.background = 'rgba(239, 68, 68, 0.15)';
        document.getElementById('connection-status').parentElement.style.color = '#ef4444';
        document.getElementById('connection-status').parentElement.style.borderColor = 'rgba(239, 68, 68, 0.3)';
        document.querySelector('.status-dot').style.backgroundColor = '#ef4444';
        document.querySelector('.status-dot').style.boxShadow = '0 0 8px #ef4444';
    }
}

// Render files list
function renderFileList() {
    const downloadAllBtn = document.getElementById('download-all-btn');
    if (sharedFiles.length === 0) {
        if (downloadAllBtn) downloadAllBtn.style.display = 'none';
        fileListContainer.innerHTML = `
            <div class="no-files">
                <i class="fa-regular fa-folder-open"></i>
                <p>Henüz bilgisayardan paylaşılan dosya yok.</p>
            </div>`;
        return;
    }

    if (downloadAllBtn && sharedFiles.length > 1) {
        downloadAllBtn.style.display = 'inline-block';
    } else if (downloadAllBtn) {
        downloadAllBtn.style.display = 'none';
    }

    fileListContainer.innerHTML = sharedFiles.map(file => {
        const mediaType = isPreviewable(file.ext);
        const previewBtnHtml = mediaType ? `
            <button class="preview-btn" onclick="openPreview('${file.id}', '${file.name.replace(/'/g, "\\'")}', '${mediaType}')" title="Önizle">
                <i class="fa-solid fa-eye"></i>
            </button>
        ` : '';
        return `
            <div class="file-card">
                <div class="file-details">
                    <div class="file-type-icon">
                        <i class="fa-solid ${getFileTypeIcon(file.ext)}"></i>
                    </div>
                    <div class="file-meta">
                        <span class="file-name" title="${file.name}">${file.name}</span>
                        <span class="file-size">${formatBytes(file.size)}</span>
                    </div>
                </div>
                <div class="file-actions">
                    ${previewBtnHtml}
                    <a href="/api/download/${file.id}" class="download-btn" download="${file.name}" title="İndir">
                        <i class="fa-solid fa-download"></i>
                    </a>
                </div>
            </div>
        `;
    }).join('');
}

// Media Preview Modal functions
window.openPreview = function (fileId, fileName, mediaType) {
    if (closePreviewTimeout) {
        clearTimeout(closePreviewTimeout);
        closePreviewTimeout = null;
    }

    previewTitle.textContent = fileName;
    previewBody.innerHTML = '';

    const fileUrl = `/api/download/${fileId}?preview=true`;

    if (mediaType === 'image') {
        const img = document.createElement('img');
        img.src = fileUrl;
        img.alt = fileName;
        previewBody.appendChild(img);
    } else if (mediaType === 'video') {
        const video = document.createElement('video');
        video.src = fileUrl;
        video.controls = true;
        video.autoplay = true;
        previewBody.appendChild(video);
    } else if (mediaType === 'audio') {
        const audio = document.createElement('audio');
        audio.src = fileUrl;
        audio.controls = true;
        audio.autoplay = true;
        previewBody.appendChild(audio);
    } else if (mediaType === 'pdf') {
        const iframe = document.createElement('iframe');
        iframe.src = fileUrl;
        iframe.style.width = '100%';
        iframe.style.height = '80vh';
        iframe.style.border = 'none';
        previewBody.appendChild(iframe);
    }

    previewModal.style.display = 'flex';
    void previewModal.offsetWidth;
    previewModal.classList.add('show');
};

function closePreview() {
    previewModal.classList.remove('show');
    if (closePreviewTimeout) clearTimeout(closePreviewTimeout);
    closePreviewTimeout = setTimeout(() => {
        previewBody.innerHTML = '';
        previewModal.style.display = 'none';
        closePreviewTimeout = null;
    }, 300);
}

// Fetch clipboard text
async function fetchClipboard() {
    try {
        const response = await fetch('/api/clipboard');
        if (response.status === 401) {
            showLockScreen();
            return;
        }
        if (response.status === 403) {
            showBlockedScreen();
            return;
        }

        const data = await response.json();

        // Only update if text area is not currently focused by user
        if (document.activeElement !== clipboardText && clipboardText.value !== data.text) {
            clipboardText.value = data.text;
        }

        document.getElementById('connection-status').textContent = 'Bilgisayara Bağlı';
        document.getElementById('connection-status').parentElement.style.background = 'rgba(16, 185, 129, 0.15)';
        document.getElementById('connection-status').parentElement.style.color = 'var(--success)';
        document.getElementById('connection-status').parentElement.style.borderColor = 'rgba(16, 185, 129, 0.3)';
        document.querySelector('.status-dot').style.backgroundColor = 'var(--success)';
        document.querySelector('.status-dot').style.boxShadow = '0 0 8px var(--success)';
    } catch (error) {
        console.error('Error fetching clipboard:', error);
    }
}

// Fetch clipboard history
async function fetchClipboardHistory() {
    try {
        const response = await fetch('/api/clipboard/history');
        if (response.status === 401) {
            showLockScreen();
            return;
        }
        if (response.status === 403) {
            showBlockedScreen();
            return;
        }
        const history = await response.json();

        const historyJson = JSON.stringify(history);
        if (historyJson === cachedHistoryJson) {
            return;
        }
        cachedHistoryJson = historyJson;

        renderClipboardHistory(history);
    } catch (error) {
        console.error('Error fetching clipboard history:', error);
    }
}

// Render clipboard history items
function renderClipboardHistory(history) {
    if (!clipboardHistoryList) return;
    if (history.length === 0) {
        clipboardHistoryList.innerHTML = `<div style="font-size: 11px; color: var(--text-muted); text-align: center; padding: 10px;">Geçmiş boş.</div>`;
        return;
    }
    clipboardHistoryList.innerHTML = history.map((text, idx) => {
        const display = text.replace(/[\n\r]+/g, " ");
        return `
            <div class="history-item" onclick="selectHistoryItem(${idx})" title="${text.replace(/"/g, '&quot;')}">${display}</div>
        `;
    }).join('');
}

// Expose history item click
window.selectHistoryItem = async function (idx) {
    const history = JSON.parse(cachedHistoryJson);
    const text = history[idx];
    if (!text) return;

    clipboardText.value = text;

    try {
        const response = await fetch('/api/clipboard', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        if (response.status === 401) {
            showLockScreen();
            return;
        }
        const result = await response.json();
        if (result.status === 'success') {
            showToast('Pano metni güncellendi!');
            fetchClipboardHistory();
        }
    } catch (error) {
        showToast('Pano güncellenemedi!', 'error');
    }
};

// Send clipboard text to server
sendClipboardBtn.addEventListener('click', async () => {
    const text = clipboardText.value;
    try {
        const response = await fetch('/api/clipboard', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });

        if (response.status === 401) {
            showLockScreen();
            return;
        }

        const result = await response.json();
        if (result.status === 'success') {
            showToast('Metin bilgisayara gönderildi!');
            fetchClipboardHistory();
        }
    } catch (error) {
        showToast('Metin gönderilemedi!', 'error');
    }
});

// Copy current clipboard text to device clipboard
copyClipboardBtn.addEventListener('click', () => {
    clipboardText.select();
    document.execCommand('copy');
    window.getSelection().removeAllRanges();
    showToast('Metin kopyalandı!');
});

// Drag & Drop event listeners

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
        dropZone.classList.add('drag-over');
    }, false);
});
['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
        dropZone.classList.remove('drag-over');
    }, false);
});

dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFilesUpload(files);
});

dropZone.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        handleFilesUpload(fileInput.files);
        fileInput.value = ''; // Reset
    }
});

// Upload files implementation
function handleFilesUpload(files) {
    if (files.length === 0) return;

    Array.from(files).forEach(file => {
        uploadFile(file);
    });
}

function uploadFile(file) {
    const itemId = 'upload-' + Math.random().toString(36).substr(2, 9);
    const progressItemHtml = `
        <div class="progress-item" id="${itemId}">
            <div class="progress-info">
                <span class="progress-name">${file.name}</span>
                <span class="progress-percent" id="${itemId}-percent">Hazırlanıyor...</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" id="${itemId}-fill"></div>
            </div>
        </div>
    `;

    progressContainer.insertAdjacentHTML('afterbegin', progressItemHtml);

    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload', true);

    // Track progress
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            const fillEl = document.getElementById(`${itemId}-fill`);
            const percentEl = document.getElementById(`${itemId}-percent`);

            if (fillEl) fillEl.style.width = percentComplete + '%';

            if (percentEl) {
                if (percentComplete === 100) {
                    percentEl.textContent = 'Kaydediliyor...';
                } else {
                    percentEl.textContent = percentComplete + '%';
                }
            }
        }
    });

    // Upload complete or error
    xhr.addEventListener('load', () => {
        if (xhr.status === 401) {
            showLockScreen();
            handleUploadError(itemId, file.name);
            return;
        }
        if (xhr.status === 200) {
            try {
                const response = JSON.parse(xhr.responseText);
                const percentEl = document.getElementById(`${itemId}-percent`);
                const fillEl = document.getElementById(`${itemId}-fill`);

                if (percentEl) {
                    percentEl.textContent = 'Tamamlandı';
                    percentEl.style.color = 'var(--success)';
                }
                if (fillEl) {
                    fillEl.style.background = 'var(--success)';
                    fillEl.style.boxShadow = '0 0 8px var(--success)';
                }
                showToast(`${file.name} başarıyla gönderildi!`);

                setTimeout(() => {
                    const item = document.getElementById(itemId);
                    if (item) item.remove();
                }, 3000);
            } catch (err) {
                handleUploadError(itemId, file.name);
            }
        } else {
            handleUploadError(itemId, file.name);
        }
    });

    xhr.addEventListener('error', () => {
        handleUploadError(itemId, file.name);
    });

    xhr.send(formData);
}

function handleUploadError(itemId, filename) {
    const percentEl = document.getElementById(`${itemId}-percent`);
    const fillEl = document.getElementById(`${itemId}-fill`);

    if (percentEl) {
        percentEl.textContent = 'Hata';
        percentEl.style.color = '#ef4444';
    }
    if (fillEl) {
        fillEl.style.background = '#ef4444';
        fillEl.style.boxShadow = '0 0 8px #ef4444';
    }
    showToast(`${filename} gönderilirken hata oluştu!`, 'error');

    setTimeout(() => {
        const item = document.getElementById(itemId);
        if (item) item.remove();
    }, 5000);
}