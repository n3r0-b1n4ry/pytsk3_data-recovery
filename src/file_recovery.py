"""
File Recovery Module
Core logic để phục hồi các file đã xóa từ NTFS
"""

import os
import pytsk3
from typing import List, Optional, Callable
from pathlib import Path
from .mft_analyzer import DeletedFileInfo
from .fragment_handler import FragmentHandler


class RecoveryStats:
    """
    Class để theo dõi thống kê quá trình recovery
    """
    
    def __init__(self):
        self.total_files = 0
        self.recovered_files = 0
        self.failed_files = 0
        self.total_bytes_recovered = 0
        self.errors = []
        
    def add_success(self, size: int):
        """Thêm một file recovery thành công"""
        self.recovered_files += 1
        self.total_bytes_recovered += size
        
    def add_failure(self, error_msg: str):
        """Thêm một file recovery thất bại"""
        self.failed_files += 1
        self.errors.append(error_msg)
        
    def get_success_rate(self) -> float:
        """Tính tỷ lệ thành công"""
        if self.total_files == 0:
            return 0.0
        return (self.recovered_files / self.total_files) * 100
    
    def __repr__(self):
        return (f"RecoveryStats(total={self.total_files}, "
                f"recovered={self.recovered_files}, "
                f"failed={self.failed_files}, "
                f"success_rate={self.get_success_rate():.2f}%)")


class FileRecovery:
    """
    Class chính để thực hiện recovery các file đã xóa
    """
    
    def __init__(self, fs_info: pytsk3.FS_Info, output_dir: str):
        """
        Khởi tạo File Recovery
        
        Args:
            fs_info: Filesystem info object
            output_dir: Thư mục để lưu các file đã recover
        """
        self.fs_info = fs_info
        self.output_dir = output_dir
        self.fragment_handler = FragmentHandler(fs_info)
        self.stats = RecoveryStats()
        
        # Tạo output directory nếu chưa tồn tại
        os.makedirs(output_dir, exist_ok=True)
        
    def recover_file(self, file_info: DeletedFileInfo, 
                    custom_name: Optional[str] = None) -> bool:
        """
        Phục hồi một file đã xóa
        
        Args:
            file_info: DeletedFileInfo object chứa thông tin file
            custom_name: Tên tùy chỉnh cho file (optional)
            
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            # Bỏ qua directory
            if file_info.is_directory:
                return False
            
            # Bỏ qua file rỗng
            if file_info.size == 0:
                self.stats.add_failure(f"{file_info.name}: File rỗng")
                return False
            
            # Mở file object theo inode
            file_obj = self.fs_info.open_meta(inode=file_info.inode)
            
            # Đọc nội dung file (fragment handler tự động xử lý fragmentation)
            file_data = self.fragment_handler.read_fragmented_file(file_obj)
            
            if file_data is None or len(file_data) == 0:
                self.stats.add_failure(f"{file_info.name}: Không đọc được dữ liệu")
                return False
            
            # Kiểm tra data integrity
            is_valid, message = self.fragment_handler.check_data_integrity(
                file_data, file_info.size
            )
            
            if not is_valid:
                print(f"[!] Cảnh báo: {file_info.name} - {message}")
            
            # Xác định tên file output
            if custom_name:
                output_filename = custom_name
            else:
                output_filename = self._sanitize_filename(file_info.name, file_info.inode)
            
            # Đường dẫn đầy đủ
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Tránh ghi đè file đã tồn tại
            output_path = self._get_unique_path(output_path)
            
            # Ghi file ra disk
            with open(output_path, 'wb') as f:
                f.write(file_data)
            
            # Cập nhật stats
            self.stats.add_success(len(file_data))
            
            print(f"[+] Đã phục hồi: {output_filename} ({len(file_data)} bytes)")
            return True
            
        except Exception as e:
            error_msg = f"{file_info.name}: {str(e)}"
            self.stats.add_failure(error_msg)
            print(f"[!] Lỗi khi phục hồi {file_info.name}: {e}")
            return False
    
    def recover_files(self, file_list: List[DeletedFileInfo],
                     progress_callback: Optional[Callable] = None) -> RecoveryStats:
        """
        Phục hồi nhiều file
        
        Args:
            file_list: Danh sách DeletedFileInfo objects
            progress_callback: Optional callback để báo cáo tiến trình
                             Signature: callback(current, total, filename)
            
        Returns:
            RecoveryStats object với thống kê
        """
        self.stats = RecoveryStats()
        self.stats.total_files = len(file_list)
        
        print(f"[*] Bắt đầu phục hồi {len(file_list)} file...")
        
        for idx, file_info in enumerate(file_list, 1):
            if progress_callback:
                progress_callback(idx, len(file_list), file_info.name)
            
            self.recover_file(file_info)
        
        print(f"\n[+] Hoàn tất phục hồi!")
        print(f"[+] Thành công: {self.stats.recovered_files}/{self.stats.total_files}")
        print(f"[+] Tỷ lệ: {self.stats.get_success_rate():.2f}%")
        print(f"[+] Tổng dung lượng: {self._format_size(self.stats.total_bytes_recovered)}")
        
        return self.stats
    
    def recover_by_inode(self, inode: int, output_name: str) -> bool:
        """
        Phục hồi file theo inode number
        
        Args:
            inode: Inode number của file cần phục hồi
            output_name: Tên file output
            
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            # Tạo DeletedFileInfo object tạm
            file_info = DeletedFileInfo()
            file_info.inode = inode
            file_info.name = output_name
            
            # Lấy file metadata để biết size
            file_obj = self.fs_info.open_meta(inode=inode)
            file_info.size = file_obj.info.meta.size
            file_info.is_directory = (file_obj.info.meta.type == 
                                     pytsk3.TSK_FS_META_TYPE_DIR)
            
            return self.recover_file(file_info, custom_name=output_name)
            
        except Exception as e:
            print(f"[!] Lỗi khi phục hồi inode {inode}: {e}")
            return False
    
    def _sanitize_filename(self, filename: str, inode: int) -> str:
        """
        Làm sạch tên file để đảm bảo hợp lệ trên filesystem
        
        Args:
            filename: Tên file gốc
            inode: Inode number (dùng làm fallback)
            
        Returns:
            Tên file đã được sanitize
        """
        # Xóa các ký tự không hợp lệ
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Nếu filename rỗng hoặc chỉ có dấu chấm, dùng inode
        if not filename or filename.strip('.') == '':
            filename = f"recovered_file_{inode}"
        
        # Giới hạn độ dài filename
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:190] + ext
        
        return filename
    
    def _get_unique_path(self, path: str) -> str:
        """
        Tạo path unique để tránh ghi đè file đã tồn tại
        
        Args:
            path: Đường dẫn gốc
            
        Returns:
            Đường dẫn unique
        """
        if not os.path.exists(path):
            return path
        
        # Thêm số vào tên file
        base, ext = os.path.splitext(path)
        counter = 1
        
        while True:
            new_path = f"{base}_{counter}{ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    
    def _format_size(self, size_bytes: int) -> str:
        """
        Format kích thước file thành dạng human-readable
        
        Args:
            size_bytes: Kích thước tính bằng bytes
            
        Returns:
            Chuỗi đã format (vd: "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def create_recovery_report(self, report_path: Optional[str] = None) -> str:
        """
        Tạo báo cáo chi tiết về quá trình recovery
        
        Args:
            report_path: Đường dẫn file báo cáo (optional)
            
        Returns:
            Nội dung báo cáo dưới dạng string
        """
        report = []
        report.append("=" * 60)
        report.append("NTFS FILE RECOVERY REPORT")
        report.append("=" * 60)
        report.append(f"\nTổng số file: {self.stats.total_files}")
        report.append(f"Phục hồi thành công: {self.stats.recovered_files}")
        report.append(f"Thất bại: {self.stats.failed_files}")
        report.append(f"Tỷ lệ thành công: {self.stats.get_success_rate():.2f}%")
        report.append(f"Tổng dung lượng: {self._format_size(self.stats.total_bytes_recovered)}")
        
        if self.stats.errors:
            report.append(f"\n\nLỖI ({len(self.stats.errors)}):")
            report.append("-" * 60)
            for error in self.stats.errors[:20]:  # Hiển thị tối đa 20 lỗi
                report.append(f"  - {error}")
            if len(self.stats.errors) > 20:
                report.append(f"  ... và {len(self.stats.errors) - 20} lỗi khác")
        
        report.append("\n" + "=" * 60)
        
        report_text = "\n".join(report)
        
        # Ghi ra file nếu có report_path
        if report_path:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"[+] Đã lưu báo cáo tại: {report_path}")
        
        return report_text
    
    def get_recoverable_size_estimate(self, file_list: List[DeletedFileInfo]) -> int:
        """
        Ước tính tổng kích thước có thể phục hồi
        
        Args:
            file_list: Danh sách file cần phục hồi
            
        Returns:
            Kích thước ước tính (bytes)
        """
        total_size = sum(f.size for f in file_list if not f.is_directory)
        return total_size

