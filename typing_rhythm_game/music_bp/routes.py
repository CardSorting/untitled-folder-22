from flask import jsonify, request, current_app, Response, stream_with_context
from flask_login import login_required, current_user
from . import music_bp
from ..game.music_management import MusicManager, MusicProvider
from ..utils.exceptions import GameDataError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import logging

logger = logging.getLogger(__name__)
music_manager = MusicManager()
music_provider = MusicProvider()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"
)

@music_bp.route('/start/<int:level>', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def start_music(level: int):
    """Start music for a specific level."""
    try:
        if not 1 <= level <= 5:
            return jsonify({'error': 'Invalid level'}), 400
            
        result = music_manager.start_level_music(level)
        if not result['success']:
            return jsonify({'error': result['error']}), 500
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error starting music: {str(e)}")
        return jsonify({'error': 'Failed to start music'}), 500

@music_bp.route('/stop', methods=['POST'])
@login_required
def stop_music():
    """Stop the current music playback."""
    try:
        music_manager.stop_music()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error stopping music: {str(e)}")
        return jsonify({'error': 'Failed to stop music'}), 500

@music_bp.route('/stream/<int:level>')
def stream_music(level: int):
    """Stream music for a specific level."""
    try:
        if not 1 <= level <= 5:
            return jsonify({'error': 'Invalid level'}), 400
            
        url = music_provider.get_stream_url(level)
        if not url:
            return jsonify({'error': 'Music not found'}), 404
            
        # Stream the music from the B2 bucket
        def generate():
            response = requests.get(url, stream=True)
            for chunk in response.iter_content(chunk_size=4096):
                yield chunk
                
        return Response(
            stream_with_context(generate()),
            content_type='audio/wav'
        )
    except Exception as e:
        logger.error(f"Error streaming music: {str(e)}")
        return jsonify({'error': 'Failed to stream music'}), 500

@music_bp.route('/timing')
@login_required
def get_timing():
    """Get current music timing information."""
    try:
        timing = music_manager.get_next_beat_timing()
        if not timing:
            return jsonify({'error': 'No active music'}), 404
            
        return jsonify(timing)
    except Exception as e:
        logger.error(f"Error getting timing: {str(e)}")
        return jsonify({'error': 'Failed to get timing'}), 500

@music_bp.route('/sync', methods=['POST'])
@login_required
def sync_word():
    """Get timing points for a word based on current rhythm."""
    try:
        data = request.get_json()
        if not data or 'word' not in data:
            return jsonify({'error': 'No word provided'}), 400
            
        timing_points = music_manager.sync_with_word(data['word'])
        return jsonify({
            'success': True,
            'timing_points': timing_points
        })
    except Exception as e:
        logger.error(f"Error syncing word: {str(e)}")
        return jsonify({'error': 'Failed to sync word'}), 500

@music_bp.route('/state')
@login_required
def get_state():
    """Get current music state."""
    try:
        state = music_manager.get_current_state()
        return jsonify(state)
    except Exception as e:
        logger.error(f"Error getting state: {str(e)}")
        return jsonify({'error': 'Failed to get state'}), 500
