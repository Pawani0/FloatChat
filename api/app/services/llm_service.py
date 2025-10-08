"""
Gemini LLM Service for FloatChat Sprint 2

Integrates Google Gemini AI with RAG retrieval for
enhanced oceanographic research assistance.
"""

import os
import logging
from typing import List, Dict, Tuple, Optional, Any
import time
from datetime import datetime

import google.generativeai as genai
from app.tools.sql_tool import generate_postgresql_query, fire_sql
from app.config.settings import AppConfig

logger = logging.getLogger(__name__)

class OceanographicGeminiService:
    """Gemini LLM service optimized for oceanographic research"""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or AppConfig.DEFAULT_LLM_MODEL
        self.api_key = AppConfig.GEMINI_API_KEY

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required. "
                "Please get your API key from: https://aistudio.google.com/apikey"
            )

        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the Gemini model"""
        try:
            logger.info(f"Initializing Gemini model: {self.model_name}")

            self.model = genai.GenerativeModel(self.model_name)

            # Test the model with a simple request
            test_response = self.model.generate_content("Hello")
            logger.info("Gemini model initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing Gemini model: {e}")
            raise RuntimeError(f"Failed to initialize Gemini model: {e}")

    def generate_response(
        self,
        query: str,
        context_documents: List[Dict],
        conversation_history: Optional[List[Dict]] = None,
        is_conversational: bool = False
    ) -> Tuple[str, Dict]:
        """Generate response using retrieved context with Gemini"""

        # Format context documents (skip for conversational queries)
        context_text = "" if is_conversational else self._format_context(context_documents)
        # Generate SQL and fetch results once
        sql_query = generate_postgresql_query(query)
        sql_result = fire_sql(sql_query)
        # Build prompt
        prompt = self._build_prompt(
            query,
            context_text,
            conversation_history,
            is_conversational,
            sql_query,
            sql_result,
        )
        try:
            start_time = time.time()

            # Generate response with safety settings
            generation_config = genai.types.GenerationConfig(
                temperature=AppConfig.LLM_TEMPERATURE,
                top_p=AppConfig.LLM_TOP_P,
                max_output_tokens=AppConfig.LLM_MAX_TOKENS,
            )

            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            # Calculate generation time
            generation_time = time.time() - start_time

            # Extract response text
            if response and response.text:
                response_text = response.text.strip()
            else:
                response_text = "I apologize, but I couldn't generate a response at this time."

            # Prepare metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'model': self.model_name,
                'context_docs_used': len(context_documents),
                'generation_time_seconds': generation_time,
                'total_tokens_used': len(prompt.split()) + len(response_text.split()),
                'device': 'cloud',
                'api_calls': 1
            }

            # Add usage metadata if available
            if hasattr(response, 'usage_metadata'):
                metadata['prompt_tokens'] = response.usage_metadata.prompt_token_count
                metadata['completion_tokens'] = response.usage_metadata.candidates_token_count
                metadata['total_tokens'] = response.usage_metadata.total_token_count

            return response_text, metadata

        except Exception as e:
            logger.error(f"Error generating response with Gemini: {e}")
            return f"Error generating response: {str(e)}", {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _format_context(self, documents: List[Dict]) -> str:
        """Format retrieved documents into context string"""
        if not documents:
            return "No relevant context found."

        context_parts = []
        for i, doc in enumerate(documents[:AppConfig.CONTEXT_WINDOW_SIZE], 1):
            text = doc.get('text', '')
            source = doc.get('metadata', {}).get('source_file', 'Unknown')
            similarity = doc.get('similarity_score', 0)

            context_parts.append(
                f"[Document {i}] (Source: {source}, Similarity: {similarity:.3f})\n"
                f"{text[:1000]}{'...' if len(text) > 1000 else ''}\n"
            )

        return "\n".join(context_parts)

    def _build_prompt(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None,
        is_conversational: bool = False,
        sql_query: Optional[str] = "",
        sql_result: Optional[str] = "",
    ) -> str:
        """Build prompt for Gemini"""

        if is_conversational:
            # Simple conversational system message
            system_message = (
                "You are FloatChat, a friendly AI assistant specialized in oceanographic research. "
                "You're having a casual conversation with a user. Respond naturally and warmly to "
                "greetings, thanks, and other conversational messages. Keep responses brief and friendly. "
                "If asked technical questions, you can provide oceanographic expertise, but for simple "
                "conversational exchanges, just be a friendly assistant."
                "Give concise and clear responses."
            )
        else:
            # Technical system message for oceanographic context
            system_message = (
                "You are FloatChat, an advanced AI assistant specialized in oceanographic research. "
                "You help researchers, scientists, and students with questions about ocean data, "
                "ARGO floats, CTD measurements, biogeochemical processes, and marine science. "
                "Use the provided context to give accurate, helpful answers. If the context "
                "doesn't contain enough information, use your general knowledge but clearly "
                "indicate when you're drawing from general knowledge vs. the provided documents."
                "Give concise and clear responses."
                """provide the data "sql_result"/"RELEVANT SQL INFORMATION" in table format if possible."""
            )

        # Format conversation history
        history_text = ""
        if conversation_history:
            # Limit to last 5 exchanges to avoid token limits
            recent_history = conversation_history[-5:]
            for msg in recent_history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_text += f"{role.capitalize()}: {content}\n\n"

        # Build the complete prompt based on query type
        if is_conversational:
            prompt = f"""{system_message}

{history_text}USER: {query}

Please respond naturally and friendly to this message.

FLOATCHAT:"""
        else:
            prompt = f"""{system_message}

RELEVANT CONTEXT INFORMATION:
{context}

RELEVANT SQL INFORMATION:
{sql_result}

{history_text}USER QUERY: {query}
USER SQL QUERY: {sql_query}
USER SQL RESULT: {sql_result} (RELEVANT SQL INFORMATION)
provide the data "sql_result"/"RELEVANT SQL INFORMATION" in table format if possible.
Please provide a comprehensive, scientifically accurate answer based on the context provided above. Include specific references to the source documents when possible. If you need to use general knowledge beyond the provided context, please make that clear and concise.

ANSWER:"""

        return prompt

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_name": self.model_name,
            "device": "cloud",
            "api_key_configured": bool(self.api_key),
            "context_window": AppConfig.MAX_CONTEXT_LENGTH,
            "max_tokens": AppConfig.LLM_MAX_TOKENS,
            "status": "ready" if self.model else "not_initialized"
        }

    def clear_cache(self):
        """Clear any local cache (not applicable for API-based model)"""
        logger.info("Gemini service - no local cache to clear")

    def test_connection(self) -> bool:
        """Test the Gemini API connection"""
        try:
            response = self.model.generate_content("Hello! Please respond with 'Connection successful' if you can read this.")
            return "Connection successful" in response.text
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available Gemini models"""
        try:
            models = genai.list_models()
            return [model.name for model in models if 'gemini' in model.name]
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return [self.model_name]  # Return current model as fallback
