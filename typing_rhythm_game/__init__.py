from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
cache = Cache()
limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Cache configuration
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    
    # Game configuration
    app.config['GAME_CONFIG'] = {
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
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    
    with app.app_context():
        # Import and register blueprints
        from .auth import auth_bp
        from .main import main_bp
        
        app.register_blueprint(auth_bp)  # /auth prefix is already set in auth_bp
        app.register_blueprint(main_bp)  # No prefix needed for main routes
    
    return app
