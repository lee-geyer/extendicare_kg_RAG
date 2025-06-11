#!/usr/bin/env python3
"""
Debug script to test metadata extraction issue
"""
import asyncio
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent / "scripts"))

from ingest import FileIngestionAgent
from parse import LlamaParseAgent
from extract_metadata import MetadataExtractionAgent

async def main():
    print("🔧 Testing metadata extraction debug...")
    
    # Initialize agents
    agents = {
        'parse': LlamaParseAgent(),
        'metadata': MetadataExtractionAgent()
    }
    
    # Get a test document
    ingestion_agent = FileIngestionAgent("data/raw/extendicare_kb")
    all_documents = ingestion_agent.discover_documents()
    
    # Find first infection prevention doc
    target_categories = ["Infection Prevention and Control"]
    target_docs = [doc for doc in all_documents if doc.category in target_categories]
    
    if not target_docs:
        print("No target documents found")
        return
    
    doc = target_docs[0]
    print(f"Testing with: {doc.filename}")
    print(f"Document object type: {type(doc)}")
    print(f"Document attributes: {dir(doc)}")
    
    # Test parsing
    print("\n📄 Parsing document...")
    parsed_result = await agents['parse'].parse_document(doc)
    print(f"Parsed result type: {type(parsed_result)}")
    
    if parsed_result:
        print(f"Parsed result is not None")
        print(f"Has doc_id: {hasattr(parsed_result, 'doc_id')}")
        print(f"Has markdown_content: {hasattr(parsed_result, 'markdown_content')}")
        
        if hasattr(parsed_result, 'doc_id'):
            print(f"doc_id value: {parsed_result.doc_id}")
            print(f"doc_id type: {type(parsed_result.doc_id)}")
            
        if hasattr(parsed_result, 'markdown_content'):
            content = parsed_result.markdown_content
            print(f"Content is None: {content is None}")
            print(f"Content length: {len(content) if content else 0}")
            print(f"Content type: {type(content)}")
            
        print(f"Error field: {getattr(parsed_result, 'error', 'No error field')}")
        
        # Now check the condition that might fail
        parsed_content = parsed_result.markdown_content if parsed_result else None
        print(f"parsed_content is None: {parsed_content is None}")
        
        if not parsed_content:
            print("❌ Would fail the parsing check!")
            return
    else:
        print("❌ parsed_result is None!")
        return
    
    # Test metadata extraction
    print("\n🏷️  Testing metadata extraction...")
    try:
        # Use the exact same call as in the processing script
        metadata = await agents['metadata'].extract_metadata(parsed_result, doc.category)
        print(f"✅ Metadata extraction successful!")
        print(f"Metadata type: {type(metadata)}")
        print(f"Success: {metadata.extraction_success}")
    except Exception as e:
        print(f"❌ Metadata extraction failed: {str(e)}")
        print(f"Error type: {type(e)}")
        
        # Try to debug the exact issue
        import traceback
        print("Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())