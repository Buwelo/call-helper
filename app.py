from flask import Flask, render_template, Response, request, redirect, url_for
from utility.utils import readSrtFile
from config.extensions import logging, db, login_manager
from config import create_app
from models import User
from flask_login import login_required
from controllers.transcriptionController import score_transcription
import os
from dotenv import load_dotenv

load_dotenv()

app = create_app(os.getenv('FLASK_ENV', 'development'))

@login_manager.user_loader
def load_user(user_id):
    print("run")
    return db.session.get(User, int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('auth.login'))

@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/stream')
@login_required
def stream():
    currenttime = request.args.get('currenttime', 0, type=float)  # Get currenttime from query params
    logging.info(f"currenttime: {currenttime}")
    return Response(readSrtFile('./files/call_with_mark.srt', currenttime), content_type='text/event-stream')

@app.route('/score-transcript', methods=['POST'])
@login_required
def score_transcript():
    return score_transcription()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)