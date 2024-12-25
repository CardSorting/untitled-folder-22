from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import random
import json
import os
from pathlib import Path

@dataclass
class WordChallenge:
    word: str
    points: int
    time_limit: float
    level: int
    combo_requirement: int
    power_ups: List[str]
    rhythm_pattern: List[float]

class GameMechanics:
    def __init__(self, config: Dict):
        self.config = config
        self.word_lists = self._load_word_lists()
        self.rhythm_patterns = self._load_rhythm_patterns()
        
    def _load_word_lists(self) -> Dict[int, List[str]]:
        """Load word lists from JSON files based on difficulty levels."""
        word_lists = {}
        word_lists_dir = Path(__file__).parent / 'data' / 'word_lists'
        
        try:
            for difficulty in range(1, 6):
                file_path = word_lists_dir / f'level_{difficulty}.json'
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        word_lists[difficulty] = json.load(f)
                else:
                    # Fallback word lists if files don't exist
                    word_lists[difficulty] = self._get_fallback_words(difficulty)
        except Exception as e:
            # Fallback to basic word lists if there's an error
            return self._get_fallback_word_lists()
            
        return word_lists
    
    def _get_fallback_words(self, difficulty: int) -> List[str]:
        """Get fallback words for a specific difficulty level."""
        basic_words = {
            1: ["the", "and", "for", "are", "but", "not", "you", "all", "any", "can", "day", "get"],
            2: ["python", "coding", "typing", "games", "learn", "write", "speak", "think", "quick"],
            3: ["algorithm", "function", "variable", "keyboard", "practice", "sequence", "pattern"],
            4: ["programming", "development", "javascript", "experience", "challenge", "knowledge"],
            5: ["asynchronous", "optimization", "inheritance", "polymorphism", "encapsulation"]
        }
        return basic_words.get(difficulty, basic_words[1])
    
    def _get_fallback_word_lists(self) -> Dict[int, List[str]]:
        """Get complete fallback word lists."""
        return {i: self._get_fallback_words(i) for i in range(1, 6)}
    
    def _load_rhythm_patterns(self) -> List[List[float]]:
        """Load rhythm patterns for typing challenges."""
        return [
            [1.0, 1.0, 1.0, 1.0],  # Regular
            [0.8, 1.2, 0.8, 1.2],  # Syncopated
            [0.5, 0.5, 1.0, 1.0],  # Quick-slow
            [1.5, 0.5, 1.5, 0.5],  # Long-short
            [0.7, 0.7, 0.7, 1.9]   # Triple-long
        ]
    
    def calculate_word_difficulty(self, word: str) -> int:
        """
        Calculate word difficulty based on multiple factors.
        
        Args:
            word: The word to analyze
            
        Returns:
            Difficulty score from 1 to 5
        """
        # Base difficulty from length
        length_score = min(len(word) / 3, 2.5)
        
        # Complexity score based on character patterns
        char_patterns = {
            'uppercase': lambda c: c.isupper(),
            'special': lambda c: not c.isalnum(),
            'number': lambda c: c.isdigit(),
            'repeated': lambda c: word.count(c) > 1
        }
        
        complexity_score = sum(
            sum(1 for c in word if pattern(c))
            for pattern in char_patterns.values()
        ) / len(word)
        
        # Rhythm difficulty based on consecutive similar characters
        rhythm_score = sum(
            1 for i in range(len(word)-1)
            if word[i] == word[i+1]
        ) / len(word)
        
        total_score = length_score + complexity_score + rhythm_score
        return min(round(total_score + 1), 5)
    
    def generate_challenge(self, user_level: int) -> WordChallenge:
        """
        Generate a word challenge based on user level and current performance.
        
        Args:
            user_level: Current user level (1-5)
            
        Returns:
            WordChallenge object with challenge details
        """
        # Select appropriate difficulty levels
        available_levels = [
            max(1, user_level - 1),
            user_level,
            min(5, user_level + 1)
        ]
        
        # Weight towards user's current level
        weights = [0.2, 0.6, 0.2]
        selected_level = random.choices(available_levels, weights=weights)[0]
        
        # Get word and calculate base points
        word = random.choice(self.word_lists[selected_level])
        difficulty = self.calculate_word_difficulty(word)
        
        # Calculate points and time limit
        base_points = self.config['base_points']
        points = base_points * difficulty * self.config.get('combo_multiplier', 1.0)
        
        # Dynamic time limit based on word complexity
        base_time = len(word) * 0.5
        difficulty_factor = 1 + (difficulty * 0.2)
        time_limit = round(base_time * difficulty_factor, 1)
        
        # Select power-ups based on level
        available_power_ups = self._get_available_power_ups(selected_level)
        power_ups = random.sample(available_power_ups, min(2, len(available_power_ups)))
        
        # Get rhythm pattern
        rhythm_pattern = random.choice(self.rhythm_patterns)
        
        # Calculate combo requirement
        combo_requirement = max(3, min(10, selected_level * 2))
        
        return WordChallenge(
            word=word,
            points=round(points),
            time_limit=time_limit,
            level=selected_level,
            combo_requirement=combo_requirement,
            power_ups=power_ups,
            rhythm_pattern=rhythm_pattern
        )
    
    def _get_available_power_ups(self, level: int) -> List[str]:
        """Get available power-ups based on level."""
        all_power_ups = {
            'time_freeze': 1,      # Freezes the timer temporarily
            'point_boost': 1,      # Doubles points for next word
            'shield': 2,           # Prevents combo break on next mistake
            'slow_motion': 3,      # Slows down word movement
            'instant_clear': 4,    # Instantly completes current word
            'combo_lock': 5        # Maintains combo for next 3 words
        }
        return [
            power_up for power_up, req_level in all_power_ups.items()
            if req_level <= level
        ]
    
    def calculate_score(self, 
                       typed_word: str, 
                       target_word: str, 
                       time_taken: float, 
                       time_limit: float,
                       combo_count: int = 0,
                       power_ups: List[str] = None) -> Tuple[int, float, bool]:
        """
        Calculate score based on accuracy, speed, combo, and power-ups.
        
        Args:
            typed_word: Word typed by user
            target_word: Target word to match
            time_taken: Time taken to type the word
            time_limit: Time limit for the word
            combo_count: Current combo count
            power_ups: List of active power-ups
            
        Returns:
            Tuple of (final_score, accuracy, combo_maintained)
        """
        if not typed_word or not target_word:
            return 0, 0.0, False
            
        # Calculate accuracy using Levenshtein distance
        distance = self._levenshtein_distance(typed_word.lower(), target_word.lower())
        max_distance = max(len(typed_word), len(target_word))
        accuracy = (1 - (distance / max_distance)) * 100
        
        # Perfect match bonus
        perfect_match = typed_word.lower() == target_word.lower()
        
        # Calculate time bonus
        time_bonus = 1.0
        if time_taken < time_limit:
            time_bonus = 1 + ((time_limit - time_taken) / time_limit)
        
        # Calculate combo bonus
        combo_bonus = 1.0
        if combo_count > 0:
            combo_bonus = 1 + (combo_count * self.config.get('combo_multiplier', 0.1))
        
        # Calculate power-up multipliers
        power_up_multiplier = 1.0
        if power_ups:
            if 'point_boost' in power_ups:
                power_up_multiplier *= 2.0
            if 'combo_lock' in power_ups:
                combo_bonus *= 1.5
        
        # Calculate final score
        base_score = self.config['base_points']
        difficulty_multiplier = self.calculate_word_difficulty(target_word)
        
        final_score = (
            base_score * 
            difficulty_multiplier * 
            time_bonus * 
            combo_bonus * 
            power_up_multiplier
        )
        
        # Determine if combo should be maintained
        combo_maintained = (
            perfect_match or 
            accuracy >= self.config.get('accuracy_threshold', 95) or
            'shield' in (power_ups or [])
        )
        
        return round(final_score), round(accuracy, 1), combo_maintained
    
    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate the Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return GameMechanics._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
