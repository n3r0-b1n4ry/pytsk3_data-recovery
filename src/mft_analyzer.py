"""
MFT Analyzer Module
Phân tích Master File Table để tìm và xác định các file đã xóa
"""

import pytsk3
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class DeletedFileInfo:
    """
    Class chứa thông tin về file đã xóa
    """
    
    def __init__(self):
        self.inode = 0
        self.name = ""
        self.size = 0
        self.is_directory = False
        self.parent_inode = 0
        self.created_time = None
        self.modified_time = None
        self.accessed_time = None
        self.mft_modified_time = None
        self.is_resident = False
        self.is_encrypted = False
        self.is_compressed = False
        self.is_sparse = False
        self.extension = ""
        
    def __repr__(self):
        return f"DeletedFile(inode={self.inode}, name='{self.name}', size={self.size})"


class MFTAnalyzer:
    """
    Class để phân tích Master File Table và tìm các file đã xóa
    """
    
    def __init__(self, fs_info: pytsk3.FS_Info):
        """
        Khởi tạo MFT Analyzer
        
        Args:
            fs_info: Filesystem info object từ NTFSParser
        """
        self.fs_info = fs_info
        self.deleted_files = []
        self.total_entries = 0
        self.deleted_count = 0
        
    def traverse_directory(self, directory: pytsk3.Directory, 
                          parent_path: str = "/") -> List[DeletedFileInfo]:
        """
        Duyệt qua một directory và tìm các file đã xóa
        
        Args:
            directory: Directory object cần duyệt
            parent_path: Đường dẫn của directory cha
            
        Returns:
            Danh sách các DeletedFileInfo objects
        """
        deleted_files = []
        
        try:
            for entry in directory:
                self.total_entries += 1
                
                # Bỏ qua các entry đặc biệt
                if not hasattr(entry, 'info') or entry.info is None:
                    continue
                    
                if not hasattr(entry.info, 'meta') or entry.info.meta is None:
                    continue
                
                # Lấy tên file
                try:
                    name = entry.info.name.name.decode('utf-8')
                except:
                    name = "Unknown"
                
                # Bỏ qua . và ..
                if name in ['.', '..']:
                    continue
                
                # Kiểm tra xem file có bị xóa không
                # TSK_FS_META_FLAG_UNALLOC = file đã bị xóa (unallocated)
                is_deleted = bool(entry.info.meta.flags & pytsk3.TSK_FS_META_FLAG_UNALLOC)
                
                if is_deleted:
                    # Thu thập thông tin về file đã xóa
                    file_info = self._extract_file_info(entry, name, parent_path)
                    if file_info:
                        deleted_files.append(file_info)
                        self.deleted_count += 1
                
                # Nếu là directory và chưa bị xóa, duyệt tiếp (recursive)
                # Không duyệt vào deleted directories để tránh lỗi
                if (entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR and 
                    not is_deleted):
                    try:
                        sub_dir = entry.as_directory()
                        current_path = f"{parent_path}{name}/"
                        deleted_files.extend(
                            self.traverse_directory(sub_dir, current_path)
                        )
                    except:
                        # Một số directory không thể mở
                        pass
                        
        except Exception as e:
            print(f"[!] Lỗi khi duyệt directory {parent_path}: {e}")
        
        return deleted_files
    
    def _extract_file_info(self, entry, name: str, 
                          parent_path: str) -> Optional[DeletedFileInfo]:
        """
        Trích xuất thông tin chi tiết về file đã xóa
        
        Args:
            entry: Directory entry object
            name: Tên file
            parent_path: Đường dẫn directory cha
            
        Returns:
            DeletedFileInfo object hoặc None
        """
        try:
            info = DeletedFileInfo()
            meta = entry.info.meta
            
            # Thông tin cơ bản
            info.inode = meta.addr
            info.name = name
            info.size = meta.size
            info.is_directory = (meta.type == pytsk3.TSK_FS_META_TYPE_DIR)
            
            # Extension
            if '.' in name and not info.is_directory:
                info.extension = name.split('.')[-1].lower()
            
            # Timestamps (convert từ Unix timestamp)
            if hasattr(meta, 'crtime') and meta.crtime:
                info.created_time = datetime.fromtimestamp(meta.crtime)
            if hasattr(meta, 'mtime') and meta.mtime:
                info.modified_time = datetime.fromtimestamp(meta.mtime)
            if hasattr(meta, 'atime') and meta.atime:
                info.accessed_time = datetime.fromtimestamp(meta.atime)
            if hasattr(meta, 'ctime') and meta.ctime:
                info.mft_modified_time = datetime.fromtimestamp(meta.ctime)
            
            # Flags để kiểm tra các thuộc tính đặc biệt
            if hasattr(meta, 'flags'):
                # Check if file is compressed
                info.is_compressed = bool(meta.flags & pytsk3.TSK_FS_META_FLAG_COMP)
                # Note: Encryption và sparse detection phức tạp hơn trong NTFS
                # Cần đọc attributes để xác định chính xác
            
            return info
            
        except Exception as e:
            print(f"[!] Lỗi khi trích xuất thông tin file '{name}': {e}")
            return None
    
    def scan_for_deleted_files(self, progress_callback=None) -> List[DeletedFileInfo]:
        """
        Quét toàn bộ filesystem để tìm các file đã xóa
        
        Args:
            progress_callback: Optional callback function để báo cáo tiến trình
                             Signature: callback(current, total, message)
            
        Returns:
            Danh sách các DeletedFileInfo objects
        """
        print("[*] Bắt đầu quét filesystem để tìm file đã xóa...")
        
        self.deleted_files = []
        self.total_entries = 0
        self.deleted_count = 0
        
        try:
            # Mở root directory
            root_dir = self.fs_info.open_dir(path="/")
            
            # Duyệt toàn bộ cây thư mục
            self.deleted_files = self.traverse_directory(root_dir, "/")
            
            print(f"[+] Quét hoàn tất!")
            print(f"[+] Tổng số entries đã quét: {self.total_entries}")
            print(f"[+] Số file đã xóa tìm thấy: {self.deleted_count}")
            
            return self.deleted_files
            
        except Exception as e:
            print(f"[!] Lỗi khi quét filesystem: {e}")
            return []
    
    def scan_mft_directly(self, max_entries: int = 100000) -> List[DeletedFileInfo]:
        """
        Quét trực tiếp MFT entries (phương pháp nhanh hơn cho disk lớn)
        
        Args:
            max_entries: Số lượng MFT entries tối đa cần quét
            
        Returns:
            Danh sách các DeletedFileInfo objects
        """
        print("[*] Bắt đầu quét MFT entries trực tiếp...")
        
        self.deleted_files = []
        self.total_entries = 0
        self.deleted_count = 0
        
        try:
            # Quét từng inode (MFT entry)
            for inode in range(max_entries):
                self.total_entries += 1
                
                try:
                    # Mở file metadata theo inode
                    file_meta = self.fs_info.open_meta(inode=inode)
                    
                    # Kiểm tra xem có bị xóa không
                    is_deleted = bool(file_meta.info.meta.flags & 
                                    pytsk3.TSK_FS_META_FLAG_UNALLOC)
                    
                    if is_deleted:
                        # Tạo một entry giả để trích xuất thông tin
                        # Lưu ý: không có tên file ở đây, phải tìm từ MFT
                        info = DeletedFileInfo()
                        info.inode = inode
                        info.name = f"inode_{inode}"  # Tên tạm
                        info.size = file_meta.info.meta.size
                        info.is_directory = (file_meta.info.meta.type == 
                                           pytsk3.TSK_FS_META_TYPE_DIR)
                        
                        # Timestamps
                        if hasattr(file_meta.info.meta, 'mtime'):
                            info.modified_time = datetime.fromtimestamp(
                                file_meta.info.meta.mtime
                            )
                        
                        self.deleted_files.append(info)
                        self.deleted_count += 1
                        
                except:
                    # Entry không tồn tại hoặc không đọc được
                    pass
                
                # Progress report mỗi 1000 entries
                if inode % 1000 == 0:
                    print(f"[*] Đã quét {inode} entries, tìm thấy {self.deleted_count} file đã xóa...")
            
            print(f"[+] Quét MFT hoàn tất!")
            print(f"[+] Tổng số entries đã quét: {self.total_entries}")
            print(f"[+] Số file đã xóa tìm thấy: {self.deleted_count}")
            
            return self.deleted_files
            
        except Exception as e:
            print(f"[!] Lỗi khi quét MFT: {e}")
            return []
    
    def filter_by_extension(self, extensions: List[str]) -> List[DeletedFileInfo]:
        """
        Lọc các file đã xóa theo extension
        
        Args:
            extensions: Danh sách các extension cần lọc (vd: ['txt', 'pdf', 'jpg'])
            
        Returns:
            Danh sách file đã được lọc
        """
        extensions = [ext.lower() for ext in extensions]
        return [f for f in self.deleted_files if f.extension in extensions]
    
    def filter_by_size(self, min_size: int = 0, 
                      max_size: int = None) -> List[DeletedFileInfo]:
        """
        Lọc các file đã xóa theo kích thước
        
        Args:
            min_size: Kích thước tối thiểu (bytes)
            max_size: Kích thước tối đa (bytes), None = không giới hạn
            
        Returns:
            Danh sách file đã được lọc
        """
        filtered = [f for f in self.deleted_files if f.size >= min_size]
        if max_size is not None:
            filtered = [f for f in filtered if f.size <= max_size]
        return filtered
    
    def get_statistics(self) -> Dict:
        """
        Lấy thống kê về các file đã xóa
        
        Returns:
            Dictionary chứa thống kê
        """
        stats = {
            'total_deleted': len(self.deleted_files),
            'total_directories': sum(1 for f in self.deleted_files if f.is_directory),
            'total_files': sum(1 for f in self.deleted_files if not f.is_directory),
            'total_size': sum(f.size for f in self.deleted_files),
            'extensions': {},
        }
        
        # Thống kê theo extension
        for file_info in self.deleted_files:
            if not file_info.is_directory and file_info.extension:
                ext = file_info.extension
                if ext not in stats['extensions']:
                    stats['extensions'][ext] = {'count': 0, 'total_size': 0}
                stats['extensions'][ext]['count'] += 1
                stats['extensions'][ext]['total_size'] += file_info.size
        
        return stats

