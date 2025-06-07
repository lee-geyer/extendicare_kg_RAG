from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
import json
from pathlib import Path
import os
from datetime import datetime
import statistics

app = FastAPI(title="Extendicare Document Processing Dashboard")

def get_processing_stats():
    """Get current processing statistics"""
    parsed_dir = Path("data/parsed")
    metadata_dir = Path("data/metadata")
    
    if not parsed_dir.exists():
        return {"error": "Parsed directory not found"}
    
    md_files = list(parsed_dir.glob("*.md"))
    chunk_files = list(parsed_dir.glob("*_chunks.json"))
    metadata_files = list(metadata_dir.glob("*_metadata.json")) if metadata_dir.exists() else []
    
    # Calculate chunk statistics
    total_chunks = 0
    all_token_counts = []
    
    for chunk_file in chunk_files:
        try:
            with open(chunk_file) as f:
                data = json.load(f)
            chunks = data.get('chunks', [])
            total_chunks += len(chunks)
            
            for chunk in chunks:
                token_count = chunk.get('token_estimate', 0)
                if token_count > 0:
                    all_token_counts.append(token_count)
        except:
            continue
    
    # Check if processing script is running
    import subprocess
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        is_processing = ('process_all_care.py' in result.stdout or 
                        'process_all_categories.py' in result.stdout or
                        'process_expanded_simple.py' in result.stdout)
        
        # Additional check for Python processes running these scripts
        if not is_processing:
            result2 = subprocess.run(['pgrep', '-f', 'python.*process_.*\\.py'], capture_output=True, text=True)
            is_processing = len(result2.stdout.strip()) > 0
            
    except:
        is_processing = False
    
    stats = {
        "documents_processed": len(md_files),
        "chunk_files": len(chunk_files),
        "metadata_files": len(metadata_files),
        "total_chunks": total_chunks,
        "avg_chunks_per_doc": round(total_chunks / len(md_files), 1) if md_files else 0,
        "is_processing": is_processing,
        "last_updated": datetime.now().isoformat()
    }
    
    if all_token_counts:
        stats.update({
            "avg_tokens_per_chunk": round(statistics.mean(all_token_counts), 1),
            "min_tokens": min(all_token_counts),
            "max_tokens": max(all_token_counts),
            "total_tokens": sum(all_token_counts)
        })
    
    return stats

def get_recent_documents(limit=20):
    """Get recently processed documents"""
    parsed_dir = Path("data/parsed")
    if not parsed_dir.exists():
        return []
    
    md_files = sorted(
        parsed_dir.glob("*.md"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )[:limit]
    
    documents = []
    for md_file in md_files:
        doc_id = md_file.stem
        
        # Get chunk info
        chunk_file = parsed_dir / f"{doc_id}_chunks.json"
        chunk_count = 0
        avg_tokens = 0
        
        if chunk_file.exists():
            try:
                with open(chunk_file) as f:
                    chunk_data = json.load(f)
                chunks = chunk_data.get('chunks', [])
                chunk_count = len(chunks)
                
                if chunks:
                    token_counts = [c.get('token_estimate', 0) for c in chunks]
                    avg_tokens = sum(token_counts) / len(token_counts)
            except:
                pass
        
        # Clean filename
        clean_name = md_file.name.replace('.md', '').replace('_', ' ')
        if len(clean_name) > 80:
            clean_name = clean_name[:80] + "..."
        
        documents.append({
            "doc_id": doc_id,
            "filename": clean_name,
            "chunks": chunk_count,
            "avg_tokens": round(avg_tokens, 1),
            "size_kb": round(md_file.stat().st_size / 1024, 1),
            "modified": datetime.fromtimestamp(md_file.stat().st_mtime).isoformat()
        })
    
    return documents

@app.get("/")
def read_root():
    return {"message": "Extendicare Document Processing Dashboard", "status": "running"}

@app.get("/api/stats")
def get_stats():
    """Get processing statistics"""
    return get_processing_stats()

@app.get("/api/documents")
def get_documents(limit: int = 20):
    """Get recent documents"""
    return {"documents": get_recent_documents(limit)}

@app.get("/api/document/{doc_id}")
def get_document(doc_id: str):
    """Get specific document details"""
    parsed_dir = Path("data/parsed")
    metadata_dir = Path("data/metadata")
    
    # Get content
    md_file = parsed_dir / f"{doc_id}.md"
    content = ""
    if md_file.exists():
        try:
            content = md_file.read_text(encoding='utf-8')
        except:
            content = "Error reading content"
    
    # Get chunks
    chunk_file = parsed_dir / f"{doc_id}_chunks.json"
    chunks = {}
    if chunk_file.exists():
        try:
            with open(chunk_file) as f:
                chunks = json.load(f)
        except:
            chunks = {"error": "Error reading chunks"}
    
    # Get metadata
    metadata_file = metadata_dir / f"{doc_id}_metadata.json"
    metadata = {}
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)
        except:
            metadata = {"error": "Error reading metadata"}
    
    return {
        "doc_id": doc_id,
        "content": content[:5000] + "..." if len(content) > 5000 else content,
        "chunks": chunks,
        "metadata": metadata,
        "file_exists": md_file.exists()
    }

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """Interactive HTML dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Extendicare Processing Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                margin: 0; padding: 20px; background: #f8f9fa;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px;
                text-align: center;
            }
            .stats { 
                display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px; margin-bottom: 30px;
            }
            .stat-card { 
                background: white; padding: 25px; border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center;
            }
            .stat-number { 
                font-size: 2.5em; font-weight: bold; 
                background: linear-gradient(45deg, #667eea, #764ba2);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                margin-bottom: 5px;
            }
            .stat-label { color: #666; font-size: 0.9em; }
            .status-indicator {
                display: inline-block; width: 12px; height: 12px;
                border-radius: 50%; margin-right: 8px;
            }
            .processing { background: #28a745; animation: pulse 2s infinite; }
            .idle { background: #dc3545; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
            .documents-section { 
                background: white; border-radius: 10px; padding: 25px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .document-list { max-height: 400px; overflow-y: auto; }
            .document-item { 
                display: flex; justify-content: space-between; align-items: center;
                padding: 12px; border-bottom: 1px solid #eee; cursor: pointer;
                transition: background 0.2s;
            }
            .document-item:hover { background: #f8f9fa; }
            .document-name { font-weight: 500; flex: 1; }
            .document-meta { 
                display: flex; gap: 15px; font-size: 0.85em; color: #666;
            }
            .refresh-btn {
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white; border: none; padding: 10px 20px;
                border-radius: 5px; cursor: pointer; margin-bottom: 20px;
            }
            .last-updated { 
                text-align: center; color: #666; font-size: 0.85em; 
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📚 Extendicare Document Processing Dashboard</h1>
                <p>Real-time monitoring of document processing pipeline</p>
            </div>
            
            <button class="refresh-btn" onclick="loadData()">🔄 Refresh Data</button>
            
            <div class="stats" id="stats-container">
                <!-- Stats will be loaded here -->
            </div>
            
            <div class="documents-section">
                <h2>📋 Recently Processed Documents</h2>
                <div class="document-list" id="documents-container">
                    <!-- Documents will be loaded here -->
                </div>
            </div>
            
            <div class="last-updated" id="last-updated">
                Last updated: Loading...
            </div>
        </div>
        
        <script>
            async function loadStats() {
                try {
                    const response = await fetch('/api/stats');
                    const stats = await response.json();
                    
                    const statusClass = stats.is_processing ? 'processing' : 'idle';
                    const statusText = stats.is_processing ? 'Processing' : 'Idle';
                    
                    document.getElementById('stats-container').innerHTML = `
                        <div class="stat-card">
                            <div class="stat-number">${stats.documents_processed}</div>
                            <div class="stat-label">Documents Processed</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${stats.total_chunks.toLocaleString()}</div>
                            <div class="stat-label">Total Chunks</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${stats.avg_chunks_per_doc}</div>
                            <div class="stat-label">Avg Chunks/Doc</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">
                                <span class="status-indicator ${statusClass}"></span>
                                ${statusText}
                            </div>
                            <div class="stat-label">Processing Status</div>
                        </div>
                        ${stats.avg_tokens_per_chunk ? `
                        <div class="stat-card">
                            <div class="stat-number">${stats.avg_tokens_per_chunk}</div>
                            <div class="stat-label">Avg Tokens/Chunk</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${stats.total_tokens?.toLocaleString() || 0}</div>
                            <div class="stat-label">Total Tokens</div>
                        </div>
                        ` : ''}
                    `;
                    
                    document.getElementById('last-updated').textContent = 
                        `Last updated: ${new Date(stats.last_updated).toLocaleString()}`;
                        
                } catch (error) {
                    console.error('Error loading stats:', error);
                    document.getElementById('stats-container').innerHTML = 
                        '<div class="stat-card"><div class="stat-label">Error loading stats</div></div>';
                }
            }
            
            async function loadDocuments() {
                try {
                    const response = await fetch('/api/documents?limit=30');
                    const data = await response.json();
                    
                    document.getElementById('documents-container').innerHTML = 
                        data.documents.map(doc => `
                            <div class="document-item" onclick="viewDocument('${doc.doc_id}')">
                                <div class="document-name">${doc.filename}</div>
                                <div class="document-meta">
                                    <span>📄 ${doc.chunks} chunks</span>
                                    <span>🔤 ${doc.avg_tokens} avg tokens</span>
                                    <span>📏 ${doc.size_kb} KB</span>
                                </div>
                            </div>
                        `).join('');
                        
                } catch (error) {
                    console.error('Error loading documents:', error);
                    document.getElementById('documents-container').innerHTML = 
                        '<div class="document-item">Error loading documents</div>';
                }
            }
            
            function viewDocument(docId) {
                window.open(`/api/document/${docId}`, '_blank');
            }
            
            function loadData() {
                loadStats();
                loadDocuments();
            }
            
            // Initial load
            loadData();
            
            // Auto-refresh every 30 seconds
            setInterval(loadData, 30000);
        </script>
    </body>
    </html>
    """
    return html_content
