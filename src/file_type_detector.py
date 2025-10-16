"""
File Type Detector Module
Nhận diện loại file dựa trên magic numbers (file signatures)
"""

from typing import Optional, Dict, Tuple


class FileTypeDetector:
    """
    Class để nhận diện loại file dựa trên magic numbers và extension
    """
    
    # Extension database - mapping từ extension sang file type info
    # Format: extension -> (mime_type, description, category)
    EXTENSION_DATABASE = {
        # Documents
        'pdf': ('application/pdf', 'PDF Document', 'document'),
        'doc': ('application/msword', 'Microsoft Word Document', 'document'),
        'docx': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                'Microsoft Word Document (2007+)', 'document'),
        'xls': ('application/vnd.ms-excel', 'Microsoft Excel Spreadsheet', 'document'),
        'xlsx': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'Microsoft Excel Spreadsheet (2007+)', 'document'),
        'ppt': ('application/vnd.ms-powerpoint', 'Microsoft PowerPoint Presentation', 'document'),
        'pptx': ('application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'Microsoft PowerPoint Presentation (2007+)', 'document'),
        'odt': ('application/vnd.oasis.opendocument.text', 'OpenDocument Text', 'document'),
        'ods': ('application/vnd.oasis.opendocument.spreadsheet', 'OpenDocument Spreadsheet', 'document'),
        'txt': ('text/plain', 'Text File', 'document'),
        'rtf': ('application/rtf', 'Rich Text Format', 'document'),
        
        # Images
        'jpg': ('image/jpeg', 'JPEG Image', 'image'),
        'jpeg': ('image/jpeg', 'JPEG Image', 'image'),
        'png': ('image/png', 'PNG Image', 'image'),
        'gif': ('image/gif', 'GIF Image', 'image'),
        'bmp': ('image/bmp', 'Bitmap Image', 'image'),
        'tif': ('image/tiff', 'TIFF Image', 'image'),
        'tiff': ('image/tiff', 'TIFF Image', 'image'),
        'ico': ('image/x-icon', 'Icon File', 'image'),
        'svg': ('image/svg+xml', 'SVG Vector Image', 'image'),
        'webp': ('image/webp', 'WebP Image', 'image'),
        'psd': ('image/vnd.adobe.photoshop', 'Photoshop Document', 'image'),
        
        # Audio
        'mp3': ('audio/mpeg', 'MP3 Audio', 'audio'),
        'wav': ('audio/wav', 'WAV Audio', 'audio'),
        'flac': ('audio/flac', 'FLAC Audio', 'audio'),
        'aac': ('audio/aac', 'AAC Audio', 'audio'),
        'ogg': ('audio/ogg', 'OGG Audio', 'audio'),
        'm4a': ('audio/mp4', 'M4A Audio', 'audio'),
        'wma': ('audio/x-ms-wma', 'Windows Media Audio', 'audio'),
        
        # Video
        'mp4': ('video/mp4', 'MP4 Video', 'video'),
        'avi': ('video/x-msvideo', 'AVI Video', 'video'),
        'mkv': ('video/x-matroska', 'Matroska Video', 'video'),
        'mov': ('video/quicktime', 'QuickTime Video', 'video'),
        'wmv': ('video/x-ms-wmv', 'Windows Media Video', 'video'),
        'flv': ('video/x-flv', 'Flash Video', 'video'),
        'webm': ('video/webm', 'WebM Video', 'video'),
        'mpeg': ('video/mpeg', 'MPEG Video', 'video'),
        'mpg': ('video/mpeg', 'MPEG Video', 'video'),
        
        # Archives
        'zip': ('application/zip', 'ZIP Archive', 'archive'),
        'rar': ('application/x-rar-compressed', 'RAR Archive', 'archive'),
        '7z': ('application/x-7z-compressed', '7-Zip Archive', 'archive'),
        'tar': ('application/x-tar', 'TAR Archive', 'archive'),
        'gz': ('application/gzip', 'GZIP Archive', 'archive'),
        'bz2': ('application/x-bzip2', 'BZIP2 Archive', 'archive'),
        'xz': ('application/x-xz', 'XZ Archive', 'archive'),
        
        # Executables
        'exe': ('application/x-msdownload', 'Windows Executable', 'executable'),
        'dll': ('application/x-msdownload', 'Windows DLL', 'executable'),
        'msi': ('application/x-msi', 'Windows Installer', 'executable'),
        'apk': ('application/vnd.android.package-archive', 'Android Package', 'executable'),
        'deb': ('application/x-deb', 'Debian Package', 'executable'),
        'rpm': ('application/x-rpm', 'RPM Package', 'executable'),
        
        # Programming
        'py': ('text/x-python', 'Python Source', 'code'),
        'js': ('text/javascript', 'JavaScript Source', 'code'),
        'java': ('text/x-java-source', 'Java Source', 'code'),
        'cpp': ('text/x-c++src', 'C++ Source', 'code'),
        'c': ('text/x-csrc', 'C Source', 'code'),
        'h': ('text/x-chdr', 'C Header', 'code'),
        'cs': ('text/x-csharp', 'C# Source', 'code'),
        'php': ('text/x-php', 'PHP Source', 'code'),
        'rb': ('text/x-ruby', 'Ruby Source', 'code'),
        'go': ('text/x-go', 'Go Source', 'code'),
        'rs': ('text/x-rust', 'Rust Source', 'code'),
        'html': ('text/html', 'HTML Document', 'code'),
        'css': ('text/css', 'CSS Stylesheet', 'code'),
        'json': ('application/json', 'JSON Data', 'code'),
        'xml': ('application/xml', 'XML Document', 'code'),
        'yaml': ('text/yaml', 'YAML Configuration', 'code'),
        'yml': ('text/yaml', 'YAML Configuration', 'code'),
        
        # Database
        'db': ('application/x-sqlite3', 'Database File', 'database'),
        'sqlite': ('application/x-sqlite3', 'SQLite Database', 'database'),
        'sql': ('text/x-sql', 'SQL Script', 'database'),
    }
    
    # Dictionary chứa các magic numbers phổ biến
    # Format: magic_bytes -> (extension, mime_type, description)
    MAGIC_NUMBERS = {
        # Images
        b'\xFF\xD8\xFF': ('jpg', 'image/jpeg', 'JPEG Image'),
        b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A': ('png', 'image/png', 'PNG Image'),
        b'\x47\x49\x46\x38\x37\x61': ('gif', 'image/gif', 'GIF Image (87a)'),
        b'\x47\x49\x46\x38\x39\x61': ('gif', 'image/gif', 'GIF Image (89a)'),
        b'\x42\x4D': ('bmp', 'image/bmp', 'BMP Image'),
        b'\x49\x49\x2A\x00': ('tif', 'image/tiff', 'TIFF Image (little-endian)'),
        b'\x4D\x4D\x00\x2A': ('tif', 'image/tiff', 'TIFF Image (big-endian)'),
        b'\x00\x00\x01\x00': ('ico', 'image/x-icon', 'Icon File'),
        b'\x52\x49\x46\x46': ('webp', 'image/webp', 'WebP Image (needs WEBP check)'),
        
        # Documents
        b'\x25\x50\x44\x46': ('pdf', 'application/pdf', 'PDF Document'),
        b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1': ('doc', 'application/msword', 'MS Office Document (OLE)'),
        b'\x50\x4B\x03\x04': ('zip', 'application/zip', 'ZIP Archive / Office 2007+'),
        b'\x50\x4B\x05\x06': ('zip', 'application/zip', 'ZIP Archive (empty)'),
        b'\x50\x4B\x07\x08': ('zip', 'application/zip', 'ZIP Archive (spanned)'),
        
        # Executables
        b'\x4D\x5A': ('exe', 'application/x-msdownload', 'Windows Executable'),
        b'\x7F\x45\x4C\x46': ('elf', 'application/x-elf', 'ELF Executable'),
        
        # Archives
        b'\x52\x61\x72\x21\x1A\x07\x00': ('rar', 'application/x-rar-compressed', 'RAR Archive (v1.5+)'),
        b'\x52\x61\x72\x21\x1A\x07\x01\x00': ('rar', 'application/x-rar-compressed', 'RAR Archive (v5.0+)'),
        b'\x1F\x8B\x08': ('gz', 'application/gzip', 'GZIP Archive'),
        b'\x42\x5A\x68': ('bz2', 'application/x-bzip2', 'BZIP2 Archive'),
        b'\x37\x7A\xBC\xAF\x27\x1C': ('7z', 'application/x-7z-compressed', '7-Zip Archive'),
        
        # Media
        b'\x49\x44\x33': ('mp3', 'audio/mpeg', 'MP3 Audio (ID3v2)'),
        b'\xFF\xFB': ('mp3', 'audio/mpeg', 'MP3 Audio'),
        b'\xFF\xF3': ('mp3', 'audio/mpeg', 'MP3 Audio'),
        b'\xFF\xF2': ('mp3', 'audio/mpeg', 'MP3 Audio'),
        b'\x66\x74\x79\x70': ('mp4', 'video/mp4', 'MP4 Video (offset 4)'),
        b'\x00\x00\x00\x18\x66\x74\x79\x70': ('mp4', 'video/mp4', 'MP4 Video'),
        b'\x00\x00\x00\x20\x66\x74\x79\x70': ('mp4', 'video/mp4', 'MP4 Video'),
        b'\x52\x49\x46\x46': ('avi', 'video/x-msvideo', 'AVI Video / WAV Audio (needs check)'),
        b'\x46\x4C\x56\x01': ('flv', 'video/x-flv', 'Flash Video'),
        b'\x1A\x45\xDF\xA3': ('mkv', 'video/x-matroska', 'Matroska Video'),
        b'\x4F\x67\x67\x53': ('ogg', 'audio/ogg', 'OGG Audio'),
        
        # Database
        b'\x53\x51\x4C\x69\x74\x65\x20\x66\x6F\x72\x6D\x61\x74\x20\x33\x00': 
            ('sqlite', 'application/x-sqlite3', 'SQLite Database'),
        
        # Other
        b'\x38\x42\x50\x53': ('psd', 'image/vnd.adobe.photoshop', 'Photoshop Document'),
        b'\x4E\x45\x53\x1A': ('nes', 'application/x-nes-rom', 'NES ROM'),
    }
    
    # Extended checks cho các format cần kiểm tra thêm
    EXTENDED_CHECKS = {
        # RIFF format có thể là WebP, AVI, WAV
        b'\x52\x49\x46\x46': {
            8: {
                b'WEBP': ('webp', 'image/webp', 'WebP Image'),
                b'AVI ': ('avi', 'video/x-msvideo', 'AVI Video'),
                b'WAVE': ('wav', 'audio/wav', 'WAV Audio'),
            }
        }
    }
    
    # Office 2007+ signatures (ZIP-based formats)
    # Cần kiểm tra nội dung bên trong ZIP để phân biệt
    OFFICE_SIGNATURES = {
        'docx': [b'word/document.xml', b'word/', b'[Content_Types].xml'],
        'xlsx': [b'xl/workbook.xml', b'xl/', b'[Content_Types].xml'],
        'pptx': [b'ppt/presentation.xml', b'ppt/', b'[Content_Types].xml'],
    }
    
    def __init__(self):
        """Khởi tạo FileTypeDetector"""
        pass
    
    def _detect_zip_based_format(self, data: bytes) -> Optional[Tuple[str, str, str]]:
        """
        Phân biệt các format dựa trên ZIP (docx, xlsx, pptx, jar, apk, zip)
        
        Args:
            data: Dữ liệu bytes (ít nhất 512 bytes)
            
        Returns:
            Tuple (extension, mime_type, description) hoặc None
        """
        if len(data) < 30:
            return None
        
        # Kiểm tra ZIP signature
        if not data.startswith(b'\x50\x4B\x03\x04') and not data.startswith(b'\x50\x4B\x05\x06'):
            return None
        
        # Priority 1: Microsoft Office 2007+ formats
        # Check cho [Content_Types].xml - đặc trưng của Office files
        if b'[Content_Types].xml' in data:
            # DOCX: chứa word/
            if b'word/' in data or b'word/document.xml' in data:
                return ('docx', 
                       'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                       'Microsoft Word Document (2007+)')
            
            # XLSX: chứa xl/
            elif b'xl/' in data or b'xl/workbook.xml' in data:
                return ('xlsx',
                       'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                       'Microsoft Excel Spreadsheet (2007+)')
            
            # PPTX: chứa ppt/
            elif b'ppt/' in data or b'ppt/presentation.xml' in data:
                return ('pptx',
                       'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                       'Microsoft PowerPoint Presentation (2007+)')
        
        # Priority 2: OpenDocument formats
        if b'mimetype' in data[:100]:
            if b'application/vnd.oasis.opendocument.text' in data:
                return ('odt', 'application/vnd.oasis.opendocument.text', 'OpenDocument Text')
            elif b'application/vnd.oasis.opendocument.spreadsheet' in data:
                return ('ods', 'application/vnd.oasis.opendocument.spreadsheet', 'OpenDocument Spreadsheet')
            elif b'application/vnd.oasis.opendocument.presentation' in data:
                return ('odp', 'application/vnd.oasis.opendocument.presentation', 'OpenDocument Presentation')
        
        # Priority 3: Android APK
        if b'AndroidManifest.xml' in data:
            return ('apk', 'application/vnd.android.package-archive', 'Android Package')
        
        # Priority 4: Java JAR
        if b'META-INF/' in data or b'META-INF/MANIFEST.MF' in data:
            return ('jar', 'application/java-archive', 'Java Archive')
        
        # Priority 5: EPUB (eBook)
        if b'mimetype' in data[:100] and b'application/epub+zip' in data:
            return ('epub', 'application/epub+zip', 'EPUB eBook')
        
        # Default: Plain ZIP
        return ('zip', 'application/zip', 'ZIP Archive')
    
    def _parse_zip_filenames(self, data: bytes) -> list:
        """
        Parse filenames từ ZIP central directory
        
        Args:
            data: ZIP file data
            
        Returns:
            List các filenames trong ZIP
        """
        filenames = []
        
        try:
            # Tìm ZIP local file headers (0x50 0x4B 0x03 0x04)
            offset = 0
            while offset < len(data) - 30:
                if data[offset:offset+4] == b'\x50\x4B\x03\x04':
                    # Local file header found
                    # Offset 26-27: filename length
                    if offset + 30 <= len(data):
                        filename_len = int.from_bytes(data[offset+26:offset+28], 'little')
                        extra_len = int.from_bytes(data[offset+28:offset+30], 'little')
                        
                        # Filename starts at offset 30
                        filename_start = offset + 30
                        filename_end = filename_start + filename_len
                        
                        if filename_end <= len(data):
                            try:
                                filename = data[filename_start:filename_end].decode('utf-8', errors='ignore')
                                filenames.append(filename)
                            except:
                                pass
                        
                        # Move to next header
                        offset = filename_end + extra_len
                    else:
                        break
                else:
                    offset += 1
        except Exception as e:
            pass
        
        return filenames
    
    def detect_from_bytes(self, data: bytes, max_check_size: int = 8192) -> Optional[Tuple[str, str, str]]:
        """
        Nhận diện loại file từ dữ liệu bytes
        
        Args:
            data: Dữ liệu bytes của file (ít nhất 8KB để detect Office files)
            max_check_size: Kích thước tối đa để kiểm tra (default 8KB)
            
        Returns:
            Tuple (extension, mime_type, description) hoặc None nếu không nhận diện được
        """
        if not data or len(data) == 0:
            return None
        
        # Giới hạn kích thước kiểm tra
        check_data = data[:max_check_size] if len(data) > max_check_size else data
        
        # SPECIAL CHECK: ZIP-based formats (DOCX, XLSX, PPTX, JAR, APK, ZIP)
        # Phải check trước vì cần phân biệt chính xác
        if check_data.startswith(b'\x50\x4B\x03\x04') or check_data.startswith(b'\x50\x4B\x05\x06') or check_data.startswith(b'\x50\x4B\x07\x08'):
            zip_result = self._detect_zip_based_format(check_data)
            if zip_result:
                return zip_result
        
        # Kiểm tra các magic numbers theo thứ tự từ dài đến ngắn
        # để tránh false positive
        sorted_magics = sorted(self.MAGIC_NUMBERS.items(), 
                              key=lambda x: len(x[0]), 
                              reverse=True)
        
        for magic_bytes, file_info in sorted_magics:
            if check_data.startswith(magic_bytes):
                # SKIP ZIP magic vì đã xử lý ở trên
                if magic_bytes == b'\x50\x4B\x03\x04' or magic_bytes == b'\x50\x4B\x05\x06' or magic_bytes == b'\x50\x4B\x07\x08':
                    continue
                
                # Kiểm tra xem có cần extended check không
                if magic_bytes in self.EXTENDED_CHECKS:
                    extended_result = self._extended_check(check_data, magic_bytes)
                    if extended_result:
                        return extended_result
                
                return file_info
        
        return None
    
    def _extended_check(self, data: bytes, magic_bytes: bytes) -> Optional[Tuple[str, str, str]]:
        """
        Thực hiện kiểm tra mở rộng cho các format đặc biệt
        
        Args:
            data: Dữ liệu bytes
            magic_bytes: Magic bytes đã match
            
        Returns:
            Tuple (extension, mime_type, description) hoặc None
        """
        checks = self.EXTENDED_CHECKS.get(magic_bytes, {})
        
        # Kiểm tra tại các offset cụ thể
        for offset, patterns in checks.items():
            if offset == 'contains':
                # Kiểm tra toàn bộ data
                for pattern, file_info in patterns.items():
                    if pattern in data:
                        return file_info
            elif isinstance(offset, int) and len(data) > offset:
                # Kiểm tra tại offset cụ thể
                for pattern, file_info in patterns.items():
                    if data[offset:offset+len(pattern)] == pattern:
                        return file_info
        
        return None
    
    def detect_from_file_object(self, file_obj) -> Optional[Tuple[str, str, str]]:
        """
        Nhận diện loại file từ file object (pytsk3 file)
        
        Args:
            file_obj: PyTSK3 file object
            
        Returns:
            Tuple (extension, mime_type, description) hoặc None
        """
        try:
            # Đọc 512 bytes đầu tiên
            file_obj.seek(0)
            data = file_obj.read_random(0, 512)
            
            if data:
                return self.detect_from_bytes(data)
        except Exception as e:
            print(f"[!] Lỗi khi detect file type: {e}")
        
        return None
    
    def get_extension_from_detection(self, data: bytes) -> Optional[str]:
        """
        Lấy extension từ kết quả detection
        
        Args:
            data: Dữ liệu bytes
            
        Returns:
            Extension string hoặc None
        """
        result = self.detect_from_bytes(data)
        return result[0] if result else None
    
    def get_mime_type_from_detection(self, data: bytes) -> Optional[str]:
        """
        Lấy MIME type từ kết quả detection
        
        Args:
            data: Dữ liệu bytes
            
        Returns:
            MIME type string hoặc None
        """
        result = self.detect_from_bytes(data)
        return result[1] if result else None
    
    def get_all_supported_extensions(self) -> list:
        """
        Lấy danh sách tất cả extensions được hỗ trợ
        
        Returns:
            List các extension strings
        """
        extensions = set()
        for file_info in self.MAGIC_NUMBERS.values():
            extensions.add(file_info[0])
        
        # Thêm extensions từ extended checks
        for checks in self.EXTENDED_CHECKS.values():
            for patterns in checks.values():
                if isinstance(patterns, dict):
                    for file_info in patterns.values():
                        extensions.add(file_info[0])
        
        return sorted(list(extensions))
    
    def validate_extension(self, data: bytes, claimed_extension: str) -> bool:
        """
        Kiểm tra xem extension có khớp với nội dung file không
        
        Args:
            data: Dữ liệu bytes
            claimed_extension: Extension được claim
            
        Returns:
            True nếu khớp, False nếu không khớp
        """
        detected = self.detect_from_bytes(data)
        if not detected:
            # Không detect được, không thể xác thực
            return False
        
        detected_ext = detected[0]
        claimed_ext = claimed_extension.lower().lstrip('.')
        
        return detected_ext == claimed_ext
    
    def detect_from_extension(self, extension: str) -> Optional[Tuple[str, str, str]]:
        """
        Nhận diện file type từ extension (lấy từ MFT filename)
        
        Args:
            extension: Extension của file (vd: 'pdf', 'jpg')
            
        Returns:
            Tuple (extension, mime_type, description) hoặc None nếu không nhận diện được
        """
        if not extension:
            return None
        
        # Normalize extension
        ext = extension.lower().lstrip('.')
        
        # Tìm trong database
        if ext in self.EXTENSION_DATABASE:
            mime_type, description, category = self.EXTENSION_DATABASE[ext]
            return (ext, mime_type, description)
        
        return None
    
    def detect_from_filename(self, filename: str) -> Optional[Tuple[str, str, str]]:
        """
        Nhận diện file type từ filename (từ MFT)
        
        Args:
            filename: Tên file đầy đủ (vd: 'document.pdf')
            
        Returns:
            Tuple (extension, mime_type, description) hoặc None
        """
        if not filename or '.' not in filename:
            return None
        
        # Extract extension từ filename
        extension = filename.split('.')[-1]
        return self.detect_from_extension(extension)
    
    def get_file_category(self, extension: str) -> Optional[str]:
        """
        Lấy category của file từ extension
        
        Args:
            extension: Extension của file
            
        Returns:
            Category string ('document', 'image', 'video', etc.) hoặc None
        """
        if not extension:
            return None
        
        ext = extension.lower().lstrip('.')
        if ext in self.EXTENSION_DATABASE:
            return self.EXTENSION_DATABASE[ext][2]  # category
        
        return None

