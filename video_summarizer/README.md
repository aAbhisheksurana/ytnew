# Offline AI Video Editor

This tool automatically:
1.  **Transcribes** your video (supports Hindi/English).
2.  Generates a **Subtitle File (.srt)**.
3.  Creates a **Vertical (9:16) Short** from your landscape video.

## Setup & Running

**Step 1: Activate Environment**
```bash
source venv/bin/activate
```

**Step 2: Add Your Video**
Upload your video file (e.g., `my_video.mp4`) into this folder.

**Step 3: Run the Script**
```bash
python process_video.py my_video.mp4
```

## Output
Two files will be created in the same folder:
1.  `my_video.srt` (Subtitles)
2.  `my_video_short.mp4` (Vertical Video)

## Notes
- First run will download the Whisper AI model (approx 200MB - 1GB depending on model size).
- Processing speed depends on your CPU/GPU.
- To improve Hindi accuracy, edit `process_video.py` and change `model_size="base"` to `"medium"`.
