from flask import render_template, redirect, url_for, request, jsonify, current_app
from . import main_bp
from flask_login import login_required, current_user
from ..models import Score, GameStats, db, User
from ..services.game_service import GameService
from ..utils.exceptions import GameDataError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

logger = logging.getLogger(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"
)

@main_bp.before_request
def before_request():
    """Set user_id in request object for logging and caching."""
    if current_user.is_authenticated:
        request.user_id = current_user.id

@main_bp.route('/')
def home():
    """Home page route with user statistics."""
    if current_user.is_authenticated:
        try:
            user_stats = GameService.get_user_stats(current_user.id)
            logger.info(f"Fetched stats for user {current_user.id}")
            return render_template('home.html', stats=user_stats)
        except GameDataError as e:
            logger.error(f"Error fetching stats: {str(e)}")
            return render_template('home.html', error="Unable to load statistics")
    return render_template('home.html')

@main_bp.route('/game')
@login_required
def game():
    """Game page route that starts a new game session."""
    try:
        game_session = GameService.start_game_session(current_user.id)
        logger.info(f"Started new game session for user {current_user.id}")
        return render_template('game.html', 
                             challenge=game_session['challenge'],
                             power_ups=game_session['power_ups_available'])
    except GameDataError as e:
        logger.error(f"Error starting game: {str(e)}")
        return redirect(url_for('main.home'))

@main_bp.route('/api/v1/game/challenge')
@login_required
@limiter.limit("60 per minute")
def get_challenge():
    """Get the next word challenge with rhythm patterns."""
    try:
        challenge = GameService.get_next_challenge(current_user.id)
        return jsonify(challenge)
    except GameDataError as e:
        logger.error(f"Error generating challenge: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error generating challenge: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@main_bp.route('/api/v1/game/submit', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def submit_score():
    """Submit a game score with power-ups and combo tracking."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        result = GameService.submit_score(current_user.id, data)
        return jsonify({
            'success': True,
            'score': result['score'],
            'accuracy': result['accuracy'],
            'combo_count': result['combo_count'],
            'total_score': result['total_score'],
            'words_completed': result['words_completed'],
            'avg_accuracy': result['avg_accuracy'],
            'active_power_ups': result['active_power_ups'],
            'next_challenge': result['next_challenge'],
            'new_level': result['new_level'],
            'high_score': result['high_score']
        })
    except GameDataError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error submitting score: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@main_bp.route('/api/v1/game/end', methods=['POST'])
@login_required
def end_game():
    """End the current game session and get final stats."""
    try:
        final_stats = GameService.end_game_session(current_user.id)
        return jsonify({
            'success': True,
            'stats': final_stats
        })
    except GameDataError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error ending game session: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@main_bp.route('/api/v1/game/stats')
@login_required
@limiter.limit("60 per minute")
def get_stats():
    """Get detailed user game statistics."""
    try:
        stats = GameService.get_user_stats(current_user.id)
        return jsonify(stats)
    except GameDataError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch statistics'}), 500

@main_bp.route('/api/v1/game/leaderboard')
@limiter.limit("30 per minute")
def get_leaderboard():
    """Get global leaderboard with recent high scores."""
    try:
        # Get top 10 scores of all time
        top_scores = Score.query\
            .join(User)\
            .with_entities(
                User.username,
                Score.score,
                Score.accuracy,
                Score.timestamp
            )\
            .order_by(Score.score.desc())\
            .limit(10)\
            .all()
        
        # Format the results
        leaderboard = [
            {
                'username': score.username,
                'score': score.score,
                'accuracy': score.accuracy,
                'date': score.timestamp.strftime('%Y-%m-%d %H:%M')
            }
            for score in top_scores
        ]
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard
        })
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch leaderboard'}), 500
