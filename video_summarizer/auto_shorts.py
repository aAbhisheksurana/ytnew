
import os
import sys
import argparse
import random
import datetime
import whisper
from moviepy import VideoFileClip
# Import our smart cropping logic
from smart_crop import smart_reframe
# Import viral subtitle generator
from subtitle_optimizer import generate_viral_subtitles

# --- Configuration ---
CLIP_DURATION = 60  # seconds
OUTPUT_DIR = "generated_shorts"
HISTORY_FILE = "generated_history.txt"
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

def get_video_duration(video_path):
    with VideoFileClip(video_path) as clip:
        return clip.duration

def generate_subtitles(video_path, output_srt_path, model_size="small"):
    """Generate ULTRA-CLEAN viral subtitles (1 word per line, no overlap)"""
    return generate_viral_subtitles(video_path, output_srt_path, words_per_chunk=1, model_size=model_size)

def burn_subtitles(video_path, srt_path, output_path):
    """Burn subtitles into video using ffmpeg"""
    print("   -> Burning subtitles into video...")
    try:
        import subprocess
        
        # FFmpeg command to burn subtitles
        # Using ass subtitles filter for better styling
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"subtitles={srt_path}:force_style='FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,BorderStyle=3,Outline=2,Shadow=1,MarginV=20,Alignment=2'",
            "-c:a", "copy",  # Copy audio without re-encoding
            "-y",  # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   -> Subtitles burned successfully!")
            return True
        else:
            print(f"   -> Warning: Could not burn subtitles: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   -> Error burning subtitles: {e}")
        return False


def add_subtitles_to_short(short_folder):
    """
    Add subtitles to an existing preview short (Phase 2).
    
    Args:
        short_folder: Path to the short folder (e.g., generated_shorts/short_12_34)
    """
    try:
        print(f"\n🎙️ Adding subtitles to: {os.path.basename(short_folder)}")
        
        final_video = os.path.join(short_folder, "final_short.mp4")
        final_srt = os.path.join(short_folder, "subtitles.srt")
        temp_no_subs = os.path.join(short_folder, "temp_no_subs.mp4")
        
        if not os.path.exists(final_video):
            print(f"   ❌ Video not found: {final_video}")
            return False
        
        # Check if subtitles already exist
        if os.path.exists(final_srt):
            print(f"   ⚠️ Subtitles already exist, skipping...")
            return True
        
        # Rename current video (without subs)
        os.rename(final_video, temp_no_subs)
        
        # Generate subtitles
        print("   -> Transcribing...")
        generate_subtitles(temp_no_subs, final_srt)
        
        # Burn subtitles
        if os.path.exists(final_srt):
            print("   -> Burning subtitles...")
            burn_success = burn_subtitles(temp_no_subs, final_srt, final_video)
            
            if burn_success:
                # Cleanup temp
                os.remove(temp_no_subs)
                print(f"   ✅ Subtitles added successfully!")
                return True
            else:
                # Restore original
                os.rename(temp_no_subs, final_video)
                print(f"   ❌ Failed to burn subtitles")
                return False
        else:
            # Restore original
            os.rename(temp_no_subs, final_video)
            print(f"   ❌ Failed to generate subtitles")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False



def load_history():
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                history.append(float(line.strip()))
    return history

def save_history(start_time):
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{start_time}\n")

def is_overlapping(start_time, history, duration=CLIP_DURATION):
    for prev_start in history:
        # Check if the new clip overlaps with any previous clip
        if abs(start_time - prev_start) < duration:
            return True
    return False

def auto_generate_shorts(video_path, count=3, use_face_tracking=True, smoothing_seconds=4, preview_mode=False, model_size="small", range_start=0.0, range_end=None):
    """
    Auto-generate shorts from video.
    
    Args:
        preview_mode: If True, skip subtitle generation (faster preview)
    """
    if preview_mode:
        print(f"🎬 PREVIEW MODE: Generating {count} shorts WITHOUT subtitles (faster!)")
    else:
        print(f"🎬 FULL MODE: Generating {count} shorts WITH subtitles")
    
    print(f"Processing: {video_path}")
    
    if not os.path.exists(video_path):
        print(f"Error: File {video_path} not found.")
        return

    # 1. Get Duration
    total_duration = get_video_duration(video_path)
    print(f"Total Video Duration: {total_duration/60:.2f} minutes")
    
    # 2. Randomly Select Slots
    history = load_history()
    selected_slots = []
    attempts = 0
    max_attempts = 100
    
    while len(selected_slots) < count and attempts < max_attempts:
        # Random start time within user-specified range (leave buffer at end)
        start_limit = range_start
        end_limit = (range_end if range_end else total_duration) - CLIP_DURATION
        
        if end_limit <= start_limit:
            print(f"Error: Selected range ({start_limit}-{end_limit+CLIP_DURATION}) is smaller than clip duration ({CLIP_DURATION}s). using 0-{total_duration} instead.")
            start_limit = 0
            end_limit = total_duration - CLIP_DURATION

        possible_start = random.uniform(start_limit, end_limit)
        
        if not is_overlapping(possible_start, history) and not is_overlapping(possible_start, selected_slots):
            selected_slots.append(possible_start)
        else:
            attempts += 1
            
    if len(selected_slots) < count:
        print(f"Warning: Could only find {len(selected_slots)} non-overlapping slots.")
    
    # 3. Process Each Slot
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for i, start_time in enumerate(selected_slots):
        end_time = start_time + CLIP_DURATION
        
        timestamp_str = f"{int(start_time//60):02d}_{int(start_time%60):02d}"
        base_name = f"short_{timestamp_str}"
        folder_name = os.path.join(OUTPUT_DIR, base_name)
        os.makedirs(folder_name, exist_ok=True)
        
        temp_cut = os.path.join(folder_name, "temp_cut.mp4")
        cropped_video = os.path.join(folder_name, "cropped.mp4")
        final_srt = os.path.join(folder_name, "subtitles.srt")
        final_video = os.path.join(folder_name, "final_short.mp4")
        
        print(f"\n[{i+1}/{len(selected_slots)}] Creating Short from {format_timestamp(start_time)} to {format_timestamp(end_time)}...")
        
        try:
            # A. Cut Video
            with VideoFileClip(video_path) as video:
                cut = video.subclipped(start_time, end_time)
                cut.write_videofile(temp_cut, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
            
            # B. Smart Crop
            crop_mode = "Face Tracking" if use_face_tracking else "Fixed Center"
            print(f"   -> Smart Cropping ({crop_mode})...")
            smart_reframe(temp_cut, cropped_video, use_face_tracking, smoothing_seconds)
            
            # C. Transcribe (SKIP in preview mode)
            if not preview_mode:
                print(f"   -> Generating Subtitles ({model_size})...")
                generate_subtitles(cropped_video, final_srt, model_size=model_size)
                
                # D. Burn Subtitles into Video
                if os.path.exists(final_srt):
                    burn_success = burn_subtitles(cropped_video, final_srt, final_video)
                    
                    if not burn_success:
                        # If burning fails, use cropped video as final
                        print("   -> Using video without burned subtitles")
                        import shutil
                        shutil.copy(cropped_video, final_video)
                else:
                    # No subtitles generated, use cropped video
                    import shutil
                    shutil.copy(cropped_video, final_video)
            else:
                # Preview mode: Skip subtitles, use cropped video directly
                print("   -> Skipping subtitles (preview mode)")
                import shutil
                shutil.copy(cropped_video, final_video)
            
            # Record History
            save_history(start_time)
            
            # Save Metadata (for Clip Editor)
            metadata = {
                "original_video": os.path.abspath(video_path),
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
                "face_tracking": use_face_tracking,
                "smoothing": smoothing_seconds
            }
            import json
            with open(os.path.join(folder_name, "metadata.json"), "w") as f:
                json.dump(metadata, f, indent=4)
            print(f"   -> Metadata saved (allows re-editing!)")
            
            # Cleanup temp files
            if os.path.exists(temp_cut):
                os.remove(temp_cut)
            if os.path.exists(cropped_video):
                os.remove(cropped_video)
                
            print(f"   -> Success! Saved in {folder_name}")
            
        except Exception as e:
            print(f"   -> Failed: {e}")

    print("\n" + "="*50)
    print(f"All done! Generated {len(selected_slots)} shorts in '{OUTPUT_DIR}'")
    print("Run this script again to generate MORE unique shorts.")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto Generate Viral Shorts from Long Video")
    parser.add_argument("video", help="Path to input video file")
    parser.add_argument("--count", type=int, default=3, help="Number of shorts to generate (default: 3)")
    parser.add_argument("--face-tracking", action="store_true", help="Enable face tracking (dynamic crop)")
    parser.add_argument("--no-face-tracking", action="store_true", help="Disable face tracking (fixed center crop)")
    parser.add_argument("--smoothing", type=int, default=4, help="Smoothing window in seconds (default: 4)")
    parser.add_argument("--preview", action="store_true", help="Preview mode: Skip subtitles for faster generation")
    parser.add_argument("--model-size", default="small", choices=["small", "large-v2", "medium"], help="Subtitle model size")
    parser.add_argument("--range-start", type=float, default=0.0, help="Start time for random selection (seconds)")
    parser.add_argument("--range-end", type=float, default=0.0, help="End time for random selection (seconds, 0 = end)")
    
    args = parser.parse_args()
    
    # Determine face tracking setting
    use_face_tracking = False  # Default to OFF for speed (CPU optimization)
    if args.face_tracking:
        use_face_tracking = True
    elif args.no_face_tracking:
        use_face_tracking = False
    
    # Determine end range
    range_end = args.range_end if args.range_end > 0 else None
    
    auto_generate_shorts(args.video, args.count, use_face_tracking, args.smoothing, preview_mode=args.preview, model_size=args.model_size, range_start=args.range_start, range_end=range_end)
