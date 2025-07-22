"""
Jinja2 template integration for internationalization.

This module provides template functions and filters for i18n support.
"""

from typing import Any, Dict, Optional
from jinja2 import Environment
from fastapi import Request

from admin.i18n import i18n
from admin.i18n.middleware import get_current_language


def setup_i18n_jinja2(env: Environment):
    """
    Setup i18n functions and filters for Jinja2 environment.
    
    Adds the following to templates:
    - _() function for translation
    - get_available_languages() function
    - current_language variable (requires request context)
    """
    
    # Make these functions available globally but they will be overridden by context
    def fallback_translate(key: str, **kwargs) -> str:
        """Fallback translation function when no context is available."""
        return i18n.translate(key, i18n.default_language, **kwargs)
    
    def get_available_languages_function() -> Dict[str, str]:
        """Template function to get available languages."""
        return i18n.get_available_languages()
    
    def get_current_language_function() -> str:
        """Fallback current language function.""" 
        return i18n.default_language
    
    # Add functions to Jinja2 environment - these are fallbacks
    # The actual functions will be provided via template context
    env.globals.setdefault('_', fallback_translate)
    env.globals.setdefault('get_available_languages', get_available_languages_function)  
    env.globals.setdefault('get_current_language', get_current_language_function)


def create_template_context(request: Request) -> Dict[str, Any]:
    """
    Create template context with i18n variables and functions.
    
    This should be used when rendering templates to ensure
    i18n functions have access to the current request.
    """
    current_lang = get_current_language(request)
    
    # Create a translation function bound to current language
    def translate_bound(key: str, **kwargs) -> str:
        return i18n.translate(key, current_lang, **kwargs)
    
    def get_current_lang() -> str:
        return current_lang
        
    return {
        'request': request,
        'current_language': current_lang,
        'available_languages': i18n.get_available_languages(),
        '_': translate_bound,  # Translation function
        'get_current_language': get_current_lang,
        'get_available_languages': lambda: i18n.get_available_languages()
    }