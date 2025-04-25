#!/usr/bin/env python3
"""
Script to run the Fantasy Football Manager server continuously
with proper frontend connection settings.
"""
import os
import sys
import argparse
import subprocess
import signal
import logging
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(parent_dir / "server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("server_runner")

def run_server(host="0.0.0.0", port=8000, frontend_url=None, reload=True):
    """
    Run the Fantasy Football Manager server.
    
    Args:
        host: Host to bind to
        port: Port to run on
        frontend_url: URL of the frontend for CORS configuration
        reload: Whether to enable auto-reload
    """
    # Set environment variables for frontend URL if provided
    if frontend_url:
        os.environ["FRONTEND_URL"] = frontend_url
        logger.info(f"Setting CORS for frontend URL: {frontend_url}")
    
    # Command to run the server
    cmd = [
        "uvicorn", 
        "app.main:app", 
        "--host", host, 
        "--port", str(port)
    ]
    
    if reload:
        cmd.append("--reload")
    
    try:
        logger.info(f"Starting server on {host}:{port}")
        
        # Run the server
        process = subprocess.Popen(cmd)
        
        # Handle graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Shutting down server...")
            process.terminate()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Wait for the process to complete
        process.wait()
        
    except Exception as e:
        logger.error(f"Error running server: {e}")
        return 1
    
    return 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run the Fantasy Football Manager server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on")
    parser.add_argument("--frontend-url", help="URL of the frontend for CORS configuration")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    
    args = parser.parse_args()
    
    return run_server(
        host=args.host,
        port=args.port,
        frontend_url=args.frontend_url,
        reload=not args.no_reload
    )

if __name__ == "__main__":
    sys.exit(main()) 