/**
 * MediaUploader - Simple drag-drop file upload component
 * 
 * Usage:
 *   const uploader = new MediaUploader(containerElement, {
 *       apiUrl: '/api/media',
 *       onUploadSuccess: (fileInfo) => console.log('Uploaded:', fileInfo),
 *       onUploadError: (error) => console.error('Error:', error)
 *   });
 */
class MediaUploader {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            apiUrl: options.apiUrl || '/api/media',
            maxFileSize: options.maxFileSize || 100 * 1024 * 1024, // 100MB default
            allowedTypes: options.allowedTypes || ['image/*', 'video/*', 'audio/*'],
            onUploadStart: options.onUploadStart || (() => {}),
            onUploadProgress: options.onUploadProgress || (() => {}),
            onUploadSuccess: options.onUploadSuccess || (() => {}),
            onUploadError: options.onUploadError || (() => {})
        };
        
        this.render();
        this.attachEvents();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="media-uploader">
                <div class="upload-zone" id="uploadZone">
                    <div class="upload-icon">📁</div>
                    <div class="upload-text">
                        <p class="upload-primary">Drag & drop files here</p>
                        <p class="upload-secondary">or click to browse</p>
                    </div>
                    <input 
                        type="file" 
                        id="fileInput" 
                        multiple 
                        accept="${this.options.allowedTypes.join(',')}"
                        style="display: none;"
                    />
                </div>
                <div class="upload-progress" id="uploadProgress" style="display: none;">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text" id="progressText">Uploading...</div>
                </div>
            </div>
        `;
        
        // Add CSS if not already present
        if (!document.getElementById('media-uploader-styles')) {
            this.injectStyles();
        }
    }
    
    injectStyles() {
        const style = document.createElement('style');
        style.id = 'media-uploader-styles';
        style.textContent = `
            .media-uploader {
                width: 100%;
            }
            
            .upload-zone {
                border: 2px dashed #cbd5e0;
                border-radius: 12px;
                padding: 40px 20px;
                text-align: center;
                background: #f7fafc;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .upload-zone:hover {
                border-color: #4299e1;
                background: #ebf8ff;
            }
            
            .upload-zone.drag-over {
                border-color: #3182ce;
                background: #bee3f8;
                transform: scale(1.02);
            }
            
            .upload-icon {
                font-size: 48px;
                margin-bottom: 16px;
            }
            
            .upload-primary {
                font-size: 18px;
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 8px;
            }
            
            .upload-secondary {
                font-size: 14px;
                color: #718096;
                margin: 0;
            }
            
            .upload-progress {
                margin-top: 20px;
            }
            
            .progress-bar {
                width: 100%;
                height: 8px;
                background: #e2e8f0;
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 8px;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #4299e1 0%, #3182ce 100%);
                transition: width 0.3s;
                width: 0%;
            }
            
            .progress-text {
                font-size: 14px;
                color: #4a5568;
                text-align: center;
            }
        `;
        document.head.appendChild(style);
    }
    
    attachEvents() {
        const uploadZone = this.container.querySelector('#uploadZone');
        const fileInput = this.container.querySelector('#fileInput');
        
        // Click to browse
        uploadZone.addEventListener('click', () => fileInput.click());
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
            fileInput.value = ''; // Reset for re-upload
        });
        
        // Drag and drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });
        
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('drag-over');
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            this.handleFiles(e.dataTransfer.files);
        });
    }
    
    async handleFiles(files) {
        if (files.length === 0) return;
        
        for (const file of files) {
            await this.uploadFile(file);
        }
    }
    
    async uploadFile(file) {
        // Validate file size
        if (file.size > this.options.maxFileSize) {
            const maxMB = this.options.maxFileSize / (1024 * 1024);
            this.options.onUploadError({
                message: `File too large. Maximum size: ${maxMB}MB`,
                file: file.name
            });
            return;
        }
        
        // Show progress
        const progressContainer = this.container.querySelector('#uploadProgress');
        const progressFill = this.container.querySelector('#progressFill');
        const progressText = this.container.querySelector('#progressText');
        
        progressContainer.style.display = 'block';
        progressText.textContent = `Uploading ${file.name}...`;
        
        this.options.onUploadStart(file);
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            // Upload with progress tracking
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = (e.loaded / e.total) * 100;
                    progressFill.style.width = `${percent}%`;
                    this.options.onUploadProgress(percent, file);
                }
            });
            
            const response = await new Promise((resolve, reject) => {
                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        resolve(JSON.parse(xhr.responseText));
                    } else {
                        reject(new Error(xhr.statusText || 'Upload failed'));
                    }
                });
                
                xhr.addEventListener('error', () => reject(new Error('Network error')));
                xhr.addEventListener('abort', () => reject(new Error('Upload cancelled')));
                
                xhr.open('POST', `${this.options.apiUrl}/upload`);
                xhr.send(formData);
            });
            
            // Success
            progressText.textContent = `✓ ${file.name} uploaded successfully`;
            setTimeout(() => {
                progressContainer.style.display = 'none';
                progressFill.style.width = '0%';
            }, 2000);
            
            this.options.onUploadSuccess(response);
            
        } catch (error) {
            progressText.textContent = `✗ Upload failed: ${error.message}`;
            setTimeout(() => {
                progressContainer.style.display = 'none';
                progressFill.style.width = '0%';
            }, 3000);
            
            this.options.onUploadError({
                message: error.message,
                file: file.name
            });
        }
    }
}

// Export for ES modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MediaUploader;
}
