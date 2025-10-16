# Detailed Usage Examples

## 📝 Table of Contents

1. [Preparing Disk Image](#preparing-disk-image)
2. [Scanning Deleted Files](#scanning-deleted-files)
3. [Recovering Files](#recovering-files)
4. [Filtering and Searching](#filtering-and-searching)
5. [Real-World Use Cases](#real-world-use-cases)

## 🔧 Preparing Disk Image

### Create Image from Physical Disk

**Linux:**
```bash
# List all disks
lsblk

# Create image from USB drive (replace /dev/sdb with your device)
sudo dd if=/dev/sdb of=usb_disk.img bs=4M status=progress

# Create compressed image
sudo dd if=/dev/sdb bs=4M status=progress | gzip > usb_disk.img.gz
```

**Windows (with FTK Imager or dd for Windows):**
```powershell
# Download dd for Windows: http://www.chrysocome.net/dd
dd.exe if=\\.\E: of=E:\disk.img bs=4M --progress
```

**macOS:**
```bash
# List disks
diskutil list

# Unmount disk
diskutil unmountDisk /dev/disk2

# Create image
sudo dd if=/dev/disk2 of=disk.img bs=4m
```

### Create Test Image

```bash
# Create virtual disk image (100MB)
dd if=/dev/zero of=test_disk.img bs=1M count=100

# Format with NTFS (Linux)
mkfs.ntfs -F test_disk.img

# Mount and add files
sudo mkdir /mnt/test
sudo mount -o loop test_disk.img /mnt/test
sudo cp some_files.txt /mnt/test/
sudo rm /mnt/test/some_files.txt  # Delete to test recovery
sudo umount /mnt/test
```

## 🔍 Scanning Deleted Files

### Basic Scan

```bash
# Scan and display all deleted files
python3 -m src.main disk.img --scan-only
```

**Sample Output:**
```
======================================================================
                NTFS FILE RECOVERY TOOL v1.0
     Recover deleted files from NTFS using PyTSK3
======================================================================

[+] Opened disk image: disk.img
[+] Image size: 104857600 bytes
[+] Detected NTFS partition at offset: 0
[+] Opened NTFS filesystem

DELETED FILES LIST (15 files)
+----+--------+------------------+------------+------+-------------------+
| #  | Inode  | File Name        | Size       | Type | Modified          |
+====+========+==================+============+======+===================+
| 1  | 123    | document.pdf     | 2.5 MB     | PDF  | 2024-01-15 10:30  |
| 2  | 124    | photo.jpg        | 1.2 MB     | JPG  | 2024-01-14 15:20  |
+----+--------+------------------+------------+------+-------------------+
```

### Save List to File

```bash
# Redirect output
python3 -m src.main disk.img --scan-only > file_list.txt
```

## 💾 Recovering Files

### Recover All

```bash
# Recover all files to ./recovered directory
python3 -m src.main disk.img -o ./recovered

# With detailed report
python3 -m src.main disk.img -o ./recovered --report recovery_report.txt
```

### Selective Recovery

```bash
# Recover only first 10 files (for testing)
python3 -m src.main disk.img -o ./recovered --max-files 10

# Disable progress bar (when running in scripts)
python3 -m src.main disk.img -o ./recovered --no-progress
```

### Recover Specific File by Inode

```bash
# Recover file with inode 12345
python3 -m src.main disk.img -i 12345 -o ./recovered

# Combine with scan to find inode
python3 -m src.main disk.img --scan-only | grep "important.doc"
# Remember inode number, then:
python3 -m src.main disk.img -i <inode_number> -o ./recovered
```

## 🔎 Filtering and Searching

### Filter by Extension

```bash
# Recover only documents
python3 -m src.main disk.img -e pdf,docx,doc,txt -o ./documents

# Recover only images
python3 -m src.main disk.img -e jpg,jpeg,png,gif,bmp -o ./images

# Recover only videos
python3 -m src.main disk.img -e mp4,avi,mkv,mov -o ./videos

# Multiple extensions
python3 -m src.main disk.img -e pdf,docx,xlsx,pptx -o ./office_files
```

### Filter by Size

```bash
# Only files larger than 1MB
python3 -m src.main disk.img -s 1048576 -o ./large_files

# Only files smaller than 10MB (to avoid very large files)
python3 -m src.main disk.img -m 10485760 -o ./small_files

# Files between 100KB and 50MB
python3 -m src.main disk.img -s 102400 -m 52428800 -o ./medium_files

# Only very small files (< 100KB) - likely text files
python3 -m src.main disk.img -m 102400 -o ./tiny_files
```

### Combine Multiple Filters

```bash
# PDF files larger than 1MB
python3 -m src.main disk.img -e pdf -s 1048576 -o ./large_pdfs

# JPG images smaller than 5MB
python3 -m src.main disk.img -e jpg,jpeg -m 5242880 -o ./photos

# Documents between 10KB and 10MB
python3 -m src.main disk.img -e pdf,docx,txt -s 10240 -m 10485760 -o ./docs
```

## 🎯 Real-World Use Cases

### Case 1: Recover Photos from Formatted USB

```bash
# Step 1: Create image from USB
sudo dd if=/dev/sdb of=usb_backup.img bs=4M status=progress

# Step 2: Scan to see what's available
python3 -m src.main usb_backup.img --scan-only

# Step 3: Recover all images
python3 -m src.main usb_backup.img -e jpg,png,raw,cr2 -o ./recovered_photos

# Step 4: Check results
ls -lh ./recovered_photos
```

### Case 2: Recover Important Documents

```bash
# Scan and find file
python3 -m src.main disk.img --scan-only | grep -i "report"

# Remember inode of "annual_report.docx"
# Assume inode is 4567

# Recover that file
python3 -m src.main disk.img -i 4567 -o ./recovered

# Or recover all documents
python3 -m src.main disk.img -e docx,xlsx,pptx,pdf -o ./recovered_docs
```

### Case 3: Digital Forensics Investigation

```bash
# Step 1: Create working copy of evidence
cp evidence.img working_copy.img

# Step 2: Scan and save report
python3 -m src.main working_copy.img --scan-only > scan_report.txt

# Step 3: Recover all with detailed report
python3 -m src.main working_copy.img -o ./evidence_recovery \
    --report forensics_report.txt

# Step 4: Analyze by file type
python3 -m src.main working_copy.img -e exe,dll -o ./executables
python3 -m src.main working_copy.img -e pdf,doc -o ./documents
python3 -m src.main working_copy.img -e jpg,png -o ./images

# Step 5: Create checksums
cd evidence_recovery
find . -type f -exec sha256sum {} \; > checksums.txt
```

### Case 4: Recover from Damaged Disk

```bash
# Create image with ddrescue (better than dd for damaged disks)
sudo ddrescue -f -n /dev/sdb disk_rescue.img rescue.log

# Scan with caution
python3 -m src.main disk_rescue.img --scan-only

# Recover by file type, starting with most important
python3 -m src.main disk_rescue.img -e docx,xlsx -o ./important_docs
python3 -m src.main disk_rescue.img -e jpg,png -o ./photos
python3 -m src.main disk_rescue.img -e pdf -o ./pdfs
```

### Case 5: Batch Processing Multiple Images

```bash
#!/bin/bash
# Script to process multiple disk images

for img in *.img; do
    echo "Processing $img..."
    output_dir="recovered_${img%.img}"
    python3 -m src.main "$img" -o "$output_dir" \
        --report "report_${img%.img}.txt"
done

echo "All images processed!"
```

## 📊 Analyzing Results

### Read Recovery Report

```bash
cat recovery_report.txt
```

**Sample Report:**
```
============================================================
NTFS FILE RECOVERY REPORT
============================================================

Total files: 150
Successfully recovered: 143
Failed: 7
Success rate: 95.33%
Total size: 2.34 GB

ERRORS (7):
------------------------------------------------------------
  - encrypted_file.docx: Unable to read data
  - corrupted.jpg: Missing data: 1024/2048 bytes
  ...
```

### Check Recovered Files

```bash
# Count files
ls -1 ./recovered | wc -l

# Total size
du -sh ./recovered

# List by type
ls ./recovered/*.pdf | wc -l
ls ./recovered/*.jpg | wc -l

# Check file integrity (for images)
file ./recovered/*.jpg
```

## 🔧 Troubleshooting

### Error: "Permission denied"

```bash
# Run with sudo (be careful!)
sudo python3 -m src.main disk.img -o ./recovered

# Or change ownership
sudo chown $USER:$USER disk.img
```

### Can't Find Required File

```bash
# Try scanning MFT directly
# (This feature may be added to the tool)

# Or use grep to search in scan output
python3 -m src.main disk.img --scan-only | grep -i "filename"
```

### Recovered File is Corrupted

```bash
# Some files may be encrypted or corrupted
# Check in recovery report

# For images, use other tools to repair:
# - JPEG: jpeginfo, jhead
# - PNG: pngcheck
```

## 📝 Tips and Tricks

1. **Always work with a copy of the disk image**, not the original
2. **Scan first, recover later** to know what's available
3. **Use filters** to avoid recovering too many unnecessary files
4. **Save reports** for documentation
5. **Verify recovered files** by opening and checking them
6. **Backup immediately** after successful recovery

---

**Good luck with your recovery!** 🎉
