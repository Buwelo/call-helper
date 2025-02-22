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
from utility import transcript_compare


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

    compare_transcript_result = transcript_compare.compare_transcript(
        good_transcript, user_submitted_transcript)
    logger.info(f"Comparison result: {compare_transcript_result}")

    content = f"""
    You are an AI assistant tasked with scoring transcriptions for accessibility needs, particularly for the deaf. Follow these instructions:

    1. Comparison:
       - Compare the user's submitted transcript with the correct transcript.
       - Use the provided transcript comparison result as a reference.
       - Example comparison result: {transcript_compare.EXAMPLE_COMPARISON_RESULT}

    2. Scoring Rules:
       - Starting score: 200 points
       - For each mismatch: Subtract 5 points
       - Perfect match: Full score (200 points)
       - Ignore any words or characters in the user's transcript not present in the correct transcript

    3. Evaluation Criteria:
       - Ignore all timestamps
       - Disregard repeated lines in the user's submitted transcript
       - Focus on:
         a) Misspelled words
         b) Missing words
         c) Punctuation errors
         d) Transcript character count should be within 10% of the correct transcript character count else user has failed and should lose 50 points.
       - Do not make assumptions; evaluate based on observable differences only

    4. Feedback Requirements:
       - Provide an overall score based on the mismatches
       - Detail what the user missed and explain why
       - Give specific feedback on items missed or added
       - Summarize mismatches (e.g., "Total Mismatches detected: 5, resulting in 25 points lost")
       - Include relevant observations from the comparison result for context
       - Avoid any hallucinations or made-up information

    5. Output Format:
       - Scores should be in points, not percentages
       - Provide a detailed breakdown of differences between the transcripts
       - List every correction or miss by the user

    Remember: Your main focus is on accurately comparing the two texts and providing detailed, constructive feedback based on the observable differences.
    """
    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {'role': 'system', 'content': content},
                {
                    'role': 'user',
                    'content': f"User's transcript:\n{user_submitted_transcript}\n\nCorrect transcript:\n{good_transcript}\n\nTranscript comparison result:{compare_transcript_result}"
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
