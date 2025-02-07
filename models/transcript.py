from config.extensions import db
from datetime import datetime, timezone


class TranscriptTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    good_transcript = db.Column(db.String(15000), nullable=False)  # Used to score test
    bad_transcript = db.Column(db.String(15000), nullable=False)  # Used to generate test
    audio_file_path = db.Column(db.String(200), nullable=True)  # Path to audio file for test
    srt_file_path = db.Column(db.String(200), nullable=True)  # Path to srt file for test
    name_of_test = db.Column(db.String(150), nullable=False)  # Name of the test
    def __repr__(self):
        return f'<TranscriptTest {self.id}>'
    
    
class UserTranscript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.String(15000), nullable=False)  # Stores test scores in JSON format
    test_taken = db.Column(db.Integer, db.ForeignKey('transcript_test.id'), nullable=False)
    user_transcript = db.Column(db.String(15000), nullable=False)  # User's submitted transcript
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Auto-set on creation
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=datetime.now())  # Auto-set on update
