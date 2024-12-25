from flask import Blueprint, jsonify, current_app, stream_with_context, Response
from flask_login import login_required
import requests
import logging
from ..game.music_management import MusicProvider

music_bp = Blueprint('music', __name__)
logger = logging.getLogger(__name__)
music_provider = MusicProvider()

@music_bp.route('/start/<int:level>', methods=['POST'])
@login_required
def start_music(level):
    """Start music for a level."""
    try:
        track_info = music_provider.get_track_url(level)
        if not track_info or not track_info['success']:
            return jsonify({
                'success': False,
                'error': 'Failed to get track information'
            }), 404
            
        return jsonify({
            'success': True,
            'name': track_info['name'],
            'rhythm': track_info['rhythm']
        })
        
    except Exception as e:
        logger.error(f"Error starting music for level {level}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@music_bp.route('/stream/<int:level>')
@login_required
def stream_music(level):
    """Stream music directly from storage."""
    try:
        track_info = music_provider.get_track_url(level)
        if not track_info or not track_info['success']:
            return jsonify({
                'success': False,
                'error': 'Track not found'
            }), 404

        def generate():
            # Stream in chunks to avoid memory issues
            response = requests.get(track_info['url'], stream=True)
            if response.status_code != 200:
                logger.error(f"Failed to get track from storage: {response.status_code}")
                return
                
            for chunk in response.iter_content(chunk_size=4096):
                yield chunk

        return Response(
            stream_with_context(generate()),
            content_type='audio/mpeg',
            headers={
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        logger.error(f"Error streaming music for level {level}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to stream music'
        }), 500

@music_bp.route('/stop', methods=['POST'])
@login_required
def stop_music():
    """Stop currently playing music."""
    return jsonify({'success': True})

@music_bp.route('/timing')
@login_required
def get_timing():
    """Get current music timing information."""
    try:
        return jsonify({
            'success': True,
            'timestamp': current_app.music_state.get_current_time(),
            'next_beat': current_app.music_state.get_next_beat()
        })
    except Exception as e:
        logger.error(f"Error getting timing: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get timing'
        }), 500

@music_bp.route('/sync', methods=['POST'])
@login_required
def sync_word():
    """Get timing points for a word."""
    try:
        word = request.json.get('word')
        if not word:
            return jsonify({
                'success': False,
                'error': 'No word provided'
            }), 400
            
        timing_points = current_app.music_state.get_timing_points(word)
        return jsonify({
            'success': True,
            'timing_points': timing_points
        })
        
    except Exception as e:
        logger.error(f"Error syncing word: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to sync word'
        }), 500

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
