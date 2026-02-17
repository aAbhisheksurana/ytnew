
import os
import sys
import datetime
from moviepy import VideoFileClip
import whisper

# Paths
VIDEO_PATH = "videoplayback.mp4"
CLIP_PATH = "test_clip_large.mp4"
FFMPEG_BINARY = os.path.abspath("../bin/ffmpeg")

# Setup FFmpeg
if os.path.exists(FFMPEG_BINARY):
    os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_BINARY
    os.environ["PATH"] += os.pathsep + os.path.dirname(FFMPEG_BINARY)

def format_timestamp(seconds: float):
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds_ = total_seconds % 60
    milliseconds = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_:02d},{milliseconds:03d}"

print("Step 1: Extracting 30-second clip (05:00 - 05:30)...")
# Extract only the problematic part
try:
    clip = VideoFileClip(VIDEO_PATH).subclipped(300, 330) # 5 min to 5:30 min
    clip.write_videofile(CLIP_PATH, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
    print(f"Clip saved: {CLIP_PATH}")
except Exception as e:
    print(f"Error extracting clip: {e}")
    sys.exit(1)

print("\nStep 2: Transcribing with Whisper LARGE Model (This may take a moment)...")
try:
    # Load the LARGE model
    model = whisper.load_model("large")
    
    # Transcribe
    result = model.transcribe(CLIP_PATH, language="hi") # Force Hindi
    
    print("\n--- TRANSCRIPTION RESULT (LARGE MODEL) ---")
    for segment in result["segments"]:
        start = format_timestamp(segment["start"])
        end = format_timestamp(segment["end"])
        text = segment["text"].strip()
        print(f"[{start} --> {end}] {text}")
    print("------------------------------------------")

except Exception as e:
    print(f"Error transcribing: {e}")
