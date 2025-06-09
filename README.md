# Extendicare Knowledge Graph RAG

A hybrid RAG system for Extendicare policy documents that combines vector search with knowledge graphs for comprehensive document retrieval and analysis.

## Quick Start

```bash
# Install dependencies
uv sync

# Set up API key in .env file
cp .env.example .env
# Edit .env and add your LLAMA_CLOUD_API_KEY

# Complete workflow: sync files and process new documents
uv run python sync_and_process.py

# Check processing status
uv run python quick_status.py
```

## Current Status

✅ **Complete Document Processing System**
- **91.4% Complete**: 829/907 documents processed across 5 categories
- File change detection with automatic sync and cleanup
- LlamaParse integration for robust content extraction  
- Metadata extraction with category-specific schemas
- Text cleaning and semantic chunking (~300 tokens)
- Real-time progress monitoring and status tracking

📊 **Document Categories Processed:**
- **Care**: 243 documents (policies, procedures, tools)
- **Infection Prevention and Control**: 219 documents  
- **Emergency Planning and Management**: 149 documents
- **Maintenance**: 145 documents
- **Environmental Services**: 106 documents
- **Privacy and Confidentiality**: 33 documents
- **Administration**: 12 documents

✅ **File Management System**
- Automatic detection of new/removed files from source repository
- Database cleanup for removed files (records + processed files)
- Orphaned file detection and cleanup utilities
- Complete sync and process workflow

🔄 **Next Phase: Vector & Graph Storage**
- Embedding generation for semantic search
- Neo4j knowledge graph construction  
- Qdrant vector database setup
- FastAPI retrieval endpoints

## Architecture

**Hybrid RAG System:**
- **Vector Search**: Qdrant for semantic similarity over document chunks
- **Knowledge Graph**: Neo4j for structured document relationships
- **Processing Pipeline**: 8 specialized agents for document processing

**Data Flow:**
1. File Ingestion → 2. LlamaParse → 3. Metadata Extraction → 4. Text Cleaning/Chunking → 5. Embedding → 6. Knowledge Graph → 7. Hybrid Retrieval → 8. FastAPI Interface

## Commands

### Primary Workflow
```bash
# Complete sync and process workflow
uv run python sync_and_process.py

# Check processing status
uv run python quick_status.py

# Process discovered files with real-time progress
uv run python process_discovered_simple.py
```

### File Change Detection
```bash
# Detect file changes (preview)
uv run python detect_changes.py

# Auto-sync changes (detect + cleanup)
uv run python detect_changes.py --sync

# Clean up orphaned files
uv run python cleanup_orphaned.py
```

### Specialized Processing
```bash
# Test with small batch
uv run python scripts/test_care_docs.py

# Process specific categories
uv run python scripts/process_all_care.py
uv run python scripts/process_expanded_simple.py

# Validate API limits
uv run python scripts/test_rate_limits.py
```

### Monitoring and Reports
```bash
# Start FastAPI dashboard
uv run uvicorn scripts.api:app --reload --host 127.0.0.1 --port 8080

# Generate HTML report
uv run python generate_html_report.py
```

## Project Structure

```
├── data/
│   ├── parsed/           # Processed documents (markdown + chunks)
│   ├── metadata/         # Extracted metadata (JSON)
│   └── raw/extendicare_kb/  # Source documents (symlinked)
├── scripts/              # Processing pipeline agents
├── configs/              # Pydantic schemas for metadata
├── models/               # Saved models and embeddings
└── .env                  # API keys and configuration
```
