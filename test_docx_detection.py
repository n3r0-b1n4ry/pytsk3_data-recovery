#!/usr/bin/env python3
"""
Test detection của file DOCX (inode_42.zip)
"""

import sys
sys.path.insert(0, '.')

from src.file_type_detector import FileTypeDetector

def test_docx_file():
    """Test với file thực tế"""
    
    detector = FileTypeDetector()
    
    # Đọc file inode_42.zip (thực ra là DOCX)
    file_path = 'sample/recovered/inode_42.zip'
    
    print("="*70)
    print("TEST: DOCX DETECTION (inode_42.zip)")
    print("="*70)
    print()
    
    try:
        with open(file_path, 'rb') as f:
            # Test với 512 bytes (cũ)
            data_512 = f.read(512)
            result_512 = detector.detect_from_bytes(data_512, max_check_size=512)
            
            print("Test 1: 512 bytes (phương pháp cũ)")
            if result_512:
                print(f"  Extension: {result_512[0]}")
                print(f"  Description: {result_512[2]}")
            else:
                print(f"  Không detect được")
            print()
            
            # Test với 8KB (mới)
            f.seek(0)
            data_8k = f.read(8192)
            result_8k = detector.detect_from_bytes(data_8k, max_check_size=8192)
            
            print("Test 2: 8192 bytes (phương pháp mới)")
            if result_8k:
                print(f"  Extension: {result_8k[0]}")
                print(f"  MIME: {result_8k[1]}")
                print(f"  Description: {result_8k[2]}")
            else:
                print(f"  Không detect được")
            print()
            
            # Check cho [Content_Types].xml
            print("Test 3: Kiểm tra nội dung")
            print(f"  [Content_Types].xml trong 512 bytes: {b'[Content_Types].xml' in data_512}")
            print(f"  [Content_Types].xml trong 8192 bytes: {b'[Content_Types].xml' in data_8k}")
            print(f"  word/ trong 8192 bytes: {b'word/' in data_8k}")
            print()
            
            # Summary
            if result_8k and result_8k[0] == 'docx':
                print("✅ SUCCESS: File được detect đúng là DOCX")
                return True
            else:
                print("❌ FAILED: File vẫn được detect sai")
                return False
                
    except FileNotFoundError:
        print(f"❌ File không tồn tại: {file_path}")
        print("Vui lòng chạy recovery trước:")
        print("  python3 -m src.main sample/disk.img -o ./sample/recovered")
        return False
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_docx_file()
    sys.exit(0 if success else 1)

