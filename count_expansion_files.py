#!/usr/bin/env python3
"""
Count files in the expanded processing categories
"""

from pathlib import Path

def count_files_in_category(category_name):
    """Count processable files in a category"""
    category_path = Path(f"data/raw/extendicare_kb/{category_name}")
    
    if not category_path.exists():
        return 0, []
    
    file_types = ['.pdf', '.docx', '.pptx']
    files = []
    
    for file_type in file_types:
        files.extend(list(category_path.rglob(f"*{file_type}")))
    
    return len(files), files

def main():
    categories = [
        "Emergency Planning and Management",
        "Environmental Services", 
        "Infection Prevention and Control",
        "Privacy and Confidentiality"
    ]
    
    total_files = 0
    all_files = []
    
    print("📊 Expansion Scope File Count")
    print("=" * 50)
    
    for category in categories:
        count, files = count_files_in_category(category)
        total_files += count
        all_files.extend(files)
        
        print(f"\n📁 {category}")
        print(f"   Files: {count}")
        
        if files:
            print("   Sample files:")
            for file in files[:3]:  # Show first 3 files
                print(f"     - {file.name}")
            if len(files) > 3:
                print(f"     ... and {len(files) - 3} more")
    
    print(f"\n🎯 TOTAL NEW FILES TO PROCESS: {total_files}")
    print(f"📄 Current processed: 237 (CARE documents)")
    print(f"🔄 After expansion: {237 + total_files} total documents")
    
    return total_files, all_files

if __name__ == "__main__":
    count, files = main()