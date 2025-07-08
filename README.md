# Diabetes Monitoring System - Project Guide

## Project Structure
```
diabetes-monitoring/
├── bot/                    # Telegram bot code
├── database/              # SQLAlchemy models and helpers
├── scripts/               # Utility scripts
├── llm/                   # LLM integration (Week 8)
├── alembic/              # Database migrations
├── venv/                 # Python virtual environment
├── .env                  # Environment variables
├── config.py             # Configuration
└── requirements.txt      # Python dependencies
```

## Weekly Implementation Plan

### ✅ Week 1: Setup
- Project structure
- Virtual environment
- Dependencies

### ✅ Week 2: Database & Encryption
- SQLAlchemy models with encryption
- Helper functions (instead of stored procedures)
- Alembic migrations

### Week 3-4: Telegram Bot
- Bot registration and commands
- User registration flow
- Questionnaire implementation

### Week 5-6: Alert System
- Scheduling with `schedule` library
- Error handling for blocked users

### Week 7: Data Export
- XML export functionality
- Graph generation

### Week 8: LLM Integration
- Compare models
- Integrate with bot

## Key Commands

```bash
# Activate environment
source venv/bin/activate

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Run tests
python test_week2.py
```

## Database Models

- **User**: Encrypted personal data (passport_id, phone, email)
- **Response**: Questionnaire answers
- **AssistantInteraction**: AI chat history

## Next Steps (Week 3)

1. Create `bot/telegram_bot.py`
2. Implement `/start` and `/register` commands
3. Test with BotFather token