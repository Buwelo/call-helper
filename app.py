import logging
import random
from flask import render_template, redirect, url_for
from flask_socketio import SocketIO
from config.extensions import db, login_manager
from config import create_app
from models import User, TranscriptTest
from flask_login import login_required
from routes.transcript import handle_connect, handle_transcription
import os
from dotenv import load_dotenv

load_dotenv()

app = create_app(os.getenv('FLASK_ENV', 'development'))
socketio = SocketIO(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50 MB


@login_manager.user_loader
def load_user(user_id):
    # print("run")
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('auth.login'))



@app.route('/')
@login_required
def index():
    return render_template('home.html')

@app.route('/practice')
@login_required

def home():
    tests = [test.serialize() for test in TranscriptTest.query.all()]
    if not tests:
        return render_template('error.html', message="No tests available")
    random_test = random.choice(tests)
    # logging.info(f'random test, {random_test}')

    audio_file = random_test.get('audio_file_path')
    srt_file = random_test.get('srt_file_path')
    return render_template('index.html', audio_file=audio_file, srt_file=srt_file, random_test=random_test)


# Register your socket event handlers
socketio.on_event('connect', handle_connect)
socketio.on_event('request_transcription', handle_transcription)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
