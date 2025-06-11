"""
Scale up processing for all CARE documents
"""

import asyncio
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))

from ingest import FileIngestionAgent, DocumentInfo
from parse import LlamaParseAgent
from extract_metadata import MetadataExtractionAgent
from clean_chunk import TextCleaningChunkingAgent


class BatchProcessor:
    """Handles batch processing of documents with progress tracking and error handling"""
    
    def __init__(self, batch_size: int = 5, max_concurrent: int = 2):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.results = {
            'successful': [],
            'failed': [],
            'total_processed': 0,
            'total_chunks': 0,
            'processing_time': 0
        }
    
    async def process_documents_batch(self, 
                                    documents: List[DocumentInfo],
                                    agents: Dict[str, Any]) -> Dict[str, Any]:
        """Process documents in batches with error handling"""
        
        start_time = time.time()
        total_docs = len(documents)
        
        print(f"🚀 Starting batch processing of {total_docs} documents")
        print(f"📊 Batch size: {self.batch_size}, Max concurrent: {self.max_concurrent}")
        
        # Process in batches
        for i in range(0, total_docs, self.batch_size):
            batch = documents[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (total_docs + self.batch_size - 1) // self.batch_size
            
            print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} documents)")
            
            # Process batch with concurrency control
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def process_single_doc(doc_info):
                async with semaphore:
                    return await self._process_single_document(doc_info, agents)
            
            batch_tasks = [process_single_doc(doc) for doc in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Collect results
            for doc_info, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    print(f"❌ {doc_info.filename}: {result}")
                    self.results['failed'].append({
                        'filename': doc_info.filename,
                        'doc_id': doc_info.doc_id,
                        'error': str(result)
                    })
                elif result and result.get('success'):
                    print(f"✅ {doc_info.filename}: {result['chunks']} chunks")
                    self.results['successful'].append(result)
                    self.results['total_chunks'] += result['chunks']
                else:
                    print(f"⚠️ {doc_info.filename}: Processing failed")
                    self.results['failed'].append({
                        'filename': doc_info.filename,
                        'doc_id': doc_info.doc_id,
                        'error': 'Unknown processing error'
                    })
            
            self.results['total_processed'] += len(batch)
            
            # Progress update
            progress = (self.results['total_processed'] / total_docs) * 100
            print(f"📈 Progress: {self.results['total_processed']}/{total_docs} ({progress:.1f}%)")
            print(f"   ✅ Successful: {len(self.results['successful'])}")
            print(f"   ❌ Failed: {len(self.results['failed'])}")
            print(f"   📄 Total chunks: {self.results['total_chunks']}")
            
            # Longer delay between batches to respect API rate limits
            if i + self.batch_size < total_docs:
                print(f"😴 Waiting 10 seconds before next batch to respect API limits...")
                await asyncio.sleep(10)
        
        self.results['processing_time'] = time.time() - start_time
        return self.results
    
    async def _process_single_document(self, 
                                     doc_info: DocumentInfo, 
                                     agents: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single document through the full pipeline"""
        try:
            parse_agent = agents['parse']
            metadata_agent = agents['metadata'] 
            chunk_agent = agents['chunk']
            
            # Step 1: Parse document
            parsed_doc = await parse_agent.parse_document(doc_info)
            if parsed_doc.error:
                raise Exception(f"Parse failed: {parsed_doc.error}")
            
            # Step 2: Extract metadata
            extracted_metadata = await metadata_agent.extract_metadata(parsed_doc, doc_info.category)
            
            # Step 3: Clean and chunk
            chunks = chunk_agent.chunk_document(parsed_doc, extracted_metadata)
            
            # Step 4: Save results
            parse_agent.save_parsed_content(parsed_doc)
            metadata_agent.save_metadata(extracted_metadata)
            chunk_agent.save_chunks(chunks)
            
            return {
                'success': True,
                'doc_id': doc_info.doc_id,
                'filename': doc_info.filename,
                'chunks': len(chunks),
                'content_length': len(parsed_doc.markdown_content),
                'metadata_success': extracted_metadata.extraction_success
            }
            
        except Exception as e:
            return {
                'success': False,
                'doc_id': doc_info.doc_id,
                'filename': doc_info.filename,
                'error': str(e)
            }
    
    def save_results_summary(self, output_file: str = "data/processing_summary.json"):
        """Save processing results summary"""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        summary = {
            'processing_summary': {
                'total_documents': self.results['total_processed'],
                'successful': len(self.results['successful']),
                'failed': len(self.results['failed']),
                'success_rate': len(self.results['successful']) / self.results['total_processed'] * 100,
                'total_chunks_created': self.results['total_chunks'],
                'processing_time_seconds': self.results['processing_time'],
                'avg_time_per_doc': self.results['processing_time'] / self.results['total_processed']
            },
            'successful_documents': self.results['successful'],
            'failed_documents': self.results['failed']
        }
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📊 Results summary saved to: {output_file}")


async def main():
    """Scale up processing for all CARE documents"""
    
    print("🏥 SCALING UP: Processing ALL CARE documents")
    
    # Initialize agents with conservative settings
    ingestion_agent = FileIngestionAgent()
    parse_agent = LlamaParseAgent(verbose=False, num_workers=2)  # Reduce workers to respect API limits
    metadata_agent = MetadataExtractionAgent(verbose=False)
    chunk_agent = TextCleaningChunkingAgent(verbose=False)
    
    agents = {
        'parse': parse_agent,
        'metadata': metadata_agent,
        'chunk': chunk_agent
    }
    
    # Get all CARE documents
    all_documents = ingestion_agent.discover_documents()
    care_documents = ingestion_agent.filter_by_filename_prefix(all_documents, "CARE")
    
    print(f"📂 Total documents: {len(all_documents)}")
    print(f"🏥 CARE documents: {len(care_documents)}")
    
    if not care_documents:
        print("❌ No CARE documents found!")
        return
    
    # Initialize batch processor with conservative settings
    processor = BatchProcessor(batch_size=3, max_concurrent=1)  # Very conservative to avoid rate limits
    
    # Process all documents
    results = await processor.process_documents_batch(care_documents, agents)
    
    # Save summary
    processor.save_results_summary()
    
    # Print final results
    print(f"\n🎉 PROCESSING COMPLETE!")
    print(f"📊 Final Results:")
    print(f"   📄 Documents processed: {results['total_processed']}")
    print(f"   ✅ Successful: {len(results['successful'])} ({len(results['successful'])/results['total_processed']*100:.1f}%)")
    print(f"   ❌ Failed: {len(results['failed'])} ({len(results['failed'])/results['total_processed']*100:.1f}%)")
    print(f"   📝 Total chunks created: {results['total_chunks']}")
    print(f"   ⏱️  Total time: {results['processing_time']:.1f} seconds")
    print(f"   📈 Avg time per doc: {results['processing_time']/results['total_processed']:.1f} seconds")
    
    if results['failed']:
        print(f"\n⚠️  Failed documents:")
        for failed in results['failed'][:5]:  # Show first 5 failures
            print(f"   - {failed['filename']}: {failed['error']}")
        if len(results['failed']) > 5:
            print(f"   ... and {len(results['failed']) - 5} more (see processing_summary.json)")


if __name__ == "__main__":
    asyncio.run(main())