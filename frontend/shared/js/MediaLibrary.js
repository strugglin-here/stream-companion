/**
 * MediaLibrary - Display and manage uploaded media files
 * 
 * Usage:
 *   const library = new MediaLibrary(containerElement, {
 *       apiUrl: '/api/media',
 *       onFileSelect: (fileInfo) => console.log('Selected:', fileInfo),
 *       onFileDelete: (filename) => console.log('Deleted:', filename)
 *   });
 */
class MediaLibrary {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            apiUrl: options.apiUrl || '/api/media',
            filterType: options.filterType || null, // 'image', 'video', 'audio', or null for all
            onFileSelect: options.onFileSelect || (() => {}),
            onFileDelete: options.onFileDelete || (() => {}),
            onRefresh: options.onRefresh || (() => {})
        };
        
        this.files = [];
        this.selectedFile = null;
        
        this.render();
        this.loadFiles();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="media-library">
                <div class="library-header">
                    <h3 class="library-title">Media Library</h3>
                    <div class="library-actions">
                        <select id="typeFilter" class="type-filter">
                            <option value="">All Types</option>
                            <option value="image">Images</option>
                            <option value="video">Videos</option>
                            <option value="audio">Audio</option>
                        </select>
                        <button id="refreshBtn" class="btn-refresh" title="Refresh">🔄</button>
                    </div>
                </div>
                <div class="library-grid" id="mediaGrid">
                    <div class="loading">Loading media files...</div>
                </div>
            </div>
        `;
        
        // Add CSS if not already present
        if (!document.getElementById('media-library-styles')) {
            this.injectStyles();
        }
        
        // Attach event listeners
        this.container.querySelector('#typeFilter').addEventListener('change', (e) => {
            this.options.filterType = e.target.value || null;
            this.loadFiles();
        });
        
        this.container.querySelector('#refreshBtn').addEventListener('click', () => {
            this.loadFiles();
        });
    }
    
    injectStyles() {
        const style = document.createElement('style');
        style.id = 'media-library-styles';
        style.textContent = `
            .media-library {
                width: 100%;
            }
            
            .library-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 12px;
                border-bottom: 2px solid #e2e8f0;
            }
            
            .library-title {
                font-size: 20px;
                font-weight: 600;
                color: #2d3748;
                margin: 0;
            }
            
            .library-actions {
                display: flex;
                gap: 12px;
                align-items: center;
            }
            
            .type-filter {
                padding: 6px 12px;
                border: 1px solid #cbd5e0;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                cursor: pointer;
            }
            
            .btn-refresh {
                padding: 6px 12px;
                border: 1px solid #cbd5e0;
                border-radius: 6px;
                background: white;
                cursor: pointer;
                font-size: 16px;
                transition: all 0.2s;
            }
            
            .btn-refresh:hover {
                background: #f7fafc;
                transform: rotate(90deg);
            }
            
            .library-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
                gap: 16px;
                min-height: 200px;
            }
            
            .loading {
                grid-column: 1 / -1;
                text-align: center;
                padding: 60px 20px;
                color: #718096;
                font-size: 14px;
            }
            
            .media-item {
                position: relative;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                overflow: hidden;
                cursor: pointer;
                transition: all 0.2s;
                background: white;
            }
            
            .media-item:hover {
                border-color: #4299e1;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
            
            .media-item.selected {
                border-color: #3182ce;
                box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.2);
            }
            
            .media-preview {
                width: 100%;
                height: 140px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f7fafc;
                overflow: hidden;
            }
            
            .media-preview img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            
            .media-preview video {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            
            .media-icon {
                font-size: 48px;
                opacity: 0.5;
            }
            
            .media-info {
                padding: 12px;
            }
            
            .media-filename {
                font-size: 13px;
                font-weight: 500;
                color: #2d3748;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                margin-bottom: 4px;
            }
            
            .media-meta {
                font-size: 11px;
                color: #718096;
                display: flex;
                justify-content: space-between;
            }
            
            .media-actions {
                position: absolute;
                top: 8px;
                right: 8px;
                display: flex;
                gap: 4px;
                opacity: 0;
                transition: opacity 0.2s;
            }
            
            .media-item:hover .media-actions {
                opacity: 1;
            }
            
            .btn-action {
                width: 28px;
                height: 28px;
                border: none;
                border-radius: 4px;
                background: rgba(0, 0, 0, 0.6);
                color: white;
                cursor: pointer;
                font-size: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
            }
            
            .btn-action:hover {
                background: rgba(0, 0, 0, 0.8);
            }
            
            .btn-delete {
                background: rgba(220, 38, 38, 0.9);
            }
            
            .btn-delete:hover {
                background: rgba(185, 28, 28, 1);
            }
        `;
        document.head.appendChild(style);
    }
    
    async loadFiles() {
        const grid = this.container.querySelector('#mediaGrid');
        grid.innerHTML = '<div class="loading">Loading media files...</div>';
        
        try {
            const url = this.options.filterType 
                ? `${this.options.apiUrl}/?type=${this.options.filterType}`
                : `${this.options.apiUrl}/`;
            
            const response = await fetch(url);
            const data = await response.json();
            
            this.files = data.items;
            this.renderGrid();
            this.options.onRefresh(this.files);
            
        } catch (error) {
            grid.innerHTML = `<div class="loading">Failed to load media files: ${error.message}</div>`;
        }
    }
    
    renderGrid() {
        const grid = this.container.querySelector('#mediaGrid');
        
        if (this.files.length === 0) {
            grid.innerHTML = '<div class="loading">No media files found. Upload some files to get started!</div>';
            return;
        }
        
        grid.innerHTML = this.files.map(file => this.renderMediaItem(file)).join('');
        
        // Attach event listeners
        grid.querySelectorAll('.media-item').forEach((item, index) => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.media-actions')) {
                    this.selectFile(this.files[index]);
                }
            });
        });
        
        grid.querySelectorAll('.btn-delete').forEach((btn, index) => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteFile(this.files[index]);
            });
        });
    }
    
    renderMediaItem(file) {
        const fileType = file.mime_type.split('/')[0];
        const fileSize = this.formatFileSize(file.size);
        const uploadDate = new Date(file.uploaded_at).toLocaleDateString();
        
        let preview = '';
        if (fileType === 'image') {
            preview = `<img src="${file.url}" alt="${file.filename}" loading="lazy">`;
        } else if (fileType === 'video') {
            preview = `<video src="${file.url}" preload="metadata"></video>`;
        } else if (fileType === 'audio') {
            preview = '<div class="media-icon">🎵</div>';
        } else {
            preview = '<div class="media-icon">📄</div>';
        }
        
        return `
            <div class="media-item" data-filename="${file.filename}">
                <div class="media-actions">
                    <button class="btn-action btn-delete" title="Delete">🗑️</button>
                </div>
                <div class="media-preview">
                    ${preview}
                </div>
                <div class="media-info">
                    <div class="media-filename" title="${file.filename}">${file.filename}</div>
                    <div class="media-meta">
                        <span>${fileSize}</span>
                        <span>${uploadDate}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    selectFile(file) {
        this.selectedFile = file;
        
        // Update UI
        this.container.querySelectorAll('.media-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        const selectedItem = this.container.querySelector(`[data-filename="${file.filename}"]`);
        if (selectedItem) {
            selectedItem.classList.add('selected');
        }
        
        this.options.onFileSelect(file);
    }
    
    async deleteFile(file) {
        if (!confirm(`Delete "${file.filename}"? This cannot be undone.`)) {
            return;
        }
        
        try {
            const response = await fetch(`${this.options.apiUrl}/${file.filename}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Delete failed');
            }
            
            this.options.onFileDelete(file.filename);
            await this.loadFiles();
            
        } catch (error) {
            alert(`Failed to delete file: ${error.message}`);
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }
    
    refresh() {
        return this.loadFiles();
    }
}

// Export for ES modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MediaLibrary;
}
