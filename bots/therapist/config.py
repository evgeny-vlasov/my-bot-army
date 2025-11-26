"""
Configuration settings for Therapist Bot
"""

import os


class Config:
    """
    Configuration class for the Therapist bot
    """

    # Server settings
    HOST = '0.0.0.0'
    PORT = 5002
    DEBUG = False

    # Bot settings
    BOT_ID = 'therapist'
    BOT_NAME = 'Therapist Assistant'

    # API settings
    MAX_CONVERSATION_HISTORY = 10  # Keep last 10 messages
    MAX_MESSAGE_LENGTH = 1000      # Max chars per message

    # CORS settings
    CORS_ORIGINS = ['*']  # In production, specify actual domains
