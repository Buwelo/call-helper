import os
from venv import logger
from flask import jsonify, request
from flask_login import current_user
import logging
from openai import OpenAI
import openai
from config.extensions import db
from models import TranscriptTest, UserTranscript
from datetime import datetime
from werkzeug.utils import secure_filename


# TODO use structured json results\
# TODO tune prompt to perfection so scoring is more accurate

openai.api_key = os.environ["OPENAI_API_KEY"]
logger = logging.getLogger(__name__)
client = OpenAI()


# id will be used to get the correct transcript from the database to compare
def score_transcription(id):
    logger.info(f"Scoring transcription for id: {id}")

    # Get the user submitted transcript from the request
    user_submitted_transcript = request.json.get('transcript')

    # Fetch the test data using the id
    test_data = TranscriptTest.query.get(id)

    if not test_data:
        return jsonify({
            'status': 'error',
            'message': f'No test found with id {id}'
        }), 404

    good_transcript = test_data.good_transcript

    content = """
You are an AI assistant knowledgeable in how transcriptions for accessibility needs especially the deaf are scored.
The transcriptions in this case are a result of a user correcting AI transcriptions on the fly for CaptionCall.
Given the user's transcript and the correct transcript, compare the two transcripts and provide a score on the following criteria:
- Audio cues like YAWN, LAUGHTER, and BABBLE, assign a score of 100
- Corrections made in terms of proper contextual word use, e.g. AI produced "rain" in transcript, user corrects it to "reign", assign a score of 100.
- Punctuation, e.g., AI produces "!" in transcript, user corrects it to ".", Emphasis on punctuations that can affect sentence meaning, assign a score of 100.

Provide a score out of 100 and a brief explanation for each criterion, scoring format should be text-based and brief and not more than 30 words.
Produce a value for each item above and assign "not applicable" if the criterion was not met.
Provide an overall percentage score for the entire test, as eg. (audio score + corrections score + punctuation/ 300) = Overall Percentage Score.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {'role': 'system', 'content': content},
                {
                    'role': 'user',
                    'content': f"User's transcript:\n{user_submitted_transcript}\n\nCorrect transcript:\n{good_transcript}"
                }
            ]
        )

        gpt4_score = response.choices[0].message.content
        
        result = UserTranscript(
            user_id=current_user.id,
            score=gpt4_score,
            test_taken=id,
            user_transcript=user_submitted_transcript
        )
        db.session.add(result)
        db.session.commit()

        print(f"User's transcript  saved: {result}")
        return jsonify({
            'test_id': id,
            'status': 'success',
            'message': 'Transcript scored successfully',
            # 'user_transcript': user_submitted_transcript[:100] + '...' if user_submitted_transcript else None,
            # 'correct_transcript': good_transcript[:100] + '...',
            'gpt4_score': gpt4_score
        })
        
        

    except Exception as e:
        logger.error(f"Error in scoring transcription: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while scoring the transcript'
        }), 500


UPLOAD_FOLDER = os.path.abspath('files')  # Or your desired path

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'srt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_test():
    if request.method != 'POST':
        return jsonify({'status': 'error', 'message': 'Method not allowed'}), 405
    
    # Get form data
    name_of_test = request.form.get('name_of_test')
    good_transcript = request.form.get('score_transcript')  # From frontend's score_transcript
    bad_transcript = request.form.get('test_transcript')    # From frontend's test_transcript
    
    # Input validation
    if not all([name_of_test, good_transcript, bad_transcript]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'status': 'error', 'message': 'Invalid file format'}), 400
    
    try:
        # Create new test object with initial values
        new_test = TranscriptTest(
            good_transcript=good_transcript,
            bad_transcript=bad_transcript,
            name_of_test=name_of_test
        )
        
        # Add and commit to get the ID
        db.session.add(new_test)
        db.session.flush()  # This gets us the ID without committing
        
        # Save the file
        filename = secure_filename(f'{new_test.id}.srt')
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        print(f"Saving file to: {file_path}")
        
        if os.path.exists(file_path): # Check for existing file
            filename = secure_filename(f'{new_test.id}.srt')
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            print(f"File already exists. Saving to: {file_path}")

        file.save(file_path)
        # Update the audio file path
        new_test.audio_file_path = file_path
        
        # Now commit everything
        db.session.commit()
        
        logger.info(f"New test created: {new_test.id}")
        return jsonify({
            'status': 'success',
            'message': 'Test created successfully',
            'test_id': new_test.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating test: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'An error occurred while creating the test: {str(e)}'
        }), 500