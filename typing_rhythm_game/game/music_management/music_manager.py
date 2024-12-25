from flask import current_app
import logging
from .music_provider import MusicProvider

logger = logging.getLogger(__name__)

class MusicManager:
    """Manages music playback and synchronization for the game."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MusicManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._music_provider = MusicProvider()
        self._current_level = None
        self._start_time = None
        self._initialized = True
        logger.info("MusicManager initialized")
    
    def start_level_music(self, level):
        """
        Start music for a specific level.
        
        Args:
            level (int): The level to start music for
            
        Returns:
            dict: Result of the operation
        """
        try:
            track_info = self._music_provider.get_track_url(level)
            if not track_info or not track_info['success']:
                return {
                    'success': False,
                    'error': 'Failed to get track information'
                }
            
            self._current_level = level
            self._start_time = current_app.music_state.get_current_time()
            
            return {
                'success': True,
                'track_info': track_info
            }
            
        except Exception as e:
            logger.error(f"Error starting level music: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to start music'
            }
    
    def stop_music(self):
        """Stop the current music playback."""
        self._current_level = None
        self._start_time = None
    
    def get_next_beat_timing(self):
        """
        Get timing information for the next beat.
        
        Returns:
            dict: Timing information or None if no music is playing
        """
        if not self._current_level or not self._start_time:
            return None
            
        rhythm_info = self._music_provider.get_rhythm_info(self._current_level)
        if not rhythm_info:
            return None
            
        current_time = current_app.music_state.get_current_time()
        elapsed_time = current_time - self._start_time
        
        # Calculate next beat based on BPM
        beat_duration = 60 / rhythm_info['bpm']
        current_beat = elapsed_time / beat_duration
        next_beat = int(current_beat) + 1
        
        return {
            'next_beat': next_beat,
            'time': self._start_time + (next_beat * beat_duration),
            'pattern': rhythm_info['pattern'][next_beat % len(rhythm_info['pattern'])]
        }
    
    def sync_with_word(self, word):
        """
        Synchronize a word with the current rhythm.
        
        Args:
            word (str): The word to synchronize
            
        Returns:
            list: Timing points for each letter
        """
        if not self._current_level or not self._start_time:
            return None
            
        rhythm_info = self._music_provider.get_rhythm_info(self._current_level)
        if not rhythm_info:
            return None
            
        next_beat = self.get_next_beat_timing()
        if not next_beat:
            return None
            
        timing_points = []
        current_beat = next_beat['next_beat']
        beat_duration = 60 / rhythm_info['bpm']
        pattern = rhythm_info['pattern']
        
        for letter in word:
            # Find next beat that aligns with the rhythm pattern
            while not pattern[current_beat % len(pattern)]:
                current_beat += 1
            
            timing_points.append({
                'letter': letter,
                'time': self._start_time + (current_beat * beat_duration)
            })
            current_beat += 1
        
        return timing_points
