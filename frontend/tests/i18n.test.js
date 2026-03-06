/**
 * Tests for i18n (internationalization) module
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { i18n, t, translations } from '../scripts/i18n.js';

describe('i18n module', () => {
    beforeEach(() => {
        // Reset to Russian before each test
        localStorage.clear();
    });

    describe('translations dictionary', () => {
        it('has Russian translations', () => {
            expect(translations.ru).toBeDefined();
            expect(translations.ru['header.title']).toBe('Milana Superintelligence Hub');
        });

        it('has English translations', () => {
            expect(translations.en).toBeDefined();
            expect(translations.en['header.title']).toBe('Milana Superintelligence Hub');
        });

        it('has matching keys in both languages', () => {
            const ruKeys = Object.keys(translations.ru).sort();
            const enKeys = Object.keys(translations.en).sort();
            expect(ruKeys).toEqual(enKeys);
        });
    });

    describe('language manager', () => {
        it('defaults to Russian when no stored preference', () => {
            // After clear, loadLanguage should detect browser language
            const lang = i18n.getLanguage();
            expect(['ru', 'en']).toContain(lang);
        });

        it('toggles between Russian and English', () => {
            i18n.setLanguage('ru');
            expect(i18n.getLanguage()).toBe('ru');

            i18n.toggle();
            expect(i18n.getLanguage()).toBe('en');

            i18n.toggle();
            expect(i18n.getLanguage()).toBe('ru');
        });

        it('saves language preference to localStorage', () => {
            i18n.setLanguage('en');
            expect(localStorage.getItem('milana_language')).toBe('en');
        });

        it('notifies subscribers on language change', () => {
            const callback = vi.fn();
            i18n.subscribe(callback);

            i18n.setLanguage('en');
            expect(callback).toHaveBeenCalledWith('en');

            i18n.setLanguage('ru');
            expect(callback).toHaveBeenCalledWith('ru');
        });

        it('allows unsubscribing from language changes', () => {
            const callback = vi.fn();
            const unsubscribe = i18n.subscribe(callback);

            i18n.setLanguage('en');
            expect(callback).toHaveBeenCalledTimes(1);

            unsubscribe();
            i18n.setLanguage('ru');
            expect(callback).toHaveBeenCalledTimes(1); // Still 1, not called again
        });
    });

    describe('translation function t()', () => {
        beforeEach(() => {
            i18n.setLanguage('ru');
        });

        it('returns translated string for valid key', () => {
            expect(t('chat.send')).toBe('Отправить');
        });

        it('returns key itself when translation not found', () => {
            expect(t('nonexistent.key')).toBe('nonexistent.key');
        });

        it('replaces placeholders with params', () => {
            // The story user prompt has a {prompt} placeholder
            const result = i18n.t('story.userPrompt', { prompt: 'test topic' });
            expect(result).toContain('test topic');
        });

        it('returns English translation when language is set to English', () => {
            i18n.setLanguage('en');
            expect(t('chat.send')).toBe('Send');
        });
    });

    describe('chat-related translations', () => {
        it('has intro message in Russian', () => {
            i18n.setLanguage('ru');
            expect(t('chat.intro')).toContain('Милана');
        });

        it('has intro message in English', () => {
            i18n.setLanguage('en');
            expect(t('chat.intro')).toContain('Milana');
        });

        it('has file upload related translations', () => {
            expect(translations.ru['chat.attachFile']).toBeDefined();
            expect(translations.ru['chat.attachPhoto']).toBeDefined();
            expect(translations.en['chat.attachFile']).toBeDefined();
            expect(translations.en['chat.attachPhoto']).toBeDefined();
        });
    });
});
