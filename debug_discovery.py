#!/usr/bin/env python3
"""
Debug the document discovery process
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / "scripts"))

from ingest import FileIngestionAgent

def main():
    print("🔍 Debugging document discovery...")
    
    agent = FileIngestionAgent("data/raw/extendicare_kb")
    all_docs = agent.discover_documents()
    
    print(f"📄 Found {len(all_docs)} total documents")
    
    # Check first few documents
    print("\n🔍 First 5 documents:")
    for i, doc in enumerate(all_docs[:5]):
        print(f"{i+1}. Type: {type(doc)}")
        print(f"   Has filename attr: {hasattr(doc, 'filename')}")
        print(f"   Has name attr: {hasattr(doc, 'name')}")
        if hasattr(doc, 'filename'):
            print(f"   Filename: {doc.filename}")
        if hasattr(doc, 'name'):
            print(f"   Name: {doc.name}")
        print(f"   String repr: {str(doc)}")
        print()
    
    # Target categories
    target_categories = [
        "Care",
        "Emergency Planning and Management", 
        "Environmental Services",
        "Infection Prevention and Control",
        "Privacy and Confidentiality"
    ]
    
    target_docs = [doc for doc in all_docs if hasattr(doc, 'category') and doc.category in target_categories]
    print(f"📁 Target docs with category attribute: {len(target_docs)}")
    
    # Try the problematic filter
    care_docs = []
    for doc in all_docs:
        if hasattr(doc, 'category'):
            if doc.category in target_categories:
                care_docs.append(doc)
        else:
            print(f"⚠️  Document without category: {type(doc)} - {doc}")
    
    print(f"📋 Final filtered docs: {len(care_docs)}")

if __name__ == "__main__":
    main()