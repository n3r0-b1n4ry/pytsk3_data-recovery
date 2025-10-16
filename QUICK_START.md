# Quick Start Guide

## ⚡ Get Started in 5 Minutes

### Step 1: Installation (2 minutes)

```bash
# Clone and setup
git clone <repo-url>
cd pytsk3

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install
pip install -r requirements.txt
```

### Step 2: Prepare Disk Image

```bash
# If you have USB or disk to recover:
# Linux:
sudo dd if=/dev/sdb of=disk.img bs=4M status=progress

# Or use existing disk image
```

### Step 3: Scan for Deleted Files (30 seconds)

```bash
python3 -m src.main disk.img --scan-only
```

**You will see:**
- List of deleted files
- Size, file type, modification date
- Overall statistics

### Step 4: Recover Files (1-2 minutes)

```bash
# Recover all
python3 -m src.main disk.img -o ./recovered

# Or selective recovery:
python3 -m src.main disk.img -e pdf,docx -o ./documents
```

### Step 5: Check Results

```bash
ls -lh ./recovered
```

## 🎯 Common Commands

```bash
# Recover only images
python3 -m src.main disk.img -e jpg,png -o ./photos

# Recover files larger than 1MB
python3 -m src.main disk.img -s 1048576 -o ./large_files

# Recover specific file by inode
python3 -m src.main disk.img -i 12345 -o ./recovered

# Create report
python3 -m src.main disk.img -o ./recovered --report report.txt
```

## 📚 Further Reading

- [README.md](README.md) - Full documentation
- [INSTALL.md](INSTALL.md) - Detailed installation guide
- [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - Usage examples
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Project structure

## 🆘 Need Help?

```bash
# Display help
python3 -m src.main --help

# Run demo
python3 examples/demo.py full disk.img

# Run tests
python3 tests/test_recovery.py
```

---

**Good luck with your recovery!** 🚀
