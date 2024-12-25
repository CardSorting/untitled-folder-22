from typing import Dict, Set
import re
from .word_difficulty import WordDifficulty

class WordAnalyzer:
    """Analyzes words to determine their difficulty based on various factors."""
    
    def __init__(self):
        self._common_bigrams = self._load_common_bigrams()
        self._common_suffixes = self._load_common_suffixes()
        self._keyboard_patterns = self._load_keyboard_patterns()
    
    def analyze_word(self, word: str) -> WordDifficulty:
        """
        Analyze a word and return its difficulty metrics.
        
        Args:
            word: Word to analyze
            
        Returns:
            WordDifficulty object containing difficulty metrics
        """
        # Basic metrics
        length_score = self._calculate_length_score(word)
        complexity_score = self._calculate_complexity_score(word)
        pattern_score = self._calculate_pattern_score(word)
        typing_score = self._calculate_typing_difficulty(word)
        
        # Calculate final scores
        base_difficulty = (length_score + complexity_score + pattern_score + typing_score) / 4
        normalized_difficulty = min(max(round(base_difficulty, 2), 1.0), 5.0)
        
        return WordDifficulty(
            word=word,
            length_score=length_score,
            complexity_score=complexity_score,
            pattern_score=pattern_score,
            typing_score=typing_score,
            final_score=normalized_difficulty
        )
    
    def _calculate_length_score(self, word: str) -> float:
        """Calculate difficulty score based on word length."""
        length = len(word)
        if length <= 3:
            return 1.0
        elif length <= 5:
            return 2.0
        elif length <= 7:
            return 3.0
        elif length <= 9:
            return 4.0
        else:
            return 5.0
    
    def _calculate_complexity_score(self, word: str) -> float:
        """Calculate complexity score based on character patterns."""
        scores = []
        
        # Check for capital letters
        capital_ratio = sum(1 for c in word if c.isupper()) / len(word)
        scores.append(capital_ratio * 5)
        
        # Check for special characters
        special_ratio = sum(1 for c in word if not c.isalnum()) / len(word)
        scores.append(special_ratio * 5)
        
        # Check for numbers
        number_ratio = sum(1 for c in word if c.isdigit()) / len(word)
        scores.append(number_ratio * 4)
        
        # Check for repeated characters
        char_counts = {}
        for c in word.lower():
            char_counts[c] = char_counts.get(c, 0) + 1
        repeat_score = sum(count - 1 for count in char_counts.values()) / len(word)
        scores.append(repeat_score * 3)
        
        return min(sum(scores) / len(scores) if scores else 1.0, 5.0)
    
    def _calculate_pattern_score(self, word: str) -> float:
        """Calculate difficulty based on character patterns."""
        word = word.lower()
        scores = []
        
        # Check for common bigrams
        bigram_score = 0
        for i in range(len(word) - 1):
            bigram = word[i:i+2]
            if bigram in self._common_bigrams:
                bigram_score += 1
        scores.append(5 - (bigram_score / max(len(word) - 1, 1)) * 2)
        
        # Check for common suffixes
        has_common_suffix = any(word.endswith(suffix) for suffix in self._common_suffixes)
        scores.append(3 if has_common_suffix else 4)
        
        # Check for alternating hands in typing
        alt_hand_score = 0
        for i in range(len(word) - 1):
            if self._is_alternating_hands(word[i], word[i+1]):
                alt_hand_score += 1
        scores.append(5 - (alt_hand_score / max(len(word) - 1, 1)) * 2)
        
        return min(sum(scores) / len(scores) if scores else 1.0, 5.0)
    
    def _calculate_typing_difficulty(self, word: str) -> float:
        """Calculate difficulty based on typing patterns."""
        word = word.lower()
        scores = []
        
        # Check for same-finger typing
        same_finger_count = 0
        for pattern in self._keyboard_patterns['same_finger']:
            same_finger_count += sum(1 for i in range(len(word)-1) 
                                   if word[i:i+2] in pattern)
        scores.append(min(same_finger_count + 1, 5))
        
        # Check for awkward combinations
        awkward_count = 0
        for pattern in self._keyboard_patterns['awkward']:
            awkward_count += sum(1 for i in range(len(word)-2)
                               if word[i:i+3] in pattern)
        scores.append(min(awkward_count + 1, 5))
        
        # Check for hand alternation
        alt_score = sum(1 for i in range(len(word)-1)
                       if not self._is_alternating_hands(word[i], word[i+1]))
        scores.append(min(alt_score + 1, 5))
        
        return min(sum(scores) / len(scores) if scores else 1.0, 5.0)
    
    def _is_alternating_hands(self, char1: str, char2: str) -> bool:
        """Check if two characters are typed with alternating hands."""
        left_hand = set('qwertasdfgzxcvb')
        right_hand = set('yuiophjklnm')
        
        return (char1 in left_hand and char2 in right_hand) or \
               (char1 in right_hand and char2 in left_hand)
    
    @staticmethod
    def _load_common_bigrams() -> Set[str]:
        """Load common English bigrams."""
        return {
            'th', 'he', 'in', 'er', 'an', 're', 'nd', 'at', 'on', 'nt',
            'ha', 'es', 'st', 'en', 'ed', 'to', 'it', 'ou', 'ea', 'hi',
            'is', 'or', 'ti', 'as', 'te', 'et', 'ng', 'of', 'al', 'de',
            'se', 'le', 'sa', 'si', 'ar', 've', 'ra', 'ld', 'ur'
        }
    
    @staticmethod
    def _load_common_suffixes() -> Set[str]:
        """Load common English suffixes."""
        return {
            'ing', 'ed', 'er', 'est', 'ly', 'able', 'ible', 'ful', 'ment',
            'ness', 'ous', 'ish', 'less', 'tion', 'sion', 'ize', 'ise',
            'ify', 'ity', 'ive', 'ize', 'dom', 'ship', 'hood', 'ance',
            'ence', 'ant', 'ent', 'ic', 'al', 'ical', 'ial', 'ious'
        }
    
    @staticmethod
    def _load_keyboard_patterns() -> Dict[str, Set[str]]:
        """Load keyboard-specific typing patterns."""
        return {
            'same_finger': {
                # Top row same finger
                {'qq', 'ww', 'ee', 'rr', 'tt', 'yy', 'uu', 'ii', 'oo', 'pp'},
                # Home row same finger
                {'aa', 'ss', 'dd', 'ff', 'gg', 'hh', 'jj', 'kk', 'll'},
                # Bottom row same finger
                {'zz', 'xx', 'cc', 'vv', 'bb', 'nn', 'mm'}
            },
            'awkward': {
                # Awkward three-letter combinations
                {'qaz', 'wsx', 'edc', 'rfv', 'tgb', 'yhn', 'ujm', 'ik,', 'ol.'},
                # Reverse direction awkward combinations
                {'zaq', 'xsw', 'cde', 'vfr', 'bgt', 'nhy', 'mju', ',ki', '.lo'}
            }
        }
