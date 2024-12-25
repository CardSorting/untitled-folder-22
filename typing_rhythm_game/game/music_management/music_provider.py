import requests
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class MusicProvider:
    """Provides access to music tracks for different game levels."""
    
    _instance = None
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super(MusicProvider, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the music provider if not already initialized."""
        if self._initialized:
            return
            
        self._config = current_app.config['MUSIC_CONFIG']
        self._initialized = True
        logger.info("MusicProvider initialized")
    
    def get_track_url(self, level):
        """
        Get the URL for a level's music track.
        
        Args:
            level (int): The game level
            
        Returns:
            dict: Track information including URL and metadata
        """
        try:
            if level not in self._config['levels']:
                logger.warning(f"No music configured for level {level}")
                return None
                
            level_config = self._config['levels'][level]
            
            return {
                'success': True,
                'url': level_config['url'],
                'name': level_config['name'],
                'bpm': level_config['bpm'],
                'rhythm': {
                    'bpm': level_config['bpm'],
                    'pattern': level_config['rhythm_pattern']
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting track URL for level {level}: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to get music for level {level}"
            }
    
    def get_rhythm_info(self, level):
        """
        Get rhythm information for a level.
        
        Args:
            level (int): The game level
            
        Returns:
            dict: Rhythm information including BPM and pattern
        """
        try:
            if level not in self._config['levels']:
                return None
                
            level_config = self._config['levels'][level]
            return {
                'bpm': level_config['bpm'],
                'pattern': level_config['rhythm_pattern']
            }
            
        except Exception as e:
            logger.error(f"Error getting rhythm info for level {level}: {str(e)}")
            return None
