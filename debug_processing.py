#!/usr/bin/env python3
"""
Debug exactly where the processing fails
"""

import asyncio
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / "scripts"))

from ingest import FileIngestionAgent
from parse import LlamaParseAgent

async def main():
    print("🔍 Debugging processing failure...")
    
    # Get a document to test
    ingestion_agent = FileIngestionAgent("data/raw/extendicare_kb")
    all_documents = ingestion_agent.discover_documents()
    
    target_categories = [
        "Emergency Planning and Management",
        "Environmental Services", 
        "Infection Prevention and Control",
        "Privacy and Confidentiality"
    ]
    
    target_docs = [doc for doc in all_documents if doc.category in target_categories]
    
    # Get first unprocessed doc
    parsed_dir = Path("data/parsed")
    already_processed = set()
    if parsed_dir.exists():
        for md_file in parsed_dir.glob("*.md"):
            already_processed.add(md_file.stem)
    
    test_doc = None
    for doc in target_docs:
        if doc.doc_id not in already_processed:
            test_doc = doc
            break
    
    if not test_doc:
        print("No unprocessed documents found")
        return
    
    print(f"📄 Testing with: {test_doc.filename}")
    print(f"   Type: {type(test_doc)}")
    print(f"   Doc ID: {test_doc.doc_id}")
    print(f"   File path: {test_doc.file_path}")
    print(f"   Category: {test_doc.category}")
    
    # Test LlamaParse agent initialization
    print("\n🔧 Initializing LlamaParse agent...")
    try:
        parse_agent = LlamaParseAgent()
        print("✅ LlamaParse agent initialized")
    except Exception as e:
        print(f"❌ Failed to initialize LlamaParse agent: {e}")
        return
    
    # Test parse_document call
    print(f"\n📄 Testing parse_document with file_path...")
    print(f"   Calling: parse_agent.parse_document({test_doc.file_path})")
    print(f"   File path type: {type(test_doc.file_path)}")
    print(f"   File exists: {test_doc.file_path.exists()}")
    
    try:
        result = await parse_agent.parse_document(test_doc.file_path)
        print(f"✅ Parse successful: {len(result) if result else 0} characters")
    except Exception as e:
        print(f"❌ Parse failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())