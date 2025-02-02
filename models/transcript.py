from config.extensions import db
from datetime import datetime


class TranscriptTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    good_transcript = db.Column(db.String(1500), nullable=False)  # Used to score test
    bad_transcript = db.Column(db.String(1500), nullable=False)  # Used to generate test

class UserTranscript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.JSON, nullable=True)  # Stores test scores in JSON format
    test_taken = db.Column(db.Integer, db.ForeignKey('transcripttest.id'), nullable=False)
    user_transcript = db.Column(db.String(1500), nullable=False)  # User's submitted transcript
    created_at = db.Column(db.DateTime, default=datetime.now())  # Auto-set on creation
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())  # Auto-set on update
