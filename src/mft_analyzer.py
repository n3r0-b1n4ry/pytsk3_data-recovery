"""
MFT Analyzer Module
Phân tích Master File Table để tìm và xác định các file đã xóa
"""

import pytsk3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from .file_type_detector import FileTypeDetector


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
        # Thông tin file type detection
        self.detected_extension = None  # Extension nhận diện từ magic number
        self.detected_mime_type = None  # MIME type
        self.detected_description = None  # Mô tả loại file
        self.is_extension_verified = False  # Extension có khớp với magic number không
        self.info_source = None  # Nguồn thông tin: 'MFT', 'MAGIC', 'BOTH', 'MFT_FILENAME'
        self.file_category = None  # Category: document, image, video, audio, etc.
        
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
        self.file_type_detector = FileTypeDetector()
        
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
            
            # Detect file type từ magic number (chỉ cho files, không phải directories)
            if not info.is_directory and info.size > 0:
                self._detect_file_type(entry, info)
            
            return info
            
        except Exception as e:
            print(f"[!] Lỗi khi trích xuất thông tin file '{name}': {e}")
            return None
    
    def _detect_file_type(self, entry, info: DeletedFileInfo):
        """
        Detect file type từ directory entry - ƯU TIÊN MFT
        
        Args:
            entry: Directory entry object
            info: DeletedFileInfo object cần cập nhật
        
        Logic: Tương tự _detect_file_type_from_inode, ưu tiên MFT
        """
        try:
            # Kiểm tra MFT đã có thông tin chưa
            has_mft_extension = bool(info.extension)
            
            # Mở file để đọc nội dung - TĂNG LÊN 8KB
            file_obj = entry.read_random(0, min(8192, info.size))
            
            if file_obj and len(file_obj) > 0:
                # Detect file type từ magic number
                detection_result = self.file_type_detector.detect_from_bytes(file_obj)
                
                if detection_result:
                    detected_ext, detected_mime, detected_desc = detection_result
                    
                    # Lưu thông tin detected
                    info.detected_extension = detected_ext
                    info.detected_mime_type = detected_mime
                    info.detected_description = detected_desc
                    
                    # CASE 1: MFT có extension → GIỮ NGUYÊN, chỉ verify
                    if has_mft_extension:
                        info.is_extension_verified = (info.extension.lower() == detected_ext.lower())
                        info.info_source = 'MFT'
                        
                        if not info.is_extension_verified:
                            print(f"[!] Cảnh báo: Extension không khớp cho {info.name}")
                            print(f"    MFT: {info.extension} vs Detected: {detected_ext}")
                    
                    # CASE 2: MFT không có extension → Bổ sung từ magic
                    else:
                        info.extension = detected_ext
                        info.is_extension_verified = True
                        info.info_source = 'BOTH'
                else:
                    # Không detect được, tin MFT
                    if has_mft_extension:
                        info.info_source = 'MFT'
                        
        except Exception as e:
            # Không thể đọc file hoặc detect, tin MFT
            if info.extension:
                info.info_source = 'MFT'
            pass
    
    def _detect_file_type_from_inode(self, inode: int, info: DeletedFileInfo):
        """
        Detect file type - KẾT HỢP 3 NGUỒN: MFT filename, Extension database, Magic number
        
        Args:
            inode: Inode number
            info: DeletedFileInfo object cần cập nhật
        
        Priority Logic:
            1. MFT filename → Extension database → Magic number verify
            2. Text files (txt, py, js): Dùng extension vì không có magic number
            3. Binary files: Cần magic number verify
        """
        try:
            # Kiểm tra xem MFT đã có thông tin đầy đủ chưa
            has_mft_name = not info.name.startswith('inode_')
            has_mft_extension = bool(info.extension)
            has_extension_info = bool(info.detected_mime_type)  # Đã detect từ filename
            
            # Mở file theo inode
            file_obj = self.fs_info.open_meta(inode=inode)
            
            # Đọc nội dung file - TĂNG LÊN 8KB để detect Office files
            # Office files cần nhiều hơn 512 bytes để phát hiện [Content_Types].xml
            read_size = min(8192, info.size)  # 8KB thay vì 512 bytes
            data = file_obj.read_random(0, read_size)
            
            if data and len(data) > 0:
                # Detect file type từ magic number
                magic_detection = self.file_type_detector.detect_from_bytes(data)
                
                # CASE 1: MFT có đầy đủ (tên + extension) VÀ đã có thông tin từ extension database
                if has_mft_name and has_mft_extension and has_extension_info:
                    
                    if magic_detection:
                        detected_ext, detected_mime, detected_desc = magic_detection
                        info.detected_extension = detected_ext
                        
                        # Verify: magic number khớp với extension?
                        if info.extension.lower() == detected_ext.lower():
                            # ✓ Verified: MFT extension khớp với magic number
                            info.is_extension_verified = True
                            info.info_source = 'MFT'  # MFT + verified
                            # Cập nhật description từ magic (chi tiết hơn)
                            info.detected_description = detected_desc
                        else:
                            # ⚠ Mismatch: Có thể giả mạo
                            info.is_extension_verified = False
                            info.info_source = 'MFT'  # Vẫn tin MFT, nhưng warning
                            print(f"[!] Cảnh báo: Extension không khớp cho {info.name}")
                            print(f"    MFT: {info.extension} ({info.detected_description})")
                            print(f"    Magic: {detected_ext} ({detected_desc})")
                    else:
                        # Không detect được magic (text files, etc.)
                        # → Tin tưởng extension database
                        info.is_extension_verified = False  # Không verify được
                        info.info_source = 'MFT_FILENAME'  # Từ extension database
                
                # CASE 2: MFT có tên nhưng không có extension
                elif has_mft_name and not has_mft_extension:
                    if magic_detection:
                        detected_ext, detected_mime, detected_desc = magic_detection
                        info.name = f"{info.name}.{detected_ext}"
                        info.extension = detected_ext
                        info.detected_extension = detected_ext
                        info.detected_mime_type = detected_mime
                        info.detected_description = detected_desc
                        info.is_extension_verified = True
                        info.info_source = 'BOTH'  # Tên từ MFT + extension từ magic
                        info.file_category = self.file_type_detector.get_file_category(detected_ext)
                
                # CASE 3: MFT không có tên (corrupt)
                elif not has_mft_name:
                    if magic_detection:
                        detected_ext, detected_mime, detected_desc = magic_detection
                        info.name = f"inode_{inode}.{detected_ext}"
                        info.extension = detected_ext
                        info.detected_extension = detected_ext
                        info.detected_mime_type = detected_mime
                        info.detected_description = detected_desc
                        info.is_extension_verified = True
                        info.info_source = 'MAGIC'  # Chỉ có magic
                        info.file_category = self.file_type_detector.get_file_category(detected_ext)
                
                # CASE 4: Có extension nhưng chưa có thông tin từ database
                elif has_mft_extension and not has_extension_info:
                    # Thử detect từ extension database
                    ext_detection = self.file_type_detector.detect_from_extension(info.extension)
                    if ext_detection:
                        ext, mime, desc = ext_detection
                        info.detected_mime_type = mime
                        info.detected_description = desc
                        info.file_category = self.file_type_detector.get_file_category(info.extension)
                    
                    # Verify bằng magic nếu có
                    if magic_detection:
                        detected_ext, _, detected_desc = magic_detection
                        info.detected_extension = detected_ext
                        info.is_extension_verified = (info.extension.lower() == detected_ext.lower())
                        info.info_source = 'MFT' if info.is_extension_verified else 'MFT'
                    else:
                        info.info_source = 'MFT_FILENAME'
            else:
                # Không đọc được data
                if has_mft_extension and not has_extension_info:
                    # Thử detect từ extension database
                    ext_detection = self.file_type_detector.detect_from_extension(info.extension)
                    if ext_detection:
                        ext, mime, desc = ext_detection
                        info.detected_mime_type = mime
                        info.detected_description = desc
                        info.file_category = self.file_type_detector.get_file_category(info.extension)
                        info.info_source = 'MFT_FILENAME'
                        
        except Exception as e:
            # Lỗi khi đọc file, giữ nguyên thông tin từ MFT/extension database
            if info.extension and not info.detected_mime_type:
                # Thử detect từ extension database
                ext_detection = self.file_type_detector.detect_from_extension(info.extension)
                if ext_detection:
                    ext, mime, desc = ext_detection
                    info.detected_mime_type = mime
                    info.detected_description = desc
                    info.file_category = self.file_type_detector.get_file_category(info.extension)
                    info.info_source = 'MFT_FILENAME'
            pass
    
    def _extract_filename_from_mft(self, file_meta) -> Optional[str]:
        """
        Trích xuất tên file từ MFT attributes ($FILE_NAME)
        
        Args:
            file_meta: File metadata object từ pytsk3
            
        Returns:
            Tên file hoặc None nếu không tìm thấy
        """
        try:
            # Duyệt qua các attributes của MFT entry
            for attr in file_meta:
                # $FILE_NAME attribute (type 0x30 = 48)
                if attr.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_FNAME:
                    try:
                        # Đọc attribute data
                        fname_data = attr.info.name
                        if fname_data:
                            # Decode tên file
                            filename = fname_data.decode('utf-8', errors='ignore')
                            # Bỏ qua các tên đặc biệt
                            if filename and filename not in ['.', '..']:
                                return filename
                    except:
                        continue
            
            return None
            
        except Exception as e:
            return None
    
    def _extract_file_info_from_meta(self, file_meta, inode: int) -> Optional[DeletedFileInfo]:
        """
        Trích xuất thông tin file từ MFT metadata
        
        Args:
            file_meta: File metadata object
            inode: Inode number
            
        Returns:
            DeletedFileInfo object hoặc None
        """
        try:
            info = DeletedFileInfo()
            meta = file_meta.info.meta
            
            # Thông tin cơ bản
            info.inode = inode
            info.size = meta.size
            info.is_directory = (meta.type == pytsk3.TSK_FS_META_TYPE_DIR)
            
            # Trích xuất tên file từ MFT attributes
            filename = self._extract_filename_from_mft(file_meta)
            if filename:
                info.name = filename
                # Extract extension từ tên file
                if '.' in filename and not info.is_directory:
                    info.extension = filename.split('.')[-1].lower()
                    
                    # Detect file type từ extension trong MFT filename
                    ext_detection = self.file_type_detector.detect_from_filename(filename)
                    if ext_detection:
                        ext, mime, desc = ext_detection
                        info.detected_mime_type = mime
                        info.detected_description = desc
                        info.file_category = self.file_type_detector.get_file_category(info.extension)
                        # Đánh dấu là từ MFT filename (chưa verify bằng magic)
                        info.info_source = 'MFT_FILENAME'
            else:
                info.name = f"inode_{inode}"
            
            # Timestamps
            if hasattr(meta, 'crtime') and meta.crtime:
                info.created_time = datetime.fromtimestamp(meta.crtime)
            if hasattr(meta, 'mtime') and meta.mtime:
                info.modified_time = datetime.fromtimestamp(meta.mtime)
            if hasattr(meta, 'atime') and meta.atime:
                info.accessed_time = datetime.fromtimestamp(meta.atime)
            if hasattr(meta, 'ctime') and meta.ctime:
                info.mft_modified_time = datetime.fromtimestamp(meta.ctime)
            
            # Flags
            if hasattr(meta, 'flags'):
                info.is_compressed = bool(meta.flags & pytsk3.TSK_FS_META_FLAG_COMP)
            
            return info
            
        except Exception as e:
            print(f"[!] Lỗi khi trích xuất thông tin từ MFT entry {inode}: {e}")
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
                        # Trích xuất thông tin từ MFT metadata
                        info = self._extract_file_info_from_meta(file_meta, inode)
                        
                        if info:
                            # Detect file type từ magic number
                            if not info.is_directory and info.size > 0:
                                self._detect_file_type_from_inode(inode, info)
                            
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

