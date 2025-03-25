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


openai.api_key = os.environ["OPENAI_API_KEY"]
logger = logging.getLogger(__name__)
client = OpenAI()

# id will be used to get the correct transcript from the database to compare

def aiEvaluation(user_transcript, correct_transcript, scoring_function_eval):
        """
        Evaluates a user's transcript to provide additional feedback and a possible score adjustment.
        """
        scoring_function_eval = str(scoring_function_eval)
        
        example_evaluation = {
    "corrected_errors": 1,
    "error_tracking": {
        "corrected_errors": 1,
        "message": "Found and fixed 1 out of 2 intentional errors (50.00%)",
        "missed_errors": [
            {
                "correct": "little tiny thing.",
                "error": "little.",
                "id": "E2",
                "type": "replace"
            }
        ],
        "percentage": 50,
        "similarity": 99.02,
        "status": "success",
        "total_errors": 2
    },
    "message": "Found and fixed 1 out of 2 intentional errors (50.00%) Punctuation errors: 1",
    "percentage": 50,
    "punctuation_errors": 1,
    "readable_diff": "MATCH: out in the garden\n\nDELETE: ','\n\nMATCH: mary sat hemming a pocket handkerchief , and there came a little insect running , oh , in such a hurry , across the small stone table by her side . the sewing was done , for mary liked doing nothing best , and she thought it would be fun to drop her thimble over the little ant . now he is in the dark , said she , keep in mind he is only such a little\n\nDELETE: 'tiny thing'\n\nMATCH: . mary ran away , for her mother called her , and she forgot all about the ant under the thimble . there he was , running round and round and round the dark prison , with little horns on his head , quivering , little perfect legs bending as beautifully as those of a racehorse , and he was in quite as big a fright as if he were an elephant . oh , you would have heard him say , if you had been clever enough , i can ' t get out , i can ' t get out , i shall lie down and die . mary went to bed , and in the night the rain poured , the handkerchief was soaked as if somebody had been crying very much . when she went out to fetch it as soon as the sun shone , she remembered who was under the thimble . i wonder what he is doing , said mary , but when she lifted up the thimble , the little tiny thing lay stiff and still . oh , did he die of being under the thimble , said she aloud , i am afraid he did mine . why did you do that , mary , said her father , who was close by and who had guessed the truth . see , he moved one of his legs . run to the house and fetch a wee taste of honey from the breakfast table for the little thing you starved . i didn ' t mean to , said mary . she touched the honey in the spoon .\n",
    "similarity": 99.58620689655172,
    "status": "success",
    "total_errors": 2
}
        converted_example_evaluation = json.dumps(example_evaluation)
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"""You are an AI assistant tasked with evaluating and potentially adjusting scores based on user transcripts. Here's what you need to do:
                                                        1. Compare the user's transcript, correct_transcript and evaluation from the scoring program.
                                                        2. The evaluation is a result of a scoring program. Here's an example of an evaluation for a user's transcript: {converted_example_evaluation}.
                                                        3. Your response should include:
                                                        - An adjusted score (either the same as the original from the evaluation or different if adjusted).
                                                        - A brief summary explaining what triggered any adjustments.

                                                        Please analyze the following:
                                                        the following user transcript:
                                                        {user_transcript},
                                                        the following correct transcript:
                                                        {correct_transcript},
                                                        the following evaluation:
                                                        {scoring_function_eval}

                                                        Based on this information, provide your analysis and any score adjustments."""},
                    {"role": "user", "content": f"Compare the following user transcript to the correct transcript and provide feedback. User transcript: {user_transcript}. Correct transcript: {correct_transcript}. Initial score evaluation: {scoring_function_eval}"}
                ],
                temperature=0.7,
                max_tokens=300,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            ai_response = response.choices[0].message.content
            return ai_response
        except Exception as e:
            logger.error(f"Error in AI evaluation: {str(e)}")
            return "Error in AI evaluation"
    
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
    # logger.info(f"Scoring transcription for id: {id}")

    # Get the user submitted transcript from the request
    user_submitted_transcript = request.json.get('transcript')
    data = request.get_json()

    testingId = data.get('testingId')

    # Fetch the test data using the id
    test_data = TranscriptTest.query.get(id)

    if not test_data:
        return jsonify({
            'status': 'error',
            'message': f'No test found with id {id}'
        }), 404

    good_transcript = test_data.good_transcript
    bad_transcript = test_data.bad_transcript

    compare_transcript_result = transcript_compare.compare_transcript_with_errors(
        good_transcript, bad_transcript, user_submitted_transcript)
    
    aiEvaluation_result = aiEvaluation( user_submitted_transcript, good_transcript, compare_transcript_result)
    
    logger.info(f"AI evaluation result: {aiEvaluation_result}")

    userResult = UserTranscript(
        testing_id=testingId,
        user_transcript=user_submitted_transcript,
        score=json.dumps(compare_transcript_result),
        test_taken=id,
        user_id=current_user.id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        overall_score=compare_transcript_result.get('percentage'),
        summary=compare_transcript_result.get('message'),
    )
    db.session.add(userResult)
    db.session.commit()

    logger.info(
        f"Compare transcript result: {compare_transcript_result}")
    return compare_transcript_result


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


def edit_test(id):
    """
    Edits an existing transcription test by updating the test details in the
    database with the provided data.
    """

    test = TranscriptTest.query.get(id)
    if not test:
        return jsonify({'status': 'error', 'message': 'Test not found'}), 404

    # Get form data
    if request.method == 'PATCH':
        data = request.json
        test.name_of_test = data.get('name_of_test', test.name_of_test)
        test.good_transcript = data.get(
            'score_transcript', test.good_transcript)
        test.bad_transcript = data.get('test_transcript', test.bad_transcript)
        test.benchmark_score = data.get(
            'benchmark_score', test.benchmark_score)

        # Save changes
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Test updated successfully'}), 200


def get_single_test(id):
    """
    Retrieves a single transcription test from the database based on its ID.
    Returns:
    Response: A JSON response containing the status and the test details.
    """
    logger.info(f"Getting test with ID: {id}")
    test = TranscriptTest.query.get(id)
    if not test:
        return jsonify({'status': 'error', 'message': 'Test not found'}), 404
    return jsonify({
        'status': 'success',
        'test': test.serialize()
    })


def get_tests():
    """
    Retrieves all transcription tests from the database.
    Returns:
    Response: A JSON response containing the status and a list of test details.
    """
    logger.info("Getting all transcription tests")
    tests = TranscriptTest.query.all()
    return render_template('tests.html', tests=tests)


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
