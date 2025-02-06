from datetime import datetime
import logging
import re
from time import sleep
from flask import Blueprint, Response, render_template, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from flask_login import login_required, current_user
from controllers import transcriptionController


transcription = Blueprint('transcription', __name__)
socketio = SocketIO()


class SubtitleEntry:
    def __init__(self, index, start_time, end_time, text):
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text

def parse_time(time_str):
    """Convert SRT timestamp to seconds"""
    time_obj = datetime.strptime(time_str.replace(',', '.'), '%H:%M:%S.%f')
    return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1000000

class SRTHandler:
    def __init__(self):
        self._subtitle_cache = {}  # Cache for parsed subtitles

    def read_srt_file(self, file_path):
        """Read and cache SRT file if not already cached"""
        if file_path not in self._subtitle_cache:
            entries = []
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                blocks = content.split('\n\n')
                
                for block in blocks:
                    lines = block.split('\n')
                    if len(lines) >= 3:
                        index = int(lines[0])
                        time_line = lines[1]
                        text = '\n'.join(lines[2:])
                        
                        time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', time_line)
                        if time_match:
                            start_time = parse_time(time_match.group(1))
                            end_time = parse_time(time_match.group(2))
                            entries.append(SubtitleEntry(index, start_time, end_time, text))
            
            self._subtitle_cache[file_path] = sorted(entries, key=lambda x: x.start_time)
        
        return self._subtitle_cache[file_path]

    def find_subtitle_at_time(self, entries, current_time):
        """Find the subtitle that should be displayed at the given time"""
        for entry in entries:
            if entry.start_time <= current_time <= entry.end_time:
                return entry
        return None

# Create a global instance of SRTHandler
srt_handler = SRTHandler()

@socketio.on('connect')
@login_required
def handle_connect():
    """Handle WebSocket connection"""
    logging.info(f"Client connected: {current_user.id}")
    emit('connection_established', {'status': 'connected'})

@socketio.on('request_transcription')
@login_required
def handle_transcription(data):
    """
    Handle transcription requests via WebSocket
    Expects data with currentTime and fileId
    """
    try:
        current_time = float(data.get('currentTime', 0))
        
        
      
        # Use a default file path
        srtFile = './files/caption_call.srt'


        # Get subtitle entries (cached if already read)
        # Get subtitle entries (cached if already read)
        subtitle_entries = srt_handler.read_srt_file(srtFile)
        
        # Find current subtitle
        current_subtitle = srt_handler.find_subtitle_at_time(subtitle_entries, current_time)
        
        if current_subtitle:
            # Emit in the format expected by the frontend
            emit('transcription_segment', {
                'start': current_subtitle.start_time,
                'end': current_subtitle.end_time,
                'text': current_subtitle.text.strip()
            })
                
    except FileNotFoundError as e:
        logging.error(f"SRT file not found: {str(e)}")
        emit('transcription_error', {'error': 'Subtitle file not found'})
    except Exception as e:
        logging.error(f"Error in handle_transcription: {str(e)}")
        emit('transcription_error', {'error': str(e)})

@socketio.on('disconnect')
def handle_disconnect():
    logging.info(f"Client disconnected: {current_user.id}")

# Score Test
@transcription.route('/score-transcription/<int:id>', methods=['POST'])
@login_required
def score_transcription(id):
	return transcriptionController.score_transcription(id)

# Create Test
@transcription.route('/create_test', methods=['GET', 'POST'])
@login_required
def create_test():
    if request.method == 'POST':
        return transcriptionController.create_test()
    return render_template('create_test.html')