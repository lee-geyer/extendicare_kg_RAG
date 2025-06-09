"""
Process all document categories with expansion scope
Skips already processed CARE documents
"""

import asyncio
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Set

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))

from ingest import FileIngestionAgent, DocumentInfo
from parse import LlamaParseAgent
from extract_metadata import MetadataExtractionAgent
from clean_chunk import TextCleaningChunkingAgent


class AllCategoriesProcessor:
    """Handles processing of all document categories with skip logic"""
    
    def __init__(self, batch_size: int = 3, max_concurrent: int = 2):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.results = {
            'successful': [],
            'failed': [],
            'skipped': [],
            'total_processed': 0,
        }
        
        # Target categories for expansion
        self.target_categories = [
            "Care",  # Already processed but include for completeness
            "Emergency Planning and Management",
            "Environmental Services", 
            "Infection Prevention and Control",
            "Privacy and Confidentiality"
        ]
    
    def get_already_processed_files(self) -> Set[str]:
        """Get set of already processed document IDs"""
        parsed_dir = Path("data/parsed")
        processed = set()
        
        if parsed_dir.exists():
            for md_file in parsed_dir.glob("*.md"):
                processed.add(md_file.stem)
        
        print(f"📋 Found {len(processed)} already processed documents")
        return processed
    
    def filter_unprocessed_documents(self, documents: List[DocumentInfo]) -> List[DocumentInfo]:
        """Filter out already processed documents"""
        processed_ids = self.get_already_processed_files()
        
        unprocessed = []
        skipped_count = 0
        
        for doc in documents:
            # Generate expected document ID (same logic as in the pipeline)
            doc_id = self.generate_document_id(doc)
            
            if doc_id in processed_ids:
                skipped_count += 1
                self.results['skipped'].append({
                    'doc_id': doc_id,
                    'filename': doc.filename,
                    'reason': 'Already processed'
                })
            else:
                unprocessed.append(doc)
        
        print(f"⏭️  Skipping {skipped_count} already processed documents")
        print(f"🔄 {len(unprocessed)} documents remaining to process")
        
        return unprocessed
    
    def generate_document_id(self, doc) -> str:
        """Generate document ID using same logic as processing pipeline"""
        import hashlib
        
        # Handle both DocumentInfo objects and Path objects
        if hasattr(doc, 'filename'):
            base_name = doc.filename.lower()
            file_path = doc.file_path
        else:
            base_name = doc.name.lower()
            file_path = doc
        
        # Remove file extension
        base_name = base_name.rsplit('.', 1)[0]
        
        # Clean up the name - remove spaces, special chars, etc.
        import re
        clean_name = re.sub(r'[^\w\-]', '', base_name.replace(' ', '').replace('-', ''))
        
        # Create short hash from file path for uniqueness
        path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:12]
        
        return f"{clean_name}_{path_hash}"
    
    async def process_document(self, doc: DocumentInfo, agents: Dict) -> Dict[str, Any]:
        """Process a single document through the pipeline"""
        try:
            # Handle both DocumentInfo objects and Path objects
            if hasattr(doc, 'filename'):
                filename = doc.filename
                file_path = doc.file_path
            else:
                # If it's a Path object, extract filename
                filename = doc.name
                file_path = doc
            
            print(f"\n🔄 Processing: {filename}")
            start_time = time.time()
            
            # Generate document ID
            doc_id = self.generate_document_id(doc)
            
            # Step 1: Parse with LlamaParse
            print(f"   📄 Parsing...")
            parsed_content = await agents['parse'].parse_document(file_path)
            if not parsed_content:
                raise Exception("Failed to parse document")
            
            # Step 2: Extract metadata
            print(f"   🏷️  Extracting metadata...")
            metadata = await agents['metadata'].extract_metadata(parsed_content, doc)
            
            # Step 3: Clean and chunk
            print(f"   ✂️  Cleaning and chunking...")
            chunks_result = await agents['chunk'].process_document(
                content=parsed_content,
                doc_info=doc,
                doc_id=doc_id
            )
            
            processing_time = time.time() - start_time
            
            result = {
                'success': True,
                'doc_id': doc_id,
                'filename': filename,
                'category': getattr(doc, 'category', 'Unknown'),
                'chunks': len(chunks_result.get('chunks', [])),
                'content_length': len(parsed_content),
                'metadata_success': metadata is not None,
                'processing_time': processing_time
            }
            
            print(f"   ✅ Completed in {processing_time:.1f}s - {result['chunks']} chunks")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"   ❌ Failed after {processing_time:.1f}s: {str(e)}")
            # Handle error case with same filename logic
            if hasattr(doc, 'filename'):
                filename = doc.filename
            else:
                filename = doc.name if hasattr(doc, 'name') else 'unknown'
            
            return {
                'success': False,
                'doc_id': getattr(doc, 'doc_id', 'unknown'),
                'filename': filename,
                'category': getattr(doc, 'category', 'Unknown'),
                'error': str(e),
                'processing_time': processing_time
            }
    
    async def process_batch(self, documents: List[DocumentInfo], agents: Dict) -> List[Dict]:
        """Process a batch of documents concurrently"""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_with_semaphore(doc):
            async with semaphore:
                return await self.process_document(doc, agents)
        
        tasks = [process_with_semaphore(doc) for doc in documents]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def process_all_categories(self):
        """Main processing function"""
        print("🚀 Starting expanded category processing...")
        start_time = time.time()
        
        # Initialize agents
        print("🔧 Initializing processing agents...")
        agents = {
            'parse': LlamaParseAgent(),
            'metadata': MetadataExtractionAgent(),
            'chunk': TextCleaningChunkingAgent()
        }
        
        # Discover documents in target categories
        print("🔍 Discovering documents...")
        ingestion_agent = FileIngestionAgent("data/raw/extendicare_kb")
        all_documents = ingestion_agent.discover_documents()
        
        # Filter to target categories
        target_docs = []
        for doc in all_documents:
            if doc.category in self.target_categories:
                target_docs.append(doc)
        
        print(f"📁 Found {len(target_docs)} documents in target categories:")
        for category in self.target_categories:
            count = len([d for d in target_docs if d.category == category])
            print(f"   - {category}: {count} files")
        
        # Filter out already processed documents
        unprocessed_docs = self.filter_unprocessed_documents(target_docs)
        
        if not unprocessed_docs:
            print("🎉 All documents in target categories are already processed!")
            return
        
        # Process in batches
        total_batches = (len(unprocessed_docs) + self.batch_size - 1) // self.batch_size
        print(f"\n🔄 Processing {len(unprocessed_docs)} documents in {total_batches} batches")
        print(f"⚙️  Batch size: {self.batch_size}, Max concurrent: {self.max_concurrent}")
        
        for i in range(0, len(unprocessed_docs), self.batch_size):
            batch = unprocessed_docs[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} documents)")
            
            # Process batch
            batch_results = await self.process_batch(batch, agents)
            
            # Handle results
            for result in batch_results:
                if isinstance(result, Exception):
                    self.results['failed'].append({
                        'error': str(result),
                        'batch': batch_num
                    })
                elif result.get('success'):
                    self.results['successful'].append(result)
                else:
                    self.results['failed'].append(result)
            
            # Progress update
            total_completed = len(self.results['successful']) + len(self.results['failed'])
            progress = (total_completed / len(unprocessed_docs)) * 100
            print(f"📊 Progress: {total_completed}/{len(unprocessed_docs)} ({progress:.1f}%)")
            
            # Rate limiting delay between batches
            if batch_num < total_batches:
                print("⏸️  Rate limiting pause...")
                await asyncio.sleep(10)
        
        # Final summary
        total_time = time.time() - start_time
        self.save_results(total_time)
        self.print_summary(total_time)
    
    def save_results(self, total_time: float):
        """Save processing results to file"""
        summary = {
            'processing_summary': {
                'total_documents': len(self.results['successful']) + len(self.results['failed']),
                'successful': len(self.results['successful']),
                'failed': len(self.results['failed']),
                'skipped': len(self.results['skipped']),
                'success_rate': len(self.results['successful']) / max(1, len(self.results['successful']) + len(self.results['failed'])) * 100,
                'total_chunks_created': sum(r.get('chunks', 0) for r in self.results['successful']),
                'processing_time_seconds': total_time,
                'avg_time_per_doc': total_time / max(1, len(self.results['successful']) + len(self.results['failed']))
            },
            'successful_documents': self.results['successful'],
            'failed_documents': self.results['failed'],
            'skipped_documents': self.results['skipped']
        }
        
        # Save to file
        output_file = Path("data/expanded_processing_summary.json")
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"💾 Results saved to {output_file}")
    
    def print_summary(self, total_time: float):
        """Print processing summary"""
        successful = len(self.results['successful'])
        failed = len(self.results['failed'])
        skipped = len(self.results['skipped'])
        total_attempted = successful + failed
        
        print(f"\n" + "="*60)
        print("🎉 EXPANDED PROCESSING COMPLETE!")
        print("="*60)
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"📊 Success rate: {(successful/max(1,total_attempted)*100):.1f}%")
        print(f"⏱️  Total time: {total_time/3600:.1f} hours")
        print(f"📈 Average per doc: {total_time/max(1,total_attempted):.1f} seconds")
        
        if successful > 0:
            total_chunks = sum(r.get('chunks', 0) for r in self.results['successful'])
            print(f"✂️  Total chunks: {total_chunks:,}")
            print(f"📄 Avg chunks/doc: {total_chunks/successful:.1f}")


async def main():
    processor = AllCategoriesProcessor(batch_size=3, max_concurrent=2)
    await processor.process_all_categories()


if __name__ == "__main__":
    asyncio.run(main())