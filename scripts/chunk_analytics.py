"""
Chunk Analytics
Analyze chunking patterns and distribution across processed documents
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import statistics
import pandas as pd

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Removed unused import


def analyze_chunk_distribution() -> Dict[str, Any]:
    """Analyze chunk size distribution across all processed documents"""
    
    parsed_dir = Path("data/parsed")
    chunk_files = list(parsed_dir.glob("*_chunks.json"))
    
    if not chunk_files:
        return {"error": "No chunk files found"}
    
    # Collect all chunk data
    all_chunks = []
    doc_chunk_counts = []
    doc_total_tokens = []
    section_types = []
    
    for chunk_file in chunk_files:
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunk_data = json.load(f)
            
            if 'chunks' not in chunk_data:
                continue
                
            chunks = chunk_data['chunks']
            doc_chunk_counts.append(len(chunks))
            
            doc_tokens = 0
            for chunk in chunks:
                token_count = chunk.get('token_estimate', 0)
                char_count = chunk.get('char_count', 0)
                section_title = chunk.get('section_title')
                
                all_chunks.append({
                    'doc_id': chunk.get('doc_id', ''),
                    'chunk_index': chunk.get('chunk_index', 0),
                    'token_estimate': token_count,
                    'char_count': char_count,
                    'section_title': section_title,
                    'has_section': bool(section_title),
                    'chunk_type': chunk.get('chunk_type', 'content')
                })
                
                doc_tokens += token_count
                
                if section_title:
                    section_types.append(section_title)
            
            doc_total_tokens.append(doc_tokens)
            
        except Exception as e:
            print(f"Error processing {chunk_file}: {e}")
            continue
    
    if not all_chunks:
        return {"error": "No valid chunks found"}
    
    # Calculate statistics
    token_counts = [chunk['token_estimate'] for chunk in all_chunks]
    char_counts = [chunk['char_count'] for chunk in all_chunks]
    
    # Token statistics
    token_stats = {
        'count': len(token_counts),
        'mean': statistics.mean(token_counts),
        'median': statistics.median(token_counts),
        'std_dev': statistics.stdev(token_counts) if len(token_counts) > 1 else 0,
        'min': min(token_counts),
        'max': max(token_counts),
        'q25': statistics.quantiles(token_counts, n=4)[0] if len(token_counts) >= 4 else min(token_counts),
        'q75': statistics.quantiles(token_counts, n=4)[2] if len(token_counts) >= 4 else max(token_counts)
    }
    
    # Character statistics
    char_stats = {
        'mean': statistics.mean(char_counts),
        'median': statistics.median(char_counts),
        'min': min(char_counts),
        'max': max(char_counts)
    }
    
    # Document-level statistics
    doc_stats = {
        'total_documents': len(doc_chunk_counts),
        'total_chunks': sum(doc_chunk_counts),
        'avg_chunks_per_doc': statistics.mean(doc_chunk_counts),
        'median_chunks_per_doc': statistics.median(doc_chunk_counts),
        'min_chunks_per_doc': min(doc_chunk_counts),
        'max_chunks_per_doc': max(doc_chunk_counts),
        'avg_tokens_per_doc': statistics.mean(doc_total_tokens),
        'median_tokens_per_doc': statistics.median(doc_total_tokens)
    }
    
    # Token size distribution
    token_distribution = {
        'under_100': len([t for t in token_counts if t < 100]),
        '100_199': len([t for t in token_counts if 100 <= t < 200]),
        '200_299': len([t for t in token_counts if 200 <= t < 300]),
        '300_399': len([t for t in token_counts if 300 <= t < 400]),
        '400_499': len([t for t in token_counts if 400 <= t < 500]),
        '500_plus': len([t for t in token_counts if t >= 500])
    }
    
    # Section analysis
    chunks_with_sections = len([c for c in all_chunks if c['has_section']])
    section_coverage = chunks_with_sections / len(all_chunks) * 100
    
    # Most common section types
    from collections import Counter
    section_counter = Counter(section_types)
    common_sections = section_counter.most_common(10)
    
    # Chunk type distribution
    chunk_type_counter = Counter([c['chunk_type'] for c in all_chunks])
    
    return {
        'methodology': {
            'target_size': 300,
            'overlap': 50,
            'max_size': 500,
            'min_size': 100,
            'chunking_method': 'Semantic boundaries with section awareness',
            'preprocessing': [
                'Remove page headers/footers',
                'Normalize dates to ISO format', 
                'Clean repetitive content',
                'Split by sentence boundaries'
            ]
        },
        'token_stats': token_stats,
        'char_stats': char_stats,
        'doc_stats': doc_stats,
        'token_distribution': token_distribution,
        'section_analysis': {
            'chunks_with_sections': chunks_with_sections,
            'section_coverage_percent': section_coverage,
            'common_sections': common_sections
        },
        'chunk_types': dict(chunk_type_counter),
        'raw_data': {
            'token_counts': token_counts[:1000],  # Limit for display
            'doc_chunk_counts': doc_chunk_counts,
            'doc_tokens': doc_total_tokens
        }
    }


def get_chunking_methodology_summary() -> str:
    """Get a summary of the chunking methodology"""
    return """
## 📚 Chunking Methodology

**Target Configuration:**
- **Target size:** 300 tokens per chunk
- **Overlap:** 50 tokens between adjacent chunks  
- **Size limits:** 100-500 tokens (merge small, split large)
- **Boundary detection:** Sentence-aware splitting

**Preprocessing Steps:**
1. **Clean repetitive content** (headers, footers, page numbers)
2. **Normalize dates** to ISO format (YYYY-MM-DD)
3. **Split by sections** using markdown headers and structure
4. **Sentence boundaries** for natural chunk breaks
5. **Merge small chunks** (<100 tokens) with neighbors
6. **Post-process large chunks** (>500 tokens) by re-splitting

**Section Awareness:**
- Preserves document structure and hierarchy
- Maintains section titles for context
- Respects logical document boundaries
- Overlaps content to maintain continuity

**Quality Control:**
- Token estimation using ~4 characters per token
- Content hash for chunk uniqueness
- Section title preservation for semantic context
"""


def main():
    """Analyze and display chunk statistics"""
    print("📊 Analyzing chunk distribution...")
    
    analytics = analyze_chunk_distribution()
    
    if 'error' in analytics:
        print(f"❌ {analytics['error']}")
        return
    
    # Print summary
    token_stats = analytics['token_stats']
    doc_stats = analytics['doc_stats']
    
    print(f"\n📈 Chunk Statistics:")
    print(f"   Total chunks: {token_stats['count']:,}")
    print(f"   Total documents: {doc_stats['total_documents']:,}")
    print(f"   Avg chunks per doc: {doc_stats['avg_chunks_per_doc']:.1f}")
    
    print(f"\n🎯 Token Distribution:")
    print(f"   Mean: {token_stats['mean']:.0f} tokens")
    print(f"   Median: {token_stats['median']:.0f} tokens") 
    print(f"   Range: {token_stats['min']}-{token_stats['max']} tokens")
    print(f"   Std Dev: {token_stats['std_dev']:.0f}")
    
    print(f"\n📊 Size Buckets:")
    dist = analytics['token_distribution']
    for bucket, count in dist.items():
        percentage = count / token_stats['count'] * 100
        print(f"   {bucket.replace('_', '-')}: {count:,} chunks ({percentage:.1f}%)")
    
    print(f"\n📝 Section Analysis:")
    section = analytics['section_analysis']
    print(f"   Chunks with sections: {section['chunks_with_sections']:,} ({section['section_coverage_percent']:.1f}%)")
    print(f"   Common sections:")
    for section_name, count in section['common_sections'][:5]:
        print(f"     • {section_name}: {count} chunks")


if __name__ == "__main__":
    main()