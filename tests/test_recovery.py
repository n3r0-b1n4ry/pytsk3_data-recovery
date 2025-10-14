"""
Unit Tests cho NTFS File Recovery Tool
"""

import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mft_analyzer import DeletedFileInfo, MFTAnalyzer
from src.fragment_handler import DataRun, FragmentHandler
from src.file_recovery import RecoveryStats, FileRecovery


class TestDeletedFileInfo(unittest.TestCase):
    """Test DeletedFileInfo class"""
    
    def test_init(self):
        """Test khởi tạo DeletedFileInfo"""
        info = DeletedFileInfo()
        self.assertEqual(info.inode, 0)
        self.assertEqual(info.name, "")
        self.assertEqual(info.size, 0)
        self.assertFalse(info.is_directory)
    
    def test_repr(self):
        """Test __repr__ method"""
        info = DeletedFileInfo()
        info.inode = 123
        info.name = "test.txt"
        info.size = 1024
        
        repr_str = repr(info)
        self.assertIn("123", repr_str)
        self.assertIn("test.txt", repr_str)


class TestDataRun(unittest.TestCase):
    """Test DataRun class"""
    
    def test_init(self):
        """Test khởi tạo DataRun"""
        run = DataRun(offset=100, length=10, is_sparse=False)
        self.assertEqual(run.offset, 100)
        self.assertEqual(run.length, 10)
        self.assertFalse(run.is_sparse)
    
    def test_sparse_run(self):
        """Test sparse data run"""
        run = DataRun(offset=0, length=5, is_sparse=True)
        self.assertTrue(run.is_sparse)


class TestRecoveryStats(unittest.TestCase):
    """Test RecoveryStats class"""
    
    def test_init(self):
        """Test khởi tạo RecoveryStats"""
        stats = RecoveryStats()
        self.assertEqual(stats.total_files, 0)
        self.assertEqual(stats.recovered_files, 0)
        self.assertEqual(stats.failed_files, 0)
    
    def test_add_success(self):
        """Test thêm recovery thành công"""
        stats = RecoveryStats()
        stats.add_success(1024)
        
        self.assertEqual(stats.recovered_files, 1)
        self.assertEqual(stats.total_bytes_recovered, 1024)
    
    def test_add_failure(self):
        """Test thêm recovery thất bại"""
        stats = RecoveryStats()
        stats.add_failure("Test error")
        
        self.assertEqual(stats.failed_files, 1)
        self.assertEqual(len(stats.errors), 1)
    
    def test_success_rate(self):
        """Test tính toán success rate"""
        stats = RecoveryStats()
        stats.total_files = 10
        stats.recovered_files = 9
        
        self.assertEqual(stats.get_success_rate(), 90.0)
    
    def test_success_rate_zero_files(self):
        """Test success rate khi không có file"""
        stats = RecoveryStats()
        self.assertEqual(stats.get_success_rate(), 0.0)


class TestMFTAnalyzer(unittest.TestCase):
    """Test MFTAnalyzer class"""
    
    def setUp(self):
        """Setup mock filesystem"""
        self.mock_fs = Mock()
        self.analyzer = MFTAnalyzer(self.mock_fs)
    
    def test_init(self):
        """Test khởi tạo MFTAnalyzer"""
        self.assertIsNotNone(self.analyzer)
        self.assertEqual(self.analyzer.deleted_count, 0)
    
    def test_filter_by_extension(self):
        """Test lọc file theo extension"""
        # Tạo test data
        file1 = DeletedFileInfo()
        file1.extension = "txt"
        
        file2 = DeletedFileInfo()
        file2.extension = "pdf"
        
        file3 = DeletedFileInfo()
        file3.extension = "jpg"
        
        self.analyzer.deleted_files = [file1, file2, file3]
        
        # Lọc chỉ txt và pdf
        filtered = self.analyzer.filter_by_extension(['txt', 'pdf'])
        
        self.assertEqual(len(filtered), 2)
        self.assertIn(file1, filtered)
        self.assertIn(file2, filtered)
        self.assertNotIn(file3, filtered)
    
    def test_filter_by_size(self):
        """Test lọc file theo size"""
        file1 = DeletedFileInfo()
        file1.size = 100
        
        file2 = DeletedFileInfo()
        file2.size = 1000
        
        file3 = DeletedFileInfo()
        file3.size = 10000
        
        self.analyzer.deleted_files = [file1, file2, file3]
        
        # Lọc size từ 500 đến 5000
        filtered = self.analyzer.filter_by_size(min_size=500, max_size=5000)
        
        self.assertEqual(len(filtered), 1)
        self.assertIn(file2, filtered)
    
    def test_get_statistics(self):
        """Test lấy thống kê"""
        file1 = DeletedFileInfo()
        file1.is_directory = False
        file1.size = 1000
        file1.extension = "txt"
        
        file2 = DeletedFileInfo()
        file2.is_directory = True
        file2.size = 0
        
        self.analyzer.deleted_files = [file1, file2]
        
        stats = self.analyzer.get_statistics()
        
        self.assertEqual(stats['total_deleted'], 2)
        self.assertEqual(stats['total_files'], 1)
        self.assertEqual(stats['total_directories'], 1)
        self.assertIn('txt', stats['extensions'])


class TestFragmentHandler(unittest.TestCase):
    """Test FragmentHandler class"""
    
    def setUp(self):
        """Setup mock filesystem"""
        self.mock_fs = Mock()
        self.mock_fs.info.block_size = 4096
        self.handler = FragmentHandler(self.mock_fs)
    
    def test_init(self):
        """Test khởi tạo FragmentHandler"""
        self.assertIsNotNone(self.handler)
        self.assertEqual(self.handler.block_size, 4096)
    
    def test_is_file_fragmented(self):
        """Test kiểm tra file fragmentation"""
        # Mock file object
        mock_file = Mock()
        
        # Mock data runs - 2 non-sparse runs = fragmented
        mock_attr = Mock()
        mock_attr.info.type = 128  # TSK_FS_ATTR_TYPE_NTFS_DATA
        mock_attr.info.flags = 0  # Non-resident
        
        mock_run1 = Mock()
        mock_run1.addr = 100
        mock_run1.len = 10
        
        mock_run2 = Mock()
        mock_run2.addr = 200
        mock_run2.len = 5
        
        mock_attr.__iter__ = Mock(return_value=iter([mock_run1, mock_run2]))
        mock_file.__iter__ = Mock(return_value=iter([mock_attr]))
        
        is_frag, count = self.handler.is_file_fragmented(mock_file)
        
        self.assertTrue(is_frag)
        self.assertEqual(count, 2)


class TestFileRecovery(unittest.TestCase):
    """Test FileRecovery class"""
    
    def setUp(self):
        """Setup mock objects"""
        self.mock_fs = Mock()
        self.mock_fs.info.block_size = 4096
        self.output_dir = "./test_output"
        self.recovery = FileRecovery(self.mock_fs, self.output_dir)
    
    def tearDown(self):
        """Cleanup test output directory"""
        import shutil
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
    
    def test_init(self):
        """Test khởi tạo FileRecovery"""
        self.assertIsNotNone(self.recovery)
        self.assertTrue(os.path.exists(self.output_dir))
    
    def test_sanitize_filename(self):
        """Test sanitize filename"""
        # Test invalid characters
        sanitized = self.recovery._sanitize_filename("test<file>name.txt", 123)
        self.assertNotIn('<', sanitized)
        self.assertNotIn('>', sanitized)
        
        # Test empty filename
        sanitized = self.recovery._sanitize_filename("", 123)
        self.assertIn("123", sanitized)
    
    def test_format_size(self):
        """Test format file size"""
        self.assertEqual(self.recovery._format_size(500), "500.00 B")
        self.assertEqual(self.recovery._format_size(1024), "1.00 KB")
        self.assertEqual(self.recovery._format_size(1024*1024), "1.00 MB")
    
    def test_get_unique_path(self):
        """Test tạo unique path"""
        # Tạo file test
        test_path = os.path.join(self.output_dir, "test.txt")
        with open(test_path, 'w') as f:
            f.write("test")
        
        # Get unique path
        unique_path = self.recovery._get_unique_path(test_path)
        
        self.assertNotEqual(test_path, unique_path)
        self.assertIn("_1", unique_path)


def run_tests():
    """Chạy tất cả tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()

