import os
from typing import List
from venv import logger
from flask import json, jsonify, request
from flask_login import current_user
import logging
from openai import OpenAI, beta
import openai
from config.extensions import db
from models import TranscriptTest, UserTranscript
from datetime import datetime
from werkzeug.utils import secure_filename
from pydantic import BaseModel
from flask import render_template
import json

# TODO tune prompt to perfection so scoring is more accurate

class ScoreItem(BaseModel):
    category: str
    assigned_score: float
    comment: str


class Breakdown(BaseModel):
    score_items: List[ScoreItem]
    overall_score: float
    summary: str


openai.api_key = os.environ["OPENAI_API_KEY"]
logger = logging.getLogger(__name__)
client = OpenAI()


# id will be used to get the correct transcript from the database to compare
def score_transcription(id):
    """
    Scores a user-submitted transcript against a correct transcript from the database.

    Parameters:
        id (int): The identifier for the transcript test to be scored.

    Returns:
        Response: A JSON response containing the status of the scoring process.
                  On success, returns a status of 'success', the test ID, and the GPT-4 score.
                  On failure, returns a status of 'error' and an error message.
    """
    logger.info(f"Scoring transcription for id: {id}")

    # Get the user submitted transcript from the request
    user_submitted_transcript = request.json.get('transcript')
    data = request.get_json()

    testingId = data.get('testingId')

    logger.info(f"request : {request}")
    logger.info(f"Testing ID: {testingId}")


    logger.info(f"Data: {data}")
    # Fetch the test data using the id
    test_data = TranscriptTest.query.get(id)

    if not test_data:
        return jsonify({
            'status': 'error',
            'message': f'No test found with id {id}'
        }), 404

    good_transcript = test_data.good_transcript

    content = """
        You are an AI assistant knowledgeable in how transcriptions for accessibility needs, especially for the deaf, are scored.
        The transcriptions in this case are a result of a user potentially correcting AI transcriptions on the fly for CaptionCall. 
        Given the user's transcript and the correct transcript, compare the two transcripts and provide a score on the following criteria, also show the changes the user made (if any) as compared with the correct transcript:
        You shall ignore repeated lines in the script submitted if any.
You shall focus on differences between the user's transcript and the correct transcript and detail every correction or miss by the user in the score, main areas should be comparing the two texts and detailing the differences, misspelled words, missing words and punctuations.
You shall detail the changes the user made in comparison with the correct transcript.

        Provide a score out of 100 and a brief explanation for each criterion. The scoring format should be text-based and brief.
Accumulate a score of 10 for each correction made by the user.

The overall score should be the sum of the scores for each criterion in percentage"""
    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {'role': 'system', 'content': content},
                {
                    'role': 'user',
                    'content': f"User's transcript:\n{user_submitted_transcript}\n\nCorrect transcript:\n{good_transcript}"
                }
            ], response_format=Breakdown
        )

        gpt_score = response.choices[0].message.content
        gpt_score_raw = json.loads(gpt_score) 
        overall_score = gpt_score_raw.get('overall_score', 0)
        summary = gpt_score_raw.get('summary', '')

        result = UserTranscript(
            user_id=current_user.id,
            score=gpt_score,
            test_taken=id,
            user_transcript=user_submitted_transcript,
            testing_id=testingId,
            overall_score=overall_score,
            summary=summary
        )
        db.session.add(result)
        db.session.commit()

        print(f"User's transcript  saved: {result}")
        return jsonify({
            'test_id': id,
            'status': 'success',
            'message': 'Transcript scored successfully',
            'gpt_score': gpt_score
        })

    except Exception as e:
        logger.error(f"Error in scoring transcription: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while scoring the transcript'
        }), 500


SRT_UPLOAD_FOLDER = os.path.abspath('files')  # Or your desired path
AUDIO_UPLOAD_FOLDER = os.path.abspath('static/audio')  # Or your desired path

if not os.path.exists(SRT_UPLOAD_FOLDER):
    os.makedirs(SRT_UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'srt', 'm4a', 'wav', 'mp3', }
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_test():
    """
    Creates a new transcription test by processing uploaded SRT and audio files, 
    and storing the test details in the database.

    Returns:
        Response: A JSON response indicating the success or failure of the test creation.
                  On success, returns a status of 'success' and the test ID.
                  On failure, returns a status of 'error' and an error message.
    """
    if request.method != 'POST':
        return jsonify({'status': 'error', 'message': 'Method not allowed'}), 405

    logger.info(f"request: {request.files}")

    name_of_test = request.form.get('name_of_test')
    good_transcript = request.form.get('score_transcript')
    bad_transcript = request.form.get('test_transcript')

    if not all([name_of_test, good_transcript, bad_transcript]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    # Check for multiple SRT files
    srt_files = request.files.getlist('srt_file')
    if not srt_files:
        return jsonify({'status': 'error', 'message': 'No SRT files part'}), 400

    # Check for multiple audio files
    audio_files = request.files.getlist('audio_file')
    if not audio_files:
        return jsonify({'status': 'error', 'message': 'No audio files part'}), 400

    try:
        new_test = TranscriptTest(
            good_transcript=good_transcript,
            bad_transcript=bad_transcript,
            name_of_test=name_of_test
        )

        db.session.add(new_test)
        db.session.flush()  # Get the ID

        # Save each SRT file
        for srt_file in srt_files:
            if srt_file.filename == '':
                continue
            if not allowed_file(srt_file.filename):
                return jsonify({'status': 'error', 'message': 'Invalid SRT file format'}), 400

            srt_filename = secure_filename(f'{new_test.id}.srt')
            srt_file_path = os.path.join(SRT_UPLOAD_FOLDER, srt_filename)
            srt_file.save(srt_file_path)
            # Assuming you have a way to store multiple SRT file paths in your model

        # Save each audio file
        for audio_file in audio_files:
            if audio_file.filename == '':
                continue
            if not allowed_file(audio_file.filename):
                return jsonify({'status': 'error', 'message': 'Invalid audio file format'}), 400

            audio_extension = os.path.splitext(audio_file.filename)[1]

            audio_filename = secure_filename(f'{new_test.id}{audio_extension}')
            audio_file_path = os.path.join(AUDIO_UPLOAD_FOLDER, audio_filename)
            audio_file.save(audio_file_path)

            new_test.audio_file_path = f'/audio/{new_test.id}{audio_extension}'
            new_test.srt_file_path = f'./files/{new_test.id}.srt'

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


def get_tests():
    """
    Retrieves all transcription tests from the database.
    Returns:
    Response: A JSON response containing the status and a list of test details.
    """
    logger.info("Getting all transcription tests")
    tests = TranscriptTest.query.all()
    return jsonify({
        'status': 'success',
        'tests': [test.serialize() for test in tests]
    })


def take_tests():
    testing_id = datetime.now().strftime("%Y%m%d%H%M%S")
    tests = TranscriptTest.query.all()
    tests_data = []
    for test in tests:
        tests_data.append({
            'id': test.id,
            'name_of_test': test.name_of_test,
            'good_transcript': test.good_transcript,
            'bad_transcript': test.bad_transcript,
            'audio_file_path': test.audio_file_path,
            'srt_file_path': test.srt_file_path
        })
    return render_template('take_test.html', tests=tests_data, testing_id=testing_id)
