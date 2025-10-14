# Ví dụ sử dụng chi tiết

## 📝 Mục lục

1. [Chuẩn bị Disk Image](#chuẩn-bị-disk-image)
2. [Quét File đã xóa](#quét-file-đã-xóa)
3. [Phục hồi File](#phục-hồi-file)
4. [Lọc và Tìm kiếm](#lọc-và-tìm-kiếm)
5. [Use Cases thực tế](#use-cases-thực-tế)

## 🔧 Chuẩn bị Disk Image

### Tạo Image từ Physical Disk

**Linux:**
```bash
# List tất cả disks
lsblk

# Tạo image từ USB drive (thay /dev/sdb với device của bạn)
sudo dd if=/dev/sdb of=usb_disk.img bs=4M status=progress

# Tạo compressed image
sudo dd if=/dev/sdb bs=4M status=progress | gzip > usb_disk.img.gz
```

**Windows (với FTK Imager hoặc dd for Windows):**
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

### Tạo Test Image

```bash
# Tạo virtual disk image (100MB)
dd if=/dev/zero of=test_disk.img bs=1M count=100

# Format với NTFS (Linux)
mkfs.ntfs -F test_disk.img

# Mount và thêm files
sudo mkdir /mnt/test
sudo mount -o loop test_disk.img /mnt/test
sudo cp some_files.txt /mnt/test/
sudo rm /mnt/test/some_files.txt  # Xóa để test recovery
sudo umount /mnt/test
```

## 🔍 Quét File đã xóa

### Quét cơ bản

```bash
# Quét và hiển thị tất cả file đã xóa
python3 -m src.main disk.img --scan-only
```

**Output mẫu:**
```
======================================================================
                NTFS FILE RECOVERY TOOL v1.0
     Phục hồi file đã xóa từ NTFS sử dụng PyTSK3
======================================================================

[+] Đã mở disk image: disk.img
[+] Image size: 104857600 bytes
[+] Đã phát hiện NTFS partition tại offset: 0
[+] Đã mở NTFS filesystem

DANH SÁCH FILE ĐÃ XÓA (15 file)
+----+--------+------------------+------------+------+-------------------+
| #  | Inode  | Tên File         | Kích thước | Loại | Ngày sửa          |
+====+========+==================+============+======+===================+
| 1  | 123    | document.pdf     | 2.5 MB     | PDF  | 2024-01-15 10:30  |
| 2  | 124    | photo.jpg        | 1.2 MB     | JPG  | 2024-01-14 15:20  |
+----+--------+------------------+------------+------+-------------------+
```

### Lưu danh sách ra file

```bash
# Redirect output
python3 -m src.main disk.img --scan-only > file_list.txt
```

## 💾 Phục hồi File

### Phục hồi tất cả

```bash
# Phục hồi tất cả file vào thư mục ./recovered
python3 -m src.main disk.img -o ./recovered

# Với báo cáo chi tiết
python3 -m src.main disk.img -o ./recovered --report recovery_report.txt
```

### Phục hồi có chọn lọc

```bash
# Chỉ phục hồi 10 file đầu tiên (để test)
python3 -m src.main disk.img -o ./recovered --max-files 10

# Tắt progress bar (nếu chạy trong script)
python3 -m src.main disk.img -o ./recovered --no-progress
```

### Phục hồi file cụ thể theo inode

```bash
# Phục hồi file có inode 12345
python3 -m src.main disk.img -i 12345 -o ./recovered

# Kết hợp với scan để tìm inode
python3 -m src.main disk.img --scan-only | grep "important.doc"
# Ghi nhớ inode number, sau đó:
python3 -m src.main disk.img -i <inode_number> -o ./recovered
```

## 🔎 Lọc và Tìm kiếm

### Lọc theo Extension

```bash
# Chỉ phục hồi documents
python3 -m src.main disk.img -e pdf,docx,doc,txt -o ./documents

# Chỉ phục hồi ảnh
python3 -m src.main disk.img -e jpg,jpeg,png,gif,bmp -o ./images

# Chỉ phục hồi videos
python3 -m src.main disk.img -e mp4,avi,mkv,mov -o ./videos

# Multiple extensions
python3 -m src.main disk.img -e pdf,docx,xlsx,pptx -o ./office_files
```

### Lọc theo Kích thước

```bash
# Chỉ file lớn hơn 1MB
python3 -m src.main disk.img -s 1048576 -o ./large_files

# Chỉ file nhỏ hơn 10MB (để tránh file quá lớn)
python3 -m src.main disk.img -m 10485760 -o ./small_files

# File từ 100KB đến 50MB
python3 -m src.main disk.img -s 102400 -m 52428800 -o ./medium_files

# Chỉ file rất nhỏ (< 100KB) - có thể là text files
python3 -m src.main disk.img -m 102400 -o ./tiny_files
```

### Kết hợp nhiều bộ lọc

```bash
# PDF files lớn hơn 1MB
python3 -m src.main disk.img -e pdf -s 1048576 -o ./large_pdfs

# Ảnh JPG nhỏ hơn 5MB
python3 -m src.main disk.img -e jpg,jpeg -m 5242880 -o ./photos

# Documents từ 10KB đến 10MB
python3 -m src.main disk.img -e pdf,docx,txt -s 10240 -m 10485760 -o ./docs
```

## 🎯 Use Cases thực tế

### Case 1: Phục hồi ảnh từ USB đã format

```bash
# Bước 1: Tạo image từ USB
sudo dd if=/dev/sdb of=usb_backup.img bs=4M status=progress

# Bước 2: Quét để xem có gì
python3 -m src.main usb_backup.img --scan-only

# Bước 3: Phục hồi tất cả ảnh
python3 -m src.main usb_backup.img -e jpg,png,raw,cr2 -o ./recovered_photos

# Bước 4: Kiểm tra kết quả
ls -lh ./recovered_photos
```

### Case 2: Phục hồi documents quan trọng

```bash
# Quét và tìm file
python3 -m src.main disk.img --scan-only | grep -i "report"

# Ghi nhớ inode của file "annual_report.docx"
# Giả sử inode là 4567

# Phục hồi file đó
python3 -m src.main disk.img -i 4567 -o ./recovered

# Hoặc phục hồi tất cả documents
python3 -m src.main disk.img -e docx,xlsx,pptx,pdf -o ./recovered_docs
```

### Case 3: Digital Forensics Investigation

```bash
# Bước 1: Tạo working copy của evidence
cp evidence.img working_copy.img

# Bước 2: Quét toàn bộ và lưu báo cáo
python3 -m src.main working_copy.img --scan-only > scan_report.txt

# Bước 3: Phục hồi tất cả với báo cáo chi tiết
python3 -m src.main working_copy.img -o ./evidence_recovery \
    --report forensics_report.txt

# Bước 4: Phân tích theo loại file
python3 -m src.main working_copy.img -e exe,dll -o ./executables
python3 -m src.main working_copy.img -e pdf,doc -o ./documents
python3 -m src.main working_copy.img -e jpg,png -o ./images

# Bước 5: Tạo checksums
cd evidence_recovery
find . -type f -exec sha256sum {} \; > checksums.txt
```

### Case 4: Phục hồi từ disk bị hỏng

```bash
# Tạo image với ddrescue (tốt hơn dd cho disk lỗi)
sudo ddrescue -f -n /dev/sdb disk_rescue.img rescue.log

# Quét với caution
python3 -m src.main disk_rescue.img --scan-only

# Phục hồi từng loại file, bắt đầu với quan trọng nhất
python3 -m src.main disk_rescue.img -e docx,xlsx -o ./important_docs
python3 -m src.main disk_rescue.img -e jpg,png -o ./photos
python3 -m src.main disk_rescue.img -e pdf -o ./pdfs
```

### Case 5: Batch Processing nhiều images

```bash
#!/bin/bash
# Script để xử lý nhiều disk images

for img in *.img; do
    echo "Processing $img..."
    output_dir="recovered_${img%.img}"
    python3 -m src.main "$img" -o "$output_dir" \
        --report "report_${img%.img}.txt"
done

echo "All images processed!"
```

## 📊 Phân tích kết quả

### Đọc Recovery Report

```bash
cat recovery_report.txt
```

**Report mẫu:**
```
============================================================
NTFS FILE RECOVERY REPORT
============================================================

Tổng số file: 150
Phục hồi thành công: 143
Thất bại: 7
Tỷ lệ thành công: 95.33%
Tổng dung lượng: 2.34 GB

LỖI (7):
------------------------------------------------------------
  - encrypted_file.docx: Không đọc được dữ liệu
  - corrupted.jpg: Thiếu dữ liệu: 1024/2048 bytes
  ...
```

### Kiểm tra file đã phục hồi

```bash
# Đếm số file
ls -1 ./recovered | wc -l

# Tổng dung lượng
du -sh ./recovered

# List theo loại
ls ./recovered/*.pdf | wc -l
ls ./recovered/*.jpg | wc -l

# Kiểm tra file integrity (cho ảnh)
file ./recovered/*.jpg
```

## 🔧 Troubleshooting

### Lỗi: "Permission denied"

```bash
# Chạy với sudo (cẩn thận!)
sudo python3 -m src.main disk.img -o ./recovered

# Hoặc thay đổi ownership
sudo chown $USER:$USER disk.img
```

### Không tìm thấy file cần thiết

```bash
# Thử quét trực tiếp MFT
# (Feature này có thể được thêm vào tool)

# Hoặc sử dụng grep để tìm trong scan output
python3 -m src.main disk.img --scan-only | grep -i "filename"
```

### File phục hồi bị corrupted

```bash
# Một số file có thể bị encrypted hoặc corrupted
# Kiểm tra trong recovery report

# Với ảnh, có thể dùng tools khác để repair:
# - JPEG: jpeginfo, jhead
# - PNG: pngcheck
```

## 📝 Tips and Tricks

1. **Luôn làm việc với copy của disk image**, không phải original
2. **Quét trước, phục hồi sau** để biết có gì
3. **Sử dụng filters** để tránh phục hồi quá nhiều file không cần
4. **Lưu reports** cho documentation
5. **Verify recovered files** bằng cách mở và kiểm tra
6. **Backup ngay khi phục hồi thành công**

---

**Chúc bạn phục hồi thành công!** 🎉

