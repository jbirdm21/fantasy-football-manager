#!/bin/bash
# Start the Fantasy Football Manager server for development

# Exit on error
set -e

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python -m venv .venv
  echo "Installing dependencies..."
  .venv/bin/pip install -r requirements.txt
fi

# Activate virtual environment
source .venv/bin/activate

# Run the server
echo "Starting Fantasy Football Manager server..."
python scripts/run_server.py --frontend-url "http://localhost:3000"

# This script will only reach here if the server terminates
echo "Server stopped" 