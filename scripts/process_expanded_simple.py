"""
Simplified expanded processing script
"""

import asyncio
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))

from ingest import FileIngestionAgent
from parse import LlamaParseAgent
from extract_metadata import MetadataExtractionAgent
from clean_chunk import TextCleaningChunkingAgent


async def process_single_document(doc, agents):
    """Process a single document"""
    try:
        print(f"\n🔄 Processing: {doc.filename}")
        start_time = time.time()
        
        # Step 1: Parse with LlamaParse
        print(f"   📄 Parsing...")
        parsed_result = await agents['parse'].parse_document(doc)
        parsed_content = parsed_result.markdown_content if parsed_result else None
        if not parsed_content:
            raise Exception("Failed to parse document")
        
        # Step 2: Extract metadata  
        print(f"   🏷️  Extracting metadata...")
        metadata = await agents['metadata'].extract_metadata(parsed_result, doc.category)
        
        # Step 3: Clean and chunk
        print(f"   ✂️  Cleaning and chunking...")
        chunks_result = agents['chunk'].chunk_document(
            parsed_doc=parsed_result,
            metadata=metadata
        )
        
        # Step 4: Save all results
        print(f"   💾 Saving results...")
        
        # Save parsed content
        parsed_dir = Path("data/parsed")
        parsed_dir.mkdir(parents=True, exist_ok=True)
        parsed_file = parsed_dir / f"{doc.doc_id}.md"
        with open(parsed_file, 'w', encoding='utf-8') as f:
            f.write(parsed_content)
        
        # Save metadata
        agents['metadata'].save_metadata(metadata)
        
        # Save chunks
        agents['chunk'].save_chunks(chunks_result)
        
        processing_time = time.time() - start_time
        chunk_count = len(chunks_result) if chunks_result else 0
        
        print(f"   ✅ Completed in {processing_time:.1f}s - {chunk_count} chunks")
        
        return {
            'success': True,
            'doc_id': doc.doc_id,
            'filename': doc.filename,
            'category': doc.category,
            'chunks': chunk_count,
            'processing_time': processing_time
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"   ❌ Failed after {processing_time:.1f}s: {str(e)}")
        return {
            'success': False,
            'doc_id': doc.doc_id,
            'filename': doc.filename,
            'category': doc.category,
            'error': str(e),
            'processing_time': processing_time
        }


async def main():
    print("🚀 Starting simplified expanded processing...")
    
    # Initialize agents
    print("🔧 Initializing agents...")
    agents = {
        'parse': LlamaParseAgent(),
        'metadata': MetadataExtractionAgent(), 
        'chunk': TextCleaningChunkingAgent()
    }
    
    # Discover documents
    print("🔍 Discovering documents...")
    ingestion_agent = FileIngestionAgent("data/raw/extendicare_kb")
    all_documents = ingestion_agent.discover_documents()
    
    # Filter to target categories
    target_categories = [
        "Care",
        "Emergency Planning and Management",
        "Environmental Services", 
        "Infection Prevention and Control",
        "Privacy and Confidentiality"
    ]
    
    target_docs = [doc for doc in all_documents if doc.category in target_categories]
    print(f"📁 Found {len(target_docs)} documents in target categories")
    
    # Check already processed
    parsed_dir = Path("data/parsed")
    already_processed = set()
    if parsed_dir.exists():
        for md_file in parsed_dir.glob("*.md"):
            already_processed.add(md_file.stem)
    
    print(f"📋 Already processed: {len(already_processed)} documents")
    
    # Filter unprocessed
    unprocessed_docs = []
    for doc in target_docs:
        if doc.doc_id not in already_processed:
            unprocessed_docs.append(doc)
    
    print(f"🔄 Documents to process: {len(unprocessed_docs)}")
    
    if not unprocessed_docs:
        print("🎉 All documents already processed!")
        return
    
    # Process all remaining documents
    successful = 0
    failed = 0
    total_docs = len(unprocessed_docs)
    
    print(f"\n🚀 Starting to process all {total_docs} remaining documents...")
    
    for i, doc in enumerate(unprocessed_docs):
        doc_num = i + 1
        print(f"\n📦 Document {doc_num}/{total_docs}")
        
        result = await process_single_document(doc, agents)
        
        if result['success']:
            successful += 1
        else:
            failed += 1
        
        # Progress update every 10 documents
        if doc_num % 10 == 0:
            print(f"📊 Progress: {doc_num}/{total_docs} ({successful} successful, {failed} failed)")
        
        # Small delay between documents to respect API limits
        if doc_num < total_docs:
            print("⏸️  Pause...")
            await asyncio.sleep(3)  # Reduced to 3 seconds for faster processing
    
    print(f"\n🎉 ALL PROCESSING COMPLETE!")
    print(f"📊 Final Results: {successful} successful, {failed} failed out of {total_docs} documents")
    print(f"📁 Total documents now processed: {237 + successful}")


if __name__ == "__main__":
    asyncio.run(main())