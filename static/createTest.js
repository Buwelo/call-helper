document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM fully loaded and parsed');

  const fileUpload = document.getElementById('file-upload');
  const scoreTranscriptInput = document.getElementById('score-transcript');
  const testTranscriptInput = document.getElementById('test-transcript');
  const nameOfTestInput = document.getElementById('name-of-test');
  const submitButton = document.getElementById('submit');

  const showError = (message, field) => {
    const errorSpan = field.nextElementSibling;
    if (errorSpan && errorSpan.classList.contains('error-message')) {
      const errorDiv = document.createElement('div');
      errorDiv.textContent = message;
      errorSpan.appendChild(errorDiv);
      setTimeout(() => {
        errorDiv.remove();
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

  submitButton.addEventListener('click', e => {
    e.preventDefault();

    const validations = [
      { field: fileUpload, message: 'Please select a file.' },
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
    
  });
});
