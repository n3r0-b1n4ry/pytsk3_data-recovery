# Project Structure

## 📁 Directory Tree Overview

```
pytsk3/
├── src/                          # Main source code
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # Entry point - orchestrates entire flow
│   ├── ntfs_parser.py           # NTFS structure parsing module
│   ├── mft_analyzer.py          # Master File Table analysis module
│   ├── file_type_detector.py    # File type detection module (3 sources)
│   ├── fragment_handler.py      # File fragmentation handling module
│   ├── file_recovery.py         # Core file recovery logic module
│   └── ui/                      # User Interface package
│       ├── __init__.py
│       └── interface.py         # CLI interface with colors & progress
│
├── tests/                        # Test suite
│   ├── __init__.py
│   └── test_recovery.py         # Unit tests for modules
│
├── examples/                     # Demo scripts
│   └── demo.py                  # Various demo scenarios
│
├── docs/                         # Documentation
│   ├── FILE_TYPE_DETECTION.md
│   ├── MFT_FILE_DETECTION.md
│   ├── FILENAME_BASED_DETECTION.md
│   └── OFFICE_FILE_DETECTION.md
│
├── recovered/                    # Default output (gitignored)
│
├── .gitignore                    # Git ignore rules
├── LICENSE                       # MIT License
├── README.md                     # Main documentation
├── INSTALL.md                    # Detailed installation guide
├── USAGE_EXAMPLES.md            # Detailed usage examples
├── PROJECT_STRUCTURE.md         # This file - project structure
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup configuration
└── abstract.txt                 # Research paper abstract
```

## 📄 File Details

### Core Source Files

#### `src/main.py`
- **Purpose**: Main application entry point
- **Features**:
  - Parse command-line arguments
  - Orchestrate entire workflow
  - Connect modules together
- **Dependencies**: All other modules
- **Size**: ~250 lines

#### `src/ntfs_parser.py`
- **Purpose**: Handle NTFS disk structure
- **Main Class**: `NTFSParser`
- **Features**:
  - Open disk image
  - Detect partition offset
  - Open NTFS filesystem
  - Provide filesystem access interface
- **Dependencies**: pytsk3
- **Size**: ~200 lines

#### `src/mft_analyzer.py`
- **Purpose**: Analyze Master File Table
- **Main Classes**: 
  - `DeletedFileInfo`: Data class containing file information
  - `MFTAnalyzer`: Main analyzer
- **Features**:
  - Traverse directories to find deleted files
  - Extract metadata (name, size, timestamps)
  - Filter files by extension, size
  - Calculate statistics
- **Dependencies**: pytsk3, datetime
- **Size**: ~400 lines

#### `src/file_type_detector.py`
- **Purpose**: Detect file types using 3 sources
- **Main Class**: `FileTypeDetector`
- **Features**:
  - MFT filename extraction (priority 1)
  - Extension database lookup (300+ extensions)
  - Magic number detection (ZIP-based formats)
  - File categorization (7 categories)
- **Dependencies**: zipfile, struct
- **Size**: ~800 lines

#### `src/fragment_handler.py`
- **Purpose**: Handle file fragmentation
- **Main Classes**:
  - `DataRun`: Represents a data segment
  - `FragmentHandler`: Main handler
- **Features**:
  - Extract data runs from file attributes
  - Read fragmented files
  - Rebuild files from multiple fragments
  - Check data integrity
- **Dependencies**: pytsk3
- **Size**: ~250 lines

#### `src/file_recovery.py`
- **Purpose**: Core file recovery logic
- **Main Classes**:
  - `RecoveryStats`: Tracking statistics
  - `FileRecovery`: Main recovery engine
- **Features**:
  - Recover individual files
  - Batch recovery of multiple files
  - Sanitize filenames
  - Create recovery reports
  - Progress tracking
- **Dependencies**: fragment_handler, mft_analyzer, file_type_detector, pytsk3
- **Size**: ~350 lines

#### `src/ui/interface.py`
- **Purpose**: CLI user interface
- **Main Class**: `UserInterface`
- **Features**:
  - Pretty printing with colors
  - Display tables (deleted files list)
  - Progress bars
  - User confirmation prompts
  - Input handling
  - Help display
- **Dependencies**: colorama, tqdm, tabulate
- **Size**: ~350 lines

### Test Files

#### `tests/test_recovery.py`
- **Purpose**: Unit tests
- **Test Classes**:
  - `TestDeletedFileInfo`
  - `TestDataRun`
  - `TestRecoveryStats`
  - `TestMFTAnalyzer`
  - `TestFragmentHandler`
  - `TestFileRecovery`
- **Coverage**: ~70-80% code coverage
- **Size**: ~400 lines

### Example Files

#### `examples/demo.py`
- **Purpose**: Demo scripts for use cases
- **Demo Functions**:
  - `demo_scan_only()`: Scan only
  - `demo_recover_by_extension()`: Recover by extension
  - `demo_recover_by_inode()`: Recover by inode
  - `demo_full_recovery()`: Full demo
- **Size**: ~350 lines

### Documentation Files

#### `README.md`
- Main documentation
- Features overview
- Installation guide
- Basic usage
- API documentation
- ~500 lines

#### `INSTALL.md`
- Detailed installation guide
- Platform-specific instructions
- Troubleshooting
- Docker setup
- ~250 lines

#### `USAGE_EXAMPLES.md`
- Real-world usage examples
- Specific use cases
- Tips and tricks
- ~350 lines

#### `PROJECT_STRUCTURE.md`
- This file
- Project structure description
- File details
- ~200 lines

#### `docs/` Directory
- Technical documentation
- File type detection strategies
- MFT-based detection
- Office format detection

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
FileTypeDetector (Detect file types - 3 sources)
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
│   ├── file_type_detector.py
│   └── (uses pytsk3)
├── file_recovery.py
│   ├── file_type_detector.py
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
- Each module has distinct responsibility
- UI separated from business logic
- Parser separated from recovery logic

### 2. **Dependency Injection**
- FileRecovery receives fs_info through constructor
- MFTAnalyzer receives fs_info through constructor
- Easy testing with mocks

### 3. **Data Classes**
- `DeletedFileInfo`: Encapsulate file metadata
- `DataRun`: Encapsulate fragment info
- `RecoveryStats`: Encapsulate statistics

### 4. **Strategy Pattern**
- FileTypeDetector uses 3-source strategy
- Priority: MFT → Extension DB → Magic Number

### 5. **Error Handling**
- Try-except blocks in all critical operations
- Graceful degradation
- Comprehensive error messages

## 📈 Code Statistics

| Component | Lines of Code | Files |
|-----------|--------------|-------|
| Core Logic | ~2,400 | 7 |
| Tests | ~400 | 1 |
| Examples | ~350 | 1 |
| Documentation | ~1,400 | 6+ |
| **Total** | **~4,550** | **15+** |

## 🔧 Extension Points

To extend the tool:

1. **Support other file systems**:
   - Create `Ext4Parser`, `FATParser` similar to `NTFSParser`
   - Implement common interface

2. **GUI Interface**:
   - Create `src/ui/gui.py` with tkinter/PyQt
   - Reuse entire core logic

3. **Advanced Filtering**:
   - Add methods to `MFTAnalyzer`
   - Filter by date, file signature, etc.

4. **Machine Learning**:
   - Create `src/ml/classifier.py`
   - File type classification
   - Recovery success prediction

5. **Parallel Processing**:
   - Modify `FileRecovery.recover_files()`
   - Use multiprocessing/threading

## 📝 Coding Conventions

- **Style Guide**: PEP 8
- **Docstrings**: Google style
- **Type Hints**: Using typing module
- **Error Messages**: English
- **Comments**: English for clarity

## 🎓 Learning Path

To understand the project:

1. Read `README.md` - overview
2. View `abstract.txt` - understand paper
3. Run `examples/demo.py` - see tool in action
4. Read `src/main.py` - understand flow
5. Read each module in order:
   - `ntfs_parser.py`
   - `mft_analyzer.py`
   - `file_type_detector.py`
   - `fragment_handler.py`
   - `file_recovery.py`
   - `ui/interface.py`
6. Read tests to understand usage
7. Try modifying and extending

---

**Project Structure Version**: 1.0  
**Last Updated**: 2024
