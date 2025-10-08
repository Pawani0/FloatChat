"""
Configuration module for FloatChat Sprint 1 - BGE-M3 Embedding Pipeline
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Configuration class for the BGE-M3 embedding pipeline.

    This class manages all configuration settings including paths, model parameters,
    and processing settings for the embedding pipeline.
    """

    # Paths Configuration - Use absolute paths to avoid working directory issues
    CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Use absolute paths by default, only use env vars if explicitly set to non-relative paths
    text_env = os.getenv("TEXT_DATA_PATH", "")
    faiss_env = os.getenv("FAISS_INDEX_PATH", "")
    model_env = os.getenv("MODEL_CACHE_DIR", "")
    
    TEXT_DATA_PATH = os.path.join(CURRENT_DIR, "data", "text_files") if not text_env or text_env.startswith('./') else text_env
    FAISS_INDEX_PATH = os.path.join(CURRENT_DIR, "data", "faiss_indexes") if not faiss_env or faiss_env.startswith('./') else faiss_env
    MODEL_CACHE_DIR = os.path.join(CURRENT_DIR, "models") if not model_env or model_env.startswith('./') else model_env

    # Device Configuration
    DEVICE = os.getenv("DEVICE", "cpu")

    # BGE-M3 Model Configuration
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
    MAX_LENGTH = int(os.getenv("MAX_LENGTH", "8192"))

    # Text Processing Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))  # characters per chunk
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))  # overlap between chunks

    # FAISS Configuration
    INDEX_TYPE = os.getenv("INDEX_TYPE", "FLAT")  # or "IVF"
    N_CLUSTERS = int(os.getenv("N_CLUSTERS", "100"))  # for IVF index

    # Batch Processing Configuration
    DEFAULT_BATCH_SIZE = 8
    MAX_BATCH_SIZE = 32

    # Model Performance Configuration
    USE_FP16 = True  # Use float16 for faster inference on GPU

    @classmethod
    def get_device_info(cls):
        """
        Get information about the current device configuration.

        Returns:
            dict: Dictionary containing device information
        """
        return {
            "device": cls.DEVICE,
            "embedding_model": cls.EMBEDDING_MODEL,
            "embedding_dimension": cls.EMBEDDING_DIMENSION,
            "max_length": cls.MAX_LENGTH,
            "chunk_size": cls.CHUNK_SIZE,
            "chunk_overlap": cls.CHUNK_OVERLAP,
            "index_type": cls.INDEX_TYPE,
            "n_clusters": cls.N_CLUSTERS
        }

    @classmethod
    def validate_paths(cls):
        """
        Validate that all required directories exist or create them.

        This method ensures that all necessary directories are available
        before starting the pipeline execution.
        """
        paths_to_check = [
            cls.TEXT_DATA_PATH,
            cls.FAISS_INDEX_PATH,
            cls.MODEL_CACHE_DIR
        ]

        for path in paths_to_check:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                print(f"Created directory: {path}")

    @classmethod
    def print_config_summary(cls):
        """
        Print a summary of the current configuration settings.

        This is useful for debugging and verification of settings.
        """
        print("=== FloatChat Configuration Summary ===")
        config_info = cls.get_device_info()

        for key, value in config_info.items():
            print(f"{key}: {value}")

        print(f"Text data path: {cls.TEXT_DATA_PATH}")
        print(f"FAISS index path: {cls.FAISS_INDEX_PATH}")
        print(f"Model cache directory: {cls.MODEL_CACHE_DIR}")
        print("=====================================")


# Validate paths on module import
Config.validate_paths()
