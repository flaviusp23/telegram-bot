"""
FastAPI middleware for internationalization.

This middleware handles:
- Language detection from cookies, headers, and query parameters
- Setting the current language in the request state
- Managing language preferences via cookies
"""


from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.responses import Response

from admin.i18n import i18n

class I18nMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle language detection and persistence.
    
    Language detection priority:
    1. Query parameter (?lang=es)
    2. Cookie (preferred_language)
    3. Accept-Language header
    4. Default language
    """
    
    def __init__(self, app: ASGIApp, default_language: str = "en", cookie_name: str = "preferred_language"):
        super().__init__(app)
        self.default_language = default_language
        self.cookie_name = cookie_name
        
    async def dispatch(self, request: Request, call_next):
        # Detect language from various sources
        language = self.detect_language(request)
        
        # Store language in request state for easy access
        request.state.language = language
        
        # Process the request
        response = await call_next(request)
        
        # If language was explicitly set via query param, update cookie
        query_lang = request.query_params.get("lang")
        if query_lang and query_lang in i18n.get_available_languages():
            response.set_cookie(
                key=self.cookie_name,
                value=query_lang,
                max_age=60 * 60 * 24 * 365,  # 1 year
                httponly=True,
                samesite="lax",
                secure=request.url.scheme == "https"
            )
            
        return response
    
    def detect_language(self, request: Request) -> str:
        """
        Detect the user's preferred language.
        
        Priority order:
        1. Query parameter (?lang=es)
        2. Cookie
        3. Accept-Language header
        4. Default language
        """
        available_languages = i18n.get_available_languages()
        
        # 1. Check query parameter
        query_lang = request.query_params.get("lang")
        if query_lang and query_lang in available_languages:
            return query_lang
        
        # 2. Check cookie
        cookie_lang = request.cookies.get(self.cookie_name)
        if cookie_lang and cookie_lang in available_languages:
            return cookie_lang
        
        # 3. Check Accept-Language header
        accept_language = request.headers.get("accept-language", "")
        if accept_language:
            # Parse the header and find the best match
            for lang_spec in accept_language.split(","):
                lang_code = lang_spec.split(";")[0].strip().split("-")[0]
                if lang_code in available_languages:
                    return lang_code
        
        # 4. Return default language
        return self.default_language


def get_current_language(request: Request) -> str:
    """
    Get the current language from the request.
    
    This is a dependency that can be used in FastAPI routes.
    """
    if hasattr(request, 'state') and hasattr(request.state, 'language'):
        return request.state.language
    return "en"


def translate(key: str, request: Request, **kwargs) -> str:
    """
    Translate a key using the current request's language.
    
    This is a convenience function for use in routes.
    """
    language = get_current_language(request)
    return i18n.translate(key, language, **kwargs)