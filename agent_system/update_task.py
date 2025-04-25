#!/usr/bin/env python3
"""
Script to update task status in the agent system.
"""
from agent_system.agents.models import TaskStatus
from agent_system.utils.persistence import get_task, save_task
import argparse
import sys
from pathlib import Path
import logging

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("update_task")


def update_task(task_id: str, status: str, message: str = None) -> bool:
    """
    Update a task's status.

    Args:
        task_id: The ID of the task to update
        status: The new status (READY, IN_PROGRESS, COMPLETED, etc.)
        message: Optional status message

    Returns:
        True if successful, False otherwise
    """
    # Get task
    task = get_task(task_id)
    if not task:
        logger.error(f"Task {task_id} not found")
        return False

    # Update status
    try:
        task.status = TaskStatus(status)
        if message:
            task.metadata = task.metadata or {}
            task.metadata["status_message"] = message

        # Save task
        save_task(task)
        logger.info(f"Task {task_id} updated: {status}")
        return True

    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Update task status")
    parser.add_argument("task_id", help="ID of the task to update")
    parser.add_argument("status", choices=[s.value for s in TaskStatus], help="New status")
    parser.add_argument("--message", help="Status message")

    args = parser.parse_args()

    success = update_task(args.task_id, args.status, args.message)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
