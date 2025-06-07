# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup
- Use `uv` for environment management and running scripts
- Run FastAPI app: `uv run uvicorn scripts.api:app --reload`
- Install dependencies: `uv sync` or `uv pip install -r requirements.txt`

## Document Processing Commands
- Test small batch: `uv run python scripts/test_care_docs.py`
- Process all CARE docs: `uv run python scripts/process_all_care.py`
- Process expanded categories: `uv run python scripts/process_expanded_simple.py`
- Test rate limits: `uv run python scripts/test_rate_limits.py`
- Generate HTML report: `uv run python generate_html_report.py`
- Monitor processing: `uv run uvicorn scripts.api:app --reload --host 127.0.0.1 --port 8080`

## Architecture Overview
This is a hybrid RAG system for Extendicare policy documents that combines:
- **Vector Search**: Qdrant for semantic similarity search over document chunks
- **Knowledge Graph**: Neo4j for structured relationships between documents
- **Document Processing Pipeline**: LlamaParse for extraction, chunking, and embedding

### Key Components
- **data/raw/extendicare_kb**: Symlinked to OneDrive folder containing source documents
- **scripts/**: Processing pipeline scripts (ingest, parse, embed, build_kg, api)
- **configs/**: Pydantic schemas for metadata extraction
- **models/**: Saved models and embeddings

### Agent Architecture
The system uses 8 specialized agents for document processing:
1. File Ingestion → 2. LlamaParse → 3. Metadata Extraction → 4. Text Cleaning/Chunking → 5. Embedding → 6. Knowledge Graph Construction → 7. Hybrid Retrieval → 8. FastAPI Interface

## Document Processing Flow
1. Documents from `data/raw/extendicare_kb/` are parsed using LlamaParse
2. Metadata extracted using LlamaExtract with PolicyMeta schema
3. Text cleaned, chunked (~300 tokens), and embedded
4. Chunks stored in Qdrant collection `extendicare_docs`
5. Document relationships mapped in Neo4j graph
6. Hybrid retrieval combines vector search + graph traversal

## API Authentication
- LlamaParse/LlamaExtract requires `llx-` API key in `.env` file
- OpenAI embeddings or local sentence-transformers for vector generation

## Processing Status
**Current Progress:**
- ✅ Document parsing pipeline fully implemented and robust
- ✅ Expanded to 5 document categories (up from 1)
- ✅ 391+ documents processed successfully from expanded categories
- ✅ Real-time FastAPI dashboard with processing status monitoring  
- ✅ End-to-end pipeline: Parse → Metadata → Chunk → Save
- 🔄 Processing remaining documents from expanded categories (54% complete)

**Document Categories:**
1. **Care** (237 documents) - ✅ Complete
2. **Emergency Planning and Management** (148 documents) - 🔄 Processing
3. **Environmental Services** (106 documents) - 🔄 Processing  
4. **Infection Prevention and Control** (211 documents) - 🔄 Processing
5. **Privacy and Confidentiality** (6 documents) - 🔄 Processing

**Data Locations:**
- Parsed content: `data/parsed/` (markdown + chunks)
- Metadata: `data/metadata/` (structured extraction)
- Processing logs: `data/*_summary.json`
- HTML report: `document_report.html`
- Dashboard: `http://127.0.0.1:8080/dashboard`

**Current Status:**
The system is actively processing documents from all expanded categories with:
- LlamaParse integration working reliably
- Metadata extraction using category-specific schemas
- Text chunking with ~300 token target size
- Real-time progress monitoring via web dashboard
- Robust error handling and rate limiting

**Next Steps:**
- Complete processing of remaining 476 documents (in progress)
- Implement embedding generation for vector search
- Set up Neo4j knowledge graph construction
- Build FastAPI endpoints for hybrid retrieval