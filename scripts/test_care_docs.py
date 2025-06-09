"""
Test script for processing CARE documents specifically
"""

import asyncio
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))

from ingest import FileIngestionAgent
from parse import LlamaParseAgent
from extract_metadata import MetadataExtractionAgent
from clean_chunk import TextCleaningChunkingAgent


async def process_care_documents():
    """Process documents that start with 'CARE' prefix"""
    print("🏥 Processing CARE documents...")
    
    # Initialize agents
    ingestion_agent = FileIngestionAgent()
    parse_agent = LlamaParseAgent(verbose=True)
    metadata_agent = MetadataExtractionAgent(verbose=True)
    chunk_agent = TextCleaningChunkingAgent(verbose=True)
    
    # Discover all documents
    all_documents = ingestion_agent.discover_documents()
    print(f"📂 Total documents found: {len(all_documents)}")
    
    # Filter for CARE documents
    care_documents = ingestion_agent.filter_by_filename_prefix(all_documents, "CARE")
    print(f"🏥 CARE documents found: {len(care_documents)}")
    
    if not care_documents:
        print("❌ No CARE documents found")
        return
    
    # Show first few CARE documents
    print("\n📋 CARE documents to process:")
    for i, doc in enumerate(care_documents[:5]):
        print(f"  {i+1}. {doc.filename} ({doc.category})")
    if len(care_documents) > 5:
        print(f"  ... and {len(care_documents) - 5} more")
    
    # Process first few documents for testing
    test_documents = care_documents[:3]  # Start with first 3
    print(f"\n🚀 Processing {len(test_documents)} documents...")
    
    for i, doc_info in enumerate(test_documents, 1):
        print(f"\n--- Processing {i}/{len(test_documents)}: {doc_info.filename} ---")
        
        try:
            # Step 1: Parse document
            print("📄 Parsing document...")
            parsed_doc = await parse_agent.parse_document(doc_info)
            
            if parsed_doc.error:
                print(f"❌ Parse failed: {parsed_doc.error}")
                continue
            
            print(f"✅ Parsed successfully ({len(parsed_doc.markdown_content)} characters)")
            
            # Step 2: Extract metadata
            print("🏷️  Extracting metadata...")
            extracted_metadata = await metadata_agent.extract_metadata(parsed_doc, doc_info.category)
            
            if extracted_metadata.extraction_success:
                print("✅ Metadata extracted successfully")
                print(f"   Schema: {extracted_metadata.schema_used}")
                if extracted_metadata.metadata.get('title'):
                    print(f"   Title: {extracted_metadata.metadata['title']}")
            else:
                print(f"⚠️  Metadata extraction failed: {extracted_metadata.error}")
                if extracted_metadata.fallback_metadata:
                    print("   Using fallback regex extraction")
            
            # Step 3: Clean and chunk
            print("✂️  Cleaning and chunking...")
            chunks = chunk_agent.chunk_document(parsed_doc, extracted_metadata)
            print(f"✅ Created {len(chunks)} chunks")
            
            # Step 4: Save results
            print("💾 Saving results...")
            parse_agent.save_parsed_content(parsed_doc)
            metadata_agent.save_metadata(extracted_metadata)
            chunk_agent.save_chunks(chunks)
            
            print(f"✅ Completed processing {doc_info.filename}")
            
        except Exception as e:
            print(f"❌ Error processing {doc_info.filename}: {e}")
            continue
    
    print(f"\n🎉 Completed processing {len(test_documents)} CARE documents!")
    print("\n📁 Check these directories for results:")
    print("   - data/parsed/ (markdown content and chunks)")
    print("   - data/metadata/ (extracted metadata)")


if __name__ == "__main__":
    asyncio.run(process_care_documents())