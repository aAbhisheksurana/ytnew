# AI AGENT SETUP INSTRUCTIONS
## Automated Setup for GPU System (64GB RAM + 8GB NVIDIA GPU)

---

## 🎯 OBJECTIVE
Set up the AI Shorts Generator project on a new GPU-enabled system with all dependencies installed and verified.

---

## 📋 PREREQUISITES CHECK

Before starting, verify the following:

### 1. Check NVIDIA GPU
```bash
nvidia-smi
```
**Expected Output:** Should show GPU information and CUDA version (11.x or 12.x)

### 2. Check Python Version
```bash
python3 --version
```
**Expected Output:** Python 3.8 or higher

### 3. Check System Resources
```bash
free -h  # Should show ~64 GB RAM
```

---

## 🚀 AUTOMATED SETUP STEPS

Execute these commands in sequence. Each step must complete successfully before proceeding to the next.

### STEP 1: Navigate to Project Directory
```bash
cd /path/to/ai-shorts-generator
# Or if cloned from git:
# git clone <repo-url>
# cd ai-shorts-generator
```

### STEP 2: Create Virtual Environment
```bash
python3 -m venv venv
```
**Verification:** Check if `venv` folder exists:
```bash
ls -la venv
```

### STEP 3: Activate Virtual Environment
```bash
source venv/bin/activate
```
**Verification:** Prompt should show `(venv)` prefix

### STEP 4: Upgrade pip
```bash
pip install --upgrade pip
```

### STEP 5: Detect CUDA Version
```bash
export CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}' | cut -d. -f1)
echo "Detected CUDA version: $CUDA_VERSION"
```

### STEP 6: Install PyTorch with GPU Support

**For CUDA 11.x:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**For CUDA 12.x:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Auto-detect and install:**
```bash
if [[ "$CUDA_VERSION" == "12" ]]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
fi
```

**Verification:**
```bash
python -c "import torch; print('PyTorch installed:', torch.__version__)"
```

### STEP 7: Verify GPU Detection
```bash
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Not detected')"
```
**Expected Output:**
```
CUDA available: True
GPU: NVIDIA GeForce RTX 3080 (or similar)
```

**CRITICAL:** If output shows `False`, STOP and troubleshoot before continuing.

### STEP 8: Install Other Dependencies
```bash
pip install streamlit
pip install openai-whisper
pip install moviepy
pip install opencv-python
pip install yt-dlp
pip install numpy
```

**Or use requirements file:**
```bash
pip install streamlit openai-whisper moviepy opencv-python yt-dlp numpy
```

### STEP 9: Verify All Installations
```bash
python << 'PYEOF'
import sys
packages = ['streamlit', 'whisper', 'moviepy', 'cv2', 'yt_dlp', 'numpy', 'torch']
missing = []
for pkg in packages:
    try:
        if pkg == 'cv2':
            import cv2
        elif pkg == 'yt_dlp':
            import yt_dlp
        else:
            __import__(pkg)
        print(f"✅ {pkg}: installed")
    except ImportError:
        print(f"❌ {pkg}: MISSING")
        missing.append(pkg)

if missing:
    print(f"\n⚠️ Missing packages: {', '.join(missing)}")
    sys.exit(1)
else:
    print("\n✅ All packages installed successfully!")
PYEOF
```

### STEP 10: Enable GPU in Code

Edit `auto_shorts.py` to use GPU:

```bash
# Backup original
cp auto_shorts.py auto_shorts.py.backup

# Update line 39-43 (generate_subtitles function)
python << 'PYEOF'
import re

# Read file
with open('auto_shorts.py', 'r') as f:
    content = f.read()

# Find and replace the whisper loading line
old_pattern = r'model = whisper\.load_model\("large"\)'
new_code = '''import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🚀 Using device: {device}")
        model = whisper.load_model("large", device=device)'''

# Replace
content = re.sub(old_pattern, new_code, content)

# Write back
with open('auto_shorts.py', 'w') as f:
    f.write(content)

print("✅ Updated auto_shorts.py to use GPU")
PYEOF
```

**Manual verification:**
```bash
grep -n "device.*cuda" auto_shorts.py
```
Should show the updated line.

### STEP 11: Test GPU Setup
```bash
python << 'PYEOF'
import torch
import whisper

print("=" * 50)
print("GPU SETUP TEST")
print("=" * 50)

# Check CUDA
cuda_available = torch.cuda.is_available()
print(f"CUDA Available: {cuda_available}")

if cuda_available:
    print(f"GPU Name: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    # Test Whisper on GPU
    print("\nTesting Whisper model loading on GPU...")
    device = "cuda"
    try:
        model = whisper.load_model("base", device=device)
        print(f"✅ Whisper loaded successfully on {device}")
        del model
        torch.cuda.empty_cache()
    except Exception as e:
        print(f"❌ Whisper loading failed: {e}")
else:
    print("❌ CUDA not available - will use CPU (slow)")

print("=" * 50)
PYEOF
```

**Expected Output:**
```
CUDA Available: True
GPU Name: NVIDIA GeForce RTX 3080
GPU Memory: 8.00 GB
Testing Whisper model loading on GPU...
✅ Whisper loaded successfully on cuda
```

### STEP 12: Run Application
```bash
streamlit run app.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

---

## ✅ VERIFICATION CHECKLIST

After setup, verify the following:

- [ ] Virtual environment created and activated
- [ ] PyTorch installed with GPU support
- [ ] `torch.cuda.is_available()` returns `True`
- [ ] All dependencies installed (streamlit, whisper, moviepy, etc.)
- [ ] `auto_shorts.py` updated to use GPU
- [ ] Streamlit app starts without errors
- [ ] Can access app at http://localhost:8501

---

## 🔧 TROUBLESHOOTING

### Issue: GPU not detected (torch.cuda.is_available() = False)

**Solution 1:** Check NVIDIA drivers
```bash
nvidia-smi
```
If this fails, reinstall NVIDIA drivers.

**Solution 2:** Reinstall PyTorch with correct CUDA version
```bash
pip uninstall torch torchvision torchaudio
# Check CUDA version from nvidia-smi, then install matching PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Solution 3:** Check CUDA toolkit
```bash
nvcc --version
```
If not found, install:
```bash
sudo apt install nvidia-cuda-toolkit
```

### Issue: Out of memory during processing

**Solution:** Reduce batch size or use half precision

Edit `auto_shorts.py`, add to generate_subtitles function:
```python
result = model.transcribe(video_path, language="hi", fp16=True)  # Enable half precision
```

### Issue: Module not found errors

**Solution:** Ensure virtual environment is activated
```bash
which python  # Should show path to venv/bin/python
source venv/bin/activate
pip list  # Verify packages
```

---

## 📊 EXPECTED PERFORMANCE

After successful GPU setup:

| Task | CPU Time | GPU Time | Speedup |
|------|----------|----------|---------|
| Whisper (60s video) | 2 min | 10 sec | 12x faster |
| Face tracking (60s) | 1.5 min | 45 sec | 2x faster |
| Video encoding (60s) | 30 sec | 15 sec | 2x faster |
| **Total per short** | 4-5 min | **1 min** | **5x faster** |
| **15 shorts** | 70 min | **15 min** | **4.7x faster** |

---

## 🎯 FINAL VALIDATION TEST

Run this complete test:

```bash
python << 'PYEOF'
import torch
import whisper
import cv2
import streamlit
import numpy as np

print("\n🔍 FINAL VALIDATION TEST")
print("=" * 60)

# 1. GPU Check
assert torch.cuda.is_available(), "❌ GPU not available"
print(f"✅ GPU: {torch.cuda.get_device_name(0)}")

# 2. Whisper on GPU
device = "cuda"
model = whisper.load_model("base", device=device)
print(f"✅ Whisper model loaded on GPU")
del model
torch.cuda.empty_cache()

# 3. OpenCV
assert cv2.__version__, "❌ OpenCV not found"
print(f"✅ OpenCV: {cv2.__version__}")

# 4. Streamlit
print(f"✅ Streamlit installed")

print("=" * 60)
print("✅ ALL TESTS PASSED - SETUP COMPLETE!")
print("\n🚀 Ready to generate shorts 10x faster!")
print("\nNext step: Run 'streamlit run app.py'")
PYEOF
```

**Expected Output:**
```
✅ GPU: NVIDIA GeForce RTX 3080
✅ Whisper model loaded on GPU
✅ OpenCV: 4.x.x
✅ Streamlit installed
✅ ALL TESTS PASSED - SETUP COMPLETE!
🚀 Ready to generate shorts 10x faster!
```

---

## 📝 SUMMARY OF COMMANDS (Quick Reference)

```bash
# Complete setup in one go
cd ai-shorts-generator
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install PyTorch GPU (auto-detect CUDA)
CUDA_VER=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}' | cut -d. -f1)
if [[ "$CUDA_VER" == "12" ]]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
fi

# Install other dependencies
pip install streamlit openai-whisper moviepy opencv-python yt-dlp numpy

# Verify GPU
python -c "import torch; print(torch.cuda.is_available())"

# Run app
streamlit run app.py
```

---

## 🤖 FOR AI AGENTS

If you are an AI agent executing this setup:

1. **Execute each STEP sequentially** in the order listed
2. **Verify** each step output matches expected output
3. **STOP immediately** if any verification fails and report the error
4. **Run Final Validation Test** before declaring success
5. **Report status** after each major step (GPU detection, package installation, etc.)

**Success Criteria:**
- All packages installed
- GPU detected and accessible
- Final validation test passes
- Streamlit app starts successfully

---

## 📞 SUPPORT

If setup fails:
1. Check `GPU_SETUP_GUIDE.md` for detailed troubleshooting
2. Verify NVIDIA drivers: `nvidia-smi`
3. Check Python version: `python3 --version` (must be 3.8+)
4. Ensure sufficient disk space: `df -h` (need ~10 GB)

---

**End of Setup Instructions**
**Version: 1.0**
**Last Updated: 2024**
