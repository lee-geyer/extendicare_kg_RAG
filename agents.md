# agents.md

## Project: Extendicare Policy Knowledge Graph RAG System

### Overview
This document guides the development of a Codex agent responsible for parsing, indexing, and enriching Extendicare's policy-related documents for integration into a hybrid RAG system backed by Qdrant (semantic search) and Neo4j (knowledge graph). The system processes unstructured documents and extracts structured content and metadata for LLM use.

### Goals
- Ingest a variety of document types from a local folder.
- Extract layout-aware text, tables, and metadata.
- Clean and normalize document content.
- Chunk and embed text for semantic search in Qdrant.
- Extract relationships and structured data for a Neo4j knowledge graph.
- Provide a lightweight FastAPI interface for UI/API interaction.

---

## Agent Responsibilities

### 1. File Ingestion Agent
**Trigger:** New or modified file in a designated folder.  
**Responsibilities:**
- Read PDFs, DOCX, PPTX, XLSX.
- Determine category from folder path (e.g., Policies, Procedures).
- Assign unique document ID (filename-based or UUID).
- Pass file to the LlamaParse Agent.

---

### 2. LlamaParse Agent
**Tool:** `llama_cloud_services.LlamaParse`  
**Responsibilities:**
- Parse file to extract full structured content.
- Output text in Markdown format, preserving:
  - Headers
  - Sections
  - Tables (as markdown)
- Return per-page metadata if needed.

**Optional Parameters:**
- `language='en'`
- `preset='default'` or `preset='premium'` for best OCR accuracy
- `num_workers=4` for concurrent file processing

---

### 3. Metadata Extraction Agent
**Tool:** `llama_cloud_services.LlamaExtract`  
**Schema (Pydantic):**
```python
class PolicyMeta(BaseModel):
    policy_index: str
    title: str
    effective_date: str
    review_date: str
```

**Responsibilities:**
- Extract structured fields from top-of-document tables.
- Allow configuration of schema per folder (e.g., Tools may use a different schema).
- Fallback to regex-based post-processing if LlamaExtract fails.

---

### 4. Text Cleaning & Chunking Agent
**Responsibilities:**
- Remove repetitive headers, footers, or logos from parsed text.
- Normalize dates to ISO format.
- Chunk by headings or into ~300 token segments.
- Assign each chunk a unique ID: `doc_id + chunk_index`

---

### 5. Embedding Agent
**Model:** OpenAI `text-embedding-ada-002` or local `sentence-transformers` model  
**Responsibilities:**
- Embed each chunk of cleaned text.
- Store:
  - `chunk_id`
  - `embedding`
  - `doc_id`, `title`, `category`, `text`, etc.
- Upsert to Qdrant collection `extendicare_docs`

---

### 6. Knowledge Graph Construction Agent
**Tool:** `neo4j` Python driver or `py2neo`  
**Responsibilities:**
- Create nodes:
  - `(:Document {id, title, category, effective_date, review_date})`
- Create relationships:
  - `(:Document)-[:REFERS_TO]->(:Document)` when one document mentions another's ID
  - `(:Education)-[:COVERS]->(:Policy)` from file metadata or manual mapping
- Maintain versioned documents (if effective_date > prior revision)

---

### 7. Graph-Vector Hybrid Retrieval Agent
**Responsibilities:**
- Embed query
- Perform vector search in Qdrant
- Get related doc IDs
- Traverse Neo4j for linked documents
- Merge and rank results for RAG context

---

### 8. FastAPI Interface Agent
**Endpoints:**
- `POST /upload`: Upload file(s)
- `GET /document/{id}`: Return document metadata and text
- `POST /query`: Accept query string, return LLM-generated response
- `GET /graph/{id}`: Return Neo4j subgraph for a given document

**Optional:** Streamlit UI, or Swagger UI from FastAPI docs

---

## Folder Structure
```
extendicare_kg_rag/
├── data/
│   ├── raw/
│   ├── parsed/
│   └── metadata/
├── scripts/
│   ├── ingest.py
│   ├── parse.py
│   ├── extract_metadata.py
│   ├── clean_chunk.py
│   ├── embed.py
│   ├── build_kg.py
│   └── api.py
├── models/
├── configs/
│   └── schema_policy.py
├── agents.md
└── requirements.txt
```

---

## Future Considerations
- Versioning support in Neo4j (e.g., retain historical documents).
- Scheduled background processing (watch folder).
- Support for French-language content.
- LLM summarization or QA fine-tuning.
- Integration with Teams or Athena/Hermes UI layer.

---

## Notes
- All API usage with LlamaParse/LlamaExtract requires authentication with `llx-` API key.
- Large files and scanned PDFs may incur higher processing time and cost.
- Ensure Qdrant and Neo4j indices are kept in sync using document IDs.
- Agent logging and retry logic should be robust for production.

---

## Contact
This document is maintained by the Extendicare AI/NLP pipeline design team.  
For questions or access to infrastructure, please contact the project lead or system architect.