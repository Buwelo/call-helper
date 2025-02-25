window.addEventListener('load', function () {
  const elements = {
    audioPlayer: document.getElementById('audioPlayer'),
    // transcript: document.getElementById('transcript'),
    timeDisplay: document.getElementById('time-display'),
    editableTranscript: document.getElementById('editable-transcript'),
    nextButton: document.getElementById('next'),
    scoreModalBody: document.getElementById('score-modal-body'),
    startTestButton: document.getElementById('start-test'),
    srtToStream: document.getElementById('srt-to-stream'),
    testId: document.getElementById('test-id'),
    testStatus: document.getElementById('test-status'),
    testingId: document.getElementById('testing-id'),
    spinner: document.getElementById('loading-spinner'),
  };
  elements.startTestButton.addEventListener('click', e => {
    e.preventDefault();
    elements.editableTranscript.value = '';
    elements.editableTranscript.disabled = false;
    elements.audioPlayer.play();
  });

  elements.audioPlayer.addEventListener('ended', () => {
    console.log('audio has ended');
    disableTextareaAfterDelay();
    alert('Textarea disabled after audio ends, proceed to next...');
  });

  elements.audioPlayer.addEventListener('play', () => {
    console.log('Audio started playing');
    elements.editableTranscript.disabled = false;
  });

  function disableTextareaAfterDelay() {
    // Check if audio has actually ended
    if (elements.audioPlayer.ended) {
      console.log('Disabling textarea in 8 seconds');
      setTimeout(() => {
        if (elements.audioPlayer.ended) {
          console.log('Textarea disabled');
          elements.editableTranscript.disabled = true;
        } else {
          console.log('Audio is playing again, textarea not disabled');
        }
      }, 8000);
    }
  }

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

  // Utility functions
  const formatTime = time => {
    const hours = Math.floor(time / 3600);
    const minutes = Math.floor((time % 3600) / 60);
    const seconds = Math.floor(time % 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds
      .toString()
      .padStart(2, '0')}`;
  };

  // State management
  const state = {
    socket: null,
    lastTime: -1,
    transcriptHistory: [], // Store transcript segments
    transcriptions: [], // Store transcriptions to be sent to server
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
  // Handle when audio ends



  // Initialize WebSocket connection
  const initializeWebSocket = () => {
    state.socket = io();

    state.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    state.socket.on('transcription_segment', data => {
      //when piece of data is received from server, update transcript and editable transcript
      updateEditableTranscript(data);
    });

    state.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });
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

  // Initialize Audio Player
  if (elements.audioPlayer) {
    elements.audioPlayer.addEventListener('play', () => {
      elements.audioPlayer.controls = true;
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

  const stopAudio = () => {
    elements.audioPlayer.pause();
  };

  let initialTestId = elements.testId.value;

  elements.nextButton.addEventListener('click', e => {
    e.preventDefault();
    stopAudio();
    elements.audioPlayer.controls = true;

    const transcriptValue = elements.editableTranscript.value.trim();
    elements.editableTranscript.value = '';

    if (transcriptValue.length <= 15) {
      alert('Transcript is too short. Please provide a more substantial submission.');
      return;
    }

    let userTranscriptItem = {
      testingId: elements.testingId.value,
      testId: initialTestId,
      transcript: transcriptValue,
    };

    if (!state.transcriptions.some(item => item.testId === userTranscriptItem.testId)) {
      state.transcriptions.push(userTranscriptItem);
    } else {
      console.log('Transcript for this test ID already exists.');
    }

    initialTestId = elements.testId.value;
    if (elements.testStatus.value === 'completed') {
      console.log('submitting test');
      console.log(state.transcriptions);

      elements.nextButton.disabled = true;
      showSpinner();
      const submissionPromises = state.transcriptions.map(async item => {
        return fetch('/transcription/score-transcription/' + item.testId, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(item),
        }).then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        });
      });

      Promise.all(submissionPromises)
        .then(results => {
          console.log('All transcriptions submitted successfully.', results);
          alert('Your test results have been submitted. Thank you!');
          // TODO redirect user to the results page or show modal with scores

          modal.show();
          const scoreHTML = results
            .map(result => {
              const gptScore = JSON.parse(result.gpt_score);
              hideSpinner();
              let scoreItemsHTML = gptScore.score_items
                .map(
                  item => `
                <div class="score-item mb-4">
                  <h4 class="font-semibold mb-1">${item.category}</h4>
                  <p class="mb-1">Score: ${item.assigned_score} points</p>
                  <p>${item.comment}</p>
                </div>
              `
                )
                .join('');
              return `
              <div class="test-result mb-5">
                <div class="overall-score text-xl font-bold mb-3">
                  <h4>Overall Score: ${gptScore.overall_score} points</h4>
                </div>
                <div class="score-items space-y-4">
                  ${scoreItemsHTML}
                </div>
                <div class="summary mt-4 italic">
                  <h4 class="font-semibold mb-1">Summary:</h4>
                  <p>${gptScore.summary}</p>
                </div>
              </div>
            `;
            })
            .join('<hr>');
          elements.scoreModalBody.innerHTML = scoreHTML;
        })
        .catch(error => {
          console.error('Error submitting transcriptions:', error);
          alert('Error submitting test results. Please try again.');
          elements.nextButton.disabled = false;
        })
        .finally(() => {
          state.transcriptions = [];
        });
    }
  });
});
