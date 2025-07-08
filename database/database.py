from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, ProgrammingError
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from database.constants import DatabaseSettings

# Create database URL
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Create engine
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    # Connect without database name to create it
    engine_without_db = create_engine(
        f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/",
        echo=False
    )
    
    try:
        with engine_without_db.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SHOW DATABASES LIKE '{DB_NAME}'"))
            if not result.fetchone():
                # Create database
                conn.execute(text(f"CREATE DATABASE {DB_NAME} CHARACTER SET {DatabaseSettings.CHARSET} COLLATE {DatabaseSettings.COLLATION}"))
                conn.commit()
                print(f"✓ Database '{DB_NAME}' created")
            else:
                print(f"✓ Database '{DB_NAME}' already exists")
        return True
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        return False
    finally:
        engine_without_db.dispose()

def test_connection():
    """Test database connection using SQLAlchemy"""
    try:
        # Try to connect and execute a simple query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✓ Database connected successfully")
        return True
    except OperationalError as e:
        print(f"✗ Database connection failed: {e}")
        return False

def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they're registered
        from database import models  # noqa
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False