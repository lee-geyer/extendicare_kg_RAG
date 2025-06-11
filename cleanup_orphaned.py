#!/usr/bin/env python3
"""
Orphaned File Cleanup Utility
Removes database records and processed files for source documents that no longer exist.
"""

import sys
from pathlib import Path
from scripts.file_tracker import FileTracker

def show_orphaned_files():
    """Show details of orphaned files"""
    tracker = FileTracker()
    orphaned_files = tracker.get_orphaned_files()
    
    if not orphaned_files:
        print("✨ No orphaned files found!")
        return []
    
    print(f"Found {len(orphaned_files)} orphaned files:")
    print("=" * 80)
    
    # Group by status for better organization
    by_status = {}
    for file in orphaned_files:
        status = file.status.value
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(file)
    
    for status, files in by_status.items():
        print(f"\n📊 {status.upper()} ({len(files)} files):")
        for i, file in enumerate(files, 1):
            print(f"   {i:2d}. {file.filename}")
            print(f"       Category: {file.category}")
            print(f"       Doc ID: {file.doc_id}")
            print(f"       Discovered: {file.discovered_at.strftime('%Y-%m-%d %H:%M')}")
            
            # Check if processed files exist
            parsed_dir = Path("data/parsed")
            metadata_dir = Path("data/metadata")
            
            has_md = (parsed_dir / f"{file.doc_id}.md").exists()
            has_chunks = (parsed_dir / f"{file.doc_id}_chunks.json").exists()
            has_metadata = (metadata_dir / f"{file.doc_id}_metadata.json").exists()
            
            processed_files = []
            if has_md:
                processed_files.append("markdown")
            if has_chunks:
                processed_files.append("chunks")
            if has_metadata:
                processed_files.append("metadata")
            
            if processed_files:
                print(f"       Processed files: {', '.join(processed_files)}")
            else:
                print(f"       Processed files: none")
            print()
    
    return orphaned_files

def cleanup_orphaned_files(remove_processed: bool = True, dry_run: bool = False):
    """Clean up orphaned files"""
    tracker = FileTracker()
    orphaned_files = tracker.get_orphaned_files()
    
    if not orphaned_files:
        print("✨ No orphaned files to clean up!")
        return
    
    if dry_run:
        print(f"🧪 DRY RUN: Would remove {len(orphaned_files)} orphaned files")
        if remove_processed:
            print("   - Database records")
            print("   - Processed markdown files")
            print("   - Chunk files")
            print("   - Metadata files")
        else:
            print("   - Database records only")
        return
    
    print(f"🧹 Cleaning up {len(orphaned_files)} orphaned files...")
    
    if remove_processed:
        print("   This will remove database records AND processed files from disk")
    else:
        print("   This will remove database records only")
    
    results = tracker.remove_orphaned_files(remove_processed_files=remove_processed)
    
    print(f"✅ Cleanup completed:")
    print(f"   - Database records removed: {results['database_records']}")
    if remove_processed:
        print(f"   - Processed markdown files removed: {results['processed_files']}")
        print(f"   - Metadata files removed: {results['metadata_files']}")

def main():
    """Main function"""
    print("🧹 Orphaned File Cleanup Utility")
    print("=" * 50)
    
    # Parse command line arguments
    args = sys.argv[1:]
    
    dry_run = '--dry-run' in args
    db_only = '--db-only' in args
    auto_clean = '--clean' in args
    full_clean = '--full-clean' in args
    
    if '--help' in args or '-h' in args:
        print("""
Usage: python cleanup_orphaned.py [OPTIONS]

Options:
  --help, -h        Show this help message
  --dry-run         Show what would be removed without actually removing
  --db-only         Remove database records only (keep processed files)
  --clean           Remove database records only (non-interactive)
  --full-clean      Remove database records AND processed files (non-interactive)

Interactive mode (default):
  Shows orphaned files and prompts for cleanup options
        """)
        return
    
    # Show orphaned files
    orphaned_files = show_orphaned_files()
    
    if not orphaned_files:
        return
    
    print("=" * 50)
    
    # Handle non-interactive modes
    if dry_run:
        cleanup_orphaned_files(remove_processed=not db_only, dry_run=True)
        return
    
    if auto_clean:
        cleanup_orphaned_files(remove_processed=False, dry_run=False)
        return
    
    if full_clean:
        cleanup_orphaned_files(remove_processed=True, dry_run=False)
        return
    
    # Interactive mode
    try:
        print(f"Options:")
        print(f"  1. Remove database records AND processed files (full cleanup)")
        print(f"  2. Remove database records only (keep processed files)")
        print(f"  3. Dry run (show what would be removed)")
        print(f"  4. Cancel")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            cleanup_orphaned_files(remove_processed=True, dry_run=False)
        elif choice == '2':
            cleanup_orphaned_files(remove_processed=False, dry_run=False)
        elif choice == '3':
            cleanup_orphaned_files(remove_processed=True, dry_run=True)
        elif choice == '4':
            print("ℹ️  Cleanup cancelled")
        else:
            print("❌ Invalid choice")
            
    except (EOFError, KeyboardInterrupt):
        print("\nℹ️  Cleanup cancelled")

if __name__ == "__main__":
    main()