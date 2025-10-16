#!/usr/bin/env python3
"""
Test script để demo tính năng MFT-based file detection
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.ntfs_parser import NTFSParser
from src.mft_analyzer import MFTAnalyzer
from src.ui.interface import UserInterface


def test_mft_detection(image_path: str):
    """
    Test MFT detection trên một disk image
    
    Args:
        image_path: Đường dẫn đến disk image
    """
    ui = UserInterface()
    ui.print_banner()
    
    print(f"\n{'='*70}")
    print("TEST: MFT-BASED FILE DETECTION")
    print(f"{'='*70}\n")
    
    # Khởi tạo parser
    ui.print_info(f"Đang mở disk image: {image_path}")
    parser = NTFSParser(image_path)
    
    if not parser.initialize():
        ui.print_error("Không thể khởi tạo NTFS parser")
        return False
    
    ui.print_success("Đã khởi tạo NTFS parser")
    
    # Tạo analyzer
    analyzer = MFTAnalyzer(parser.get_filesystem())
    
    # Test: Quét 1000 MFT entries đầu tiên
    ui.print_info("Đang quét 1000 MFT entries đầu tiên...")
    deleted_files = analyzer.scan_mft_directly(max_entries=1000)
    
    if not deleted_files:
        ui.print_warning("Không tìm thấy file đã xóa nào")
        parser.close()
        return False
    
    ui.print_success(f"Tìm thấy {len(deleted_files)} file đã xóa")
    
    # Hiển thị chi tiết
    print(f"\n{'='*70}")
    print("CHI TIẾT FILE ĐÃ XÓA")
    print(f"{'='*70}\n")
    
    # Phân loại files
    with_mft_name = 0
    with_extension = 0
    with_detected_type = 0
    verified = 0
    mismatched = 0
    
    for file_info in deleted_files[:10]:  # Hiển thị 10 file đầu
        print(f"\n📄 File #{file_info.inode}")
        print(f"   Tên: {file_info.name}")
        print(f"   Kích thước: {file_info.size} bytes")
        
        # Hiển thị nguồn thông tin
        if file_info.info_source:
            source_icon = {
                'MFT': '📋',           # Từ MFT (nguồn chính)
                'MAGIC': '🔮',         # Từ magic number
                'BOTH': '🤝',          # Kết hợp cả 2
                'MFT_FILENAME': '📝'   # Từ MFT filename + extension DB
            }.get(file_info.info_source, '❓')
            print(f"   {source_icon} Nguồn: {file_info.info_source}")
        
        if file_info.extension:
            print(f"   Extension: {file_info.extension}", end='')
            if file_info.info_source == 'MFT':
                print(" (từ MFT)")
            elif file_info.info_source == 'BOTH':
                print(" (MFT + Magic)")
            elif file_info.info_source == 'MAGIC':
                print(" (từ Magic)")
            else:
                print()
            with_extension += 1
        
        if file_info.detected_extension:
            print(f"   Magic detected: {file_info.detected_extension}")
            with_detected_type += 1
        
        if file_info.detected_mime_type:
            print(f"   MIME Type: {file_info.detected_mime_type}")
        
        if file_info.detected_description:
            print(f"   Mô tả: {file_info.detected_description}")
        
        if file_info.file_category:
            category_icon = {
                'document': '📄',
                'image': '🖼️',
                'video': '🎬',
                'audio': '🎵',
                'code': '💻',
                'archive': '📦',
                'executable': '⚙️',
                'database': '🗄️'
            }.get(file_info.file_category, '📁')
            print(f"   {category_icon} Category: {file_info.file_category}")
        
        if file_info.is_extension_verified:
            print(f"   ✓ Extension đã được xác thực")
            verified += 1
        elif file_info.detected_extension and file_info.extension:
            if file_info.extension != file_info.detected_extension:
                print(f"   ⚠️  CẢNH BÁO: Extension không khớp! (có thể giả mạo)")
                print(f"      MFT: {file_info.extension} vs Detected: {file_info.detected_extension}")
                mismatched += 1
        
        if not file_info.name.startswith('inode_'):
            with_mft_name += 1
        
        if file_info.modified_time:
            print(f"   Ngày sửa: {file_info.modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"   {'─'*60}")
    
    # Thống kê
    print(f"\n{'='*70}")
    print("THỐNG KÊ")
    print(f"{'='*70}\n")
    
    total = len(deleted_files)
    print(f"📊 Tổng số file đã xóa: {total}")
    print(f"📝 File có tên từ MFT: {with_mft_name} ({with_mft_name/total*100:.1f}%)")
    print(f"🏷️  File có extension từ MFT: {with_extension} ({with_extension/total*100:.1f}%)")
    print(f"🔍 File được detect type: {with_detected_type} ({with_detected_type/total*100:.1f}%)")
    print(f"✓  Extension đã verify: {verified} ({verified/total*100:.1f}%)")
    
    if mismatched > 0:
        print(f"⚠️  Extension không khớp: {mismatched} ({mismatched/total*100:.1f}%)")
    
    # So sánh phương pháp
    print(f"\n{'='*70}")
    print("SO SÁNH PHƯƠNG PHÁP")
    print(f"{'='*70}\n")
    
    print("Phương pháp cũ (Magic Priority):")
    print(f"  - Giữ được tên file: 0% (luôn dùng inode_xxx)")
    print(f"  - Detect được type: {with_detected_type/total*100:.1f}%")
    print(f"  - Verify extension: Không")
    print(f"  - Phát hiện giả mạo: Không")
    
    print("\nPhương pháp mới (MFT Priority):")
    print(f"  - Giữ được tên file: {with_mft_name/total*100:.1f}% (ưu tiên MFT)")
    print(f"  - Detect được type: {with_detected_type/total*100:.1f}%")
    print(f"  - Verify extension: {verified/total*100:.1f}% (MFT + Magic)")
    print(f"  - Phát hiện giả mạo: {mismatched/total*100:.1f}% (⚠️  cảnh báo)")
    
    improvement = (with_mft_name/total*100) if total > 0 else 0
    print(f"\n🎯 Cải thiện: +{improvement:.1f}% khả năng giữ nguyên tên file!")
    print(f"🔒 Bảo mật: Phát hiện được {mismatched} file nghi ngờ giả mạo")
    
    print(f"\n{'='*70}")
    print("PHÂN TÍCH NGUỒN THÔNG TIN")
    print(f"{'='*70}\n")
    
    # Thống kê theo nguồn
    mft_count = sum(1 for f in deleted_files if f.info_source == 'MFT')
    magic_count = sum(1 for f in deleted_files if f.info_source == 'MAGIC')
    both_count = sum(1 for f in deleted_files if f.info_source == 'BOTH')
    mft_filename_count = sum(1 for f in deleted_files if f.info_source == 'MFT_FILENAME')
    
    print(f"📋 MFT (verified): {mft_count} ({mft_count/total*100:.1f}%)")
    print(f"📝 MFT_FILENAME (extension DB): {mft_filename_count} ({mft_filename_count/total*100:.1f}%)")
    print(f"🤝 MFT + Magic (both): {both_count} ({both_count/total*100:.1f}%)")
    print(f"🔮 Magic only: {magic_count} ({magic_count/total*100:.1f}%)")
    
    reliable = mft_count + both_count + mft_filename_count
    print(f"\n✅ Tổng nguồn tin cậy (có thông tin từ MFT): {reliable} ({reliable/total*100:.1f}%)")
    
    # Thống kê theo category
    print(f"\n{'='*70}")
    print("PHÂN LOẠI THEO CATEGORY")
    print(f"{'='*70}\n")
    
    categories = {}
    for f in deleted_files:
        if f.file_category:
            categories[f.file_category] = categories.get(f.file_category, 0) + 1
    
    if categories:
        category_icons = {
            'document': '📄',
            'image': '🖼️',
            'video': '🎬',
            'audio': '🎵',
            'code': '💻',
            'archive': '📦',
            'executable': '⚙️',
            'database': '🗄️'
        }
        
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            icon = category_icons.get(cat, '📁')
            print(f"{icon} {cat.capitalize()}: {count} ({count/total*100:.1f}%)")
        
        categorized = sum(categories.values())
        print(f"\n📊 Tổng đã phân loại: {categorized} ({categorized/total*100:.1f}%)")
    
    # Đóng parser
    parser.close()
    ui.print_success("\nTest hoàn tất!")
    
    return True


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 test_mft_detection.py <disk_image>")
        print("\nVí dụ:")
        print("  python3 test_mft_detection.py sample/disk.img")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"❌ Không tìm thấy disk image: {image_path}")
        sys.exit(1)
    
    try:
        success = test_mft_detection(image_path)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã hủy bởi người dùng")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

