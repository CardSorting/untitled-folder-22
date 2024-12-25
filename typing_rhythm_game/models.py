from datetime import datetime
from flask_login import UserMixin
from . import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    scores = db.relationship('Score', backref='user', lazy=True)
    stats = db.relationship('GameStats', backref='user', lazy=True, uselist=False)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    words_typed = db.Column(db.Integer, nullable=False)
    time_taken = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class GameStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_games = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Integer, default=0)
    high_score = db.Column(db.Integer, default=0)
    total_words = db.Column(db.Integer, default=0)
    total_accuracy = db.Column(db.Float, default=0)
    avg_accuracy = db.Column(db.Float, default=0)
    last_played = db.Column(db.DateTime)

    def update_stats(self, score, accuracy, words):
        self.total_games += 1
        self.total_score += score
        self.high_score = max(self.high_score, score)
        self.total_words += words
        self.total_accuracy += accuracy
        self.avg_accuracy = self.total_accuracy / self.total_games
        self.last_played = datetime.utcnow()
