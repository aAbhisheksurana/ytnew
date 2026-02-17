import os
import sys
import datetime

# Ensure ffmpeg is found and set for moviepy
FFMPEG_BINARY = os.path.abspath("../bin/ffmpeg")
if os.path.exists(FFMPEG_BINARY):
    os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_BINARY
    os.environ["PATH"] += os.pathsep + os.path.dirname(FFMPEG_BINARY)
    print(f"Using local ffmpeg: {FFMPEG_BINARY}")
else:
    print("Warning: Local ffmpeg not found, relying on system path.")

import whisper
from moviepy import VideoFileClip

def format_timestamp(seconds: float):
    td = datetime.timedelta(seconds=seconds)
    # Extract hours, minutes, seconds, milliseconds
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds_ = total_seconds % 60
    milliseconds = int(td.microseconds / 1000)
    
    return f"{hours:02d}:{minutes:02d}:{seconds_:02d},{milliseconds:03d}"

def transcribe_video(video_path, model_size="base"):
    print(f"Loading Whisper model ({model_size})...")
    model = whisper.load_model(model_size)
    
    print(f"Transcribing {video_path}...")
    # Using specific language 'hi' can improve Hindi detection if mixed.
    # For Hinglish, allowing auto-detect usually works better or specifying English if mostly English.
    # Let's try auto-detect first.
    result = model.transcribe(video_path)
    
    srt_path = os.path.splitext(video_path)[0] + ".srt"
    
    print(f"Saving subtitles to {srt_path}...")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"]):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip()
            
            f.write(f"{i + 1}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
            
    return srt_path

def create_short(video_path):
    print(f"Creating 9:16 Short from {video_path}...")
    clip = VideoFileClip(video_path)
    
    # Calculate crop dimensions
    w, h = clip.size
    target_ratio = 9/16
    
    # Target width based on height
    new_w = h * target_ratio
    
    # Center crop
    x1 = (w / 2) - (new_w / 2)
    x2 = (w / 2) + (new_w / 2)
    
    cropped_clip = clip.crop(x1=x1, y1=0, x2=x2, y2=h)
    
    output_path = os.path.splitext(video_path)[0] + "_short.mp4"
    
    # Write video
    print(f"Rendering short to {output_path}...")
    
    # Use slower preset for better compression, ultrafast for testing. 
    # Also ensuring audio codec is aac for compatibility.
    cropped_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="ultrafast")
    
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_video.py <video_file>")
        sys.exit(1)
        
    video_file = sys.argv[1]
    
    if not os.path.exists(video_file):
        print(f"Error: File {video_file} not found.")
        sys.exit(1)
        
    # Step 1: Transcribe
    srt_file = transcribe_video(video_file)
    
    # Step 2: Create Vertical Short
    short_file = create_short(video_file)
    
    print("\nProcessing Complete!")
    print(f"• Subtitles: {srt_file}")
    print(f"• Vertical Video: {short_file}")
