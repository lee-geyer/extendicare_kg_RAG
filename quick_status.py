#!/usr/bin/env python3
"""
Quick status check - shows current processing state
"""

from scripts.file_tracker import FileTracker, ProcessingStatus
from datetime import datetime

def show_quick_status():
    """Show current processing status"""
    tracker = FileTracker()
    
    # Get status summary
    status_summary = tracker.get_status_summary()
    total_files = sum(status_summary.values())
    
    print("📊 Current Processing Status")
    print("=" * 40)
    
    for status, count in status_summary.items():
        percentage = (count / total_files * 100) if total_files > 0 else 0
        print(f"   {status.upper()}: {count} ({percentage:.1f}%)")
    
    print(f"\nTotal files: {total_files}")
    
    # Show currently processing files
    processing = tracker.get_all_files(status_filter=ProcessingStatus.PROCESSING)
    if processing:
        print(f"\n🔄 Currently Processing ({len(processing)} files):")
        for file in processing:
            print(f"   • {file.filename} ({file.category})")
    
    # Show recently completed files (last 5)
    completed = tracker.get_all_files(status_filter=ProcessingStatus.COMPLETED)
    completed.sort(key=lambda x: x.processing_completed_at or x.discovered_at, reverse=True)
    if completed:
        print(f"\n✅ Recently Completed (last 5):")
        for file in completed[:5]:
            completion_time = file.processing_completed_at or file.discovered_at
            time_str = completion_time.strftime("%H:%M:%S") if completion_time else "Unknown"
            print(f"   • {file.filename} - {time_str}")
    
    # Show failed files if any
    failed = tracker.get_all_files(status_filter=ProcessingStatus.FAILED)
    if failed:
        print(f"\n❌ Failed Files ({len(failed)}):")
        for file in failed[-3:]:  # Show last 3 failures
            error_msg = file.error_message or "Unknown error"
            print(f"   • {file.filename} - {error_msg[:50]}...")
    
    # Calculate progress
    completed_count = status_summary.get('completed', 0)
    discovered_count = status_summary.get('discovered', 0)
    processing_count = status_summary.get('processing', 0)
    
    if discovered_count > 0 or processing_count > 0:
        print(f"\n🎯 Progress Summary:")
        print(f"   Remaining to process: {discovered_count + processing_count}")
        completion_rate = (completed_count / total_files * 100) if total_files > 0 else 0
        print(f"   Overall completion: {completion_rate:.1f}%")
        
        if processing_count > 0:
            print(f"   Status: 🔄 PROCESSING")
        elif discovered_count > 0:
            print(f"   Status: ⏳ READY TO PROCESS")
        else:
            print(f"   Status: ✅ ALL COMPLETE")
    else:
        print(f"\n🎉 All files processed!")

if __name__ == "__main__":
    show_quick_status()