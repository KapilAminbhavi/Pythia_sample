"""
Celery worker entry point.

Start worker:
    celery -A celery_worker worker --loglevel=info
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.celery_app import celery_app

if __name__ == '__main__':
    celery_app.start()
