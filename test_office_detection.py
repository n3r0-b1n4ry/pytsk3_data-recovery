#!/usr/bin/env python3
"""
Test script để kiểm tra nhận diện file Office formats (docx, xlsx, pptx)
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.file_type_detector import FileTypeDetector


def test_zip_based_formats():
    """Test nhận diện các ZIP-based formats"""
    
    detector = FileTypeDetector()
    
    print("="*70)
    print("TEST: ZIP-BASED FORMAT DETECTION")
    print("="*70)
    print()
    
    # Test cases: (data_signature, expected_ext, description)
    test_cases = []
    
    # 1. DOCX - có [Content_Types].xml và word/
    docx_data = b'\x50\x4B\x03\x04' + b'\x00' * 100 + b'[Content_Types].xml' + b'\x00' * 50 + b'word/document.xml'
    test_cases.append((docx_data, 'docx', 'DOCX (Word Document)'))
    
    # 2. XLSX - có [Content_Types].xml và xl/
    xlsx_data = b'\x50\x4B\x03\x04' + b'\x00' * 100 + b'[Content_Types].xml' + b'\x00' * 50 + b'xl/workbook.xml'
    test_cases.append((xlsx_data, 'xlsx', 'XLSX (Excel Spreadsheet)'))
    
    # 3. PPTX - có [Content_Types].xml và ppt/
    pptx_data = b'\x50\x4B\x03\x04' + b'\x00' * 100 + b'[Content_Types].xml' + b'\x00' * 50 + b'ppt/presentation.xml'
    test_cases.append((pptx_data, 'pptx', 'PPTX (PowerPoint Presentation)'))
    
    # 4. JAR - có META-INF/
    jar_data = b'\x50\x4B\x03\x04' + b'\x00' * 100 + b'META-INF/MANIFEST.MF'
    test_cases.append((jar_data, 'jar', 'JAR (Java Archive)'))
    
    # 5. APK - có AndroidManifest.xml
    apk_data = b'\x50\x4B\x03\x04' + b'\x00' * 100 + b'AndroidManifest.xml'
    test_cases.append((apk_data, 'apk', 'APK (Android Package)'))
    
    # 6. Plain ZIP - không có đặc điểm đặc biệt
    zip_data = b'\x50\x4B\x03\x04' + b'\x00' * 200
    test_cases.append((zip_data, 'zip', 'ZIP (Plain Archive)'))
    
    # 7. ODT - OpenDocument Text
    odt_data = b'\x50\x4B\x03\x04' + b'mimetype' + b'\x00' * 30 + b'application/vnd.oasis.opendocument.text'
    test_cases.append((odt_data, 'odt', 'ODT (OpenDocument Text)'))
    
    # Run tests
    passed = 0
    failed = 0
    
    for i, (data, expected_ext, desc) in enumerate(test_cases, 1):
        print(f"Test {i}: {desc}")
        print(f"  Expected: {expected_ext}")
        
        result = detector.detect_from_bytes(data)
        
        if result:
            detected_ext, mime_type, description = result
            print(f"  Detected: {detected_ext}")
            print(f"  MIME: {mime_type}")
            print(f"  Description: {description}")
            
            if detected_ext == expected_ext:
                print(f"  ✅ PASSED")
                passed += 1
            else:
                print(f"  ❌ FAILED (expected {expected_ext}, got {detected_ext})")
                failed += 1
        else:
            print(f"  ❌ FAILED (no detection)")
            failed += 1
        
        print()
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total tests: {len(test_cases)}")
    print(f"✅ Passed: {passed} ({passed/len(test_cases)*100:.1f}%)")
    print(f"❌ Failed: {failed} ({failed/len(test_cases)*100:.1f}%)")
    print()
    
    return failed == 0


def test_magic_number_priority():
    """Test ưu tiên giữa ZIP signature và Office detection"""
    
    print("="*70)
    print("TEST: MAGIC NUMBER PRIORITY")
    print("="*70)
    print()
    
    detector = FileTypeDetector()
    
    # Test: DOCX phải được detect là DOCX, không phải ZIP
    print("Test: DOCX vs ZIP priority")
    docx_data = b'\x50\x4B\x03\x04' + b'\x00' * 100 + b'[Content_Types].xml' + b'word/'
    result = detector.detect_from_bytes(docx_data)
    
    if result and result[0] == 'docx':
        print(f"  ✅ Correctly detected as DOCX (not ZIP)")
        print(f"  Description: {result[2]}")
        return True
    else:
        print(f"  ❌ FAILED: Detected as {result[0] if result else 'None'}")
        return False


def test_extension_database_integration():
    """Test tích hợp với extension database"""
    
    print("\n" + "="*70)
    print("TEST: EXTENSION DATABASE INTEGRATION")
    print("="*70)
    print()
    
    detector = FileTypeDetector()
    
    # Test: Extension database phải có thông tin về docx, xlsx, pptx
    extensions = ['docx', 'xlsx', 'pptx', 'odt', 'ods']
    
    all_passed = True
    for ext in extensions:
        result = detector.detect_from_extension(ext)
        if result:
            detected_ext, mime, desc = result
            print(f"✅ {ext.upper()}: {desc}")
        else:
            print(f"❌ {ext.upper()}: Not found in database")
            all_passed = False
    
    return all_passed


def main():
    """Main test function"""
    
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "OFFICE FILE DETECTION TEST" + " "*27 + "║")
    print("╚" + "="*68 + "╝")
    print()
    
    results = []
    
    # Test 1: ZIP-based formats
    try:
        results.append(("ZIP-Based Formats", test_zip_based_formats()))
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        results.append(("ZIP-Based Formats", False))
    
    # Test 2: Priority
    try:
        results.append(("Magic Number Priority", test_magic_number_priority()))
    except Exception as e:
        print(f"❌ Error in test: {e}")
        results.append(("Magic Number Priority", False))
    
    # Test 3: Extension database
    try:
        results.append(("Extension Database", test_extension_database_integration()))
    except Exception as e:
        print(f"❌ Error in test: {e}")
        results.append(("Extension Database", False))
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\n🎉 All tests PASSED! Office file detection is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - total_passed} test(s) FAILED. Please check the implementation.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

