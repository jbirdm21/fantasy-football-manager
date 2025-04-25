FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY agent_system/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Set up environment variables
ENV PYTHONPATH=/app
ENV AGENT_LOG_LEVEL=INFO

# Create directory for agent outputs
RUN mkdir -p /app/agent_system/outputs /app/agent_system/outputs/logs

# Command to run when the container starts
# This will be overridden by docker-compose
CMD ["python", "-m", "agent_system.agent_runner", "--initialize", "--daemon"] 