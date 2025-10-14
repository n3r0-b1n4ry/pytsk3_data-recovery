"""
Main Entry Point
File chính để chạy NTFS File Recovery Tool
"""

import sys
import argparse
import os
from typing import List, Optional

from .ntfs_parser import NTFSParser
from .mft_analyzer import MFTAnalyzer, DeletedFileInfo
from .file_recovery import FileRecovery
from .ui.interface import UserInterface


def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        Parsed arguments object
    """
    parser = argparse.ArgumentParser(
        description='NTFS File Recovery Tool - Phục hồi file đã xóa từ NTFS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  # Quét và hiển thị danh sách file đã xóa
  python3 -m src.main disk.img --scan-only

  # Phục hồi tất cả file đã xóa
  python3 -m src.main disk.img -o ./recovered

  # Phục hồi chỉ file PDF và DOCX
  python3 -m src.main disk.img -e pdf,docx -o ./recovered

  # Phục hồi file theo inode
  python3 -m src.main disk.img -i 12345 -o ./recovered
        """
    )
    
    parser.add_argument(
        'image',
        help='Đường dẫn đến NTFS disk image'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='./recovered',
        help='Thư mục đầu ra cho file đã phục hồi (mặc định: ./recovered)'
    )
    
    parser.add_argument(
        '-e', '--extensions',
        help='Lọc theo extension, phân cách bằng dấu phẩy (vd: txt,pdf,jpg)'
    )
    
    parser.add_argument(
        '-s', '--min-size',
        type=int,
        default=0,
        help='Kích thước tối thiểu của file (bytes)'
    )
    
    parser.add_argument(
        '-m', '--max-size',
        type=int,
        help='Kích thước tối đa của file (bytes)'
    )
    
    parser.add_argument(
        '-i', '--inode',
        type=int,
        help='Phục hồi file theo inode cụ thể'
    )
    
    parser.add_argument(
        '--scan-only',
        action='store_true',
        help='Chỉ quét và hiển thị danh sách file, không phục hồi'
    )
    
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Tắt progress bar'
    )
    
    parser.add_argument(
        '--max-files',
        type=int,
        help='Giới hạn số lượng file phục hồi'
    )
    
    parser.add_argument(
        '--report',
        help='Đường dẫn file báo cáo kết quả'
    )
    
    return parser.parse_args()


def scan_deleted_files(parser: NTFSParser, ui: UserInterface) -> List[DeletedFileInfo]:
    """
    Quét và tìm các file đã xóa
    
    Args:
        parser: NTFSParser object
        ui: UserInterface object
        
    Returns:
        Danh sách DeletedFileInfo objects
    """
    ui.print_section("QUÉT FILESYSTEM")
    
    # Tạo MFT Analyzer
    analyzer = MFTAnalyzer(parser.get_filesystem())
    
    # Quét deleted files
    ui.print_info("Đang quét filesystem để tìm file đã xóa...")
    deleted_files = analyzer.scan_for_deleted_files()
    
    if not deleted_files:
        ui.print_warning("Không tìm thấy file đã xóa nào")
        return []
    
    # Hiển thị thống kê
    stats = analyzer.get_statistics()
    ui.display_statistics(stats)
    
    return deleted_files


def filter_files(deleted_files: List[DeletedFileInfo], 
                args, ui: UserInterface) -> List[DeletedFileInfo]:
    """
    Lọc danh sách file theo các tiêu chí
    
    Args:
        deleted_files: Danh sách file ban đầu
        args: Command line arguments
        ui: UserInterface object
        
    Returns:
        Danh sách file đã được lọc
    """
    filtered = deleted_files
    
    # Lọc theo extension
    if args.extensions:
        extensions = [ext.strip().lower() for ext in args.extensions.split(',')]
        filtered = [f for f in filtered if f.extension.lower() in extensions]
        ui.print_info(f"Lọc theo extension {extensions}: còn {len(filtered)} file")
    
    # Lọc theo size
    if args.min_size > 0:
        filtered = [f for f in filtered if f.size >= args.min_size]
        ui.print_info(f"Lọc theo min size {args.min_size} bytes: còn {len(filtered)} file")
    
    if args.max_size:
        filtered = [f for f in filtered if f.size <= args.max_size]
        ui.print_info(f"Lọc theo max size {args.max_size} bytes: còn {len(filtered)} file")
    
    # Giới hạn số lượng
    if args.max_files and len(filtered) > args.max_files:
        filtered = filtered[:args.max_files]
        ui.print_info(f"Giới hạn {args.max_files} file đầu tiên")
    
    # Lọc bỏ directories
    filtered = [f for f in filtered if not f.is_directory]
    
    return filtered


def recover_files(parser: NTFSParser, deleted_files: List[DeletedFileInfo],
                 args, ui: UserInterface):
    """
    Thực hiện phục hồi các file
    
    Args:
        parser: NTFSParser object
        deleted_files: Danh sách file cần phục hồi
        args: Command line arguments
        ui: UserInterface object
    """
    ui.print_section("PHỤC HỒI FILE")
    
    if not deleted_files:
        ui.print_warning("Không có file nào để phục hồi")
        return
    
    # Hiển thị danh sách file
    ui.display_deleted_files_table(deleted_files, max_display=50)
    
    # Xác nhận
    if not args.scan_only:
        total_size = sum(f.size for f in deleted_files)
        size_str = ui._format_size(total_size)
        
        print(f"\n{ui._format_size(total_size)} sẽ được phục hồi vào thư mục: {args.output}")
        
        if not ui.confirm_action(f"Bạn có muốn phục hồi {len(deleted_files)} file?", default=True):
            ui.print_warning("Hủy bỏ phục hồi")
            return
    else:
        ui.print_info("Chế độ scan-only: không phục hồi file")
        return
    
    # Tạo FileRecovery object
    recovery = FileRecovery(parser.get_filesystem(), args.output)
    
    # Tạo progress callback
    if not args.no_progress:
        progress_bar = ui.create_progress_bar(len(deleted_files), "Phục hồi")
        
        def progress_callback(current, total, filename):
            progress_bar.update(1)
            progress_bar.set_postfix_str(filename[:30])
        
        # Phục hồi với progress bar
        stats = recovery.recover_files(deleted_files, progress_callback)
        progress_bar.close()
    else:
        # Phục hồi không có progress bar
        stats = recovery.recover_files(deleted_files)
    
    # Hiển thị kết quả
    ui.display_recovery_stats(stats)
    
    # Tạo báo cáo nếu được yêu cầu
    if args.report:
        recovery.create_recovery_report(args.report)


def recover_by_inode(parser: NTFSParser, inode: int, 
                    args, ui: UserInterface):
    """
    Phục hồi file theo inode cụ thể
    
    Args:
        parser: NTFSParser object
        inode: Inode number
        args: Command line arguments
        ui: UserInterface object
    """
    ui.print_section(f"PHỤC HỒI FILE THEO INODE {inode}")
    
    # Tạo FileRecovery object
    recovery = FileRecovery(parser.get_filesystem(), args.output)
    
    # Tạo tên file output
    output_name = ui.prompt_input(
        "Nhập tên file output", 
        default=f"recovered_inode_{inode}"
    )
    
    # Phục hồi
    ui.print_info(f"Đang phục hồi inode {inode}...")
    success = recovery.recover_by_inode(inode, output_name)
    
    if success:
        ui.print_success(f"Đã phục hồi file vào: {os.path.join(args.output, output_name)}")
    else:
        ui.print_error("Phục hồi thất bại")


def main():
    """
    Main function
    """
    # Parse arguments
    args = parse_arguments()
    
    # Tạo UI
    ui = UserInterface()
    ui.print_banner()
    
    # Kiểm tra file image có tồn tại không
    if not os.path.exists(args.image):
        ui.print_error(f"Không tìm thấy disk image: {args.image}")
        sys.exit(1)
    
    try:
        # Khởi tạo NTFS Parser
        ui.print_section("KHỞI TẠO")
        ui.print_info(f"Đang mở disk image: {args.image}")
        
        parser = NTFSParser(args.image)
        
        if not parser.initialize():
            ui.print_error("Không thể khởi tạo NTFS parser")
            sys.exit(1)
        
        # Nếu chỉ định inode cụ thể
        if args.inode:
            recover_by_inode(parser, args.inode, args, ui)
            parser.close()
            return
        
        # Quét deleted files
        deleted_files = scan_deleted_files(parser, ui)
        
        if not deleted_files:
            parser.close()
            return
        
        # Lọc files
        filtered_files = filter_files(deleted_files, args, ui)
        
        # Phục hồi files
        recover_files(parser, filtered_files, args, ui)
        
        # Đóng parser
        parser.close()
        
        ui.print_success("Hoàn tất!")
        
    except KeyboardInterrupt:
        print()
        ui.print_warning("Đã hủy bỏ bởi người dùng")
        sys.exit(0)
        
    except Exception as e:
        ui.print_error(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

