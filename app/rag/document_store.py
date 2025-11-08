"""FAISS-based document store for RAG system using OpenAI embeddings only."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle
from datetime import datetime
import numpy as np

try:
    import faiss
    from openai import OpenAI
except ImportError as e:
    raise ImportError(f"Required package not found: {e}. Install with: uv sync")


class DocumentStore:
    """Simple FAISS-based document store using OpenAI embeddings. No PyTorch."""
    
    def __init__(self, index_path: Path, openai_api_key: Optional[str] = None):
        """Initialize document store with OpenAI embeddings."""
        if not openai_api_key:
            raise ValueError("OpenAI API key required for embeddings")
            
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.faiss_index_file = self.index_path / "faiss_index.bin"
        self.metadata_file = self.index_path / "metadata.pkl"
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=openai_api_key)
        self.embedding_model = "text-embedding-3-small"
        
        # FAISS index
        self.dimension = 1536
        self.index = None
        self.documents = []
        self.metadata = []
        
        self._load_index()
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using OpenAI."""
        response = self.client.embeddings.create(model=self.embedding_model, input=text)
        return np.array(response.data[0].embedding, dtype=np.float32)
    
    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for multiple texts."""
        response = self.client.embeddings.create(model=self.embedding_model, input=texts)
        embeddings = [np.array(item.embedding, dtype=np.float32) for item in response.data]
        return np.vstack(embeddings)
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Simple text chunking."""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            
            if end < text_len:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return [c for c in chunks if c]
    
    def _load_index(self):
        """Load existing FAISS index or create new."""
        if self.faiss_index_file.exists() and self.metadata_file.exists():
            try:
                self.index = faiss.read_index(str(self.faiss_index_file))
                with open(self.metadata_file, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents', [])
                    self.metadata = data.get('metadata', [])
            except Exception as e:
                print(f"Error loading index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create new FAISS index."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        self.metadata = []
    
    def _save_index(self):
        """Save FAISS index and metadata."""
        faiss.write_index(self.index, str(self.faiss_index_file))
        data = {'documents': self.documents, 'metadata': self.metadata}
        with open(self.metadata_file, 'wb') as f:
            pickle.dump(data, f)
    
    def add_documents(self, texts: List[str], source: str = "unknown", 
                     metadatas: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Add documents to store."""
        if not texts:
            return {"status": "error", "message": "No texts provided"}
        
        all_chunks = []
        all_metadata = []
        
        for i, text in enumerate(texts):
            chunks = self._chunk_text(text)
            all_chunks.extend(chunks)
            
            base_meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            for chunk_idx, chunk in enumerate(chunks):
                meta = {
                    'source': source,
                    'doc_index': i,
                    'chunk_index': chunk_idx,
                    'timestamp': datetime.now().isoformat(),
                    **base_meta
                }
                all_metadata.append(meta)
        
        embeddings = self._get_embeddings(all_chunks)
        self.index.add(embeddings)
        self.documents.extend(all_chunks)
        self.metadata.extend(all_metadata)
        self._save_index()
        
        return {
            "status": "success",
            "chunks_added": len(all_chunks),
            "total_documents": len(self.documents)
        }
    
    def search(self, query: str, k: int = 5, filter_source: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if not self.documents:
            return []
        
        query_embedding = self._get_embedding(query).reshape(1, -1)
        distances, indices = self.index.search(query_embedding, min(k * 2, len(self.documents)))
        
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            
            meta = self.metadata[idx]
            if filter_source and meta.get('source') != filter_source:
                continue
            
            results.append({
                'text': self.documents[idx],
                'metadata': meta,
                'score': float(distance)
            })
            
            if len(results) >= k:
                break
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics."""
        sources = {}
        for meta in self.metadata:
            source = meta.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        return {
            'total_documents': len(self.documents),
            'sources': sources,
            'index_dimension': self.dimension,
            'embedding_model': self.embedding_model
        }
    
    def clear_index(self):
        """Clear all documents."""
        self._create_new_index()
        self._save_index()
        return {"status": "success", "message": "Index cleared"}
    
    def delete_by_source(self, source: str) -> Dict[str, Any]:
        """Delete documents from source."""
        indices_to_keep = [i for i, meta in enumerate(self.metadata) 
                          if meta.get('source') != source]
        
        if len(indices_to_keep) == len(self.documents):
            return {"status": "error", "message": f"No documents found from source: {source}"}
        
        remaining_docs = [self.documents[i] for i in indices_to_keep]
        remaining_meta = [self.metadata[i] for i in indices_to_keep]
        
        if remaining_docs:
            embeddings = self._get_embeddings(remaining_docs)
            self._create_new_index()
            self.index.add(embeddings)
        else:
            self._create_new_index()
        
        self.documents = remaining_docs
        self.metadata = remaining_meta
        self._save_index()
        
        return {
            "status": "success",
            "deleted_count": len(self.metadata) - len(remaining_meta),
            "remaining_documents": len(self.documents)
        }


class RAGRetriever:
    """Simple wrapper for RAG retrieval."""
    
    def __init__(self, doc_store: DocumentStore):
        self.doc_store = doc_store
    
    def get_context(self, query: str, k: int = 3) -> str:
        """Get context for query."""
        results = self.doc_store.search(query, k=k)
        
        if not results:
            return "No relevant context found."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result['metadata'].get('source', 'unknown')
            text = result['text']
            context_parts.append(f"[{i}] (from {source}):\n{text}")
        
        return "\n\n".join(context_parts)
