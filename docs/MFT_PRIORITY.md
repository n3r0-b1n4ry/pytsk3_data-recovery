# MFT Priority Strategy

## Tổng quan

Hệ thống đã được điều chỉnh để **ƯU TIÊN THÔNG TIN TỪ MFT** (Master File Table) trước, chỉ sử dụng magic number detection để:
1. **Bổ sung** khi MFT thiếu thông tin
2. **Verify** tính chính xác của thông tin MFT
3. **Phát hiện** file giả mạo

---

## 🎯 Nguyên tắc ưu tiên

### 1. MFT là nguồn chính thức (Primary Source)

**Lý do:**
- MFT là cấu trúc dữ liệu chính thức của NTFS
- Được hệ điều hành Windows quản lý
- Chứa tên file gốc và metadata đáng tin cậy
- Có thể chứa thông tin về file type từ Windows

**Ưu tiên:**
```
MFT > Magic Number Detection
```

### 2. Magic Number là công cụ bổ trợ (Secondary Tool)

**Chức năng:**
- ✅ Bổ sung extension khi MFT thiếu
- ✅ Verify tính chính xác của MFT
- ✅ Phát hiện file giả mạo
- ❌ KHÔNG override thông tin từ MFT

---

## 🔄 Logic Flow mới

### Flow chart:

```
┌─────────────────────┐
│  Scan MFT Entry     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Extract from MFT:   │
│ - Filename          │
│ - Extension         │
│ - Timestamps        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Read file content   │
│ (512 bytes)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Detect magic number │
└──────────┬──────────┘
           │
           ▼
    ┌──────┴──────┐
    │             │
    ▼             ▼
[MFT có          [MFT không có
 extension]       extension]
    │             │
    ▼             ▼
[GIỮ NGUYÊN]   [BỔ SUNG từ
[chỉ VERIFY]    magic number]
    │             │
    │             │
    └──────┬──────┘
           │
           ▼
    ┌──────┴──────┐
    │             │
    ▼             ▼
[Verified ✓]  [Mismatch ⚠]
```

---

## 📋 3 Cases xử lý

### Case 1: MFT có đầy đủ (Tên + Extension)

**Input:**
```
MFT: document.pdf
Magic: PDF (0x25 0x50 0x44 0x46)
```

**Logic:**
```python
if has_mft_name and has_mft_extension:
    # GIỮ NGUYÊN thông tin từ MFT
    info.name = "document.pdf"  # Không thay đổi
    info.extension = "pdf"      # Không thay đổi
    
    # CHỈ VERIFY
    info.is_extension_verified = (mft_ext == detected_ext)
    info.info_source = 'MFT'    # Nguồn: MFT
```

**Output:**
```
Name: document.pdf
Type: PDF ✓ (MFT verified)
Source: MFT
```

**Kết quả:** ✅ Tin tưởng MFT, verified bằng magic number

---

### Case 2: MFT có tên nhưng thiếu extension

**Input:**
```
MFT: myfile (không có extension)
Magic: JPEG (0xFF 0xD8 0xFF)
```

**Logic:**
```python
elif has_mft_name and not has_mft_extension:
    # GIỮ TÊN từ MFT
    info.name = "myfile.jpg"     # Thêm extension
    
    # BỔ SUNG extension từ magic
    info.extension = "jpg"       # Từ magic number
    info.is_extension_verified = True
    info.info_source = 'BOTH'    # Nguồn: MFT + Magic
```

**Output:**
```
Name: myfile.jpg
Type: JPG ✓ (MFT + magic)
Source: BOTH
```

**Kết quả:** ✅ Kết hợp: Tên từ MFT + Extension từ magic

---

### Case 3: MFT không có thông tin (corrupted)

**Input:**
```
MFT: (none/corrupted)
Magic: PNG (0x89 0x50 0x4E 0x47)
```

**Logic:**
```python
else:  # MFT bị corrupt
    # FALLBACK sang magic number
    info.name = f"inode_{inode}.png"
    info.extension = "png"
    info.is_extension_verified = True
    info.info_source = 'MAGIC'   # Nguồn: Chỉ Magic
```

**Output:**
```
Name: inode_12345.png
Type: PNG * (magic only)
Source: MAGIC
```

**Kết quả:** ⚠️ Chỉ có magic number, không có MFT

---

## 🚨 Phát hiện file giả mạo

### Case đặc biệt: Extension mismatch

**Input:**
```
MFT: invoice.pdf
Magic: Windows EXE (0x4D 0x5A)
```

**Logic:**
```python
if has_mft_name and has_mft_extension:
    info.is_extension_verified = (mft_ext == detected_ext)
    # "pdf" != "exe" → False
    
    if not info.is_extension_verified:
        print(f"[!] Cảnh báo: Extension không khớp")
        print(f"    MFT: {info.extension}")
        print(f"    Detected: {detected_ext}")
```

**Output:**
```
Name: invoice.pdf
Type: PDF ⚠ (MISMATCH!)

⚠️  CẢNH BÁO: Extension không khớp
    MFT: pdf
    Detected: exe (Windows Executable)
    
→ Có thể là malware giả dạng!
```

**Kết quả:** 🚨 Phát hiện file giả mạo, cảnh báo người dùng

---

## 📊 Ký hiệu trong UI

### Bảng hiển thị:

```
+-----+--------+------------------+--------------+----------+
| #   | Inode  | Tên File         | Kích thước   | Loại     |
+-----+--------+------------------+--------------+----------+
| 1   | 12345  | document.pdf     | 1.5 MB       | PDF ✓    |
| 2   | 12346  | myfile.jpg       | 2.3 MB       | JPG ✓    |
| 3   | 12347  | inode_12347.png  | 512 KB       | PNG *    |
| 4   | 12348  | invoice.pdf      | 1.2 MB       | PDF ⚠    |
+-----+--------+------------------+--------------+----------+
```

### Ý nghĩa ký hiệu:

| Ký hiệu | Ý nghĩa | Nguồn | Tin cậy |
|---------|---------|-------|---------|
| **✓** | Verified | MFT + Magic verified | ⭐⭐⭐ Cao nhất |
| **⚠** | Mismatch | MFT (không khớp magic) | ⭐ Nghi ngờ |
| ***** | Magic only | Chỉ Magic number | ⭐⭐ Trung bình |
| (none) | MFT only | Chỉ MFT, chưa verify | ⭐⭐ Trung bình |

### Chú thích đầy đủ:

```
Chú thích (ưu tiên MFT):
  ✓ = Extension từ MFT và đã verify bằng magic number
  ⚠ = Extension từ MFT nhưng không khớp với magic number (có thể giả mạo)
  * = Chỉ detect từ magic number (MFT không có thông tin)
  (không ký hiệu) = Chỉ từ MFT, chưa verify
```

---

## 💻 Code Implementation

### Trong mft_analyzer.py:

```python
def _detect_file_type_from_inode(self, inode: int, info: DeletedFileInfo):
    """ƯU TIÊN MFT, chỉ dùng magic number để bổ sung"""
    
    # Kiểm tra MFT
    has_mft_name = not info.name.startswith('inode_')
    has_mft_extension = bool(info.extension)
    
    # Detect từ magic
    detection_result = self.file_type_detector.detect_from_bytes(data)
    
    if detection_result:
        detected_ext, detected_mime, detected_desc = detection_result
        
        # CASE 1: MFT đầy đủ → GIỮ NGUYÊN, verify
        if has_mft_name and has_mft_extension:
            info.is_extension_verified = (info.extension == detected_ext)
            info.info_source = 'MFT'
        
        # CASE 2: MFT thiếu extension → BỔ SUNG
        elif has_mft_name and not has_mft_extension:
            info.extension = detected_ext
            info.info_source = 'BOTH'
        
        # CASE 3: MFT corrupt → DÙNG magic
        else:
            info.name = f"inode_{inode}.{detected_ext}"
            info.info_source = 'MAGIC'
```

---

## 📈 So sánh với phương pháp cũ

### Phương pháp cũ (Magic Priority):

```
1. Scan MFT → Lấy inode
2. Detect magic → Tạo tên "inode_12345.jpg"
3. Ignore MFT filename
```

**Vấn đề:**
- ❌ Mất tên file gốc
- ❌ Override thông tin từ MFT
- ❌ Không tin tưởng nguồn chính thức

### Phương pháp mới (MFT Priority):

```
1. Scan MFT → Lấy tên gốc "document.pdf"
2. Detect magic → Verify "pdf" == "pdf" ✓
3. Keep MFT info, verified!
```

**Lợi ích:**
- ✅ Giữ nguyên tên file gốc
- ✅ Tin tưởng nguồn chính thức
- ✅ Magic chỉ để verify/bổ sung
- ✅ Phát hiện file giả mạo

---

## 🔍 Ví dụ thực tế

### Scenario 1: File bình thường

```bash
Input: vacation_photo.jpg
MFT: ✓ Có tên
Magic: ✓ JPEG

Result:
  Name: vacation_photo.jpg
  Extension: jpg (from MFT)
  Verified: ✓ (matches magic)
  Display: JPG ✓
```

### Scenario 2: File không extension

```bash
Input: report (no extension)
MFT: ✓ Có tên, ✗ Không extension
Magic: ✓ MS Word

Result:
  Name: report.docx (added extension)
  Extension: docx (from magic)
  Verified: ✓
  Display: DOCX ✓
```

### Scenario 3: Malware giả dạng

```bash
Input: contract.pdf
MFT: ✓ Có tên
Magic: ✓ Windows EXE

Result:
  Name: contract.pdf (kept from MFT)
  Extension: pdf (from MFT)
  Detected: exe (warning!)
  Verified: ✗ MISMATCH!
  Display: PDF ⚠
  
⚠️  Warning: Possible malware disguised as PDF!
```

### Scenario 4: MFT bị corrupt

```bash
Input: (MFT corrupted)
MFT: ✗ Không đọc được
Magic: ✓ PNG

Result:
  Name: inode_12345.png (fallback)
  Extension: png (from magic)
  Verified: ✓ (no MFT to compare)
  Display: PNG *
```

---

## 🎯 Best Practices

### 1. Tin tưởng MFT trước

```python
# ✅ ĐÚNG
if info.extension:  # Từ MFT
    # Giữ nguyên, chỉ verify
    pass

# ❌ SAI
if detected_extension:  # Từ magic
    info.extension = detected_extension  # Override MFT!
```

### 2. Chỉ bổ sung khi thiếu

```python
# ✅ ĐÚNG
if not info.extension:  # MFT thiếu
    info.extension = detected_extension

# ❌ SAI
info.extension = detected_extension  # Luôn override
```

### 3. Cảnh báo khi mismatch

```python
# ✅ ĐÚNG
if info.extension != detected_extension:
    print("[!] Cảnh báo: Extension không khớp")
    # Nhưng VẪN GIỮ thông tin từ MFT

# ❌ SAI
if info.extension != detected_extension:
    info.extension = detected_extension  # Override
```

---

## 🧪 Testing

### Test Case 1: MFT Priority

```python
# Setup
mft_name = "document.pdf"
magic_result = ("pdf", "application/pdf", "PDF Document")

# Expected
assert info.name == "document.pdf"  # Từ MFT
assert info.extension == "pdf"      # Từ MFT
assert info.info_source == 'MFT'    # Nguồn: MFT
assert info.is_extension_verified   # Verified
```

### Test Case 2: Magic Supplement

```python
# Setup
mft_name = "myfile"  # Không extension
magic_result = ("jpg", "image/jpeg", "JPEG Image")

# Expected
assert info.name == "myfile.jpg"    # Bổ sung
assert info.extension == "jpg"      # Từ magic
assert info.info_source == 'BOTH'   # MFT + Magic
```

### Test Case 3: Malware Detection

```python
# Setup
mft_name = "invoice.pdf"
magic_result = ("exe", "application/x-msdownload", "Windows EXE")

# Expected
assert info.name == "invoice.pdf"           # Giữ MFT
assert info.extension == "pdf"              # Giữ MFT
assert not info.is_extension_verified      # Not verified!
assert info.detected_extension == "exe"     # Warning
```

---

## 📚 Tham khảo

- [NTFS Documentation](https://flatcap.github.io/linux-ntfs/)
- [Forensic File Analysis](https://www.forensicfocus.com/)
- [Digital Forensics Best Practices](https://www.nist.gov/digital-forensics)

---

**Kết luận:** MFT Priority là phương pháp tin cậy và chuyên nghiệp, được sử dụng trong các công cụ forensics hàng đầu.

