document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM fully loaded and parsed');

  const form = document.getElementById('test-form');
  const fileUpload = document.getElementById('file-upload');
  const audiofileUpload = document.getElementById('audio-file-upload');
  const scoreTranscriptInput = document.getElementById('score-transcript');
  const testTranscriptInput = document.getElementById('test-transcript');
  const nameOfTestInput = document.getElementById('name-of-test');

  const showError = (message, field) => {
    const errorSpan = field.nextElementSibling;
    if (errorSpan && errorSpan.classList.contains('error-message')) {
      errorSpan.textContent = message;
      setTimeout(() => {
        errorSpan.textContent = '';
      }, 3000);
    }
  };

  const validateField = (field, errorMessage) => {
    if (!field.value.trim()) {
      field.focus();
      showError(errorMessage, field);
      return false;
    }
    return true;
  };

  form.addEventListener('submit', e => {
    e.preventDefault();

    const validations = [
      { field: fileUpload, message: 'Please select a file.' },
      { field: audiofileUpload, message: 'Please select a file.' },
      { field: scoreTranscriptInput, message: 'Please fill in the Score Transcript.' },
      { field: testTranscriptInput, message: 'Please fill in the Test Transcript.' },
      { field: nameOfTestInput, message: 'Please fill in the Name of Test.' },
    ];

    for (const validation of validations) {
      if (!validateField(validation.field, validation.message)) {
        return;
      }
    }

    // If all validations pass, proceed with form submission
    console.log('All fields are valid. Proceeding with form submission.');

    const formData = new FormData();
    formData.append('srt_file', fileUpload.files[0]);
    formData.append('audio_file', audiofileUpload.files[0]);
    formData.append('score_transcript', scoreTranscriptInput.value);
    formData.append('test_transcript', testTranscriptInput.value);
    formData.append('name_of_test', nameOfTestInput.value);
    
    console.log(
      'File 1:', fileUpload.files[0].name,
      'File 2:', audiofileUpload.files[0].name,
      'Score Transcript:', scoreTranscriptInput.value,
      'Test Transcript:', testTranscriptInput.value,
      'Name of Test:', nameOfTestInput.value,
    );
    

    fetch('/transcription/create_test', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        alert('Test created successfully!');
        form.reset();
      } else {
        alert(`Error: ${data.message}`);
      }
    })
    .catch((error) => {
      console.error('Error:', error);
      alert('An error occurred while creating the test.');
    });
  });
});