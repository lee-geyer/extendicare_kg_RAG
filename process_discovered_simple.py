#!/usr/bin/env python3
"""
Simple script to process all discovered files
"""

import asyncio
import os
import json
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add scripts directory to path for imports
import sys
sys.path.append(str(Path("scripts")))

from ingest import DocumentInfo
from parse import LlamaParseAgent
from extract_metadata import MetadataExtractionAgent  
from clean_chunk import TextCleaningChunkingAgent
from file_tracker import FileTracker, ProcessingStatus

async def process_discovered_files():
    """Process all files with discovered status"""
    
    # Check API key
    api_key = os.getenv('LLAMA_CLOUD_API_KEY')
    if not api_key:
        print("❌ LLAMA_CLOUD_API_KEY not found in environment")
        return
    
    print("🔧 Initializing agents...")
    agents = {
        'parse': LlamaParseAgent(),
        'metadata': MetadataExtractionAgent(),
        'chunk': TextCleaningChunkingAgent()
    }
    
    # Get files to process from file tracker
    tracker = FileTracker()
    discovered_files = tracker.get_all_files(status_filter=ProcessingStatus.DISCOVERED)
    
    print(f"📋 Found {len(discovered_files)} files to process")
    
    if not discovered_files:
        print("✨ No files to process!")
        return
    
    # Create directories
    parsed_dir = Path("data/parsed")
    metadata_dir = Path("data/metadata")
    parsed_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each file
    processed_count = 0
    failed_count = 0
    
    for i, file_record in enumerate(discovered_files, 1):
        try:
            print(f"\n🔄 [{i}/{len(discovered_files)}] Processing: {file_record.filename}")
            
            # Update status to processing
            tracker.update_file_status(file_record.doc_id, ProcessingStatus.PROCESSING)
            
            # Create DocumentInfo object for compatibility
            doc = DocumentInfo(
                file_path=Path(file_record.file_path),
                doc_id=file_record.doc_id,
                category=file_record.category,
                filename=file_record.filename,
                file_extension=file_record.file_extension,
                file_size=file_record.file_size,
                file_hash=file_record.file_hash
            )
            
            # Skip if source file no longer exists
            if not doc.file_path.exists():
                print(f"   ⚠️  Source file no longer exists, skipping")
                tracker.update_file_status(file_record.doc_id, ProcessingStatus.FAILED, "Source file not found")
                failed_count += 1
                continue
            
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
            
            # Save markdown
            with open(parsed_dir / f"{doc.doc_id}.md", 'w', encoding='utf-8') as f:
                f.write(parsed_content)
            
            # Save chunks
            if chunks_result:
                with open(parsed_dir / f"{doc.doc_id}_chunks.json", 'w', encoding='utf-8') as f:
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
            
            # Save metadata
            if metadata:
                with open(metadata_dir / f"{doc.doc_id}_metadata.json", 'w', encoding='utf-8') as f:
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
            
            # Update file tracker with results
            if isinstance(chunks_result, list):
                chunk_count = len(chunks_result)
            elif isinstance(chunks_result, dict):
                chunk_count = len(chunks_result.get('chunks', []))
            else:
                chunk_count = 0
                
            content_length = len(parsed_content)
            tracker.update_processing_results(doc.doc_id, chunk_count, content_length, metadata is not None)
            tracker.update_file_status(file_record.doc_id, ProcessingStatus.COMPLETED)
            
            processed_count += 1
            print(f"   ✅ Completed successfully ({chunk_count} chunks, {content_length:,} chars)")
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")
            tracker.update_file_status(file_record.doc_id, ProcessingStatus.FAILED, str(e))
            failed_count += 1
    
    print(f"\n🎉 Processing completed!")
    print(f"   ✅ Successfully processed: {processed_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📊 Success rate: {(processed_count/(processed_count+failed_count)*100):.1f}%")

if __name__ == "__main__":
    asyncio.run(process_discovered_files())