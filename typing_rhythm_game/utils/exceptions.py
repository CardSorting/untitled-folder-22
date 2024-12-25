class GameDataError(Exception):
    """Exception raised for errors in game data validation or processing."""
    pass

class RateLimitExceeded(Exception):
    """Exception raised when a user exceeds the rate limit."""
    pass
