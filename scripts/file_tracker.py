"""
File Processing Status Tracker
Maintains a database of all documents and their processing status
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from ingest import FileIngestionAgent, DocumentInfo


class ProcessingStatus(Enum):
    """Document processing status"""
    DISCOVERED = "discovered"
    QUEUED = "queued" 
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FileRecord:
    """Complete file record with processing information"""
    doc_id: str
    filename: str
    file_path: str
    category: str
    file_extension: str
    file_size: int
    file_hash: str
    status: ProcessingStatus
    discovered_at: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    chunk_count: Optional[int] = None
    content_length: Optional[int] = None
    metadata_extracted: bool = False


class FileTracker:
    """Tracks document processing status in SQLite database"""
    
    def __init__(self, db_path: str = "data/file_tracker.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with file tracking tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    doc_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    category TEXT NOT NULL,
                    file_extension TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    discovered_at TIMESTAMP NOT NULL,
                    processing_started_at TIMESTAMP,
                    processing_completed_at TIMESTAMP,
                    error_message TEXT,
                    chunk_count INTEGER,
                    content_length INTEGER,
                    metadata_extracted BOOLEAN DEFAULT FALSE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON files(status)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_category ON files(category)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_filename ON files(filename)
            """)
    
    def sync_discovered_files(self) -> int:
        """Sync database with currently discovered files"""
        ingestion_agent = FileIngestionAgent()
        discovered_docs = ingestion_agent.discover_documents()
        
        added_count = 0
        with sqlite3.connect(self.db_path) as conn:
            for doc_info in discovered_docs:
                # Check if file already exists
                cursor = conn.execute(
                    "SELECT doc_id FROM files WHERE doc_id = ?", 
                    (doc_info.doc_id,)
                )
                
                if not cursor.fetchone():
                    # Add new file
                    conn.execute("""
                        INSERT INTO files (
                            doc_id, filename, file_path, category, file_extension,
                            file_size, file_hash, status, discovered_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        doc_info.doc_id,
                        doc_info.filename,
                        str(doc_info.file_path),
                        doc_info.category,
                        doc_info.file_extension,
                        doc_info.file_size,
                        doc_info.file_hash,
                        ProcessingStatus.DISCOVERED.value,
                        datetime.now()
                    ))
                    added_count += 1
        
        return added_count
    
    def update_file_status(self, doc_id: str, status: ProcessingStatus, 
                          error_message: Optional[str] = None):
        """Update file processing status"""
        with sqlite3.connect(self.db_path) as conn:
            timestamp_field = None
            timestamp_value = datetime.now()
            
            if status == ProcessingStatus.PROCESSING:
                timestamp_field = "processing_started_at"
            elif status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
                timestamp_field = "processing_completed_at"
            
            if timestamp_field:
                conn.execute(f"""
                    UPDATE files 
                    SET status = ?, {timestamp_field} = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE doc_id = ?
                """, (status.value, timestamp_value, error_message, doc_id))
            else:
                conn.execute("""
                    UPDATE files 
                    SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE doc_id = ?
                """, (status.value, error_message, doc_id))
    
    def update_processing_results(self, doc_id: str, chunk_count: int, 
                                content_length: int, metadata_extracted: bool = True):
        """Update file with processing results"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE files 
                SET chunk_count = ?, content_length = ?, metadata_extracted = ?, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE doc_id = ?
            """, (chunk_count, content_length, metadata_extracted, doc_id))
    
    def get_all_files(self, status_filter: Optional[ProcessingStatus] = None,
                     category_filter: Optional[str] = None) -> List[FileRecord]:
        """Get all files with optional filtering"""
        query = "SELECT * FROM files WHERE 1=1"
        params = []
        
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter.value)
        
        if category_filter:
            query += " AND category = ?"
            params.append(category_filter)
        
        query += " ORDER BY discovered_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            files = []
            for row in cursor.fetchall():
                files.append(FileRecord(
                    doc_id=row['doc_id'],
                    filename=row['filename'],
                    file_path=row['file_path'],
                    category=row['category'],
                    file_extension=row['file_extension'],
                    file_size=row['file_size'],
                    file_hash=row['file_hash'],
                    status=ProcessingStatus(row['status']),
                    discovered_at=datetime.fromisoformat(row['discovered_at']),
                    processing_started_at=datetime.fromisoformat(row['processing_started_at']) if row['processing_started_at'] else None,
                    processing_completed_at=datetime.fromisoformat(row['processing_completed_at']) if row['processing_completed_at'] else None,
                    error_message=row['error_message'],
                    chunk_count=row['chunk_count'],
                    content_length=row['content_length'],
                    metadata_extracted=bool(row['metadata_extracted'])
                ))
            
            return files
    
    def get_file_by_id(self, doc_id: str) -> Optional[FileRecord]:
        """Get a specific file by doc_id"""
        files = self.get_all_files()
        for file_record in files:
            if file_record.doc_id == doc_id:
                return file_record
        return None
    
    def get_status_summary(self) -> Dict[str, int]:
        """Get summary of files by status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM files 
                GROUP BY status
            """)
            
            summary = {}
            for row in cursor.fetchall():
                summary[row[0]] = row[1]
            
            return summary
    
    def get_category_summary(self) -> Dict[str, int]:
        """Get summary of files by category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT category, COUNT(*) as count 
                FROM files 
                GROUP BY category
                ORDER BY count DESC
            """)
            
            summary = {}
            for row in cursor.fetchall():
                summary[row[0]] = row[1]
            
            return summary
    
    def sync_processing_status(self):
        """Sync database with actual processed files on disk"""
        parsed_dir = Path("data/parsed")
        metadata_dir = Path("data/metadata")
        
        if not parsed_dir.exists():
            return
        
        # Get all processed files
        processed_files = set()
        for md_file in parsed_dir.glob("*.md"):
            doc_id = md_file.stem
            processed_files.add(doc_id)
        
        with sqlite3.connect(self.db_path) as conn:
            # Update status for processed files
            for doc_id in processed_files:
                # Check if we have chunks and metadata
                chunks_file = parsed_dir / f"{doc_id}_chunks.json"
                metadata_file = metadata_dir / f"{doc_id}_metadata.json"
                
                chunk_count = 0
                content_length = 0
                metadata_extracted = False
                
                if chunks_file.exists():
                    try:
                        with open(chunks_file) as f:
                            chunk_data = json.load(f)
                            chunk_count = chunk_data.get('total_chunks', 0)
                    except:
                        pass
                
                if metadata_file.exists():
                    metadata_extracted = True
                
                # Get content length from markdown file
                md_file = parsed_dir / f"{doc_id}.md"
                if md_file.exists():
                    content_length = len(md_file.read_text(encoding='utf-8'))
                
                # Update database
                conn.execute("""
                    UPDATE files 
                    SET status = ?, chunk_count = ?, content_length = ?, 
                        metadata_extracted = ?, processing_completed_at = COALESCE(processing_completed_at, ?),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE doc_id = ? AND status != ?
                """, (
                    ProcessingStatus.COMPLETED.value,
                    chunk_count,
                    content_length,
                    metadata_extracted,
                    datetime.now(),
                    doc_id,
                    ProcessingStatus.COMPLETED.value
                ))
    
    def remove_orphaned_files(self, remove_processed_files: bool = False) -> Dict[str, int]:
        """
        Remove files from database that no longer exist in filesystem
        
        Args:
            remove_processed_files: If True, also delete processed files from disk
            
        Returns:
            Dict with counts of removed items
        """
        ingestion_agent = FileIngestionAgent()
        current_files = ingestion_agent.discover_documents()
        current_doc_ids = {doc.doc_id for doc in current_files}
        
        # Get orphaned files before removing them
        orphaned_files = self.get_orphaned_files()
        
        db_removed_count = 0
        processed_files_removed = 0
        metadata_files_removed = 0
        
        with sqlite3.connect(self.db_path) as conn:
            # Remove orphaned files from database
            for file_record in orphaned_files:
                conn.execute("DELETE FROM files WHERE doc_id = ?", (file_record.doc_id,))
                db_removed_count += 1
                
                # Also remove processed files if requested
                if remove_processed_files:
                    parsed_dir = Path("data/parsed")
                    metadata_dir = Path("data/metadata")
                    
                    # Remove markdown file
                    md_file = parsed_dir / f"{file_record.doc_id}.md"
                    if md_file.exists():
                        md_file.unlink()
                        processed_files_removed += 1
                    
                    # Remove chunks file
                    chunks_file = parsed_dir / f"{file_record.doc_id}_chunks.json"
                    if chunks_file.exists():
                        chunks_file.unlink()
                    
                    # Remove metadata file
                    metadata_file = metadata_dir / f"{file_record.doc_id}_metadata.json"
                    if metadata_file.exists():
                        metadata_file.unlink()
                        metadata_files_removed += 1
        
        return {
            'database_records': db_removed_count,
            'processed_files': processed_files_removed,
            'metadata_files': metadata_files_removed
        }
    
    def get_orphaned_files(self) -> List[FileRecord]:
        """Get list of files in database that no longer exist in filesystem"""
        ingestion_agent = FileIngestionAgent()
        current_files = ingestion_agent.discover_documents()
        current_doc_ids = {doc.doc_id for doc in current_files}
        
        all_files = self.get_all_files()
        orphaned_files = [file for file in all_files if file.doc_id not in current_doc_ids]
        
        return orphaned_files


def main():
    """Initialize and sync file tracker"""
    tracker = FileTracker()
    
    print("🔄 Syncing discovered files...")
    added = tracker.sync_discovered_files()
    print(f"✅ Added {added} new files to database")
    
    print("🔄 Syncing processing status...")
    tracker.sync_processing_status()
    print("✅ Processing status synced")
    
    # Print summary
    status_summary = tracker.get_status_summary()
    category_summary = tracker.get_category_summary()
    
    print("\n📊 Status Summary:")
    for status, count in status_summary.items():
        print(f"   {status}: {count}")
    
    print("\n📂 Category Summary:")
    for category, count in category_summary.items():
        print(f"   {category}: {count}")


if __name__ == "__main__":
    main()