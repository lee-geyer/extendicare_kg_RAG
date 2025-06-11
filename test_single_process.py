#!/usr/bin/env python3
"""
Test processing a single discovered file
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add scripts directory to path for imports
sys.path.append(str(Path("scripts")))

from ingest import DocumentInfo
from parse import LlamaParseAgent
from extract_metadata import MetadataExtractionAgent  
from clean_chunk import TextCleaningChunkingAgent
from file_tracker import FileTracker, ProcessingStatus

async def test_single_file():
    """Test processing a single file"""
    
    # Check API key
    api_key = os.getenv('LLAMA_CLOUD_API_KEY')
    if not api_key:
        print("❌ LLAMA_CLOUD_API_KEY not found in environment")
        return
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    # Get one discovered file
    tracker = FileTracker()
    discovered_files = tracker.get_all_files(status_filter=ProcessingStatus.DISCOVERED)
    
    if not discovered_files:
        print("❌ No discovered files to test with")
        return
    
    # Take the first file
    file_record = discovered_files[0]
    print(f"🧪 Testing with: {file_record.filename}")
    print(f"   Category: {file_record.category}")
    print(f"   Doc ID: {file_record.doc_id}")
    
    # Create DocumentInfo object
    doc = DocumentInfo(
        file_path=Path(file_record.file_path),
        doc_id=file_record.doc_id,
        category=file_record.category,
        filename=file_record.filename,
        file_extension=file_record.file_extension,
        file_size=file_record.file_size,
        file_hash=file_record.file_hash
    )
    
    # Check if file exists
    if not doc.file_path.exists():
        print(f"❌ Source file not found: {doc.file_path}")
        return
    
    print(f"✅ Source file exists: {doc.file_path}")
    
    try:
        print("🔧 Initializing agents...")
        
        # Initialize agents
        parse_agent = LlamaParseAgent()
        metadata_agent = MetadataExtractionAgent()
        chunk_agent = TextCleaningChunkingAgent()
        
        # Update status to processing
        tracker.update_file_status(file_record.doc_id, ProcessingStatus.PROCESSING)
        
        # Step 1: Parse
        print("📄 Step 1: Parsing with LlamaParse...")
        parsed_result = await parse_agent.parse_document(doc)
        
        if not parsed_result or not parsed_result.markdown_content:
            raise Exception("Failed to parse document - no content returned")
        
        print(f"✅ Parsed successfully - {len(parsed_result.markdown_content)} characters")
        
        # Step 2: Extract metadata
        print("🏷️  Step 2: Extracting metadata...")
        metadata = await metadata_agent.extract_metadata(parsed_result, doc.category)
        print(f"✅ Metadata extracted: {type(metadata)}")
        
        # Step 3: Chunk
        print("✂️  Step 3: Chunking...")
        chunks_result = chunk_agent.chunk_document(
            parsed_doc=parsed_result,
            metadata=metadata
        )
        
        if isinstance(chunks_result, list):
            chunk_count = len(chunks_result)
        elif isinstance(chunks_result, dict):
            chunk_count = len(chunks_result.get('chunks', []))
        else:
            chunk_count = 0
        print(f"✅ Chunked into {chunk_count} chunks")
        
        # Step 4: Save (optional for test)
        print("💾 Step 4: Saving...")
        
        # Create directories
        parsed_dir = Path("data/parsed")
        metadata_dir = Path("data/metadata")
        parsed_dir.mkdir(parents=True, exist_ok=True)
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Save markdown
        md_file = parsed_dir / f"{doc.doc_id}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(parsed_result.markdown_content)
        print(f"✅ Saved markdown: {md_file}")
        
        # Save chunks
        if chunks_result:
            chunks_file = parsed_dir / f"{doc.doc_id}_chunks.json"
            with open(chunks_file, 'w', encoding='utf-8') as f:
                # Convert to proper format if it's a list
                if isinstance(chunks_result, list):
                    # Convert DocumentChunk objects to dictionaries
                    chunks_list = []
                    for chunk in chunks_result:
                        if hasattr(chunk, 'dict'):
                            chunks_list.append(chunk.dict())
                        elif hasattr(chunk, '__dict__'):
                            chunks_list.append(chunk.__dict__)
                        else:
                            chunks_list.append(str(chunk))
                    chunks_data = {'chunks': chunks_list, 'total_chunks': len(chunks_list)}
                else:
                    chunks_data = chunks_result
                json.dump(chunks_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved chunks: {chunks_file}")
        
        # Save metadata
        if metadata:
            metadata_file = metadata_dir / f"{doc.doc_id}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                try:
                    if hasattr(metadata, 'dict'):
                        metadata_dict = metadata.dict()
                    elif hasattr(metadata, '__dict__'):
                        metadata_dict = metadata.__dict__
                    else:
                        metadata_dict = str(metadata)
                    json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    # Fallback: convert to string representation
                    json.dump({'metadata': str(metadata), 'error': str(e)}, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved metadata: {metadata_file}")
        
        # Update tracker
        content_length = len(parsed_result.markdown_content)
        tracker.update_processing_results(doc.doc_id, chunk_count, content_length, metadata is not None)
        tracker.update_file_status(file_record.doc_id, ProcessingStatus.COMPLETED)
        
        print(f"🎉 Test completed successfully!")
        print(f"   Content length: {content_length:,} characters")
        print(f"   Chunks created: {chunk_count}")
        print(f"   Metadata extracted: {'Yes' if metadata else 'No'}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        tracker.update_file_status(file_record.doc_id, ProcessingStatus.FAILED, str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_single_file())