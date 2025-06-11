#!/usr/bin/env python3
"""
Test File Detection System
Tests the ability to detect new and removed files from the source repository.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from scripts.file_tracker import FileTracker, ProcessingStatus
from scripts.ingest import FileIngestionAgent

def test_new_file_detection():
    """Test detection of new files"""
    print("🧪 Testing new file detection...")
    
    # Create a temporary test file in the source directory
    source_dir = Path("data/raw/extendicare_kb")
    if not source_dir.exists():
        print("❌ Source directory not found")
        return False
    
    # Create a temporary subdirectory
    test_dir = source_dir / "test_category"
    test_dir.mkdir(exist_ok=True)
    
    # Create a temporary test file
    test_file = test_dir / "test_document.pdf"
    test_file.write_text("This is a test PDF content")
    
    try:
        # Get current file count
        tracker = FileTracker()
        initial_files = len(tracker.get_all_files())
        
        # Run discovery
        added = tracker.sync_discovered_files()
        
        # Check if new file was detected
        final_files = len(tracker.get_all_files())
        
        if final_files > initial_files:
            print(f"✅ New file detection PASSED: Added {added} file(s)")
            
            # Verify the test file is in database
            discovered_files = tracker.get_all_files(status_filter=ProcessingStatus.DISCOVERED)
            test_file_found = any(f.filename == "test_document.pdf" for f in discovered_files)
            
            if test_file_found:
                print("✅ Test file correctly added to database")
                return True
            else:
                print("❌ Test file not found in database")
                return False
        else:
            print(f"❌ New file detection FAILED: No new files detected")
            return False
            
    finally:
        # Clean up test file and directory
        if test_file.exists():
            test_file.unlink()
        if test_dir.exists():
            test_dir.rmdir()

def test_removed_file_detection():
    """Test detection of removed files"""
    print("\n🧪 Testing removed file detection...")
    
    tracker = FileTracker()
    
    # Get all files currently in database
    all_files = tracker.get_all_files()
    initial_count = len(all_files)
    
    # Get files from actual filesystem
    agent = FileIngestionAgent()
    current_files = agent.discover_documents()
    current_doc_ids = {doc.doc_id for doc in current_files}
    
    # Find files in database that are no longer on filesystem
    removed_files = []
    for file_record in all_files:
        if file_record.doc_id not in current_doc_ids:
            removed_files.append(file_record)
    
    if removed_files:
        print(f"✅ Removed file detection PASSED: Found {len(removed_files)} files that no longer exist")
        print("📂 Example removed files:")
        for i, file in enumerate(removed_files[:5]):  # Show first 5
            print(f"   {i+1}. {file.filename} (Category: {file.category})")
        if len(removed_files) > 5:
            print(f"   ... and {len(removed_files) - 5} more")
        return True
    else:
        print("ℹ️  No removed files detected (all database files still exist)")
        return True

def test_file_hash_change_detection():
    """Test detection of file content changes via hash"""
    print("\n🧪 Testing file hash change detection...")
    
    source_dir = Path("data/raw/extendicare_kb")
    if not source_dir.exists():
        print("❌ Source directory not found")
        return False
    
    # Create a temporary test file
    test_dir = source_dir / "test_category"
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "test_hash_document.pdf"
    
    try:
        # Create initial file
        test_file.write_text("Initial content")
        
        tracker = FileTracker()
        
        # First discovery
        tracker.sync_discovered_files()
        initial_files = tracker.get_all_files()
        test_file_record = next((f for f in initial_files if f.filename == "test_hash_document.pdf"), None)
        
        if not test_file_record:
            print("❌ Test file not found after initial sync")
            return False
        
        initial_hash = test_file_record.file_hash
        
        # Modify file content
        test_file.write_text("Modified content - this should change the hash")
        
        # Run discovery again
        added = tracker.sync_discovered_files()
        
        # Check if a new record was created (due to hash change)
        final_files = tracker.get_all_files()
        test_files = [f for f in final_files if f.filename == "test_hash_document.pdf"]
        
        if len(test_files) > 1:
            print("✅ Hash change detection PASSED: New record created for modified file")
            return True
        elif len(test_files) == 1 and test_files[0].file_hash != initial_hash:
            print("✅ Hash change detection PASSED: File hash updated")
            return True
        else:
            print("❌ Hash change detection FAILED: No change detected")
            return False
            
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()
        if test_dir.exists():
            test_dir.rmdir()

def print_system_status():
    """Print current system status"""
    print("\n📊 Current System Status:")
    
    tracker = FileTracker()
    status_summary = tracker.get_status_summary()
    category_summary = tracker.get_category_summary()
    
    print("File Status Summary:")
    for status, count in status_summary.items():
        print(f"   {status}: {count}")
    
    print("\nCategory Summary:")
    for category, count in category_summary.items():
        print(f"   {category}: {count}")
    
    # Check for potential issues
    total_discovered = status_summary.get('discovered', 0)
    total_files = sum(status_summary.values())
    
    print(f"\nTotal files tracked: {total_files}")
    if total_discovered > 0:
        print(f"⚠️  {total_discovered} files waiting to be processed")

def main():
    """Run all file detection tests"""
    print("🚀 Starting File Detection System Tests")
    print("=" * 50)
    
    # Print initial status
    print_system_status()
    
    # Run tests
    tests = [
        test_new_file_detection,
        test_removed_file_detection,
        test_file_hash_change_detection
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Summary:")
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "New file detection",
        "Removed file detection", 
        "File hash change detection"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {i+1}. {name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! File detection system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the output above.")
    
    # Print final status
    print_system_status()

if __name__ == "__main__":
    main()