"""
Fragment Handler Module
Xử lý file fragmentation - ghép các fragment của file lại với nhau
"""

import pytsk3
from typing import List, Tuple, Optional


class DataRun:
    """
    Class đại diện cho một data run (một đoạn liên tục của file trên disk)
    """
    
    def __init__(self, offset: int, length: int, is_sparse: bool = False):
        """
        Args:
            offset: Offset trên disk (theo clusters)
            length: Độ dài (theo clusters)
            is_sparse: Có phải sparse run không (chỉ chứa zeros)
        """
        self.offset = offset
        self.length = length
        self.is_sparse = is_sparse
        
    def __repr__(self):
        return f"DataRun(offset={self.offset}, length={self.length}, sparse={self.is_sparse})"


class FragmentHandler:
    """
    Class để xử lý fragmented files - file bị phân mảnh trên nhiều vị trí
    """
    
    def __init__(self, fs_info: pytsk3.FS_Info):
        """
        Khởi tạo Fragment Handler
        
        Args:
            fs_info: Filesystem info object
        """
        self.fs_info = fs_info
        self.block_size = fs_info.info.block_size
        
    def extract_data_runs(self, file_obj: pytsk3.File) -> List[DataRun]:
        """
        Trích xuất data runs từ file object
        
        Args:
            file_obj: File object từ pytsk3
            
        Returns:
            Danh sách DataRun objects
        """
        data_runs = []
        
        try:
            # Duyệt qua các attributes của file
            for attr in file_obj:
                # Tìm $DATA attribute (chứa nội dung file)
                if attr.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_DATA:
                    
                    # Kiểm tra xem data có resident không
                    # Resident = data được lưu trực tiếp trong MFT entry
                    if attr.info.flags & pytsk3.TSK_FS_ATTR_RES:
                        # Resident data - không có runs
                        continue
                    
                    # Non-resident data - có data runs
                    # Duyệt qua các runs
                    for run in attr:
                        if run is None:
                            continue
                            
                        offset = run.addr  # Cluster address
                        length = run.len   # Length in clusters
                        
                        # Sparse run có offset = 0
                        is_sparse = (offset == 0)
                        
                        data_run = DataRun(offset, length, is_sparse)
                        data_runs.append(data_run)
                        
        except Exception as e:
            print(f"[!] Lỗi khi extract data runs: {e}")
        
        return data_runs
    
    def read_fragmented_file(self, file_obj: pytsk3.File, 
                            max_size: Optional[int] = None) -> Optional[bytes]:
        """
        Đọc toàn bộ nội dung của fragmented file
        
        Args:
            file_obj: File object từ pytsk3
            max_size: Giới hạn kích thước đọc (bytes), None = đọc hết
            
        Returns:
            Nội dung file dưới dạng bytes, hoặc None nếu lỗi
        """
        try:
            # Lấy kích thước file
            file_size = file_obj.info.meta.size
            
            # Giới hạn kích thước nếu cần
            if max_size is not None and file_size > max_size:
                read_size = max_size
            else:
                read_size = file_size
            
            # Đọc file content
            # PyTSK3 tự động xử lý fragmentation
            offset = 0
            file_data = bytearray()
            chunk_size = 1024 * 1024  # 1MB chunks
            
            while offset < read_size:
                # Tính số bytes cần đọc
                remaining = read_size - offset
                to_read = min(chunk_size, remaining)
                
                # Đọc chunk
                chunk = file_obj.read_random(offset, to_read)
                if not chunk:
                    break
                    
                file_data.extend(chunk)
                offset += len(chunk)
            
            return bytes(file_data)
            
        except Exception as e:
            print(f"[!] Lỗi khi đọc fragmented file: {e}")
            return None
    
    def is_file_fragmented(self, file_obj: pytsk3.File) -> Tuple[bool, int]:
        """
        Kiểm tra xem file có bị phân mảnh không
        
        Args:
            file_obj: File object từ pytsk3
            
        Returns:
            Tuple (is_fragmented, fragment_count)
        """
        try:
            data_runs = self.extract_data_runs(file_obj)
            
            # Nếu có nhiều hơn 1 data run (non-sparse), file bị phân mảnh
            non_sparse_runs = [r for r in data_runs if not r.is_sparse]
            fragment_count = len(non_sparse_runs)
            
            is_fragmented = fragment_count > 1
            
            return is_fragmented, fragment_count
            
        except Exception as e:
            print(f"[!] Lỗi khi kiểm tra fragmentation: {e}")
            return False, 0
    
    def read_data_run(self, data_run: DataRun) -> Optional[bytes]:
        """
        Đọc nội dung của một data run cụ thể
        
        Args:
            data_run: DataRun object cần đọc
            
        Returns:
            Nội dung của data run dưới dạng bytes
        """
        try:
            if data_run.is_sparse:
                # Sparse run chỉ chứa zeros
                return b'\x00' * (data_run.length * self.block_size)
            
            # Tính offset theo bytes
            byte_offset = data_run.offset * self.block_size
            byte_length = data_run.length * self.block_size
            
            # Đọc data từ filesystem
            # Lưu ý: đây là low-level read, cần cẩn thận
            data = bytearray()
            for i in range(data_run.length):
                block_addr = data_run.offset + i
                try:
                    block_data = self.fs_info.read_block(block_addr)
                    data.extend(block_data)
                except:
                    # Không đọc được block, điền zeros
                    data.extend(b'\x00' * self.block_size)
            
            return bytes(data)
            
        except Exception as e:
            print(f"[!] Lỗi khi đọc data run: {e}")
            return None
    
    def reconstruct_file_from_runs(self, data_runs: List[DataRun], 
                                  file_size: int) -> Optional[bytes]:
        """
        Tái tạo file từ các data runs
        
        Args:
            data_runs: Danh sách các DataRun objects
            file_size: Kích thước thực của file (bytes)
            
        Returns:
            Nội dung file đã được tái tạo
        """
        try:
            file_data = bytearray()
            
            # Đọc từng data run và ghép lại
            for data_run in data_runs:
                run_data = self.read_data_run(data_run)
                if run_data:
                    file_data.extend(run_data)
            
            # Cắt về đúng kích thước file
            # (data runs thường lớn hơn file size thực tế)
            if len(file_data) > file_size:
                file_data = file_data[:file_size]
            
            return bytes(file_data)
            
        except Exception as e:
            print(f"[!] Lỗi khi reconstruct file: {e}")
            return None
    
    def get_fragmentation_info(self, file_obj: pytsk3.File) -> dict:
        """
        Lấy thông tin chi tiết về fragmentation của file
        
        Args:
            file_obj: File object từ pytsk3
            
        Returns:
            Dictionary chứa thông tin fragmentation
        """
        try:
            data_runs = self.extract_data_runs(file_obj)
            is_frag, frag_count = self.is_file_fragmented(file_obj)
            
            total_clusters = sum(r.length for r in data_runs)
            sparse_clusters = sum(r.length for r in data_runs if r.is_sparse)
            
            info = {
                'is_fragmented': is_frag,
                'fragment_count': frag_count,
                'total_runs': len(data_runs),
                'total_clusters': total_clusters,
                'sparse_clusters': sparse_clusters,
                'data_clusters': total_clusters - sparse_clusters,
                'total_size_bytes': total_clusters * self.block_size,
                'file_size_bytes': file_obj.info.meta.size,
            }
            
            return info
            
        except Exception as e:
            print(f"[!] Lỗi khi lấy fragmentation info: {e}")
            return {}
    
    def check_data_integrity(self, file_data: bytes, 
                           expected_size: int) -> Tuple[bool, str]:
        """
        Kiểm tra tính toàn vẹn của dữ liệu đã đọc
        
        Args:
            file_data: Dữ liệu file đã đọc
            expected_size: Kích thước mong đợi
            
        Returns:
            Tuple (is_valid, message)
        """
        if file_data is None:
            return False, "Không có dữ liệu"
        
        actual_size = len(file_data)
        
        if actual_size == 0:
            return False, "File rỗng"
        
        if actual_size < expected_size:
            return False, f"Thiếu dữ liệu: {actual_size}/{expected_size} bytes"
        
        if actual_size > expected_size:
            return True, f"Có thêm {actual_size - expected_size} bytes (đã cắt)"
        
        return True, "Dữ liệu toàn vẹn"

