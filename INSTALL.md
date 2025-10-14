# Hướng dẫn cài đặt chi tiết

## 📦 Yêu cầu

### Python Version
- Python 3.8 trở lên
- Khuyến nghị: Python 3.9 hoặc 3.10

### Build Tools

Để cài đặt PyTSK3, bạn cần compiler và build tools:

#### Windows
```bash
# Cài đặt Visual Studio Build Tools
# Download từ: https://visualstudio.microsoft.com/downloads/
# Chọn "Desktop development with C++"

# Hoặc cài đặt pre-built wheel:
# Download từ: https://github.com/py4n6/pytsk/releases
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
# Cài đặt Xcode Command Line Tools
xcode-select --install

# Cài đặt Homebrew (nếu chưa có)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Cài đặt dependencies
brew install pkg-config autoconf automake libtool
```

## 🚀 Cài đặt

### Bước 1: Clone Repository

```bash
git clone https://github.com/yourusername/ntfs-file-recovery.git
cd ntfs-file-recovery
```

### Bước 2: Tạo Virtual Environment (Khuyến nghị)

```bash
# Tạo virtual environment
python3 -m venv venv

# Kích hoạt virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1
```

### Bước 3: Cài đặt Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Cài đặt requirements
pip install -r requirements.txt
```

### Bước 4: Cài đặt Package

```bash
# Development mode (khuyến nghị cho development)
pip install -e .

# Hoặc cài đặt bình thường
pip install .
```

## 🔧 Xử lý lỗi cài đặt

### Lỗi: PyTSK3 installation failed

**Giải pháp 1: Sử dụng pre-built wheels**
```bash
# Windows
pip install pytsk3 --only-binary :all:

# Nếu không được, download wheel từ:
# https://github.com/py4n6/pytsk/releases
```

**Giải pháp 2: Build from source**
```bash
# Cài đặt build dependencies trước
# Sau đó:
pip install --no-binary :all: pytsk3
```

### Lỗi: Permission denied

```bash
# Linux/macOS: Sử dụng sudo (không khuyến nghị)
# Tốt hơn là sử dụng virtual environment

# Hoặc cài đặt cho user:
pip install --user -r requirements.txt
```

### Lỗi: Module not found

```bash
# Đảm bảo bạn đã activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall
pip install -r requirements.txt
```

## ✅ Kiểm tra cài đặt

```bash
# Kiểm tra Python version
python3 --version

# Kiểm tra PyTSK3
python3 -c "import pytsk3; print(pytsk3.__version__)"

# Kiểm tra các packages khác
python3 -c "import colorama, tqdm, tabulate; print('OK')"

# Chạy tests
python3 tests/test_recovery.py

# Hiển thị help
python3 -m src.main --help
```

## 🐳 Cài đặt với Docker (Alternative)

Nếu gặp khó khăn với cài đặt trực tiếp, bạn có thể sử dụng Docker:

```dockerfile
# Dockerfile (tạo file này)
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

## 📚 Cài đặt dependencies bổ sung

### Cho development

```bash
pip install pytest pytest-cov black flake8 mypy
```

### Cho documentation

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

## ❓ Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra [Issues](https://github.com/yourusername/ntfs-file-recovery/issues)
2. Tạo issue mới với thông tin:
   - OS và version
   - Python version
   - Error message đầy đủ
   - Output của `pip list`

## 📖 Tài liệu thêm

- [README.md](README.md) - Hướng dẫn sử dụng
- [PyTSK Documentation](https://github.com/py4n6/pytsk)
- [The Sleuth Kit](https://www.sleuthkit.org/)

