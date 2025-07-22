/**
 * Frontend JavaScript i18n system
 *
 * Provides client-side translation functionality that works with
 * the backend i18n system.
 */

class I18n {
    constructor() {
        this.translations = {};
        this.currentLanguage = 'en';
        this.defaultLanguage = 'en';
        this.cookieName = 'preferred_language';

        // Initialize with current language from cookie or HTML lang attribute
        this.init();
    }

    init() {
        // Detect current language
        this.currentLanguage = this.detectLanguage();

        // Note: loadTranslations is async, so it will complete later
        // The DOMContentLoaded handler will ensure translations are loaded before use
    }

    detectLanguage() {
        // 1. Check HTML lang attribute
        const htmlLang = document.documentElement.lang;
        if (htmlLang) {
            return htmlLang;
        }

        // 2. Check cookie
        const cookieValue = this.getCookie(this.cookieName);
        if (cookieValue) {
            return cookieValue;
        }

        // 3. Check browser language
        const browserLang = navigator.language.split('-')[0];
        if (browserLang) {
            return browserLang;
        }

        // 4. Default language
        return this.defaultLanguage;
    }

    async loadTranslations(language) {
        try {
            // Try to load translations from server
            const response = await fetch(`/static/i18n/${language}.json`);
            if (response.ok) {
                this.translations[language] = await response.json();
            } else {
                // Failed to load translations, try fallback
                if (language !== this.defaultLanguage) {
                    await this.loadTranslations(this.defaultLanguage);
                }
            }
        } catch (error) {
            // Error loading translations - using fallback
        }
    }

    translate(key, variables = {}) {
        const translation = this.getTranslation(key, this.currentLanguage);

        // Interpolate variables
        return this.interpolate(translation, variables);
    }

    getTranslation(key, language) {
        const translations = this.translations[language] || {};

        // Navigate through nested keys
        const keys = key.split('.');
        let value = translations;

        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                // Try default language if key not found
                if (language !== this.defaultLanguage) {
                    return this.getTranslation(key, this.defaultLanguage);
                }
                // Return key if not found in any language
                return key;
            }
        }

        // Return key if value is not a string
        return typeof value === 'string' ? value : key;
    }

    interpolate(text, variables) {
        if (!variables || Object.keys(variables).length === 0) {
            return text;
        }

        // Replace {variable} placeholders
        return text.replace(/\{(\w+)\}/g, (match, key) => {
            return variables[key] !== undefined ? variables[key] : match;
        });
    }

    async setLanguage(language) {
        // Load translations for new language
        if (!this.translations[language]) {
            await this.loadTranslations(language);
        }

        this.currentLanguage = language;

        // Update cookie
        this.setCookie(this.cookieName, language, 365);

        // Update HTML lang attribute
        document.documentElement.lang = language;

        // Trigger language change event
        this.dispatchLanguageChangeEvent();
    }

    getCurrentLanguage() {
        return this.currentLanguage;
    }

    getAvailableLanguages() {
        // This would typically be loaded from the server
        // For now, return hardcoded list
        return {
            'en': 'English',
            'es': 'Español',
            'ro': 'Română'
        };
    }

    dispatchLanguageChangeEvent() {
        const event = new CustomEvent('languageChanged', {
            detail: {
                language: this.currentLanguage,
                translations: this.translations[this.currentLanguage]
            }
        });
        document.dispatchEvent(event);
    }

    // Utility methods
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(';').shift();
        }
        return null;
    }

    setCookie(name, value, days) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
    }
}

// Create global instance
window.i18n = new I18n();

// Convenience function for translations
window._ = (key, variables) => window.i18n.translate(key, variables);

// Auto-translate elements with data-i18n attribute ONLY after translations are loaded
document.addEventListener('DOMContentLoaded', async () => {
    // Ensure current language is detected
    if (!window.i18n.currentLanguage) {
        window.i18n.currentLanguage = window.i18n.detectLanguage();
    }

    // Wait for translations to load before translating page
    await window.i18n.loadTranslations(window.i18n.currentLanguage);

    // Translate the page
    translatePage();

    // Dispatch event to signal i18n is ready
    const event = new CustomEvent('i18nReady', { detail: { language: window.i18n.currentLanguage } });
    document.dispatchEvent(event);
});

// Listen for language changes and retranslate page
document.addEventListener('languageChanged', () => {
    translatePage();
});

function translatePage() {
    // Find all elements with data-i18n attribute
    const elements = document.querySelectorAll('[data-i18n]');

    elements.forEach(element => {
        const key = element.getAttribute('data-i18n');

        // SKIP if element already has translated content (from server)
        // Only translate if content matches the translation key (not translated yet)
        if (element.textContent === key || element.textContent.trim() === '' || element.tagName === 'INPUT') {
            const variables = {};

            // Check for data-i18n-* attributes for variables
            Array.from(element.attributes).forEach(attr => {
                if (attr.name.startsWith('data-i18n-') && attr.name !== 'data-i18n') {
                    const varName = attr.name.replace('data-i18n-', '');
                    variables[varName] = attr.value;
                }
            });

            const translation = window.i18n.translate(key, variables);

            // Update text content or placeholder
            if (element.tagName === 'INPUT' && element.type === 'text') {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }

        }
    });
}

// Language selector functionality
function createLanguageSelector(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const select = document.createElement('select');
    select.className = 'form-select form-select-sm';
    select.id = 'language-selector';

    const languages = window.i18n.getAvailableLanguages();
    const currentLang = window.i18n.getCurrentLanguage();

    Object.entries(languages).forEach(([code, name]) => {
        const option = document.createElement('option');
        option.value = code;
        option.textContent = name;
        option.selected = code === currentLang;
        select.appendChild(option);
    });

    select.addEventListener('change', async (e) => {
        const newLanguage = e.target.value;
        await window.i18n.setLanguage(newLanguage);

        // Reload page to update server-side content
        const url = new URL(window.location);
        url.searchParams.set('lang', newLanguage);
        window.location.href = url.toString();
    });

    container.appendChild(select);
}
