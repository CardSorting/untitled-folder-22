from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class WordDifficulty:
    """Stores difficulty metrics for a word."""
    word: str
    length_score: float
    complexity_score: float
    pattern_score: float
    typing_score: float
    final_score: float
    
    def get_level(self) -> int:
        """Get the integer difficulty level (1-5)."""
        return max(1, min(5, round(self.final_score)))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'word': self.word,
            'metrics': {
                'length_score': self.length_score,
                'complexity_score': self.complexity_score,
                'pattern_score': self.pattern_score,
                'typing_score': self.typing_score,
                'final_score': self.final_score,
                'level': self.get_level()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WordDifficulty':
        """Create instance from dictionary format."""
        metrics = data['metrics']
        return cls(
            word=data['word'],
            length_score=metrics['length_score'],
            complexity_score=metrics['complexity_score'],
            pattern_score=metrics['pattern_score'],
            typing_score=metrics['typing_score'],
            final_score=metrics['final_score']
        )
