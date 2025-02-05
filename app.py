from flask import render_template, redirect, url_for
from flask_socketio import SocketIO
from config.extensions import db, login_manager
from config import create_app
from models import User
from flask_login import login_required
from routes.transcript import handle_connect, handle_transcription
import os
from dotenv import load_dotenv

load_dotenv()

app = create_app(os.getenv('FLASK_ENV', 'development'))
socketio = SocketIO(app)

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

# Import your socket event handlers

# Register your socket event handlers
socketio.on_event('connect', handle_connect)
socketio.on_event('request_transcription', handle_transcription)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)