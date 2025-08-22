"""Google Gemini integration for emotional support.

This implementation uses Google's Gemini API (free tier) which provides
60 requests per minute and is perfect for deployment on Railway.
"""
from typing import Dict, List, Optional
import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from bot_config.llm_constants import (
    LLMSettings, SupportMessages, PromptTemplates, ResponseSettings
)

logger = logging.getLogger(__name__)


class GeminiEmotionalSupport:
    """Handles emotional support conversations using Google Gemini"""
    
    def __init__(self):
        """Initialize the Gemini service"""
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.model_name = "gemini-1.5-flash"  # Free tier model
        self.model = None
        self.last_initialized = None
        self.initialization_timeout = timedelta(hours=1)  # Reinitialize every hour
        self.request_timeout = 30  # 30 seconds timeout for API calls
        
        if self.api_key:
            logger.info("Gemini: API key found, initializing service...")
            self._configure_and_initialize()
        else:
            logger.warning("Gemini: API key not found in environment variables")
    
    def _configure_and_initialize(self):
        """Configure API and initialize model"""
        try:
            genai.configure(api_key=self.api_key)
            self._initialize_model()
            self.last_initialized = datetime.now()
            logger.info("Gemini: Service initialized successfully")
        except Exception as e:
            logger.error(f"Gemini: Failed to initialize - {type(e).__name__}: {str(e)}")
            self.model = None
            self.last_initialized = None
    
    def _should_reinitialize(self) -> bool:
        """Check if we should reinitialize the connection"""
        if not self.model:
            return True
        if not self.last_initialized:
            return True
        if datetime.now() - self.last_initialized > self.initialization_timeout:
            logger.info("Gemini: Connection is stale, will reinitialize")
            return True
        return False
    
    def _initialize_model(self):
        """Initialize the Gemini model with safety settings"""
        # Configure safety settings to allow medical/health discussions
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # Configure generation parameters
        generation_config = {
            "temperature": ResponseSettings.TEMPERATURE,
            "top_p": ResponseSettings.TOP_P,
            "max_output_tokens": ResponseSettings.MAX_TOKENS,
        }
        
        self.model = genai.GenerativeModel(
            self.model_name,
            safety_settings=safety_settings,
            generation_config=generation_config
        )
        
    async def is_available(self) -> bool:
        """Check if Gemini service is available"""
        if not self.api_key:
            logger.warning("Gemini: No API key available")
            return False
        
        # Check if we need to reinitialize
        if self._should_reinitialize():
            logger.info("Gemini: Reinitializing connection...")
            self._configure_and_initialize()
            
        if not self.model:
            return False
            
        try:
            # Quick test with timeout to check if API is working
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.model.generate_content("Hello, respond with 'OK'")
                ),
                timeout=10  # 10 second timeout for availability check
            )
            return bool(response.text)
        except asyncio.TimeoutError:
            logger.error("Gemini: Availability check timed out")
            self.model = None  # Force reinitialization next time
            return False
        except Exception as e:
            logger.error(f"Gemini availability check failed: {type(e).__name__}: {str(e)}")
            self.model = None  # Force reinitialization next time
            return False
    
    async def generate_response(
        self, 
        user_message: str, 
        conversation_history: List[Dict[str, str]], 
        user_name: str,
        language: str = 'English'
    ) -> str:
        """Generate a supportive response using Gemini"""
        logger.info(f"Gemini: Generating response for user '{user_name}' in {language}")
        
        # Check if we need to reinitialize before generating response
        if self._should_reinitialize():
            logger.info("Gemini: Reinitializing before generating response...")
            self._configure_and_initialize()
        
        if not self.model:
            logger.error("Gemini: Model not available after reinitialization attempt")
            return SupportMessages.SERVICE_UNAVAILABLE
            
        try:
            # Build context from conversation history
            context = self._build_context(conversation_history, user_name)
            
            # Create the prompt
            prompt = PromptTemplates.SUPPORT_PROMPT.format(
                context=context,
                user_message=user_message,
                user_name=user_name,
                max_paragraphs=ResponseSettings.MAX_RESPONSE_LENGTH,
                language=language
            )
            
            logger.debug(f"Gemini: Sending request to API with {self.request_timeout}s timeout...")
            
            # Generate response with timeout
            try:
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.model.generate_content(prompt)
                    ),
                    timeout=self.request_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Gemini: Request timed out after {self.request_timeout} seconds")
                # Force reinitialization for next request
                self.model = None
                self.last_initialized = None
                return SupportMessages.SERVICE_UNAVAILABLE
            
            if response and response.text:
                generated_text = response.text.strip()
                
                # Validate response
                if len(generated_text) < 10:
                    logger.warning("Gemini: Response too short, using fallback")
                    return SupportMessages.UNDERSTANDING_RESPONSE
                
                logger.info(f"Gemini: Successfully generated response of {len(generated_text)} chars")
                return generated_text
            else:
                logger.warning("Gemini: Empty response received from API")
                return SupportMessages.UNDERSTANDING_RESPONSE
                
        except Exception as e:
            logger.error(f"Gemini response generation error: {type(e).__name__}: {str(e)}")
            
            # Reset model on certain errors
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['quota', 'invalid', 'unauthorized', 'forbidden']):
                logger.error("Gemini: Critical error detected, resetting model")
                self.model = None
                self.last_initialized = None
            
            # Try to provide more specific error info
            if "quota" in error_str:
                logger.error("Gemini: API quota exceeded")
            elif "api" in error_str and "key" in error_str:
                logger.error("Gemini: API key issue detected")
            elif "network" in error_str or "connection" in error_str:
                logger.error("Gemini: Network/connection issue")
                
            return SupportMessages.UNDERSTANDING_RESPONSE
    
    def _build_context(self, conversation_history: List[Dict[str, str]], user_name: str) -> str:
        """Build conversation context for the prompt"""
        if not conversation_history:
            return "This is the start of the conversation."
            
        # Take last N messages
        recent_history = conversation_history[-LLMSettings.MAX_CONVERSATION_HISTORY:]
        
        context_parts = []
        for msg in recent_history:
            role = "User" if msg['role'] == 'user' else "Assistant"
            context_parts.append(f"{role}: {msg['content']}")
            
        return "\n".join(context_parts)


# Create a single instance to reuse
_gemini_instance = None
_instance_created_at = None
_instance_lifetime = timedelta(hours=6)  # Create new instance every 6 hours

def get_llm_service():
    """Get or create the LLM service instance with automatic refresh"""
    global _gemini_instance, _instance_created_at
    
    # Check if we need a new instance
    should_create_new = (
        _gemini_instance is None or
        _instance_created_at is None or
        datetime.now() - _instance_created_at > _instance_lifetime
    )
    
    if should_create_new:
        logger.info("Creating new Gemini service instance")
        _gemini_instance = GeminiEmotionalSupport()
        _instance_created_at = datetime.now()
    
    return _gemini_instance


async def test_gemini_connection():
    """Test if Gemini is properly set up"""
    service = get_llm_service()
        
    if await service.is_available():
        print(f"✅ Google Gemini ({service.model_name}) is available and ready!")
        
        # Test generation
        test_response = await service.generate_response(
            "I'm feeling overwhelmed by my diabetes management",
            [],
            "Test User",
            "English"
        )
        print(f"✅ Test response: {test_response[:100]}...")
    else:
        print(f"❌ Google Gemini is not available.")
        print(f"   Please ensure GOOGLE_API_KEY is set in your environment variables")


if __name__ == "__main__":
    asyncio.run(test_gemini_connection())