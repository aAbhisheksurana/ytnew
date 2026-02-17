
import os
import sys
from moviepy import VideoFileClip, vfx

# Paths
VIDEO_PATH = "videoplayback.mp4"
PROCESSED_SHORT = "preview_short.mp4"
FFMPEG_BINARY = os.path.abspath("../bin/ffmpeg")

# Setup FFmpeg
if os.path.exists(FFMPEG_BINARY):
    os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_BINARY
    os.environ["PATH"] += os.pathsep + os.path.dirname(FFMPEG_BINARY)

print("Creating 30-second preview...")

# Load Video (Only 01:00 to 01:30)
try:
    clip = VideoFileClip(VIDEO_PATH).subclipped(60, 90)
    
    # Create Vertical Crop (9:16)
    w, h = clip.size
    target_ratio = 9/16
    new_w = h * target_ratio
    
    x_center = w / 2
    y_center = h / 2
    
    # Crop using vfx (Center Crop)
    cropped_clip = clip.cropped(x1=(w/2)-(new_w/2), y1=0, width=new_w, height=h)
    
    # Write video
    cropped_clip.write_videofile(PROCESSED_SHORT, codec="libx264", audio_codec="aac", preset="ultrafast")
    
    print(f"Preview created: {PROCESSED_SHORT}")

except Exception as e:
    print(f"Error: {e}")
