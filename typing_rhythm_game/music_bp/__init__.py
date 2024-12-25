from flask import Blueprint

music_bp = Blueprint('music', __name__, url_prefix='/api/v1/music')

from . import routes
