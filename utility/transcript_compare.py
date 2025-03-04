import difflib
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscriptError:
    """Class to represent an intentionally introduced error in a transcript"""

    def __init__(self, error_id: str, correct_text: str, error_text: str,
                 position: Optional[int] = None, error_type: str = "general"):
        self.error_id = error_id
        self.correct_text = correct_text
        self.error_text = error_text
        self.position = position
        self.error_type = error_type
        self.was_corrected = False

    def __repr__(self):
        return f"Error({self.error_id}: '{self.error_text}' should be '{self.correct_text}')"


def extract_text_from_srt(srt_content):
    """Extract only the text content from SRT format, ignoring timestamps and sequence numbers"""
    lines = srt_content.split('\n')
    text_lines = []
    for line in lines:
        if not re.match(r'^\d+$', line) and not re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line) and line.strip():
            text_lines.append(line.strip())
    return ' '.join(text_lines)


def preprocess_transcript(transcript):
    """Normalize transcript text for comparison"""
    # Extract text if in SRT format
    transcript = extract_text_from_srt(transcript)

    # Normalize the text
    transcript = transcript.lower().strip()
    transcript = re.sub(r'\s+', ' ', transcript)

    return transcript


def generate_introduced_errors(good_transcript: str, bad_transcript: str) -> List[TranscriptError]:
    """
    Analyze differences between good and bad transcripts to create TranscriptError objects
    This function can be used to identify the intentional errors you've introduced

    Parameters:
        good_transcript: The correct transcript text
        bad_transcript: The transcript with intentionally introduced errors

    Returns:
        List of TranscriptError objects representing the differences
    """
    # Preprocess both transcripts
    good_text = preprocess_transcript(good_transcript)
    bad_text = preprocess_transcript(bad_transcript)

    # Split into words
    good_words = good_text.split()
    bad_words = bad_text.split()

    # Use difflib to find differences
    matcher = difflib.SequenceMatcher(None, good_words, bad_words)

    errors = []
    error_id = 1

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            errors.append(TranscriptError(
                error_id=f"E{error_id}",
                correct_text=' '.join(good_words[i1:i2]),
                error_text=' '.join(bad_words[j1:j2]),
                error_type="replace"
            ))
            error_id += 1
        elif tag == 'delete':
            errors.append(TranscriptError(
                error_id=f"E{error_id}",
                correct_text=' '.join(good_words[i1:i2]),
                error_text="",  # Text was deleted
                error_type="delete"
            ))
            error_id += 1
        elif tag == 'insert':
            errors.append(TranscriptError(
                error_id=f"E{error_id}",
                correct_text="",  # Nothing should be here
                error_text=' '.join(bad_words[j1:j2]),
                error_type="insert"
            ))
            error_id += 1

    return errors


def score_user_transcript(good_transcript: str,
                          bad_transcript: str,
                          user_transcript: str,
                          introduced_errors: Optional[List[TranscriptError]] = None) -> Dict[str, Any]:
    """
    Score a user-submitted transcript against the correct version and track which errors were fixed

    Parameters:
        good_transcript: The error-free transcript
        bad_transcript: The transcript with intentionally introduced errors
        user_transcript: The transcript submitted by the user
        introduced_errors: List of TranscriptError objects (optional - will be generated if not provided)

    Returns:
        Dictionary with scoring results including percentage, fixed errors, and missed errors
    """
    # Preprocess all transcripts
    good_text = preprocess_transcript(good_transcript)
    bad_text = preprocess_transcript(bad_transcript)
    user_text = preprocess_transcript(user_transcript)

    # Generate errors list if not provided
    if introduced_errors is None:
        introduced_errors = generate_introduced_errors(
            good_transcript, bad_transcript)

    total_errors = len(introduced_errors)
    corrected_errors = 0
    missed_errors = []

    # Check each error to see if it was corrected in the user transcript
    for error in introduced_errors:
        # For replaced text
        if error.error_type == "replace":
            # Check if the correct text is in the user transcript instead of the error text
            correct_present = error.correct_text.lower() in user_text.lower()
            error_present = error.error_text.lower() in user_text.lower()

            # If correct text is present and error text is not, mark as corrected
            if correct_present and not error_present:
                error.was_corrected = True
                corrected_errors += 1
            else:
                missed_errors.append(error)

        # For deleted text (user should have added it back)
        elif error.error_type == "delete":
            if error.correct_text.lower() in user_text.lower():
                error.was_corrected = True
                corrected_errors += 1
            else:
                missed_errors.append(error)

        # For inserted text (user should have removed it)
        elif error.error_type == "insert":
            if error.error_text.lower() not in user_text.lower():
                error.was_corrected = True
                corrected_errors += 1
            else:
                missed_errors.append(error)

    # Calculate percentage score
    percentage = (corrected_errors / total_errors *
                  100) if total_errors > 0 else 100

    # Use your existing difflib comparison for overall similarity
    good_words = good_text.split()
    user_words = user_text.split()
    matcher = difflib.SequenceMatcher(None, good_words, user_words)
    similarity = matcher.ratio() * 100

    return {
        'status': 'success',
        'total_errors': total_errors,
        'corrected_errors': corrected_errors,
        'missed_errors': [{"id": e.error_id, "correct": e.correct_text, "error": e.error_text, "type": e.error_type} for e in missed_errors],
        'percentage': round(percentage, 2),
        'similarity': round(similarity, 2),
        'message': f"Found and fixed {corrected_errors} out of {total_errors} intentional errors ({percentage:.2f}%)"
    }


def generate_highlighted_transcript(user_transcript: str, missed_errors: List[Dict[str, Any]]) -> str:
    """
    Generate a version of the user's transcript with missed errors highlighted

    Parameters:
        user_transcript: The transcript submitted by the user
        missed_errors: List of errors that weren't corrected

    Returns:
        Transcript with HTML highlighting on missed errors
    """
    highlighted = user_transcript

    # Add HTML highlighting for each missed error
    for error in missed_errors:
        if error["error"]:  # If there's error text to highlight
            # Use HTML span with red background for highlighting
            highlighted = highlighted.replace(
                error["error"],
                f'<span class="bg-red-200 text-red-800 rounded px-1 hover:bg-red-300 cursor-help" title="Should be: {error["correct"]}">{error["error"]}</span>'
            )

    return highlighted


def compare_transcript_with_errors(good_transcript: str, bad_transcript: str, user_transcript: str) -> Dict[str, Any]:
    """
    Enhanced version of compare_transcript that tracks intentionally introduced errors

    Parameters:
        good_transcript: The error-free transcript
        bad_transcript: The transcript with intentionally introduced errors
        user_transcript: The transcript submitted by the user

    Returns:
        Dictionary with scoring results and detailed error information
    """
    # First, identify what errors were introduced
    introduced_errors = generate_introduced_errors(
        good_transcript, bad_transcript)

    # Score the user's transcript against these introduced errors
    score_results = score_user_transcript(
        good_transcript, bad_transcript, user_transcript, introduced_errors)

    # Create a highlighted version of the transcript
    highlighted_transcript = generate_highlighted_transcript(
        user_transcript, score_results['missed_errors'])

    # Get detailed diff using your existing method
    base_comparison = compare_transcript(good_transcript, user_transcript)

    # Combine the results
    return {
        'status': 'success',
        'error_tracking': score_results,
        'similarity': base_comparison['similarity'],
        'total_errors': len(introduced_errors),
        'corrected_errors': score_results['corrected_errors'],
        'percentage': score_results['percentage'],
        'highlighted_transcript': highlighted_transcript,
        'readable_diff': base_comparison['readable_diff'],
        'message': score_results['message']
    }

# Your existing compare_transcript function (with slight modifications)


def compare_transcript(good_transcript, user_transcript):
    """Original difflib-based transcript comparison"""
    good_transcript = preprocess_transcript(good_transcript)
    user_transcript = preprocess_transcript(user_transcript)

    # Split into words for comparison
    good_words = good_transcript.split()
    user_words = user_transcript.split()

    logger.info(f'Good words count: {len(good_words)}')
    logger.info(f'User words count: {len(user_words)}')

    if good_words == user_words:
        return {
            'status': 'identical',
            'message': 'Transcripts are identical',
            'diff': '',
            'readable_diff': 'No differences found.',
            'total_errors': 0,
            'similarity': 100
        }

    # Use difflib to compare the words
    matcher = difflib.SequenceMatcher(None, good_words, user_words)

    # Calculate similarity ratio
    similarity = matcher.ratio() * 100

    # Generate a readable diff
    readable_diff = []
    error_count = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            readable_diff.append(f"MATCH: {' '.join(good_words[i1:i2])}")
            readable_diff.append("")
        elif tag == 'replace':
            error_count += max(i2 - i1, j2 - j1)
            readable_diff.append(
                f"REPLACE: '{' '.join(good_words[i1:i2])}' -> '{' '.join(user_words[j1:j2])}'")
            readable_diff.append("")
        elif tag == 'delete':
            error_count += (i2 - i1)
            readable_diff.append(f"DELETE: '{' '.join(good_words[i1:i2])}'")
            readable_diff.append("")
        elif tag == 'insert':
            error_count += (j2 - j1)
            readable_diff.append(f"INSERT: '{' '.join(user_words[j1:j2])}'")
            readable_diff.append("")

    readable_diff_str = "\n".join(readable_diff)

    # Create a more detailed diff for debugging
    diff = difflib.ndiff(good_words, user_words)
    diff_str = '\n'.join(diff)

    return {
        'status': 'different',
        'message': f'Found {error_count} differences between transcripts (Similarity: {similarity:.2f}%)',
        'diff': diff_str,
        'readable_diff': readable_diff_str,
        'total_errors': error_count,
        'similarity': similarity
    }


# Example usage:
if __name__ == "__main__":
    # Example transcripts
    good_transcript = "The quick brown fox jumps over the lazy dog."
    bad_transcript = "The quik brown fox jumps ober the laazy dog."  # 3 errors
    user_transcript = "The quick brown fox jumps over the laazy dog."  # Fixed 2/3 errors

    # Get scoring results
    results = compare_transcript_with_errors(
        good_transcript, bad_transcript, user_transcript)

    print(
        f"Score: {results['percentage']}% ({results['corrected_errors']}/{results['total_errors']} errors corrected)")
    print(f"Similarity to correct transcript: {results['similarity']}%")
    print(f"Highlighted transcript: {results['highlighted_transcript']}")
