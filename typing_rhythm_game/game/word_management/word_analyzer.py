class WordAnalyzer:
    """Analyzes words for typing patterns and difficulty."""

    def __init__(self):
        """Initialize the word analyzer with keyboard patterns."""
        self._keyboard_patterns = self._load_keyboard_patterns()

    def analyze_word(self, word):
        """
        Analyze a word for typing patterns and difficulty.
        
        Args:
            word (str): The word to analyze
            
        Returns:
            dict: Analysis results including patterns found and difficulty score
        """
        if not word:
            return {'difficulty': 0, 'patterns': []}

        patterns = []
        for i in range(len(word) - 1):
            current_char = word[i].lower()
            next_char = word[i + 1].lower()
            
            # Check for same finger usage
            if self._is_same_finger(current_char, next_char):
                patterns.append(('same_finger', current_char + next_char))
            
            # Check for alternating hands
            if self._is_alternating_hands(current_char, next_char):
                patterns.append(('alternating_hands', current_char + next_char))
            
            # Check for rolling motion
            if self._is_rolling_motion(current_char, next_char):
                patterns.append(('rolling', current_char + next_char))

        # Calculate difficulty based on patterns
        difficulty = self._calculate_difficulty(patterns, len(word))

        return {
            'difficulty': difficulty,
            'patterns': patterns
        }

    def _is_same_finger(self, char1, char2):
        """Check if two characters are typed with the same finger."""
        for finger_keys in self._keyboard_patterns['same_finger']:
            if char1 in finger_keys and char2 in finger_keys:
                return True
        return False

    def _is_alternating_hands(self, char1, char2):
        """Check if two characters are typed with alternating hands."""
        left_hand = self._keyboard_patterns['left_hand']
        right_hand = self._keyboard_patterns['right_hand']
        
        return (char1 in left_hand and char2 in right_hand) or \
               (char1 in right_hand and char2 in left_hand)

    def _is_rolling_motion(self, char1, char2):
        """Check if two characters create a rolling motion."""
        for roll in self._keyboard_patterns['rolling']:
            if char1 + char2 in roll or char2 + char1 in roll:
                return True
        return False

    def _calculate_difficulty(self, patterns, word_length):
        """Calculate difficulty score based on patterns and word length."""
        if word_length == 0:
            return 0

        # Base difficulty from word length
        difficulty = word_length * 0.5

        # Pattern weights
        weights = {
            'same_finger': 2.0,
            'alternating_hands': -0.5,  # Reduces difficulty
            'rolling': -0.3  # Slightly reduces difficulty
        }

        # Add pattern-based difficulty
        for pattern_type, _ in patterns:
            difficulty += weights.get(pattern_type, 0)

        # Normalize to 1-10 scale
        difficulty = max(1, min(10, difficulty))
        
        return round(difficulty, 1)

    def _load_keyboard_patterns(self):
        """Load keyboard typing patterns."""
        return {
            'same_finger': [
                {'1', 'q', 'a', 'z'},  # Left pinky
                {'2', 'w', 's', 'x'},  # Left ring
                {'3', 'e', 'd', 'c'},  # Left middle
                {'4', '5', 'r', 't', 'f', 'g', 'v', 'b'},  # Left index
                {'6', '7', 'y', 'u', 'h', 'j', 'n', 'm'},  # Right index
                {'8', 'i', 'k', ','},  # Right middle
                {'9', 'o', 'l', '.'},  # Right ring
                {'0', 'p', ';', '/'}   # Right pinky
            ],
            'left_hand': {'q', 'w', 'e', 'r', 't', 'a', 's', 'd', 'f', 'g', 'z', 'x', 'c', 'v', 'b'},
            'right_hand': {'y', 'u', 'i', 'o', 'p', 'h', 'j', 'k', 'l', 'n', 'm'},
            'rolling': [
                'qwe', 'wer', 'ert', 'rty', 'tyu', 'yui', 'uio', 'iop',
                'asd', 'sdf', 'dfg', 'fgh', 'ghj', 'hjk', 'jkl',
                'zxc', 'xcv', 'cvb', 'vbn', 'bnm'
            ]
        }
