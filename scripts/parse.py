"""
LlamaParse Agent
Responsible for parsing documents using LlamaParse to extract structured content.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import asyncio
import json
from dotenv import load_dotenv

try:
    from llama_parse import LlamaParse
except ImportError:
    print("Warning: llama-parse not installed. Install with: uv add llama-parse")
    LlamaParse = None

from ingest import DocumentInfo

load_dotenv()


@dataclass 
class ParsedDocument:
    """Container for parsed document content and metadata"""
    doc_id: str
    original_file: Path
    markdown_content: str
    page_metadata: Optional[List[Dict[str, Any]]] = None
    parse_job_id: Optional[str] = None
    error: Optional[str] = None


class LlamaParseAgent:
    """
    Agent responsible for parsing documents using LlamaParse service.
    Extracts structured content while preserving layout, headers, tables, etc.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 language: str = 'en',
                 system_prompt: Optional[str] = None,
                 user_prompt: Optional[str] = None,
                 num_workers: int = 4,
                 verbose: bool = True):
        """
        Initialize LlamaParse Agent
        
        Args:
            api_key: LlamaCloud API key (will use LLAMA_CLOUD_API_KEY env var if not provided)
            language: Document language code 
            system_prompt: System-level parsing instructions
            user_prompt: User-specific parsing instructions
            num_workers: Number of concurrent workers
            verbose: Enable verbose logging
        """
        self.api_key = api_key or os.getenv('LLAMA_CLOUD_API_KEY')
        if not self.api_key:
            raise ValueError("LLAMA_CLOUD_API_KEY environment variable or api_key parameter required")
        
        self.language = language
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.user_prompt = user_prompt or self._get_default_user_prompt()
        self.num_workers = num_workers
        self.verbose = verbose
        
        # Initialize parser
        if LlamaParse is None:
            raise ImportError("llama-parse package required. Install with: uv add llama-parse")
            
        self.parser = LlamaParse(
            api_key=self.api_key,
            result_type="markdown",
            language=self.language,
            system_prompt=self.system_prompt,
            user_prompt=self.user_prompt,
            num_workers=self.num_workers,
            verbose=self.verbose
        )
    
    def _get_default_system_prompt(self) -> str:
        """Default system prompt optimized for policy documents"""
        return """You are a document parsing assistant specialized in extracting content from policy, procedure, and care documents. Your goal is to preserve the document structure and important information while converting to markdown format."""
    
    def _get_default_user_prompt(self) -> str:
        """Default user prompt with specific parsing instructions"""
        return """
        Extract and preserve the complete document structure including:
        - All headers and subheaders with proper hierarchy
        - Tables in markdown format with clear column alignment
        - Lists and bullet points with proper indentation
        - Policy numbers, effective dates, and review dates
        - Section references and cross-references
        - Maintain original formatting for readability
        - Preserve any document metadata tables at the beginning
        """
    
    async def parse_document(self, doc_info: DocumentInfo) -> ParsedDocument:
        """
        Parse a single document using LlamaParse
        
        Args:
            doc_info: DocumentInfo object with file path and metadata
            
        Returns:
            ParsedDocument with extracted content
        """
        try:
            if self.verbose:
                print(f"Parsing document: {doc_info.filename}")
            
            # Parse the document
            documents = await self.parser.aload_data(str(doc_info.file_path))
            
            if not documents:
                return ParsedDocument(
                    doc_id=doc_info.doc_id,
                    original_file=doc_info.file_path,
                    markdown_content="",
                    error="No content extracted from document"
                )
            
            # Combine all pages into single markdown content
            markdown_content = "\n\n".join([doc.text for doc in documents])
            
            # Extract page metadata if available
            page_metadata = []
            for i, doc in enumerate(documents):
                metadata = {
                    "page_number": i + 1,
                    "char_count": len(doc.text),
                }
                # Add any additional metadata from the document
                if hasattr(doc, 'metadata') and doc.metadata:
                    metadata.update(doc.metadata)
                page_metadata.append(metadata)
            
            return ParsedDocument(
                doc_id=doc_info.doc_id,
                original_file=doc_info.file_path,
                markdown_content=markdown_content,
                page_metadata=page_metadata
            )
            
        except Exception as e:
            error_msg = f"Failed to parse document {doc_info.filename}: {str(e)}"
            if self.verbose:
                print(f"Error: {error_msg}")
            
            return ParsedDocument(
                doc_id=doc_info.doc_id,
                original_file=doc_info.file_path,
                markdown_content="",
                error=error_msg
            )
    
    async def parse_documents_batch(self, doc_infos: List[DocumentInfo]) -> List[ParsedDocument]:
        """
        Parse multiple documents concurrently
        
        Args:
            doc_infos: List of DocumentInfo objects
            
        Returns:
            List of ParsedDocument results
        """
        if self.verbose:
            print(f"Parsing {len(doc_infos)} documents...")
        
        # Create tasks for concurrent processing
        tasks = [self.parse_document(doc_info) for doc_info in doc_infos]
        
        # Execute with concurrency limit
        semaphore = asyncio.Semaphore(self.num_workers)
        
        async def parse_with_semaphore(task):
            async with semaphore:
                return await task
        
        limited_tasks = [parse_with_semaphore(task) for task in tasks]
        results = await asyncio.gather(*limited_tasks, return_exceptions=True)
        
        # Handle any exceptions
        parsed_docs = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                parsed_docs.append(ParsedDocument(
                    doc_id=doc_infos[i].doc_id,
                    original_file=doc_infos[i].file_path,
                    markdown_content="",
                    error=f"Parse failed with exception: {str(result)}"
                ))
            else:
                parsed_docs.append(result)
        
        return parsed_docs
    
    def save_parsed_content(self, parsed_doc: ParsedDocument, output_dir: str = "data/parsed"):
        """
        Save parsed document content to file
        
        Args:
            parsed_doc: ParsedDocument to save
            output_dir: Directory to save parsed content
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save markdown content
        markdown_file = output_path / f"{parsed_doc.doc_id}.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(parsed_doc.markdown_content)
        
        # Save metadata if available
        if parsed_doc.page_metadata:
            metadata_file = output_path / f"{parsed_doc.doc_id}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "doc_id": parsed_doc.doc_id,
                    "original_file": str(parsed_doc.original_file),
                    "page_metadata": parsed_doc.page_metadata,
                    "parse_job_id": parsed_doc.parse_job_id,
                    "error": parsed_doc.error
                }, f, indent=2)
        
        if self.verbose:
            print(f"Saved parsed content: {markdown_file}")


async def main():
    """Test the LlamaParse Agent"""
    try:
        # Import here to avoid circular imports in testing
        from ingest import FileIngestionAgent
        
        # Initialize agents
        ingestion_agent = FileIngestionAgent()
        parse_agent = LlamaParseAgent()
        
        # Discover documents
        documents = ingestion_agent.discover_documents()
        print(f"Found {len(documents)} documents")
        
        if not documents:
            print("No documents found to parse")
            return
        
        # Parse first few documents for testing
        test_docs = documents[:2]  # Limit for testing
        parsed_results = await parse_agent.parse_documents_batch(test_docs)
        
        # Save results
        for parsed_doc in parsed_results:
            if parsed_doc.error:
                print(f"Error parsing {parsed_doc.doc_id}: {parsed_doc.error}")
            else:
                parse_agent.save_parsed_content(parsed_doc)
                print(f"Successfully parsed {parsed_doc.doc_id} ({len(parsed_doc.markdown_content)} chars)")
        
    except Exception as e:
        print(f"Error in main: {e}")


if __name__ == "__main__":
    asyncio.run(main())