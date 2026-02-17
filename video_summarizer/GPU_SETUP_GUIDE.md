# 🚀 GPU Setup Guide for High-Performance System

**Target System Specs:**
- RAM: 64 GB
- GPU: 8 GB NVIDIA
- Expected Speed: **10x faster!**

---

## 📋 Step-by-Step Setup

### 1️⃣ Copy Project to New System

```bash
# Copy entire folder
cp -r video_summarizer /path/on/new/system/
cd /path/on/new/system/video_summarizer
```

---

### 2️⃣ Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3️⃣ Install GPU-Enabled PyTorch

**IMPORTANT:** Install GPU version, not CPU!

```bash
# For CUDA 11.8 (most common)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1 (newer GPUs)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Check CUDA version:**
```bash
nvidia-smi  # Shows CUDA version at top
```

---

### 4️⃣ Install Other Dependencies

```bash
pip install streamlit
pip install openai-whisper
pip install moviepy
pip install opencv-python
pip install yt-dlp
```

---

### 5️⃣ Verify GPU Detection

```bash
python -c "import torch; print('GPU Available:', torch.cuda.is_available())"
python -c "import torch; print('GPU Name:', torch.cuda.get_device_name(0))"
```

**Should show:**
```
GPU Available: True
GPU Name: NVIDIA GeForce RTX 3080 (or similar)
```

---

### 6️⃣ Enable GPU in Code

**Edit:** `auto_shorts.py` (line ~42)

**Change this:**
```python
model = whisper.load_model("large")
```

**To this:**
```python
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("large", device=device)
print(f"🚀 Using device: {device}")
```

---

### 7️⃣ (Optional) GPU Video Encoding

For even faster video processing:

```bash
# Install NVIDIA codec SDK
sudo apt update
sudo apt install ffmpeg nvidia-cuda-toolkit
```

**Edit:** `auto_shorts.py` burn_subtitles function

Add GPU encoding flag:
```python
cmd = [
    "ffmpeg", "-hwaccel", "cuda",  # <-- Add this
    "-i", video_path,
    # ... rest of command
]
```

---

## 🎯 Expected Performance Improvements

| Task | Current System | New System (CPU) | New System (GPU) |
|------|----------------|------------------|------------------|
| **Whisper (60s video)** | 2 min | 1 min | **10 sec** 🚀 |
| **Face Tracking** | 1.5 min | 45 sec | 45 sec |
| **Video Encoding** | 30 sec | 20 sec | **15 sec** |
| **Per Short (total)** | 4-5 min | 2-3 min | **1 min** ✅ |
| **15 Shorts** | 70 min | 35 min | **15 min!!** 🔥 |

**Speed Increase: 87% faster!**

---

## ✅ Test GPU Setup

Run this test script:

```bash
python test_large_model.py
```

It should show GPU being used.

---

## 🐛 Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA driver
nvidia-smi

# Reinstall CUDA toolkit
sudo apt install nvidia-cuda-toolkit

# Reinstall PyTorch with correct CUDA version
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Out of Memory Error

If GPU runs out of memory (8GB might be tight for very long videos):

**Edit:** `auto_shorts.py`

```python
# Add memory optimization
import torch
torch.cuda.empty_cache()  # Add after each short generation
```

Or reduce batch size in Whisper:
```python
result = model.transcribe(video_path, language="hi", fp16=True)  # Use half precision
```

---

## 🚀 Run the App

```bash
source venv/bin/activate
streamlit run app.py
```

**Open browser:** http://localhost:8501

---

## 📊 Monitor GPU Usage While Processing

```bash
# In a separate terminal
watch -n 1 nvidia-smi
```

You should see:
- GPU usage: 80-95%
- Memory usage: 5-7 GB
- Temperature: Should stay under 80°C

---

## 🎯 Final Checklist

- [ ] PyTorch GPU installed
- [ ] `torch.cuda.is_available()` returns True
- [ ] Whisper using GPU (check with `nvidia-smi` during processing)
- [ ] Processing time reduced by 80%+
- [ ] No out-of-memory errors

---

## 💡 Tips for Best Performance

1. **Close unnecessary apps** to free GPU memory
2. **Monitor temperature** - keep GPU cool
3. **Use face tracking = OFF** for maximum speed (30% faster)
4. **Process in batches** - Generate 5 shorts at a time instead of 15

---

**Enjoy your 10x speed boost! 🚀**
