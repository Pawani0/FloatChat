"""
FAISS Manager module for FloatChat Sprint 1

This module handles FAISS vector index creation, storage, and similarity search
for the BGE-M3 embedding pipeline.
"""

import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Tuple, Any, Optional
import time
import json
from pathlib import Path
from src.utils.config import Config


class FAISSManager:
    """
    FAISS manager for vector storage and similarity search.

    This class provides functionality to create, save, load, and search
    FAISS indexes for efficient similarity search operations.
    """

    def __init__(self, index_name: str = "oceanographic_data"):
        """
        Initialize FAISS manager.

        Args:
            index_name (str): Name for the index files
        """
        self.index_name = index_name
        self.dimension = Config.EMBEDDING_DIMENSION

        # Set up paths
        self.index_path = os.path.join(Config.FAISS_INDEX_PATH, f"{index_name}.index")
        self.metadata_path = os.path.join(Config.FAISS_INDEX_PATH, f"{index_name}_metadata.pkl")
        self.config_path = os.path.join(Config.FAISS_INDEX_PATH, f"{index_name}_config.json")

        # Ensure directory exists
        os.makedirs(Config.FAISS_INDEX_PATH, exist_ok=True)

        # Initialize attributes
        self.index = None
        self.metadata = []
        self.config = {}

        print(f"FAISS manager initialized for index: {index_name}")
        print(f"Index path: {self.index_path}")
        print(f"Metadata path: {self.metadata_path}")

    def create_index(self, embeddings: List[np.ndarray],
                    index_type: Optional[str] = None,
                    normalize: bool = True) -> faiss.Index:
        """
        Create FAISS index from embeddings.

        Args:
            embeddings (List[np.ndarray]): List of embedding vectors
            index_type (str, optional): Type of FAISS index ("FLAT" or "IVF")
            normalize (bool): Whether to normalize embeddings for cosine similarity

        Returns:
            faiss.Index: Created FAISS index
        """
        if not embeddings:
            raise ValueError("No embeddings provided for index creation")

        # Convert embeddings to numpy array
        embedding_matrix = np.vstack(embeddings).astype(np.float32)

        print(f"Creating FAISS index from {len(embeddings)} embeddings")
        print(f"Embedding shape: {embedding_matrix.shape}")

        # Normalize embeddings if requested (for cosine similarity)
        if normalize:
            print("Normalizing embeddings for cosine similarity...")
            faiss.normalize_L2(embedding_matrix)

        # Determine index type
        if index_type is None:
            index_type = Config.INDEX_TYPE
            if len(embeddings) >= 1000:
                index_type = "IVF"  # Use IVF for larger datasets

        print(f"Using index type: {index_type}")

        # Create index based on type
        if index_type == "FLAT":
            # Simple brute-force search - most accurate but slower
            if normalize:
                self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product (cosine)
            else:
                self.index = faiss.IndexFlatL2(self.dimension)  # L2 distance

        elif index_type == "IVF":
            # Inverted File index - faster search for large datasets
            if normalize:
                quantizer = faiss.IndexFlatIP(self.dimension)
            else:
                quantizer = faiss.IndexFlatL2(self.dimension)

            # Determine number of clusters
            n_clusters = min(Config.N_CLUSTERS, len(embeddings) // 40)
            n_clusters = max(1, n_clusters)  # At least 1 cluster

            print(f"Using {n_clusters} clusters for IVF index")

            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, n_clusters)

            # Train the index
            print("Training IVF index...")
            self.index.train(embedding_matrix)

        else:
            raise ValueError(f"Unsupported index type: {index_type}. "
                           "Supported types: 'FLAT', 'IVF'")

        # Add embeddings to index
        print("Adding embeddings to index...")
        self.index.add(embedding_matrix)

        # Store configuration
        self.config = {
            "index_type": index_type,
            "dimension": self.dimension,
            "normalized": normalize,
            "n_embeddings": len(embeddings),
            "n_clusters": getattr(self.index, 'nlist', None) if hasattr(self.index, 'nlist') else None,
            "creation_time": time.time()
        }

        print(f"FAISS index created successfully!")
        print(f"Index contains {self.index.ntotal} vectors")

        return self.index

    def save_index(self, metadata: Optional[List[Dict]] = None) -> bool:
        """
        Save FAISS index and metadata to disk.

        Args:
            metadata (List[Dict], optional): Metadata for each embedding

        Returns:
            bool: True if successful, False otherwise
        """
        if self.index is None:
            print("Error: No index to save. Create index first.")
            return False

        try:
            # Save FAISS index
            print(f"Saving FAISS index to: {self.index_path}")
            faiss.write_index(self.index, self.index_path)

            # Save metadata if provided
            if metadata is not None:
                self.metadata = metadata
                print(f"Saving metadata to: {self.metadata_path}")
                with open(self.metadata_path, 'wb') as f:
                    pickle.dump(metadata, f)

            # Save configuration
            print(f"Saving configuration to: {self.config_path}")
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)

            print("Index and metadata saved successfully!")
            return True

        except Exception as e:
            print(f"Error saving index: {e}")
            return False

    def load_index(self) -> bool:
        """
        Load FAISS index and metadata from disk.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if index file exists
            if not os.path.exists(self.index_path):
                print(f"Index file not found: {self.index_path}")
                return False

            # Load FAISS index
            print(f"Loading FAISS index from: {self.index_path}")
            self.index = faiss.read_index(self.index_path)

            # Load metadata if exists
            if os.path.exists(self.metadata_path):
                print(f"Loading metadata from: {self.metadata_path}")
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
            else:
                print("No metadata file found")
                self.metadata = []

            # Load configuration if exists
            if os.path.exists(self.config_path):
                print(f"Loading configuration from: {self.config_path}")
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)

            print("Index loaded successfully!")
            print(f"Index contains {self.index.ntotal} vectors")
            print(f"Metadata entries: {len(self.metadata)}")

            return True

        except Exception as e:
            print(f"Error loading index: {e}")
            return False

    def search(self, query_embedding: np.ndarray, k: int = 5,
              search_params: Optional[Dict] = None) -> Tuple[List[float], List[Dict]]:
        """
        Search for similar documents.

        Args:
            query_embedding (np.ndarray): Query embedding vector
            k (int): Number of results to return
            search_params (Dict, optional): Search parameters for advanced indexing

        Returns:
            Tuple[List[float], List[Dict]]: Similarity scores and metadata
        """
        if self.index is None:
            raise ValueError("No index loaded. Load or create index first.")

        # Ensure query embedding is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # Normalize query if index uses normalized embeddings
        if self.config.get('normalized', False):
            faiss.normalize_L2(query_embedding)

        # Set search parameters for IVF index
        if hasattr(self.index, 'nprobe') and search_params:
            nprobe = search_params.get('nprobe', 10)
            self.index.nprobe = nprobe

        # Perform search
        start_time = time.time()
        scores, indices = self.index.search(query_embedding, k)
        search_time = time.time() - start_time

        # Retrieve metadata for results
        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result['similarity_score'] = float(scores[0][i])
                result['rank'] = i + 1
                results.append(result)
            else:
                # Handle out-of-range indices
                results.append({
                    'similarity_score': float(scores[0][i]) if i < len(scores[0]) else 0.0,
                    'rank': i + 1,
                    'error': 'Index out of range'
                })

        print(f"Search completed in {search_time:.4f} seconds")
        print(f"Returned {len(results)} results")

        return scores[0].tolist(), results

    def search_with_threshold(self, query_embedding: np.ndarray,
                            threshold: float = 0.7, max_results: int = 100) -> Tuple[List[float], List[Dict]]:
        """
        Search with similarity threshold filtering.

        Args:
            query_embedding (np.ndarray): Query embedding vector
            threshold (float): Minimum similarity score (0.0 to 1.0)
            max_results (int): Maximum number of results to consider

        Returns:
            Tuple[List[float], List[Dict]]: Filtered similarity scores and metadata
        """
        # Get initial results
        raw_scores, raw_results = self.search(query_embedding, k=max_results)

        # Filter by threshold
        filtered_results = []
        filtered_scores = []

        for score, result in zip(raw_scores, raw_results):
            if score >= threshold:
                filtered_results.append(result)
                filtered_scores.append(score)

        print(f"Filtered {len(raw_results)} results to {len(filtered_results)} "
              f"above threshold {threshold}")

        return filtered_scores, filtered_results

    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the index.

        Returns:
            Dict[str, Any]: Index statistics
        """
        if self.index is None:
            return {"error": "No index loaded"}

        stats = {
            "index_name": self.index_name,
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": type(self.index).__name__,
            "metadata_count": len(self.metadata),
            "index_file_path": self.index_path,
            "metadata_file_path": self.metadata_path,
            "config_file_path": self.config_path
        }

        # Add configuration info
        stats.update(self.config)

        # Add index-specific stats
        if hasattr(self.index, 'nlist'):
            stats["nlist"] = self.index.nlist
        if hasattr(self.index, 'nprobe'):
            stats["nprobe"] = self.index.nprobe

        return stats

    def rebuild_index(self, embeddings: List[np.ndarray], metadata: List[Dict],
                     index_type: Optional[str] = None) -> bool:
        """
        Rebuild the index with new embeddings and metadata.

        Args:
            embeddings (List[np.ndarray]): New embedding vectors
            metadata (List[Dict]): New metadata
            index_type (str, optional): Type of index to create

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create new index
            self.create_index(embeddings, index_type=index_type)

            # Update metadata
            self.metadata = metadata

            # Save everything
            success = self.save_index()

            if success:
                print("Index rebuilt successfully!")

            return success

        except Exception as e:
            print(f"Error rebuilding index: {e}")
            return False

    def delete_index(self) -> bool:
        """
        Delete the index and associated files.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            files_to_delete = [self.index_path, self.metadata_path, self.config_path]

            for file_path in files_to_delete:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")

            # Reset in-memory objects
            self.index = None
            self.metadata = []
            self.config = {}

            print("Index deleted successfully!")
            return True

        except Exception as e:
            print(f"Error deleting index: {e}")
            return False

    def export_metadata(self, output_path: str) -> bool:
        """
        Export metadata to a JSON file for external analysis.

        Args:
            output_path (str): Path to save the metadata

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Export metadata with index information
            export_data = {
                "index_name": self.index_name,
                "metadata": self.metadata,
                "export_time": time.time(),
                "total_entries": len(self.metadata)
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            print(f"Metadata exported to: {output_path}")
            return True

        except Exception as e:
            print(f"Error exporting metadata: {e}")
            return False
