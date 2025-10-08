"""
Text Processor module for FloatChat Sprint 1

This module handles text preprocessing, chunking, and file management
for the BGE-M3 embedding pipeline.
"""

import os
import re
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import time
from src.utils.config import Config


class TextProcessor:
    """
    Text processor for cleaning, preprocessing, and chunking text data.

    This class provides functionality to load text files, clean text content,
    and split large texts into manageable chunks for embedding.
    """

    def __init__(self):
        """
        Initialize text processor with configuration settings.
        """
        self.chunk_size = Config.CHUNK_SIZE
        self.chunk_overlap = Config.CHUNK_OVERLAP
        self.supported_extensions = {'.txt', '.md', '.csv', '.json'}

        # Oceanographic-specific cleaning patterns
        self.oceanographic_terms = {
            'temperature', 'salinity', 'pressure', 'depth', 'conductivity',
            'oxygen', 'ph', 'chlorophyll', 'turbidity', 'current', 'velocity',
            'argo', 'ctd', 'bgc', 'float', 'sensor', 'profile', 'cast'
        }

        print(f"Text processor initialized with chunk_size={self.chunk_size}, "
              f"chunk_overlap={self.chunk_overlap}")

    def load_text_files(self, directory: str) -> Dict[str, str]:
        """
        Load all supported text files from a directory.

        Args:
            directory (str): Directory containing text files

        Returns:
            Dict[str, str]: Mapping of filename to content
        """
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist")
            return {}

        texts = {}
        total_files = 0
        loaded_files = 0

        print(f"Loading text files from: {directory}")

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            # Check if it's a supported file type
            if self._is_supported_file(filename):
                total_files += 1
                try:
                    content = self._read_file(file_path)
                    if content and len(content.strip()) > 0:
                        texts[filename] = content
                        loaded_files += 1
                        print(f"  Loaded: {filename} ({len(content)} characters)")
                    else:
                        print(f"  Skipped empty file: {filename}")

                except Exception as e:
                    print(f"  Error reading {filename}: {e}")

        print(f"Successfully loaded {loaded_files}/{total_files} files")
        return texts

    def _is_supported_file(self, filename: str) -> bool:
        """
        Check if a file has a supported extension.

        Args:
            filename (str): Name of the file

        Returns:
            bool: True if supported, False otherwise
        """
        return Path(filename).suffix.lower() in self.supported_extensions

    def _read_file(self, file_path: str) -> str:
        """
        Read content from a file with appropriate encoding handling.

        Args:
            file_path (str): Path to the file

        Returns:
            str: File content
        """
        # Try different encodings
        encodings = ['utf-8', 'latin1', 'cp1252']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                raise e

        raise UnicodeDecodeError(f"Could not decode file {file_path} with any supported encoding")

    def preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess text data.

        This method handles multiple cleaning steps including whitespace normalization,
        special character handling, and preservation of oceanographic terms.

        Args:
            text (str): Raw text input

        Returns:
            str: Preprocessed text
        """
        if not text:
            return ""

        original_length = len(text)

        # Step 1: Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        # Step 2: Handle special characters but preserve oceanographic terms
        # Remove most special characters but keep important ones
        text = re.sub(r'[^\w\s\-\.\,\;\:\(\)\[\]°%‰′″℃℉]', ' ', text)

        # Step 3: Clean up multiple spaces and normalize
        text = re.sub(r' +', ' ', text)

        # Step 4: Handle specific oceanographic formatting
        # Clean up degree symbols and units
        text = re.sub(r'°\s*C', '°C', text)  # Fix temperature notation
        text = re.sub(r'°\s*F', '°F', text)  # Fix temperature notation

        # Step 5: Remove excessive newlines and tabs
        text = text.replace('\n', ' ').replace('\t', ' ')

        # Step 6: Clean up spacing around punctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([,.!?;:])\s+', r'\1 ', text)

        # Step 7: Final cleanup
        text = text.strip()

        processed_length = len(text)
        compression_ratio = (original_length - processed_length) / original_length if original_length > 0 else 0

        if compression_ratio > 0.1:  # Log if significant compression
            print(f"  Text preprocessing: {original_length} → {processed_length} "
                  f"characters ({compression_ratio:.1%} compression)")

        return text

    def chunk_text(self, text: str, metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Split text into overlapping chunks.

        Args:
            text (str): Input text to chunk
            metadata (Dict, optional): Additional metadata for chunks

        Returns:
            List[Dict]: List of text chunks with metadata
        """
        if not text or len(text.strip()) == 0:
            return []

        words = text.split()
        chunks = []

        # Calculate words per chunk based on character limit
        avg_word_length = 5  # Average word length
        words_per_chunk = max(50, self.chunk_size // avg_word_length)  # Minimum 50 words
        overlap_words = max(10, self.chunk_overlap // avg_word_length)  # Minimum 10 words

        print(f"Chunking {len(words)} words into chunks of ~{words_per_chunk} words "
              f"with {overlap_words} word overlap")

        for i in range(0, len(words), words_per_chunk - overlap_words):
            chunk_words = words[i:i + words_per_chunk]
            chunk_text = ' '.join(chunk_words)

            # Only create chunk if it has sufficient content
            if len(chunk_text.strip()) > 50:  # Minimum chunk size
                chunk_data = {
                    'text': chunk_text,
                    'chunk_id': len(chunks),
                    'start_word': i,
                    'end_word': min(i + words_per_chunk, len(words)),
                    'word_count': len(chunk_words),
                    'char_count': len(chunk_text),
                    'metadata': metadata or {}
                }
                chunks.append(chunk_data)

        print(f"Created {len(chunks)} chunks from {len(words)} words")

        # Print some statistics
        if chunks:
            avg_chunk_size = sum(chunk['word_count'] for chunk in chunks) / len(chunks)
            print(f"Average chunk size: {avg_chunk_size:.0f} words")

        return chunks

    def process_all_files(self, directory: str) -> Tuple[List[Dict], List[str]]:
        """
        Process all text files in a directory.

        Args:
            directory (str): Directory containing text files

        Returns:
            Tuple[List[Dict], List[str]]: Processed chunks and texts for embedding
        """
        print("=== Text Processing Pipeline ===")

        # Step 1: Load text files
        start_time = time.time()
        files = self.load_text_files(directory)

        if not files:
            print("No files found to process")
            return [], []

        print(f"Loaded {len(files)} files")

        # Step 2: Process each file
        all_chunks = []
        texts_to_embed = []

        for filename, content in files.items():
            print(f"\nProcessing {filename}...")

            # Preprocess content
            clean_content = self.preprocess_text(content)

            if len(clean_content) == 0:
                print(f"  Skipping empty file after preprocessing: {filename}")
                continue

            # Create chunks
            chunks = self.chunk_text(
                clean_content,
                metadata={
                    'source_file': filename,
                    'original_length': len(content),
                    'processed_length': len(clean_content)
                }
            )

            # Add chunks to collection
            for chunk in chunks:
                all_chunks.append(chunk)
                texts_to_embed.append(chunk['text'])

        processing_time = time.time() - start_time
        print("\n=== Processing Summary ===")
        print(f"Total processing time: {processing_time:.2f} seconds")
        print(f"Files processed: {len(files)}")
        print(f"Chunks created: {len(all_chunks)}")
        print(f"Texts ready for embedding: {len(texts_to_embed)}")

        if all_chunks:
            avg_chunk_size = sum(chunk['word_count'] for chunk in all_chunks) / len(all_chunks)
            print(f"Average chunk size: {avg_chunk_size:.0f} words")

        return all_chunks, texts_to_embed

    def get_processing_stats(self, chunks: List[Dict]) -> Dict[str, Any]:
        """
        Get statistics about processed chunks.

        Args:
            chunks (List[Dict]): List of processed chunks

        Returns:
            Dict[str, Any]: Processing statistics
        """
        if not chunks:
            return {"error": "No chunks provided"}

        total_words = sum(chunk['word_count'] for chunk in chunks)
        total_chars = sum(chunk['char_count'] for chunk in chunks)
        avg_words_per_chunk = total_words / len(chunks)
        avg_chars_per_chunk = total_chars / len(chunks)

        # Get unique source files
        source_files = set()
        for chunk in chunks:
            if 'metadata' in chunk and 'source_file' in chunk['metadata']:
                source_files.add(chunk['metadata']['source_file'])

        return {
            "total_chunks": len(chunks),
            "total_words": total_words,
            "total_characters": total_chars,
            "average_words_per_chunk": round(avg_words_per_chunk, 1),
            "average_characters_per_chunk": round(avg_chars_per_chunk, 1),
            "unique_source_files": len(source_files),
            "chunk_size_config": self.chunk_size,
            "chunk_overlap_config": self.chunk_overlap
        }

    def save_processed_chunks(self, chunks: List[Dict], output_path: str):
        """
        Save processed chunks to a file for later use.

        Args:
            chunks (List[Dict]): Processed chunks to save
            output_path (str): Path to save the chunks
        """
        try:
            import json

            # Convert chunks to JSON-serializable format
            serializable_chunks = []
            for chunk in chunks:
                serializable_chunk = {
                    'text': chunk['text'],
                    'chunk_id': chunk['chunk_id'],
                    'start_word': chunk['start_word'],
                    'end_word': chunk['end_word'],
                    'word_count': chunk['word_count'],
                    'char_count': chunk['char_count'],
                    'metadata': chunk['metadata']
                }
                serializable_chunks.append(serializable_chunk)

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_chunks, f, indent=2, ensure_ascii=False)

            print(f"Processed chunks saved to: {output_path}")
            print(f"Total chunks saved: {len(serializable_chunks)}")

        except Exception as e:
            print(f"Error saving processed chunks: {e}")
