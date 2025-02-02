document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM fully loaded and parsed');

  const audioPlayer = document.getElementById('audioPlayer');
  const transcript = document.getElementById('transcript');
  const timeDisplay = document.getElementById('time-display');
  const editableTranscript = document.getElementById('editable-transcript');

  // play audio and disable controls

  if (audioPlayer) {
    audioPlayer.addEventListener('play', () => {
      audioPlayer.controls = false;
    });

    // audioPlayer.addEventListener('pause', () => {
    //     audioPlayer.controls = true;
    // });

    audioPlayer.addEventListener('ended', () => {
      audioPlayer.controls = true;
    });
  } else {
    console.error('Audio player element not found');
  }

  let eventSource = null;
  let lastTime = -1;

  const formatTime = time => {
    const hours = Math.floor(time / 3600);
    const minutes = Math.floor((time % 3600) / 60);
    const seconds = Math.floor(time % 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds
      .toString()
      .padStart(2, '0')}`;
  };

  function connectEventSource(currentTime) {
    if (eventSource) {
      eventSource.close();
    }

    eventSource = new EventSource(`/stream?currenttime=${currentTime}`);

    eventSource.onmessage = function (event) {
      try {
        const data = JSON.parse(event.data);
        transcript.value = data.text;

        // Only append to editable transcript if it's new text
        if (data.text && !editableTranscript.value.endsWith(data.text)) {
          // Store current cursor and scroll position
          const cursorPosition = editableTranscript.selectionStart;
          const cursorEnd = editableTranscript.selectionEnd;
          const scrollTop = editableTranscript.scrollTop;

          // Get current content
          let newValue = editableTranscript.value;

          // Add newline if needed and append new text
          if (newValue) {
            newValue += '\n';
          }
          newValue += `[${formatTime(data.start)}] ${data.text}`;

          // Update the textarea
          editableTranscript.value = newValue;

          // If user was actively editing (cursor position not at end),
          // restore their position
          if (cursorPosition !== editableTranscript.value.length - data.text.length - 1) {
            editableTranscript.setSelectionRange(cursorPosition, cursorEnd);
            editableTranscript.scrollTop = scrollTop;
          } else {
            // If cursor was at end, keep it at end
            editableTranscript.setSelectionRange(newValue.length, newValue.length);
            // Optional: scroll to bottom only if user was already at bottom
            if (scrollTop + editableTranscript.clientHeight === editableTranscript.scrollHeight) {
              editableTranscript.scrollTop = editableTranscript.scrollHeight;
            }
          }

          console.log('data text ', data.text);
        }
      } catch (e) {
        console.error('Error parsing subtitle data:', e);
      }
    };

    eventSource.onerror = function (error) {
      console.error('EventSource failed:', error);
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
    };
  }

  // Update time display and check for subtitle updates
  audioPlayer.addEventListener('timeupdate', () => {
    const currentTime = audioPlayer.currentTime;
    timeDisplay.textContent = formatTime(currentTime);

    // Only update if time has changed significantly (100ms)
    if (Math.abs(currentTime - lastTime) >= 0.1) {
      lastTime = currentTime;
      if (!eventSource || eventSource.readyState !== EventSource.OPEN) {
        connectEventSource(currentTime);
      } else {
        // Reconnect with new time
        connectEventSource(currentTime);
      }
    }
  });

  // Handle playback controls
  audioPlayer.addEventListener('play', () => {
    connectEventSource(audioPlayer.currentTime);
  });

  audioPlayer.addEventListener('pause', () => {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  });

  audioPlayer.addEventListener('seeking', () => {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    transcript.value = ''; // Clear current subtitle while seeking
  });

  audioPlayer.addEventListener('seeked', () => {
    connectEventSource(audioPlayer.currentTime);
  });

  audioPlayer.addEventListener('ended', () => {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  });

  // Clean up on page unload
  window.addEventListener('beforeunload', () => {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  });

  // Handle transcript submission
  const submitButton = document.getElementById('submit');
    submitButton.addEventListener('click', async (e) => {
      e.preventDefault()
      const textAreaContent = document.getElementById('editable-transcript').value;
      
    // Send updated transcript to server
    try {
      const response = await fetch('/score-transcript', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            transcript: textAreaContent,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error submitting transcript:', error);
    }
  });
});
