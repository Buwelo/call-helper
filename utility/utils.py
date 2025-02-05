# utils.py
from datetime import datetime
import time
import logging
import json
from models.transcript import TranscriptTest


logger = logging.getLogger(__name__)

def parse_time(time_str):
    """Convert SRT timestamp to seconds"""
    hours, minutes, seconds = time_str.replace(',', '.').split(':')
    return float(hours) * 3600 + float(minutes) * 60 + float(seconds)

def find_subtitle_for_time(subtitles, current_time):
    """Find the subtitle that matches the current time"""
    for subtitle in subtitles:
        if subtitle['start'] <= current_time <= subtitle['end']:
            return subtitle
    return None

def readSrtFile(filename=None, current_audio_time=0, id=None):
    logger.info(f"Current audio time received: {current_audio_time}")
    
    try:
        # Parse and cache subtitles
        subtitles = []
        
        if id is not None:
            # Fetch transcript from database based on id
            # This is a placeholder - you need to implement the actual database query
            db_transcript = TranscriptTest.query.filter_by(id=id).first().bad_transcript
            lines = db_transcript.split('\n')
        else:
            # Use the default file if no id is provided
            filename = './files/call_with_mark.srt'
            with open(filename, 'r', encoding='utf-8') as srt_file:
                lines = srt_file.readlines()

        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            try:
                # Parse subtitle number
                subtitle_number = int(line)
                time_line = lines[i + 1].strip()
                text_lines = []
                
                # Get all text lines
                i += 2
                while i < len(lines) and lines[i].strip():
                    text_lines.append(lines[i].strip())
                    i += 1
                
                # Parse time range
                start_time_str, end_time_str = time_line.split(' --> ')
                start_time = parse_time(start_time_str)
                end_time = parse_time(end_time_str)
                
                subtitles.append({
                    'number': subtitle_number,
                    'start': start_time,
                    'end': end_time,
                    'text': ' '.join(text_lines)
                })
                
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing subtitle at line {i}: {e}")
                i += 1
                continue
            
            i += 1
        
        # Track last sent subtitle to avoid duplicates
        last_sent_text = None
        
        while True:
            try:
                # Find matching subtitle for current time
                current_subtitle = find_subtitle_for_time(subtitles, float(current_audio_time))
                
                if current_subtitle and current_subtitle['text'] != last_sent_text:
                    last_sent_text = current_subtitle['text']
                    response_data = {
                        'text': current_subtitle['text'],
                        'start': current_subtitle['start'],
                        'end': current_subtitle['end']
                    }
                    yield f"data: {json.dumps(response_data)}\n\n"
                elif not current_subtitle and last_sent_text is not None:
                    # Clear subtitle when no match is found
                    last_sent_text = None
                    yield f"data: {json.dumps({'text': '', 'start': 0, 'end': 0})}\n\n"
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                logger.error(f"Error processing subtitle: {e}")
                yield f"data: {json.dumps({'text': 'Error processing subtitle', 'start': 0, 'end': 0})}\n\n"
                time.sleep(0.1)
                
    except Exception as e:
        logger.error(f"Error reading SRT file: {e}")
        yield f"data: {json.dumps({'text': 'Error reading subtitles', 'start': 0, 'end': 0})}\n\n"