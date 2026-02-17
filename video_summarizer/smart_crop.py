
import cv2
import numpy as np
import os
from moviepy import VideoFileClip, vfx

def smart_reframe(video_path, output_path, use_face_tracking=True, smoothing_seconds=4, manual_alignment=0.5):
    # --- 1. FACE DETECTION PHASE ---
    x_centers = []
    
    if use_face_tracking:
        print(f"Analyzing {video_path} for faces (HAAR Cascade)...")
        # Load Video for Analysis
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Could not open video.")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Load Haar Cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        frame_count = 0
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break
            
            # Optimization: Process every 5th frame (enough for 30fps)
            if frame_count % 5 == 0:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                if len(faces) > 0:
                    # Pick largest face
                    largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
                    (x, y, w, h_face) = largest_face
                    center_x = x + (w / 2)
                    x_centers.append(center_x)
                else:
                    # Use previous or center
                    if x_centers:
                        x_centers.append(x_centers[-1])
                    else:
                        x_centers.append(width / 2)
            else:
                # Interpolate for skipped frames
                if x_centers:
                    x_centers.append(x_centers[-1])
                else:
                    x_centers.append(width / 2)

            frame_count += 1
            if frame_count % 500 == 0:
                print(f"   -> Scanned {frame_count}/{total_frames} frames...")

        cap.release()
        
        # Smooth Camera Movement
        window_size = int(fps * smoothing_seconds)
        if len(x_centers) > window_size:
            smoothed_centers = np.convolve(x_centers, np.ones(window_size)/window_size, mode='same')
        else:
            smoothed_centers = x_centers if x_centers else [width/2]
            
        print(f"✅ Face tracking complete. Rendering...")

    else:
        print("⚡ Skipping face detection (Fast Mode). Using fixed center crop.")
        # Load clip metadata just for dimensions
        with VideoFileClip(video_path) as clip:
            width, height = clip.size
            fps = clip.fps 
        # Initialize smoothed_centers
        smoothed_centers = [width / 2] * int(fps * clip.duration + 1)

    # --- 2. RENDER PHASE ---
    clip = VideoFileClip(video_path)
    
    # Target 9:16 Ratio
    target_ratio = 9/16
    width, height = clip.size
    new_w = height * target_ratio
    
    # Dynamic crop function
    def get_x1(t):
        if not use_face_tracking:
            # Fixed Crop with Manual Alignment
            # alignment 0.0 = Left, 0.5 = Center, 1.0 = Right
            min_center = new_w / 2
            max_center = width - (new_w / 2)
            center_x = min_center + (manual_alignment * (max_center - min_center))
            return center_x - (new_w / 2)
        
        # Dynamic Crop (Face Tracking)
        frame_idx = int(t * clip.fps)
        if frame_idx >= len(smoothed_centers):
            frame_idx = len(smoothed_centers) - 1
            
        center_x = smoothed_centers[frame_idx]
        x1 = center_x - (new_w / 2)
        
        # Clamp
        if x1 < 0: x1 = 0
        if x1 + new_w > width: x1 = width - new_w
        
        return x1

    # Apply Crop
    # In MoviePy 2.0+, clip.fx is deprecated or changed. Use vfx.crop(clip, ...)
    # In MoviePy 2.0+, it is capitalized. vfx.Crop
    
    # MoviePy 2.0 has changed .fl to .transform
    def crop_filter(get_frame, t):
        frame = get_frame(t)
        # Determine crop x coordinate
        try:
             x1 = int(get_x1(t))
        except:
             x1 = 0
             
        # Ensure x1 is within bounds
        if x1 < 0: x1 = 0
        if x1 + int(new_w) > frame.shape[1]: 
             x1 = frame.shape[1] - int(new_w)
             
        x2 = x1 + int(new_w)
        # Crop the frame array (numpy slicing: y1:y2, x1:x2)
        return frame[:, x1:x2]

    # Use .transform in v2
    # MoviePy will infer the new size from the first frame processed
    final_clip = clip.transform(crop_filter)
    
    # Export
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
    print(f"Done! Smart crop saved: {output_path}")

if __name__ == "__main__":
    # Ensure we use the short clip we made earlier
    input_file = "test_clip_large.mp4"
    if not os.path.exists(input_file):
        print("Test clip not found. Please run 'create_preview.py' or 'test_large_model.py' first.")
    else:
        smart_reframe(input_file, "smart_crop_final.mp4")
