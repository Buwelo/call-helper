from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from controllers import transcriptionController

transcription = Blueprint('transcription', __name__)

@transcription.route('/score-transcription/<int:id>', methods=['POST'])
@login_required
def score_transcription(id):
	return transcriptionController.score_transcription(id)