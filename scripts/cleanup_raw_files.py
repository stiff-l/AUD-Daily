#!/usr/bin/env python3
"""
Cleanup Raw Files Script

Keeps only a maximum of 2 raw JSON files per date for both forex_data and commodities_data.
Files are sorted by timestamp (most recent first) and older files are deleted.
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
import re

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def extract_date_and_timestamp(filename: str) -> tuple:
    """
    Extract date and timestamp from filename.
    
    Patterns:
    - Forex: aud_data_YYYYMMDD_HHMMSS.json
    - Commodities: commodity_data_YYYYMMDD_HHMMSS.json
    
    Returns:
        Tuple of (date_str, full_timestamp_str) or (None, None) if pattern doesn't match
    """
    # Match pattern: prefix_YYYYMMDD_HHMMSS.json
    pattern = r'(.+)_(\d{8})_(\d{6})\.json'
    match = re.match(pattern, filename)
    
    if match:
        prefix = match.group(1)
        date_str = match.group(2)  # YYYYMMDD
        time_str = match.group(3)  # HHMMSS
        full_timestamp = f"{date_str}_{time_str}"  # YYYYMMDD_HHMMSS
        return date_str, full_timestamp
    
    return None, None


def cleanup_raw_files(verbose: bool = False) -> dict:
    """
    Clean up raw files for both forex and commodities data.
    Keeps only a maximum of 2 raw JSON files per date.
    
    Args:
        verbose: Whether to print detailed cleanup messages (default: False)
        
    Returns:
        Dictionary with cleanup statistics
    """
    # Get project root directory
    project_root = Path(__file__).parent.parent
    
    # Define directories to clean
    directories = [
        project_root / "data" / "forex_data" / "raw",
        project_root / "data" / "commodities_data" / "raw"
    ]
    
    if verbose:
        print("\n" + "=" * 60)
        print("Raw Files Cleanup")
        print("=" * 60)
        print(f"Keeping maximum of 2 files per date\n")
    
    all_stats = []
    
    for raw_dir in directories:
        if verbose:
            print(f"\nProcessing: {raw_dir}")
            print("-" * 60)
        stats = cleanup_directory(raw_dir, max_files_per_date=2, verbose=verbose)
        all_stats.append(stats)
    
    if verbose:
        # Print summary
        print("\n" + "=" * 60)
        print("Cleanup Summary")
        print("=" * 60)
        
        total_files = 0
        total_kept = 0
        total_deleted = 0
        
        for stats in all_stats:
            print(f"\n{stats['directory']}:")
            print(f"  Total files: {stats['total_files']}")
            print(f"  Files kept: {stats['files_kept']}")
            print(f"  Files deleted: {stats['files_deleted']}")
            print(f"  Dates processed: {stats['dates_processed']}")
            
            total_files += stats['total_files']
            total_kept += stats['files_kept']
            total_deleted += stats['files_deleted']
        
        print(f"\nOverall:")
        print(f"  Total files: {total_files}")
        print(f"  Total kept: {total_kept}")
        print(f"  Total deleted: {total_deleted}")
        print("=" * 60)
        print("Cleanup complete!")
    
    return {
        'total_files': sum(s['total_files'] for s in all_stats),
        'total_kept': sum(s['files_kept'] for s in all_stats),
        'total_deleted': sum(s['files_deleted'] for s in all_stats),
        'directories_processed': len(all_stats)
    }


def cleanup_directory(raw_dir: Path, max_files_per_date: int = 2, verbose: bool = False) -> dict:
    """
    Clean up raw files in a directory, keeping only max_files_per_date per date.
    
    Args:
        raw_dir: Path to the raw directory
        max_files_per_date: Maximum number of files to keep per date (default: 2)
        
    Returns:
        Dictionary with cleanup statistics
    """
    if not raw_dir.exists():
        return {
            'directory': str(raw_dir),
            'total_files': 0,
            'files_kept': 0,
            'files_deleted': 0,
            'dates_processed': 0
        }
    
    # Group files by date
    files_by_date = defaultdict(list)
    
    # Find all JSON files
    json_files = list(raw_dir.glob("*.json"))
    
    for filepath in json_files:
        date_str, timestamp = extract_date_and_timestamp(filepath.name)
        if date_str and timestamp:
            files_by_date[date_str].append((filepath, timestamp))
        else:
            if verbose:
                print(f"Warning: Could not parse filename: {filepath.name}")
    
    # Sort files by date, then by timestamp (most recent first)
    stats = {
        'directory': str(raw_dir),
        'total_files': len(json_files),
        'files_kept': 0,
        'files_deleted': 0,
        'dates_processed': len(files_by_date)
    }
    
    # Process each date
    for date_str, file_list in sorted(files_by_date.items()):
        # Sort by timestamp (descending - most recent first)
        file_list.sort(key=lambda x: x[1], reverse=True)
        
        # Keep only the most recent max_files_per_date files
        files_to_keep = file_list[:max_files_per_date]
        files_to_delete = file_list[max_files_per_date:]
        
        # Delete older files
        for filepath, _ in files_to_delete:
            try:
                filepath.unlink()
                stats['files_deleted'] += 1
                if verbose:
                    print(f"Deleted: {filepath.name}")
            except Exception as e:
                if verbose:
                    print(f"Error deleting {filepath.name}: {e}")
        
        # Count kept files
        stats['files_kept'] += len(files_to_keep)
        
        if files_to_delete and verbose:
            print(f"Date {date_str}: Kept {len(files_to_keep)}, Deleted {len(files_to_delete)}")
    
    return stats


def main():
    """Main cleanup function (standalone script entry point)."""
    cleanup_raw_files(verbose=True)


if __name__ == "__main__":
    main()
