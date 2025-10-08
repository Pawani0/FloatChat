"""
FloatChat App Package

Sprint 2: LLM + RAG Integration for Oceanographic Research
"""

__version__ = "2.0.0"
__author__ = "FloatChat Development Team"

from app.config.settings import AppConfig
from app.services.rag_service import EnhancedRAGService
from app.services.llm_service import OceanographicGeminiService

__all__ = [
    'AppConfig',
    'EnhancedRAGService',
    'OceanographicGeminiService'
]
