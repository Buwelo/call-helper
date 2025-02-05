import logging
from flask import Blueprint, Response, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from controllers import transcriptionController
from utility.utils import readSrtFile

transcription = Blueprint('transcription', __name__)

@transcription.route('/stream')
@transcription.route('/stream/<int:id>')
@login_required
def stream(id=None):
    currenttime = request.args.get('currenttime', 0, type=float)  # Get currenttime from query params
    logging.info(f"currenttime: {currenttime}, id: {id} ")
    return Response(readSrtFile('./files/call_with_mark.srt', currenttime, id), content_type='text/event-stream')


@transcription.route('/score-transcription/<int:id>', methods=['POST'])
@login_required
def score_transcription(id):
	return transcriptionController.score_transcription(id)