"""ChatBot API Router - Integrates RAG, LLM, and SQL services"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os
from datetime import datetime
import uuid

# Add paths for importing existing services
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
app_dir = os.path.dirname(api_dir)
backend_dir = os.path.dirname(app_dir)

sys.path.insert(0, backend_dir)
sys.path.insert(0, app_dir)
sys.path.insert(0, api_dir)

# Import data formatter first (always available)
try:
    from processors.data_formatter import DataFormatter
    formatter = DataFormatter()
    print("✓ Data formatter loaded")
except ImportError as e:
    print(f"✗ Could not import DataFormatter: {e}")
    # Create a minimal fallback formatter
    class DataFormatter:
        @staticmethod
        def format_for_recharts(raw_data, x_field, y_field):
            return [{"name": str(row.get(x_field)), "value": float(row.get(y_field))} 
                    for row in raw_data if row.get(y_field) not in ['NaN', None]]
    formatter = DataFormatter()

# Import existing services
EnhancedRAGService = None
OceanographicGeminiService = None

try:
    from app.services.rag_service import EnhancedRAGService
    print("✓ RAG service imported")
except ImportError as e:
    print(f"⚠ RAG service not available: {e}")

try:
    from app.services.llm_service import OceanographicGeminiService
    print("✓ LLM service imported")
except ImportError as e:
    print(f"⚠ LLM service not available: {e}")

try:
    from app.tools.sql_tool import generate_postgresql_query, fire_sql
    print("✓ SQL tool imported")
except ImportError as e:
    print(f"✗ SQL tool import failed: {e}")
    raise

router = APIRouter()

# Initialize services
rag_service = None
llm_service = None

try:
    if EnhancedRAGService:
        rag_service = EnhancedRAGService("oceanographic_data_v1")
        print("✓ RAG service initialized")
except Exception as e:
    print(f"⚠ RAG initialization warning: {e}")

try:
    if OceanographicGeminiService:
        llm_service = OceanographicGeminiService()
        print("✓ LLM service initialized")
except Exception as e:
    print(f"⚠ LLM initialization warning: {e}")

print("\n✓ ChatBot services ready:")
if rag_service:
    print("  → RAG Service: Ready")
if llm_service:
    print("  → LLM Service: Ready")
print("  → SQL Tool: Ready")
print("  → Data Formatter: Ready")
print()

# Conversation history storage (in-memory for now)
conversation_history = {}  # session_id -> list of messages

# Request/Response Models
class ChatQuery(BaseModel):
    query: str
    session_id: Optional[str] = None  # For conversation history

class ChatResponse(BaseModel):
    summary: str
    data: Optional[List[Dict]] = None
    hasVisualization: bool = False
    visualizationType: str = "line"
    metadata: Dict = {}
    session_id: Optional[str] = None

# Conversational patterns
SIMPLE_GREETINGS = [
    'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
    'thanks', 'thank you', 'bye', 'goodbye', 'see you'
]

CONVERSATIONAL_PATTERNS = [
    'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
    'thanks', 'thank you', 'bye', 'goodbye', 'see you', 'how are you',
    'what\'s your name', 'whats your name', 'what is your name',
    'who are you', 'your name', 'my name is', 'i am', 'i\'m',
    'what\'s my name', 'whats my name', 'do you remember me',
    'how about you', 'and you', 'tell me about yourself'
]

def is_simple_greeting(query: str) -> bool:
    """Check if query is just a simple greeting (return hardcoded response)"""
    q = query.lower().strip()
    # Check for exact matches or simple greetings without additional content
    return q in SIMPLE_GREETINGS or any(q == word for word in SIMPLE_GREETINGS)

def is_conversational_query(query: str) -> bool:
    """Check if query is conversational (no data needed, use conversational LLM mode)"""
    q = query.lower().strip()
    return any(q.startswith(word) for word in CONVERSATIONAL_PATTERNS) or q in CONVERSATIONAL_PATTERNS

def get_conversation_history(session_id: str) -> List[Dict]:
    """Get conversation history for a session"""
    return conversation_history.get(session_id, [])

def add_to_conversation_history(session_id: str, role: str, content: str):
    """Add a message to conversation history"""
    if session_id not in conversation_history:
        conversation_history[session_id] = []
    
    conversation_history[session_id].append({
        "role": role,
        "content": content,
        "timestamp": str(datetime.now())
    })
    
    # Keep only last 10 messages to prevent memory issues
    if len(conversation_history[session_id]) > 10:
        conversation_history[session_id] = conversation_history[session_id][-10:]

@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatQuery):
    """
    Process chat query using RAG + LLM + SQL
    
    Flow:
    1. Check if conversational (hi, thanks, etc.)
    2. If needs data: Generate SQL → Execute → Format
    3. Retrieve RAG context for better responses
    4. Generate LLM summary with context
    5. Return response with optional visualization
    """
    try:
        query = request.query.strip()
        print(f"\n📩 Query: {query}")
        
        # Handle session management
        session_id = request.session_id or str(uuid.uuid4())
        history = get_conversation_history(session_id)
        
        # Add user query to history
        add_to_conversation_history(session_id, "user", query)
        
        # Handle simple greetings (return hardcoded response)
        if is_simple_greeting(query):
            response = "Hello! I'm FloatChat, your oceanographic AI assistant. I can help you analyze ocean data, temperature trends, salinity profiles, and Argo float trajectories. What would you like to know?"
            add_to_conversation_history(session_id, "assistant", response)
            return ChatResponse(
                summary=response,
                hasVisualization=False,
                session_id=session_id
            )
        
        # Check if query is conversational (no data needed, use conversational LLM mode)
        if is_conversational_query(query):
            print("  → Conversational query, using conversational LLM mode")
            
            summary = ""
            if rag_service and llm_service:
                try:
                    # Use conversational mode - no RAG retrieval needed
                    response_tuple = llm_service.generate_response(
                        query, 
                        [],  # Empty context for conversational queries
                        conversation_history=history,
                        is_conversational=True
                    )
                    if isinstance(response_tuple, tuple):
                        summary = response_tuple[0]
                    else:
                        summary = str(response_tuple)
                    print(f"  → Generated conversational response")
                except Exception as e:
                    print(f"  ⚠ Conversational LLM error: {e}")
                    summary = "Hello! I'm FloatChat, your oceanographic AI assistant. How can I help you today?"
            else:
                summary = "Hello! I'm FloatChat, your oceanographic AI assistant. How can I help you today?"
            
            # Add assistant response to history
            add_to_conversation_history(session_id, "assistant", summary)
            
            print("  ✓ Response ready\n")
            return ChatResponse(
                summary=summary,
                hasVisualization=False,
                session_id=session_id,
                metadata={"query_type": "conversational", "rag_sources": 0}
            )
        
        # Check if query needs database data
        needs_data = any(word in query.lower() for word in 
                        ['temperature', 'salinity', 'float', 'data', 'show', 'trend', 
                         'profile', 'depth', 'anomaly', 'analysis', 'compare', 'plot',
                         'chart', 'graph', 'visualize', 'distribution', 'pattern'])
        
        if needs_data:
            print("  → Query needs database data")
            
            # Step 1: Get data from PostgreSQL
            try:
                sql = generate_postgresql_query(query)
                print(f"  → Generated SQL: {sql[:100]}...")
                raw_data = fire_sql(sql)
                print(f"  → Retrieved {len(raw_data) if raw_data else 0} rows from database")
            except Exception as e:
                print(f"  ✗ SQL error: {e}")
                raw_data = []
            
            # Step 2: Format data for Recharts visualization
            formatted_data = None
            if raw_data and len(raw_data) > 0:
                keys = list(raw_data[0].keys())
                if len(keys) >= 2:
                    # Auto-detect best fields for x and y axis
                    x_field = keys[0]
                    y_field = keys[1]
                    
                    # Prefer certain field names
                    for key in keys:
                        if key in ['month', 'date', 'time', 'juld', 'depth', 'pres']:
                            x_field = key
                        if key in ['temp', 'temperature', 'temp_adjusted', 'avg_temp', 'psal', 'salinity']:
                            y_field = key
                    
                    formatted_data = formatter.format_for_recharts(raw_data, x_field, y_field)
                    print(f"  → Formatted {len(formatted_data)} data points for visualization")
            
            # Step 3: Retrieve RAG context (before LLM so it can use context)
            rag_context = []
            if rag_service:
                try:
                    rag_context, stats = rag_service.retrieve(query, k=3, threshold=0.1)
                    print(f"  → RAG retrieved {len(rag_context)} relevant documents")
                except Exception as e:
                    print(f"  ⚠ RAG retrieval warning: {e}")
                    import traceback
                    print(f"  ⚠ Full traceback: {traceback.format_exc()}")
            
            # Step 4: Let LLM intelligently decide visualization type
            data_keys = list(raw_data[0].keys()) if raw_data and len(raw_data) > 0 else None
            viz_type = decide_visualization_type(query, data_keys)
            print(f"  → Visualization type: {viz_type}")
            
            # Step 5: Generate AI summary using LLM with RAG context
            summary = ""
            if llm_service:
                try:
                    # LLM service returns tuple (response_text, metadata)
                    response_tuple = llm_service.generate_response(query, rag_context, conversation_history=history, is_conversational=False)
                    if isinstance(response_tuple, tuple):
                        summary = response_tuple[0]  # Extract just the text
                    else:
                        summary = str(response_tuple)
                    print(f"  → LLM generated response ({len(summary)} chars)")
                except Exception as e:
                    print(f"  ⚠ LLM error: {e}, using fallback")
                    summary = generate_fallback_summary(query, raw_data)
            else:
                summary = generate_fallback_summary(query, raw_data)
            
            # Add assistant response to history
            add_to_conversation_history(session_id, "assistant", summary)
            
            print("  ✓ Response ready\n")
            
            return ChatResponse(
                summary=summary,
                data=formatted_data,
                hasVisualization=formatted_data is not None and len(formatted_data) > 0,
                visualizationType=viz_type,
                session_id=session_id,
                metadata={
                    "sql_query": sql if 'sql' in locals() else "",
                    "row_count": len(raw_data) if raw_data else 0,
                    "rag_sources": len(rag_context),
                    "formatted_points": len(formatted_data) if formatted_data else 0
                }
            )
        else:
            # General oceanographic question - use RAG + LLM only
            print("  → General question, using RAG + LLM")
            
            summary = ""
            rag_context = []
            
            if rag_service and llm_service:
                try:
                    rag_context, _ = rag_service.retrieve(query, k=3)
                    print(f"  → RAG retrieved {len(rag_context)} relevant documents")
                    # LLM service returns tuple (response_text, metadata)
                    response_tuple = llm_service.generate_response(query, rag_context, conversation_history=history, is_conversational=False)
                    if isinstance(response_tuple, tuple):
                        summary = response_tuple[0]  # Extract just the text
                    else:
                        summary = str(response_tuple)
                    print(f"  → Generated contextual response")
                except Exception as e:
                    print(f"  ⚠ Error: {e}")
                    import traceback
                    print(f"  ⚠ Full traceback: {traceback.format_exc()}")
                    summary = get_default_response()
            else:
                summary = get_default_response()
            
            # Add assistant response to history
            add_to_conversation_history(session_id, "assistant", summary)
            
            print("  ✓ Response ready\n")
            print("raw_llm_response: ", summary)
            
            return ChatResponse(
                summary=summary,
                hasVisualization=False,
                session_id=session_id,
                metadata={"rag_sources": len(rag_context)}
            )
            
    except Exception as e:
        print(f"  ✗ Error in chat_query: {e}\n")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

def generate_fallback_summary(query: str, data: List[Dict]) -> str:
    """Generate fallback response when LLM is unavailable"""
    if not data:
        return "I couldn't find data matching your query in the database. Try asking about temperature trends, salinity profiles, or Argo float trajectories in specific ocean regions like the Arabian Sea or Bay of Bengal."
    
    row_count = len(data)
    query_lower = query.lower()
    
    if "temperature" in query_lower:
        return f"Based on the oceanographic database, I analyzed {row_count} temperature measurements. The data shows thermal patterns typical of oceanic environments, with variations by depth and geographic location. Temperature ranges are influenced by solar radiation, ocean currents, and mixing processes. The visualization shows these temperature trends over the queried parameters."
    
    elif "salinity" in query_lower:
        return f"Analysis of {row_count} salinity measurements from the Argo float database. Salinity patterns vary significantly by ocean region and depth, influenced by factors such as freshwater input from rivers, precipitation, evaporation rates, and ocean circulation. The Arabian Sea typically shows higher salinity (35-37 PSU) due to high evaporation, while the Bay of Bengal has lower values (33-35 PSU) due to river discharge. The chart visualizes this salinity distribution."
    
    elif "float" in query_lower or "trajectory" in query_lower:
        return f"Retrieved {row_count} Argo float position records. Argo floats are autonomous profiling instruments that drift with ocean currents, diving to depths of up to 2000 meters and surfacing every 10 days to transmit data. The trajectory patterns reveal ocean circulation dynamics, including major currents like the Southwest Monsoon Current and Northeast Monsoon Current in the Indian Ocean."
    
    elif "depth" in query_lower or "profile" in query_lower:
        return f"Analyzed {row_count} depth profile measurements. Ocean properties vary dramatically with depth due to factors like light penetration, temperature gradients (thermocline), and pressure. Surface layers are warmer and more variable, while deep ocean waters are cold (2-4°C) and stable. The profile shows this vertical structure."
    
    else:
        return f"Retrieved {row_count} data points from the oceanographic database based on your query. The data includes measurements from Argo floats deployed across Indian Ocean regions. Each data point represents carefully calibrated observations of ocean properties. The visualization displays the analyzed patterns and trends from this dataset."

def decide_visualization_type(query: str, data_keys: list = None) -> str:
    """
    Intelligently decide visualization type using LLM or fallback logic
    
    Args:
        query: User's query
        data_keys: Available data fields (optional)
    
    Returns:
        Chart type: 'line', 'bar', or 'area'
    """
    if llm_service:
        try:
            data_info = f"\nData fields available: {', '.join(data_keys)}" if data_keys else ""
            
            viz_prompt = f"""You are a data visualization expert. Based on this oceanographic query, suggest the BEST chart type.

Query: "{query}"{data_info}

Chart types and when to use them:
- "line": Time series, trends over time, continuous measurements, temporal patterns
- "bar": Comparisons between categories, discrete groups, vs/versus analysis, regional comparisons
- "area": Distributions, cumulative values, depth profiles, volume/magnitude representation

IMPORTANT: Respond with ONLY ONE WORD - either "line", "bar", or "area".
No explanation, just the chart type."""
            
            viz_response = llm_service.generate_response(viz_prompt, [])
            viz_suggestion = viz_response[0].strip().lower() if isinstance(viz_response, tuple) else str(viz_response).strip().lower()
            
            # Extract the chart type
            if "line" in viz_suggestion:
                return "line"
            elif "bar" in viz_suggestion:
                return "bar"
            elif "area" in viz_suggestion:
                return "area"
        except Exception as e:
            print(f"  ⚠ LLM viz decision error: {e}")
    
    # Fallback to keyword-based logic
    query_lower = query.lower()
    if any(word in query_lower for word in ["compare", "vs", "versus", "difference", "between"]):
        return "bar"
    elif any(word in query_lower for word in ["distribution", "spread", "range", "depth profile"]):
        return "area"
    else:
        return "line"  # Default for trends

def get_default_response() -> str:
    """Default response when no services are available"""
    return """I'm FloatChat, an AI assistant for oceanographic data analysis. I can help you with:

🌊 **Temperature Analysis**: Trends, profiles, and thermal patterns
💧 **Salinity Data**: Distribution, depth profiles, and regional variations  
🎈 **Argo Floats**: Trajectories, positions, and deployment information
📊 **Data Visualization**: Interactive charts and graphs
🔍 **Anomaly Detection**: Unusual patterns and events

Try asking questions like:
- "Show me temperature trends in the Arabian Sea"
- "Analyze salinity by depth"
- "Track Argo float trajectories"
- "What are the latest temperature anomalies?"

What would you like to explore?"""

@router.get("/test")
async def test_services():
    """Test if all backend services are working"""
    return {
        "rag_service": "available" if rag_service else "unavailable",
        "llm_service": "available" if llm_service else "unavailable",
        "sql_tool": "available",
        "data_formatter": "available",
        "status": "operational"
    }

@router.get("/health")
async def health_check():
    """Health check for chatbot service"""
    return {
        "service": "chatbot",
        "status": "healthy",
        "components": {
            "rag": rag_service is not None,
            "llm": llm_service is not None,
            "sql": True,
            "formatter": True
        }
    }

@router.post("/query-simple")
async def chat_query_simple(request: ChatQuery):
    """Simplified test endpoint without LLM"""
    try:
        query = request.query.strip()
        
        # Just use SQL and formatter, no LLM
        sql = generate_postgresql_query(query)
        raw_data = fire_sql(sql)
        
        formatted_data = None
        if raw_data and len(raw_data) > 0:
            keys = list(raw_data[0].keys())
            if len(keys) >= 2:
                formatted_data = formatter.format_for_recharts(raw_data, keys[0], keys[1])
        
        summary = f"Retrieved {len(raw_data) if raw_data else 0} rows from database."
        
        return ChatResponse(
            summary=summary,
            data=formatted_data,
            hasVisualization=formatted_data is not None,
            visualizationType="line",
            metadata={"row_count": len(raw_data) if raw_data else 0}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
