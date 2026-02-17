#!/bin/bash
# GPU System Setup Script
# Run this on the new GPU system (64GB RAM + 8GB GPU)

echo "🚀 AI Shorts Generator - GPU Setup"
echo "=================================="
echo ""

# Check if NVIDIA GPU is available
echo "📊 Checking GPU..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ ERROR: nvidia-smi not found!"
    echo "   Install NVIDIA drivers first."
    exit 1
fi

nvidia-smi
echo ""

# Get CUDA version
CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
echo "✅ CUDA Version detected: $CUDA_VERSION"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install PyTorch with GPU support
echo ""
echo "🔥 Installing PyTorch with GPU support..."
echo "   (This may take 5-10 minutes)"

if [[ "$CUDA_VERSION" == 12.* ]]; then
    echo "   Using CUDA 12.1 version..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    echo "   Using CUDA 11.8 version..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
fi

# Verify GPU
echo ""
echo "🔍 Verifying GPU detection..."
python -c "import torch; print('GPU Available:', torch.cuda.is_available()); print('GPU Name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"

if ! python -c "import torch; exit(0 if torch.cuda.is_available() else 1)"; then
    echo "❌ ERROR: GPU not detected by PyTorch!"
    echo "   Check CUDA installation."
    exit 1
fi

echo "✅ GPU detected successfully!"
echo ""

# Install other dependencies
echo "📦 Installing other dependencies..."
pip install streamlit openai-whisper moviepy opencv-python yt-dlp numpy

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit auto_shorts.py line 39:"
echo "      model = whisper.load_model('large', device='cuda')"
echo ""
echo "   2. Run the app:"
echo "      source venv/bin/activate"
echo "      streamlit run app.py"
echo ""
echo "🚀 Expected speed: 10x faster than CPU!"
