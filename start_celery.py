#!/usr/bin/env python3
"""
Celery worker startup script for PRIME platform
"""

import os
import sys
from app.core.celery_app import celery_app

if __name__ == "__main__":
    # Set up environment
    os.environ.setdefault("PYTHONPATH", os.path.dirname(os.path.abspath(__file__)))
    
    # Start Celery worker
    celery_app.start()