"""FastAPI application for FloatChat ChatBot"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(
    title="FloatChat API",
    version="1.0.0",
    description="REST API for oceanographic data analysis chatbot and dashboard"
)

# CORS for React frontend - Must be added BEFORE routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Import and include routers
try:
    from api.routers import chatbot
    app.include_router(chatbot.router, prefix="/api/chat", tags=["ChatBot"])
    print("✓ ChatBot router loaded successfully")
except ImportError as e:
    print(f"Warning: Could not load chatbot router: {e}")

try:
    from api.routers import dashboard
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
    print("✓ Dashboard router loaded successfully")
except ImportError as e:
    print(f"Warning: Could not load dashboard router: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FloatChat API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "chatbot": "/api/chat",
            "dashboard": "/api/dashboard"
        },
        "status": "ready"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "services": ["chatbot", "dashboard"]}

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Starting FloatChat ChatBot API Server")
    print("API Documentation: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
