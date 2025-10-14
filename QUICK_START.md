# Quick Start Guide

## ⚡ Bắt đầu nhanh trong 5 phút

### Bước 1: Cài đặt (2 phút)

```bash
# Clone và setup
git clone <repo-url>
cd pytsk3

# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# hoặc: venv\Scripts\activate  # Windows

# Cài đặt
pip install -r requirements.txt
```

### Bước 2: Chuẩn bị Disk Image

```bash
# Nếu có USB hoặc disk cần phục hồi:
# Linux:
sudo dd if=/dev/sdb of=disk.img bs=4M status=progress

# Hoặc dùng disk image có sẵn
```

### Bước 3: Quét File đã xóa (30 giây)

```bash
python3 -m src.main disk.img --scan-only
```

**Bạn sẽ thấy:**
- Danh sách file đã xóa
- Kích thước, loại file, ngày sửa
- Thống kê tổng quan

### Bước 4: Phục hồi File (1-2 phút)

```bash
# Phục hồi tất cả
python3 -m src.main disk.img -o ./recovered

# Hoặc phục hồi có chọn lọc:
python3 -m src.main disk.img -e pdf,docx -o ./documents
```

### Bước 5: Kiểm tra kết quả

```bash
ls -lh ./recovered
```

## 🎯 Các lệnh hay dùng

```bash
# Chỉ phục hồi ảnh
python3 -m src.main disk.img -e jpg,png -o ./photos

# Phục hồi file lớn hơn 1MB
python3 -m src.main disk.img -s 1048576 -o ./large_files

# Phục hồi file cụ thể theo inode
python3 -m src.main disk.img -i 12345 -o ./recovered

# Tạo báo cáo
python3 -m src.main disk.img -o ./recovered --report report.txt
```

## 📚 Đọc thêm

- [README.md](README.md) - Tài liệu đầy đủ
- [INSTALL.md](INSTALL.md) - Hướng dẫn cài đặt chi tiết
- [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - Ví dụ sử dụng
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Cấu trúc project

## 🆘 Cần giúp đỡ?

```bash
# Hiển thị help
python3 -m src.main --help

# Chạy demo
python3 examples/demo.py full disk.img

# Chạy tests
python3 tests/test_recovery.py
```

---

**Chúc bạn phục hồi thành công!** 🚀

