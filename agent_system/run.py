from pathlib import Path
import subprocess
import argparse
import sys
import os
import logging

logger = logging.getLogger(__name__)
#!/usr/bin/env python
"""Script to run the agent system locally without Docker."""

# Get the root directory
ROOT_DIR = Path(__file__).parent.parent
AGENT_SYSTEM_DIR = ROOT_DIR / "agent_system"


def check_requirements():
    """Check if required packages are installed."""
    try:
        import openai
        import rich
        import pydantic
        import yaml
        import dotenv
        # If we get here, required packages are installed
        return True
    except ImportError as e:
        logger.info(f"Missing required package: {e}")
        install = input("Install required packages? (y/n): ")
        if install.lower() == "y":
            subprocess.run([sys.executable, "-m", "pip", "install", "-r",
                           str(AGENT_SYSTEM_DIR / "requirements.txt")])
            return True
        return False


def setup_env():
    """Setup environment variables from .env file."""
    env_path = AGENT_SYSTEM_DIR / ".env"

    if not env_path.exists():
        # Create sample .env file
        logger.info("Creating sample .env file...")
        with open(env_path, "w") as f:
            f.write("""# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=your_username/fantasy-football-manager

# Redis Configuration (for agent state persistence)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Notification Webhooks (optional)
SLACK_WEBHOOK_URL=your_slack_webhook_url
DISCORD_WEBHOOK_URL=your_discord_webhook_url

# Agent System Configuration
AGENT_LOG_LEVEL=INFO
MAX_CONCURRENT_TASKS=3
TASK_TIMEOUT_HOURS=24
""")
        logger.info(f"Please edit {env_path} to add your API keys")
        return False

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(env_path)

    # Check if essential environment variables are set
    if not os.environ.get("OPENAI_API_KEY"):
        logger.info("OPENAI_API_KEY is not set in .env file")
        return False

    return True


def run_agent_system(initialize=False, agent=None, task=None, daemon=False):
    """Run the agent system.

    Args:
        initialize: Whether to initialize the agent system.
        agent: ID of a specific agent to run.
        task: ID of a specific task to run.
        daemon: Whether to run in daemon mode.
    """
    # Set PYTHONPATH to include the root directory
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)

    # Build command
    cmd = [sys.executable, "-m", "agent_system.agent_runner"]

    if initialize:
        cmd.append("--initialize")
    if agent:
        cmd.extend(["--agent", agent])
    if task:
        cmd.extend(["--task", task])
    if daemon:
        cmd.append("--daemon")

    # Run the command
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        logger.info("\nStopped by user")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run the agent system locally")
    parser.add_argument("--initialize", action="store_true",
                        help="Initialize agents and tasks")
    parser.add_argument("--agent", type=str,
                        help="Run a specific agent by ID")
    parser.add_argument("--task", type=str,
                        help="Run a specific task by ID")
    parser.add_argument("--daemon", action="store_true",
                        help="Run in daemon mode (continuous operation)")
    parser.add_argument("--setup", action="store_true",
                        help="Set up environment variables")

    args = parser.parse_args()

    # If setup requested, just set up environment and exit
    if args.setup:
        if setup_env():
            logger.info("Environment setup complete")
        return

    # Check requirements
    if not check_requirements():
        logger.info("Required packages are missing. Please install them first.")
        return

    # Setup environment if not already done
    if not setup_env():
        logger.info("Environment setup failed. Please run with --setup to configure.")
        return

    # Run the agent system
    run_agent_system(
        initialize=args.initialize,
        agent=args.agent,
        task=args.task,
        daemon=args.daemon
    )


if __name__ == "__main__":
    main()
