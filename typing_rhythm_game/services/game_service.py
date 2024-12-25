from typing import Dict, Optional, Tuple, List
from flask import current_app
from ..models import User, Score, GameStats, db
from ..utils.exceptions import GameDataError
from ..game.mechanics import GameMechanics, WordChallenge
from datetime import datetime
import logging
from flask_caching import Cache

logger = logging.getLogger(__name__)
cache = Cache()

class GameSession:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.combo_count = 0
        self.active_power_ups = []
        self.current_challenge = None
        self.total_score = 0
        self.words_completed = 0
        self.avg_accuracy = 0.0
        self.start_time = datetime.now()

class GameService:
    _active_sessions = {}  # Store active game sessions
    
    @staticmethod
    def get_user_stats(user_id: int) -> Dict:
        """
        Get comprehensive user statistics.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Dict containing user statistics
            
        Raises:
            GameDataError: If there's an error retrieving stats
        """
        try:
            stats = GameStats.query.filter_by(user_id=user_id).first()
            if not stats:
                stats = GameStats(user_id=user_id)
                db.session.add(stats)
                db.session.commit()
                
            # Get recent high scores
            recent_scores = Score.query.filter_by(user_id=user_id)\
                .order_by(Score.score.desc())\
                .limit(5)\
                .all()
            
            return {
                'total_games': stats.total_games,
                'high_score': stats.high_score,
                'avg_accuracy': round(stats.avg_accuracy, 2) if stats.avg_accuracy else 0,
                'total_words': stats.total_words,
                'level': GameService._calculate_user_level(stats),
                'recent_scores': [
                    {
                        'score': score.score,
                        'accuracy': score.accuracy,
                        'date': score.timestamp.strftime('%Y-%m-%d %H:%M')
                    }
                    for score in recent_scores
                ]
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}", exc_info=True)
            raise GameDataError("Failed to retrieve user statistics")

    @staticmethod
    def start_game_session(user_id: int) -> Dict:
        """
        Start a new game session for the user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Dict containing initial game state
        """
        try:
            # Clear any existing session
            if user_id in GameService._active_sessions:
                GameService.end_game_session(user_id)
            
            # Create new session
            session = GameSession(user_id)
            GameService._active_sessions[user_id] = session
            
            # Get initial challenge
            challenge = GameService.get_next_challenge(user_id)
            session.current_challenge = challenge
            
            return {
                'session_started': True,
                'challenge': challenge,
                'power_ups_available': session.active_power_ups,
                'combo_count': session.combo_count
            }
        except Exception as e:
            logger.error(f"Error starting game session: {str(e)}", exc_info=True)
            raise GameDataError("Failed to start game session")

    @staticmethod
    def get_next_challenge(user_id: int) -> Dict:
        """
        Generate the next word challenge for the user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Dict containing the challenge details
        """
        try:
            session = GameService._active_sessions.get(user_id)
            if not session:
                session = GameSession(user_id)
                GameService._active_sessions[user_id] = session
            
            stats = GameStats.query.filter_by(user_id=user_id).first()
            user_level = GameService._calculate_user_level(stats) if stats else 1
            
            mechanics = GameMechanics(current_app.config['GAME_CONFIG'])
            challenge = mechanics.generate_challenge(user_level)
            session.current_challenge = challenge
            
            return {
                'word': challenge.word,
                'time_limit': challenge.time_limit,
                'points_possible': challenge.points,
                'level': challenge.level,
                'combo_requirement': challenge.combo_requirement,
                'power_ups': challenge.power_ups,
                'rhythm_pattern': challenge.rhythm_pattern
            }
        except Exception as e:
            logger.error(f"Error generating challenge: {str(e)}", exc_info=True)
            raise GameDataError("Failed to generate challenge")

    @staticmethod
    def submit_score(user_id: int, score_data: Dict) -> Dict:
        """
        Submit and process a game score.
        
        Args:
            user_id: The ID of the user
            score_data: Dict containing score details
            
        Returns:
            Dict containing the submission results
        """
        try:
            GameService._validate_score_data(score_data)
            session = GameService._active_sessions.get(user_id)
            
            if not session:
                raise GameDataError("No active game session found")
            
            mechanics = GameMechanics(current_app.config['GAME_CONFIG'])
            final_score, accuracy, combo_maintained = mechanics.calculate_score(
                score_data['typed_word'],
                score_data['target_word'],
                score_data['time_taken'],
                score_data['time_limit'],
                session.combo_count,
                session.active_power_ups
            )
            
            # Update session stats
            session.total_score += final_score
            session.words_completed += 1
            session.avg_accuracy = (
                (session.avg_accuracy * (session.words_completed - 1) + accuracy) /
                session.words_completed
            )
            
            # Update combo
            if combo_maintained:
                session.combo_count += 1
            else:
                session.combo_count = 0
            
            # Process power-ups
            GameService._process_power_ups(session, score_data.get('power_ups_used', []))
            
            # Save score to database
            score = Score(
                user_id=user_id,
                score=final_score,
                accuracy=accuracy,
                words_typed=1,
                time_taken=score_data['time_taken']
            )
            db.session.add(score)
            
            # Update user stats
            stats = GameStats.query.filter_by(user_id=user_id).first()
            if not stats:
                stats = GameStats(user_id=user_id)
                db.session.add(stats)
            
            stats.update_stats(
                score=final_score,
                accuracy=accuracy,
                words=1
            )
            
            db.session.commit()
            
            # Generate next challenge
            next_challenge = GameService.get_next_challenge(user_id)
            
            return {
                'score': final_score,
                'accuracy': accuracy,
                'combo_count': session.combo_count,
                'total_score': session.total_score,
                'words_completed': session.words_completed,
                'avg_accuracy': round(session.avg_accuracy, 1),
                'active_power_ups': session.active_power_ups,
                'next_challenge': next_challenge,
                'new_level': GameService._calculate_user_level(stats),
                'high_score': stats.high_score
            }
            
        except GameDataError as e:
            logger.warning(f"Invalid score data: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error submitting score: {str(e)}", exc_info=True)
            db.session.rollback()
            raise GameDataError("Failed to submit score")

    @staticmethod
    def end_game_session(user_id: int) -> Dict:
        """
        End the current game session and save final stats.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Dict containing final session stats
        """
        try:
            session = GameService._active_sessions.get(user_id)
            if not session:
                raise GameDataError("No active game session found")
            
            # Calculate final stats
            duration = (datetime.now() - session.start_time).total_seconds()
            words_per_minute = (session.words_completed * 60) / duration if duration > 0 else 0
            
            final_stats = {
                'total_score': session.total_score,
                'words_completed': session.words_completed,
                'avg_accuracy': round(session.avg_accuracy, 1),
                'duration': round(duration, 1),
                'words_per_minute': round(words_per_minute, 1)
            }
            
            # Clear session
            del GameService._active_sessions[user_id]
            
            return final_stats
            
        except Exception as e:
            logger.error(f"Error ending game session: {str(e)}", exc_info=True)
            raise GameDataError("Failed to end game session")

    @staticmethod
    def _calculate_user_level(stats: GameStats) -> int:
        """Calculate user level based on their statistics."""
        if not stats:
            return 1
            
        # Base level from total words typed
        base_level = min(stats.total_words // 50, 4)  # Every 50 words increases level
        
        # Bonus level from accuracy
        accuracy_bonus = 1 if stats.avg_accuracy and stats.avg_accuracy >= 95 else 0
        
        return base_level + accuracy_bonus + 1

    @staticmethod
    def _validate_score_data(data: Dict) -> None:
        """Validate score submission data."""
        required_fields = ['typed_word', 'target_word', 'time_taken', 'time_limit']
        
        if not all(field in data for field in required_fields):
            raise GameDataError("Missing required fields in score data")
            
        if not isinstance(data['time_taken'], (int, float)) or data['time_taken'] < 0:
            raise GameDataError("Invalid time_taken value")
            
        if not isinstance(data['time_limit'], (int, float)) or data['time_limit'] < 0:
            raise GameDataError("Invalid time_limit value")
            
        if not isinstance(data['typed_word'], str) or not isinstance(data['target_word'], str):
            raise GameDataError("Invalid word data types")

    @staticmethod
    def _process_power_ups(session: GameSession, power_ups_used: List[str]) -> None:
        """Process power-ups used in the current turn."""
        # Remove used one-time power-ups
        one_time_power_ups = {'time_freeze', 'point_boost', 'instant_clear'}
        session.active_power_ups = [
            p for p in session.active_power_ups
            if p not in one_time_power_ups or p not in power_ups_used
        ]
        
        # Process new power-ups
        for power_up in power_ups_used:
            if power_up not in session.active_power_ups:
                session.active_power_ups.append(power_up)
