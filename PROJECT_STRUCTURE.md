# Cấu trúc Project

## 📁 Tổng quan cây thư mục

```
pytsk3/
├── src/                          # Source code chính
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # Entry point - điều phối toàn bộ flow
│   ├── ntfs_parser.py           # Module parse NTFS structure
│   ├── mft_analyzer.py          # Module phân tích Master File Table
│   ├── fragment_handler.py      # Module xử lý file fragmentation
│   ├── file_recovery.py         # Module core logic phục hồi file
│   └── ui/                      # User Interface package
│       ├── __init__.py
│       └── interface.py         # CLI interface với colors & progress
│
├── tests/                        # Test suite
│   ├── __init__.py
│   └── test_recovery.py         # Unit tests cho các modules
│
├── examples/                     # Demo scripts
│   └── demo.py                  # Các demo scenarios khác nhau
│
├── docs/                         # Documentation (có thể thêm)
│
├── recovered/                    # Output mặc định (gitignored)
│
├── .gitignore                    # Git ignore rules
├── LICENSE                       # MIT License
├── README.md                     # Documentation chính
├── INSTALL.md                    # Hướng dẫn cài đặt chi tiết
├── USAGE_EXAMPLES.md            # Ví dụ sử dụng chi tiết
├── PROJECT_STRUCTURE.md         # File này - cấu trúc project
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup configuration
└── abstract.txt                 # Abstract của paper nghiên cứu
```

## 📄 Chi tiết từng file

### Core Source Files

#### `src/main.py`
- **Mục đích**: Entry point chính của application
- **Chức năng**:
  - Parse command-line arguments
  - Orchestrate toàn bộ workflow
  - Kết nối các modules lại với nhau
- **Dependencies**: Tất cả các modules khác
- **Kích thước**: ~250 lines

#### `src/ntfs_parser.py`
- **Mục đích**: Xử lý NTFS disk structure
- **Class chính**: `NTFSParser`
- **Chức năng**:
  - Mở disk image
  - Detect partition offset
  - Mở NTFS filesystem
  - Cung cấp interface để truy cập filesystem
- **Dependencies**: pytsk3
- **Kích thước**: ~200 lines

#### `src/mft_analyzer.py`
- **Mục đích**: Phân tích Master File Table
- **Classes chính**: 
  - `DeletedFileInfo`: Data class chứa thông tin file
  - `MFTAnalyzer`: Analyzer chính
- **Chức năng**:
  - Traverse directories để tìm deleted files
  - Extract metadata (name, size, timestamps)
  - Filter files theo extension, size
  - Tính toán statistics
- **Dependencies**: pytsk3, datetime
- **Kích thước**: ~300 lines

#### `src/fragment_handler.py`
- **Mục đích**: Xử lý file fragmentation
- **Classes chính**:
  - `DataRun`: Đại diện cho một đoạn data
  - `FragmentHandler`: Handler chính
- **Chức năng**:
  - Extract data runs từ file attributes
  - Đọc fragmented files
  - Rebuild file từ multiple fragments
  - Kiểm tra data integrity
- **Dependencies**: pytsk3
- **Kích thước**: ~250 lines

#### `src/file_recovery.py`
- **Mục đích**: Core logic phục hồi files
- **Classes chính**:
  - `RecoveryStats`: Tracking statistics
  - `FileRecovery`: Recovery engine chính
- **Chức năng**:
  - Phục hồi individual files
  - Batch recovery nhiều files
  - Sanitize filenames
  - Tạo recovery reports
  - Progress tracking
- **Dependencies**: fragment_handler, mft_analyzer, pytsk3
- **Kích thước**: ~350 lines

#### `src/ui/interface.py`
- **Mục đích**: User interface CLI
- **Class chính**: `UserInterface`
- **Chức năng**:
  - Pretty printing với colors
  - Display tables (deleted files list)
  - Progress bars
  - User confirmation prompts
  - Input handling
  - Help display
- **Dependencies**: colorama, tqdm, tabulate
- **Kích thước**: ~300 lines

### Test Files

#### `tests/test_recovery.py`
- **Mục đích**: Unit tests
- **Test Classes**:
  - `TestDeletedFileInfo`
  - `TestDataRun`
  - `TestRecoveryStats`
  - `TestMFTAnalyzer`
  - `TestFragmentHandler`
  - `TestFileRecovery`
- **Coverage**: ~70-80% code coverage
- **Kích thước**: ~400 lines

### Example Files

#### `examples/demo.py`
- **Mục đích**: Demo scripts cho các use cases
- **Demo Functions**:
  - `demo_scan_only()`: Quét only
  - `demo_recover_by_extension()`: Phục hồi theo extension
  - `demo_recover_by_inode()`: Phục hồi theo inode
  - `demo_full_recovery()`: Full demo
- **Kích thước**: ~350 lines

### Documentation Files

#### `README.md`
- Tài liệu chính
- Features overview
- Installation guide
- Basic usage
- API documentation
- ~500 lines

#### `INSTALL.md`
- Hướng dẫn cài đặt chi tiết
- Platform-specific instructions
- Troubleshooting
- Docker setup
- ~300 lines

#### `USAGE_EXAMPLES.md`
- Ví dụ sử dụng thực tế
- Use cases cụ thể
- Tips and tricks
- ~400 lines

#### `PROJECT_STRUCTURE.md`
- File này
- Mô tả cấu trúc project
- Chi tiết từng file
- ~200 lines

### Configuration Files

#### `requirements.txt`
```
pytsk3>=20231007
argparse
tqdm>=4.65.0
colorama>=0.4.6
tabulate>=0.9.0
```

#### `setup.py`
- Package configuration
- Entry points
- Dependencies
- Metadata

#### `.gitignore`
- Ignore patterns
- Python cache files
- Virtual environments
- Output directories
- Test files

## 🔄 Data Flow

```
User Input (CLI)
    ↓
main.py (Parse args)
    ↓
NTFSParser (Open image)
    ↓
MFTAnalyzer (Scan deleted files)
    ↓
[Optional] Filters (extension, size)
    ↓
FileRecovery + FragmentHandler
    ↓
Output Files + Report
    ↓
UserInterface (Display results)
```

## 📊 Module Dependencies

```
main.py
├── ntfs_parser.py
├── mft_analyzer.py
│   └── (uses pytsk3)
├── file_recovery.py
│   ├── fragment_handler.py
│   │   └── (uses pytsk3)
│   └── mft_analyzer.py
└── ui/interface.py
    ├── (uses colorama)
    ├── (uses tqdm)
    └── (uses tabulate)
```

## 🎯 Design Patterns

### 1. **Separation of Concerns**
- Mỗi module có trách nhiệm riêng biệt
- UI tách biệt khỏi business logic
- Parser tách biệt khỏi recovery logic

### 2. **Dependency Injection**
- FileRecovery nhận fs_info qua constructor
- MFTAnalyzer nhận fs_info qua constructor
- Dễ dàng testing với mocks

### 3. **Data Classes**
- `DeletedFileInfo`: Encapsulate file metadata
- `DataRun`: Encapsulate fragment info
- `RecoveryStats`: Encapsulate statistics

### 4. **Error Handling**
- Try-except blocks ở mọi critical operations
- Graceful degradation
- Comprehensive error messages

## 📈 Code Statistics

| Component | Lines of Code | Files |
|-----------|--------------|-------|
| Core Logic | ~1,650 | 6 |
| Tests | ~400 | 1 |
| Examples | ~350 | 1 |
| Documentation | ~1,400 | 4 |
| **Total** | **~3,800** | **12** |

## 🔧 Extension Points

Để mở rộng tool:

1. **Hỗ trợ file systems khác**:
   - Tạo `Ext4Parser`, `FATParser` tương tự `NTFSParser`
   - Implement interface chung

2. **GUI Interface**:
   - Tạo `src/ui/gui.py` với tkinter/PyQt
   - Reuse toàn bộ core logic

3. **Advanced Filtering**:
   - Thêm methods vào `MFTAnalyzer`
   - Filter theo date, file signature, etc.

4. **Machine Learning**:
   - Tạo `src/ml/classifier.py`
   - File type classification
   - Recovery success prediction

5. **Parallel Processing**:
   - Modify `FileRecovery.recover_files()`
   - Sử dụng multiprocessing/threading

## 📝 Coding Conventions

- **Style Guide**: PEP 8
- **Docstrings**: Google style
- **Type Hints**: Sử dụng typing module
- **Error Messages**: Tiếng Việt (theo user preference)
- **Comments**: Tiếng Việt cho clarity

## 🎓 Learning Path

Để hiểu project:

1. Đọc `README.md` - overview
2. Xem `abstract.txt` - hiểu paper
3. Chạy `examples/demo.py` - thấy tool hoạt động
4. Đọc `src/main.py` - hiểu flow
5. Đọc từng module theo thứ tự:
   - `ntfs_parser.py`
   - `mft_analyzer.py`
   - `fragment_handler.py`
   - `file_recovery.py`
   - `ui/interface.py`
6. Đọc tests để hiểu usage
7. Thử modify và extend

---

**Project Structure Version**: 1.0  
**Last Updated**: 2024

