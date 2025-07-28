#!/bin/bash
# Setup script for RepoWhisperer
# Installs dependencies and prepares the environment for GitHub Codespaces

set -e

echo "🚀 Setting up RepoWhisperer..."

# Check if we're in Codespaces
if [ -n "$CODESPACES" ]; then
    echo "📱 Detected GitHub Codespaces environment"
    CODESPACE_ENV=true
else
    echo "💻 Running in local environment"
    CODESPACE_ENV=false
fi

# Check Python version
echo "🐍 Checking Python version..."

# Use Python for version comparison
python3 -c "
import sys
version_info = sys.version_info
version = version_info.major + version_info.minor / 10.0
print(f'Detected Python {version_info.major}.{version_info.minor}.{version_info.micro}')
if version < 3.8:
    print('❌ Python 3.8 or higher is required')
    sys.exit(1)
else:
    print('✅ Python version is compatible')
"

# Install system dependencies if needed
echo "📦 Installing system dependencies..."

# For Codespaces/Ubuntu
if command -v apt-get &> /dev/null; then
    echo "  Installing apt packages..."
    sudo apt-get update -qq
    sudo apt-get install -y git-lfs build-essential curl wget
    
    # Install additional dependencies for better model performance
    if [ "$CODESPACE_ENV" = true ]; then
        sudo apt-get install -y libaio-dev
    fi
fi

# For macOS
if command -v brew &> /dev/null; then
    echo "  Installing Homebrew packages..."
    brew install git-lfs
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🏗️  Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install wheel
echo "📈 Upgrading pip and essential packages..."
pip install --upgrade pip setuptools wheel

# Install PyTorch first with CUDA support if available
echo "🔥 Installing PyTorch..."
if command -v nvidia-smi &> /dev/null; then
    echo "  GPU detected, installing PyTorch with CUDA support..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
else
    echo "  No GPU detected, installing CPU-only PyTorch..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install requirements
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Try to install GPU/quantization libraries if CUDA is available
if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    echo "🎮 GPU detected, installing quantization libraries..."
    pip install -r requirements-gpu.txt || echo "⚠️  Some GPU libraries failed to install, but basic functionality will work"
else
    echo "💻 No GPU detected, skipping quantization libraries (will use CPU mode)"
fi

# Download Git LFS files if any
if command -v git-lfs &> /dev/null; then
    echo "📥 Pulling Git LFS files..."
    git lfs pull || echo "  No LFS files to pull"
fi

# Test the installation
echo "🧪 Testing installation..."
if python test_components.py; then
    echo "✅ Component tests passed"
else
    echo "⚠️  Some component tests failed, but basic functionality should work"
fi

# Check GPU availability and memory
echo "🎮 Checking system capabilities..."
python3 -c "
import torch
import psutil
import sys

print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')

# System memory
memory = psutil.virtual_memory()
print(f'System RAM: {memory.total / 1e9:.1f} GB (Available: {memory.available / 1e9:.1f} GB)')

if torch.cuda.is_available():
    print(f'CUDA devices: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'  Device {i}: {torch.cuda.get_device_name(i)}')
        props = torch.cuda.get_device_properties(i)
        print(f'    VRAM: {props.total_memory / 1e9:.1f} GB')
        
    # Recommend settings based on VRAM
    max_vram = max(torch.cuda.get_device_properties(i).total_memory for i in range(torch.cuda.device_count()))
    if max_vram < 8e9:  # Less than 8GB
        print('💡 Recommendation: Use 4-bit quantization for best performance')
    elif max_vram < 16e9:  # Less than 16GB  
        print('💡 Recommendation: Use 8-bit quantization for good balance')
    else:
        print('💡 Recommendation: You can use full precision or light quantization')
else:
    print('Will use CPU for inference (slower but functional)')
    if memory.total < 16e9:  # Less than 16GB RAM
        print('💡 Recommendation: Use 4-bit quantization and reduce max_tokens')
    else:
        print('💡 Recommendation: Use 4-bit quantization for CPU inference')
"

# Validate core files exist
echo "📋 Validating installation..."
missing_files=()
required_files=("generate_readme.py" "config.yaml" "model/inference.py" "parser/file_parser.py" "parser/prompt_builder.py" "utils/markdown_writer.py")

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo "✅ All required files present"
else
    echo "❌ Missing files: ${missing_files[*]}"
    exit 1
fi

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "🎯 Quick Start:"
echo "   source venv/bin/activate                              # Activate the environment"
echo "   python generate_readme.py --repo . --dry-run         # Test on current directory"
echo "   python generate_readme.py --repo ./my_project        # Generate README"
echo ""
echo "📖 More Examples:"
echo "   python generate_readme.py --repo /path/to/project --output custom_readme.md"
echo "   python generate_readme.py --repo . --verbose         # With detailed output"
echo ""
echo "⚙️  Configuration:"
echo "   Edit config.yaml to customize model settings and parsing options"
echo ""
echo "🔧 Troubleshooting:"
echo "   - If you get CUDA out of memory errors, edit config.yaml:"
echo "     model:"
echo "       device: 'cpu'                    # Force CPU usage"
echo "       quantization: '4bit'             # Use 4-bit quantization"
echo "       max_tokens: 2048                 # Reduce token limit"
echo ""
echo "   - For slow generation, try:"
echo "     - Using GPU if available"
echo "     - Reducing max_chunk_size in config.yaml"
echo "     - Using smaller model variants"
echo ""
echo "   - If model downloads fail:"
echo "     huggingface-cli download deepseek-ai/deepseek-coder-33b-instruct"
echo ""
echo "📚 Documentation: Check README.md for detailed usage instructions"
echo ""

# Create a simple activation script for convenience
cat > activate_env.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
echo "✅ RepoWhisperer environment activated!"
echo "💡 Run: python generate_readme.py --repo . --dry-run"
EOF
chmod +x activate_env.sh

echo "💡 Tip: Run './activate_env.sh' to quickly activate the environment"
