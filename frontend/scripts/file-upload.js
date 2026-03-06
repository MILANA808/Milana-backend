/**
 * File Upload Module for Milana frontend
 * Supports image and document uploads with backend integration
 */

import { i18n, t } from './i18n.js';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
const ALLOWED_FILE_TYPES = [
    ...ALLOWED_IMAGE_TYPES,
    'application/pdf',
    'text/plain',
    'text/markdown',
    'application/json'
];

/**
 * File upload manager class
 */
export class FileUploadManager {
    constructor(options = {}) {
        this.onUpload = options.onUpload || (() => {});
        this.onError = options.onError || console.error;
        this.onProgress = options.onProgress || (() => {});
        this.apiEndpoint = options.apiEndpoint || '/aksi/v2/tools/vision/upload';
        this.pendingFiles = [];
    }

    /**
     * Create file input element
     */
    createFileInput(acceptTypes = ALLOWED_FILE_TYPES) {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = acceptTypes.join(',');
        input.style.display = 'none';
        input.multiple = false;

        input.addEventListener('change', async (e) => {
            const file = e.target.files?.[0];
            if (file) {
                await this.handleFile(file);
            }
            input.value = ''; // Reset for next selection
        });

        return input;
    }

    /**
     * Create image input (photos only)
     */
    createImageInput() {
        return this.createFileInput(ALLOWED_IMAGE_TYPES);
    }

    /**
     * Validate file before upload
     */
    validateFile(file) {
        if (file.size > MAX_FILE_SIZE) {
            const maxMB = MAX_FILE_SIZE / (1024 * 1024);
            return { valid: false, error: `File too large. Maximum size: ${maxMB}MB` };
        }

        if (!ALLOWED_FILE_TYPES.includes(file.type)) {
            return { valid: false, error: `File type not supported: ${file.type}` };
        }

        return { valid: true };
    }

    /**
     * Check if file is an image
     */
    isImage(file) {
        return ALLOWED_IMAGE_TYPES.includes(file.type);
    }

    /**
     * Read file as base64
     */
    readAsBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result.split(',')[1]; // Remove data URL prefix
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    /**
     * Read file as text
     */
    readAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsText(file);
        });
    }

    /**
     * Handle file selection
     */
    async handleFile(file) {
        // Validate
        const validation = this.validateFile(file);
        if (!validation.valid) {
            this.onError(validation.error);
            return null;
        }

        // Process based on type
        if (this.isImage(file)) {
            return await this.processImage(file);
        } else {
            return await this.processDocument(file);
        }
    }

    /**
     * Process image file
     */
    async processImage(file) {
        try {
            const base64 = await this.readAsBase64(file);
            const previewUrl = URL.createObjectURL(file);

            const result = {
                type: 'image',
                file: file,
                name: file.name,
                size: file.size,
                mimeType: file.type,
                base64: base64,
                previewUrl: previewUrl
            };

            this.pendingFiles.push(result);
            this.onUpload(result);

            return result;
        } catch (error) {
            this.onError(`Failed to process image: ${error.message}`);
            return null;
        }
    }

    /**
     * Process document file
     */
    async processDocument(file) {
        try {
            let content;

            if (file.type === 'application/pdf') {
                // For PDF, read as base64
                content = await this.readAsBase64(file);
            } else {
                // For text files, read as text
                content = await this.readAsText(file);
            }

            const result = {
                type: 'document',
                file: file,
                name: file.name,
                size: file.size,
                mimeType: file.type,
                content: content
            };

            this.pendingFiles.push(result);
            this.onUpload(result);

            return result;
        } catch (error) {
            this.onError(`Failed to process document: ${error.message}`);
            return null;
        }
    }

    /**
     * Get pending files
     */
    getPendingFiles() {
        return this.pendingFiles;
    }

    /**
     * Clear pending files
     */
    clearPendingFiles() {
        // Revoke object URLs to prevent memory leaks
        this.pendingFiles.forEach(f => {
            if (f.previewUrl) {
                URL.revokeObjectURL(f.previewUrl);
            }
        });
        this.pendingFiles = [];
    }

    /**
     * Remove a specific pending file
     */
    removePendingFile(index) {
        const file = this.pendingFiles[index];
        if (file?.previewUrl) {
            URL.revokeObjectURL(file.previewUrl);
        }
        this.pendingFiles.splice(index, 1);
    }
}

/**
 * Create upload buttons UI
 */
export function createUploadButtons(uploadManager, container) {
    // Create file input elements
    const imageInput = uploadManager.createImageInput();
    const fileInput = uploadManager.createFileInput();

    // Create buttons wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'upload-buttons';

    // Photo upload button
    const photoButton = document.createElement('button');
    photoButton.type = 'button';
    photoButton.className = 'upload-btn upload-photo';
    photoButton.innerHTML = '<span class="upload-icon">📷</span>';
    photoButton.title = t('chat.attachPhoto');

    photoButton.addEventListener('click', () => {
        imageInput.click();
    });

    // File upload button
    const fileButton = document.createElement('button');
    fileButton.type = 'button';
    fileButton.className = 'upload-btn upload-file';
    fileButton.innerHTML = '<span class="upload-icon">📎</span>';
    fileButton.title = t('chat.attachFile');

    fileButton.addEventListener('click', () => {
        fileInput.click();
    });

    // Update titles on language change
    i18n.subscribe(() => {
        photoButton.title = t('chat.attachPhoto');
        fileButton.title = t('chat.attachFile');
    });

    wrapper.appendChild(imageInput);
    wrapper.appendChild(fileInput);
    wrapper.appendChild(photoButton);
    wrapper.appendChild(fileButton);

    if (container) {
        container.appendChild(wrapper);
    }

    return {
        wrapper,
        photoButton,
        fileButton,
        imageInput,
        fileInput
    };
}

/**
 * Create file preview element
 */
export function createFilePreview(fileData, onRemove) {
    const preview = document.createElement('div');
    preview.className = 'file-preview';

    if (fileData.type === 'image') {
        const img = document.createElement('img');
        img.src = fileData.previewUrl;
        img.alt = fileData.name;
        img.className = 'file-preview-image';
        preview.appendChild(img);
    } else {
        const icon = document.createElement('div');
        icon.className = 'file-preview-icon';
        icon.textContent = '📄';
        preview.appendChild(icon);
    }

    const info = document.createElement('div');
    info.className = 'file-preview-info';
    info.innerHTML = `
        <span class="file-preview-name">${escapeHtml(fileData.name)}</span>
        <span class="file-preview-size">${formatFileSize(fileData.size)}</span>
    `;
    preview.appendChild(info);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'file-preview-remove';
    removeBtn.textContent = '×';
    removeBtn.addEventListener('click', onRemove);
    preview.appendChild(removeBtn);

    return preview;
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

export default FileUploadManager;
