"""Main Telegram bot with integrated scheduler for diabetes monitoring system"""
import logging
import os
import sys
import asyncio
from datetime import datetime, timedelta, time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import Forbidden, BadRequest
from database import (
    SessionLocal, 
    add_user, 
    get_user_by_telegram_id,
    get_active_users,
    record_response,
    QuestionTypes,
    ResponseValues,
    UserStatus
)
from database.models import User
from config import BOT_TOKEN, ENVIRONMENT, IS_DEVELOPMENT

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Scheduler configuration
DEV_ALERT_MINUTES = 2  # Every 2 minutes in dev mode
PROD_ALERT_TIMES = [
    {'hour': 9, 'minute': 0},   # 9:00 AM
    {'hour': 15, 'minute': 0},  # 3:00 PM
    {'hour': 21, 'minute': 0}   # 9:00 PM
]
MESSAGE_DELAY = 0.5  # Delay between messages to avoid rate limits

# Global scheduler instance
scheduler = AsyncIOScheduler()

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Check if user already registered
    db = SessionLocal()
    try:
        existing_user = get_user_by_telegram_id(db, telegram_id)
        if existing_user:
            await update.message.reply_text(
                f"Welcome back, {existing_user.first_name}! 👋\n\n"
                f"I'm here to help you manage diabetes-related distress.\n"
                f"Use /help to see available commands."
            )
        else:
            await update.message.reply_text(
                f"Hello {user.first_name}! 👋\n\n"
                f"I'm a diabetes monitoring assistant designed to help track and manage "
                f"diabetes-related distress.\n\n"
                f"To get started, please register using /register"
            )
    finally:
        db.close()

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Register a new user"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    db = SessionLocal()
    try:
        # Check if already registered
        existing_user = get_user_by_telegram_id(db, telegram_id)
        if existing_user:
            await update.message.reply_text(
                f"You're already registered, {existing_user.first_name}! ✅"
            )
            return
        
        # Register new user
        new_user = add_user(
            db=db,
            first_name=user.first_name or "User",
            family_name=user.last_name or "Unknown",
            passport_id=None,
            phone_number=None,
            telegram_id=telegram_id,
            email=None
        )
        
        await update.message.reply_text(
            f"Registration successful! 🎉\n\n"
            f"Welcome {new_user.first_name}!\n\n"
            f"You'll receive questionnaires at scheduled times to help monitor "
            f"your diabetes-related distress.\n\n"
            f"Use /help to see available commands."
        )
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        await update.message.reply_text(
            "Sorry, there was an error during registration. Please try again later."
        )
        db.rollback()
    finally:
        db.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
Available commands:

/start - Start the bot
/register - Register as a new user
/status - Check your registration status
/pause - Pause automatic questionnaires
/resume - Resume automatic questionnaires
/questionnaire - Complete the distress questionnaire
/export - Export your data (XML + graphs)
/health - Check bot health status
/help - Show this help message

More features coming soon:
- AI assistant for emotional support
"""
    await update.message.reply_text(help_text)

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Health check for monitoring"""
    scheduler_status = "running" if scheduler.running else "stopped"
    jobs = scheduler.get_jobs()
    
    health_msg = f"""
🏥 Bot Health Status

✅ Bot: Online
✅ Scheduler: {scheduler_status}
📅 Environment: {ENVIRONMENT}
⏰ Scheduled Jobs: {len(jobs)}
"""
    
    if IS_DEVELOPMENT:
        health_msg += f"\n🔧 DEV Mode: Alerts every {DEV_ALERT_MINUTES} minutes"
    else:
        health_msg += "\n🏭 PROD Mode: Alerts at 9:00, 15:00, 21:00"
    
    await update.message.reply_text(health_msg)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check user registration status"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    db = SessionLocal()
    try:
        db_user = get_user_by_telegram_id(db, telegram_id)
        if db_user:
            # Determine alert status message
            if db_user.status.value == 'active':
                alert_status = "✅ Active - Receiving automatic questionnaires"
            elif db_user.status.value == 'inactive':
                alert_status = "⏸️ Paused - Not receiving automatic questionnaires"
            else:  # blocked
                alert_status = "🚫 Blocked - Cannot receive messages"
            
            status_text = f"""
📊 Your Status:

Name: {db_user.first_name} {db_user.family_name}
Alert Status: {alert_status}
Registered: {db_user.registration_date.strftime('%Y-%m-%d %H:%M')}
Last interaction: {db_user.last_interaction.strftime('%Y-%m-%d %H:%M') if db_user.last_interaction else 'Never'}

Commands:
• Use /pause to stop automatic questionnaires
• Use /resume to start receiving them again
• Use /questionnaire to complete one manually
"""
            await update.message.reply_text(status_text)
        else:
            await update.message.reply_text(
                "You're not registered yet. Use /register to get started!"
            )
    finally:
        db.close()

async def pause_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pause automatic questionnaires for user"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    db = SessionLocal()
    try:
        db_user = get_user_by_telegram_id(db, telegram_id)
        if not db_user:
            await update.message.reply_text(
                "You're not registered yet. Use /register to get started!"
            )
            return
        
        # Update status to inactive
        from database.models import User, UserStatus
        user_obj = db.query(User).filter(User.id == db_user.id).first()
        if user_obj:
            if user_obj.status == UserStatus.inactive:
                await update.message.reply_text(
                    "⏸️ Your automatic questionnaires are already paused."
                )
            else:
                user_obj.status = UserStatus.inactive
                db.commit()
                await update.message.reply_text(
                    "⏸️ Automatic questionnaires have been paused.\n\n"
                    "You will no longer receive scheduled questionnaires.\n"
                    "You can still complete questionnaires manually with /questionnaire\n"
                    "Use /resume to start receiving automatic questionnaires again."
                )
        
    except Exception as e:
        logger.error(f"Error pausing alerts: {e}")
        await update.message.reply_text(
            "Sorry, there was an error. Please try again later."
        )
        db.rollback()
    finally:
        db.close()

async def resume_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resume automatic questionnaires for user"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    db = SessionLocal()
    try:
        db_user = get_user_by_telegram_id(db, telegram_id)
        if not db_user:
            await update.message.reply_text(
                "You're not registered yet. Use /register to get started!"
            )
            return
        
        # Update status to active
        from database.models import User, UserStatus
        user_obj = db.query(User).filter(User.id == db_user.id).first()
        if user_obj:
            if user_obj.status == UserStatus.active:
                await update.message.reply_text(
                    "✅ Your automatic questionnaires are already active."
                )
            elif user_obj.status == UserStatus.blocked:
                await update.message.reply_text(
                    "❌ Cannot resume - you have blocked the bot.\n"
                    "Please unblock the bot in Telegram settings first."
                )
            else:
                user_obj.status = UserStatus.active
                db.commit()
                await update.message.reply_text(
                    "✅ Automatic questionnaires have been resumed!\n\n"
                    "You will now receive questionnaires at scheduled times.\n"
                    "Use /pause if you need to stop them again."
                )
        
    except Exception as e:
        logger.error(f"Error resuming alerts: {e}")
        await update.message.reply_text(
            "Sorry, there was an error. Please try again later."
        )
        db.rollback()
    finally:
        db.close()

async def questionnaire(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the questionnaire with inline buttons"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Check if user is registered
    db = SessionLocal()
    try:
        db_user = get_user_by_telegram_id(db, telegram_id)
        if not db_user:
            await update.message.reply_text(
                "Please register first using /register"
            )
            return
        
        # Store user_id in context for callback
        context.user_data['db_user_id'] = db_user.id
        context.user_data['user_name'] = db_user.first_name
    finally:
        db.close()
    
    # First question: Yes/No distress check
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="distress_yes"),
            InlineKeyboardButton("No", callback_data="distress_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Hello {context.user_data['user_name']}! 👋\n\n"
        f"Time for your diabetes distress check.\n\n"
        f"Have you experienced diabetes-related distress today?",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("distress_"):
        # Handle distress check response
        response_value = ResponseValues.YES if query.data == "distress_yes" else ResponseValues.NO
        user_id = context.user_data.get('db_user_id')
        
        # If no user_id in context (scheduled message), get from telegram_id
        if not user_id:
            telegram_id = str(query.from_user.id)
            db = SessionLocal()
            try:
                user = get_user_by_telegram_id(db, telegram_id)
                if user:
                    user_id = user.id
                    context.user_data['db_user_id'] = user_id
                else:
                    await query.edit_message_text("User not found. Please register with /register")
                    return
            finally:
                db.close()
        
        # Record the response
        db = SessionLocal()
        try:
            record_response(
                db=db,
                user_id=user_id,
                question_type=QuestionTypes.DISTRESS_CHECK,
                response_value=response_value
            )
        except Exception as e:
            logger.error(f"Error recording response: {e}")
            await query.edit_message_text(
                "Sorry, there was an error recording your response. Please try again later."
            )
            return
        finally:
            db.close()
        
        if response_value == ResponseValues.NO:
            # No distress, end questionnaire
            await query.edit_message_text(
                "Great to hear you're doing well! 😊\n\n"
                "Keep up the good work with your diabetes management.\n"
                "I'll check in with you again later."
            )
            context.user_data.clear()
        else:
            # Yes to distress, ask severity
            keyboard = [
                [
                    InlineKeyboardButton("1 - Very mild", callback_data="severity_1"),
                    InlineKeyboardButton("2 - Mild", callback_data="severity_2")
                ],
                [
                    InlineKeyboardButton("3 - Moderate", callback_data="severity_3"),
                    InlineKeyboardButton("4 - Severe", callback_data="severity_4")
                ],
                [
                    InlineKeyboardButton("5 - Very severe", callback_data="severity_5")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "I'm sorry to hear you're experiencing distress. 💙\n\n"
                "On a scale of 1-5, how severe is your distress?\n\n"
                "1 = Very mild\n"
                "5 = Very severe",
                reply_markup=reply_markup
            )
    
    elif query.data.startswith("severity_"):
        # Handle severity rating
        severity = query.data.split("_")[1]
        user_id = context.user_data.get('db_user_id')
        
        # If no user_id in context (scheduled message), get from telegram_id
        if not user_id:
            telegram_id = str(query.from_user.id)
            db = SessionLocal()
            try:
                user = get_user_by_telegram_id(db, telegram_id)
                if user:
                    user_id = user.id
                else:
                    await query.edit_message_text("User not found. Please register with /register")
                    return
            finally:
                db.close()
        
        # Record the severity
        db = SessionLocal()
        try:
            record_response(
                db=db,
                user_id=user_id,
                question_type=QuestionTypes.SEVERITY_RATING,
                response_value=severity
            )
        except Exception as e:
            logger.error(f"Error recording severity: {e}")
            await query.edit_message_text(
                "Sorry, there was an error recording your response. Please try again later."
            )
            return
        finally:
            db.close()
        
        # Provide appropriate response based on severity
        if severity in ["1", "2"]:
            message = (
                "Thank you for sharing. It's good that your distress is relatively mild. 🌟\n\n"
                "Remember, it's normal to experience some distress with diabetes management.\n"
                "Keep using your coping strategies!"
            )
        elif severity == "3":
            message = (
                "Thank you for sharing. Moderate distress can be challenging. 💪\n\n"
                "Consider taking a few minutes for self-care today.\n"
                "Would you like to chat with the AI assistant for support? (Coming soon)"
            )
        else:  # 4 or 5
            message = (
                "I'm concerned about your high distress level. 🫂\n\n"
                "Please consider reaching out to your healthcare team or a mental health professional.\n"
                "Remember, you don't have to manage this alone.\n\n"
                "The AI assistant feature (coming soon) will provide additional support."
            )
        
        await query.edit_message_text(message)
        context.user_data.clear()

async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export user data and send files via Telegram"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Check if user is registered
    db = SessionLocal()
    try:
        db_user = get_user_by_telegram_id(db, telegram_id)
        if not db_user:
            await update.message.reply_text(
                "You're not registered yet. Use /register to get started!"
            )
            return
        
        await update.message.reply_text(
            "📊 Generating your data export...\n"
            "This may take a moment. I'll send you the files when ready."
        )
        
        # Import the exporter
        from scripts.data_export import DataExporter
        
        # Set date range (last 30 days by default)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Create temporary directory for this export
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_dir = f"temp_exports/user_{telegram_id}_{timestamp}"
        os.makedirs(export_dir, exist_ok=True)
        
        try:
            # Create exporter and generate files
            exporter = DataExporter(db)
            
            # Export XML
            xml_file = os.path.join(export_dir, 'data_export.xml')
            stats = exporter.export_to_xml(db_user.id, start_date, end_date, xml_file)
            
            # Generate graphs if matplotlib is available
            try:
                exporter.generate_graphs(db_user.id, start_date, end_date, export_dir)
                graphs_generated = True
            except Exception as e:
                logger.warning(f"Could not generate graphs: {e}")
                graphs_generated = False
            
            # Send statistics summary
            summary = f"""
📊 **Your Data Export Summary**
Period: {start_date.date()} to {end_date.date()}

**Statistics:**
• Total responses: {stats['total_responses']}
• Distress occurrences: {stats['distress_count']} ({stats['distress_percentage']:.1f}%)
• Average severity: {stats['average_severity']}
• Response rate: {stats['response_rate']:.1f}%

**Severity Distribution:**
"""
            for level in range(1, 6):
                count = stats['severity_distribution'][level]
                if count > 0:
                    summary += f"• Level {level}: {count} times\n"
            
            await update.message.reply_text(summary, parse_mode='Markdown')
            
            # Send XML file
            with open(xml_file, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f'diabetes_data_{timestamp}.xml',
                    caption="📄 Your complete data in XML format"
                )
            
            # Send graphs if generated
            if graphs_generated:
                graph_files = [
                    ('distress_timeline.png', '📈 Distress Timeline'),
                    ('severity_distribution.png', '🥧 Severity Distribution'),
                    ('response_rate.png', '📊 Daily Response Rate'),
                    ('severity_trend.png', '📉 Severity Trend')
                ]
                
                for filename, caption in graph_files:
                    filepath = os.path.join(export_dir, filename)
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            await update.message.reply_photo(
                                photo=f,
                                caption=caption
                            )
            
            await update.message.reply_text(
                "✅ Export complete! All your data has been sent above.\n\n"
                "💡 Tip: You can save these files for your records or share them with your healthcare provider."
            )
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            await update.message.reply_text(
                "Sorry, there was an error generating your export. Please try again later."
            )
        finally:
            # Clean up temporary files
            import shutil
            if os.path.exists(export_dir):
                shutil.rmtree(export_dir)
            
    finally:
        db.close()

# Scheduler functions
async def send_questionnaire_to_user(bot, user: User) -> bool:
    """Send questionnaire to a single user"""
    try:
        # Create the questionnaire keyboard
        keyboard = [
            [
                InlineKeyboardButton("Yes", callback_data="distress_yes"),
                InlineKeyboardButton("No", callback_data="distress_no")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Personalized message
        message = (
            f"Hello {user.first_name}! 👋\n\n"
            f"Time for your scheduled diabetes distress check.\n\n"
            f"Have you experienced diabetes-related distress today?"
        )
        
        # Send message
        await bot.send_message(
            chat_id=int(user.telegram_id),
            text=message,
            reply_markup=reply_markup
        )
        
        logger.info(f"✅ Sent questionnaire to {user.first_name} (ID: {user.telegram_id})")
        return True
        
    except Forbidden:
        # User blocked the bot
        logger.warning(f"⚠️ User {user.first_name} (ID: {user.telegram_id}) has blocked the bot")
        # Update user status to blocked
        db = SessionLocal()
        try:
            db_user = db.query(User).filter(User.id == user.id).first()
            if db_user:
                db_user.status = UserStatus.blocked
                db.commit()
                logger.info(f"Updated user {user.telegram_id} status to blocked")
        finally:
            db.close()
        return False
        
    except BadRequest as e:
        # Invalid telegram_id or other bad request
        logger.error(f"❌ Bad request for user {user.telegram_id}: {e}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error sending to {user.telegram_id}: {e}")
        return False

async def send_scheduled_alerts(bot):
    """Send alerts to all active users"""
    logger.info("🔔 Starting scheduled alert job...")
    
    db = SessionLocal()
    try:
        # Get all active users
        active_users = get_active_users(db)
        logger.info(f"Found {len(active_users)} active users")
        
        if not active_users:
            logger.info("No active users to send alerts to")
            return
        
        # Statistics
        sent_count = 0
        failed_count = 0
        
        # Send to each user
        for user in active_users:
            success = await send_questionnaire_to_user(bot, user)
            if success:
                sent_count += 1
            else:
                failed_count += 1
            
            # Small delay between messages to avoid rate limits
            await asyncio.sleep(MESSAGE_DELAY)
        
        logger.info(
            f"📊 Alert job completed: "
            f"Sent: {sent_count}, Failed: {failed_count}"
        )
        
    except Exception as e:
        logger.error(f"❌ Error in scheduled alert job: {e}")
    finally:
        db.close()

# Manual trigger commands (for testing/admin)
async def send_alerts_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger alerts to all active users"""
    # You might want to add admin check here
    await update.message.reply_text("🔔 Sending alerts to all active users...")
    await send_scheduled_alerts(context.bot)
    await update.message.reply_text("✅ Alert job completed")

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

async def post_init(application: Application) -> None:
    """Initialize the bot and scheduler after startup"""
    bot = application.bot
    logger.info(f"Initializing bot with scheduler - Environment: {ENVIRONMENT}")
    
    # Schedule alerts based on environment
    if IS_DEVELOPMENT:
        # Development mode: run every N minutes
        scheduler.add_job(
            send_scheduled_alerts,
            'interval',
            minutes=DEV_ALERT_MINUTES,
            args=[bot],
            id='dev_alerts',
            replace_existing=True,
            coalesce=True,
            max_instances=1
        )
        logger.info(f"🔧 DEV MODE: Scheduled alerts every {DEV_ALERT_MINUTES} minutes")
    else:
        # Production mode: schedule at specific times
        for idx, time_config in enumerate(PROD_ALERT_TIMES):
            scheduler.add_job(
                send_scheduled_alerts,
                'cron',
                hour=time_config['hour'],
                minute=time_config['minute'],
                args=[bot],
                id=f'prod_alert_{idx}',
                replace_existing=True,
                coalesce=True,
                max_instances=1
            )
        logger.info(f"🏭 PROD MODE: Scheduled alerts at 9:00, 15:00, 21:00")
    
    # Start scheduler
    scheduler.start()
    logger.info("✅ Scheduler started successfully")

async def post_shutdown(application: Application) -> None:
    """Cleanup on shutdown"""
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()
    logger.info("✅ Scheduler stopped")

def main() -> None:
    """Start the bot with integrated scheduler"""
    # Create the Application with post_init and post_shutdown callbacks
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .job_queue(None)  # Disable job queue due to Python 3.13 compatibility
        .build()
    )
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("pause", pause_alerts))
    application.add_handler(CommandHandler("resume", resume_alerts))
    application.add_handler(CommandHandler("questionnaire", questionnaire))
    application.add_handler(CommandHandler("export", export_data))
    application.add_handler(CommandHandler("health", health_check))
    application.add_handler(CommandHandler("send_now", send_alerts_now))
    
    # Register callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("🚀 Starting Diabetes Monitoring Bot with integrated scheduler...")
    logger.info(f"📅 Environment: {ENVIRONMENT}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()