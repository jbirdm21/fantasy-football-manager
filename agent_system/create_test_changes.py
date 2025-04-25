from pathlib import Path
import argparse
import sys
import os
from agent_system.utils.persistence import get_task, save_task
from agent_system.utils.github_integration import commit_agent_changes
from agent_system.agents.models import TaskStatus
import logging

logger = logging.getLogger(__name__)
#!/usr/bin/env python
"""Script to test file changes and PR creation for a specific task."""

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Set up environment
os.environ["PYTHONPATH"] = str(parent_dir)


def create_test_file_for_task(task_id):
    """Create a test file for a specific task and submit a PR.

    Args:
        task_id: ID of the task to create a test file for
    """
    # Get the task
    task = get_task(task_id)
    if not task:
        logger.info(f"Task {task_id} not found")
        return

    logger.info(f"Creating test file for task: {task.title}")

    # Create a test file in the appropriate directory based on task title
    title_lower = task.title.lower()
    file_path = ""
    file_content = ""

    if any(keyword in title_lower for keyword in ["auth", "secret", "oauth", "login"]):
        # Auth-related task
        file_path = "backend/auth/test_file.py"
        file_content = f"""
# Test file for task: {task.title}
# Task ID: {task.task_id}

def get_auth_config():
    \"\"\"
    Returns authentication configuration.

    This is a test function created for task: {task.title}
    \"\"\"
    return {{
        "auth_enabled": True,
        "oauth_providers": ["google", "github"],
        "jwt_expiration": 3600,
        "refresh_token_expiration": 86400
    }}
"""
    elif any(keyword in title_lower for keyword in ["dashboard", "analytics", "chart", "visualization"]):
        # Dashboard/analytics task
        file_path = "frontend/components/dashboard/TestComponent.jsx"
        file_content = f"""
import React from 'react';

/**
 * Dashboard test component for task: {task.title}
 * Task ID: {task.task_id}
 */
export const TestDashboardComponent = () => {{
  return (
    <div className="dashboard-container">
      <h2>Dashboard Test</h2>
      <p>This component was created for task: {task.title}</p>
      <div className="metrics-panel">
        <div className="metric">
          <h3>Total Points</h3>
          <p className="value">128.5</p>
        </div>
        <div className="metric">
          <h3>Win Probability</h3>
          <p className="value">68%</p>
        </div>
      </div>
    </div>
  );
}};
"""
    elif "faab" in title_lower or "bid" in title_lower:
        # FAAB bid suggestions task
        file_path = "backend/analysis/faab_suggestions.py"
        file_content = f"""
# FAAB bid suggestions implementation for task: {task.title}
# Task ID: {task.task_id}

def calculate_faab_bid(player_stats, league_settings, team_needs):
    \"\"\"
    Calculate recommended FAAB bid amount.

    Args:
        player_stats: Dictionary containing player statistics
        league_settings: Dictionary with league settings
        team_needs: Dictionary representing team needs

    Returns:
        Tuple of (min_bid, recommended_bid, max_bid)
    \"\"\"
    # This is a simplified implementation for task: {task.title}
    base_value = player_stats.get("projected_points", 0) * 1.5
    position_scarcity = {{"QB": 0.8, "RB": 1.2, "WR": 1.0, "TE": 1.3, "K": 0.5, "DEF": 0.6}}

    # Apply position scarcity
    position = player_stats.get("position", "RB")
    scarcity_factor = position_scarcity.get(position, 1.0)

    # Apply team needs factor
    need_factor = team_needs.get(position, 0.5) * 1.5

    # Calculate bid ranges
    recommended_bid = base_value * scarcity_factor * need_factor
    min_bid = max(1, int(recommended_bid * 0.7))
    max_bid = int(recommended_bid * 1.3)

    return (min_bid, int(recommended_bid), max_bid)
"""
    else:
        # Default file for other tasks
        file_path = f"docs/tasks/{task.task_id}.md"
        file_content = f"""
# {task.title}

## Description
{task.description}

## Implementation Notes
This is a test file created to verify the PR creation system for task: {task.title}.

## Status
- Task ID: {task.task_id}
- Status: {task.status.value}
- Assigned to: {task.assigned_agent_id}
"""

    # Dictionary of file changes to commit
    file_changes = {
        file_path: file_content
    }

    # Commit the changes
    try:
        pr_url = commit_agent_changes(
            agent_id=task.assigned_agent_id,
            file_changes=file_changes,
            commit_message=f"Test change for task: {task.title}",
            pr_description=f"This PR adds test changes for task {task.task_id}: {task.title}\n\nThis is a test PR to verify GitHub integration."
        )

        logger.info(f"Successfully created PR: {pr_url}")

        # Update task with PR URL
        if hasattr(task, 'artifacts') and task.artifacts:
            task.artifacts.append(pr_url)
        else:
            task.artifacts = [pr_url]

        # Update task status
        task.status = TaskStatus.COMPLETED

        # Save task
        save_task(task)
        logger.info(f"Updated task {task.task_id} with PR URL and set status to COMPLETED")

        return True

    except Exception as e:
        logger.info(f"Error creating PR: {str(e)}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test file changes and PR creation for a task")
    parser.add_argument(
        "task_id",
        help="ID of the task to create test file for"
    )

    args = parser.parse_args()
    create_test_file_for_task(args.task_id)


if __name__ == "__main__":
    main()
