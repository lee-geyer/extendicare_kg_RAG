"""
File Ingestion Agent
Responsible for discovering, categorizing, and preparing documents for processing.
"""

import os
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import hashlib


@dataclass
class DocumentInfo:
    """Container for document metadata and file information"""
    file_path: Path
    doc_id: str
    category: str
    filename: str
    file_extension: str
    file_size: int
    file_hash: str


class FileIngestionAgent:
    """
    Agent responsible for discovering and categorizing documents from the raw data folder.
    Supports PDF, DOCX, PPTX, XLSX file types.
    """
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.pptx', '.xlsx'}
    
    def __init__(self, raw_data_path: str = "data/raw/extendicare_kb"):
        self.raw_data_path = Path(raw_data_path)
        if not self.raw_data_path.exists():
            raise FileNotFoundError(f"Raw data path does not exist: {self.raw_data_path}")
    
    def discover_documents(self) -> List[DocumentInfo]:
        """
        Recursively discover all supported document types in the raw data folder.
        
        Returns:
            List of DocumentInfo objects for each discovered document
        """
        documents = []
        
        for file_path in self.raw_data_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                doc_info = self._create_document_info(file_path)
                documents.append(doc_info)
        
        return documents
    
    def _create_document_info(self, file_path: Path) -> DocumentInfo:
        """
        Create DocumentInfo object for a given file path.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            DocumentInfo object with metadata
        """
        # Generate document ID based on file path and content hash
        file_hash = self._calculate_file_hash(file_path)
        doc_id = self._generate_document_id(file_path, file_hash)
        
        # Determine category from folder structure
        category = self._determine_category(file_path)
        
        return DocumentInfo(
            file_path=file_path,
            doc_id=doc_id,
            category=category,
            filename=file_path.name,
            file_extension=file_path.suffix.lower(),
            file_size=file_path.stat().st_size,
            file_hash=file_hash
        )
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content for duplicate detection"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()[:12]  # Use first 12 chars for brevity
    
    def _generate_document_id(self, file_path: Path, file_hash: str) -> str:
        """
        Generate unique document ID based on filename and content hash.
        Format: filename_without_ext_hash
        """
        base_name = file_path.stem
        # Clean filename for ID (remove spaces, special chars)
        clean_name = "".join(c for c in base_name if c.isalnum() or c in "_-").lower()
        return f"{clean_name}_{file_hash}"
    
    def _determine_category(self, file_path: Path) -> str:
        """
        Determine document category based on folder structure.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Category string (e.g., "Policies", "Procedures", "Tools")
        """
        # Get relative path from raw data root
        relative_path = file_path.relative_to(self.raw_data_path)
        path_parts = relative_path.parts
        
        if len(path_parts) > 1:
            # Use first directory as category
            return path_parts[0]
        else:
            # File is in root directory
            return "General"
    
    def filter_by_category(self, documents: List[DocumentInfo], category: str) -> List[DocumentInfo]:
        """Filter documents by category"""
        return [doc for doc in documents if doc.category.lower() == category.lower()]
    
    def filter_by_extension(self, documents: List[DocumentInfo], extension: str) -> List[DocumentInfo]:
        """Filter documents by file extension"""
        return [doc for doc in documents if doc.file_extension == extension.lower()]
    
    def filter_by_filename_prefix(self, documents: List[DocumentInfo], prefix: str) -> List[DocumentInfo]:
        """Filter documents by filename prefix (case-insensitive)"""
        return [doc for doc in documents if doc.filename.upper().startswith(prefix.upper())]
    
    def get_processing_queue(self) -> List[DocumentInfo]:
        """
        Get list of documents ready for processing.
        This method can be extended to check processing status, skip already processed files, etc.
        """
        return self.discover_documents()


def main():
    """Test the File Ingestion Agent"""
    try:
        agent = FileIngestionAgent()
        documents = agent.discover_documents()
        
        print(f"Discovered {len(documents)} documents:")
        for doc in documents[:5]:  # Show first 5
            print(f"  {doc.doc_id} - {doc.category}/{doc.filename} ({doc.file_extension})")
        
        if len(documents) > 5:
            print(f"  ... and {len(documents) - 5} more")
            
        # Show category breakdown
        categories = {}
        for doc in documents:
            categories[doc.category] = categories.get(doc.category, 0) + 1
        
        print(f"\nCategory breakdown:")
        for category, count in categories.items():
            print(f"  {category}: {count} documents")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()