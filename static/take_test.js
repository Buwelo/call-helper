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
      }, 15000);
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

      // elements.nextButton.disabled = false;
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

          modal.show();
          const scoreHTML = results
            .map(result => {
              hideSpinner();

              // Extract error tracking details
              const errorTracking = result.error_tracking || {};
              const missedErrors = errorTracking.missed_errors || [];

              return `
              <div class="test-result mb-5">
                <div class="overall-score text-xl font-bold mb-3">
                  <h4>Percentage Score: ${result.percentage.toFixed(2)}%</h4>
                </div>
                
                <div class="error-tracking mt-4">
                  <h4 class="font-semibold mb-2">Error Correction:</h4>
                  <p class="mb-2">${errorTracking.message || result.message || 'No error tracking data available'}</p>
                  
                  <div class="flex justify-between mb-3">
                    <span>Corrected: ${errorTracking.corrected_errors || result.corrected_errors || 0}</span>
                    <span>Total Errors: ${errorTracking.total_errors || result.total_errors || 0}</span>
                    <span>Success Rate: ${errorTracking.percentage || result.percentage || 0}%</span>
                  </div>
          
                  <div class="ai-evaluation mt-4">
                    <h4 class="font-semibold mb-2">AI Evaluation:</h4>
                    <div class="mb-2">${result.aiEvaluation || 'No AI evaluation available'}</div>
                  </div>
                  
                  ${
                    missedErrors.length > 0
                      ? `
                    <div class="missed-errors mt-3">
                      <h5 class="font-semibold">Missed Errors:</h5>
                      <div class="bg-gray-500 p-3 rounded mt-2 max-h-40 overflow-y-auto">
                        <table class="w-full text-sm">
                          <thead>
                            <tr class="bg-gray-200">
                              <th class="p-2 text-left">ID</th>
                              <th class="p-2 text-left">Type</th>
                              <th class="p-2 text-left">Correct Text</th>
                              <th class="p-2 text-left">Error Text</th>
                            </tr>
                          </thead>
                          <tbody>
                            ${missedErrors
                              .map(
                                error => `
                              <tr class="border-b border-gray-200">
                                <td class="p-2">${error.id}</td>
                                <td class="p-2">${error.type}</td>
                                <td class="p-2 font-medium">${error.correct}</td>
                                <td class="p-2 text-red-600">${error.error || '(empty)'}</td>
                              </tr>
                            `
                              )
                              .join('')}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  `
                      : ''
                  }
                </div>
                
                <div class="status mt-4">
                  <p><strong>Status:</strong> ${errorTracking.status || result.status || 'Unknown'}</p>
                </div>
              </div>
            `;
                })
                .join('');
          elements.scoreModalBody.innerHTML = scoreHTML;
        })
        .catch(error => {
          console.error('Error submitting transcriptions:', error);
          alert('Error submitting test results. Please try again.');
          hideSpinner();
          elements.nextButton.disabled = false;
        })

        .finally(() => {
          state.transcriptions = [];
        });
    }
  });
});
