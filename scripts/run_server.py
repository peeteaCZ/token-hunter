"""
Start the Token Hunter web server.

Usage (from D:\\token_hunter\\):
    python scripts/run_server.py

Then open:  http://localhost:8000
"""

from __future__ import annotations

import sys
import os

# Python 3.10 compatibility: X | Y union type hints require __future__.annotations

# Ensure project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn

if __name__ == "__main__":
    print("Token Hunter starting...")
    print("  Open: http://localhost:8000")
    print("  API:  http://localhost:8000/api/v1/radar")
    print("  Stop: Ctrl+C\n")
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["."],
        log_level="info",
    )
