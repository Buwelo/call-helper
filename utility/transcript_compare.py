import difflib
import logging
from datetime import datetime
import re


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_time(time_str):
    """Convert SRT timestamp to seconds"""
    time_obj = datetime.strptime(time_str.replace(',', '.'), '%H:%M:%S.%f')
    return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1000000


def extract_text_from_srt(srt_content):
    """Extract only the text content from SRT format, ignoring timestamps and sequence numbers"""
    lines = srt_content.split('\n')
    text_lines = []
    for line in lines:
        if not re.match(r'^\d+$', line) and not re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line) and line.strip():
            text_lines.append(line.strip())
    return ' '.join(text_lines)


def compare_transcript(good_transcript, bad_transcript):
    good_transcript = extract_text_from_srt(good_transcript)
    bad_transcript = extract_text_from_srt(bad_transcript)

    # Normalize both transcripts to make comparison more accurate
    good_transcript = good_transcript.lower().strip()
    bad_transcript = bad_transcript.lower().strip()

    # Remove extra whitespace
    good_transcript = re.sub(r'\s+', ' ', good_transcript)
    bad_transcript = re.sub(r'\s+', ' ', bad_transcript)

    # Split into words for comparison
    good_words = good_transcript.split()
    bad_words = bad_transcript.split()

    logger.info(f'Good words count: {len(good_words)}')
    logger.info(f'Bad words count: {len(bad_words)}')

    if good_words == bad_words:
        return {
            'status': 'identical',
            'message': 'Transcripts are identical',
            'diff': '',
            'readable_diff': 'No differences found.',
            'total_errors': 0,
            'similarity': 100
        }

    # Use difflib to compare the words
    matcher = difflib.SequenceMatcher(None, good_words, bad_words)

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
            readable_diff.append(f"REPLACE: '{' '.join(good_words[i1:i2])}' -> '{' '.join(bad_words[j1:j2])}'")
            readable_diff.append("")

        elif tag == 'delete':
            error_count += (i2 - i1)
            readable_diff.append(f"DELETE: '{' '.join(good_words[i1:i2])}'")
            readable_diff.append("")

        elif tag == 'insert':
            error_count += (j2 - j1)
            readable_diff.append(f"INSERT: '{' '.join(bad_words[j1:j2])}'")
            readable_diff.append("")

    readable_diff_str = "\n".join(readable_diff)

    # Create a more detailed diff for debugging
    diff = difflib.ndiff(good_words, bad_words)
    diff_str = '\n'.join(diff)
    return {
        'status': 'different',
        'message': f'Found {error_count} differences between transcripts (Similarity: {similarity:.2f}%)',
        'diff': diff_str,
        'readable_diff': readable_diff_str,
        'total_errors': error_count,
        'similarity': similarity
    }







EXAMPLE_COMPARISON_RESULT = """"""

