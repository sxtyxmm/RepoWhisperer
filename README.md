# RepoWhisperer 🤖📝

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg) ![AI](https://img.shields.io/badge/AI-DeepSeek--Coder-orange.svg)

RepoWhisperer is an AI-powered agent that scans your entire project directory, interprets your codebase, configuration, and structure, and automatically generates a clean, comprehensive README.md. Think of it as your personal documentation assistant that whispers the story of your repository into well-written markdown.

## ✨ Features

- **🔍 Deep Code Analysis**: Parses source code line-by-line using AST for Python and smart regex patterns for other languages
- **🧠 AI-Powered Documentation**: Uses DeepSeek-Coder 33B to understand your project's architecture and generate human-readable documentation  
- **🌍 Multi-Language Support**: Supports Python, JavaScript, TypeScript, Java, C/C++, Go, Rust, and more
- **⚡ Intelligent Chunking**: Handles large codebases by intelligently splitting analysis into manageable chunks
- **🎯 Context-Aware**: Understands project structure, dependencies, and design patterns
- **🔧 Highly Configurable**: Customizable parsing rules, model settings, and output formatting
- **💾 Memory Efficient**: Uses 4-bit quantization to run large models in resource-constrained environments

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Git LFS (for model downloads)
- 8GB+ RAM (16GB+ recommended for optimal performance)
- Optional: CUDA-compatible GPU for faster inference

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/sxtyxmm/RepoWhisperer.git
cd RepoWhisperer
```

2. **Run the setup script:**
```bash
./setup.sh
```

3. **Activate the environment:**
```bash
source venv/bin/activate
```

### Basic Usage

Generate a README for any project:

```bash
# Analyze the current directory
python generate_readme.py --repo .

# Analyze a specific project
python generate_readme.py --repo /path/to/your/project

# Custom output location
python generate_readme.py --repo ./my_project --output ./custom_readme.md

# Dry run (analyze without generating)
python generate_readme.py --repo . --dry-run --verbose
```

## 🏗️ Architecture

RepoWhisperer follows a modular architecture designed for scalability and maintainability:

```
RepoWhisperer/
├── generate_readme.py          # 🎯 Main CLI entry point
├── config.yaml                 # ⚙️ Configuration settings
├── model/
│   └── inference.py            # 🧠 DeepSeek-Coder model interface
├── parser/
│   ├── file_parser.py          # 📄 AST-based code parsing
│   └── prompt_builder.py       # 💬 LLM prompt construction
├── utils/
│   └── markdown_writer.py      # 📝 README generation & formatting
├── requirements.txt            # 📦 Python dependencies
├── setup.sh                    # 🔧 Environment setup script
└── test_components.py          # 🧪 Component testing
```

### Core Components

#### 1. **File Parser** (`parser/file_parser.py`)
- **Purpose**: Extracts structural information from source code files
- **Features**: 
  - AST-based parsing for Python with full syntax analysis
  - Regex-based parsing for JavaScript, TypeScript, Java, C/C++
  - Configurable file filtering and exclusion rules
  - Multi-language detection and handling
- **Key Classes**: `FileParser`, `CodeStructure`, `ClassInfo`, `FunctionInfo`

#### 2. **Prompt Builder** (`parser/prompt_builder.py`)
- **Purpose**: Constructs intelligent prompts for the LLM based on code analysis
- **Features**:
  - Context-aware prompt generation with code snippets
  - Architecture analysis prompts for design pattern detection
  - Usage example prompts for practical documentation
  - Intelligent chunking for large codebases
- **Key Classes**: `PromptBuilder`

#### 3. **Model Inference** (`model/inference.py`)
- **Purpose**: Manages DeepSeek-Coder model loading and inference
- **Features**:
  - Automatic GPU/CPU detection and optimization
  - 4-bit/8-bit quantization for memory efficiency
  - Streaming generation with memory management
  - Graceful fallback to CPU when GPU unavailable
- **Key Classes**: `ModelInference`, `LocalInferenceWrapper`

#### 4. **Markdown Writer** (`utils/markdown_writer.py`)
- **Purpose**: Formats and validates generated README content
- **Features**:
  - Professional markdown formatting with proper structure
  - LLM response cleaning and post-processing
  - Multi-response merging for comprehensive documentation
  - Markdown validation and issue detection
- **Key Classes**: `MarkdownWriter`

## 📋 File Structure

| File/Directory | Purpose | Key Features |
|---|---|---|
| `generate_readme.py` | Main CLI application | Orchestrates the entire pipeline, handles arguments |
| `config.yaml` | Configuration management | Model settings, parsing rules, output formatting |
| `parser/file_parser.py` | Code structure extraction | AST parsing, multi-language support, file filtering |
| `parser/prompt_builder.py` | LLM prompt generation | Context-aware prompts, intelligent chunking |
| `model/inference.py` | AI model interface | DeepSeek-Coder integration, memory optimization |
| `utils/markdown_writer.py` | README formatting | Markdown generation, validation, post-processing |
| `test_components.py` | Testing framework | Component testing, integration verification |
| `setup.sh` | Environment setup | Dependency installation, GPU detection |

## ⚙️ Configuration

RepoWhisperer uses `config.yaml` for comprehensive configuration:

### Model Settings
```yaml
model:
  name: "deepseek-ai/deepseek-coder-33b-instruct"
  device: "auto"                 # auto, cpu, cuda:0, etc.
  quantization: "4bit"           # none, 4bit, 8bit
  max_tokens: 4096
  temperature: 0.1               # Lower = more focused
  top_p: 0.95
```

### Parsing Configuration
```yaml
parsing:
  exclude_dirs:
    - ".git"
    - "__pycache__"
    - "node_modules"
    - "venv"
  
  exclude_files:
    - "*.pyc"
    - "*.log"
    - "*.min.js"
  
  supported_extensions:
    - ".py"
    - ".js"
    - ".ts"
    - ".java"
    - ".cpp"
    # ... and more
```

### Prompt Tuning
```yaml
prompts:
  max_chunk_size: 3000          # Maximum tokens per chunk
  context_lines: 5              # Lines of context around functions
```

## 🎯 Usage Examples

### Example 1: Basic Python Project
```bash
python generate_readme.py --repo ./my_flask_app
```

**Generated Output**: Comprehensive README with Flask app architecture, API endpoints, database models, and deployment instructions.

### Example 2: JavaScript/Node.js Project
```bash
python generate_readme.py --repo ./my_node_api --config custom_config.yaml
```

**Generated Output**: README with Express.js architecture, middleware analysis, route documentation, and npm scripts.

### Example 3: Multi-Language Project
```bash
python generate_readme.py --repo ./fullstack_project --verbose
```

**Generated Output**: Unified documentation covering both frontend (React/TypeScript) and backend (Python/Django) components.

## 🔧 Advanced Usage

### Custom Configuration
Create a custom configuration file:

```yaml
# custom_config.yaml
model:
  quantization: "8bit"          # Use 8-bit for better quality
  temperature: 0.05             # More deterministic output

parsing:
  exclude_dirs:
    - "dist"
    - "build"
    - ".next"
  
  supported_extensions:
    - ".py"
    - ".ts"
    - ".tsx"
    - ".md"
```

```bash
python generate_readme.py --repo ./my_project --config custom_config.yaml
```

### Batch Processing
Process multiple projects:

```bash
#!/bin/bash
for project in ./projects/*/; do
    echo "Processing $project"
    python generate_readme.py --repo "$project"
done
```

### Integration with CI/CD
Add to your GitHub Actions workflow:

```yaml
# .github/workflows/auto-readme.yml
name: Auto-generate README
on:
  push:
    branches: [main]

jobs:
  generate-readme:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup RepoWhisperer
        run: |
          git clone https://github.com/sxtyxmm/RepoWhisperer.git
          cd RepoWhisperer && ./setup.sh
      - name: Generate README
        run: |
          cd RepoWhisperer
          source venv/bin/activate
          python generate_readme.py --repo ../ --output ../README_generated.md
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Test all components
python test_components.py

# Test with verbose output
python test_components.py --verbose

# Test parsing only (faster)
python generate_readme.py --repo . --dry-run
```

## 🚨 Troubleshooting

### Common Issues

#### 1. **Out of Memory Errors**
```bash
# Solution: Use smaller quantization
# Edit config.yaml:
model:
  quantization: "4bit"  # or "8bit"
  max_tokens: 2048      # Reduce max tokens
```

#### 2. **Model Download Fails**
```bash
# Solution: Manual download
huggingface-cli download deepseek-ai/deepseek-coder-33b-instruct
```

#### 3. **CUDA Out of Memory**
```bash
# Solution: Force CPU usage
# Edit config.yaml:
model:
  device: "cpu"
```

#### 4. **Slow Generation**
```bash
# Solutions:
# 1. Use GPU if available
# 2. Reduce max_tokens in config.yaml
# 3. Use smaller model variant
```

### Performance Optimization

1. **GPU Usage**: Ensure CUDA is properly installed for GPU acceleration
2. **Memory Management**: Use 4-bit quantization for large models
3. **Chunk Size**: Adjust `max_chunk_size` based on available memory
4. **File Filtering**: Exclude unnecessary files/directories

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `python test_components.py`
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/RepoWhisperer.git
cd RepoWhisperer

# Setup development environment
./setup.sh

# Install development dependencies
pip install pytest black flake8 mypy

# Run linting
black . && flake8 . && mypy .

# Run tests
python test_components.py
```

### Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings for all public functions/classes
- Write tests for new functionality

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **DeepSeek AI** for the incredible DeepSeek-Coder model
- **Hugging Face** for the transformers library and model hosting
- **GitHub Codespaces** for providing an excellent development environment
- The open-source community for inspiration and support

## 📞 Support

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and community support
- **Documentation**: Check the wiki for detailed guides

---

*This README was generated by RepoWhisperer 🤖 - Experience the power of AI-driven documentation!*
