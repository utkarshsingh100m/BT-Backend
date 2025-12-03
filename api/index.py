"""
Vercel API Entrypoint for Buddy Tools Backend
This file serves as the entry point for Vercel serverless deployment
"""

import sys
import os

# Add parent directory to path so we can import from app folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat_api import app

# Vercel looks for 'app' variable
# This exports the Flask app from app/chat_api.py
