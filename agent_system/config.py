"""Configuration module for the agent system."""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GitHub Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "username/fantasy-football-manager")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Webhook Configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Agent System Configuration
AGENT_LOG_LEVEL = os.getenv("AGENT_LOG_LEVEL", "INFO")
MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "3"))
TASK_TIMEOUT_HOURS = int(os.getenv("TASK_TIMEOUT_HOURS", "24"))

# LLM Model Configuration
DEFAULT_MODEL = "gpt-4-1106-preview"
FAST_MODEL = "gpt-3.5-turbo-1106"

# Agent System Paths
PROJECT_ROOT = Path(__file__).parent.parent
AGENT_SYSTEM_DIR = PROJECT_ROOT / "agent_system"
TASK_DEFINITIONS_DIR = AGENT_SYSTEM_DIR / "tasks" / "definitions"
AGENT_OUTPUTS_DIR = AGENT_SYSTEM_DIR / "outputs"

# Create directories if they don't exist
AGENT_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# System Prompts
SYSTEM_PROMPT_TEMPLATE = """
You are {agent_name}, a specialized AI agent working on the Ultimate Personal Fantasy Football Manager project.
Your role is {agent_role} and your main goal is {agent_goal}.

The project has the following key characteristics:
- Modern Python stack (≥ 3.11) with FastAPI backend
- PostgreSQL database with Timescale extension
- Next.js (React 18) front-end with shadcn/ui
- Dagster for ETL & scheduled scrapes

When reasoning about tasks, always follow this sequence:
1. Clarify Intent – restate the acceptance criteria
2. Context Scan – list all code/files/docs that might be touched
3. Plan – ordered checklist; estimate effort
4. Execute – implement the solution
5. Self-Test – validate your changes work
6. Reflect – note edge-cases missed & open follow-ups
7. Commit & PR – prepare changes for review

Always build for maintainability and reusability. Comment complex logic but not obvious code.
""" 