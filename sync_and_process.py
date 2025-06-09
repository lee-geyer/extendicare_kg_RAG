#!/usr/bin/env python3
"""
Complete Sync and Process Workflow
Detects file changes, cleans up orphaned files, and processes new documents through LlamaParse.
"""

import sys
import subprocess
from pathlib import Path
from scripts.file_tracker import FileTracker, ProcessingStatus

def run_file_detection_and_cleanup():
    """Run file detection and cleanup"""
    print("🔍 Step 1: Detecting file changes and cleaning up orphaned files...")
    print("=" * 70)
    
    tracker = FileTracker()
    
    # Get initial counts
    initial_files = tracker.get_all_files()
    initial_discovered = len([f for f in initial_files if f.status == ProcessingStatus.DISCOVERED])
    initial_total = len(initial_files)
    
    # Sync discovered files
    print("🔄 Syncing discovered files...")
    added = tracker.sync_discovered_files()
    print(f"✅ Added {added} new files to database")
    
    # Sync processing status
    print("🔄 Syncing processing status...")
    tracker.sync_processing_status()
    print("✅ Processing status synced")
    
    # Clean up orphaned files
    print("🧹 Cleaning up orphaned files...")
    orphaned_files = tracker.get_orphaned_files()
    
    if orphaned_files:
        print(f"   Found {len(orphaned_files)} orphaned files to remove:")
        for file in orphaned_files[:5]:  # Show first 5
            print(f"   - {file.filename} ({file.category})")
        if len(orphaned_files) > 5:
            print(f"   ... and {len(orphaned_files) - 5} more")
        
        results = tracker.remove_orphaned_files(remove_processed_files=True)
        print(f"✅ Cleanup completed:")
        print(f"   - Database records removed: {results['database_records']}")
        print(f"   - Processed markdown files removed: {results['processed_files']}")
        print(f"   - Metadata files removed: {results['metadata_files']}")
    else:
        print("✨ No orphaned files found")
    
    # Get final counts
    final_files = tracker.get_all_files()
    final_discovered = len([f for f in final_files if f.status == ProcessingStatus.DISCOVERED])
    final_total = len(final_files)
    
    print(f"\n📊 Summary:")
    print(f"   Total files: {initial_total} → {final_total}")
    print(f"   Files awaiting processing: {initial_discovered} → {final_discovered}")
    print(f"   New files to process: {final_discovered - initial_discovered + added}")
    
    return final_discovered

def run_document_processing():
    """Run document processing pipeline"""
    print(f"\n🚀 Step 2: Processing documents through LlamaParse pipeline...")
    print("=" * 70)
    
    # Check if there are files to process
    tracker = FileTracker()
    discovered_files = tracker.get_all_files(status_filter=ProcessingStatus.DISCOVERED)
    
    if not discovered_files:
        print("✨ No files to process!")
        return True
    
    print(f"📋 Processing {len(discovered_files)} discovered files...")
    
    # Show some examples of what will be processed
    print("🗂️  Files to process:")
    for i, file in enumerate(discovered_files[:5]):
        print(f"   {i+1}. {file.filename} ({file.category})")
    if len(discovered_files) > 5:
        print(f"   ... and {len(discovered_files) - 5} more")
    
    try:
        # Run the processing script with real-time output streaming
        print("🔄 Starting document processing with real-time progress...")
        print("-" * 50)
        
        process = subprocess.Popen([
            "uv", "run", "python", "process_discovered_simple.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
           text=True, bufsize=1, universal_newlines=True, cwd=Path.cwd())
        
        # Stream output in real-time
        for line in process.stdout:
            print(line.rstrip())
        
        # Wait for process to complete and get return code
        process.wait()
        
        print("-" * 50)
        if process.returncode == 0:
            print("✅ Document processing completed successfully!")
            return True
        else:
            print(f"❌ Document processing failed with return code: {process.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to run processing script: {e}")
        return False

def show_final_status():
    """Show final system status"""
    print(f"\n📊 Final System Status:")
    print("=" * 70)
    
    tracker = FileTracker()
    status_summary = tracker.get_status_summary()
    category_summary = tracker.get_category_summary()
    
    print("File Status Summary:")
    for status, count in status_summary.items():
        print(f"   {status}: {count}")
    
    print(f"\nTop Categories:")
    for category, count in list(category_summary.items())[:8]:  # Show top 8
        print(f"   {category}: {count}")
    
    total_files = sum(status_summary.values())
    completed_files = status_summary.get('completed', 0)
    discovered_files = status_summary.get('discovered', 0)
    
    completion_rate = (completed_files / total_files * 100) if total_files > 0 else 0
    
    print(f"\n🎯 Progress Summary:")
    print(f"   Total files tracked: {total_files}")
    print(f"   Completed processing: {completed_files} ({completion_rate:.1f}%)")
    print(f"   Awaiting processing: {discovered_files}")
    
    if discovered_files == 0:
        print("🎉 All files have been processed!")
    else:
        print(f"⏳ {discovered_files} files still need processing")

def main():
    """Main workflow"""
    print("🔄 Complete Sync and Process Workflow")
    print("=" * 70)
    print("This will:")
    print("  1. Detect new and removed files")
    print("  2. Clean up orphaned database records and processed files")
    print("  3. Process new files through LlamaParse pipeline")
    print("=" * 70)
    
    # Handle command line arguments
    args = sys.argv[1:]
    
    if '--help' in args or '-h' in args:
        print("""
Usage: python sync_and_process.py [OPTIONS]

Options:
  --help, -h        Show this help message
  --sync-only       Only run file detection and cleanup (skip processing)
  --process-only    Only run document processing (skip file detection)
  --dry-run         Show what would be done without making changes

This script combines file detection, cleanup, and document processing into
a single workflow. Perfect for running after doc-sync updates.
        """)
        return
    
    sync_only = '--sync-only' in args
    process_only = '--process-only' in args
    dry_run = '--dry-run' in args
    
    if dry_run:
        print("🧪 DRY RUN MODE - No changes will be made")
        print("   Would run complete sync and process workflow")
        return
    
    success = True
    
    # Step 1: File detection and cleanup
    if not process_only:
        try:
            files_to_process = run_file_detection_and_cleanup()
            if files_to_process == 0 and not sync_only:
                print("\n✨ No files to process - skipping processing step")
                sync_only = True
        except Exception as e:
            print(f"❌ File detection/cleanup failed: {e}")
            success = False
    
    # Step 2: Document processing
    if not sync_only and success:
        try:
            processing_success = run_document_processing()
            if not processing_success:
                success = False
        except Exception as e:
            print(f"❌ Document processing failed: {e}")
            success = False
    
    # Final status
    print("\n" + "=" * 70)
    if success:
        print("🎉 Workflow completed successfully!")
    else:
        print("⚠️  Workflow completed with errors - check output above")
    
    show_final_status()
    
    # Suggest next steps
    if success:
        tracker = FileTracker()
        discovered_files = len(tracker.get_all_files(status_filter=ProcessingStatus.DISCOVERED))
        
        if discovered_files > 0:
            print(f"\n💡 Next steps:")
            print(f"   Run again to process remaining {discovered_files} files")
        else:
            print(f"\n💡 Suggested next steps:")
            print(f"   - Generate HTML report: uv run python generate_html_report.py")
            print(f"   - Start monitoring dashboard: uv run uvicorn scripts.api:app --reload --host 127.0.0.1 --port 8080")

if __name__ == "__main__":
    main()