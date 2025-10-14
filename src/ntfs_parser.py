"""
NTFS Parser Module
Xử lý cấu trúc NTFS và truy cập Master File Table
"""

import pytsk3
import sys
from typing import Optional, Tuple


class NTFSParser:
    """
    Class để parse NTFS structure và truy cập file system
    """
    
    def __init__(self, image_path: str):
        """
        Khởi tạo NTFS Parser
        
        Args:
            image_path: Đường dẫn đến NTFS disk image
        """
        self.image_path = image_path
        self.img_info = None
        self.fs_info = None
        self.partition_offset = 0
        
    def open_image(self) -> bool:
        """
        Mở disk image và khởi tạo pytsk3 objects
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            # Mở disk image
            self.img_info = pytsk3.Img_Info(self.image_path)
            print(f"[+] Đã mở disk image: {self.image_path}")
            print(f"[+] Image size: {self.img_info.get_size()} bytes")
            
            return True
            
        except Exception as e:
            print(f"[!] Lỗi khi mở disk image: {e}")
            return False
    
    def detect_partition_offset(self) -> bool:
        """
        Tự động phát hiện partition offset trong disk image
        
        Returns:
            True nếu phát hiện thành công, False nếu thất bại
        """
        try:
            # Thử đọc volume system (partition table)
            volume = pytsk3.Volume_Info(self.img_info)
            
            # Duyệt qua các partition
            for partition in volume:
                # Tìm partition NTFS
                if partition.desc.decode('utf-8').strip().upper() in ['NTFS', 'NTFS / EXFAT']:
                    self.partition_offset = partition.start * 512  # 512 bytes per sector
                    print(f"[+] Đã phát hiện NTFS partition tại offset: {self.partition_offset}")
                    print(f"[+] Partition description: {partition.desc.decode('utf-8')}")
                    print(f"[+] Partition size: {partition.len * 512} bytes")
                    return True
                    
            print("[!] Không tìm thấy NTFS partition")
            return False
            
        except Exception as e:
            # Nếu không có partition table, giả sử toàn bộ image là NTFS
            print(f"[*] Không phát hiện được partition table: {e}")
            print("[*] Giả sử toàn bộ image là NTFS filesystem")
            self.partition_offset = 0
            return True
    
    def open_filesystem(self) -> bool:
        """
        Mở NTFS filesystem
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            # Mở filesystem tại partition offset
            self.fs_info = pytsk3.FS_Info(self.img_info, offset=self.partition_offset)
            
            # Kiểm tra xem có phải NTFS không
            fs_type = self.fs_info.info.ftype
            if fs_type != pytsk3.TSK_FS_TYPE_NTFS:
                print(f"[!] Filesystem không phải NTFS: {fs_type}")
                return False
            
            print(f"[+] Đã mở NTFS filesystem")
            print(f"[+] Block size: {self.fs_info.info.block_size} bytes")
            print(f"[+] Block count: {self.fs_info.info.block_count}")
            
            return True
            
        except Exception as e:
            print(f"[!] Lỗi khi mở filesystem: {e}")
            return False
    
    def get_filesystem(self) -> Optional[pytsk3.FS_Info]:
        """
        Lấy filesystem info object
        
        Returns:
            FS_Info object hoặc None nếu chưa mở
        """
        return self.fs_info
    
    def get_root_directory(self) -> Optional[pytsk3.Directory]:
        """
        Lấy root directory của filesystem
        
        Returns:
            Directory object hoặc None nếu có lỗi
        """
        try:
            if self.fs_info is None:
                print("[!] Filesystem chưa được mở")
                return None
                
            # Mở root directory (inode 5 trong NTFS)
            root_dir = self.fs_info.open_dir(path="/")
            return root_dir
            
        except Exception as e:
            print(f"[!] Lỗi khi mở root directory: {e}")
            return None
    
    def initialize(self) -> bool:
        """
        Khởi tạo toàn bộ parser (mở image, detect partition, mở filesystem)
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        if not self.open_image():
            return False
            
        if not self.detect_partition_offset():
            return False
            
        if not self.open_filesystem():
            return False
            
        print("[+] NTFS Parser đã được khởi tạo thành công")
        return True
    
    def get_file_by_inode(self, inode: int) -> Optional[pytsk3.File]:
        """
        Lấy file object theo inode number
        
        Args:
            inode: Inode number (MFT entry number)
            
        Returns:
            File object hoặc None nếu có lỗi
        """
        try:
            if self.fs_info is None:
                return None
                
            file_obj = self.fs_info.open_meta(inode=inode)
            return file_obj
            
        except Exception as e:
            print(f"[!] Lỗi khi mở file inode {inode}: {e}")
            return None
    
    def close(self):
        """
        Đóng parser và giải phóng tài nguyên
        """
        self.fs_info = None
        self.img_info = None
        print("[+] Đã đóng NTFS Parser")

