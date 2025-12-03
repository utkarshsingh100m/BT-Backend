"""
Vercel API Entrypoint for Buddy Tools Backend
This file serves as the entry point for Vercel serverless deployment
"""

from backend.chat_api import app

# Vercel looks for 'app' variable
# This exports the Flask app from backend/chat_api.py
