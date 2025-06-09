#!/usr/bin/env python3
"""
Find which specific CARE file wasn't processed
"""

import json
from pathlib import Path

def main():
    # Load successful documents
    with open('data/processing_summary.json') as f:
        summary = json.load(f)
    
    processed_files = set()
    for doc in summary['successful_documents']:
        processed_files.add(doc['filename'])
    
    print(f"✅ Processed: {len(processed_files)} files")
    
    # Find all CARE files in source
    care_dir = Path("data/raw/extendicare_kb/Care")
    source_files = set()
    
    for file_path in care_dir.rglob("CARE*"):
        if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.docx', '.pptx']:
            source_files.add(file_path.name)
    
    print(f"📄 Source files: {len(source_files)} files")
    
    # Find missing files
    missing = source_files - processed_files
    
    if missing:
        print(f"\n❌ Missing files ({len(missing)}):")
        for file in missing:
            print(f"   - {file}")
            # Find full path
            for file_path in care_dir.rglob(file):
                print(f"     Path: {file_path}")
    else:
        print("🎉 All CARE files have been processed!")
    
    return missing

if __name__ == "__main__":
    missing = main()