"""
Test processing with conservative rate limits to avoid 429 errors
"""

import asyncio
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))

from process_all_care import BatchProcessor, main
from ingest import FileIngestionAgent
from parse import LlamaParseAgent
from extract_metadata import MetadataExtractionAgent
from clean_chunk import TextCleaningChunkingAgent


async def test_small_batch():
    """Test with a very small batch to validate rate limiting"""
    
    print("🧪 Testing rate limit handling with small batch")
    
    # Initialize agents with very conservative settings
    ingestion_agent = FileIngestionAgent()
    parse_agent = LlamaParseAgent(verbose=True, num_workers=1)  # Single worker
    metadata_agent = MetadataExtractionAgent(verbose=True)
    chunk_agent = TextCleaningChunkingAgent(verbose=True)
    
    agents = {
        'parse': parse_agent,
        'metadata': metadata_agent,
        'chunk': chunk_agent
    }
    
    # Get small subset of CARE documents
    all_documents = ingestion_agent.discover_documents()
    care_documents = ingestion_agent.filter_by_filename_prefix(all_documents, "CARE")
    
    # Test with just 6 documents (2 batches of 3)
    test_documents = care_documents[:6]
    
    print(f"🏥 Testing with {len(test_documents)} CARE documents:")
    for i, doc in enumerate(test_documents, 1):
        print(f"  {i}. {doc.filename}")
    
    # Initialize very conservative batch processor
    processor = BatchProcessor(batch_size=2, max_concurrent=1)
    
    # Process documents
    results = await processor.process_documents_batch(test_documents, agents)
    
    # Save summary
    processor.save_results_summary("data/test_processing_summary.json")
    
    # Print results
    print(f"\n🧪 Test Results:")
    print(f"   📄 Documents processed: {results['total_processed']}")
    print(f"   ✅ Successful: {len(results['successful'])}")
    print(f"   ❌ Failed: {len(results['failed'])}")
    print(f"   📝 Total chunks: {results['total_chunks']}")
    print(f"   ⏱️  Total time: {results['processing_time']:.1f} seconds")
    
    if len(results['successful']) >= 4:  # At least 4 out of 6 successful
        print("✅ Rate limiting test PASSED - ready for full scale processing")
        return True
    else:
        print("❌ Rate limiting test FAILED - need to adjust settings further")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_small_batch())
    if success:
        print("\n🚀 Rate limiting validated. Ready to scale up!")
    else:
        print("\n⚠️  Need to adjust rate limiting before scaling up.")