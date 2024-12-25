from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from config import Config
import logging
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Register blueprints
    from .main import main_bp
    from .auth import auth_bp
    from .word_management_bp import word_management_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(word_management_bp)

    # Create database tables
    with app.app_context():
        db.create_all()
        
    return app
