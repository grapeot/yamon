#!/usr/bin/env python3
"""Command-line interface for Yamon"""

import argparse
import sys
import uvicorn
from pathlib import Path


def main():
    """Main entry point for yamon command"""
    parser = argparse.ArgumentParser(
        description="Yamon - Visually pleasing, deep system monitoring for macOS"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development mode)",
    )
    
    args = parser.parse_args()
    
    # Import app after parsing args
    from yamon.main import app
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

