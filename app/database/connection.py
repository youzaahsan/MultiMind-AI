from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config.settings import settings
from app.utils.logging import get_logger

logger = get_logger("database")

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_default_users(db: Session) -> None:
    from app.database.models import User
    from app.database.repositories import UserRepository
    count = db.query(User).count()
    if count == 0:
        logger.info("Seeding default database users...")
        UserRepository.create(db, "user@multimind.ai", "Password123!", "User")
        UserRepository.create(db, "ali@multimind.ai", "Password123!", "Ali Khan")
        UserRepository.create(db, "ahmed@multimind.ai", "Password123!", "Ahmed Raza")
    else:
        # Migrate any legacy test user record to neutral User default
        legacy_user = db.query(User).filter(User.email == "youza@multimind.ai").first()
        if legacy_user:
            legacy_user.email = "user@multimind.ai"
            legacy_user.full_name = "User"
            db.commit()


def init_db() -> None:
    """Initializes tables in database."""
    try:
        # Import models so Base has all definitions
        from app.database import models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
        db = SessionLocal()
        try:
            seed_default_users(db)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database initialization error: {e}", exc_info=True)
        raise
