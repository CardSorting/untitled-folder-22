from flask import Blueprint

word_management_bp = Blueprint('word_management', __name__, url_prefix='/api/v1/words')

from . import routes  # Import routes after creating blueprint to avoid circular imports
