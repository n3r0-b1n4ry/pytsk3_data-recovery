# NTFS File Recovery Tool

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Công cụ phục hồi file đã xóa từ hệ thống file NTFS (New Technology File System) sử dụng Python3 và thư viện PyTSK3. Tool này được phát triển dựa trên nghiên cứu về digital forensics và data recovery.

## 🎯 Tính năng chính

- ✅ **Quét và phát hiện** file đã xóa từ NTFS disk images
- ✅ **Phục hồi file** với tỷ lệ thành công cao (~95%)
- ✅ **Xử lý file fragmentation** - ghép các mảnh file phân tán
- ✅ **Hỗ trợ nhiều loại file** - tất cả file types trên NTFS
- ✅ **Giao diện thân thiện** - CLI với colors và progress bars
- ✅ **Lọc nâng cao** - theo extension, size, inode
- ✅ **Báo cáo chi tiết** - thống kê và recovery report
- ✅ **Error handling** - xử lý encrypted files, corrupted data

## 📋 Yêu cầu hệ thống

- **Python**: 3.8 trở lên
- **Hệ điều hành**: Windows, Linux, macOS
- **Thư viện**: PyTSK3, colorama, tqdm, tabulate

## 🚀 Cài đặt

### Cài đặt từ source

```bash
# Clone repository
git clone https://github.com/yourusername/ntfs-file-recovery.git
cd ntfs-file-recovery

# Tạo virtual environment (khuyến nghị)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# hoặc
venv\Scripts\activate  # Windows

# Cài đặt dependencies
pip install -r requirements.txt

# Cài đặt package
pip install -e .
```

### Cài đặt PyTSK3

PyTSK3 có thể yêu cầu build tools:

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-dev build-essential
pip install pytsk3
```

**Windows:**
```bash
# Download pre-built wheel từ:
# https://github.com/py4n6/pytsk/releases
pip install pytsk3-xxx.whl
```

**macOS:**
```bash
brew install pkg-config
pip install pytsk3
```

## 📖 Hướng dẫn sử dụng

### Sử dụng cơ bản

```bash
# Quét và hiển thị danh sách file đã xóa
python3 -m src.main disk.img --scan-only

# Phục hồi tất cả file đã xóa
python3 -m src.main disk.img -o ./recovered

# Phục hồi với báo cáo
python3 -m src.main disk.img -o ./recovered --report recovery_report.txt
```

### Lọc theo extension

```bash
# Chỉ phục hồi file PDF và DOCX
python3 -m src.main disk.img -e pdf,docx -o ./recovered

# Phục hồi file ảnh
python3 -m src.main disk.img -e jpg,png,gif -o ./images
```

### Lọc theo kích thước

```bash
# Chỉ phục hồi file lớn hơn 1MB
python3 -m src.main disk.img -s 1048576 -o ./recovered

# Phục hồi file từ 1KB đến 10MB
python3 -m src.main disk.img -s 1024 -m 10485760 -o ./recovered
```

### Phục hồi theo inode

```bash
# Phục hồi file cụ thể theo inode number
python3 -m src.main disk.img -i 12345 -o ./recovered
```

### Giới hạn số lượng file

```bash
# Chỉ phục hồi 100 file đầu tiên
python3 -m src.main disk.img --max-files 100 -o ./recovered
```

## 🎬 Demo Scripts

Chúng tôi cung cấp các demo scripts để test và học cách sử dụng:

```bash
# Demo 1: Chỉ quét
python3 examples/demo.py scan disk.img

# Demo 2: Phục hồi theo extension
python3 examples/demo.py extension disk.img txt,pdf

# Demo 3: Phục hồi theo inode
python3 examples/demo.py inode disk.img 12345

# Demo 4: Full recovery demo
python3 examples/demo.py full disk.img
```

## 🏗️ Kiến trúc hệ thống

```
pytsk3/
├── src/
│   ├── __init__.py
│   ├── main.py                # Entry point chính
│   ├── ntfs_parser.py         # Parser NTFS structure
│   ├── mft_analyzer.py        # Phân tích Master File Table
│   ├── fragment_handler.py    # Xử lý file fragmentation
│   ├── file_recovery.py       # Core recovery logic
│   └── ui/
│       ├── __init__.py
│       └── interface.py       # User interface CLI
├── tests/
│   ├── __init__.py
│   └── test_recovery.py       # Unit tests
├── examples/
│   └── demo.py                # Demo scripts
├── requirements.txt           # Dependencies
├── setup.py                   # Setup script
└── README.md                  # Documentation
```

## 🔬 Phương pháp kỹ thuật

### 1. NTFS Structure Parsing
Tool sử dụng PyTSK3 để:
- Mở và parse NTFS disk images
- Truy cập Master File Table (MFT)
- Đọc metadata và file attributes

### 2. Deleted File Detection
Tìm file đã xóa bằng cách:
- Duyệt MFT entries
- Kiểm tra `TSK_FS_META_FLAG_UNALLOC` flag
- Thu thập metadata (tên, size, timestamps)

### 3. File Recovery Process
Phục hồi file theo quy trình:
1. Mở file metadata theo inode
2. Đọc $DATA attribute
3. Xử lý data runs (fragments)
4. Ghép các fragments lại
5. Kiểm tra data integrity
6. Ghi file ra output directory

### 4. Fragmentation Handling
Xử lý file phân mảnh:
- Trích xuất data runs từ MFT
- Đọc từng fragment từ clusters
- Rebuild file từ multiple runs
- Xử lý sparse runs (zeros)

### 5. Error Handling
Các cơ chế xử lý lỗi:
- Corrupted data detection
- Encrypted file notification
- Partial recovery support
- Comprehensive error logging

## 📊 Kết quả thực nghiệm

Theo paper nghiên cứu:
- **Tỷ lệ thành công**: ~95%
- **Hiệu suất**: Nhanh hơn các công cụ hiện tại
- **Độ chính xác**: Cao với nhiều file types
- **Data integrity**: Kiểm tra và validation

## 🧪 Testing

Chạy unit tests:

```bash
# Chạy tất cả tests
python3 -m pytest tests/

# Chạy với verbose output
python3 tests/test_recovery.py

# Test coverage
pip install coverage
coverage run -m pytest tests/
coverage report
```

## 📝 API Documentation

### NTFSParser

```python
from src.ntfs_parser import NTFSParser

# Khởi tạo và mở NTFS image
parser = NTFSParser("disk.img")
parser.initialize()

# Lấy filesystem object
fs = parser.get_filesystem()

# Lấy file theo inode
file_obj = parser.get_file_by_inode(123)

# Đóng parser
parser.close()
```

### MFTAnalyzer

```python
from src.mft_analyzer import MFTAnalyzer

# Tạo analyzer
analyzer = MFTAnalyzer(fs_info)

# Quét deleted files
deleted_files = analyzer.scan_for_deleted_files()

# Lọc theo extension
txt_files = analyzer.filter_by_extension(['txt'])

# Lọc theo size
large_files = analyzer.filter_by_size(min_size=1024*1024)

# Lấy thống kê
stats = analyzer.get_statistics()
```

### FileRecovery

```python
from src.file_recovery import FileRecovery

# Tạo recovery object
recovery = FileRecovery(fs_info, output_dir="./recovered")

# Phục hồi một file
success = recovery.recover_file(file_info)

# Phục hồi nhiều files
stats = recovery.recover_files(file_list)

# Phục hồi theo inode
success = recovery.recover_by_inode(inode=123, output_name="file.txt")

# Tạo báo cáo
report = recovery.create_recovery_report("report.txt")
```

## 🤝 Contributing

Chúng tôi hoan nghênh mọi đóng góp! Để contribute:

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 📄 License

Project này được phát hành dưới [MIT License](LICENSE).

## 🔗 Tài liệu tham khảo

- [The Sleuth Kit Documentation](https://www.sleuthkit.org/sleuthkit/docs.php)
- [PyTSK3 Documentation](https://github.com/py4n6/pytsk)
- [NTFS Documentation - Microsoft](https://docs.microsoft.com/en-us/windows/win32/fileio/file-systems)
- IEEE Paper: "Recovering Deleted Files from NTFS using PyTSK3"

## 👥 Authors

- NTFS Recovery Team
- Based on research paper (IEEE 10823366)

## 📧 Contact

Nếu có câu hỏi hoặc gặp vấn đề, vui lòng:
- Mở [GitHub Issue](https://github.com/yourusername/ntfs-file-recovery/issues)
- Email: your.email@example.com

## 🎓 Citation

Nếu sử dụng tool này trong nghiên cứu, vui lòng cite:

```bibtex
@inproceedings{ntfs_recovery_2024,
  title={Recovering Deleted Files from NTFS using PyTSK3},
  author={Authors},
  booktitle={IEEE Conference},
  year={2024},
  organization={IEEE}
}
```

## ⚠️ Disclaimer

Tool này được phát triển cho mục đích nghiên cứu và giáo dục. Người dùng cần:
- Có quyền hợp pháp với disk images
- Tuân thủ luật pháp địa phương về data recovery
- Sử dụng với trách nhiệm

## 🎯 Roadmap

**Tính năng tương lai:**
- [ ] Hỗ trợ file systems khác (ext4, FAT32)
- [ ] Machine learning cho file type classification
- [ ] GUI interface (desktop app)
- [ ] Cloud storage integration
- [ ] Advanced carving techniques
- [ ] Parallel processing support

---

**Made with ❤️ for Digital Forensics Community**

