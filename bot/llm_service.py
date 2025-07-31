"""Google Gemini integration for emotional support.

This implementation uses Google's Gemini API (free tier) which provides
60 requests per minute and is perfect for deployment on Railway.
"""
from typing import Dict, List
import asyncio
import logging
import os
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
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self._initialize_model()
        else:
            logger.warning("Google API key not found in environment variables")
    
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
        if not self.api_key or not self.model:
            return False
            
        try:
            # Quick test to check if API is working
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content("Hello, respond with 'OK'")
            )
            return bool(response.text)
        except Exception as e:
            logger.error(f"Error checking Gemini availability: {e}")
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
        
        if not self.model:
            logger.warning("Gemini: Model not initialized")
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
            
            # Generate response (run in executor to avoid blocking)
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            if response and response.text:
                generated_text = response.text.strip()
                
                # Validate response
                if len(generated_text) < 10:
                    logger.warning("Gemini: Response too short, using fallback")
                    return SupportMessages.UNDERSTANDING_RESPONSE
                
                logger.info(f"Gemini: Generated response of {len(generated_text)} chars")
                return generated_text
            else:
                logger.warning("Gemini: Empty response received")
                return SupportMessages.UNDERSTANDING_RESPONSE
                
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
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

def get_llm_service():
    """Get or create the LLM service instance"""
    global _gemini_instance
    if _gemini_instance is None:
        _gemini_instance = GeminiEmotionalSupport()
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