"""
Quick start script for FloatChat ChatBot API
Run this from Backend/ directory: python run_chatbot_api.py
"""
import os
import sys

if __name__ == "__main__":
    # Ensure we're in the right directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)

    # Add to path
    sys.path.insert(0, current_dir)

    print("=" * 70)
    print("🌊 FloatChat API Server")
    print("=" * 70)
    print()
    print("Starting services...")
    print()

    # Import and run
    try:
        import uvicorn
        
        # Change to api directory
        api_dir = os.path.join(current_dir, 'app', 'api')
        os.chdir(api_dir)
        sys.path.insert(0, api_dir)
        
        print("✓ Server ready")
        print()
        print("📡 API Endpoints:")
        print("   • Documentation: http://localhost:8000/docs")
        print("   • Chat Query:    http://localhost:8000/api/chat/query")
        print("   • Service Test:  http://localhost:8000/api/chat/test")
        print("   • Dashboard:     http://localhost:8000/api/dashboard/metrics")
        print("   • Floats Data:   http://localhost:8000/api/dashboard/floats")
        print()
        print("🔗 Connect your React frontend to: http://localhost:8000")
        print()
        print("=" * 70)
        print()
        
        # Run server (reload=True works on Windows now)
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
        
    except ImportError:
        print("✗ FastAPI not installed!")
        print()
        print("Install with: pip install fastapi uvicorn[standard] pydantic")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        sys.exit(0)
