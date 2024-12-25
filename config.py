import os
from datetime import timedelta

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///game.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    SESSION_PROTECTION = 'strong'
    
    # Game configuration
    WORD_CONFIG = {
        'min_length': 3,
        'max_length': 10,
        'default_variance': 2
    }
    
    # Music configuration
    MUSIC_CONFIG = {
        'levels': {
            1: {
                'name': 'Pixelated Heartbeat',
                'url': 'https://f005.backblazeb2.com/file/typegamer/Pixelated+Heartbeat.wav',
                'bpm': 120,
                'rhythm_pattern': [1, 0, 1, 0]  # 1 = beat, 0 = rest
            },
            2: {
                'name': 'Digital Dreams',
                'url': 'https://f005.backblazeb2.com/file/typegamer/Pixelated+Heartbeat.wav',
                'bpm': 140,
                'rhythm_pattern': [1, 0, 1, 1]
            }
        }
    }
    
    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'csrf-key-please-change-in-production'
