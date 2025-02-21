document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const elements = {
    audioPlayer: document.getElementById('audioPlayer'),
    transcript: document.getElementById('transcript'),
    timeDisplay: document.getElementById('time-display'),
    editableTranscript: document.getElementById('editable-transcript'),
    submitButton: document.getElementById('submit'),
    scoreModalBody: document.getElementById('score-modal-body'),
    startTestButton: document.getElementById('start-test'),
    srtToStream: document.getElementById('srt-to-stream'),
    testId: document.getElementById('test-id'),
    spinner: document.getElementById('loading-spinner'),
  };

  elements.startTestButton.addEventListener('click', e => {
    e.preventDefault();
    elements.audioPlayer.play();
  });
  // Hide spinner when page is loaded
  elements.spinner.style.display = 'none';

  // Show spinner before loading a new test
  function showSpinner() {
    elements.spinner.style.display = 'flex';
  }

  // Hide spinner after loading a test
  function hideSpinner() {
    elements.spinner.style.display = 'none';
  }

  // State management
  const state = {
    socket: null,
    lastTime: -1,
    transcriptHistory: [], // Store transcript segments
  };

  // Initialize WebSocket connection
  const initializeWebSocket = () => {
    state.socket = io();

    state.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    state.socket.on('transcription_segment', data => {
      //when piece of data is received from server, update transcript and editable transcript
      updateTranscriptDisplay(data);
      updateEditableTranscript(data);
    });

    state.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });
  };

  // Utility functions
  const formatTime = time => {
    const hours = Math.floor(time / 3600);
    const minutes = Math.floor((time % 3600) / 60);
    const seconds = Math.floor(time % 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds
      .toString()
      .padStart(2, '0')}`;
  };

  const updateTranscriptDisplay = data => {
    if (!data.text) return;

    // Add new segment to history if it's not already there
    const newSegment = `[${formatTime(data.start)}] ${data.text}`;
    if (!state.transcriptHistory.includes(newSegment)) {
      state.transcriptHistory.push(newSegment);

      // Update read-only transcript
      elements.transcript.value = state.transcriptHistory.join('\n');

      // Auto-scroll
      elements.transcript.scrollTop = elements.transcript.scrollHeight;
    }
  };

  const updateEditableTranscript = data => {
    if (!data.text) return;

    // Split the current transcript and new text into lines
    const currentLines = elements.editableTranscript.value.split('\n');
    const newLines = data.text.split('\n');

    // Filter out duplicate lines
    const uniqueNewLines = newLines.filter(line => !currentLines.includes(line.trim()));

    // If there are no new unique lines, return early
    if (uniqueNewLines.length === 0) return;
    // Save current state
    const cursorPosition = elements.editableTranscript.selectionStart;
    const cursorEnd = elements.editableTranscript.selectionEnd;
    const scrollTop = elements.editableTranscript.scrollTop;
    const wasAtBottom =
      scrollTop + elements.editableTranscript.clientHeight >= elements.editableTranscript.scrollHeight - 5;

    // Update content
    let newValue = elements.editableTranscript.value;
    if (newValue && !newValue.endsWith('\n')) newValue += '\n';
    newValue += uniqueNewLines.join('\n');

    elements.editableTranscript.value = newValue;

    // Restore cursor position or keep at end
    if (cursorPosition !== elements.editableTranscript.value.length - data.text.length - 1) {
      elements.editableTranscript.setSelectionRange(cursorPosition, cursorEnd);
      elements.editableTranscript.scrollTop = scrollTop;
    } else {
      elements.editableTranscript.setSelectionRange(newValue.length, newValue.length);
      if (wasAtBottom) {
        elements.editableTranscript.scrollTop = elements.editableTranscript.scrollHeight;
      }
    }

    // Auto-scroll if user hasn't scrolled up
    if (wasAtBottom) {
      elements.editableTranscript.scrollTop = elements.editableTranscript.scrollHeight;
    }
  };

  // Audio Player Event Handlers
  const handleTimeUpdate = () => {
    const currentTime = elements.audioPlayer.currentTime;
    elements.timeDisplay.textContent = formatTime(currentTime);

    // console.log(elements.srtToStream.value);

    if (Math.abs(currentTime - state.lastTime) >= 0.1) {
      state.lastTime = currentTime;
      state.socket.emit('request_transcription', {
        currentTime: currentTime,
        srt_file: elements.srtToStream.value,
      });
    }
  };

  // Initialize Audio Player
  if (elements.audioPlayer) {
    elements.audioPlayer.addEventListener('play', () => {
      elements.audioPlayer.controls = false;
      state.socket.emit('request_transcription', {
        currentTime: elements.audioPlayer.currentTime,
        srt_file: elements.srtToStream.value,
      });
    });

    elements.audioPlayer.addEventListener('ended', () => {
      elements.audioPlayer.controls = true;
    });

    elements.audioPlayer.addEventListener('timeupdate', handleTimeUpdate);
    elements.audioPlayer.addEventListener('seeking', () => {
      state.transcriptHistory = []; // Clear history when seeking
      elements.transcript.value = '';
    });

    // elements.audioPlayer.addEventListener('seeked', () => {
    //   state.socket.emit('request_transcription', {

    //   });
    // });
  }

  // Initialize WebSocket connection
  initializeWebSocket();

  // Initialize the modal
  const modal = new Modal(document.getElementById('score-results-modal'));

  // Add event listener for the close button
  const closeModalButton = document.getElementById('close-modal-button');
  if (closeModalButton) {
    closeModalButton.addEventListener('click', () => {
      modal.hide();
    });
  }
  // Cleanup
  window.addEventListener('beforeunload', () => {
    if (state.socket) {
      state.socket.disconnect();
    }
  });

  const stopAudio = () => {
    elements.audioPlayer.pause();
  };

  // Score Submission
  elements.submitButton.addEventListener('click', e => {
    e.preventDefault();
    stopAudio();

    const transcriptValue = elements.editableTranscript.value.trim();

    if (transcriptValue.length <= 15) {
      alert('Transcript is too short. Please provide a more substantial submission.');
      return;
    }

    const data = {
      transcript: transcriptValue,
    };

    const testId = elements.testId.value;
    showSpinner();
    fetch(`/transcription/score-transcription/${testId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
      .then(response => {
        console.log(response);
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        console.log(data);

        let scoreData;
        try {
          scoreData = JSON.parse(data.gpt_score);
        } catch (e) {
          console.error('Error parsing gpt_score:', e);
          scoreData = null;
        }
        let scoreHTML = '';

        if (scoreData && typeof scoreData === 'object') {
          hideSpinner();
          // Display individual score items
          if (Array.isArray(scoreData.score_items)) {
            scoreData.score_items.forEach(item => {
              scoreHTML += `
                <div class="mb-4">
                  <h3 class="text-lg font-semibold">${item.category}</h3>
                  <p>Score: ${item.assigned_score}</p>
                  <p>${item.comment}</p>
                </div>
              `;
            });
          } else {
            scoreHTML += '<p>No detailed score items available.</p>';
          }

          // Display overall score and summary
          scoreHTML += `
            <div class="mt-6">
              <h3 class="text-lg font-semibold">Overall Score: ${scoreData.overall_score || 'N/A'}</h3>
              <p class="mt-2"><strong>Summary:</strong> ${scoreData.summary || 'No summary available.'}</p>
            </div>
          `;
        } else {
          hideSpinner();

          scoreHTML += '<p>Unable to parse score data. Please try again.</p>';
        }

        modal.show();
        elements.scoreModalBody.innerHTML = scoreHTML;
      })
      .catch(error => {
        console.error('Error:', error);
        alert('Error scoring the transcript. Please try again.');
      });
  });
});
