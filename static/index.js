document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const elements = {
    audioPlayer: document.getElementById('audioPlayer'),
    transcript: document.getElementById('transcript'),
    timeDisplay: document.getElementById('time-display'),
    editableTranscript: document.getElementById('editable-transcript'),
    submitButton: document.getElementById('submit'),
    scoreModalBody: document.getElementById('score-modal-body'),
  };

  // State management
  const state = {
    eventSource: null,
    lastTime: -1,
    transcriptHistory: [], // Store transcript segments
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
    if (!data.text || elements.editableTranscript.value.endsWith(data.text)) return;

    // Save current state
    const cursorPosition = elements.editableTranscript.selectionStart;
    const cursorEnd = elements.editableTranscript.selectionEnd;
    const scrollTop = elements.editableTranscript.scrollTop;
    const wasAtBottom =
      scrollTop + elements.editableTranscript.clientHeight === elements.editableTranscript.scrollHeight;

    // Update content
    let newValue = elements.editableTranscript.value;
    if (newValue) newValue += '\n';
    newValue += data.text; // Removed timestamp, only adding the text

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
  };

  // Event Source Management
  const connectEventSource = currentTime => {
    if (state.eventSource) {
      state.eventSource.close();
    }

    state.eventSource = new EventSource(`/transcription/stream?currenttime=${currentTime}`);

    state.eventSource.onmessage = event => {
      try {
        const data = JSON.parse(event.data);
        updateTranscriptDisplay(data);
        updateEditableTranscript(data);
      } catch (e) {
        console.error('Error parsing subtitle data:', e);
      }
    };

    state.eventSource.onerror = error => {
      console.error('EventSource failed:', error);
      if (state.eventSource) {
        state.eventSource.close();
        state.eventSource = null;
      }
    };
  };

  // Audio Player Event Handlers
  const handleTimeUpdate = () => {
    const currentTime = elements.audioPlayer.currentTime;
    elements.timeDisplay.textContent = formatTime(currentTime);

    if (Math.abs(currentTime - state.lastTime) >= 0.1) {
      state.lastTime = currentTime;
      connectEventSource(currentTime);
    }
  };

  const closeEventSource = () => {
    if (state.eventSource) {
      state.eventSource.close();
      state.eventSource = null;
    }
  };

  const scoreModal = document.getElementById('score-results-modal');
  const modal = new Modal(scoreModal);

  // Submit Transcript
  const submitTranscript = async e => {
    e.preventDefault();

    if (!elements.editableTranscript.value.trim()) {
      alert('Empty submission');
      console.error('Cannot submit empty transcript');
      return;
    }
    modal.show();

    // Set loading message
    elements.scoreModalBody.innerHTML = '<p class="text-base">Loading score...</p>';

    try {
      const response = await fetch('/transcription/score-transcription/1', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript: elements.editableTranscript.value,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (!data.gpt4_score) {
        throw new Error('No score data received from the server');
      }

      const scoreLines = data.gpt4_score.split('\n');

      const createScoreSection = (title, scoreIndex, explanationIndex) => {
        const scoreLine = scoreLines[scoreIndex] || '';
        const score = scoreLine.split(':')[1]?.trim() || 'N/A';
        const explanation = scoreLines[explanationIndex] || 'No explanation provided';

        return `
        <div>
          <h3 class="text-lg font-semibold">${title}</h3>
          <p>Score: ${score}</p>
          <p>${explanation}</p>
        </div>
      `;
      };

      const htmlContent = `
      <div class="space-y-4">
        ${createScoreSection('Audio Cues', 0, 1)}
        ${createScoreSection('Corrections (Words)', 3, 4)}
        ${createScoreSection('Punctuation', 6, 7)}
        ${createScoreSection('Grammar', 9, 10)}
      </div>
    `;

      elements.scoreModalBody.innerHTML = htmlContent;
    } catch (error) {
      console.error('Error submitting transcript:', error);
      elements.scoreModalBody.innerHTML = `
      <p class="text-red-500">Error: ${error.message}</p>
      <p>Please try again or contact support if the problem persists.</p>
    `;
    }
  };

  const closeModalButton = document.getElementById('close-modal-button');
  if (closeModalButton) {
    closeModalButton.addEventListener('click', () => {
      modal.hide();
    });
  }

  // Initialize Audio Player
  if (elements.audioPlayer) {
    // Audio player controls
    elements.audioPlayer.addEventListener('play', () => {
      elements.audioPlayer.controls = false;
      connectEventSource(elements.audioPlayer.currentTime);
    });

    elements.audioPlayer.addEventListener('ended', () => {
      elements.audioPlayer.controls = true;
      closeEventSource();
    });

    // Playback event listeners
    elements.audioPlayer.addEventListener('timeupdate', handleTimeUpdate);
    elements.audioPlayer.addEventListener('pause', closeEventSource);
    elements.audioPlayer.addEventListener('seeking', () => {
      closeEventSource();
      elements.transcript.value = '';
      state.transcriptHistory = []; // Clear history when seeking
    });
    elements.audioPlayer.addEventListener('seeked', () => {
      connectEventSource(elements.audioPlayer.currentTime);
    });
  } else {
    console.error('Audio player element not found');
  }

  // Submit button event listener
  elements.submitButton.addEventListener('click', submitTranscript);

  // Cleanup
  window.addEventListener('beforeunload', closeEventSource);
});
