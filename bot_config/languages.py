"""Multi-language support for the diabetes monitoring bot"""

class Languages:
    """Supported languages"""
    ENGLISH = 'en'
    SPANISH = 'es'
    ROMANIAN = 'ro'
    
    SUPPORTED = [ENGLISH, SPANISH, ROMANIAN]
    
    NAMES = {
        ENGLISH: 'English',
        SPANISH: 'Español',
        ROMANIAN: 'Română'
    }
    
    FLAGS = {
        ENGLISH: '🇬🇧',
        SPANISH: '🇪🇸',
        ROMANIAN: '🇷🇴'
    }


class Messages:
    """All bot messages in multiple languages"""
    
    # Start command messages
    WELCOME_BACK = {
        'en': "Welcome back, {first_name}! 👋\n\nI'm here to help you manage diabetes-related distress.\nUse /help to see available commands.",
        'es': "¡Bienvenido de nuevo, {first_name}! 👋\n\nEstoy aquí para ayudarte a manejar el estrés relacionado con la diabetes.\nUsa /help para ver los comandos disponibles.",
        'ro': "Bine ai revenit, {first_name}! 👋\n\nSunt aici să te ajut să gestionezi stresul legat de diabet.\nFolosește /help pentru a vedea comenzile disponibile."
    }
    
    WELCOME_NEW = {
        'en': "Hello {first_name}! 👋\n\nI'm a diabetes monitoring assistant designed to help track and manage diabetes-related distress.\n\nTo get started, please register using /register",
        'es': "¡Hola {first_name}! 👋\n\nSoy un asistente de monitoreo de diabetes diseñado para ayudar a rastrear y manejar el estrés relacionado con la diabetes.\n\nPara comenzar, regístrate usando /register",
        'ro': "Salut {first_name}! 👋\n\nSunt un asistent de monitorizare a diabetului conceput pentru a ajuta la urmărirea și gestionarea stresului legat de diabet.\n\nPentru a începe, te rog să te înregistrezi folosind /register"
    }
    
    # Registration messages
    ALREADY_REGISTERED = {
        'en': "You're already registered, {first_name}! ✅",
        'es': "¡Ya estás registrado, {first_name}! ✅",
        'ro': "Ești deja înregistrat, {first_name}! ✅"
    }
    
    REGISTRATION_SUCCESS = {
        'en': "Registration successful! 🎉\n\nWelcome {first_name}!\n\nYou'll receive questionnaires at scheduled times to help monitor your diabetes-related distress.\n\nUse /help to see available commands.",
        'es': "¡Registro exitoso! 🎉\n\n¡Bienvenido {first_name}!\n\nRecibirás cuestionarios en horarios programados para ayudar a monitorear tu estrés relacionado con la diabetes.\n\nUsa /help para ver los comandos disponibles.",
        'ro': "Înregistrare reușită! 🎉\n\nBine ai venit {first_name}!\n\nVei primi chestionare la ore programate pentru a ajuta la monitorizarea stresului legat de diabet.\n\nFolosește /help pentru a vedea comenzile disponibile."
    }
    
    REGISTRATION_ERROR = {
        'en': "Sorry, there was an error during registration. Please try again later.",
        'es': "Lo siento, hubo un error durante el registro. Por favor, inténtalo de nuevo más tarde.",
        'ro': "Ne pare rău, a apărut o eroare în timpul înregistrării. Te rog să încerci din nou mai târziu."
    }
    
    # Language selection
    LANGUAGE_SELECTION = {
        'en': "Please select your preferred language:",
        'es': "Por favor selecciona tu idioma preferido:",
        'ro': "Te rog selectează limba preferată:"
    }
    
    LANGUAGE_CHANGED = {
        'en': "Language changed to English! 🇬🇧",
        'es': "¡Idioma cambiado a Español! 🇪🇸",
        'ro': "Limba schimbată în Română! 🇷🇴"
    }
    
    REGISTER_PROMPT = {
        'en': "To get started, please use the /register command to create your account.",
        'es': "Para comenzar, por favor usa el comando /register para crear tu cuenta.",
        'ro': "Pentru a începe, te rog folosește comanda /register pentru a-ți crea contul."
    }
    
    # Help command
    HELP_TEXT = {
        'en': """Available commands:

/start - Start the bot
/register - Register as a new user
/status - Check your registration status
/language - Change language
/pause - Pause automatic questionnaires
/resume - Resume automatic questionnaires
/questionnaire - Complete the DDS-2 questionnaire
/support - Chat with AI emotional support assistant
/export - Export your data (XML + graphs)
/health - Check bot health status
/help - Show this help message

🤖 AI Support: After completing each questionnaire, you'll be offered a chance to chat with our AI assistant powered by LLaMA 3.2 for emotional support.

The questionnaire uses the validated DDS-2 scale:
• 2 questions about diabetes distress
• Scale from 1 (not a problem) to 6 (serious problem)""",
        
        'es': """Comandos disponibles:

/start - Iniciar el bot
/register - Registrarse como nuevo usuario
/status - Verificar tu estado de registro
/language - Cambiar idioma
/pause - Pausar cuestionarios automáticos
/resume - Reanudar cuestionarios automáticos
/questionnaire - Completar el cuestionario DDS-2
/support - Chatear con el asistente de apoyo emocional IA
/export - Exportar tus datos (XML + gráficos)
/health - Verificar estado del bot
/help - Mostrar este mensaje de ayuda

🤖 Apoyo IA: Después de completar cada cuestionario, se te ofrecerá la oportunidad de chatear con nuestro asistente IA impulsado por LLaMA 3.2 para apoyo emocional.

El cuestionario usa la escala validada DDS-2:
• 2 preguntas sobre el estrés de la diabetes
• Escala del 1 (no es un problema) al 6 (problema grave)""",
        
        'ro': """Comenzi disponibile:

/start - Pornește bot-ul
/register - Înregistrează-te ca utilizator nou
/status - Verifică starea înregistrării
/language - Schimbă limba
/pause - Întrerupe chestionarele automate
/resume - Reia chestionarele automate
/questionnaire - Completează chestionarul DDS-2
/support - Discută cu asistentul AI de suport emoțional
/export - Exportă datele tale (XML + grafice)
/health - Verifică starea bot-ului
/help - Afișează acest mesaj de ajutor

🤖 Suport AI: După completarea fiecărui chestionar, ți se va oferi șansa să discuți cu asistentul nostru AI alimentat de LLaMA 3.2 pentru suport emoțional.

Chestionarul folosește scala validată DDS-2:
• 2 întrebări despre stresul diabetului
• Scală de la 1 (nu e o problemă) la 6 (problemă gravă)"""
    }
    
    # DDS-2 Questionnaire messages
    DDS2_INTRO = {
        'en': "Hello {user_name}! 👋\n\nTime for your diabetes distress check.\n\nI'll ask you 2 quick questions about how diabetes has been affecting you.\nPlease rate each on a scale from 1 to 6:\n• 1 = Not a problem\n• 6 = Very serious problem",
        'es': "¡Hola {user_name}! 👋\n\nEs hora de tu verificación de estrés por diabetes.\n\nTe haré 2 preguntas rápidas sobre cómo te ha estado afectando la diabetes.\nPor favor califica cada una en una escala del 1 al 6:\n• 1 = No es un problema\n• 6 = Problema muy grave",
        'ro': "Salut {user_name}! 👋\n\nE timpul pentru verificarea stresului cauzat de diabet.\n\nÎți voi pune 2 întrebări rapide despre cum te-a afectat diabetul.\nTe rog să evaluezi fiecare pe o scală de la 1 la 6:\n• 1 = Nu e o problemă\n• 6 = Problemă foarte gravă"
    }
    
    DDS2_Q1_OVERWHELMED = {
        'en': "📊 **QUESTION 1 OF 2** 📊\n━━━━━━━━━━━━━━━\n\n❓ Feeling overwhelmed by the demands of living with diabetes\n\n⬇️ How much of a problem is this for you?",
        'es': "📊 **PREGUNTA 1 DE 2** 📊\n━━━━━━━━━━━━━━━\n\n❓ Sentirse agobiado por las exigencias de vivir con diabetes\n\n⬇️ ¿Qué tanto problema es esto para ti?",
        'ro': "📊 **ÎNTREBAREA 1 DIN 2** 📊\n━━━━━━━━━━━━━━━\n\n❓ Te simți copleșit de cerințele vieții cu diabet\n\n⬇️ Cât de mare este această problemă pentru tine?"
    }
    
    DDS2_Q2_FAILING = {
        'en': "📊 **QUESTION 2 OF 2** 📊\n━━━━━━━━━━━━━━━\n\n❓ Feeling that I am often failing with my diabetes regimen\n\n⬇️ How much of a problem is this for you?",
        'es': "📊 **PREGUNTA 2 DE 2** 📊\n━━━━━━━━━━━━━━━\n\n❓ Sentir que a menudo estoy fallando con mi rutina de diabetes\n\n⬇️ ¿Qué tanto problema es esto para ti?",
        'ro': "📊 **ÎNTREBAREA 2 DIN 2** 📊\n━━━━━━━━━━━━━━━\n\n❓ Sentimentul că deseori eșuez cu regimul meu de diabet\n\n⬇️ Cât de mare este această problemă pentru tine?"
    }
    
    # Transition message between questions
    DDS2_TRANSITION = {
        'en': "✅ Thank you! Moving to the final question...",
        'es': "✅ ¡Gracias! Pasando a la última pregunta...",
        'ro': "✅ Mulțumesc! Trecem la ultima întrebare..."
    }
    
    # DDS-2 Response messages
    DDS2_LOW_DISTRESS_RESPONSE = {
        'en': "Thank you for completing the questionnaire! 😊\n\nYour responses indicate low diabetes distress. That's great!\nKeep up the good work with your diabetes management.\n\nI'll check in with you again at the next scheduled time.",
        'es': "¡Gracias por completar el cuestionario! 😊\n\nTus respuestas indican bajo estrés por diabetes. ¡Eso es genial!\nSigue con el buen trabajo en el manejo de tu diabetes.\n\nVolveré a contactarte en el próximo horario programado.",
        'ro': "Mulțumesc că ai completat chestionarul! 😊\n\nRăspunsurile tale indică un nivel scăzut de stres legat de diabet. Este minunat!\nContinuă cu munca bună în gestionarea diabetului.\n\nTe voi contacta din nou la următoarea oră programată."
    }
    
    DDS2_MODERATE_DISTRESS_RESPONSE = {
        'en': "Thank you for completing the questionnaire. 💙\n\nYour responses indicate moderate diabetes distress.\nIt's normal to feel challenged by diabetes management sometimes.\n\nConsider taking some time for self-care today.",
        'es': "Gracias por completar el cuestionario. 💙\n\nTus respuestas indican estrés moderado por diabetes.\nEs normal sentirse desafiado por el manejo de la diabetes a veces.\n\nConsidera tomar algo de tiempo para el autocuidado hoy.",
        'ro': "Mulțumesc că ai completat chestionarul. 💙\n\nRăspunsurile tale indică un nivel moderat de stres legat de diabet.\nEste normal să te simți provocat de gestionarea diabetului uneori.\n\nIa în considerare să îți acorzi timp pentru îngrijire personală astăzi."
    }
    
    DDS2_HIGH_DISTRESS_RESPONSE = {
        'en': "Thank you for sharing your feelings. 🫂\n\nYour responses indicate high diabetes distress.\nPlease consider reaching out to your healthcare team for support.\n\nRemember, you don't have to manage this alone.",
        'es': "Gracias por compartir tus sentimientos. 🫂\n\nTus respuestas indican alto estrés por diabetes.\nPor favor considera contactar a tu equipo de salud para obtener apoyo.\n\nRecuerda, no tienes que manejar esto solo.",
        'ro': "Mulțumesc că ți-ai împărtășit sentimentele. 🫂\n\nRăspunsurile tale indică un nivel ridicat de stres legat de diabet.\nTe rog să iei în considerare să contactezi echipa ta medicală pentru suport.\n\nAmintește-ți, nu trebuie să gestionezi asta singur."
    }
    
    # Button labels
    BUTTON_LABELS = {
        'dds2_1': {'en': '1 - Not a problem', 'es': '1 - No es problema', 'ro': '1 - Nu e problemă'},
        'dds2_2': {'en': '2 - Slight problem', 'es': '2 - Problema leve', 'ro': '2 - Problemă ușoară'},
        'dds2_3': {'en': '3 - Moderate problem', 'es': '3 - Problema moderada', 'ro': '3 - Problemă moderată'},
        'dds2_4': {'en': '4 - Somewhat serious', 'es': '4 - Algo grave', 'ro': '4 - Oarecum gravă'},
        'dds2_5': {'en': '5 - Serious problem', 'es': '5 - Problema grave', 'ro': '5 - Problemă gravă'},
        'dds2_6': {'en': '6 - Very serious', 'es': '6 - Muy grave', 'ro': '6 - Foarte gravă'}
    }
    
    # Support messages
    CHAT_INSTRUCTIONS = {
        'en': "💬 You can chat with me about your diabetes-related feelings.\nSend /done when you want to end the conversation.",
        'es': "💬 Puedes chatear conmigo sobre tus sentimientos relacionados con la diabetes.\nEnvía /done cuando quieras terminar la conversación.",
        'ro': "💬 Poți discuta cu mine despre sentimentele tale legate de diabet.\nTrimite /done când vrei să închei conversația."
    }
    
    SERVICE_UNAVAILABLE = {
        'en': "I'm sorry, but the emotional support service is temporarily unavailable. Please remember that you're not alone in managing diabetes. Consider reaching out to your healthcare team or a trusted friend for support.",
        'es': "Lo siento, pero el servicio de apoyo emocional no está disponible temporalmente. Recuerda que no estás solo en el manejo de la diabetes. Considera contactar a tu equipo de salud o un amigo de confianza para obtener apoyo.",
        'ro': "Îmi pare rău, dar serviciul de suport emoțional este temporar indisponibil. Te rog să îți amintești că nu ești singur în gestionarea diabetului. Consideră să contactezi echipa ta medicală sau un prieten de încredere pentru suport."
    }
    
    # Common messages
    NOT_REGISTERED = {
        'en': "You're not registered yet. Use /register to get started!",
        'es': "Aún no estás registrado. ¡Usa /register para comenzar!",
        'ro': "Nu ești încă înregistrat. Folosește /register pentru a începe!"
    }
    
    ERROR_OCCURRED = {
        'en': "An error occurred. Please try again.",
        'es': "Ocurrió un error. Por favor intenta de nuevo.",
        'ro': "A apărut o eroare. Te rog încearcă din nou."
    }
    
    # Export messages
    EXPORT_GENERATING = {
        'en': "📊 Generating your data export...\n\nThis may take a moment. I'll send you:\n• XML file with your responses\n• Visual graphs showing your progress",
        'es': "📊 Generando tu exportación de datos...\n\nEsto puede tomar un momento. Te enviaré:\n• Archivo XML con tus respuestas\n• Gráficos visuales mostrando tu progreso",
        'ro': "📊 Generez exportul datelor tale...\n\nAceasta poate dura un moment. Îți voi trimite:\n• Fișier XML cu răspunsurile tale\n• Grafice vizuale care arată progresul tău"
    }
    
    EXPORT_SUCCESS = {
        'en': "✅ Export complete!\n\nYour data has been exported successfully.",
        'es': "✅ ¡Exportación completa!\n\nTus datos han sido exportados exitosamente.",
        'ro': "✅ Export complet!\n\nDatele tale au fost exportate cu succes."
    }
    
    EXPORT_NO_DATA = {
        'en': "📭 No data to export.\n\nYou haven't completed any questionnaires yet.",
        'es': "📭 No hay datos para exportar.\n\nAún no has completado ningún cuestionario.",
        'ro': "📭 Nu există date de exportat.\n\nÎncă nu ai completat niciun chestionar."
    }
    
    EXPORT_ERROR = {
        'en': "❌ Export failed.\n\nThere was an error exporting your data. Please try again later.",
        'es': "❌ Exportación fallida.\n\nHubo un error al exportar tus datos. Por favor intenta más tarde.",
        'ro': "❌ Exportul a eșuat.\n\nA apărut o eroare la exportarea datelor. Te rog încearcă mai târziu."
    }
    
    # Support conversation messages
    CONVERSATION_CANCELLED = {
        'en': "Conversation cancelled. Feel free to use /support whenever you need to talk.",
        'es': "Conversación cancelada. Siéntete libre de usar /support cuando necesites hablar.",
        'ro': "Conversație anulată. Folosește /support oricând ai nevoie să vorbești."
    }
    
    STARTING_SUPPORT_CHAT = {
        'en': "Starting emotional support chat...",
        'es': "Iniciando chat de apoyo emocional...",
        'ro': "Pornesc chat-ul de suport emoțional..."
    }
    
    # Support buttons
    SUPPORT_BUTTON_YES = {
        'en': "Yes, I'd like support",
        'es': "Sí, me gustaría apoyo",
        'ro': "Da, aș dori suport"
    }
    
    SUPPORT_BUTTON_NO = {
        'en': "No, thank you",
        'es': "No, gracias",
        'ro': "Nu, mulțumesc"
    }
    
    SUPPORT_BUTTON_CHAT = {
        'en': "💬 Chat with AI Support",
        'es': "💬 Chatear con IA de Apoyo",
        'ro': "💬 Discută cu AI de Suport"
    }
    
    SUPPORT_BUTTON_NOT_NOW = {
        'en': "Not now",
        'es': "Ahora no",
        'ro': "Nu acum"
    }
    
    # Support offers by distress level
    SUPPORT_OFFER_HIGH = {
        'en': "I noticed you're experiencing significant distress. Would you like to chat with our AI support assistant? I'm here to listen and provide emotional support.",
        'es': "Noté que estás experimentando una angustia significativa. ¿Te gustaría chatear con nuestro asistente de apoyo IA? Estoy aquí para escuchar y brindar apoyo emocional.",
        'ro': "Am observat că experimentezi un nivel semnificativ de stres. Ai dori să discuți cu asistentul nostru AI de suport? Sunt aici să ascult și să ofer suport emoțional."
    }
    
    SUPPORT_OFFER_MODERATE = {
        'en': "It seems you're dealing with some challenges. Would you like to talk about it with our AI support assistant?",
        'es': "Parece que estás lidiando con algunos desafíos. ¿Te gustaría hablar de ello con nuestro asistente de apoyo IA?",
        'ro': "Se pare că te confrunți cu unele provocări. Ai dori să vorbești despre asta cu asistentul nostru AI de suport?"
    }
    
    SUPPORT_OFFER_LOW = {
        'en': "Great job managing your diabetes! Would you like to chat with our AI assistant about maintaining your positive habits?",
        'es': "¡Buen trabajo manejando tu diabetes! ¿Te gustaría chatear con nuestro asistente IA sobre mantener tus hábitos positivos?",
        'ro': "Felicitări pentru gestionarea diabetului! Ai dori să discuți cu asistentul nostru AI despre menținerea obiceiurilor pozitive?"
    }
    
    # Error messages
    ERROR_USER_NOT_FOUND = {
        'en': "Error: User not found",
        'es': "Error: Usuario no encontrado",
        'ro': "Eroare: Utilizator negăsit"
    }
    
    ERROR_INVALID_LANGUAGE = {
        'en': "Error: Invalid language",
        'es': "Error: Idioma inválido",
        'ro': "Eroare: Limbă invalidă"
    }
    
    # Status messages
    NEVER_INTERACTED = {
        'en': "Never",
        'es': "Nunca",
        'ro': "Niciodată"
    }
    
    # Admin messages
    ADMIN_ONLY_ACCESS = {
        'en': "⛔ This command is for administrators only.",
        'es': "⛔ Este comando es solo para administradores.",
        'ro': "⛔ Această comandă este doar pentru administratori."
    }
    
    SEND_ALERTS_START = {
        'en': "📤 Sending questionnaires to all active users...",
        'es': "📤 Enviando cuestionarios a todos los usuarios activos...",
        'ro': "📤 Trimit chestionare către toți utilizatorii activi..."
    }
    
    SEND_ALERTS_COMPLETE = {
        'en': "✅ Questionnaires sent!",
        'es': "✅ ¡Cuestionarios enviados!",
        'ro': "✅ Chestionare trimise!"
    }
    
    # Rate limit
    RATE_LIMIT_EXCEEDED = {
        'en': "⏱️ Please wait before using this command again.",
        'es': "⏱️ Por favor espera antes de usar este comando de nuevo.",
        'ro': "⏱️ Te rog așteaptă înainte de a folosi din nou această comandă."
    }
    
    # Health check
    HEALTH_STATUS_TEMPLATE = {
        'en': """🏥 Bot Health Status
⚡ Scheduler: {scheduler_status}
📅 Environment: {environment}
⏰ Scheduled Jobs: {job_count}""",
        'es': """🏥 Estado de Salud del Bot
⚡ Programador: {scheduler_status}
📅 Entorno: {environment}
⏰ Trabajos Programados: {job_count}""",
        'ro': """🏥 Starea de Sănătate a Bot-ului
⚡ Planificator: {scheduler_status}
📅 Mediu: {environment}
⏰ Sarcini Programate: {job_count}"""
    }
    
    HEALTH_DEV_MODE = {
        'en': "\n🔧 DEV Mode: Alerts every {minutes} minutes",
        'es': "\n🔧 Modo DEV: Alertas cada {minutes} minutos",
        'ro': "\n🔧 Mod DEV: Alerte la fiecare {minutes} minute"
    }
    
    HEALTH_PROD_MODE = {
        'en': "\n🏭 PROD Mode: Alerts at 9:00, 15:00, 21:00",
        'es': "\n🏭 Modo PROD: Alertas a las 9:00, 15:00, 21:00",
        'ro': "\n🏭 Mod PROD: Alerte la 9:00, 15:00, 21:00"
    }
    
    # Pause/Resume messages
    PAUSE_ALREADY_PAUSED = {
        'en': "⏸️ Your automatic questionnaires are already paused.",
        'es': "⏸️ Tus cuestionarios automáticos ya están pausados.",
        'ro': "⏸️ Chestionarele tale automate sunt deja întrerupte."
    }
    
    PAUSE_SUCCESS = {
        'en': "⏸️ Automatic questionnaires have been paused.\n\nYou will no longer receive scheduled questionnaires.\nYou can still complete questionnaires manually with /questionnaire\nUse /resume to start receiving automatic questionnaires again.",
        'es': "⏸️ Los cuestionarios automáticos han sido pausados.\n\nYa no recibirás cuestionarios programados.\nAún puedes completar cuestionarios manualmente con /questionnaire\nUsa /resume para volver a recibir cuestionarios automáticos.",
        'ro': "⏸️ Chestionarele automate au fost întrerupte.\n\nNu vei mai primi chestionare programate.\nPoți completa chestionare manual cu /questionnaire\nFolosește /resume pentru a primi din nou chestionare automate."
    }
    
    RESUME_ALREADY_ACTIVE = {
        'en': "✅ Your automatic questionnaires are already active.",
        'es': "✅ Tus cuestionarios automáticos ya están activos.",
        'ro': "✅ Chestionarele tale automate sunt deja active."
    }
    
    RESUME_BLOCKED = {
        'en': "❌ Cannot resume - you have blocked the bot.\nPlease unblock the bot in Telegram settings first.",
        'es': "❌ No se puede reanudar - has bloqueado el bot.\nPor favor desbloquea el bot en la configuración de Telegram primero.",
        'ro': "❌ Nu pot relua - ai blocat bot-ul.\nTe rog deblochează bot-ul în setările Telegram mai întâi."
    }
    
    RESUME_SUCCESS = {
        'en': "✅ Automatic questionnaires have been resumed!\n\nYou will now receive questionnaires at scheduled times.\nUse /pause if you need to stop them again.",
        'es': "✅ ¡Los cuestionarios automáticos han sido reanudados!\n\nAhora recibirás cuestionarios en los horarios programados.\nUsa /pause si necesitas detenerlos de nuevo.",
        'ro': "✅ Chestionarele automate au fost reluate!\n\nAcum vei primi chestionare la orele programate.\nFolosește /pause dacă trebuie să le oprești din nou."
    }
    
    # Status command
    STATUS_TEMPLATE = {
        'en': """📊 Your Status:

Name: {first_name} {family_name}
Alert Status: {alert_status}
Registered: {registration_date}
Last interaction: {last_interaction}

Commands:
• Use /pause to stop automatic questionnaires
• Use /resume to start receiving them again
• Use /questionnaire to complete one manually""",
        'es': """📊 Tu Estado:

Nombre: {first_name} {family_name}
Estado de Alertas: {alert_status}
Registrado: {registration_date}
Última interacción: {last_interaction}

Comandos:
• Usa /pause para detener cuestionarios automáticos
• Usa /resume para comenzar a recibirlos de nuevo
• Usa /questionnaire para completar uno manualmente""",
        'ro': """📊 Starea Ta:

Nume: {first_name} {family_name}
Stare Alerte: {alert_status}
Înregistrat: {registration_date}
Ultima interacțiune: {last_interaction}

Comenzi:
• Folosește /pause pentru a opri chestionarele automate
• Folosește /resume pentru a le primi din nou
• Folosește /questionnaire pentru a completa unul manual"""
    }
    
    ALERT_STATUS_ACTIVE = {
        'en': "✅ Active - Receiving automatic questionnaires",
        'es': "✅ Activo - Recibiendo cuestionarios automáticos",
        'ro': "✅ Activ - Primești chestionare automate"
    }
    
    ALERT_STATUS_INACTIVE = {
        'en': "⏸️ Paused - Not receiving automatic questionnaires",
        'es': "⏸️ Pausado - No recibiendo cuestionarios automáticos",
        'ro': "⏸️ Întrerupt - Nu primești chestionare automate"
    }
    
    ALERT_STATUS_BLOCKED = {
        'en': "🚫 Blocked - Cannot receive messages",
        'es': "🚫 Bloqueado - No puede recibir mensajes",
        'ro': "🚫 Blocat - Nu poate primi mesaje"
    }
    
    # Support declined message
    SUPPORT_DECLINED = {
        'en': "That's okay. Remember, support is always available with /support command. Take care of yourself! 💙",
        'es': "Está bien. Recuerda, el apoyo siempre está disponible con el comando /support. ¡Cuídate! 💙",
        'ro': "Este în regulă. Ține minte, suportul este întotdeauna disponibil cu comanda /support. Ai grijă de tine! 💙"
    }
    
    # Graph captions
    GRAPH_CAPTION_DDS2_SCORES = {
        'en': "📊 DDS-2 Scores Over Time",
        'es': "📊 Puntuaciones DDS-2 en el Tiempo",
        'ro': "📊 Scoruri DDS-2 în Timp"
    }
    
    GRAPH_CAPTION_DISTRESS_DISTRIBUTION = {
        'en': "📊 Distress Level Distribution",
        'es': "📊 Distribución de Niveles de Angustia",
        'ro': "📊 Distribuția Nivelurilor de Stres"
    }
    
    GRAPH_CAPTION_RESPONSE_RATE = {
        'en': "📊 Response Rate Over Time",
        'es': "📊 Tasa de Respuesta en el Tiempo",
        'ro': "📊 Rata de Răspuns în Timp"
    }
    
    # Export XML caption
    EXPORT_XML_CAPTION = {
        'en': "📄 Your complete data in XML format",
        'es': "📄 Tus datos completos en formato XML",
        'ro': "📄 Datele tale complete în format XML"
    }
    
    # Support declined message
    SUPPORT_DECLINED = {
        'en': "That's okay. Remember, support is always available with /support command. Take care of yourself! 💙",
        'es': "Está bien. Recuerda, el apoyo siempre está disponible con el comando /support. ¡Cuídate! 💙",
        'ro': "Este în regulă. Amintește-ți, suportul este întotdeauna disponibil cu comanda /support. Ai grijă de tine! 💙"
    }
    
    # Registration error
    REGISTRATION_ERROR = {
        'en': "Sorry, there was an error during registration. Please try again later.",
        'es': "Lo siento, hubo un error durante el registro. Por favor intenta más tarde.",
        'ro': "Îmi pare rău, a apărut o eroare în timpul înregistrării. Te rog încearcă mai târziu."
    }
    
    # Please register first (same as NOT_REGISTERED but kept for clarity)
    PLEASE_REGISTER_FIRST = {
        'en': "Please register first using /register",
        'es': "Por favor regístrate primero usando /register",
        'ro': "Te rog înregistrează-te mai întâi folosind /register"
    }