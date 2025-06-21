#!/usr/bin/env python3
"""
Celery Worker Startup Script for Health Records API
"""

import os
import sys
from celery import Celery
from app.core.config import settings

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Celery app
from app.celery_app import celery_app

if __name__ == "__main__":
    # Start Celery worker
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=2",  # Number of worker processes
        "--queues=file_processing,ai_processing,export,celery",  # Queue names
        "--hostname=health_records_worker@%h"  # Worker hostname
    ]) 