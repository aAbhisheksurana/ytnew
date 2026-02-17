
import os
import sys
import argparse
import datetime
import whisper
from moviepy import VideoFileClip
# Import our smart cropping logic
from smart_crop import smart_reframe

def parse_time(time_str):
    """Converts MM:SS or HH:MM:SS to seconds"""
    parts = list(map(int, time_str.split(':')))
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    else:
        return int(time_str)

def format_timestamp(seconds: float):
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds_ = total_seconds % 60
    milliseconds = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_:02d},{milliseconds:03d}"

def generate_subtitles(video_path, output_srt_path):
    print(f"Transcribing {video_path} using Whisper (Large)...")
    model = whisper.load_model("large")
    result = model.transcribe(video_path, language="hi")
    
    with open(output_srt_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"]):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip()
            
            f.write(f"{i + 1}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
    print(f"Subtitles saved: {output_srt_path}")

def create_viral_short(video_file, start_str, end_str):
    # 0. Setup Paths
    if not os.path.exists(video_file):
        print(f"Error: File {video_file} not found.")
        return

    base_name = os.path.splitext(os.path.basename(video_file))[0]
    timestamp = datetime.datetime.now().strftime("%H%M")
    output_folder = f"short_{timestamp}"
    os.makedirs(output_folder, exist_ok=True)
    
    temp_cut = os.path.join(output_folder, "temp_cut.mp4")
    final_video = os.path.join(output_folder, f"{base_name}_vertical.mp4")
    final_srt = os.path.join(output_folder, f"{base_name}_subs.srt")

    # 1. Cut the Video
    start_sec = parse_time(start_str)
    end_sec = parse_time(end_str)
    print(f"Step 1: Cutting video from {start_str} to {end_str}...")
    
    with VideoFileClip(video_file) as video:
        cut = video.subclipped(start_sec, end_sec)
        cut.write_videofile(temp_cut, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)

    # 2. Smart Crop (Face Tracking)
    print("Step 2: Smart Cropping (Face Tracking)...")
    smart_reframe(temp_cut, final_video)

    # 3. Transcribe
    print("Step 3: Generating Hindi Subtitles...")
    generate_subtitles(final_video, final_srt)

    # Cleanup
    if os.path.exists(temp_cut):
        os.remove(temp_cut)

    print("\n" + "="*50)
    print(f"DONE! Your viral short is ready in folder: {output_folder}")
    print(f"Video: {final_video}")
    print(f"SRT:   {final_srt}")
    print("="*50)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python create_short.py <video_file> <start_time> <end_time>")
        print("Example: python create_short.py videoplayback.mp4 05:12 05:32")
    else:
        create_viral_short(sys.argv[1], sys.argv[2], sys.argv[3])
