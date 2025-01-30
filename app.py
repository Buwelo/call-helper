from flask import Response
from flask import Flask, render_template
from utils import readSrtFile

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/stream')
def stream():
    return Response(readSrtFile('./files/call_with_mark.srt'), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)