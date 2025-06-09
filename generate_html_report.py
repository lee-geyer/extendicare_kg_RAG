"""
Generate a static HTML report of processed documents
"""

import json
from pathlib import Path
import html
from datetime import datetime

def generate_html_report():
    """Generate static HTML report"""
    
    # Get document stats
    parsed_dir = Path("data/parsed")
    metadata_dir = Path("data/metadata")
    
    md_files = list(parsed_dir.glob("*.md"))
    chunk_files = list(parsed_dir.glob("*_chunks.json"))
    
    # Calculate totals
    total_docs = len(md_files)
    total_chunks = 0
    total_chars = 0
    
    documents = []
    
    for md_file in sorted(md_files, key=lambda x: x.stat().st_mtime, reverse=True)[:50]:
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
                total_chunks += chunk_count
                
                if chunks:
                    token_counts = [c.get('token_estimate', 0) for c in chunks]
                    avg_tokens = sum(token_counts) / len(token_counts)
            except:
                pass
        
        # Get content size
        content_size = md_file.stat().st_size
        total_chars += content_size
        
        # Get metadata
        metadata_file = metadata_dir / f"{doc_id}_metadata.json"
        has_metadata = metadata_file.exists()
        
        # Clean filename
        clean_name = md_file.name.replace('.md', '').replace('_', ' ')
        
        documents.append({
            'doc_id': doc_id,
            'name': clean_name,
            'chunks': chunk_count,
            'avg_tokens': avg_tokens,
            'size_kb': round(content_size / 1024, 1),
            'has_metadata': has_metadata,
            'modified': md_file.stat().st_mtime
        })
    
    # Generate HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Extendicare Document Repository</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
            .stat-box {{ background: #e6f3ff; padding: 15px; border-radius: 5px; text-align: center; flex: 1; }}
            .stat-number {{ font-size: 24px; font-weight: bold; color: #0066cc; }}
            .stat-label {{ font-size: 14px; color: #666; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .doc-link {{ color: #0066cc; text-decoration: none; }}
            .doc-link:hover {{ text-decoration: underline; }}
            .status {{ font-weight: bold; }}
            .success {{ color: green; }}
            .warning {{ color: orange; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📚 Extendicare Document Repository</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{total_docs}</div>
                <div class="stat-label">Documents Processed</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{total_chunks:,}</div>
                <div class="stat-label">Total Chunks</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{round(total_chars/1024/1024, 1)} MB</div>
                <div class="stat-label">Content Processed</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{round(total_chunks/total_docs if total_docs > 0 else 0, 1)}</div>
                <div class="stat-label">Avg Chunks/Doc</div>
            </div>
        </div>
        
        <h2>📋 Recent Documents (Top 50)</h2>
        <table>
            <tr>
                <th>Document Name</th>
                <th>Chunks</th>
                <th>Avg Tokens</th>
                <th>Size (KB)</th>
                <th>Metadata</th>
                <th>View</th>
            </tr>
    """
    
    for doc in documents:
        metadata_status = "✅ Yes" if doc['has_metadata'] else "❌ No"
        html_content += f"""
            <tr>
                <td>{html.escape(doc['name'])}</td>
                <td>{doc['chunks']}</td>
                <td>{doc['avg_tokens']:.0f}</td>
                <td>{doc['size_kb']}</td>
                <td>{metadata_status}</td>
                <td><a href="data/parsed/{doc['doc_id']}.md" class="doc-link">View Content</a></td>
            </tr>
        """
    
    html_content += """
        </table>
        
        <h2>🔧 Processing Details</h2>
        <ul>
            <li><strong>Chunking:</strong> ~300 tokens per chunk with semantic boundaries</li>
            <li><strong>Content:</strong> Parsed with LlamaParse, cleaned and structured</li>
            <li><strong>Metadata:</strong> Extracted using Pydantic schemas</li>
            <li><strong>Files:</strong> Markdown content, JSON chunks, and metadata</li>
        </ul>
        
        <p><em>This is a static report. For interactive features, use the Streamlit dashboard.</em></p>
    </body>
    </html>
    """
    
    # Save HTML report
    report_file = Path("document_report.html")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📄 HTML report generated: {report_file.absolute()}")
    print(f"🌐 Open in browser: file://{report_file.absolute()}")
    
    return report_file

if __name__ == "__main__":
    generate_html_report()