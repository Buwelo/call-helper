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
You are an AI assistant knowledgeable in how transcriptions for accessibility needs are scored.
The transcriptions in this case are a result of a user correcting AI transcriptions on the fly.
Given the user's transcript and the correct transcript, compare the two transcripts and provide a score on the following criteria:
- Audio cues like YAWN, LAUGHTER, and BABBLE, assign a score of 100
- Corrections made in terms of proper contextual word use, e.g. AI produced "rain" in transcript, user corrects it to "reign", assign a score of 100.
- Punctuation, e.g., AI produces "!" in transcript, user corrects it to ".", Emphasis on punctuations that can affect sentence meaning, assign a score of 100.

Provide a score out of 100 and a brief explanation for each criterion.
Produce a value for each item above
Provide an overall percentage score for the entire test, as eg. (audio score + corrections score + punctuation/ 300) = Overall Percentage Score
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
