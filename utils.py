from datetime import datetime, timedelta
import time

def readSrtFile(filename):
    srt_file = open(filename, 'r')
    lines = srt_file.readlines()
    srt_file.close()
    
    # parse file into subtitle dictionary
    subtitles = []
    
    for i in range(0, len(lines), 4):
        # extract subtitle number
        subtitle_number = lines[i].split()
        
        # extract time_range 
        time_range = lines[i + 1].strip()
        
        # extract subtitle text
        subtitle_text = lines[i + 2].strip()
        
        subtitle = {
            'time_range': time_range,
            'text': subtitle_text
        }
        
        subtitles.append(subtitle)
    
    # Start time
    start_time = datetime.now()
    
    for subtitle in subtitles:
        # Parse time range
        start_time_str, end_time_str = subtitle['time_range'].split(' --> ')
        start_time_obj = datetime.strptime(start_time_str, '%H:%M:%S,%f')
        end_time_obj = datetime.strptime(end_time_str, '%H:%M:%S,%f')
        
        # Calculate elapsed time
        elapsed_time = end_time_obj - start_time_obj
        
        # Display subtitle text after elapsed time
        print(f"Subtitle Text: {subtitle['text']}")
        print(f"Elapsed Time: {elapsed_time}")
        time.sleep(elapsed_time.total_seconds())

readSrtFile('./files/call_with_mark.srt')
