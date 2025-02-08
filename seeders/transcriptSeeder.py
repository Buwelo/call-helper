from models.transcript import TranscriptTest
from config.extensions import db
from sqlalchemy import inspect
from .transcripts import good_transcript, bad_transcript

def create_tables_if_not_exist():
    inspector = inspect(db.engine)
    if not inspector.has_table('transcript_test'):
        TranscriptTest.__table__.create(db.engine)

def seed_transcripts():
    # First check and create tables if they don't exist
    create_tables_if_not_exist()

    # Check if data already exists to avoid duplicates
    existing_records = TranscriptTest.query.first()
    if existing_records:
        print("Data already exists in transcript_test table")
        return

    good_transcript_ = good_transcript
    bad_transcript_ = bad_transcript
    
    test1 = TranscriptTest(
        good_transcript=good_transcript_,
        bad_transcript=bad_transcript_,
        audio_file_path="audio_file_path",
        name_of_test="Test 1"  # Replace with actual name of the tes
    )

    try:
        db.session.add(test1)
        db.session.commit()
        print("Successfully seeded transcript_test table")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding data: {str(e)}")

if __name__ == '__main__':
    seed_transcripts()

# TODO: ADD AUDIO file upload too