from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from . import word_management_bp
from ..game.word_management import WordProvider
from ..utils.exceptions import GameDataError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

logger = logging.getLogger(__name__)
word_provider = WordProvider()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"
)

@word_management_bp.route('/challenge', methods=['GET'])
@login_required
@limiter.limit("60 per minute")
def get_word_challenge():
    """Get a word challenge based on user level and preferences."""
    try:
        user_level = request.args.get('level', type=int, default=1)
        variance = request.args.get('variance', type=float, default=0.5)
        
        # Get word matching user's level
        word = word_provider.get_word(user_level, variance)
        
        # Get word analysis
        difficulty = word_provider.get_difficulty(word)
        
        return jsonify({
            'success': True,
            'word': word,
            'difficulty': difficulty.to_dict()['metrics'] if difficulty else None
        })
    except Exception as e:
        logger.error(f"Error generating word challenge: {str(e)}")
        return jsonify({'error': 'Failed to generate challenge'}), 500

@word_management_bp.route('/analyze', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def analyze_word():
    """Analyze a word and return its difficulty metrics."""
    try:
        data = request.get_json()
        if not data or 'word' not in data:
            return jsonify({'error': 'No word provided'}), 400
            
        word = data['word']
        difficulty = word_provider.get_difficulty(word)
        
        if not difficulty:
            # If word hasn't been analyzed yet, add it
            word_provider.add_word(word)
            difficulty = word_provider.get_difficulty(word)
        
        return jsonify({
            'success': True,
            'analysis': difficulty.to_dict()
        })
    except Exception as e:
        logger.error(f"Error analyzing word: {str(e)}")
        return jsonify({'error': 'Failed to analyze word'}), 500

@word_management_bp.route('/list', methods=['GET'])
@login_required
@limiter.limit("30 per minute")
def list_words():
    """Get words for a specific difficulty level."""
    try:
        level = request.args.get('level', type=int, default=1)
        if not 1 <= level <= 5:
            return jsonify({'error': 'Invalid difficulty level'}), 400
            
        words = word_provider._word_lists.get(level, [])
        analyses = [word_provider.get_difficulty(word).to_dict() 
                   for word in words if word_provider.get_difficulty(word)]
        
        return jsonify({
            'success': True,
            'level': level,
            'words': analyses
        })
    except Exception as e:
        logger.error(f"Error listing words: {str(e)}")
        return jsonify({'error': 'Failed to list words'}), 500

@word_management_bp.route('/add', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def add_word():
    """Add a new word to the word lists."""
    try:
        data = request.get_json()
        if not data or 'word' not in data:
            return jsonify({'error': 'No word provided'}), 400
            
        word = data['word']
        if not word or not isinstance(word, str):
            return jsonify({'error': 'Invalid word format'}), 400
            
        # Add word and get its analysis
        success = word_provider.add_word(word)
        if not success:
            return jsonify({'error': 'Failed to add word'}), 500
            
        difficulty = word_provider.get_difficulty(word)
        
        return jsonify({
            'success': True,
            'word': word,
            'analysis': difficulty.to_dict() if difficulty else None
        })
    except Exception as e:
        logger.error(f"Error adding word: {str(e)}")
        return jsonify({'error': 'Failed to add word'}), 500

@word_management_bp.route('/stats', methods=['GET'])
@login_required
@limiter.limit("60 per minute")
def get_word_stats():
    """Get statistics about the word lists."""
    try:
        stats = {
            'total_words': sum(len(words) for words in word_provider._word_lists.values()),
            'words_per_level': {
                level: len(words) 
                for level, words in word_provider._word_lists.items()
            },
            'difficulty_distribution': {
                level: {
                    'count': len(words),
                    'average_length': sum(len(word) for word in words) / len(words) if words else 0,
                    'sample_words': sorted(words)[:5]  # Show 5 example words per level
                }
                for level, words in word_provider._word_lists.items()
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error fetching word stats: {str(e)}")
        return jsonify({'error': 'Failed to fetch word statistics'}), 500
