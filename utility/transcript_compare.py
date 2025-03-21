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

def preprocess_transcript(transcript, preserve_punctuation=True):
    """
    Normalize transcript text for comparison
    
    Parameters:
        transcript: The transcript text to preprocess
        preserve_punctuation: Whether to preserve punctuation
    """
    # Extract text if in SRT format
    transcript = extract_text_from_srt(transcript)
    
    # Normalize whitespace
    transcript = transcript.strip()
    transcript = re.sub(r'\s+', ' ', transcript)
    
    if preserve_punctuation:
        # Convert to lowercase but preserve punctuation
        transcript = transcript.lower()
    else:
        # Remove punctuation and convert to lowercase
        transcript = re.sub(r'[^\w\s]', '', transcript).lower()
    
    return transcript

def tokenize_with_punctuation(text):
    """
    Tokenize text while preserving punctuation as separate tokens
    """
    # Add spaces around punctuation
    text = re.sub(r'([.,!?;:])', r' \1 ', text)
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    # Split into tokens
    return text.split()

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
    # Preprocess transcripts while preserving punctuation
    good_text = preprocess_transcript(good_transcript, preserve_punctuation=True)
    bad_text = preprocess_transcript(bad_transcript, preserve_punctuation=True)
    
    logger.info(f"Comparing transcripts: '{good_transcript}' vs '{bad_transcript}'")
    logger.info(f"Preprocessed: '{good_text}' vs '{bad_text}'")

    # Tokenize text with punctuation preserved
    good_tokens = tokenize_with_punctuation(good_text)
    bad_tokens = tokenize_with_punctuation(bad_text)
    
    logger.info(f"Good tokens: {good_tokens}")
    logger.info(f"Bad tokens: {bad_tokens}")
    
    # Use difflib to find differences
    matcher = difflib.SequenceMatcher(None, good_tokens, bad_tokens)
    
    errors = []
    error_id = 1
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':  # Process any difference (replace, delete, insert)
            good_chunk = ' '.join(good_tokens[i1:i2])
            bad_chunk = ' '.join(bad_tokens[j1:j2])
            
            # Log the difference found
            logger.info(f"Found difference: '{good_chunk}' vs '{bad_chunk}' (type: {tag})")
            
            if tag == 'replace':
                errors.append(TranscriptError(
                    error_id=f"E{error_id}",
                    correct_text=good_chunk,
                    error_text=bad_chunk,
                    error_type="replace"
                ))
            elif tag == 'delete':
                errors.append(TranscriptError(
                    error_id=f"E{error_id}",
                    correct_text=good_chunk,
                    error_text="",  # Text was deleted
                    error_type="delete"
                ))
            elif tag == 'insert':
                errors.append(TranscriptError(
                    error_id=f"E{error_id}",
                    correct_text="",  # Nothing should be here
                    error_text=bad_chunk,
                    error_type="insert"
                ))
            
            error_id += 1
    
    logger.info(f"Total errors found: {len(errors)}")
    for error in errors:
        logger.info(f"Error: {error}")
    
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
        Dictionary with scoring results including percentage and error counts
    """
    # Preprocess all transcripts (preserving punctuation)
    good_text = preprocess_transcript(good_transcript, preserve_punctuation=True)
    bad_text = preprocess_transcript(bad_transcript, preserve_punctuation=True)
    user_text = preprocess_transcript(user_transcript, preserve_punctuation=True)
    
    # Generate errors list if not provided
    if introduced_errors is None:
        introduced_errors = generate_introduced_errors(good_transcript, bad_transcript)
    
    total_errors = len(introduced_errors)
    corrected_errors = 0
    missed_errors = []
    
    # For exact match checking, use tokenized versions
    good_tokens = tokenize_with_punctuation(good_text)
    user_tokens = tokenize_with_punctuation(user_text)
    
    # Matcher for detailed comparison
    matcher = difflib.SequenceMatcher(None, good_tokens, user_tokens)
    
    # Check each error to see if it was corrected in the user transcript
    for error in introduced_errors:
        # Set up pattern-matching for more accurate checks
        correct_pattern = re.escape(error.correct_text)
        error_pattern = re.escape(error.error_text) if error.error_text else None
        
        # For replaced text
        if error.error_type == "replace":
            # Check if the correct text is in the user transcript
            correct_matches = re.search(correct_pattern, user_text)
            # Check if the error text is in the user transcript
            error_matches = re.search(error_pattern, user_text) if error_pattern else False
            
            # If correct text is found and error text is not, mark as corrected
            if correct_matches and not error_matches:
                error.was_corrected = True
                corrected_errors += 1
                logger.info(f"Error corrected: {error}")
            else:
                missed_errors.append(error)
                logger.info(f"Error missed: {error}")
                
        # For deleted text (user should have added it back)
        elif error.error_type == "delete":
            correct_matches = re.search(correct_pattern, user_text)
            if correct_matches:
                error.was_corrected = True
                corrected_errors += 1
                logger.info(f"Error corrected: {error}")
            else:
                missed_errors.append(error)
                logger.info(f"Error missed: {error}")
                
        # For inserted text (user should have removed it)
        elif error.error_type == "insert":
            error_matches = re.search(error_pattern, user_text) if error_pattern else False
            if not error_matches:
                error.was_corrected = True
                corrected_errors += 1
                logger.info(f"Error corrected: {error}")
            else:
                missed_errors.append(error)
                logger.info(f"Error missed: {error}")
    
    # Calculate percentage score
    percentage = (corrected_errors / total_errors * 100) if total_errors > 0 else 100
    
    # Calculate similarity for reference
    similarity = matcher.ratio() * 100
    
    logger.info(f"Scoring complete: {corrected_errors}/{total_errors} errors corrected ({percentage:.2f}%)")
    
    return {
        'status': 'success',
        'total_errors': total_errors,
        'corrected_errors': corrected_errors,
        'missed_errors_count': len(missed_errors),
        'percentage': round(percentage, 2),
        'similarity': round(similarity, 2),
        'message': f"Found and fixed {corrected_errors} out of {total_errors} intentional errors ({percentage:.2f}%)"
    }

def compare_transcript_with_errors(good_transcript: str, bad_transcript: str, user_transcript: str) -> Dict[str, Any]:
    """
    Simplified version of transcript comparison that focuses only on scoring
    
    Parameters:
        good_transcript: The error-free transcript
        bad_transcript: The transcript with intentionally introduced errors
        user_transcript: The transcript submitted by the user
        
    Returns:
        Dictionary with scoring results and error counts
    """
    # First, identify what errors were introduced
    introduced_errors = generate_introduced_errors(good_transcript, bad_transcript)
    
    # Score the user's transcript against these introduced errors
    score_results = score_user_transcript(good_transcript, bad_transcript, user_transcript, introduced_errors)
    
    # Return only the essential information
    return {
        'status': 'success',
        'total_errors': len(introduced_errors),
        'corrected_errors': score_results['corrected_errors'],
        'missed_errors_count': score_results['missed_errors_count'],
        'percentage': score_results['percentage'],
        'message': score_results['message']
    }