import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cache configuration
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Game configuration
    GAME_CONFIG = {
        'min_word_length': 3,
        'max_word_length': 12,
        'time_limit': 60,  # seconds
        'difficulty_levels': {
            'easy': {'speed': 1.0, 'score_multiplier': 1.0},
            'medium': {'speed': 1.5, 'score_multiplier': 1.5},
            'hard': {'speed': 2.0, 'score_multiplier': 2.0}
        },
        'scoring': {
            'base_points': 10,
            'combo_multiplier': 0.1,  # 10% bonus per combo
            'accuracy_weight': 1.5,
            'speed_bonus_threshold': 0.8  # seconds
        }
    }
    
    # Word management configuration
    WORD_CONFIG = {
        'min_difficulty': 1,
        'max_difficulty': 5,
        'default_variance': 0.5,
        'word_lists_path': os.path.join('game', 'data', 'word_lists'),
        'cache_timeout': 3600,  # 1 hour
        'max_words_per_level': 1000,
        'min_word_length': 2,
        'max_word_length': 20,
        'allowed_characters': set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-\''),
        'analysis_weights': {
            'length': 0.25,
            'complexity': 0.25,
            'pattern': 0.25,
            'typing': 0.25
        }
    }
    
    # Rate limiting configuration
    RATELIMIT_DEFAULT = "200 per day"
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_STRATEGY = "fixed-window"
    
    # Login configuration
    LOGIN_DISABLED = False
    LOGIN_VIEW = 'auth.login'
    
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Use more secure session configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Use Redis for caching in production
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    
    # Use Redis for rate limiting in production
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL')
    
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
