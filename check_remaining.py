#!/usr/bin/env python3
"""
Check which CARE files haven't been processed yet
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / "scripts"))

from ingest import FileIngestionAgent

def main():
    print("🔍 Checking for unprocessed CARE documents...")
    
    # Initialize agent
    agent = FileIngestionAgent("data/raw/extendicare_kb")
    
    # Get all documents and filter by CARE
    all_docs = agent.discover_documents()
    care_docs = agent.filter_by_filename_prefix(all_docs, "CARE")
    
    print(f"📄 Found {len(care_docs)} CARE documents in source")
    
    # Check which are already processed
    parsed_dir = Path("data/parsed")
    processed_files = set()
    
    for md_file in parsed_dir.glob("*.md"):
        # Extract original filename pattern from processed file
        processed_files.add(md_file.stem)
    
    print(f"✅ Found {len(processed_files)} processed documents")
    
    # Find unprocessed files
    unprocessed = []
    for doc in care_docs:
        # Create expected processed filename
        expected_id = f"{doc.category.lower()}{doc.section}-{doc.document_type}{doc.policy_number}"
        if doc.tool_number:
            expected_id += f"-{doc.tool_number}"
        
        # Check if any processed file starts with similar pattern
        found = False
        for processed in processed_files:
            if doc.filename.lower().replace(" ", "").replace("-", "").replace(".", "") in processed.lower().replace(" ", "").replace("-", "").replace(".", ""):
                found = True
                break
        
        if not found:
            unprocessed.append(doc)
    
    print(f"\n🔄 Unprocessed CARE documents ({len(unprocessed)}):")
    for doc in unprocessed:
        print(f"   - {doc.filename}")
        print(f"     Path: {doc.file_path}")
    
    if not unprocessed:
        print("🎉 All CARE documents have been processed!")
    
    return unprocessed

if __name__ == "__main__":
    remaining = main()