"""
Internationalization (i18n) system for the admin panel.

This module provides a simple but effective internationalization system
that supports multiple languages with JSON-based translation files.
"""

import json
import os
from typing import Dict, Optional, Any
from functools import lru_cache
from pathlib import Path
import threading


class SimpleI18n:
    """
    A simple internationalization system with the following features:
    - JSON-based translation files
    - Thread-safe translation loading
    - LRU cache for performance
    - Fallback to default language
    - Cookie-based language persistence
    """

    def __init__(
        self, 
        translations_dir: str = None, 
        default_language: str = "en"
    ):
        """
        Initialize the i18n system.

        Args:
            translations_dir: Directory containing translation JSON files
            default_language: Default language code (default: "en")
        """
        self.default_language = default_language

        # Set translations directory
        if translations_dir is None:
            self.translations_dir = Path(__file__).parent / "translations"
        else:
            self.translations_dir = Path(translations_dir)

        # Thread lock for safe loading
        self._lock = threading.Lock()

        # Cache for loaded translations
        self._translations_cache: Dict[str, Dict[str, Any]] = {}

        # Preload default language
        self._load_language(default_language)

    def _load_language(self, language_code: str) -> Dict[str, Any]:
        """
        Load translation file for a specific language.

        Args:
            language_code: Language code (e.g., "en", "es")

        Returns:
            Dictionary of translations
        """
        with self._lock:
            # Check cache first
            if language_code in self._translations_cache:
                return self._translations_cache[language_code]

            # Load translation file
            file_path = self.translations_dir / f"{language_code}.json"

            if not file_path.exists():
                # Fallback to default language
                if language_code != self.default_language:
                    return self._load_language(self.default_language)
                else:
                    # Return empty dict if default language not found
                    return {}

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
                    self._translations_cache[language_code] = translations
                    return translations
            except Exception:
                # Error loading translation file, return empty dict
                return {}

    @lru_cache(maxsize=1000)
    def translate(self, key: str, language: str = None, **kwargs) -> str:
        """
        Get translated text for a key.

        Args:
            key: Translation key (e.g., "common.welcome")
            language: Language code (uses default if None)
            **kwargs: Variables to interpolate in the translation

        Returns:
            Translated text or the key if translation not found
        """
        if language is None:
            language = self.default_language

        # Load translations for the language
        translations = self._load_language(language)

        # Navigate through nested keys (e.g., "common.welcome")
        keys = key.split('.')
        value = translations

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Try default language if key not found
                if language != self.default_language:
                    return self.translate(key, self.default_language, **kwargs)
                # Return key if not found in any language
                return key

        # If value is not a string, return the key
        if not isinstance(value, str):
            return key

        # Interpolate variables if provided
        if kwargs:
            try:
                return value.format(**kwargs)
            except:
                return value

        return value

    def get_available_languages(self) -> Dict[str, str]:
        """
        Get list of available languages.

        Returns:
            Dictionary of language codes to language names
        """
        languages = {}

        # Check for translation files
        if self.translations_dir.exists():
            for file_path in self.translations_dir.glob("*.json"):
                language_code = file_path.stem
                try:
                    # Load the file to get language name
                    translations = self._load_language(language_code)
                    language_name = translations.get(
                        "language", {}
                    ).get("name", language_code)
                    languages[language_code] = language_name
                except:
                    languages[language_code] = language_code

        # Ensure default language is always included
        if self.default_language not in languages:
            languages[self.default_language] = "English"

        return languages

    def clear_cache(self):
        """Clear all caches (useful for development)."""
        self.translate.cache_clear()
        with self._lock:
            self._translations_cache.clear()


# Global i18n instance - use static directory for translations
_admin_dir = Path(__file__).parent.parent
_translations_dir = _admin_dir / "static" / "i18n"
i18n = SimpleI18n(translations_dir=str(_translations_dir))

# Convenience function for translations
_ = i18n.translate