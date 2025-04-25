#!/usr/bin/env python
"""Test script to verify agents can create GitHub PRs."""
from agent_system.config import GITHUB_TOKEN, GITHUB_REPO
from agent_system.utils.github_integration import commit_agent_changes
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("github_pr_test")

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Import required modules


def test_github_pr():
    """Test function to verify GitHub PR creation."""
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN not found in environment variables.")
        logger.error("PRs cannot be created without a valid GitHub token.")
        return False

    logger.info(f"Testing PR creation for repository: {GITHUB_REPO}")

    # Create a test change to README.md
    test_file_path = "docs/agent_pr_test.md"
    test_content = f"""# Agent PR Test

This file was created by the agent system to verify GitHub PR functionality.

- Repository: {GITHUB_REPO}
- Timestamp: {__import__('datetime').datetime.now().isoformat()}
"""

    try:
        # Create a PR with the test change
        pr_url = commit_agent_changes(
            agent_id="test-agent",
            file_changes={test_file_path: test_content},
            commit_message="Test PR for agent system verification",
            pr_description="This PR was automatically created to test the agent system's ability to create PRs."
        )

        logger.info(f"✅ Successfully created test PR: {pr_url}")
        logger.info("Agents are properly configured to create PRs.")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create test PR: {str(e)}")
        logger.error("Agents will not be able to create PRs until this issue is resolved.")
        return False


if __name__ == "__main__":
    success = test_github_pr()
    sys.exit(0 if success else 1)
