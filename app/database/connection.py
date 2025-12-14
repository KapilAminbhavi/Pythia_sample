from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from app.models.database import Base
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""

    def __init__(self):
        settings = get_settings()

        # Create engine with connection pooling
        self.engine = create_engine(
            settings.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
            echo=settings.log_level == "DEBUG"
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def create_tables(self):
        """Create all tables in the database"""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()


# Global database instance
db = Database()


def get_db() -> Session:
    """
    Dependency for FastAPI routes to get database session.
    Automatically closes session after request.
    """
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()