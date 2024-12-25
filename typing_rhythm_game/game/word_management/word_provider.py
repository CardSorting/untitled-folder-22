from typing import Dict, List, Optional
from pathlib import Path
import json
import logging
import random
from .word_analyzer import WordAnalyzer
from .word_difficulty import WordDifficulty

logger = logging.getLogger(__name__)

class WordProvider:
    """
    Manages word lists and provides words based on difficulty levels.
    Implements the Singleton pattern to ensure consistent word management.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WordProvider, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._word_lists: Dict[int, List[str]] = {}
        self._cached_analyzed_words: Dict[str, WordDifficulty] = {}
        self._analyzer = WordAnalyzer()
        self._word_lists_path = Path(__file__).parent.parent / 'data' / 'word_lists'
        self._load_word_lists()
        self._initialized = True
    
    def _load_word_lists(self) -> None:
        """Load word lists from JSON files and analyze them."""
        try:
            # Create directory if it doesn't exist
            self._word_lists_path.mkdir(parents=True, exist_ok=True)
            
            # Load and analyze each difficulty level
            for difficulty in range(1, 6):
                file_path = self._word_lists_path / f'level_{difficulty}.json'
                words = self._load_word_list_file(file_path, difficulty)
                analyzed_words = self._analyze_words(words)
                self._word_lists[difficulty] = analyzed_words
                
            logger.info(f"Successfully loaded {sum(len(words) for words in self._word_lists.values())} words")
            
        except Exception as e:
            logger.error(f"Error loading word lists: {str(e)}")
            self._word_lists = self._get_fallback_word_lists()
    
    def _load_word_list_file(self, file_path: Path, difficulty: int) -> List[str]:
        """Load words from a JSON file or create it if it doesn't exist."""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                # Create file with fallback words
                words = self._get_fallback_words(difficulty)
                with open(file_path, 'w') as f:
                    json.dump(words, f, indent=2)
                return words
        except Exception as e:
            logger.error(f"Error loading word list file {file_path}: {str(e)}")
            return self._get_fallback_words(difficulty)
    
    def _analyze_words(self, words: List[str]) -> List[str]:
        """Analyze words and cache their difficulty scores."""
        analyzed_words = []
        for word in words:
            if word not in self._cached_analyzed_words:
                difficulty = self._analyzer.analyze_word(word)
                self._cached_analyzed_words[word] = difficulty
            analyzed_words.append(word)
        return analyzed_words
    
    def get_word(self, target_difficulty: int, variance: float = 0.5) -> str:
        """
        Get a word with the target difficulty level.
        
        Args:
            target_difficulty: Target difficulty level (1-5)
            variance: Allowed variance in difficulty (0.0-1.0)
            
        Returns:
            A word matching the criteria
        """
        # Determine acceptable difficulty range
        min_diff = max(1, target_difficulty - round(variance))
        max_diff = min(5, target_difficulty + round(variance))
        available_levels = range(min_diff, max_diff + 1)
        
        # Get words from acceptable levels
        candidate_words = []
        for level in available_levels:
            if level in self._word_lists:
                candidate_words.extend(self._word_lists[level])
        
        if not candidate_words:
            logger.warning(f"No words found for difficulty {target_difficulty}, using fallback")
            return random.choice(self._get_fallback_words(target_difficulty))
        
        return random.choice(candidate_words)
    
    def add_word(self, word: str) -> bool:
        """
        Add a new word to the appropriate difficulty list.
        
        Args:
            word: Word to add
            
        Returns:
            True if word was added successfully
        """
        try:
            # Analyze word difficulty
            difficulty = self._analyzer.analyze_word(word)
            level = difficulty.get_level()
            
            # Add to memory and cache
            if level not in self._word_lists:
                self._word_lists[level] = []
            if word not in self._word_lists[level]:
                self._word_lists[level].append(word)
                self._cached_analyzed_words[word] = difficulty
            
            # Update JSON file
            file_path = self._word_lists_path / f'level_{level}.json'
            with open(file_path, 'w') as f:
                json.dump(self._word_lists[level], f, indent=2)
            
            logger.info(f"Added word '{word}' to difficulty level {level}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding word '{word}': {str(e)}")
            return False
    
    def get_difficulty(self, word: str) -> Optional[WordDifficulty]:
        """Get the cached difficulty analysis for a word."""
        return self._cached_analyzed_words.get(word)
    
    @staticmethod
    def _get_fallback_words(difficulty: int) -> List[str]:
        """Get fallback words for a specific difficulty level."""
        basic_words = {
            1: [
                "the", "and", "for", "are", "but", "not", "you", "all", "any",
                "can", "day", "get", "has", "him", "his", "how", "man", "new",
                "now", "old", "see", "two", "way", "who", "boy", "did", "its",
                "let", "put", "say", "she", "too", "was"
            ],
            2: [
                "about", "after", "again", "below", "could", "every", "first",
                "found", "great", "house", "large", "learn", "never", "other",
                "place", "plant", "point", "right", "small", "sound", "spell",
                "still", "study", "their", "there", "these", "thing", "think"
            ],
            3: [
                "algorithm", "function", "variable", "keyboard", "practice",
                "sequence", "pattern", "complete", "continue", "document",
                "exercise", "increase", "organize", "remember", "separate",
                "solution", "together", "category", "discover", "important"
            ],
            4: [
                "programming", "development", "javascript", "experience",
                "challenge", "knowledge", "understand", "technology",
                "difference", "particular", "processing", "successful",
                "everything", "production", "collection", "commercial",
                "confidence", "generation", "population", "university"
            ],
            5: [
                "asynchronous", "optimization", "inheritance", "polymorphism",
                "encapsulation", "authentication", "authorization", "configuration",
                "implementation", "initialization", "interpretation", "multiplication",
                "organization", "perpendicular", "sophisticated", "synchronization",
                "understanding", "visualization"
            ]
        }
        return basic_words.get(difficulty, basic_words[1])
    
    def _get_fallback_word_lists(self) -> Dict[int, List[str]]:
        """Get complete fallback word lists."""
        return {i: self._get_fallback_words(i) for i in range(1, 6)}
