from typing import Dict, Optional, List
import threading
import time
import logging
from .music_provider import MusicProvider

logger = logging.getLogger(__name__)

class MusicManager:
    """
    Manages music playback and synchronization with game rhythm.
    Implements the Singleton pattern for consistent music state management.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MusicManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._provider = MusicProvider()
        self._current_level = None
        self._current_pattern = None
        self._pattern_position = 0
        self._last_beat_time = 0
        self._is_playing = False
        self._initialized = True
    
    def start_level_music(self, level: int) -> Dict:
        """
        Start playing music for a specific level and return timing information.
        
        Args:
            level: Game difficulty level (1-5)
            
        Returns:
            Dictionary containing music timing information
        """
        try:
            # Get music information
            music_info = self._provider.get_music_info(level)
            if not music_info:
                raise ValueError(f"No music configuration found for level {level}")
            
            # Verify music availability
            if not self._provider.verify_music_availability(level):
                raise ValueError(f"Music for level {level} is not available")
            
            # Update current state
            self._current_level = level
            self._current_pattern = self._provider.get_rhythm_pattern(level)
            self._pattern_position = 0
            self._last_beat_time = time.time()
            self._is_playing = True
            
            return {
                'success': True,
                'music_url': music_info['url'],
                'name': music_info['name'],
                'rhythm': self._current_pattern,
                'start_time': self._last_beat_time
            }
            
        except Exception as e:
            logger.error(f"Error starting music for level {level}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def stop_music(self) -> None:
        """Stop the current music playback."""
        self._is_playing = False
        self._current_level = None
        self._current_pattern = None
        self._pattern_position = 0
    
    def get_next_beat_timing(self) -> Optional[Dict]:
        """
        Get timing information for the next beat in the pattern.
        
        Returns:
            Dictionary containing next beat timing or None if not playing
        """
        if not self._is_playing or not self._current_pattern:
            return None
            
        current_time = time.time()
        bpm = self._current_pattern['bpm']
        beat_duration = 60.0 / bpm
        
        # Calculate time until next beat
        beats_elapsed = (current_time - self._last_beat_time) / beat_duration
        next_beat_time = self._last_beat_time + (math.ceil(beats_elapsed) * beat_duration)
        
        return {
            'next_beat': next_beat_time,
            'pattern_position': self._pattern_position,
            'beat_duration': beat_duration
        }
    
    def update_pattern_position(self) -> None:
        """Update the current position in the rhythm pattern."""
        if self._is_playing and self._current_pattern:
            self._pattern_position = (self._pattern_position + 1) % self._current_pattern['pattern_length']
            self._last_beat_time = time.time()
    
    def get_current_state(self) -> Dict:
        """
        Get the current music state.
        
        Returns:
            Dictionary containing current music state information
        """
        return {
            'is_playing': self._is_playing,
            'current_level': self._current_level,
            'pattern': self._current_pattern,
            'position': self._pattern_position,
            'last_beat_time': self._last_beat_time
        }
    
    def sync_with_word(self, word: str) -> List[float]:
        """
        Generate timing points for a word based on the current rhythm pattern.
        
        Args:
            word: Word to synchronize with the rhythm
            
        Returns:
            List of timing points for each character in the word
        """
        if not self._is_playing or not self._current_pattern:
            return [0.0] * len(word)
            
        bpm = self._current_pattern['bpm']
        beat_duration = 60.0 / bpm
        beat_division = self._current_pattern['beat_division']
        subdivision_duration = beat_duration / beat_division
        
        # Create timing points for each character
        timing_points = []
        for i, char in enumerate(word):
            # Calculate timing based on character position and pattern
            position_in_pattern = (self._pattern_position + i) % self._current_pattern['pattern_length']
            timing = self._last_beat_time + (position_in_pattern * subdivision_duration)
            timing_points.append(timing)
        
        return timing_points
