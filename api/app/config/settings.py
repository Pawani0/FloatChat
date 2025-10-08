"""
Configuration settings for FloatChat Sprint 2 LLM + RAG Application
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AppConfig:
    """Application configuration for Sprint 2"""

    # RAG Configuration
    RAG_INDEX_NAME = "oceanographic_data_v1"

    # LLM Configuration - Gemini API
    DEFAULT_LLM_MODEL = "gemini-2.0-flash"  # Google's Gemini model
    # Alternative models: "gemini-1.5-pro", "gemini-1.5-flash"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # Generation Configuration
    LLM_MAX_TOKENS = 2048  # Gemini can handle longer responses
    LLM_TEMPERATURE = 0.7
    LLM_TOP_P = 0.9
    MAX_CONTEXT_LENGTH = 8192  # Gemini's context window
    MAX_RESPONSE_LENGTH = 1024  # Longer responses possible
    CONTEXT_WINDOW_SIZE = 8  # More documents with Gemini's larger context

    # Streamlit Configuration
    APP_TITLE = "FloatChat - Oceanographic AI Assistant"
    APP_DESCRIPTION = "Advanced RAG-powered AI assistant for oceanographic research with Google Gemini"

    # Performance Settings
    BATCH_SIZE = 8
    MAX_WORKERS = 4

    # Cache Settings
    CACHE_TTL = 3600  # 1 hour
    MAX_CACHE_SIZE = 1000

    @classmethod
    def get_model_path(cls, model_name: str) -> str:
        """Get local path for model storage (not used for Gemini API)"""
        return os.path.join("models", "llm", model_name.replace("/", "_"))

    @classmethod
    def is_model_available(cls, model_name: str) -> bool:
        """Check if model is available (always True for Gemini API)"""
        return bool(cls.GEMINI_API_KEY)

    @classmethod
    def get_device(cls) -> str:
        """Get computation device (not relevant for API-based models)"""
        return "cloud"  # Gemini runs in Google's cloud
