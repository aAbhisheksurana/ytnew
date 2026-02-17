"""
Clip Editor Component
Allows users to fine-tune clip timing after generation
"""
import streamlit as st
import os
from moviepy import VideoFileClip

def show_clip_editor(short_dir):
    """
    Display UI to edit clip start/end times
    
    Args:
        short_dir: Path to short directory (e.g., generated_shorts/short_12_34)
    """
    st.markdown("### ✂️ Clip Editor")
    
    # Extract current timing from folder name
    folder_name = os.path.basename(short_dir)
    time_str = folder_name.replace("short_", "")
    parts = time_str.split("_")
    
    if len(parts) >= 2:
        current_start_min = int(parts[0])
        current_start_sec = int(parts[1])
        current_start = current_start_min * 60 + current_start_sec
    else:
        st.error("Cannot parse folder name!")
        return
    
    # Assume 60-second clip
    current_end = current_start + 60
    
    st.info(f"📍 Current Clip: {current_start_min}:{current_start_sec:02d} to {current_end//60}:{current_end%60:02d}")
    
    # Editor controls
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Start Time")
        new_start_min = st.number_input("Minutes", min_value=0, value=current_start_min, key=f"start_min_{folder_name}")
        new_start_sec = st.number_input("Seconds", min_value=0, max_value=59, value=current_start_sec, key=f"start_sec_{folder_name}")
        new_start = new_start_min * 60 + new_start_sec
    
    with col2:
        st.markdown("#### Clip Duration")
        duration = st.slider("Duration (seconds)", min_value=10, max_value=120, value=60, step=5, key=f"dur_{folder_name}")
        new_end = new_start + duration
        end_min = new_end // 60
        end_sec = new_end % 60
        st.caption(f"End: {end_min}:{end_sec:02d}")
    
    # Quick adjust buttons
    st.markdown("#### Quick Adjustments")
    col_adj1, col_adj2, col_adj3, col_adj4 = st.columns(4)
    
    with col_adj1:
        if st.button("⏪ -5 sec", key=f"adj1_{folder_name}"):
            return (max(0, new_start - 5), new_end - 5)
    
    with col_adj2:
        if st.button("⏩ +5 sec", key=f"adj2_{folder_name}"):
            return (new_start + 5, new_end + 5)
    
    with col_adj3:
        if st.button("🔼 Extend +10s", key=f"adj3_{folder_name}"):
            return (new_start, new_end + 10)
    
    with col_adj4:
        if st.button("🔽 Trim -10s", key=f"adj4_{folder_name}"):
            return (new_start, max(new_start + 10, new_end - 10))
    
    # Apply changes button
    if st.button("✅ Apply New Timing", key=f"apply_{folder_name}", type="primary"):
        return (new_start, new_end)
    
    return None


def regenerate_clip(original_video, short_dir, new_start, new_end):
    """
    Regenerate clip with new timing
    
    Args:
        original_video: Path to original full video
        short_dir: Path to short directory
        new_start: New start time (seconds)
        new_end: New end time (seconds)
    """
    try:
        st.info(f"🔄 Regenerating clip from {new_start//60}:{new_start%60:02d} to {new_end//60}:{new_end%60:02d}...")
        
        # Create progress bar
        progress = st.progress(0)
        
        # Load original video
        progress.progress(10)
        with VideoFileClip(original_video) as video:
            # Check bounds
            if new_end > video.duration:
                st.error(f"❌ End time ({new_end}s) exceeds video duration ({video.duration}s)!")
                return False
            
            progress.progress(30)
            
            # Extract new clip
            new_clip = video.subclipped(new_start, new_end)
            
            progress.progress(50)
            
            # Save to temporary file
            temp_path = os.path.join(short_dir, "temp_regen.mp4")
            new_clip.write_videofile(temp_path, codec="libx264", audio_codec="aac", logger=None)
            
            progress.progress(80)
            
            # Replace final_short.mp4
            final_path = os.path.join(short_dir, "final_short.mp4")
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(temp_path, final_path)
            
            progress.progress(100)
        
        st.success("✅ Clip regenerated successfully!")
        return True
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return False
