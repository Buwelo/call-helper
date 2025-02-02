from venv import logger
from flask import jsonify, request
import logging
logger = logging.getLogger(__name__)

def score_transcription():
    logger.info('Scoring transcript')
    if request.method == 'POST':
        logger.info('Received POST request')
        # Use request.json instead of request.form for JSON data
        data = request.json
        transcript = data.get('transcript')
        
        logger.info(f'Transcript: {transcript}')
        
        # Process the transcript data here
        return jsonify({
            'status': 'success',
            'transcript': transcript
        })

# get user transcript
# get good transcript

def store_good_transcript():
	pass

