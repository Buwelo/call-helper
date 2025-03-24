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

    // Save current state
    const cursorPosition = elements.editableTranscript.selectionStart;
    const cursorEnd = elements.editableTranscript.selectionEnd;
    const scrollTop = elements.editableTranscript.scrollTop;
    const wasAtBottom =
      scrollTop + elements.editableTranscript.clientHeight >= elements.editableTranscript.scrollHeight - 5;

    // Function to find the best match for a new line
    const findBestMatch = (newLine, currentLines) => {
      let bestMatchIndex = -1;
      let bestMatchScore = 0;
      currentLines.forEach((currentLine, index) => {
        const score = similarity(newLine, currentLine);
        if (score > bestMatchScore) {
          bestMatchScore = score;
          bestMatchIndex = index;
        }
      });
      return { index: bestMatchIndex, score: bestMatchScore };
    };

    // Function to calculate similarity between two strings
    const similarity = (s1, s2) => {
      let longer = s1;
      let shorter = s2;
      if (s1.length < s2.length) {
        longer = s2;
        shorter = s1;
      }
      const longerLength = longer.length;
      if (longerLength === 0) {
        return 1.0;
      }
      return (longerLength - editDistance(longer, shorter)) / parseFloat(longerLength);
    };

    // Function to calculate edit distance between two strings
    const editDistance = (s1, s2) => {
      s1 = s1.toLowerCase();
      s2 = s2.toLowerCase();
      const costs = [];
      for (let i = 0; i <= s1.length; i++) {
        let lastValue = i;
        for (let j = 0; j <= s2.length; j++) {
          if (i === 0) {
            costs[j] = j;
          } else if (j > 0) {
            let newValue = costs[j - 1];
            if (s1.charAt(i - 1) !== s2.charAt(j - 1)) {
              newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
            }
            costs[j - 1] = lastValue;
            lastValue = newValue;
          }
        }
        if (i > 0) {
          costs[s2.length] = lastValue;
        }
      }
      return costs[s2.length];
    };

    // Update content
    let updatedLines = [...currentLines];
    newLines.forEach(newLine => {
      const { index, score } = findBestMatch(newLine, updatedLines);
      if (score > 0.7) {
        // Threshold for considering it a match
        // Merge the new line with the existing line, preserving user input
        updatedLines[index] = mergeLines(updatedLines[index], newLine);
      } else {
        // Add as a new line
        updatedLines.push(newLine);
      }
    });

    // Function to merge two lines, preserving user input
    const mergeLines = (existingLine, newLine) => {
      let mergedLine = '';
      let i = 0,
        j = 0;
      while (i < existingLine.length && j < newLine.length) {
        if (existingLine[i] === newLine[j]) {
          mergedLine += existingLine[i];
          i++;
          j++;
        } else if (existingLine[i] !== ' ' && newLine[j] === ' ') {
          // Preserve user input
          mergedLine += existingLine[i];
          i++;
        } else {
          // Use new line content
          mergedLine += newLine[j];
          j++;
        }
      }
      // Append any remaining characters
      mergedLine += existingLine.slice(i) + newLine.slice(j);
      return mergedLine;
    };

    elements.editableTranscript.value = updatedLines.join('\n');

    // Restore cursor position or keep at end
    if (cursorPosition !== elements.editableTranscript.value.length) {
      elements.editableTranscript.setSelectionRange(cursorPosition, cursorEnd);
      elements.editableTranscript.scrollTop = scrollTop;
    } else {
      elements.editableTranscript.setSelectionRange(
        elements.editableTranscript.value.length,
        elements.editableTranscript.value.length
      );
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
        hideSpinner();

        let scoreHTML = '';

        // Check if we have the new response structure
        if (data.comparison_details) {
          const result = data.comparison_details;

          // Display status and similarity information
          scoreHTML += `
            <div class="mb-4">
              <h3 class="text-lg font-semibold">Transcript Comparison</h3>
              <p>Status: ${
                result.diff === ''
                  ? '<span class="text-green-600">Identical</span>'
                  : '<span class="text-yellow-600">Different</span>'
              }</p>
              ${result.message ? `<p>Score: <strong>${result.similarity.toFixed(2)}%</strong></p>` : ''}
            </div>
          `;

          // Display errors if any
          if (result.total_errors > 0) {
            scoreHTML += `
              <div class="mb-4">
                <h3 class="text-lg font-semibold">Breakdown:
                </h3>
            `;
          }
        }

        // Display error tracking information if available
        if (data.error_tracking) {
          const errorTracking = data.error_tracking;

          scoreHTML += `
            <div class="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h3 class="text-xl font-bold text-gray-800 mb-3">Error Correction Results</h3>

              <div class="flex items-center mb-4">
                <div class="w-full bg-gray-200 rounded-full h-4">
                  <div class="bg-blue-600 h-4 rounded-full" style="width: ${errorTracking.percentage}%"></div>
                </div>
                <span class="ml-3 font-medium">${errorTracking.percentage.toFixed(2)}%</span>
              </div>

              <p class="text-lg font-medium text-gray-700 mb-2">${errorTracking.message}</p>

              <div class="grid grid-cols-2 gap-4 mt-4">
                <div class="bg-green-100 p-3 rounded-lg">
                  <p class="text-green-800 font-medium">Corrected Errors</p>
                  <p class="text-2xl font-bold text-green-700">${errorTracking.corrected_errors}</p>
                </div>
                <div class="bg-red-100 p-3 rounded-lg">
                  <p class="text-red-800 font-medium">Missed Errors</p>
                  <p class="text-2xl font-bold text-red-700">${errorTracking.missed_errors.length}</p>
                </div>
              </div>

              <div class="mt-4">
                <h4 class="font-semibold text-gray-700 mb-2">Missed Errors:</h4>
                <ul class="list-disc pl-5 space-y-1">
                  ${errorTracking.missed_errors
                    .map(
                      error => `
                    <li class="text-gray-600">
                      <span class="font-medium">Error ${error.id}</span>: 
                      ${
                        error.type === 'delete'
                          ? `Missing word "<span class="text-blue-600">${error.correct}</span>"`
                          : `"<span class="text-red-500">${error.error}</span>" should be "<span class="text-green-500">${error.correct}</span>"`
                      }
                    </li>
                  `
                    )
                    .join('')}
                </ul>
              </div>
            </div>
          `;

          // Add highlighted transcript if available
          // if (data.highlighted_transcript) {
          //   scoreHTML += `
          //     <div class="mt-6">
          //       <h3 class="text-lg font-semibold mb-2">Highlighted Transcript</h3>
          //       <div class="p-4 bg-dark border border-gray-200 rounded-lg overflow-auto max-h-96">
          //         ${data.highlighted_transcript}
          //       </div>
          //     </div>
          //   `;
          // }
        }

        modal.show();

        elements.scoreModalBody.innerHTML = scoreHTML;
      })
      .catch(error => {
        console.error('Error:', error);
        hideSpinner();
        alert('There was a problem with your submission. Please try again.');
      });
  });
});
