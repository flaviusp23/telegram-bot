"""LLM-specific constants for the diabetes monitoring system"""

class LLMSettings:
    """Constants for LLM service configuration"""
    # Model settings
    DEFAULT_MODEL = "llama3.2"
    
    # Conversation settings
    MAX_CONVERSATION_HISTORY = 5  # Number of previous messages to include in context
    MAX_RESPONSE_LENGTH = 3  # Maximum paragraphs in response
    
    # System prompt settings
    MAX_DDS2_SCORE = 12
    MIN_DDS2_SCORE = 2
    
    # Conversation limits
    REMINDER_AFTER_EXCHANGES = 6  # Remind about /done after this many exchanges
    MAX_CONVERSATION_LENGTH = 20  # Maximum conversation history entries
    
    # Timeouts and retries
    RESPONSE_TIMEOUT = 30  # Seconds to wait for LLM response
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1  # Seconds between retries
    
    # Message character limits
    MAX_USER_MESSAGE_LENGTH = 2000
    MAX_AI_RESPONSE_LENGTH = 5000


class PromptTemplates:
    """System prompt templates"""
    SUPPORT_PROMPT = """You are a compassionate diabetes support assistant helping {user_name}.

Context of conversation:
{context}

User's current message: {user_message}

Please provide empathetic support in {max_paragraphs} paragraphs or less. Remember:
- Be warm and understanding
- Never give medical advice
- Encourage professional help for serious concerns
- Focus on emotional support and coping strategies

IMPORTANT: Respond in {language}. The user prefers to communicate in {language}.
"""


class ResponseSettings:
    """Response configuration settings"""
    TEMPERATURE = 0.7
    MAX_TOKENS = 500
    TOP_P = 0.9
    MAX_RESPONSE_LENGTH = 3


class LLMPrompts:
    """System prompts and templates for LLM"""
    
    # Base system prompt template
    BASE_SYSTEM_PROMPT = """You are a compassionate diabetes support assistant. 
        The user has completed the DDS-2 questionnaire with a score of {dds2_score}/12, 
        indicating {distress_level} diabetes distress.
        
        Important guidelines:
        - Provide emotional support and understanding
        - Never give medical advice or medication recommendations
        - Encourage professional help for serious concerns
        - Be warm, empathetic, and non-judgmental
        - Keep responses concise (2-3 paragraphs max)
        - If user mentions suicide or self-harm, strongly encourage immediate professional help
        """
    
    # Language-specific instructions
    LANGUAGE_INSTRUCTIONS = {
        'es': "\n- Respond in Spanish",
        'en': ""  # Default is English
    }
    
    # Distress level specific guidance
    HIGH_DISTRESS_GUIDANCE = """
        - This user has HIGH distress - be extra supportive
        - Acknowledge their struggles
        - Suggest simple, achievable coping strategies
        - Gently recommend talking to their healthcare team
        """
    
    MODERATE_DISTRESS_GUIDANCE = """
        - This user has MODERATE distress - be understanding
        - Validate their feelings
        - Offer practical coping tips
        - Encourage self-care
        """
    
    LOW_DISTRESS_GUIDANCE = """
        - This user has LOW distress - celebrate their success
        - Reinforce positive coping strategies
        - Encourage maintaining good habits
        """


class ConversationStates:
    """States for emotional support conversation"""
    CHATTING = 1
    ENDED = 2


class SupportMessages:
    """Messages specific to emotional support features"""
    
    # Fallback responses
    SERVICE_UNAVAILABLE = (
        "I'm sorry, but the emotional support service is temporarily unavailable. "
        "Please remember that you're not alone in managing diabetes. "
        "Consider reaching out to your healthcare team or a trusted friend for support."
    )
    
    UNDERSTANDING_RESPONSE = (
        "I hear you and I understand this can be challenging. "
        "Managing diabetes isn't easy, and it's completely normal to feel overwhelmed sometimes. "
        "Remember, you're doing your best, and that's what matters."
    )
    
    # Initial prompts by distress level
    INITIAL_PROMPTS = {
        'high': {
            'en': ("I noticed you're experiencing high diabetes distress. "
                  "I'm here to listen and provide support. "
                  "What aspect of managing diabetes is most challenging for you right now?"),
            'es': ("Veo que estás experimentando un alto nivel de angustia por la diabetes. "
                  "Estoy aquí para escucharte y brindarte apoyo. "
                  "¿Qué aspecto del manejo de la diabetes es más desafiante para ti en este momento?"),
            'ro': ("Am observat că experimentezi un nivel ridicat de stres din cauza diabetului. "
                  "Sunt aici să te ascult și să îți ofer sprijin. "
                  "Care aspect al gestionării diabetului este cel mai dificil pentru tine acum?")
        },
        'moderate': {
            'en': ("I see you're dealing with some diabetes-related challenges. "
                  "It's completely normal to feel this way sometimes. "
                  "What's on your mind today?"),
            'es': ("Veo que estás lidiando con algunos desafíos relacionados con la diabetes. "
                  "Es completamente normal sentirse así a veces. "
                  "¿Qué tienes en mente hoy?"),
            'ro': ("Văd că te confrunți cu unele provocări legate de diabet. "
                  "Este complet normal să te simți așa uneori. "
                  "La ce te gândești astăzi?")
        },
        'low': {
            'en': ("It's great that your diabetes distress is relatively low! "
                  "Is there anything specific you'd like to talk about or any tips you'd like to share?"),
            'es': ("¡Es genial que tu angustia por la diabetes sea relativamente baja! "
                  "¿Hay algo específico de lo que te gustaría hablar o algún consejo que te gustaría compartir?"),
            'ro': ("Este minunat că stresul tău legat de diabet este relativ scăzut! "
                  "Există ceva specific despre care ai vrea să vorbești sau vreun sfat pe care ai vrea să-l împărtășești?")
        }
    }
    
    # Conversation instructions
    CHAT_INSTRUCTIONS = (
        "💬 You can chat with me about your diabetes-related feelings.\n"
        "Send /done when you want to end the conversation."
    )
    
    # Reminder message
    DONE_REMINDER = "💡 Remember: Send /done whenever you're ready to end our chat."
    
    # End conversation keywords
    END_KEYWORDS = ['/done', 'done', 'exit', 'bye', 'goodbye', 'quit']
    
    # Thank you message
    CONVERSATION_END_MESSAGE = (
        "Thank you for sharing with me today. 💙\n\n"
        "Remember:\n"
        "• You're not alone in this journey\n"
        "• It's okay to have difficult days\n"
        "• Your healthcare team is there to help\n\n"
        "You can use /support anytime you need to talk."
    )
    
    # Error messages
    LLM_CONNECTION_ERROR = (
        "I'm having trouble connecting right now. "
        "Please remember you're not alone in managing diabetes. "
        "Consider reaching out to your healthcare team for support."
    )
    
    TECHNICAL_ERROR = (
        "I'm having some technical difficulties. "
        "Please try again or contact your healthcare provider for support."
    )
    
    # Support offer after high DDS-2
    HIGH_DISTRESS_OFFER = (
        "I notice you're experiencing significant diabetes distress. "
        "Would you like to chat with our AI support assistant?"
    )
    
    SUPPORT_DECLINED = (
        "That's okay. Remember, support is always available with /support command. "
        "Take care of yourself! 💙"
    )
    
    # Ollama specific messages
    OLLAMA_NOT_RUNNING = "Ollama not running? Error: {error}"
    LLAMA_NOT_FOUND = "LLaMA 3.2 not found! Run: ollama pull {model}"
    
    # Test messages
    TEST_SUCCESS = "✅ LLaMA 3.2 is working!"
    TEST_FAILURE = "❌ LLaMA 3.2 error: {error}"
    TEST_INSTRUCTIONS = "Make sure Ollama is running and you've pulled llama3.2"


class ExampleScenarios:
    """Example scenarios for testing and documentation"""
    SUPPORT_EXAMPLES = {
        'overwhelmed': {
            'user': "I feel so overwhelmed by having to check my blood sugar all the time",
            'context': {'dds2_score': 10, 'distress_level': 'high'},
            'expected': "Understanding, validation, simple coping strategies"
        },
        'failing': {
            'user': "I keep forgetting to take my medication and feel like a failure",
            'context': {'dds2_score': 8, 'distress_level': 'moderate'},
            'expected': "Non-judgmental support, practical tips for remembering"
        },
        'success': {
            'user': "I've been managing well but sometimes I still worry",
            'context': {'dds2_score': 4, 'distress_level': 'low'},
            'expected': "Positive reinforcement, normalize occasional worry"
        }
    }
    
    # Test context
    DEFAULT_TEST_CONTEXT = {
        'dds2_score': 8,
        'distress_level': 'moderate',
        'language': 'en'
    }
    
    TEST_USER_MESSAGE = "I'm struggling with my diabetes routine"