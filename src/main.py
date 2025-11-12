"""
Main Entry Point
Main file to run NTFS File Recovery Tool
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
        description='NTFS File Recovery Tool - Recover deleted files from NTFS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan and display list of deleted files
  python3 -m src.main disk.img --scan-only

  # Recover all deleted files
  python3 -m src.main disk.img -o ./recovered

  # Recover only PDF and DOCX files
  python3 -m src.main disk.img -e pdf,docx -o ./recovered

  # Recover file by inode
  python3 -m src.main disk.img -i 12345 -o ./recovered
        """
    )
    
    parser.add_argument(
        'image',
        help='Path to NTFS disk image'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='./recovered',
        help='Output directory for recovered files (default: ./recovered)'
    )
    
    parser.add_argument(
        '-e', '--extensions',
        help='Filter by extension, comma-separated (e.g., txt,pdf,jpg)'
    )
    
    parser.add_argument(
        '-s', '--min-size',
        type=int,
        default=0,
        help='Minimum file size (bytes)'
    )
    
    parser.add_argument(
        '-m', '--max-size',
        type=int,
        help='Maximum file size (bytes)'
    )
    
    parser.add_argument(
        '-i', '--inode',
        type=int,
        help='Recover file by specific inode'
    )
    
    parser.add_argument(
        '--scan-only',
        action='store_true',
        help='Only scan and display file list, do not recover'
    )
    
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bar'
    )
    
    parser.add_argument(
        '--max-files',
        type=int,
        help='Limit number of files to recover'
    )
    
    parser.add_argument(
        '--report',
        help='Path to recovery report file'
    )
    
    parser.add_argument(
        '--use-carving',
        action='store_true',
        help='Enable advanced file carving for heavily fragmented files'
    )
    
    return parser.parse_args()


def scan_deleted_files(parser: NTFSParser, ui: UserInterface) -> List[DeletedFileInfo]:
    """
    Scan and find deleted files
    
    Args:
        parser: NTFSParser object
        ui: UserInterface object
        
    Returns:
        List of DeletedFileInfo objects
    """
    ui.print_section("SCANNING FILESYSTEM")
    
    # Create MFT Analyzer
    analyzer = MFTAnalyzer(parser.get_filesystem())
    
    # Scan deleted files by directly scanning MFT entries
    ui.print_info("Scanning MFT for deleted files...")
    deleted_files = analyzer.scan_mft_directly()
    
    if not deleted_files:
        ui.print_warning("No deleted files found")
        return []
    
    # Display statistics
    stats = analyzer.get_statistics()
    ui.display_statistics(stats)
    
    return deleted_files


def filter_files(deleted_files: List[DeletedFileInfo], 
                args, ui: UserInterface) -> List[DeletedFileInfo]:
    """
    Filter file list by criteria
    
    Args:
        deleted_files: Initial file list
        args: Command line arguments
        ui: UserInterface object
        
    Returns:
        Filtered file list
    """
    filtered = deleted_files
    
    # Filter by extension
    if args.extensions:
        extensions = [ext.strip().lower() for ext in args.extensions.split(',')]
        filtered = [f for f in filtered if f.extension.lower() in extensions]
        ui.print_info(f"Filter by extension {extensions}: {len(filtered)} files remaining")
    
    # Filter by size
    if args.min_size > 0:
        filtered = [f for f in filtered if f.size >= args.min_size]
        ui.print_info(f"Filter by min size {args.min_size} bytes: {len(filtered)} files remaining")
    
    if args.max_size:
        filtered = [f for f in filtered if f.size <= args.max_size]
        ui.print_info(f"Filter by max size {args.max_size} bytes: {len(filtered)} files remaining")
    
    # Limit count
    if args.max_files and len(filtered) > args.max_files:
        filtered = filtered[:args.max_files]
        ui.print_info(f"Limit to first {args.max_files} files")
    
    # Filter out directories
    filtered = [f for f in filtered if not f.is_directory]
    
    return filtered


def recover_files(parser: NTFSParser, deleted_files: List[DeletedFileInfo],
                 args, ui: UserInterface):
    """
    Perform file recovery
    
    Args:
        parser: NTFSParser object
        deleted_files: List of files to recover
        args: Command line arguments
        ui: UserInterface object
    """
    ui.print_section("FILE RECOVERY")
    
    if not deleted_files:
        ui.print_warning("No files to recover")
        return
    
    # Display file list
    ui.display_deleted_files_table(deleted_files, max_display=50)
    
    # Confirmation
    if not args.scan_only:
        total_size = sum(f.size for f in deleted_files)
        size_str = ui._format_size(total_size)
        
        print(f"\n{ui._format_size(total_size)} will be recovered to directory: {args.output}")
        
        if not ui.confirm_action(f"Do you want to recover {len(deleted_files)} files?", default=True):
            ui.print_warning("Recovery cancelled")
            return
    else:
        ui.print_info("Scan-only mode: not recovering files")
        return
    
    # Create FileRecovery object
    recovery = FileRecovery(parser.get_filesystem(), args.output, use_carving=args.use_carving)
    
    # Create progress callback
    if not args.no_progress:
        progress_bar = ui.create_progress_bar(len(deleted_files), "Recovering")
        
        def progress_callback(current, total, filename):
            progress_bar.update(1)
            progress_bar.set_postfix_str(filename[:30])
        
        # Recover with progress bar
        stats = recovery.recover_files(deleted_files, progress_callback)
        progress_bar.close()
    else:
        # Recover without progress bar
        stats = recovery.recover_files(deleted_files)
    
    # Display results
    ui.display_recovery_stats(stats)
    
    # Create report if requested
    if args.report:
        recovery.create_recovery_report(args.report)


def recover_by_inode(parser: NTFSParser, inode: int, 
                    args, ui: UserInterface):
    """
    Recover file by specific inode
    
    Args:
        parser: NTFSParser object
        inode: Inode number
        args: Command line arguments
        ui: UserInterface object
    """
    ui.print_section(f"RECOVER FILE BY INODE {inode}")
    
    # Create FileRecovery object
    recovery = FileRecovery(parser.get_filesystem(), args.output, use_carving=args.use_carving)
    
    # Create output filename
    output_name = ui.prompt_input(
        "Enter output filename", 
        default=f"recovered_inode_{inode}"
    )
    
    # Recover
    ui.print_info(f"Recovering inode {inode}...")
    success = recovery.recover_by_inode(inode, output_name)
    
    if success:
        ui.print_success(f"File recovered to: {os.path.join(args.output, output_name)}")
    else:
        ui.print_error("Recovery failed")


def main():
    """
    Main function
    """
    # Parse arguments
    args = parse_arguments()
    
    # Create UI
    ui = UserInterface()
    ui.print_banner()
    
    # Check if image file exists
    if not os.path.exists(args.image):
        ui.print_error(f"Disk image not found: {args.image}")
        sys.exit(1)
    
    try:
        # Initialize NTFS Parser
        ui.print_section("INITIALIZATION")
        ui.print_info(f"Opening disk image: {args.image}")
        
        parser = NTFSParser(args.image)
        
        if not parser.initialize():
            ui.print_error("Unable to initialize NTFS parser")
            sys.exit(1)
        
        # If specific inode specified
        if args.inode:
            recover_by_inode(parser, args.inode, args, ui)
            parser.close()
            return
        
        # Scan deleted files
        deleted_files = scan_deleted_files(parser, ui)
        
        if not deleted_files:
            parser.close()
            return
        
        # Filter files
        filtered_files = filter_files(deleted_files, args, ui)
        
        # Recover files
        recover_files(parser, filtered_files, args, ui)
        
        # Close parser
        parser.close()
        
        ui.print_success("Completed!")
        
    except KeyboardInterrupt:
        print()
        ui.print_warning("Cancelled by user")
        sys.exit(0)
        
    except Exception as e:
        ui.print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

