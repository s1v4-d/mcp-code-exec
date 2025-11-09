#!/usr/bin/env python3
"""Setup script to embed RAG documents during initialization."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.rag.service import rag_service


def load_documents_from_directory(directory: Path) -> list[tuple[str, str]]:
    """Load documents from directory."""
    documents = []
    text_extensions = {'.txt', '.md', '.csv', '.json', '.py', '.rst'}
    
    if not directory.exists():
        print(f"Directory not found: {directory}")
        return documents
    
    for file_path in directory.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in text_extensions:
            try:
                content = file_path.read_text(encoding='utf-8')
                relative_path = file_path.relative_to(directory)
                documents.append((content, str(relative_path)))
                print(f"  Loaded: {relative_path} ({len(content)} chars)")
            except Exception as e:
                print(f"  Error reading {file_path}: {e}")
    
    return documents


def setup_rag_index():
    """Setup RAG index with documents from data/rag directory."""
    print("Setting up RAG index...")
    
    if not rag_service.is_ready:
        print("WARNING: OPENAI_API_KEY not configured in .env file")
        print("RAG setup skipped. Please configure your API key to use RAG features.")
        return
    
    # Check existing documents
    stats = rag_service.get_stats()
    print(f"Current index: {stats.get('total_documents', 0)} documents")
    
    # Load documents from data/rag directory
    rag_data_dir = project_root / "data" / "rag"
    print(f"\nLoading documents from: {rag_data_dir}")
    
    documents = load_documents_from_directory(rag_data_dir)
    
    if not documents:
        print("No documents found in data/rag directory")
        print("Add .txt, .md, .csv, .json, or .py files to data/rag/ to populate the RAG index")
        return
    
    # Embed documents using the service
    print(f"\nEmbedding {len(documents)} documents...")
    texts = [doc[0] for doc in documents]
    metadatas = [{'filename': doc[1]} for doc in documents]
    
    result = rag_service.add_documents(texts, source='local_files', metadatas=metadatas)
    
    if result['status'] == 'success':
        print(f"\nSuccess! Added {result['chunks_added']} chunks")
        print(f"Total documents in index: {result['total_documents']}")
    else:
        print(f"Error: {result.get('message', 'Unknown error')}")


if __name__ == "__main__":
    try:
        setup_rag_index()
    except Exception as e:
        print(f"Error during RAG setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
