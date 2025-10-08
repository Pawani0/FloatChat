"""
RAG Service for FloatChat Sprint 2

Integrates retrieval (RAG) with the existing embedding pipeline
and provides enhanced search capabilities.
"""

import os
import sys
import logging
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from datetime import datetime

# Add src to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
src_dir = os.path.join(parent_dir, 'src')
sys.path.append(src_dir)

from src.embeddings.bge_embedder import BGEM3Embedder
from src.embeddings.faiss_manager import FAISSManager
from src.embeddings.text_processor import TextProcessor

logger = logging.getLogger(__name__)

class EnhancedRAGService:
    """Enhanced RAG service with advanced retrieval capabilities"""

    def __init__(self, index_name: str = "oceanographic_data_v1"):
        self.index_name = index_name
        self.embedder = None
        self.faiss_manager = None
        self.processor = None
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all RAG components"""
        try:
            logger.info("Initializing RAG components...")

            self.embedder = BGEM3Embedder()
            self.faiss_manager = FAISSManager(self.index_name)
            self.processor = TextProcessor()

            # Load index if it exists
            if os.path.exists(self.faiss_manager.index_path):
                self.faiss_manager.load_index()
                logger.info("RAG components initialized successfully")
            else:
                logger.warning("No existing index found. Run pipeline first.")

        except Exception as e:
            logger.error(f"Error initializing RAG components: {e}")
            raise RuntimeError(f"Failed to initialize RAG components: {e}")

    def retrieve(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.1,
        include_metadata: bool = True
    ) -> Tuple[List[Dict], Dict]:
        """Retrieve relevant documents for a query"""

        try:
            # Generate query embedding
            query_embedding = self.embedder.embed_query(query)

            # Search FAISS index
            scores, results = self.faiss_manager.search(query_embedding, k=k)

            # Filter by threshold
            filtered_results = []
            for score, result in zip(scores, results):
                if score >= threshold:
                    if include_metadata:
                        filtered_results.append({
                            **result,
                            'similarity_score': score
                        })
                    else:
                        filtered_results.append(result)

            # Prepare metadata
            retrieval_metadata = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'total_results': len(results),
                'filtered_results': len(filtered_results),
                'threshold': threshold,
                'k': k
            }

            return filtered_results, retrieval_metadata

        except Exception as e:
            logger.error(f"Error in retrieval: {e}")
            return [], {'error': str(e), 'query': query}

    def retrieve_with_reranking(
        self,
        query: str,
        k: int = 10,
        rerank_k: int = 5
    ) -> Tuple[List[Dict], Dict]:
        """Retrieve documents with two-stage retrieval and reranking"""

        # First stage: Get more candidates
        candidates, metadata = self.retrieve(query, k=k, threshold=0.0)

        if not candidates:
            return [], metadata

        # Second stage: Rerank using semantic similarity
        reranked_results = self._rerank_documents(query, candidates, rerank_k)

        return reranked_results, metadata

    def _rerank_documents(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int
    ) -> List[Dict]:
        """Rerank candidates based on semantic similarity"""
        try:
            # Get query embedding
            query_embedding = self.embedder.embed_query(query)

            # Calculate similarity for each candidate
            reranked = []
            for candidate in candidates:
                doc_text = candidate.get('text', '')
                doc_embedding = self.embedder.embed_text(doc_text)

                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, doc_embedding)

                reranked.append({
                    **candidate,
                    'reranked_score': similarity
                })

            # Sort by reranked score and return top_k
            reranked.sort(key=lambda x: x['reranked_score'], reverse=True)
            return reranked[:top_k]

        except Exception as e:
            logger.error(f"Error in reranking: {e}")
            return candidates[:top_k]

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def add_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict]] = None,
        batch_size: int = 5
    ) -> Dict:
        """Add new documents to the RAG system"""

        try:
            # Process documents into chunks
            all_chunks = []
            for i, doc in enumerate(documents):
                doc_metadata = metadata[i] if metadata and i < len(metadata) else {}
                chunks = self.processor.chunk_text(doc, metadata=doc_metadata)
                all_chunks.extend(chunks)

            # Generate embeddings
            texts_to_embed = [chunk['text'] for chunk in all_chunks]
            embeddings = []

            for i in range(0, len(texts_to_embed), batch_size):
                batch_texts = texts_to_embed[i:i + batch_size]
                batch_embeddings = self.embedder.embed_batch(batch_texts, batch_size=batch_size)
                embeddings.extend(batch_embeddings)

            # Update FAISS index
            if self.faiss_manager.index is None:
                # Create new index
                self.faiss_manager.create_index(embeddings)
                self.faiss_manager.metadata = all_chunks
            else:
                # Add to existing index
                self.faiss_manager.index.add(np.array(embeddings, dtype=np.float32))
                self.faiss_manager.metadata.extend(all_chunks)

            # Save updated index
            self.faiss_manager.save_index(self.faiss_manager.metadata)

            return {
                'status': 'success',
                'documents_added': len(documents),
                'chunks_created': len(all_chunks),
                'total_vectors': self.faiss_manager.index.ntotal if self.faiss_manager.index else 0
            }

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return {'status': 'error', 'error': str(e)}

    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        try:
            if not self.faiss_manager or not self.faiss_manager.index:
                return {'status': 'no_index'}

            faiss_stats = self.faiss_manager.get_stats()

            return {
                'rag_service': {
                    'status': 'active',
                    'index_name': self.index_name,
                    'total_documents': len(set(
                        m.get('source_file', 'Unknown')
                        for m in self.faiss_manager.metadata
                    )) if self.faiss_manager.metadata else 0,
                    'total_chunks': len(self.faiss_manager.metadata) if self.faiss_manager.metadata else 0
                },
                'faiss_index': faiss_stats,
                'embedder': self.embedder.get_model_info() if self.embedder else {},
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {'status': 'error', 'error': str(e)}

    def clear_cache(self):
        """Clear all caches"""
        if self.embedder:
            self.embedder.clear_cache()

        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass  # torch not available

        import gc
        gc.collect()

        logger.info("RAG service cache cleared")
