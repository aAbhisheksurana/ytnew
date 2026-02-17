import streamlit as st
import os
import glob
from pathlib import Path
import subprocess
import time

# Page config
st.set_page_config(
    page_title="AI Shorts Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        border: none;
        font-size: 1.1rem;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4);
        transform: translateY(-2px);
    }
    .short-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 2px solid rgba(102, 126, 234, 0.2);
        transition: all 0.3s ease;
    }
    .short-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.15);
        border-color: rgba(102, 126, 234, 0.5);
    }
    .short-card h4 {
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    .stat-box {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    /* Make video player vertical (9:16 shorts format) */
    .stVideo {
        max-width: 250px !important;
        margin: 0 auto !important;
        display: block !important;
    }
    video {
        width: 100% !important;
        height: auto !important;
        aspect-ratio: 9/16 !important;
        object-fit: contain !important;
        border-radius: 8px;
        background: #000;
    }
    .stat-label {
        color: #666;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🎬 AI Viral Shorts Generator</h1>', unsafe_allow_html=True)
st.markdown("### Transform long videos into engaging vertical shorts with AI-powered subtitles")

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/video-editing.png", width=80)
    st.title("⚙️ Settings")
    
    num_shorts = st.number_input(
        "Number of Shorts",
        min_value=1,
        max_value=50,
        value=3,
        step=1,
        help="How many random shorts to generate (1-50)"
    )
    
    use_face_tracking = st.checkbox(
        "🎯 Enable Face Tracking",
        value=False,
        help="Track faces for dynamic cropping. Disable for fixed center crop (more stable)"
    )
    
    if use_face_tracking:
        smoothing = st.slider(
            "Smoothing (seconds)",
            min_value=2,
            max_value=8,
            value=4,
            help="Higher = smoother camera movement, but less responsive"
        )
    else:
        smoothing = 4  # Default, won't be used
    
    st.divider()
    
    st.markdown("### 🎙️ Subtitle Model")
    sub_quality = st.radio(
        "Subtitle Model (Accuracy vs Speed)",
        ["Fast (Small)", "Balanced (Medium)", "Best (Large)"],
        index=0,
        help="Small (~20s) is fast. Medium (~60s) is balanced. Large (~3-5m) is most accurate but heavy on CPU."
    )
    
    if "Best" in sub_quality:
        model_size = "large-v2"
    elif "Balanced" in sub_quality:
        model_size = "medium"
    else:
        model_size = "small"
    
    st.divider()
    
    st.markdown("### 🎯 Features")
    st.markdown("""
    - ✅ Auto 9:16 Conversion
    - ✅ AI Face Tracking
    - ✅ Hindi Subtitles (Whisper AI)
    - ✅ Random Clip Selection
    - ✅ No Duplicates
    """)
    
    st.divider()
    
    if st.button("🗑️ Clear All Shorts"):
        import shutil
        if os.path.exists("generated_shorts"):
            shutil.rmtree("generated_shorts")
        if os.path.exists("generated_history.txt"):
            os.remove("generated_history.txt")
        st.success("All shorts cleared!")
        st.rerun()

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📤 Add Video")
    
    # Tabs for Upload vs URL
    tab1, tab2 = st.tabs(["📁 Upload File", "🔗 From URL"])
    
    video_path = None
    uploaded_file = None
    
    with tab1:
        uploaded_file = st.file_uploader(
            "Drop your video here or click to browse",
            type=['mp4', 'avi', 'mov', 'mkv'],
            help="Upload a long-form video to generate shorts from"
        )
        
        if uploaded_file:
            # Save uploaded file
            video_path = f"uploaded_{uploaded_file.name}"
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"✅ Uploaded: {uploaded_file.name}")
            file_size = os.path.getsize(video_path) / (1024 * 1024)
            st.info(f"📊 File Size: {file_size:.2f} MB")
    
    with tab2:
        video_url = st.text_input(
            "Enter video URL",
            placeholder="https://youtube.com/watch?v=... or direct .mp4 link",
            help="Supports YouTube, Vimeo, and direct video URLs"
        )
        
        if video_url:
            st.info("✅ URL ready! Click 'Generate Shorts' below to process.")
            # Set video_path to URL (will download automatically during generation)
            video_path = video_url
    
    # Generate button (only show if video is ready)
    if video_path:
        # Check if video_path is URL or file
        is_url = video_path.startswith('http://') or video_path.startswith('https://')
        
        if is_url or os.path.exists(video_path):
            st.divider()
            st.markdown("### ✂️ Select Video Portion")
            
            # If URL, download first to get duration
            if is_url:
                st.info("📥 Fetching video information...")
                try:
                    import yt_dlp
                    
                    with st.spinner("Getting video details..."):
                        ydl_opts = {
                            'format': 'best[ext=mp4]/best',
                            'outtmpl': 'downloaded_video.%(ext)s',
                            'quiet': True,
                            'no_warnings': True,
                        }
                        
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(video_url, download=True)
                            actual_video_path = f"downloaded_video.{info['ext']}"
                        
                        video_path = actual_video_path
                        st.success("✅ Video ready for processing!")
                        
                except Exception as e:
                    st.error(f"❌ Could not fetch video: {str(e)}")
                    video_path = None
            
            
            if video_path and os.path.exists(video_path):
                # Get video duration
                try:
                    from moviepy import VideoFileClip
                    
                    with VideoFileClip(video_path) as vid:
                        duration = vid.duration
                        duration_min = duration / 60
                    
                    # Show video preview
                    st.video(video_path)
                    
                    st.markdown(f"**Total Duration:** {int(duration_min)} min {int(duration % 60)} sec")
                    
                    # Warning for long videos
                    if duration_min > 30:
                        st.warning(f"""
                        ⚠️ **Performance Warning:** This video is {int(duration_min)} minutes long.
                        
                        **Recommendations:**
                        - Use timeline to select a smaller portion (under 30 min)
                        - Face tracking disabled for faster processing
                        - Expect 15-20 minutes processing time
                        - Monitor system resources (CPU/RAM)
                        """)
                    
                    st.markdown("#### ✂️ Drag to Select Timeline")
                    
                    # Dual-range slider for timeline selection
                    time_range = st.slider(
                        "Select time range by dragging the handles",
                        min_value=0.0,
                        max_value=duration,
                        value=(0.0, duration),
                        step=1.0,
                        format="%d sec",
                        help="Drag the left handle for start time, right handle for end time"
                    )
                    
                    start_time = time_range[0]
                    end_time = time_range[1]
                    
                    # Convert to readable format
                    start_min = int(start_time // 60)
                    start_sec = int(start_time % 60)
                    end_min = int(end_time // 60)
                    end_sec = int(end_time % 60)
                    
                    selected_duration = end_time - start_time
                    
                    if selected_duration <= 0:
                        st.error("⚠️ End time must be greater than start time!")
                    else:
                        st.success(f"✅ Selected: {selected_duration/60:.1f} minutes ({start_min}:{start_sec:02d} to {end_min}:{end_sec:02d})")
                        
                        # Extract and show frame previews (optimized to prevent hang)
                        st.markdown("#### 🎞️ Frame Preview")
                        
                        # Only update frames when slider changes significantly (every 5 seconds)
                        import hashlib
                        frame_cache_key = f"{int(start_time//5)*5}_{int(end_time//5)*5}"
                        
                        # Use session state for caching
                        if 'last_frame_key' not in st.session_state:
                            st.session_state.last_frame_key = None
                        
                        # Only extract frames if slider moved significantly
                        if st.session_state.last_frame_key != frame_cache_key:
                            try:
                                import cv2
                                import numpy as np
                                
                                # Open video
                                cap = cv2.VideoCapture(video_path)
                                
                                if cap.isOpened():
                                    fps = cap.get(cv2.CAP_PROP_FPS)
                                    
                                    col_frame1, col_frame2 = st.columns(2)
                                    
                                    with col_frame1:
                                        st.markdown(f"**Start Frame** ({start_min}:{start_sec:02d})")
                                        # Seek to start time
                                        cap.set(cv2.CAP_PROP_POS_FRAMES, int(start_time * fps))
                                        ret, start_frame = cap.read()
                                        
                                        if ret:
                                            # Resize for faster display (reduce memory)
                                            start_frame = cv2.resize(start_frame, (320, 180))
                                            # Convert BGR to RGB
                                            start_frame = cv2.cvtColor(start_frame, cv2.COLOR_BGR2RGB)
                                            st.image(start_frame, use_container_width=True)
                                        else:
                                            st.info("🎬 Move slider to preview")
                                    
                                    with col_frame2:
                                        st.markdown(f"**End Frame** ({end_min}:{end_sec:02d})")
                                        # Seek to end time
                                        cap.set(cv2.CAP_PROP_POS_FRAMES, int(end_time * fps))
                                        ret, end_frame = cap.read()
                                        
                                        if ret:
                                            # Resize for faster display
                                            end_frame = cv2.resize(end_frame, (320, 180))
                                            # Convert BGR to RGB
                                            end_frame = cv2.cvtColor(end_frame, cv2.COLOR_BGR2RGB)
                                            st.image(end_frame, use_container_width=True)
                                        else:
                                            st.info("🎬 Move slider to preview")
                                    
                                    # IMPORTANT: Release video capture to free memory
                                    cap.release()
                                    
                                    # Update cache key
                                    st.session_state.last_frame_key = frame_cache_key
                                else:
                                    st.warning("Could not open video for preview")
                                
                            except Exception as e:
                                st.warning(f"Preview unavailable: {str(e)}")
                        else:
                            # Show cached message
                            st.info("💡 Move slider by 5+ seconds to update preview (optimized for performance)")
                        
                        # Visual timeline
                        st.markdown("#### 📊 Timeline Preview")
                        progress_start = start_time / duration
                        progress_end = end_time / duration
                        
                        # Create visual representation
                        st.markdown(f"""
                        <div style="background: #e0e0e0; height: 30px; border-radius: 5px; position: relative; margin: 10px 0;">
                            <div style="background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; 
                                 border-radius: 5px; width: {progress_end*100}%; position: absolute; opacity: 0.3;"></div>
                            <div style="background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; 
                                 border-radius: 5px; margin-left: {progress_start*100}%; 
                                 width: {(progress_end-progress_start)*100}%; position: relative;">
                                <span style="position: absolute; left: 5px; top: 5px; color: white; font-size: 12px; font-weight: bold;">
                                    Selected Portion
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Two-phase workflow buttons
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            preview_btn = st.button("🎬 Generate Previews (Fast!)", key="generate_preview", use_container_width=True, type="primary")
                            st.caption("Generates shorts WITHOUT subtitles (~45 min)")
                        
                        with col_btn2:
                            full_btn = st.button("🚀 Generate with Subtitles", key="generate_full", use_container_width=True)
                            st.caption("Generates WITH subtitles (~75 min)")
                        
                        # Phase 1: Preview Mode (No Subtitles)
                        # Phase 1: Preview Mode (No Subtitles)
                        if preview_btn:
                            with st.spinner("🎬 Generating preview shorts (no subtitles)... Much faster!"):
                                # Clear previous shorts
                                import shutil
                                if os.path.exists("generated_shorts"):
                                    shutil.rmtree("generated_shorts")
                                if os.path.exists("generated_history.txt"):
                                    os.remove("generated_history.txt")
                                    
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                try:
                                    # Run the shorts generator directly on ORIGINAL video with RANGE args
                                    status_text.text("⏳ Generating preview shorts (skipping subtitles)...")
                                    tracking_flag = "--face-tracking" if use_face_tracking else "--no-face-tracking"
                                    smoothing_flag = f"--smoothing {smoothing}" if use_face_tracking else ""
                                    
                                    # Pass range args
                                    cmd = f"source venv/bin/activate && python auto_shorts.py '{video_path}' --range-start {start_time} --range-end {end_time} --count {num_shorts} {tracking_flag} {smoothing_flag} --preview"
                                    
                                    process = subprocess.Popen(
                                        cmd,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        executable='/bin/bash'
                                    )
                                    
                                    # Monitor progress
                                    current_progress = 10
                                    while process.poll() is None:
                                        time.sleep(1)
                                        current_progress = min(current_progress + 2, 95)
                                        progress_bar.progress(current_progress)
                                    
                                    stdout, stderr = process.communicate()
                                    
                                    if process.returncode == 0:
                                        progress_bar.progress(100)
                                        status_text.text("✅ Generation Complete!")
                                        st.balloons()
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Error: {stderr}")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                        
                        # Phase 2: Full Mode (With Subtitles)
                        if full_btn:
                            with st.spinner("🎬 Generating shorts with subtitles... This will take longer"):
                                # Clear previous shorts
                                import shutil
                                if os.path.exists("generated_shorts"):
                                    shutil.rmtree("generated_shorts")
                                if os.path.exists("generated_history.txt"):
                                    os.remove("generated_history.txt")
                                    
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                try:
                                    # Run the shorts generator directly on ORIGINAL video with RANGE args
                                    status_text.text("⏳ Generating shorts with subtitles...")
                                    tracking_flag = "--face-tracking" if use_face_tracking else "--no-face-tracking"
                                    smoothing_flag = f"--smoothing {smoothing}" if use_face_tracking else ""
                                    # Note: NO --preview flag = full mode with subtitles
                                    cmd = f"source venv/bin/activate && python auto_shorts.py '{video_path}' --range-start {start_time} --range-end {end_time} --count {num_shorts} {tracking_flag} {smoothing_flag} --model-size {model_size}"
                                    
                                    process = subprocess.Popen(
                                        cmd,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        executable='/bin/bash'
                                    )
                                    
                                    # Monitor progress
                                    current_progress = 10
                                    while process.poll() is None:
                                        time.sleep(1)
                                        current_progress = min(current_progress + 2, 95)
                                        progress_bar.progress(current_progress)
                                    
                                    stdout, stderr = process.communicate()
                                    
                                    if process.returncode == 0:
                                        progress_bar.progress(100)
                                        status_text.text("✅ Generation Complete!")
                                        st.balloons()
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Error: {stderr}")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                                        
                except Exception as e:
                    st.error(f"Could not load video: {str(e)}")

with col2:
    # Statistics
    st.markdown("### 📊 Statistics")
    
    shorts_dirs = glob.glob("generated_shorts/short_*")
    total_shorts = len(shorts_dirs)
    
    total_size = 0
    for short_dir in shorts_dirs:
        for file in glob.glob(f"{short_dir}/*"):
            if os.path.isfile(file):
                total_size += os.path.getsize(file)
    
    total_size_mb = total_size / (1024 * 1024)
    
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{total_shorts}</div>
        <div class="stat-label">Total Shorts</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-number">{total_size_mb:.1f} MB</div>
        <div class="stat-label">Total Size</div>
    </div>
    """, unsafe_allow_html=True)

# Display generated shorts
st.divider()
st.markdown("### 🎥 Generated Shorts Gallery")

if not shorts_dirs:
    st.info(" 👆 Upload a video and click 'Generate Previews' to get started!")
else:
    # Initialize selection state
    if 'selected_shorts' not in st.session_state:
        st.session_state.selected_shorts = set()
    
    # Add subtitles button (Phase 2)
    col_btn_subs1, col_btn_subs2, col_btn_subs3 = st.columns([2, 2, 1])
    
    with col_btn_subs1:
        if st.button("🎙️ Add Subtitles to Selected", key="add_subs", type="primary", use_container_width=True):
            if not st.session_state.selected_shorts:
                st.warning("⚠️ Please select at least one short!")
            else:
                with st.spinner(f"Adding subtitles to {len(st.session_state.selected_shorts)} shorts..."):
                    from auto_shorts import add_subtitles_to_short
                    
                    progress = st.progress(0)
                    success_count = 0
                    total = len(st.session_state.selected_shorts)
                    
                    for idx, short_dir in enumerate(st.session_state.selected_shorts):
                        result = add_subtitles_to_short(short_dir)
                        if result:
                            success_count += 1
                        progress.progress((idx + 1) / total)
                    
                    st.success(f"✅ Added subtitles to {success_count}/{total} shorts!")
                    st.session_state.selected_shorts = set()
                    time.sleep(1)
                    st.rerun()
    
    with col_btn_subs2:
        if st.button("✅ Select All", key="select_all", use_container_width=True):
            st.session_state.selected_shorts = set(shorts_dirs)
            st.rerun()
    
    with col_btn_subs3:
        if st.button("Clear", key="clear_selection", use_container_width=True):
            st.session_state.selected_shorts = set()
            st.rerun()
    
    st.caption(f"Selected: {len(st.session_state.selected_shorts)} shorts")
    
    # Sort by creation time (newest first)
    shorts_dirs = sorted(shorts_dirs, key=os.path.getmtime, reverse=True)
    
    cols = st.columns(3)  # Changed to 3 columns for compact view
    
    for idx, short_dir in enumerate(shorts_dirs):
        col = cols[idx % 3]  # Fixed for 3 columns
        
        with col:
            short_name = os.path.basename(short_dir)
            timestamp = short_name.replace("short_", "").replace("_", ":")
            
            # Check if has subtitles
            srt_file = glob.glob(f"{short_dir}/subtitles.srt")
            has_subtitles = len(srt_file) > 0
            subtitle_badge = "🎙️ WITH Subs" if has_subtitles else "📹 Preview"
            badge_color = "#28a745" if has_subtitles else "#ffc107"
            
            # Checkbox for selection
            is_selected = short_dir in st.session_state.selected_shorts
            checkbox_key = f"select_{short_name}"
            
            if st.checkbox(f"Select", value=is_selected, key=checkbox_key):
                st.session_state.selected_shorts.add(short_dir)
            else:
                st.session_state.selected_shorts.discard(short_dir)
            
            st.markdown(f"""
            <div class="short-card">
                <h4>📹 Short: {timestamp}</h4>
                <span style="background: {badge_color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold;">
                    {subtitle_badge}
                </span>
            """, unsafe_allow_html=True)
            
            # Find video and subtitle files
            video_file = glob.glob(f"{short_dir}/final_short.mp4")
            
            if video_file:
                video_path = video_file[0]
                file_size = os.path.getsize(video_path) / (1024 * 1024)
                
                # Video player
                with open(video_path, 'rb') as video:
                    st.video(video.read())
                
                st.markdown(f"**Size:** {file_size:.2f} MB")
                
                # Download buttons
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    with open(video_path, 'rb') as file:
                        st.download_button(
                            label="📥 Download Video",
                            data=file.read(),
                            file_name=f"short_{timestamp.replace(':', '_')}.mp4",
                            mime="video/mp4",
                            key=f"video_{short_name}"
                        )
                
                    with col_btn2:
                        # Always show Create/Regenerate button (User Request)
                        if st.button("✨ Create Vizard Subtitles", key=f"create_subs_{short_name}", help="Generates/Regenerates Vizard-style subtitles for this clip"):

                            status_box = st.empty()
                            progress = st.progress(0)
                            
                            try:
                                status_box.info(f"🎙️ Transcribing audio ({model_size} model)...")
                                progress.progress(10)
                                
                                # Define paths
                                current_srt = os.path.join(short_dir, "subtitles.srt")
                                temp_output = os.path.join(short_dir, "temp_subs_burn.mp4")
                                
                                # Import generator
                                from auto_shorts import generate_subtitles
                                import subprocess
                                
                                # 1. Generate SRT
                                success = generate_subtitles(video_path, current_srt, model_size=model_size)
                                progress.progress(50)
                                
                                if success and os.path.exists(current_srt):
                                    # 2. Burn Subtitles
                                    status_box.info("🔥 Burning Vizard-style captions...")
                                    
                                    # Burn command (same as main logic)
                                    cmd = [
                                        "ffmpeg",
                                        "-i", video_path,
                                        "-vf", f"subtitles='{current_srt}':force_style='FontName=Arial,FontSize=28,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=60'",
                                        "-c:a", "copy",
                                        "-y",
                                        temp_output
                                    ]
                                    
                                    try:
                                        subprocess.run(cmd, check=True, capture_output=True)
                                        progress.progress(90)
                                        
                                        # 3. Replace file
                                        if os.path.exists(temp_output):
                                            os.replace(temp_output, video_path)
                                            status_box.success("✅ Subtitles Added!")
                                            progress.progress(100)
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            status_box.error("❌ Failed to burn subtitles (ffmpeg error)")
                                    except subprocess.CalledProcessError as e:
                                        status_box.error(f"❌ Burning Failed: {e}")
                                else:
                                    status_box.error("❌ Transcription Failed (Try checking logs)")
                                    
                            except Exception as e:
                                status_box.error(f"❌ Error: {str(e)}")
                
                # Edit Clip Feature
                with st.expander("✂️ Edit Clip Timing"):
                    st.caption("Adjust start/end times to fine-tune this clip")
                    
                    # Parse current timing logic (Prioritize Metadata > Folder Name)
                    meta_file = os.path.join(short_dir, "metadata.json")
                    meta_start = None
                    meta_duration = 60
                    
                    if os.path.exists(meta_file):
                        try:
                            import json
                            with open(meta_file, 'r') as f:
                                m = json.load(f)
                                meta_start = m.get('start_time')
                                meta_duration = m.get('duration', 60)
                        except:
                            pass
                    
                    # Fallback to folder name
                    time_parts = short_name.replace("short_", "").split("_")
                    folder_start = 0
                    try:
                        if len(time_parts) >= 2:
                            curr_start_min = int(time_parts[0])
                            curr_start_sec = int(time_parts[1])
                            folder_start = curr_start_min * 60 + curr_start_sec
                    except:
                        folder_start = 0 # Safe default
                        
                    # Decide which to use
                    if meta_start is not None:
                        curr_start = meta_start
                        curr_duration = meta_duration
                    else:
                        curr_start = folder_start
                        curr_duration = 60

                    curr_end = curr_start + curr_duration
                    
                    # Initialize UI display vars
                    curr_start_min = int(curr_start // 60)
                    curr_start_sec = int(curr_start % 60)

                    # Initialize session state for this clip
                    adj_key = f"clip_adj_{short_name}"
                    if adj_key not in st.session_state:
                        st.session_state[adj_key] = {'start': curr_start, 'duration': curr_duration}
                        
                    st.info(f"Current: {curr_start_min}:{curr_start_sec:02d} to {int(curr_end//60)}:{int(curr_end%60):02d}")
                    

                        
                    # Quick adjust buttons (FIRST - before inputs)
                    st.markdown("**Fine-Tune Clip:**")
                    
                    # Row 1: Start Time Adjustments (Keep End Time Fixed)
                    c1, c2, c3, c4 = st.columns(4)
                    
                    with c1:
                        # Start Earlier (-5s) -> Increase Duration
                        if st.button("⏪ Start -5s", key=f"s_pre_{short_name}", help="Include previous 5s (Keep End fixed)"):
                            new_s = max(0, st.session_state[adj_key]['start'] - 5)
                            diff = st.session_state[adj_key]['start'] - new_s
                            st.session_state[adj_key]['start'] = new_s
                            st.session_state[adj_key]['duration'] += diff
                            
                            # Update widgets
                            st.session_state[f"emin_{short_name}"] = new_s // 60
                            st.session_state[f"esec_{short_name}"] = new_s % 60
                            st.session_state[f"edur_{short_name}"] = st.session_state[adj_key]['duration']
                            st.rerun()

                    with c2:
                        # Start Later (+5s) -> Decrease Duration to keep End fixed
                        if st.button("⏩ Start +5s", key=f"s_post_{short_name}", help="Cut first 5s (Keep End fixed)"):
                            st.session_state[adj_key]['start'] += 5
                            st.session_state[adj_key]['duration'] = max(5, st.session_state[adj_key]['duration'] - 5)
                            
                            # Update widgets
                            new_s = st.session_state[adj_key]['start']
                            st.session_state[f"emin_{short_name}"] = new_s // 60
                            st.session_state[f"esec_{short_name}"] = new_s % 60
                            st.session_state[f"edur_{short_name}"] = st.session_state[adj_key]['duration']
                            st.rerun()

                    with c3:
                        # End Earlier (-5s) -> Decrease Duration
                        if st.button("❌ End -5s", key=f"e_pre_{short_name}", help="Cut last 5s (Keep Start fixed)"):
                            st.session_state[adj_key]['duration'] = max(5, st.session_state[adj_key]['duration'] - 5)
                            # Update widgets
                            st.session_state[f"edur_{short_name}"] = st.session_state[adj_key]['duration']
                            st.rerun()

                    with c4:
                        # End Later (+5s) -> Increase Duration
                        if st.button("➕ End +5s", key=f"e_post_{short_name}", help="Include next 5s (Keep Start fixed)"):
                            st.session_state[adj_key]['duration'] = min(300, st.session_state[adj_key]['duration'] + 5)
                            # Update widgets
                            st.session_state[f"edur_{short_name}"] = st.session_state[adj_key]['duration']
                            st.session_state[f"ealign_{short_name}"] = st.session_state[adj_key].get('manual_alignment', 0.5)
                            st.rerun()
                    
                    st.divider()
                    
                    # Detect Source Video (Moved up for Preview)
                    preview_source = None
                    try:
                        # 1. Check metadata.json
                        if os.path.exists(meta_file):
                                import json
                                try:
                                    with open(meta_file, 'r') as f:
                                        m = json.load(f)
                                        if 'original_video' in m and os.path.exists(m['original_video']):
                                            preview_source = m['original_video']
                                except: pass
                        
                        # 2. Fallback
                        if not preview_source:
                            import glob
                            videos = glob.glob("*.mp4")
                            if videos:
                                # Filter out shorts/trimmed
                                candidates = [v for v in videos if "short" not in v and "trimmed" not in v]
                                if candidates:
                                    preview_source = max(candidates, key=os.path.getsize)
                                else:
                                    preview_source = max(videos, key=os.path.getsize)
                    except: pass

                    # New timing controls
                    col_time1, col_time2 = st.columns(2)
                        
                    # Use session state values as defaults
                    adjusted_start = st.session_state[adj_key]['start']
                    adjusted_duration = int(st.session_state[adj_key]['duration'])
                    adjusted_face = st.session_state[adj_key].get('face_tracking', False)
                    adjusted_align = st.session_state[adj_key].get('manual_alignment', 0.5)
                    adjusted_start_min = int(adjusted_start // 60)
                    adjusted_start_sec = int(adjusted_start % 60)
                        
                    with col_time1:
                        st.markdown("**Start Time**")
                        new_start_min = st.number_input("Min", 0, 999, adjusted_start_min, key=f"emin_{short_name}")
                        new_start_sec = st.number_input("Sec", 0, 59, adjusted_start_sec, key=f"esec_{short_name}")
                        new_start = new_start_min * 60 + new_start_sec
                            
                        # Update session state when manually changed
                        if new_start != adjusted_start:
                            st.session_state[adj_key]['start'] = new_start
                        
                    with col_time2:
                        st.markdown("**Duration & Settings**")
                        new_duration = st.slider("Seconds", 10, 120, adjusted_duration, 5, key=f"edur_{short_name}")
                        new_end = new_start + new_duration
                        st.caption(f"End: {int(new_end//60)}:{int(new_end%60):02d}")
                        
                        # Face Tracking Override
                        new_face = st.checkbox("Enable Face Tracking", value=adjusted_face, key=f"eface_{short_name}", help="Uncheck to fix shaky camera (uses Manual Crop)")
                        
                        # Manual Alignment (Only if Face Tracking OFF)
                        new_align = adjusted_align
                        if not new_face:
                            new_align = st.slider("Crop Focus (Left <> Right)", 0.0, 1.0, adjusted_align, 0.1, key=f"ealign_{short_name}", help="0.0=Left, 0.5=Center, 1.0=Right")
                            
                            # --- CROP PREVIEW ---
                            if preview_source and os.path.exists(preview_source):
                                try:
                                    import cv2
                                    cap = cv2.VideoCapture(preview_source)
                                    cap.set(cv2.CAP_PROP_POS_MSEC, adjusted_start * 1000)
                                    ret, frame = cap.read()
                                    cap.release()
                                    
                                    if ret:
                                        # BGR to RGB
                                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                        h, w, _ = frame.shape
                                        
                                        # Calculate Crop Rect (Same logic as smart_crop.py)
                                        target_ratio = 9/16
                                        new_w = h * target_ratio
                                        
                                        min_center = new_w / 2
                                        max_center = w - (new_w / 2)
                                        
                                        center_x = min_center + (new_align * (max_center - min_center))
                                        
                                        x1 = int(center_x - (new_w / 2))
                                        
                                        # Clamp
                                        if x1 < 0: x1 = 0
                                        if x1 + int(new_w) > w: x1 = w - int(new_w)
                                            
                                        x2 = x1 + int(new_w)
                                        
                                        # Crop
                                        crop_img = frame[:, x1:x2]
                                        
                                        # Show Preview
                                        st.caption("🖼️ Live Preview:")
                                        st.image(crop_img, use_container_width=False, width=150)
                                except Exception as e:
                                    pass

                        # Update session state when manually changed
                        if new_duration != adjusted_duration:
                            st.session_state[adj_key]['duration'] = new_duration
                        if new_face != adjusted_face:
                            st.session_state[adj_key]['face_tracking'] = new_face
                        if new_align != adjusted_align:
                            st.session_state[adj_key]['manual_alignment'] = new_align
                        

                    st.divider()
                    
                    # Preview (Hidden by default, used for verification)
                    with st.expander("👁️ Verify Timestamp (Preview Source)", expanded=False):
                        st.caption("Use this to check if the Start Time matches the scene you want.")
                        
                        import glob
                        all_videos = glob.glob("*.mp4")
                        source_candidates = [v for v in all_videos if "short" not in v and "trimmed" not in v]
                        if not source_candidates: source_candidates = all_videos
                        
                        default_idx = 0
                        # Use preview_source detected above as default
                        if preview_source and preview_source in source_candidates:
                            default_idx = source_candidates.index(preview_source)
                        elif source_candidates:
                             largest = max(source_candidates, key=os.path.getsize)
                             if largest in source_candidates:
                                 default_idx = source_candidates.index(largest)
                             
                        selected_source = st.selectbox("🎥 Preview Source", source_candidates, index=default_idx, key=f"src_{short_name}")
                        
                        # Verify Source and Show Video
                        if selected_source and os.path.exists(selected_source):
                            pv_time = int(st.session_state[adj_key]['start'])
                            st.caption(f"🎥 Previewing start at {int(pv_time//60)}:{int(pv_time%60):02d} (Click Play using the player controls)")
                            st.video(selected_source, start_time=pv_time)
                            st.info("💡 If this video doesn't match your clip, try changing the 'Preview Source' dropdown above.")
                        else:
                            st.warning("Source video not found")
                   
                    # Apply button
                    if st.button("✅ Regenerate with New Timing", key=f"regen_{short_name}", type="primary", help="Takes ~30-60 seconds for a 1 min clip"):
                        # Try to find original path automatically
                        original_video = None
                            
                        # 1. Check metadata.json
                        meta_file = os.path.join(short_dir, "metadata.json")
                        if os.path.exists(meta_file):
                            import json
                            try:
                                with open(meta_file, 'r') as f:
                                    meta = json.load(f)
                                    if 'original_video' in meta and os.path.exists(meta['original_video']):
                                        original_video = meta['original_video']
                            except:
                                pass
                            
                        # 2. Check recent uploads (fallback)
                        if not original_video:
                            # Look for uploaded file in current dir
                            videos = glob.glob("*.mp4")
                            if videos:
                                # Pick the largest file (likely the source)
                                original_video = max(videos, key=os.path.getsize)
                            
                        if not original_video:
                            st.warning("ℹ️ Could not auto-detect source video. Please specify path:")
                            original_video = st.text_input("Original video path:", key=f"origpath_{short_name}")
                        else:
                            st.success(f"Source: {os.path.basename(original_video)} | Segment: {int(new_start//60)}:{int(new_start%60):02d} - {int(new_end//60)}:{int(new_end%60):02d}")
                                
                        if original_video and os.path.exists(original_video):
                            # Progress Bar Implementation
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            with st.spinner("Regenerating clip..."):
                                try:
                                    # Imports
                                    # Fix for MoviePy v2.0+
                                    try:
                                        from moviepy import VideoFileClip
                                    except ImportError:
                                        from moviepy.editor import VideoFileClip
                                            
                                    from auto_shorts import smart_reframe, generate_subtitles
                                    # Local burn function since we need specific ffmpeg args
                                    import subprocess

                                    # Paths
                                    temp_cut = os.path.join(short_dir, "temp_cut_regen.mp4")
                                    cropped_video = os.path.join(short_dir, "cropped_regen.mp4")
                                    final_srt = os.path.join(short_dir, "subtitles.srt") # Overwrite old SRT
                                        
                                    # 1. Cut Video (0-25%)
                                    status_text.text("✂️ Cutting video to new timestamp...")
                                    progress_bar.progress(10)
                                    
                                    # Verify Source Duration (Prevent seeking beyond end)
                                    try:
                                        from auto_shorts import get_video_duration
                                        src_dur = get_video_duration(original_video)
                                        if new_start > src_dur:
                                            st.error(f"❌ Error: Start time ({new_start}s) is greater than Source Video duration ({src_dur:.1f}s).")
                                            st.warning("👉 You might be using a CLIP as the source instead of the FULL video. Check the 'Verify Timestamp' section below to switch source.")
                                            st.stop()
                                    except:
                                        pass # Skip check if duration fails (fallback to ffmpeg error)

                                    # Direct FFmpeg Cut (Accurate Seeking - slower but precise)
                                    cmd_cut = [
                                        "ffmpeg", 
                                        "-i", original_video,
                                        "-ss", str(new_start),
                                        "-t", str(new_end - new_start),
                                        "-c:v", "libx264", "-c:a", "aac",
                                        "-y", 
                                        temp_cut
                                    ]
                                    status_text.text(f"✂️ Cutting {new_start}s-{new_end}s (Accurate Mode)...")
                                    subprocess.run(cmd_cut, check=True, capture_output=True)
                                        
                                    progress_bar.progress(25)
                                        
                                    # 2. Smart Crop (25-50%)
                                    # Use setting from UI (Session State)
                                    use_face = st.session_state[adj_key].get('face_tracking', False)
                                    manual_align = st.session_state[adj_key].get('manual_alignment', 0.5)
                                    
                                    # Update metadata to remember preference
                                    if os.path.exists(meta_file):
                                        try:
                                            with open(meta_file, 'r') as f:
                                                m = json.load(f)
                                            m['face_tracking'] = use_face
                                            m['manual_alignment'] = manual_align
                                            with open(meta_file, 'w') as f:
                                                json.dump(m, f, indent=4)
                                        except: pass
                                            
                                    status_text.text(f"📐 Smart Cropping (Face Tracking: {use_face}, Align: {manual_align})...")
                                    smart_reframe(temp_cut, cropped_video, use_face_tracking=use_face, smoothing_seconds=4, manual_alignment=manual_align)
                                    progress_bar.progress(50)
                                        
                                    # 3. Transcribe (50-80%)
                                    # 3. Skip Transcribe/Burn (User Request: Separaate Subtitle Step)
                                    status_text.text("✅ Video updated! (Click 'Create Subtitles' above to add them)")
                                    progress_bar.progress(90)
                                    
                                    # Remove old SRT so "Create Subtitles" button appears
                                    if os.path.exists(final_srt):
                                        os.remove(final_srt)
                                        
                                    # Use cropped video as final output directly
                                    output_final = cropped_video
                                        
                                    # 5. Cleanup & Replace
                                    # Backup old video just in case (Safety)
                                    if os.path.exists(video_path):
                                        backup_path = video_path + ".bak"
                                        if os.path.exists(backup_path):
                                            os.remove(backup_path)
                                        os.rename(video_path, backup_path)
                                        st.caption(f"💾 Backup saved as {os.path.basename(backup_path)}")
                                        
                                    # Rename new to final
                                    os.rename(output_final, video_path)
                                        
                                    # Cleanup temps
                                    if os.path.exists(temp_cut): os.remove(temp_cut)
                                    if os.path.exists(cropped_video): os.remove(cropped_video)
                                        
                                    # Update metadata
                                    if os.path.exists(meta_file):
                                        with open(meta_file, 'r+') as f:
                                            m = json.load(f)
                                            m['start_time'] = new_start
                                            m['end_time'] = new_end
                                            m['duration'] = new_end - new_start
                                            f.seek(0)
                                            json.dump(m, f, indent=4)
                                            f.truncate()
                                        
                                    progress_bar.progress(100)
                                    status_text.text("✅ Done!")
                                    st.success("✅ Clip regenerated & Subtitles updated!")
                                    time.sleep(1)
                                    st.rerun()
                                        
                                except Exception as e:
                                    st.error(f"Error regeneration: {str(e)}")
                                    import traceback
                                    st.code(traceback.format_exc())
                
                # Undo Logic for Safety
                if os.path.exists(video_path + ".bak"):
                    if st.button("↩️ Undo Last Update (Restore Backup)", key=f"undo_{short_name}"):
                         backup_vid = video_path + ".bak"
                         if os.path.exists(video_path):
                             os.remove(video_path)
                         os.rename(backup_vid, video_path)
                         st.success("Restored previous version!")
                         import time
                         time.sleep(1)
                         st.rerun()

                # Subtitle Editor (Smart Vizard Support)
                if srt_file:
                    with st.expander("✏️ Edit Subtitles (Fix Transcription)", expanded=False):
                        st.caption("Edit the plain text below. We will automatically re-apply the Vizard styling (Yellow Highlights)!")
                        
                        # Read SRT file
                        srt_path = srt_file[0]
                        with open(srt_path, 'r', encoding='utf-8') as f:
                            srt_content = f.read()
                        
                        # Parse SRT into simple list of (start, end, active_word)
                        # Vizard lines look like: prev <font...><b>CURRENT</b></font> next
                        import re
                        
                        raw_segments = []
                        current_segment = {}
                        
                        for line in srt_content.split('\n'):
                            line = line.strip()
                            if line.isdigit() and not current_segment:
                                current_segment['index'] = int(line)
                            elif '-->' in line:
                                parts = line.split(' --> ')
                                current_segment['start'] = parts[0]
                                current_segment['end'] = parts[1]
                            elif line and 'index' in current_segment and 'start' in current_segment:
                                # This is the text line. Extract information.
                                text_line = line
                                
                                # Extract correct word using Regex searching for the colored tag
                                # Pattern: <font color="#FFEE00"><b>(.*?)</b></font>
                                match = re.search(r'<font color="#FFEE00"><b>(.*?)</b></font>', text_line)
                                if match:
                                    clean_word = match.group(1)
                                else:
                                    # Fallback: if no tag (maybe plain srt), use whole line
                                    clean_word = text_line
                                
                                current_segment['word'] = clean_word
                                raw_segments.append(current_segment)
                                current_segment = {}
                        
                        # Prepare Paragraph for Editor
                        all_words = [seg['word'] for seg in raw_segments]
                        paragraph_text = " ".join(all_words)
                        
                        # UI
                        st.markdown("**Edit Paragraph:**")
                        edited_paragraph = st.text_area(
                            "Subtitles",
                            value=paragraph_text,
                            height=300,
                            key=f"sub_vizard_{short_name}",
                            label_visibility="collapsed"
                        )
                        
                        if st.button("💾 Save Subtitles", key=f"save_wiz_{short_name}"):
                            # 1. Process New Words
                            new_words = edited_paragraph.strip().split()
                            
                            # 2. Timing Strategy
                            final_segments = []
                            old_count = len(raw_segments)
                            new_count = len(new_words)
                            
                            print(f"Update: {old_count} words -> {new_count} words")
                            
                            if old_count == new_count:
                                # Ideal case: 1-to-1 mapping
                                for i, word in enumerate(new_words):
                                    final_segments.append({
                                        'start': raw_segments[i]['start'],
                                        'end': raw_segments[i]['end'],
                                        'word': word
                                    })
                            else:
                                # Mismatch: Distribute time linearly (Simplest approach)
                                # This handles fixes like "Is it" -> "Isit" or "Its" -> "It is"
                                st.toast(f"Word count changed ({old_count}->{new_count}). Adjusting timings...", icon="⚠️")
                                
                                # Convert timestamp string to seconds helper
                                def ts_to_sec(ts):
                                    h, m, s = ts.replace(',', '.').split(':')
                                    return int(h)*3600 + int(m)*60 + float(s)
                                
                                def sec_to_ts(s):
                                    import datetime
                                    td = datetime.timedelta(seconds=s)
                                    total_seconds = int(td.total_seconds())
                                    hours = total_seconds // 3600
                                    minutes = (total_seconds % 3600) // 60
                                    seconds_ = total_seconds % 60
                                    milliseconds = int(td.microseconds / 1000)
                                    return f"{hours:02d}:{minutes:02d}:{seconds_:02d},{milliseconds:03d}"

                                total_start = ts_to_sec(raw_segments[0]['start'])
                                total_end = ts_to_sec(raw_segments[-1]['end'])
                                duration = total_end - total_start
                                freq = duration / new_count
                                
                                for i, word in enumerate(new_words):
                                    s_time = total_start + (i * freq)
                                    e_time = total_start + ((i + 1) * freq)
                                    # Add tiny gap
                                    e_time = max(s_time + 0.1, e_time - 0.05)
                                    
                                    final_segments.append({
                                        'start': sec_to_ts(s_time),
                                        'end': sec_to_ts(e_time),
                                        'word': word
                                    })

                            # 3. Reconstruct HTML (Prev + Highlight + Next)
                            with open(srt_path, 'w', encoding='utf-8') as f:
                                for i, seg in enumerate(final_segments):
                                    # Context
                                    parts = []
                                    if i > 0:
                                        parts.append(final_segments[i-1]['word'])
                                    
                                    # Highlight Current
                                    parts.append(f'<font color="#FFEE00"><b>{seg["word"]}</b></font>')
                                    
                                    if i < len(final_segments) - 1:
                                        parts.append(final_segments[i+1]['word'])
                                        
                                    text_line = " ".join(parts)
                                    
                                    f.write(f"{i+1}\n")
                                    f.write(f"{seg['start']} --> {seg['end']}\n")
                                    f.write(f"{text_line}\n\n")
                            
                            st.success("✅ Subtitles Updated! (Vizard Style Re-applied)")
                            time.sleep(1)
                            st.rerun()
                                

                    
                    # View-only mode

            
            st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>Made with ❤️ using AI • Whisper Large • OpenCV Face Tracking</p>
</div>
""", unsafe_allow_html=True)
