"""
Demo Script
Script demo để test NTFS File Recovery Tool
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ntfs_parser import NTFSParser
from src.mft_analyzer import MFTAnalyzer
from src.file_recovery import FileRecovery
from src.ui.interface import UserInterface


def demo_scan_only(image_path: str):
    """
    Demo: Chỉ quét và hiển thị danh sách file đã xóa
    
    Args:
        image_path: Đường dẫn đến NTFS image
    """
    ui = UserInterface()
    ui.print_banner()
    ui.print_section("DEMO: SCAN ONLY MODE")
    
    # Khởi tạo parser
    ui.print_info(f"Đang mở image: {image_path}")
    parser = NTFSParser(image_path)
    
    if not parser.initialize():
        ui.print_error("Không thể khởi tạo parser")
        return
    
    # Quét deleted files
    ui.print_info("Đang quét file đã xóa...")
    analyzer = MFTAnalyzer(parser.get_filesystem())
    deleted_files = analyzer.scan_for_deleted_files()
    
    # Hiển thị kết quả
    if deleted_files:
        stats = analyzer.get_statistics()
        ui.display_statistics(stats)
        ui.display_deleted_files_table(deleted_files, max_display=20)
    else:
        ui.print_warning("Không tìm thấy file đã xóa")
    
    parser.close()
    ui.print_success("Demo hoàn tất!")


def demo_recover_by_extension(image_path: str, extensions: list, output_dir: str):
    """
    Demo: Phục hồi file theo extension cụ thể
    
    Args:
        image_path: Đường dẫn đến NTFS image
        extensions: Danh sách extensions cần phục hồi
        output_dir: Thư mục output
    """
    ui = UserInterface()
    ui.print_banner()
    ui.print_section(f"DEMO: RECOVERY BY EXTENSION ({', '.join(extensions)})")
    
    # Khởi tạo
    parser = NTFSParser(image_path)
    if not parser.initialize():
        ui.print_error("Không thể khởi tạo parser")
        return
    
    # Quét
    analyzer = MFTAnalyzer(parser.get_filesystem())
    deleted_files = analyzer.scan_for_deleted_files()
    
    # Lọc theo extension
    filtered = analyzer.filter_by_extension(extensions)
    ui.print_info(f"Tìm thấy {len(filtered)} file với extension {extensions}")
    
    if not filtered:
        ui.print_warning("Không có file nào để phục hồi")
        parser.close()
        return
    
    # Hiển thị danh sách
    ui.display_deleted_files_table(filtered, max_display=10)
    
    # Xác nhận
    if ui.confirm_action(f"Phục hồi {len(filtered)} file?", default=True):
        # Phục hồi
        recovery = FileRecovery(parser.get_filesystem(), output_dir)
        
        progress = ui.create_progress_bar(len(filtered), "Phục hồi")
        
        def callback(current, total, filename):
            progress.update(1)
        
        stats = recovery.recover_files(filtered, callback)
        progress.close()
        
        # Hiển thị kết quả
        ui.display_recovery_stats(stats)
    
    parser.close()
    ui.print_success("Demo hoàn tất!")


def demo_recover_by_inode(image_path: str, inode: int, output_dir: str):
    """
    Demo: Phục hồi file theo inode
    
    Args:
        image_path: Đường dẫn đến NTFS image
        inode: Inode number
        output_dir: Thư mục output
    """
    ui = UserInterface()
    ui.print_banner()
    ui.print_section(f"DEMO: RECOVERY BY INODE {inode}")
    
    # Khởi tạo
    parser = NTFSParser(image_path)
    if not parser.initialize():
        ui.print_error("Không thể khởi tạo parser")
        return
    
    # Phục hồi
    recovery = FileRecovery(parser.get_filesystem(), output_dir)
    
    output_name = f"recovered_inode_{inode}"
    ui.print_info(f"Đang phục hồi inode {inode}...")
    
    success = recovery.recover_by_inode(inode, output_name)
    
    if success:
        ui.print_success(f"Đã phục hồi: {os.path.join(output_dir, output_name)}")
    else:
        ui.print_error("Phục hồi thất bại")
    
    parser.close()
    ui.print_success("Demo hoàn tất!")


def demo_full_recovery(image_path: str, output_dir: str, max_files: int = 10):
    """
    Demo: Phục hồi đầy đủ với tất cả features
    
    Args:
        image_path: Đường dẫn đến NTFS image
        output_dir: Thư mục output
        max_files: Số lượng file tối đa để demo
    """
    ui = UserInterface()
    ui.print_banner()
    ui.print_section("DEMO: FULL RECOVERY")
    
    # Khởi tạo
    ui.print_info("Đang khởi tạo...")
    parser = NTFSParser(image_path)
    if not parser.initialize():
        ui.print_error("Không thể khởi tạo parser")
        return
    
    # Quét
    ui.print_info("Đang quét filesystem...")
    analyzer = MFTAnalyzer(parser.get_filesystem())
    deleted_files = analyzer.scan_for_deleted_files()
    
    if not deleted_files:
        ui.print_warning("Không tìm thấy file đã xóa")
        parser.close()
        return
    
    # Hiển thị thống kê
    stats = analyzer.get_statistics()
    ui.display_statistics(stats)
    
    # Lọc - chỉ lấy files (không phải directories)
    files_only = [f for f in deleted_files if not f.is_directory]
    
    # Giới hạn số lượng cho demo
    if len(files_only) > max_files:
        files_only = files_only[:max_files]
        ui.print_info(f"Demo giới hạn {max_files} file đầu tiên")
    
    # Hiển thị danh sách
    ui.display_deleted_files_table(files_only)
    
    # Xác nhận
    if not ui.confirm_action(f"Phục hồi {len(files_only)} file?", default=True):
        ui.print_warning("Đã hủy")
        parser.close()
        return
    
    # Phục hồi
    recovery = FileRecovery(parser.get_filesystem(), output_dir)
    
    progress = ui.create_progress_bar(len(files_only), "Phục hồi")
    
    def callback(current, total, filename):
        progress.update(1)
        progress.set_postfix_str(filename[:30])
    
    recovery_stats = recovery.recover_files(files_only, callback)
    progress.close()
    
    # Hiển thị kết quả
    ui.display_recovery_stats(recovery_stats)
    
    # Tạo báo cáo
    report_path = os.path.join(output_dir, "recovery_report.txt")
    recovery.create_recovery_report(report_path)
    
    parser.close()
    ui.print_success("Demo hoàn tất!")


def print_usage():
    """In hướng dẫn sử dụng demo"""
    print("""
DEMO SCRIPT - NTFS File Recovery Tool

Sử dụng:
    python3 examples/demo.py <mode> <image_path> [options]

Modes:
    scan        - Chỉ quét và hiển thị file đã xóa
    extension   - Phục hồi theo extension
    inode       - Phục hồi theo inode
    full        - Demo đầy đủ

Ví dụ:
    # Quét only
    python3 examples/demo.py scan disk.img

    # Phục hồi file .txt và .pdf
    python3 examples/demo.py extension disk.img txt,pdf

    # Phục hồi theo inode
    python3 examples/demo.py inode disk.img 12345

    # Full demo
    python3 examples/demo.py full disk.img
    """)


def main():
    """Main function"""
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    image_path = sys.argv[2]
    
    # Kiểm tra image tồn tại
    if not os.path.exists(image_path):
        print(f"[!] Không tìm thấy image: {image_path}")
        sys.exit(1)
    
    output_dir = "./demo_recovered"
    
    try:
        if mode == "scan":
            demo_scan_only(image_path)
            
        elif mode == "extension":
            if len(sys.argv) < 4:
                print("[!] Cần chỉ định extensions (vd: txt,pdf,jpg)")
                sys.exit(1)
            extensions = sys.argv[3].split(',')
            demo_recover_by_extension(image_path, extensions, output_dir)
            
        elif mode == "inode":
            if len(sys.argv) < 4:
                print("[!] Cần chỉ định inode number")
                sys.exit(1)
            inode = int(sys.argv[3])
            demo_recover_by_inode(image_path, inode, output_dir)
            
        elif mode == "full":
            demo_full_recovery(image_path, output_dir, max_files=10)
            
        else:
            print(f"[!] Mode không hợp lệ: {mode}")
            print_usage()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n[!] Đã hủy bởi người dùng")
        sys.exit(0)
    except Exception as e:
        print(f"[!] Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

