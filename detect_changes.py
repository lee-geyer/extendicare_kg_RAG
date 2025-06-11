#!/usr/bin/env python3
"""
File Change Detection Utility
Shows exactly what files have been added, removed, or modified since last sync.
"""

from scripts.file_tracker import FileTracker, ProcessingStatus
from scripts.ingest import FileIngestionAgent
from datetime import datetime
from pathlib import Path

def detect_file_changes():
    """Detect and report file system changes"""
    print("🔍 Scanning for file system changes...")
    print("=" * 60)
    
    tracker = FileTracker()
    agent = FileIngestionAgent()
    
    # Get current files from filesystem
    current_files = agent.discover_documents()
    current_dict = {doc.doc_id: doc for doc in current_files}
    
    # Get files from database
    db_files = tracker.get_all_files()
    db_dict = {file.doc_id: file for file in db_files}
    
    # Find new files (in filesystem but not in database)
    new_files = []
    for doc_id, doc in current_dict.items():
        if doc_id not in db_dict:
            new_files.append(doc)
    
    # Find removed files (in database but not in filesystem)
    removed_files = []
    for doc_id, file_record in db_dict.items():
        if doc_id not in current_dict:
            removed_files.append(file_record)
    
    # Find potentially modified files (same path but different hash)
    modified_files = []
    for doc_id, doc in current_dict.items():
        if doc_id in db_dict:
            db_file = db_dict[doc_id]
            # Check if file path exists but content might have changed
            if doc.file_hash != db_file.file_hash:
                modified_files.append((db_file, doc))
    
    # Report findings
    print(f"📊 Change Detection Results:")
    print(f"   New files found: {len(new_files)}")
    print(f"   Removed files: {len(removed_files)}")
    print(f"   Modified files: {len(modified_files)}")
    
    if new_files:
        print(f"\n✅ NEW FILES ({len(new_files)}):")
        for i, doc in enumerate(new_files, 1):
            print(f"   {i:2d}. {doc.filename}")
            print(f"       Category: {doc.category}")
            print(f"       Path: {doc.file_path.relative_to(Path('data/raw/extendicare_kb'))}")
            print(f"       Size: {doc.file_size:,} bytes")
            print()
    
    if removed_files:
        print(f"\n❌ REMOVED FILES ({len(removed_files)}):")
        for i, file_record in enumerate(removed_files, 1):
            print(f"   {i:2d}. {file_record.filename}")
            print(f"       Category: {file_record.category}")
            print(f"       Originally discovered: {file_record.discovered_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"       Status: {file_record.status.value}")
            print()
    
    if modified_files:
        print(f"\n🔄 MODIFIED FILES ({len(modified_files)}):")
        for i, (old_file, new_doc) in enumerate(modified_files, 1):
            print(f"   {i:2d}. {new_doc.filename}")
            print(f"       Category: {new_doc.category}")
            print(f"       Old hash: {old_file.file_hash}")
            print(f"       New hash: {new_doc.file_hash}")
            print(f"       Size change: {old_file.file_size:,} → {new_doc.file_size:,} bytes")
            print()
    
    if not new_files and not removed_files and not modified_files:
        print("\n✨ No changes detected - file system is in sync!")
    
    return new_files, removed_files, modified_files

def sync_and_show_changes():
    """Sync the database and show what changed"""
    print("🔄 Syncing file database...")
    
    tracker = FileTracker()
    
    # Record state before sync
    before_sync = len(tracker.get_all_files())
    
    # Perform sync
    added = tracker.sync_discovered_files()
    tracker.sync_processing_status()
    
    # Record state after sync
    after_sync = len(tracker.get_all_files())
    
    print(f"✅ Sync completed:")
    print(f"   Files before sync: {before_sync}")
    print(f"   Files after sync: {after_sync}")
    print(f"   New files added: {added}")
    
    if added > 0:
        print(f"\n📋 Recently added files:")
        recent_files = tracker.get_all_files(status_filter=ProcessingStatus.DISCOVERED)
        
        # Sort by discovery time, newest first
        recent_files.sort(key=lambda x: x.discovered_at, reverse=True)
        
        for i, file in enumerate(recent_files[:added], 1):
            print(f"   {i:2d}. {file.filename}")
            print(f"       Category: {file.category}")
            print(f"       Doc ID: {file.doc_id}")
            print(f"       Discovered: {file.discovered_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

def main():
    """Main function"""
    import sys
    
    print("🚀 File Change Detection and Sync Utility")
    print("=" * 60)
    
    # Check if we should auto-sync (non-interactive mode)
    auto_sync = '--sync' in sys.argv or '-s' in sys.argv
    
    # First detect changes without syncing
    new_files, removed_files, modified_files = detect_file_changes()
    
    # If changes detected, offer to sync
    if new_files or removed_files or modified_files:
        print("\n" + "=" * 60)
        
        if auto_sync:
            print("🔄 Auto-syncing database...")
            sync_and_show_changes()
            
            # Also clean up removed files if any
            if removed_files:
                print(f"\n🧹 Cleaning up {len(removed_files)} removed files...")
                print("   This will remove database records AND processed files from disk")
                tracker = FileTracker()
                results = tracker.remove_orphaned_files(remove_processed_files=True)
                print(f"✅ Cleanup completed:")
                print(f"   - Database records removed: {results['database_records']}")
                print(f"   - Processed markdown files removed: {results['processed_files']}")
                print(f"   - Metadata files removed: {results['metadata_files']}")
        else:
            try:
                response = input("💾 Changes detected. Sync database? (y/N): ").strip().lower()
                if response in ['y', 'yes']:
                    print()
                    sync_and_show_changes()
                    
                    # Ask about cleanup if there are removed files
                    if removed_files:
                        print(f"\n🧹 {len(removed_files)} files no longer exist in source repository")
                        cleanup_response = input("Remove orphaned records AND processed files from disk? (y/N): ").strip().lower()
                        if cleanup_response in ['y', 'yes']:
                            tracker = FileTracker()
                            results = tracker.remove_orphaned_files(remove_processed_files=True)
                            print(f"✅ Cleanup completed:")
                            print(f"   - Database records removed: {results['database_records']}")
                            print(f"   - Processed markdown files removed: {results['processed_files']}")
                            print(f"   - Metadata files removed: {results['metadata_files']}")
                        else:
                            # Offer database-only cleanup
                            db_only_response = input("Remove orphaned database records only? (y/N): ").strip().lower()
                            if db_only_response in ['y', 'yes']:
                                tracker = FileTracker()
                                results = tracker.remove_orphaned_files(remove_processed_files=False)
                                print(f"✅ Removed {results['database_records']} orphaned database records")
                else:
                    print("ℹ️  Database not synced. Use --sync flag for automatic sync.")
            except (EOFError, KeyboardInterrupt):
                print("\nℹ️  Database not synced. Use --sync flag for automatic sync.")
    else:
        print("\n" + "=" * 60)
        print("ℹ️  No changes detected. Database appears to be in sync.")
        
        # Still show current status
        tracker = FileTracker()
        status_summary = tracker.get_status_summary()
        category_summary = tracker.get_category_summary()
        
        print(f"\n📊 Current Database Status:")
        print(f"   Total files: {sum(status_summary.values())}")
        for status, count in status_summary.items():
            print(f"   {status}: {count}")

if __name__ == "__main__":
    main()