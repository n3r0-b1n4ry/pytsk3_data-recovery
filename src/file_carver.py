"""
File Carving Module
Advanced file carving for fragmented file recovery
Inspired by pyFileCarving: https://github.com/wahlflo/pyFileCarving
"""

import os
import struct
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass


@dataclass
class FileSignature:
    """File signature definition"""
    name: str
    extension: str
    header: bytes
    footer: Optional[bytes] = None
    max_size: int = 100 * 1024 * 1024  # 100MB default
    min_size: int = 0
    
    def __repr__(self):
        return f"FileSignature({self.name}, .{self.extension})"


class FileCarver:
    """
    Advanced file carving for fragmented files
    
    This module complements the MFT-based recovery by providing
    file carving capabilities for:
    1. Files with corrupted MFT entries
    2. Heavily fragmented files
    3. Partially overwritten files
    """
    
    # File signatures database
    SIGNATURES = [
        # Images
        FileSignature("JPEG", "jpg", b'\xFF\xD8\xFF', b'\xFF\xD9', max_size=20*1024*1024),
        FileSignature("PNG", "png", b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A', b'\x49\x45\x4E\x44\xAE\x42\x60\x82'),
        FileSignature("GIF", "gif", b'GIF89a', max_size=10*1024*1024),
        FileSignature("BMP", "bmp", b'BM', max_size=50*1024*1024),
        
        # Documents
        FileSignature("PDF", "pdf", b'%PDF-', b'%%EOF', max_size=100*1024*1024),
        FileSignature("DOC", "doc", b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1', max_size=50*1024*1024),
        
        # ZIP-based (Office 2007+)
        FileSignature("ZIP", "zip", b'PK\x03\x04', b'PK\x05\x06', max_size=100*1024*1024),
        
        # Executables
        FileSignature("EXE", "exe", b'MZ', max_size=100*1024*1024),
        FileSignature("DLL", "dll", b'MZ', max_size=50*1024*1024),
        
        # Archives
        FileSignature("RAR", "rar", b'Rar!\x1A\x07', max_size=500*1024*1024),
        FileSignature("7Z", "7z", b'7z\xBC\xAF\x27\x1C', max_size=500*1024*1024),
        
        # Media
        FileSignature("MP3", "mp3", b'\xFF\xFB', max_size=50*1024*1024),
        FileSignature("MP4", "mp4", b'\x00\x00\x00\x18\x66\x74\x79\x70', max_size=1024*1024*1024),
        FileSignature("AVI", "avi", b'RIFF', max_size=1024*1024*1024),
        
        # Certificates
        FileSignature("PEM", "pem", b'-----BEGIN', b'-----END', max_size=1024*1024),
    ]
    
    def __init__(self, block_size: int = 512):
        """
        Initialize File Carver
        
        Args:
            block_size: Size of blocks to read (default: 512 bytes - sector size)
        """
        self.block_size = block_size
        self.signatures = self.SIGNATURES.copy()
        
    def add_signature(self, signature: FileSignature):
        """Add custom file signature"""
        self.signatures.append(signature)
        
    def carve_from_data(self, data: bytes, offset: int = 0) -> List[Tuple[str, bytes, int, int]]:
        """
        Carve files from raw data
        
        Args:
            data: Raw data to carve from
            offset: Starting offset in original source
            
        Returns:
            List of tuples (extension, file_data, start_offset, end_offset)
        """
        carved_files = []
        data_len = len(data)
        
        for sig in self.signatures:
            # Search for header signature
            pos = 0
            while pos < data_len:
                # Find header
                header_pos = data.find(sig.header, pos)
                if header_pos == -1:
                    break
                
                # Try to find footer if defined
                if sig.footer:
                    footer_pos = data.find(sig.footer, header_pos + len(sig.header))
                    if footer_pos != -1:
                        # Found complete file
                        end_pos = footer_pos + len(sig.footer)
                        file_data = data[header_pos:end_pos]
                        
                        # Check size constraints
                        if sig.min_size <= len(file_data) <= sig.max_size:
                            carved_files.append((
                                sig.extension,
                                file_data,
                                offset + header_pos,
                                offset + end_pos
                            ))
                        
                        pos = end_pos
                    else:
                        # Footer not found, extract up to max_size
                        end_pos = min(header_pos + sig.max_size, data_len)
                        file_data = data[header_pos:end_pos]
                        
                        if len(file_data) >= sig.min_size:
                            carved_files.append((
                                sig.extension,
                                file_data,
                                offset + header_pos,
                                offset + end_pos
                            ))
                        
                        pos = header_pos + len(sig.header)
                else:
                    # No footer defined, extract up to max_size
                    end_pos = min(header_pos + sig.max_size, data_len)
                    file_data = data[header_pos:end_pos]
                    
                    if len(file_data) >= sig.min_size:
                        carved_files.append((
                            sig.extension,
                            file_data,
                            offset + header_pos,
                            offset + end_pos
                        ))
                    
                    pos = header_pos + len(sig.header)
        
        return carved_files
    
    def validate_carved_file(self, extension: str, data: bytes) -> Tuple[bool, str]:
        """
        Validate carved file integrity
        
        Args:
            extension: File extension
            data: File data
            
        Returns:
            Tuple (is_valid, message)
        """
        if len(data) == 0:
            return False, "Empty file"
        
        # Extension-specific validation
        if extension == 'jpg':
            return self._validate_jpeg(data)
        elif extension == 'png':
            return self._validate_png(data)
        elif extension == 'pdf':
            return self._validate_pdf(data)
        elif extension == 'zip':
            return self._validate_zip(data)
        
        # Generic validation: check header presence
        for sig in self.signatures:
            if sig.extension == extension:
                if data.startswith(sig.header):
                    return True, "Header valid"
                else:
                    return False, "Invalid header"
        
        return True, "No validation available"
    
    def _validate_jpeg(self, data: bytes) -> Tuple[bool, str]:
        """Validate JPEG file"""
        if not data.startswith(b'\xFF\xD8\xFF'):
            return False, "Invalid JPEG header"
        
        if not data.endswith(b'\xFF\xD9'):
            return False, "Missing JPEG footer (incomplete)"
        
        return True, "Valid JPEG"
    
    def _validate_png(self, data: bytes) -> Tuple[bool, str]:
        """Validate PNG file"""
        if not data.startswith(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'):
            return False, "Invalid PNG header"
        
        if not data.endswith(b'\x49\x45\x4E\x44\xAE\x42\x60\x82'):
            return False, "Missing PNG footer (incomplete)"
        
        # Check IHDR chunk
        if b'IHDR' not in data[:100]:
            return False, "Missing IHDR chunk"
        
        return True, "Valid PNG"
    
    def _validate_pdf(self, data: bytes) -> Tuple[bool, str]:
        """Validate PDF file"""
        if not data.startswith(b'%PDF-'):
            return False, "Invalid PDF header"
        
        # Check for EOF marker
        if b'%%EOF' not in data[-1024:]:
            return False, "Missing PDF EOF (incomplete)"
        
        return True, "Valid PDF"
    
    def _validate_zip(self, data: bytes) -> Tuple[bool, str]:
        """Validate ZIP file"""
        if not data.startswith(b'PK\x03\x04'):
            return False, "Invalid ZIP header"
        
        # Check for central directory
        if b'PK\x01\x02' not in data:
            return False, "Missing central directory (incomplete)"
        
        return True, "Valid ZIP"
    
    def carve_fragmented_file(self, fragments: List[bytes]) -> Tuple[Optional[str], Optional[bytes]]:
        """
        Attempt to reconstruct file from fragments
        
        Args:
            fragments: List of data fragments
            
        Returns:
            Tuple (extension, reconstructed_data) or (None, None) if failed
        """
        if not fragments:
            return None, None
        
        # Try to identify file type from first fragment
        first_fragment = fragments[0]
        detected_sig = None
        
        for sig in self.signatures:
            if first_fragment.startswith(sig.header):
                detected_sig = sig
                break
        
        if not detected_sig:
            return None, None
        
        # Concatenate all fragments
        reconstructed = b''.join(fragments)
        
        # Validate
        is_valid, message = self.validate_carved_file(detected_sig.extension, reconstructed)
        
        if is_valid:
            return detected_sig.extension, reconstructed
        else:
            # Try to repair or extract valid portion
            return detected_sig.extension, reconstructed  # Return anyway, let caller decide
    
    def carve_from_clusters(self, cluster_reader, cluster_list: List[int], 
                           cluster_size: int) -> List[Tuple[str, bytes]]:
        """
        Carve files from disk clusters (for NTFS integration)
        
        Args:
            cluster_reader: Function to read cluster data: cluster_reader(cluster_num) -> bytes
            cluster_list: List of cluster numbers to read
            cluster_size: Size of each cluster in bytes
            
        Returns:
            List of tuples (extension, file_data)
        """
        # Read all clusters
        data_chunks = []
        for cluster_num in cluster_list:
            try:
                cluster_data = cluster_reader(cluster_num)
                if cluster_data:
                    data_chunks.append(cluster_data)
            except Exception as e:
                # Skip unreadable clusters
                continue
        
        if not data_chunks:
            return []
        
        # Concatenate and carve
        full_data = b''.join(data_chunks)
        carved = self.carve_from_data(full_data)
        
        # Return only extension and data
        return [(ext, data) for ext, data, _, _ in carved]
    
    def extract_file_header_info(self, data: bytes) -> Optional[Dict]:
        """
        Extract file information from header
        
        Args:
            data: File data (at least first few KB)
            
        Returns:
            Dictionary with file info or None
        """
        for sig in self.signatures:
            if data.startswith(sig.header):
                info = {
                    'type': sig.name,
                    'extension': sig.extension,
                    'header_size': len(sig.header),
                    'max_size': sig.max_size,
                }
                
                # Extension-specific info extraction
                if sig.extension == 'jpg':
                    info.update(self._extract_jpeg_info(data))
                elif sig.extension == 'png':
                    info.update(self._extract_png_info(data))
                elif sig.extension == 'pdf':
                    info.update(self._extract_pdf_info(data))
                
                return info
        
        return None
    
    def _extract_jpeg_info(self, data: bytes) -> Dict:
        """Extract JPEG metadata"""
        info = {}
        
        # Try to find JFIF marker
        if b'JFIF' in data[:20]:
            info['format'] = 'JFIF'
        elif b'Exif' in data[:20]:
            info['format'] = 'Exif'
        
        # Try to extract dimensions (simplified)
        # Full JPEG parsing is complex, this is basic
        try:
            # Look for SOF marker (Start of Frame)
            sof_markers = [b'\xFF\xC0', b'\xFF\xC1', b'\xFF\xC2']
            for marker in sof_markers:
                pos = data.find(marker)
                if pos != -1 and pos + 9 < len(data):
                    height = struct.unpack('>H', data[pos+5:pos+7])[0]
                    width = struct.unpack('>H', data[pos+7:pos+9])[0]
                    info['width'] = width
                    info['height'] = height
                    break
        except:
            pass
        
        return info
    
    def _extract_png_info(self, data: bytes) -> Dict:
        """Extract PNG metadata"""
        info = {}
        
        # PNG IHDR chunk contains dimensions
        try:
            ihdr_pos = data.find(b'IHDR')
            if ihdr_pos != -1 and ihdr_pos + 12 < len(data):
                width = struct.unpack('>I', data[ihdr_pos+4:ihdr_pos+8])[0]
                height = struct.unpack('>I', data[ihdr_pos+8:ihdr_pos+12])[0]
                info['width'] = width
                info['height'] = height
        except:
            pass
        
        return info
    
    def _extract_pdf_info(self, data: bytes) -> Dict:
        """Extract PDF metadata"""
        info = {}
        
        # Extract PDF version
        try:
            version_end = data.find(b'\n', 0, 20)
            if version_end != -1:
                version_line = data[5:version_end].decode('ascii', errors='ignore')
                info['version'] = version_line.strip()
        except:
            pass
        
        return info


class FragmentedFileRecovery:
    """
    Enhanced fragmented file recovery combining MFT data and file carving
    """
    
    def __init__(self, fs_info, fragment_handler):
        """
        Initialize
        
        Args:
            fs_info: Filesystem info from pytsk3
            fragment_handler: Existing FragmentHandler instance
        """
        self.fs_info = fs_info
        self.fragment_handler = fragment_handler
        self.carver = FileCarver(block_size=fs_info.info.block_size)
        
    def recover_fragmented_file_advanced(self, file_obj, expected_size: int) -> Tuple[Optional[bytes], Dict]:
        """
        Advanced recovery for heavily fragmented files
        
        Strategy:
        1. Try normal fragment reassembly
        2. If that fails, use file carving on fragments
        3. Validate and repair if needed
        
        Args:
            file_obj: File object from pytsk3
            expected_size: Expected file size from MFT
            
        Returns:
            Tuple (recovered_data, metadata_dict)
        """
        metadata = {
            'method': 'unknown',
            'is_complete': False,
            'fragments_count': 0,
            'validation': 'not_checked'
        }
        
        # Method 1: Standard fragment reassembly
        try:
            data = self.fragment_handler.read_fragmented_file(file_obj, expected_size)
            if data and len(data) > 0:
                metadata['method'] = 'standard_reassembly'
                metadata['fragments_count'] = self._count_fragments(file_obj)
                
                # Validate with carver
                file_info = self.carver.extract_file_header_info(data[:8192])
                if file_info:
                    is_valid, msg = self.carver.validate_carved_file(file_info['extension'], data)
                    metadata['validation'] = msg
                    metadata['is_complete'] = is_valid
                    metadata['file_type'] = file_info['type']
                    
                return data, metadata
        except Exception as e:
            metadata['error'] = str(e)
        
        # Method 2: File carving approach
        try:
            # Get data runs
            data_runs = self.fragment_handler.extract_data_runs(file_obj)
            if data_runs:
                # Read each run separately
                fragments = []
                for run in data_runs:
                    if not run.is_sparse:
                        run_data = self.fragment_handler.read_data_run(run)
                        if run_data:
                            fragments.append(run_data)
                
                metadata['fragments_count'] = len(fragments)
                
                # Try carving
                extension, reconstructed = self.carver.carve_fragmented_file(fragments)
                if reconstructed:
                    metadata['method'] = 'file_carving'
                    metadata['file_extension'] = extension
                    
                    if extension:
                        is_valid, msg = self.carver.validate_carved_file(extension, reconstructed)
                        metadata['validation'] = msg
                        metadata['is_complete'] = is_valid
                    
                    return reconstructed, metadata
        except Exception as e:
            metadata['carving_error'] = str(e)
        
        return None, metadata
    
    def _count_fragments(self, file_obj) -> int:
        """Count number of fragments"""
        try:
            data_runs = self.fragment_handler.extract_data_runs(file_obj)
            return len([r for r in data_runs if not r.is_sparse])
        except:
            return 0


# Export classes
__all__ = ['FileCarver', 'FileSignature', 'FragmentedFileRecovery']

