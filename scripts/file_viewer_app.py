"""
Streamlit File Repository Viewer
Browse and view processed documents with their metadata and content
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sys
import plotly.express as px
import plotly.graph_objects as go

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))

from file_tracker import FileTracker, ProcessingStatus
from chunk_analytics import analyze_chunk_distribution, get_chunking_methodology_summary


def load_file_content(doc_id: str) -> tuple[str, dict, dict]:
    """Load markdown content, metadata, and chunks for a document"""
    parsed_dir = Path("data/parsed")
    metadata_dir = Path("data/metadata")
    
    # Load markdown content
    md_file = parsed_dir / f"{doc_id}.md"
    content = ""
    if md_file.exists():
        content = md_file.read_text(encoding='utf-8')
    
    # Load metadata
    metadata_file = metadata_dir / f"{doc_id}_metadata.json"
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    
    # Load chunks
    chunks_file = parsed_dir / f"{doc_id}_chunks.json"
    chunks = {}
    if chunks_file.exists():
        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
    
    return content, metadata, chunks


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def status_emoji(status: ProcessingStatus) -> str:
    """Get emoji for processing status"""
    emoji_map = {
        ProcessingStatus.DISCOVERED: "📄",
        ProcessingStatus.QUEUED: "⏳",
        ProcessingStatus.PROCESSING: "🔄",
        ProcessingStatus.COMPLETED: "✅",
        ProcessingStatus.FAILED: "❌"
    }
    return emoji_map.get(status, "❓")


def main():
    st.set_page_config(
        page_title="Extendicare Document Repository",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 Extendicare Document Repository")
    
    # Add tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Document Browser", "📊 Chunk Analytics", "🔧 Methodology"])
    
    with tab3:
        st.markdown(get_chunking_methodology_summary())
        return
    
    with tab2:
        show_chunk_analytics()
        return
    
    with tab1:
        show_document_browser()


def show_chunk_analytics():
    """Display chunk analytics dashboard"""
    st.header("📊 Chunk Analytics Dashboard")
    st.markdown("Analysis of document chunking patterns and distribution")
    
    # Get analytics data
    with st.spinner("Analyzing chunk data..."):
        try:
            analytics = analyze_chunk_distribution()
        except Exception as e:
            st.error(f"Error loading chunk analytics: {e}")
            st.write("Debug info:")
            st.write(f"Current working directory: {Path.cwd()}")
            st.write(f"Data directory exists: {Path('data/parsed').exists()}")
            if Path('data/parsed').exists():
                chunk_files = list(Path('data/parsed').glob('*_chunks.json'))
                st.write(f"Chunk files found: {len(chunk_files)}")
            return
    
    if 'error' in analytics:
        st.error(f"Error: {analytics['error']}")
        return
    
    # Summary metrics
    token_stats = analytics['token_stats']
    doc_stats = analytics['doc_stats']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Chunks", f"{token_stats['count']:,}")
    with col2:
        st.metric("Documents Processed", f"{doc_stats['total_documents']:,}")
    with col3:
        st.metric("Avg Chunks/Doc", f"{doc_stats['avg_chunks_per_doc']:.1f}")
    with col4:
        st.metric("Avg Tokens/Chunk", f"{token_stats['mean']:.0f}")
    
    # Token distribution chart
    st.subheader("🎯 Token Size Distribution")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create histogram
        token_counts = analytics['raw_data']['token_counts']
        fig_hist = px.histogram(
            x=token_counts,
            nbins=50,
            title="Token Count Distribution",
            labels={'x': 'Tokens per Chunk', 'y': 'Number of Chunks'}
        )
        fig_hist.add_vline(x=300, line_dash="dash", line_color="red", 
                          annotation_text="Target (300)")
        fig_hist.add_vline(x=token_stats['mean'], line_dash="dot", line_color="green",
                          annotation_text=f"Mean ({token_stats['mean']:.0f})")
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # Token distribution buckets
        dist = analytics['token_distribution']
        bucket_data = []
        for bucket, count in dist.items():
            percentage = count / token_stats['count'] * 100
            bucket_data.append({
                'Range': bucket.replace('_', '-'),
                'Count': count,
                'Percentage': f"{percentage:.1f}%"
            })
        
        st.write("**Size Buckets:**")
        df_buckets = pd.DataFrame(bucket_data)
        st.dataframe(df_buckets, hide_index=True)
    
    # Document-level analysis
    st.subheader("📄 Document-Level Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Chunks per document
        doc_chunk_counts = analytics['raw_data']['doc_chunk_counts']
        fig_doc = px.histogram(
            x=doc_chunk_counts,
            nbins=20,
            title="Chunks per Document",
            labels={'x': 'Number of Chunks', 'y': 'Number of Documents'}
        )
        st.plotly_chart(fig_doc, use_container_width=True)
    
    with col2:
        # Document token totals
        doc_tokens = analytics['raw_data']['doc_tokens']
        fig_tokens = px.histogram(
            x=doc_tokens,
            nbins=20,
            title="Total Tokens per Document",
            labels={'x': 'Total Tokens', 'y': 'Number of Documents'}
        )
        st.plotly_chart(fig_tokens, use_container_width=True)
    
    # Section analysis
    st.subheader("📝 Section Analysis")
    
    section_info = analytics['section_analysis']
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric("Chunks with Sections", 
                 f"{section_info['chunks_with_sections']:,}")
        st.metric("Section Coverage", 
                 f"{section_info['section_coverage_percent']:.1f}%")
    
    with col2:
        if section_info['common_sections']:
            st.write("**Most Common Section Types:**")
            section_df = pd.DataFrame(
                section_info['common_sections'][:10],
                columns=['Section Title', 'Count']
            )
            st.dataframe(section_df, hide_index=True)
    
    # Quality metrics
    st.subheader("📈 Quality Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Target Compliance", 
                 f"{analytics['token_distribution']['200_299'] + analytics['token_distribution']['300_399']:.0f}")
        st.caption("Chunks within 200-399 tokens (near target)")
    
    with col2:
        std_dev_percent = (token_stats['std_dev'] / token_stats['mean']) * 100
        st.metric("Size Consistency", f"{100 - std_dev_percent:.1f}%")
        st.caption("Lower std dev = more consistent sizes")
    
    with col3:
        outliers = analytics['token_distribution']['under_100'] + analytics['token_distribution']['500_plus']
        outlier_percent = (outliers / token_stats['count']) * 100
        st.metric("Quality Score", f"{100 - outlier_percent:.1f}%")
        st.caption("Chunks within size limits (100-500 tokens)")


def show_document_browser():
    """Display the main document browser interface"""
    st.markdown("Browse and view processed policy documents")
    
    # Initialize file tracker
    try:
        tracker = FileTracker()
    except Exception as e:
        st.error(f"Error initializing file tracker: {e}")
        st.write("Debug info:")
        st.write(f"Current working directory: {Path.cwd()}")
        st.write(f"Database path: data/file_tracker.db")
        st.write(f"Database exists: {Path('data/file_tracker.db').exists()}")
        return
    
    # Sidebar controls
    st.sidebar.header("🔧 Controls")
    
    # Refresh data button
    if st.sidebar.button("🔄 Refresh Data"):
        with st.spinner("Syncing files..."):
            tracker.sync_discovered_files()
            tracker.sync_processing_status()
        st.sidebar.success("Data refreshed!")
        st.rerun()
    
    # Get summaries
    status_summary = tracker.get_status_summary()
    category_summary = tracker.get_category_summary()
    
    # Status metrics
    st.sidebar.header("📊 Processing Status")
    total_files = sum(status_summary.values())
    st.sidebar.metric("Total Files", total_files)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        completed = status_summary.get('completed', 0)
        st.metric("✅ Completed", completed)
    with col2:
        failed = status_summary.get('failed', 0)
        st.metric("❌ Failed", failed)
    
    # Progress bar
    if total_files > 0:
        progress = completed / total_files
        st.sidebar.progress(progress, text=f"{progress:.1%} Complete")
    
    # Filters
    st.sidebar.header("🔍 Filters")
    
    # Status filter
    status_options = ['All'] + [status.value for status in ProcessingStatus]
    selected_status = st.sidebar.selectbox("Status", status_options)
    
    # Category filter
    category_options = ['All'] + list(category_summary.keys())
    selected_category = st.sidebar.selectbox("Category", category_options)
    
    # Get filtered files
    status_filter = None if selected_status == 'All' else ProcessingStatus(selected_status)
    category_filter = None if selected_category == 'All' else selected_category
    
    files = tracker.get_all_files(status_filter, category_filter)
    
    # Main content area
    if not files:
        st.info("No files found matching the selected filters.")
        return
    
    # File list
    st.header(f"📋 Files ({len(files)} found)")
    
    # Convert to DataFrame for better display
    file_data = []
    for file_record in files:
        file_data.append({
            'Status': f"{status_emoji(file_record.status)} {file_record.status.value}",
            'Filename': file_record.filename,
            'Category': file_record.category,
            'Size': format_file_size(file_record.file_size),
            'Chunks': file_record.chunk_count or 0,
            'Discovered': file_record.discovered_at.strftime('%Y-%m-%d %H:%M'),
            'doc_id': file_record.doc_id  # Hidden column for selection
        })
    
    df = pd.DataFrame(file_data)
    
    # File selection
    selected_indices = st.dataframe(
        df.drop('doc_id', axis=1),  # Hide doc_id column
        selection_mode="single-row",
        on_select="rerun",
        use_container_width=True
    )
    
    # File detail view
    if selected_indices.selection.rows:
        selected_idx = selected_indices.selection.rows[0]
        selected_file = files[selected_idx]
        
        st.header(f"📄 {selected_file.filename}")
        
        # File metadata
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Status", f"{status_emoji(selected_file.status)} {selected_file.status.value}")
        with col2:
            st.metric("Category", selected_file.category)
        with col3:
            st.metric("File Size", format_file_size(selected_file.file_size))
        with col4:
            if selected_file.chunk_count:
                st.metric("Chunks", selected_file.chunk_count)
        
        # Processing timeline
        if selected_file.status != ProcessingStatus.DISCOVERED:
            st.subheader("⏱️ Processing Timeline")
            timeline_col1, timeline_col2, timeline_col3 = st.columns(3)
            
            with timeline_col1:
                st.write(f"**Discovered:** {selected_file.discovered_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            with timeline_col2:
                if selected_file.processing_started_at:
                    st.write(f"**Started:** {selected_file.processing_started_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            with timeline_col3:
                if selected_file.processing_completed_at:
                    st.write(f"**Completed:** {selected_file.processing_completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Error message
        if selected_file.error_message:
            st.error(f"**Error:** {selected_file.error_message}")
        
        # File content (only if processed)
        if selected_file.status == ProcessingStatus.COMPLETED:
            content, metadata, chunks = load_file_content(selected_file.doc_id)
            
            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📄 Content", "🏷️ Metadata", "✂️ Chunks", "📁 File Info"])
            
            with tab1:
                st.subheader("Parsed Content")
                if content:
                    st.markdown(content)
                else:
                    st.warning("No content available")
            
            with tab2:
                st.subheader("Extracted Metadata")
                if metadata:
                    st.json(metadata, expanded=True)
                else:
                    st.warning("No metadata available")
            
            with tab3:
                st.subheader("Document Chunks")
                if chunks and 'chunks' in chunks:
                    chunk_list = chunks['chunks']
                    st.write(f"**Total chunks:** {len(chunk_list)}")
                    
                    for i, chunk in enumerate(chunk_list):
                        with st.expander(f"Chunk {i+1} ({chunk.get('token_estimate', 0)} tokens)"):
                            if chunk.get('section_title'):
                                st.write(f"**Section:** {chunk['section_title']}")
                            st.markdown(chunk.get('text', ''))
                else:
                    st.warning("No chunks available")
            
            with tab4:
                st.subheader("File Information")
                info_data = {
                    "Document ID": selected_file.doc_id,
                    "Original Path": selected_file.file_path,
                    "File Extension": selected_file.file_extension,
                    "File Hash": selected_file.file_hash,
                    "Content Length": f"{selected_file.content_length:,} characters" if selected_file.content_length else "N/A",
                    "Metadata Extracted": "Yes" if selected_file.metadata_extracted else "No"
                }
                
                for key, value in info_data.items():
                    st.write(f"**{key}:** {value}")


if __name__ == "__main__":
    main()