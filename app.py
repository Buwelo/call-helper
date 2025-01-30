from flask import Response, request
from flask import Flask, render_template
from utils import readSrtFile
import logging

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/stream')
def stream():
    currenttime = request.args.get('currenttime', 0, type=float)  # Get currenttime from query params
    logging.info(f"currenttime: {currenttime}")
    return Response(readSrtFile('./files/call_with_mark.srt', currenttime), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)