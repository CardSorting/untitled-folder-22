from typing import Dict, Optional
import requests
import logging
from flask import current_app
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class MusicProvider:
    """
    Manages music tracks for different game levels.
    Implements the Singleton pattern for consistent music management.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MusicProvider, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._music_config = self._load_music_config()
        self._initialized = True
    
    def _load_music_config(self) -> Dict:
        """Load music configuration for each level."""
        try:
            config_path = Path(__file__).parent / 'music_config.json'
            if not config_path.exists():
                # Create default config if it doesn't exist
                default_config = {
                    "1": {
                        "url": "https://f005.backblazeb2.com/file/typegamer/Pixelated+Heartbeat.wav",
                        "name": "Pixelated Heartbeat",
                        "bpm": 120,
                        "difficulty_sync": {
                            "beat_division": 4,
                            "pattern_length": 8
                        }
                    },
                    "2": {
                        "url": "https://f005.backblazeb2.com/file/typegamer/level2_music.wav",
                        "name": "Level 2 Music",
                        "bpm": 140,
                        "difficulty_sync": {
                            "beat_division": 4,
                            "pattern_length": 8
                        }
                    },
                    "3": {
                        "url": "https://f005.backblazeb2.com/file/typegamer/level3_music.wav",
                        "name": "Level 3 Music",
                        "bpm": 160,
                        "difficulty_sync": {
                            "beat_division": 4,
                            "pattern_length": 16
                        }
                    },
                    "4": {
                        "url": "https://f005.backblazeb2.com/file/typegamer/level4_music.wav",
                        "name": "Level 4 Music",
                        "bpm": 180,
                        "difficulty_sync": {
                            "beat_division": 8,
                            "pattern_length": 16
                        }
                    },
                    "5": {
                        "url": "https://f005.backblazeb2.com/file/typegamer/level5_music.wav",
                        "name": "Level 5 Music",
                        "bpm": 200,
                        "difficulty_sync": {
                            "beat_division": 8,
                            "pattern_length": 32
                        }
                    }
                }
                
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                return default_config
            
            with open(config_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading music config: {str(e)}")
            return {}
    
    def get_music_info(self, level: int) -> Optional[Dict]:
        """
        Get music information for a specific level.
        
        Args:
            level: Game difficulty level (1-5)
            
        Returns:
            Dictionary containing music information or None if not found
        """
        return self._music_config.get(str(level))
    
    def get_stream_url(self, level: int) -> Optional[str]:
        """
        Get the streaming URL for a level's music.
        
        Args:
            level: Game difficulty level (1-5)
            
        Returns:
            URL for streaming the music or None if not found
        """
        music_info = self.get_music_info(level)
        return music_info['url'] if music_info else None
    
    def get_rhythm_pattern(self, level: int) -> Optional[Dict]:
        """
        Get rhythm pattern information for a level.
        
        Args:
            level: Game difficulty level (1-5)
            
        Returns:
            Dictionary containing rhythm pattern info or None if not found
        """
        music_info = self.get_music_info(level)
        if not music_info:
            return None
            
        return {
            'bpm': music_info['bpm'],
            'beat_division': music_info['difficulty_sync']['beat_division'],
            'pattern_length': music_info['difficulty_sync']['pattern_length']
        }
    
    def verify_music_availability(self, level: int) -> bool:
        """
        Verify that the music for a level is available and accessible.
        
        Args:
            level: Game difficulty level (1-5)
            
        Returns:
            True if music is available, False otherwise
        """
        try:
            url = self.get_stream_url(level)
            if not url:
                return False
                
            # Check if the URL is accessible
            response = requests.head(url)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error verifying music availability for level {level}: {str(e)}")
            return False
