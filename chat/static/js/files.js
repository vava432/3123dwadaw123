document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initFileUpload();
    loadFiles();
});

function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            this.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');
        });
    });
}

function initFileUpload() {
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.getElementById('file-upload-area');
    
    fileInput.addEventListener('change', function(e) {
        handleFiles(this.files);
    });
    
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });
}

function handleFiles(files) {
    if (files.length === 0) return;
    
    for (let i = 0; i < files.length; i++) {
        uploadFile(files[i]);
    }
}

function uploadFile(file) {
    if (file.size > 100 * 1024 * 1024) {
        alert('Файл слишком большой! Максимальный размер: 100MB');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('room_link', roomLink);
    
    const fileItem = createUploadingFileItem(file.name, file.size);
    
    fetch('/upload_file', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            fileItem.remove();
            loadFiles();
            showNotification('Файл успешно загружен', 'success');
        } else {
            fileItem.querySelector('.file-status').textContent = 'Ошибка: ' + data.error;
            fileItem.classList.add('error');
        }
    })
    .catch(error => {
        fileItem.querySelector('.file-status').textContent = 'Ошибка сети';
        fileItem.classList.add('error');
        console.error('Upload error:', error);
    });
}

function createUploadingFileItem(filename, size) {
    const filesList = document.getElementById('files-list');
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item uploading';
    fileItem.innerHTML = `
        <div class="file-icon">⏳</div>
        <div class="file-info">
            <div class="file-name">${filename}</div>
            <div class="file-details">
                <span class="file-size">${formatFileSize(size)}</span>
                <span class="file-status">Загрузка...</span>
            </div>
        </div>
        <div class="file-progress">
            <div class="progress-bar">
                <div class="progress"></div>
            </div>
        </div>
    `;
    filesList.insertBefore(fileItem, filesList.firstChild);
    return fileItem;
}

function loadFiles() {
    fetch(`/get_files/${roomLink}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayFiles(data.files);
            } else {
                console.error('Ошибка загрузки файлов:', data.error);
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
        });
}

function displayFiles(files) {
    const filesList = document.getElementById('files-list');
    filesList.innerHTML = '';
    
    if (files.length === 0) {
        filesList.innerHTML = '<div class="no-files">Файлы не загружены</div>';
        return;
    }
    
    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.setAttribute('data-file-id', file.id);
        
        const canDelete = currentUserId === file.user_id || roomCreatorId === currentUserId;
        
        fileItem.innerHTML = `
            <div class="file-icon">${file.icon}</div>
            <div class="file-info">
                <div class="file-name" title="${file.original_filename}">${file.original_filename}</div>
                <div class="file-details">
                    <span class="file-size">${file.size_formatted}</span>
                    <span class="file-uploader">от ${file.username}</span>
                    <span class="file-date">${new Date(file.upload_date).toLocaleString()}</span>
                </div>
            </div>
            <div class="file-actions">
                <button onclick="downloadFile(${file.id})" class="btn-small" title="Скачать">📥</button>
                ${canDelete ? `<button onclick="deleteFile(${file.id})" class="btn-small delete" title="Удалить">🗑️</button>` : ''}
            </div>
        `;
        
        filesList.appendChild(fileItem);
    });
}

function downloadFile(fileId) {
    window.open(`/download_file/${fileId}`, '_blank');
}

function deleteFile(fileId) {
    if (!confirm('Вы уверены, что хотите удалить этот файл?')) {
        return;
    }
    
    fetch(`/delete_file/${fileId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.querySelector(`.file-item[data-file-id="${fileId}"]`).remove();
            showNotification('Файл удален', 'success');
            
            const filesList = document.getElementById('files-list');
            if (filesList.children.length === 0) {
                filesList.innerHTML = '<div class="no-files">Файлы не загружены</div>';
            }
        } else {
            showNotification('Ошибка удаления: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Delete error:', error);
        showNotification('Ошибка сети', 'error');
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}