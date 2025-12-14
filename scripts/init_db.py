"""
Database initialization script.
Run this to create tables and verify connection.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database.connection import db
from app.models.database import Base
from sqlalchemy import text  # Add this import
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database tables"""
    try:
        logger.info("Initializing database...")
        db.create_tables()
        logger.info("✓ Database initialized successfully!")

        # Test connection
        session = db.get_session()
        try:
            session.execute(text("SELECT 1"))  # Wrap in text()
            logger.info("✓ Database connection verified!")
        finally:
            session.close()

    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    init_database()