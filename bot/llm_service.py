"""Simple LLaMA 3.2 integration for emotional support.

This is a FREE implementation using Ollama and LLaMA 3.2 running locally.
Perfect for students - no API costs!
"""
from typing import Dict, List
import asyncio
import logging
import aiohttp

from bot_config.llm_constants import (
    LLMSettings, SupportMessages, PromptTemplates, ResponseSettings
)

logger = logging.getLogger(__name__)


class LlamaEmotionalSupport:
    """Handles emotional support conversations using LLaMA 3.2"""
    
    def __init__(self):
        """Initialize the LLaMA service"""
        self.model = LLMSettings.DEFAULT_MODEL
        self.base_url = "http://localhost:11434"
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def is_available(self) -> bool:
        """Check if LLaMA service is available"""
        try:
            # Check if ollama is running and model is available
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get('models', [])
                        return any(model['name'].startswith(self.model.split(':')[0]) for model in models)
            return False
        except Exception as e:
            logger.error(f"Error checking LLaMA availability: {e}")
            return False
    
    async def generate_response(
        self, 
        user_message: str, 
        conversation_history: List[Dict[str, str]], 
        user_name: str
    ) -> str:
        """Generate a supportive response using LLaMA"""
        logger.info(f"LLM: Generating response for user '{user_name}'")
        
        if not await self.is_available():
            logger.warning("LLM: Service not available")
            return SupportMessages.SERVICE_UNAVAILABLE
            
        try:
            # Build context from conversation history
            context = self._build_context(conversation_history, user_name)
            
            # Create the prompt
            prompt = PromptTemplates.SUPPORT_PROMPT.format(
                context=context,
                user_message=user_message,
                user_name=user_name,
                max_paragraphs=ResponseSettings.MAX_RESPONSE_LENGTH
            )
            
            # Generate response using HTTP API
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": ResponseSettings.TEMPERATURE,
                        "num_predict": ResponseSettings.MAX_TOKENS,
                        "top_p": ResponseSettings.TOP_P,
                    }
                }
                
                logger.info(f"LLM: Sending request to {self.base_url}/api/generate")
                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        generated_text = data.get('response', '').strip()
                        
                        # Validate response
                        if not generated_text or len(generated_text) < 10:
                            logger.warning("LLM: Response too short, using fallback")
                            return SupportMessages.UNDERSTANDING_RESPONSE
                        
                        logger.info(f"LLM: Generated response of {len(generated_text)} chars")
                        return generated_text
                    else:
                        error_text = await response.text()
                        logger.error(f"LLaMA API error: {response.status} - {error_text}")
                        return SupportMessages.UNDERSTANDING_RESPONSE
            
        except Exception as e:
            logger.error(f"Error generating LLaMA response: {e}")
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


async def test_llama_connection():
    """Test if LLaMA is properly set up"""
    service = LlamaEmotionalSupport()
        
    if await service.is_available():
        print(f"✅ LLaMA {LLMSettings.DEFAULT_MODEL} is available and ready!")
        
        # Test generation
        test_response = await service.generate_response(
            "I'm feeling overwhelmed by my diabetes management",
            [],
            "Test User"
        )
        print(f"✅ Test response: {test_response[:100]}...")
    else:
        print(f"❌ LLaMA {LLMSettings.DEFAULT_MODEL} is not available.")
        print(f"   Please ensure Ollama is running and run: ollama pull {LLMSettings.DEFAULT_MODEL}")


if __name__ == "__main__":
    asyncio.run(test_llama_connection())