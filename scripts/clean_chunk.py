"""
Text Cleaning & Chunking Agent
Responsible for cleaning parsed document content and splitting it into optimized chunks.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib

from parse import ParsedDocument
from extract_metadata import ExtractedMetadata


@dataclass
class DocumentChunk:
    """Container for a document chunk with metadata"""
    chunk_id: str
    doc_id: str
    chunk_index: int
    text: str
    char_count: int
    token_estimate: int
    section_title: Optional[str] = None
    chunk_type: str = "content"  # content, header, table, list
    start_line: Optional[int] = None
    end_line: Optional[int] = None


class TextCleaningChunkingAgent:
    """
    Agent responsible for cleaning document text and creating optimized chunks.
    Removes repetitive content, normalizes formatting, and chunks by semantic boundaries.
    """
    
    def __init__(self, 
                 target_chunk_size: int = 300,
                 chunk_overlap: int = 50,
                 max_chunk_size: int = 500,
                 min_chunk_size: int = 100,
                 verbose: bool = True):
        """
        Initialize Text Cleaning & Chunking Agent
        
        Args:
            target_chunk_size: Target chunk size in tokens
            chunk_overlap: Number of tokens to overlap between chunks
            max_chunk_size: Maximum allowed chunk size
            min_chunk_size: Minimum chunk size (smaller chunks will be merged)
            verbose: Enable verbose logging
        """
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.verbose = verbose
        
        # Common patterns to remove
        self.cleanup_patterns = [
            # Page headers/footers
            (r'\n\s*Page\s+\d+\s*of\s+\d+\s*\n', '\n'),
            (r'\n\s*\d+\s*\n', '\n'),  # Page numbers on separate lines
            
            # Repetitive headers
            (r'(Extendicare\s+.*?\n){2,}', r'\1'),
            (r'(CONFIDENTIAL.*?\n){2,}', r'\1'),
            
            # Multiple consecutive newlines
            (r'\n\s*\n\s*\n+', '\n\n'),
            
            # Trailing whitespace
            (r'[ \t]+$', '', re.MULTILINE),
            
            # Leading/trailing whitespace on lines
            (r'^\s+|\s+$', '', re.MULTILINE),
        ]
        
        # Patterns for section detection
        self.section_patterns = [
            r'^#+\s+(.+)$',  # Markdown headers
            r'^([A-Z][A-Z\s&-]+):?\s*$',  # ALL CAPS sections
            r'^\d+\.\s+(.+)$',  # Numbered sections
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):?\s*$',  # Title Case sections
        ]
    
    def clean_text(self, text: str) -> str:
        """
        Clean document text by removing repetitive headers, footers, and formatting issues
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        cleaned = text
        
        # Apply cleanup patterns
        for pattern, replacement, *flags in self.cleanup_patterns:
            flag = flags[0] if flags else 0
            cleaned = re.sub(pattern, replacement, cleaned, flags=flag)
        
        # Normalize date formats
        cleaned = self._normalize_dates(cleaned)
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _normalize_dates(self, text: str) -> str:
        """Normalize date formats to ISO format where possible"""
        # MM/DD/YYYY to YYYY-MM-DD
        date_pattern = r'(\d{1,2})/(\d{1,2})/(\d{4})'
        
        def normalize_date(match):
            month, day, year = match.groups()
            try:
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except:
                return match.group(0)  # Return original if conversion fails
        
        return re.sub(date_pattern, normalize_date, text)
    
    def chunk_document(self, 
                      parsed_doc: ParsedDocument, 
                      metadata: Optional[ExtractedMetadata] = None) -> List[DocumentChunk]:
        """
        Split document into optimized chunks based on content structure
        
        Args:
            parsed_doc: ParsedDocument to chunk
            metadata: Optional metadata for enhanced chunking
            
        Returns:
            List of DocumentChunk objects
        """
        if self.verbose:
            print(f"Chunking document: {parsed_doc.doc_id}")
        
        # Clean the text first
        cleaned_text = self.clean_text(parsed_doc.markdown_content)
        
        # Split into logical sections first
        sections = self._split_into_sections(cleaned_text)
        
        # Create chunks from sections
        chunks = []
        chunk_index = 0
        
        for section in sections:
            section_chunks = self._chunk_section(
                section, 
                parsed_doc.doc_id, 
                chunk_index
            )
            chunks.extend(section_chunks)
            chunk_index += len(section_chunks)
        
        # Post-process chunks (merge small ones, split large ones)
        chunks = self._post_process_chunks(chunks)
        
        if self.verbose:
            print(f"Created {len(chunks)} chunks for {parsed_doc.doc_id}")
        
        return chunks
    
    def _split_into_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into logical sections based on headers and structure
        
        Args:
            text: Cleaned text to split
            
        Returns:
            List of section dictionaries
        """
        lines = text.split('\n')
        sections = []
        current_section = {
            'title': None,
            'content': [],
            'type': 'content',
            'start_line': 0
        }
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                current_section['content'].append('')
                continue
            
            # Check if line is a section header
            section_title = self._detect_section_header(line)
            
            if section_title and len(current_section['content']) > 0:
                # End current section and start new one
                current_section['end_line'] = i - 1
                sections.append(current_section)
                
                current_section = {
                    'title': section_title,
                    'content': [],
                    'type': 'content',
                    'start_line': i
                }
            
            current_section['content'].append(line)
        
        # Add final section
        if current_section['content']:
            current_section['end_line'] = len(lines) - 1
            sections.append(current_section)
        
        return sections
    
    def _detect_section_header(self, line: str) -> Optional[str]:
        """Detect if a line is a section header"""
        for pattern in self.section_patterns:
            match = re.match(pattern, line.strip())
            if match:
                return match.group(1) if match.groups() else line.strip()
        return None
    
    def _chunk_section(self, 
                      section: Dict[str, Any], 
                      doc_id: str, 
                      start_index: int) -> List[DocumentChunk]:
        """
        Create chunks from a single section
        
        Args:
            section: Section dictionary
            doc_id: Document ID
            start_index: Starting chunk index
            
        Returns:
            List of chunks for this section
        """
        content = '\n'.join(section['content'])
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = len(content) // 4
        
        if estimated_tokens <= self.target_chunk_size:
            # Section fits in one chunk
            return [self._create_chunk(
                doc_id=doc_id,
                chunk_index=start_index,
                text=content,
                section_title=section['title'],
                start_line=section.get('start_line'),
                end_line=section.get('end_line')
            )]
        
        # Split large section into multiple chunks
        chunks = []
        sentences = self._split_into_sentences(content)
        current_chunk_text = ""
        current_chunk_sentences = []
        
        for sentence in sentences:
            # Check if adding this sentence would exceed target size
            potential_text = current_chunk_text + (' ' if current_chunk_text else '') + sentence
            potential_tokens = len(potential_text) // 4
            
            if potential_tokens > self.target_chunk_size and current_chunk_text:
                # Create chunk with current content
                chunk = self._create_chunk(
                    doc_id=doc_id,
                    chunk_index=start_index + len(chunks),
                    text=current_chunk_text.strip(),
                    section_title=section['title']
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk_sentences[-2:] if len(current_chunk_sentences) >= 2 else []
                current_chunk_text = ' '.join(overlap_sentences)
                current_chunk_sentences = overlap_sentences[:]
            
            current_chunk_text += (' ' if current_chunk_text else '') + sentence
            current_chunk_sentences.append(sentence)
        
        # Add final chunk
        if current_chunk_text.strip():
            chunk = self._create_chunk(
                doc_id=doc_id,
                chunk_index=start_index + len(chunks),
                text=current_chunk_text.strip(),
                section_title=section['title']
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for better chunking boundaries"""
        # Simple sentence splitting (can be enhanced with spaCy/NLTK)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _create_chunk(self, 
                     doc_id: str, 
                     chunk_index: int, 
                     text: str,
                     section_title: Optional[str] = None,
                     start_line: Optional[int] = None,
                     end_line: Optional[int] = None) -> DocumentChunk:
        """Create a DocumentChunk object"""
        char_count = len(text)
        token_estimate = char_count // 4  # Rough estimate
        
        # Generate chunk ID
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        chunk_id = f"{doc_id}_chunk_{chunk_index:03d}_{text_hash}"
        
        return DocumentChunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            chunk_index=chunk_index,
            text=text,
            char_count=char_count,
            token_estimate=token_estimate,
            section_title=section_title,
            start_line=start_line,
            end_line=end_line
        )
    
    def _post_process_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Post-process chunks to merge small ones and split large ones"""
        processed_chunks = []
        i = 0
        
        while i < len(chunks):
            current_chunk = chunks[i]
            
            # If chunk is too small, try to merge with next
            if (current_chunk.token_estimate < self.min_chunk_size and 
                i + 1 < len(chunks) and
                chunks[i + 1].token_estimate + current_chunk.token_estimate <= self.max_chunk_size):
                
                next_chunk = chunks[i + 1]
                merged_text = current_chunk.text + '\n\n' + next_chunk.text
                
                merged_chunk = self._create_chunk(
                    doc_id=current_chunk.doc_id,
                    chunk_index=current_chunk.chunk_index,
                    text=merged_text,
                    section_title=current_chunk.section_title
                )
                
                processed_chunks.append(merged_chunk)
                i += 2  # Skip both chunks
            else:
                processed_chunks.append(current_chunk)
                i += 1
        
        return processed_chunks
    
    def save_chunks(self, 
                   chunks: List[DocumentChunk], 
                   output_dir: str = "data/parsed"):
        """
        Save chunks to JSON file
        
        Args:
            chunks: List of DocumentChunk objects to save
            output_dir: Directory to save chunk files
        """
        if not chunks:
            return
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        doc_id = chunks[0].doc_id
        chunks_file = output_path / f"{doc_id}_chunks.json"
        
        # Convert chunks to serializable format
        chunks_data = []
        for chunk in chunks:
            chunks_data.append({
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "char_count": chunk.char_count,
                "token_estimate": chunk.token_estimate,
                "section_title": chunk.section_title,
                "chunk_type": chunk.chunk_type,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line
            })
        
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump({
                "doc_id": doc_id,
                "total_chunks": len(chunks),
                "chunks": chunks_data
            }, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            print(f"Saved {len(chunks)} chunks: {chunks_file}")


async def main():
    """Test the Text Cleaning & Chunking Agent"""
    try:
        # Import here to avoid circular imports in testing
        from ingest import FileIngestionAgent
        from parse import LlamaParseAgent
        
        # Initialize agents
        ingestion_agent = FileIngestionAgent()
        parse_agent = LlamaParseAgent()
        chunk_agent = TextCleaningChunkingAgent()
        
        # Get first document for testing
        documents = ingestion_agent.discover_documents()
        if not documents:
            print("No documents found")
            return
        
        test_doc = documents[0]
        print(f"Testing with document: {test_doc.filename}")
        
        # Parse document
        parsed_doc = await parse_agent.parse_document(test_doc)
        if parsed_doc.error:
            print(f"Parse error: {parsed_doc.error}")
            return
        
        # Create chunks
        chunks = chunk_agent.chunk_document(parsed_doc)
        
        # Save chunks
        chunk_agent.save_chunks(chunks)
        
        # Print results
        print(f"\nChunking Results:")
        print(f"Total chunks: {len(chunks)}")
        print(f"Average chunk size: {sum(c.token_estimate for c in chunks) // len(chunks)} tokens")
        
        # Show first few chunks
        for chunk in chunks[:3]:
            print(f"\nChunk {chunk.chunk_index} ({chunk.token_estimate} tokens):")
            print(f"Section: {chunk.section_title}")
            print(f"Text preview: {chunk.text[:100]}...")
        
    except Exception as e:
        print(f"Error in main: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())