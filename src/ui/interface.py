"""
User Interface Module
Giao diện command-line thân thiện với người dùng
"""

import os
import sys
from typing import List, Optional
from tabulate import tabulate
from colorama import Fore, Back, Style, init
from tqdm import tqdm

# Khởi tạo colorama
init(autoreset=True)


class UserInterface:
    """
    Class cung cấp giao diện CLI thân thiện cho recovery tool
    """
    
    def __init__(self):
        """Khởi tạo User Interface"""
        self.use_colors = True
        
    def print_banner(self):
        """In banner chào mừng"""
        banner = f"""
{Fore.CYAN}{'=' * 70}
{Fore.YELLOW}     NTFS FILE RECOVERY TOOL v1.0
{Fore.CYAN}     Phục hồi file đã xóa từ NTFS sử dụng PyTSK3
{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}
        """
        print(banner)
    
    def print_success(self, message: str):
        """In thông báo thành công"""
        print(f"{Fore.GREEN}[✓] {message}{Style.RESET_ALL}")
    
    def print_error(self, message: str):
        """In thông báo lỗi"""
        print(f"{Fore.RED}[✗] {message}{Style.RESET_ALL}")
    
    def print_warning(self, message: str):
        """In cảnh báo"""
        print(f"{Fore.YELLOW}[!] {message}{Style.RESET_ALL}")
    
    def print_info(self, message: str):
        """In thông tin"""
        print(f"{Fore.CYAN}[i] {message}{Style.RESET_ALL}")
    
    def print_section(self, title: str):
        """In tiêu đề section"""
        print(f"\n{Fore.MAGENTA}{'=' * 70}")
        print(f"{title}")
        print(f"{'=' * 70}{Style.RESET_ALL}")
    
    def display_deleted_files_table(self, file_list: List, max_display: int = 50):
        """
        Hiển thị danh sách file đã xóa dưới dạng bảng
        
        Args:
            file_list: Danh sách DeletedFileInfo objects
            max_display: Số lượng file tối đa hiển thị
        """
        if not file_list:
            self.print_warning("Không tìm thấy file đã xóa nào")
            return
        
        self.print_section(f"DANH SÁCH FILE ĐÃ XÓA ({len(file_list)} file)")
        
        # Chuẩn bị dữ liệu cho bảng
        table_data = []
        for idx, file_info in enumerate(file_list[:max_display], 1):
            size_str = self._format_size(file_info.size)
            mtime_str = file_info.modified_time.strftime('%Y-%m-%d %H:%M:%S') if file_info.modified_time else 'N/A'
            
            # Cắt tên file nếu quá dài
            name = file_info.name[:40] + '...' if len(file_info.name) > 40 else file_info.name
            
            table_data.append([
                idx,
                file_info.inode,
                name,
                size_str,
                file_info.extension.upper() if file_info.extension else 'N/A',
                mtime_str
            ])
        
        # Headers
        headers = [
            f"{Fore.YELLOW}#",
            f"Inode",
            f"Tên File",
            f"Kích thước",
            f"Loại",
            f"Ngày sửa{Style.RESET_ALL}"
        ]
        
        # In bảng
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        
        if len(file_list) > max_display:
            self.print_info(f"Hiển thị {max_display}/{len(file_list)} file. "
                          f"Còn {len(file_list) - max_display} file khác.")
    
    def display_statistics(self, stats_dict: dict):
        """
        Hiển thị thống kê về các file đã xóa
        
        Args:
            stats_dict: Dictionary chứa thống kê từ MFTAnalyzer
        """
        self.print_section("THỐNG KÊ FILE ĐÃ XÓA")
        
        print(f"  Tổng số file đã xóa:    {Fore.CYAN}{stats_dict.get('total_deleted', 0)}{Style.RESET_ALL}")
        print(f"  Số thư mục:             {Fore.CYAN}{stats_dict.get('total_directories', 0)}{Style.RESET_ALL}")
        print(f"  Số file:                {Fore.CYAN}{stats_dict.get('total_files', 0)}{Style.RESET_ALL}")
        print(f"  Tổng kích thước:        {Fore.CYAN}{self._format_size(stats_dict.get('total_size', 0))}{Style.RESET_ALL}")
        
        # Thống kê theo extension
        if 'extensions' in stats_dict and stats_dict['extensions']:
            print(f"\n  {Fore.YELLOW}Phân loại theo extension:{Style.RESET_ALL}")
            
            # Sắp xếp theo số lượng
            sorted_exts = sorted(
                stats_dict['extensions'].items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
            
            for ext, data in sorted_exts[:10]:  # Top 10
                count = data['count']
                size = self._format_size(data['total_size'])
                print(f"    .{ext.upper():<10} {count:>5} file(s)  -  {size}")
    
    def display_recovery_stats(self, recovery_stats):
        """
        Hiển thị kết quả recovery
        
        Args:
            recovery_stats: RecoveryStats object
        """
        self.print_section("KẾT QUẢ PHỤC HỒI")
        
        success_rate = recovery_stats.get_success_rate()
        
        print(f"  Tổng số file:           {recovery_stats.total_files}")
        print(f"  {Fore.GREEN}Thành công:             {recovery_stats.recovered_files}{Style.RESET_ALL}")
        print(f"  {Fore.RED}Thất bại:               {recovery_stats.failed_files}{Style.RESET_ALL}")
        
        # Màu cho success rate
        if success_rate >= 90:
            color = Fore.GREEN
        elif success_rate >= 70:
            color = Fore.YELLOW
        else:
            color = Fore.RED
            
        print(f"  {color}Tỷ lệ thành công:       {success_rate:.2f}%{Style.RESET_ALL}")
        print(f"  Tổng dung lượng:        {self._format_size(recovery_stats.total_bytes_recovered)}")
    
    def create_progress_bar(self, total: int, desc: str = "Processing") -> tqdm:
        """
        Tạo thanh progress bar
        
        Args:
            total: Tổng số items
            desc: Mô tả
            
        Returns:
            tqdm object
        """
        return tqdm(
            total=total,
            desc=desc,
            unit="file",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
        )
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """
        Hỏi người dùng xác nhận hành động
        
        Args:
            message: Thông điệp xác nhận
            default: Giá trị mặc định (True = Yes, False = No)
            
        Returns:
            True nếu người dùng đồng ý, False nếu không
        """
        suffix = "[Y/n]" if default else "[y/N]"
        print(f"{Fore.YELLOW}[?] {message} {suffix}: {Style.RESET_ALL}", end="")
        
        try:
            response = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return False
        
        if not response:
            return default
        
        return response in ['y', 'yes']
    
    def prompt_input(self, message: str, default: Optional[str] = None) -> str:
        """
        Nhập input từ người dùng
        
        Args:
            message: Thông điệp
            default: Giá trị mặc định
            
        Returns:
            Input string
        """
        if default:
            prompt = f"{Fore.CYAN}[?] {message} [{default}]: {Style.RESET_ALL}"
        else:
            prompt = f"{Fore.CYAN}[?] {message}: {Style.RESET_ALL}"
        
        try:
            response = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(0)
        
        if not response and default:
            return default
        
        return response
    
    def select_from_list(self, items: List[str], message: str = "Chọn option:") -> Optional[int]:
        """
        Chọn từ danh sách các option
        
        Args:
            items: Danh sách các option
            message: Thông điệp
            
        Returns:
            Index của option được chọn (0-based), hoặc None nếu cancel
        """
        print(f"\n{Fore.CYAN}{message}{Style.RESET_ALL}")
        for idx, item in enumerate(items, 1):
            print(f"  {idx}. {item}")
        
        while True:
            choice = self.prompt_input(f"Nhập số (1-{len(items)}, hoặc 0 để hủy)")
            
            try:
                choice_int = int(choice)
                if choice_int == 0:
                    return None
                if 1 <= choice_int <= len(items):
                    return choice_int - 1
                else:
                    self.print_error(f"Vui lòng nhập số từ 0 đến {len(items)}")
            except ValueError:
                self.print_error("Vui lòng nhập số hợp lệ")
    
    def display_help(self):
        """Hiển thị thông tin help"""
        help_text = f"""
{Fore.YELLOW}HƯỚNG DẪN SỬ DỤNG:{Style.RESET_ALL}

{Fore.CYAN}Cú pháp:{Style.RESET_ALL}
  python3 -m src.main <disk_image> [options]

{Fore.CYAN}Options:{Style.RESET_ALL}
  -o, --output DIR          Thư mục lưu file đã phục hồi (mặc định: ./recovered)
  -e, --extensions EXT      Lọc theo extension (vd: txt,pdf,jpg)
  -s, --min-size SIZE       Kích thước tối thiểu (bytes)
  -m, --max-size SIZE       Kích thước tối đa (bytes)
  -i, --inode INODE         Phục hồi file theo inode cụ thể
  --scan-only               Chỉ quét, không phục hồi
  --no-progress             Tắt progress bar
  -h, --help                Hiển thị help

{Fore.CYAN}Ví dụ:{Style.RESET_ALL}
  # Quét và hiển thị danh sách file đã xóa
  python3 -m src.main disk.img --scan-only

  # Phục hồi tất cả file đã xóa
  python3 -m src.main disk.img -o ./recovered

  # Phục hồi chỉ file PDF và DOCX
  python3 -m src.main disk.img -e pdf,docx

  # Phục hồi file theo inode
  python3 -m src.main disk.img -i 12345 -o ./recovered
        """
        print(help_text)
    
    def _format_size(self, size_bytes: int) -> str:
        """
        Format kích thước file
        
        Args:
            size_bytes: Kích thước bytes
            
        Returns:
            String đã format
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def clear_screen(self):
        """Xóa màn hình console"""
        os.system('cls' if os.name == 'nt' else 'clear')

