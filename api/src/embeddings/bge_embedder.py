"""
BGE-M3 Embedder module for FloatChat Sprint 1

This module provides embedding functionality using the BGE-M3 model,
which supports dense retrieval, sparse retrieval, and multi-vector retrieval.
"""

import torch
import numpy as np
from typing import List, Dict, Any, Optional
from FlagEmbedding import BGEM3FlagModel
import time
import gc
from src.utils.config import Config


class BGEM3Embedder:
    """
    BGE-M3 embedder for generating high-quality vector embeddings.

    This class provides methods for embedding single texts, batches of texts,
    and calculating similarity between texts using the BGE-M3 model.
    """

    def __init__(self, use_fp16: Optional[bool] = None):
        """
        Initialize BGE-M3 embedder.

        Args:
            use_fp16 (bool, optional): Whether to use FP16 precision.
                If None, will be determined based on device availability.
        """
        self.model_name = Config.EMBEDDING_MODEL
        self.device = Config.DEVICE
        self.dimension = Config.EMBEDDING_DIMENSION
        self.max_length = Config.MAX_LENGTH

        # Determine FP16 usage
        if use_fp16 is None:
            self.use_fp16 = self.device == 'cuda' and Config.USE_FP16
        else:
            self.use_fp16 = use_fp16

        # Initialize timing
        self.load_start_time = time.time()

        print(f"Loading BGE-M3 model '{self.model_name}' on {self.device}...")
        print(f"Using FP16: {self.use_fp16}")

        try:
            # Initialize BGE-M3 model
            self.model = BGEM3FlagModel(
                self.model_name,
                use_fp16=self.use_fp16,
                device=self.device,
                cache_dir=Config.MODEL_CACHE_DIR
            )

            self.load_time = time.time() - self.load_start_time
            print(f"BGE-M3 model loaded successfully in {self.load_time:.2f} seconds!")

        except Exception as e:
            print(f"Error loading BGE-M3 model: {e}")
            print("Falling back to CPU...")
            self.device = 'cpu'
            self.use_fp16 = False

            self.model = BGEM3FlagModel(
                self.model_name,
                use_fp16=False,
                device='cpu',
                cache_dir=Config.MODEL_CACHE_DIR
            )

            self.load_time = time.time() - self.load_start_time
            print(f"BGE-M3 model loaded on CPU in {self.load_time:.2f} seconds!")

    def embed_text(self, text: str, max_length: Optional[int] = None) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text (str): Input text to embed
            max_length (int, optional): Maximum sequence length. If None, uses config default.

        Returns:
            np.ndarray: Embedding vector of shape (dimension,)
        """
        try:
            max_len = max_length or self.max_length

            # Generate dense embedding
            embeddings = self.model.encode(
                [text],
                batch_size=1,
                max_length=max_len,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False
            )

            return embeddings['dense_vecs'][0].astype(np.float32)

        except Exception as e:
            print(f"Error embedding text: {e}")
            print(f"Text length: {len(text)} characters")
            return np.zeros(self.dimension, dtype=np.float32)

    def embed_batch(self, texts: List[str], batch_size: Optional[int] = None,
                   max_length: Optional[int] = None) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts (List[str]): List of texts to embed
            batch_size (int, optional): Batch size for processing. If None, uses config default.
            max_length (int, optional): Maximum sequence length. If None, uses config default.

        Returns:
            List[np.ndarray]: List of embedding vectors
        """
        if not texts:
            return []

        batch_size = batch_size or Config.DEFAULT_BATCH_SIZE
        max_len = max_length or self.max_length

        all_embeddings = []

        print(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}")
        print(f"Using max_length: {max_len}")

        start_time = time.time()

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                # Generate embeddings for batch
                batch_embeddings = self.model.encode(
                    batch,
                    batch_size=len(batch),
                    max_length=max_len,
                    return_dense=True,
                    return_sparse=False,
                    return_colbert_vecs=False
                )

                # Convert to numpy arrays and ensure float32
                for embedding in batch_embeddings['dense_vecs']:
                    all_embeddings.append(embedding.astype(np.float32))

                # Progress update
                processed = min(i + batch_size, len(texts))
                progress = (processed / len(texts)) * 100
                print(f"Processed {processed}/{len(texts)} texts ({progress:.1f}%)")

            except Exception as e:
                print(f"Error processing batch {i//batch_size + 1}: {e}")
                print(f"Batch size: {len(batch)}")

                # Add zero embeddings for failed batch
                for _ in batch:
                    all_embeddings.append(np.zeros(self.dimension, dtype=np.float32))

        total_time = time.time() - start_time
        avg_time_per_text = total_time / len(texts) if texts else 0

        print(f"Embedding generation completed in {total_time:.2f} seconds")
        print(f"Average time per text: {avg_time_per_text:.4f} seconds")

        return all_embeddings

    def embed_query(self, query: str, max_length: Optional[int] = None) -> np.ndarray:
        """
        Generate embedding for search query.

        For BGE-M3, query and document embeddings are generated the same way,
        but this method provides a semantic distinction.

        Args:
            query (str): Search query
            max_length (int, optional): Maximum sequence length

        Returns:
            np.ndarray: Query embedding vector
        """
        return self.embed_text(query, max_length)

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.

        Returns:
            Dict[str, Any]: Model information including performance metrics
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "dimension": self.dimension,
            "max_length": self.max_length,
            "supports_multilingual": True,
            "supports_long_text": True,
            "model_size": "2.3GB",
            "load_time_seconds": round(self.load_time, 2),
            "use_fp16": self.use_fp16,
            "embedding_types": ["dense", "sparse", "colbert"],  # BGE-M3 supports all
            "max_supported_tokens": self.max_length
        }

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.

        Args:
            text1 (str): First text
            text2 (str): Second text

        Returns:
            float: Cosine similarity score between 0.0 and 1.0
        """
        try:
            embeddings = self.model.encode(
                [text1, text2],
                batch_size=2,
                max_length=self.max_length,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False
            )

            emb1 = embeddings['dense_vecs'][0]
            emb2 = embeddings['dense_vecs'][1]

            # Calculate cosine similarity
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

            return float(max(0.0, min(1.0, similarity)))  # Clamp to [0, 1]

        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

    def encode_with_all_features(self, texts: List[str], batch_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate all types of embeddings supported by BGE-M3.

        Args:
            texts (List[str]): List of texts to encode
            batch_size (int, optional): Batch size for processing

        Returns:
            Dict[str, Any]: Dictionary containing dense, sparse, and colbert embeddings
        """
        batch_size = batch_size or Config.DEFAULT_BATCH_SIZE

        try:
            # Generate all types of embeddings
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                max_length=self.max_length,
                return_dense=True,
                return_sparse=True,
                return_colbert_vecs=True
            )

            return {
                'dense_embeddings': [emb.astype(np.float32) for emb in embeddings['dense_vecs']],
                'sparse_embeddings': embeddings.get('lexical_weights', []),
                'colbert_embeddings': embeddings.get('colbert_vecs', []),
                'token_weights': embeddings.get('token_weights', [])
            }

        except Exception as e:
            print(f"Error generating full embeddings: {e}")
            return {
                'dense_embeddings': [],
                'sparse_embeddings': [],
                'colbert_embeddings': [],
                'token_weights': []
            }

    def clear_cache(self):
        """
        Clear GPU cache and garbage collect to free memory.
        """
        if self.device == 'cuda':
            torch.cuda.empty_cache()

        gc.collect()

        print("Cache cleared and garbage collected")

    def __del__(self):
        """
        Cleanup method to free resources when object is destroyed.
        """
        self.clear_cache()
