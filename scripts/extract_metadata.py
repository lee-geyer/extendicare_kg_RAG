"""
Metadata Extraction Agent
Responsible for extracting structured metadata from parsed documents using LlamaExtract.
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
import json
from dotenv import load_dotenv

try:
    from llama_parse import LlamaParse as LlamaExtract
except ImportError:
    print("Warning: llama-parse not installed. Install with: uv add llama-parse")
    LlamaExtract = None

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from configs.schema_policy import (
    PolicyMeta, ProcedureMeta, EducationMeta, ToolMeta, GenericDocumentMeta,
    get_schema_for_category
)
from parse import ParsedDocument

load_dotenv()


@dataclass
class ExtractedMetadata:
    """Container for extracted metadata"""
    doc_id: str
    category: str
    metadata: Dict[str, Any]
    schema_used: str
    extraction_success: bool
    error: Optional[str] = None
    fallback_metadata: Optional[Dict[str, Any]] = None


class MetadataExtractionAgent:
    """
    Agent responsible for extracting structured metadata from parsed documents.
    Uses LlamaExtract with category-specific schemas and regex fallbacks.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 verbose: bool = True):
        """
        Initialize Metadata Extraction Agent
        
        Args:
            api_key: LlamaCloud API key (will use LLAMA_CLOUD_API_KEY env var if not provided)
            verbose: Enable verbose logging
        """
        self.api_key = api_key or os.getenv('LLAMA_CLOUD_API_KEY')
        if not self.api_key:
            print("Warning: No LLAMA_CLOUD_API_KEY found, using regex-only extraction")
        
        self.verbose = verbose
        self.extractor = None  # Use regex-only for now
    
    async def extract_metadata(self, 
                             parsed_doc: ParsedDocument, 
                             category: str) -> ExtractedMetadata:
        """
        Extract metadata from a parsed document using appropriate schema
        
        Args:
            parsed_doc: ParsedDocument with content to extract from
            category: Document category to determine schema
            
        Returns:
            ExtractedMetadata object with structured information
        """
        try:
            # Get appropriate schema for category
            schema_class = get_schema_for_category(category)
            schema_name = schema_class.__name__
            
            if self.verbose:
                print(f"Extracting metadata for {parsed_doc.doc_id} using {schema_name}")
            
            # Extract metadata using LlamaExtract
            extraction_schema = schema_class.model_json_schema()
            
            # Use regex-based extraction for now
            regex_metadata = self._extract_metadata_regex(
                parsed_doc.markdown_content, 
                schema_class
            )
            
            return ExtractedMetadata(
                doc_id=parsed_doc.doc_id,
                category=category,
                metadata=regex_metadata,
                schema_used=schema_name,
                extraction_success=True
            )
        
        except Exception as e:
            error_msg = f"Failed to extract metadata from {parsed_doc.doc_id}: {str(e)}"
            if self.verbose:
                print(f"Error: {error_msg}")
            
            return ExtractedMetadata(
                doc_id=parsed_doc.doc_id,
                category=category,
                metadata={},
                schema_used="None",
                extraction_success=False,
                error=error_msg
            )
    
    def _extract_metadata_regex(self, 
                               content: str, 
                               schema_class) -> Dict[str, Any]:
        """
        Fallback metadata extraction using regex patterns
        
        Args:
            content: Document content to extract from
            schema_class: Pydantic schema class for structure
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {}
        
        # Common regex patterns for different metadata fields
        patterns = {
            'title': [
                r'^#\s+(.+?)$',  # Markdown H1
                r'Title:\s*(.+?)(?:\n|$)',
                r'Policy:\s*(.+?)(?:\n|$)',
                r'Procedure:\s*(.+?)(?:\n|$)',
            ],
            'policy_index': [
                r'Policy\s*#?\s*:?\s*([A-Z]+-?\d+(?:\.\d+)?)',
                r'Index:\s*([A-Z]+-?\d+(?:\.\d+)?)',
                r'Number:\s*([A-Z]+-?\d+(?:\.\d+)?)',
            ],
            'procedure_index': [
                r'Procedure\s*#?\s*:?\s*([A-Z]+-?\d+(?:\.\d+)?)',
                r'SOP:\s*([A-Z]+-?\d+(?:\.\d+)?)',
            ],
            'effective_date': [
                r'Effective\s*Date:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
                r'Effective:\s*(\d{4}-\d{2}-\d{2})',
                r'Date\s*Effective:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            ],
            'review_date': [
                r'Review\s*Date:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
                r'Next\s*Review:\s*(\d{4}-\d{2}-\d{2})',
            ],
            'department': [
                r'Department:\s*(.+?)(?:\n|$)',
                r'Division:\s*(.+?)(?:\n|$)',
                r'Responsible:\s*(.+?)(?:\n|$)',
            ],
            'version': [
                r'Version:\s*(\d+(?:\.\d+)?)',
                r'Ver\.?\s*(\d+(?:\.\d+)?)',
                r'V\s*(\d+(?:\.\d+)?)',
            ]
        }
        
        # Extract based on available schema fields
        schema_fields = schema_class.model_fields.keys()
        
        for field_name in schema_fields:
            if field_name in patterns:
                for pattern in patterns[field_name]:
                    match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                    if match:
                        metadata[field_name] = match.group(1).strip()
                        break
        
        # Always try to extract title from first line if not found
        if 'title' not in metadata:
            lines = content.strip().split('\n')
            for line in lines[:5]:  # Check first 5 lines
                line = line.strip('#* \t')
                if len(line) > 10 and len(line) < 200:  # Reasonable title length
                    metadata['title'] = line
                    break
        
        return metadata
    
    def save_metadata(self, 
                     extracted_metadata: ExtractedMetadata, 
                     output_dir: str = "data/metadata"):
        """
        Save extracted metadata to JSON file
        
        Args:
            extracted_metadata: ExtractedMetadata to save
            output_dir: Directory to save metadata files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        metadata_file = output_path / f"{extracted_metadata.doc_id}_metadata.json"
        
        # Prepare data for JSON serialization
        save_data = {
            "doc_id": extracted_metadata.doc_id,
            "category": extracted_metadata.category,
            "schema_used": extracted_metadata.schema_used,
            "extraction_success": extracted_metadata.extraction_success,
            "metadata": extracted_metadata.metadata,
            "error": extracted_metadata.error,
            "fallback_metadata": extracted_metadata.fallback_metadata
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            print(f"Saved metadata: {metadata_file}")


async def main():
    """Test the Metadata Extraction Agent"""
    try:
        # Import here to avoid circular imports in testing
        from ingest import FileIngestionAgent
        from parse import LlamaParseAgent
        
        # Initialize agents
        ingestion_agent = FileIngestionAgent()
        parse_agent = LlamaParseAgent()
        metadata_agent = MetadataExtractionAgent()
        
        # Get first document for testing
        documents = ingestion_agent.discover_documents()
        if not documents:
            print("No documents found")
            return
        
        test_doc = documents[0]
        print(f"Testing with document: {test_doc.filename} (category: {test_doc.category})")
        
        # Parse document
        parsed_doc = await parse_agent.parse_document(test_doc)
        if parsed_doc.error:
            print(f"Parse error: {parsed_doc.error}")
            return
        
        # Extract metadata
        extracted_metadata = await metadata_agent.extract_metadata(
            parsed_doc, 
            test_doc.category
        )
        
        # Save results
        metadata_agent.save_metadata(extracted_metadata)
        
        # Print results
        print(f"\nExtraction Results:")
        print(f"Success: {extracted_metadata.extraction_success}")
        print(f"Schema: {extracted_metadata.schema_used}")
        if extracted_metadata.metadata:
            print(f"Metadata: {json.dumps(extracted_metadata.metadata, indent=2)}")
        if extracted_metadata.fallback_metadata:
            print(f"Fallback: {json.dumps(extracted_metadata.fallback_metadata, indent=2)}")
        if extracted_metadata.error:
            print(f"Error: {extracted_metadata.error}")
        
    except Exception as e:
        print(f"Error in main: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())