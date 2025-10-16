# Detailed Installation Guide

## 📦 Requirements

### Python Version
- Python 3.8 or higher
- Recommended: Python 3.9 or 3.10

### Build Tools

To install PyTSK3, you need compiler and build tools:

#### Windows
```bash
# Install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/downloads/
# Select "Desktop development with C++"

# Or install pre-built wheel:
# Download from: https://github.com/py4n6/pytsk/releases
pip install pytsk3-xxxx-win_amd64.whl
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y python3-dev build-essential git
sudo apt-get install -y autoconf automake libtool pkg-config
```

#### Linux (CentOS/RHEL)
```bash
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel
```

#### macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install pkg-config autoconf automake libtool
```

## 🚀 Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/ntfs-file-recovery.git
cd ntfs-file-recovery
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Step 4: Install Package

```bash
# Development mode (recommended for development)
pip install -e .

# Or regular installation
pip install .
```

## 🔧 Troubleshooting Installation Issues

### Error: PyTSK3 installation failed

**Solution 1: Use pre-built wheels**
```bash
# Windows
pip install pytsk3 --only-binary :all:

# If that doesn't work, download wheel from:
# https://github.com/py4n6/pytsk/releases
```

**Solution 2: Build from source**
```bash
# Install build dependencies first
# Then:
pip install --no-binary :all: pytsk3
```

### Error: Permission denied

```bash
# Linux/macOS: Using sudo (not recommended)
# Better to use virtual environment

# Or install for user:
pip install --user -r requirements.txt
```

### Error: Module not found

```bash
# Ensure you've activated virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall
pip install -r requirements.txt
```

## ✅ Verify Installation

```bash
# Check Python version
python3 --version

# Check PyTSK3
python3 -c "import pytsk3; print(pytsk3.__version__)"

# Check other packages
python3 -c "import colorama, tqdm, tabulate; print('OK')"

# Run tests
python3 tests/test_recovery.py

# Display help
python3 -m src.main --help
```

## 🐳 Installation with Docker (Alternative)

If you encounter difficulties with direct installation, you can use Docker:

```dockerfile
# Dockerfile (create this file)
FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

ENTRYPOINT ["python3", "-m", "src.main"]
```

```bash
# Build Docker image
docker build -t ntfs-recovery .

# Run
docker run -v $(pwd)/disk.img:/app/disk.img \
           -v $(pwd)/recovered:/app/recovered \
           ntfs-recovery disk.img -o /app/recovered
```

## 📚 Additional Dependencies

### For development

```bash
pip install pytest pytest-cov black flake8 mypy
```

### For documentation

```bash
pip install sphinx sphinx-rtd-theme
```

## 🔄 Update

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install --upgrade -r requirements.txt

# Reinstall package
pip install -e .
```

## ❓ Support

If you encounter issues, please:
1. Check [Issues](https://github.com/yourusername/ntfs-file-recovery/issues)
2. Create new issue with information:
   - OS and version
   - Python version
   - Full error message
   - Output of `pip list`

## 📖 Additional Documentation

- [README.md](README.md) - Usage guide
- [PyTSK Documentation](https://github.com/py4n6/pytsk)
- [The Sleuth Kit](https://www.sleuthkit.org/)
