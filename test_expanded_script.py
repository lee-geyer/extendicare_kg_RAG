#!/usr/bin/env python3
"""
Quick test of the expanded processing script
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent / "scripts"))

try:
    from ingest import FileIngestionAgent
    print("✅ FileIngestionAgent import successful")
    
    agent = FileIngestionAgent("data/raw/extendicare_kb")
    print("✅ Agent initialization successful")
    
    all_docs = agent.discover_documents()
    print(f"✅ Found {len(all_docs)} total documents")
    
    target_categories = [
        "Care",
        "Emergency Planning and Management",
        "Environmental Services", 
        "Infection Prevention and Control",
        "Privacy and Confidentiality"
    ]
    
    target_docs = [doc for doc in all_docs if doc.category in target_categories]
    print(f"✅ Found {len(target_docs)} documents in target categories")
    
    # Check already processed
    parsed_dir = Path("data/parsed")
    processed = len(list(parsed_dir.glob("*.md"))) if parsed_dir.exists() else 0
    print(f"✅ Already processed: {processed} documents")
    
    remaining = len(target_docs) - processed
    print(f"🔄 Documents to process: {remaining}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()