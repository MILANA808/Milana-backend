/**
 * Tests for file-upload module
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { FileUploadManager } from '../scripts/file-upload.js';

// Mock File class for testing
class MockFile {
    constructor(parts, name, options = {}) {
        this.name = name;
        this.type = options.type || 'application/octet-stream';
        this.size = parts.reduce((acc, part) => acc + part.length, 0);
        this._parts = parts;
    }
}

// Mock FileReader
class MockFileReader {
    constructor() {
        this.result = null;
        this.onload = null;
        this.onerror = null;
    }

    readAsDataURL(file) {
        setTimeout(() => {
            // Create a mock base64 data URL
            this.result = `data:${file.type};base64,dGVzdGRhdGE=`;
            if (this.onload) this.onload();
        }, 0);
    }

    readAsText(file) {
        setTimeout(() => {
            this.result = file._parts.join('');
            if (this.onload) this.onload();
        }, 0);
    }
}

// Mock URL.createObjectURL
const mockCreateObjectURL = vi.fn(() => 'blob:mock-url');
const mockRevokeObjectURL = vi.fn();

describe('FileUploadManager', () => {
    let uploadManager;
    let onUploadCallback;
    let onErrorCallback;

    beforeEach(() => {
        // Setup mocks
        global.FileReader = MockFileReader;
        global.URL.createObjectURL = mockCreateObjectURL;
        global.URL.revokeObjectURL = mockRevokeObjectURL;

        onUploadCallback = vi.fn();
        onErrorCallback = vi.fn();

        uploadManager = new FileUploadManager({
            onUpload: onUploadCallback,
            onError: onErrorCallback
        });
    });

    describe('validateFile', () => {
        it('accepts valid image files', () => {
            const file = new MockFile(['test'], 'test.jpg', { type: 'image/jpeg' });
            file.size = 1000; // 1KB
            const result = uploadManager.validateFile(file);
            expect(result.valid).toBe(true);
        });

        it('accepts valid PNG files', () => {
            const file = new MockFile(['test'], 'test.png', { type: 'image/png' });
            file.size = 1000;
            const result = uploadManager.validateFile(file);
            expect(result.valid).toBe(true);
        });

        it('accepts valid text files', () => {
            const file = new MockFile(['test'], 'test.txt', { type: 'text/plain' });
            file.size = 1000;
            const result = uploadManager.validateFile(file);
            expect(result.valid).toBe(true);
        });

        it('rejects files that are too large', () => {
            const file = new MockFile(['test'], 'large.jpg', { type: 'image/jpeg' });
            file.size = 15 * 1024 * 1024; // 15MB
            const result = uploadManager.validateFile(file);
            expect(result.valid).toBe(false);
            expect(result.error).toContain('too large');
        });

        it('rejects unsupported file types', () => {
            const file = new MockFile(['test'], 'test.exe', { type: 'application/x-msdownload' });
            file.size = 1000;
            const result = uploadManager.validateFile(file);
            expect(result.valid).toBe(false);
            expect(result.error).toContain('not supported');
        });
    });

    describe('isImage', () => {
        it('returns true for JPEG files', () => {
            const file = new MockFile(['test'], 'test.jpg', { type: 'image/jpeg' });
            expect(uploadManager.isImage(file)).toBe(true);
        });

        it('returns true for PNG files', () => {
            const file = new MockFile(['test'], 'test.png', { type: 'image/png' });
            expect(uploadManager.isImage(file)).toBe(true);
        });

        it('returns true for GIF files', () => {
            const file = new MockFile(['test'], 'test.gif', { type: 'image/gif' });
            expect(uploadManager.isImage(file)).toBe(true);
        });

        it('returns true for WebP files', () => {
            const file = new MockFile(['test'], 'test.webp', { type: 'image/webp' });
            expect(uploadManager.isImage(file)).toBe(true);
        });

        it('returns false for text files', () => {
            const file = new MockFile(['test'], 'test.txt', { type: 'text/plain' });
            expect(uploadManager.isImage(file)).toBe(false);
        });

        it('returns false for PDF files', () => {
            const file = new MockFile(['test'], 'test.pdf', { type: 'application/pdf' });
            expect(uploadManager.isImage(file)).toBe(false);
        });
    });

    describe('pending files management', () => {
        it('starts with empty pending files', () => {
            expect(uploadManager.getPendingFiles()).toEqual([]);
        });

        it('clears pending files', () => {
            // Manually add a file to pending
            uploadManager.pendingFiles.push({
                type: 'image',
                name: 'test.jpg',
                previewUrl: 'blob:test'
            });

            uploadManager.clearPendingFiles();
            expect(uploadManager.getPendingFiles()).toEqual([]);
        });

        it('removes specific pending file by index', () => {
            uploadManager.pendingFiles.push(
                { type: 'image', name: 'test1.jpg', previewUrl: 'blob:test1' },
                { type: 'image', name: 'test2.jpg', previewUrl: 'blob:test2' }
            );

            uploadManager.removePendingFile(0);

            const remaining = uploadManager.getPendingFiles();
            expect(remaining).toHaveLength(1);
            expect(remaining[0].name).toBe('test2.jpg');
        });

        it('revokes object URLs when clearing files', () => {
            uploadManager.pendingFiles.push({
                type: 'image',
                name: 'test.jpg',
                previewUrl: 'blob:test-url'
            });

            uploadManager.clearPendingFiles();
            expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:test-url');
        });
    });

    describe('createFileInput', () => {
        it('creates hidden file input element', () => {
            const input = uploadManager.createFileInput();
            expect(input.type).toBe('file');
            expect(input.style.display).toBe('none');
        });

        it('sets accept attribute with allowed types', () => {
            const input = uploadManager.createFileInput(['image/jpeg', 'image/png']);
            expect(input.accept).toBe('image/jpeg,image/png');
        });
    });

    describe('createImageInput', () => {
        it('creates input that only accepts images', () => {
            const input = uploadManager.createImageInput();
            expect(input.accept).toContain('image/jpeg');
            expect(input.accept).toContain('image/png');
            expect(input.accept).toContain('image/gif');
            expect(input.accept).toContain('image/webp');
        });
    });
});
