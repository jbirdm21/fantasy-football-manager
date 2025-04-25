from agent_system.agents.pr_workflow import run_quality_check
from agent_system.agents.models import TaskStatus, Task
from agent_system.utils.persistence import save_task
import os
import sys
from pathlib import Path
import subprocess
from typing import Dict, Any, List, Optional
import logging

# Add parent directory to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))


logger = logging.getLogger(__name__)


def update_task_status(task_id: str, status: TaskStatus, message: str = None) -> bool:
    """Update a task's status.

    Args:
        task_id: The ID of the task to update
        status: The new status
        message: Optional status message

    Returns:
        True if successful, False otherwise
    """
    # Implementation would go here
    return True


def check_code_quality_before_pr(task: Task, changed_files: List[str] = None) -> bool:
    """
    Run code quality checks before submitting a PR for a task

    Args:
        task: The task object
        changed_files: List of changed files, or None to detect automatically

    Returns:
        True if quality checks pass, False otherwise
    """
    try:
        if not changed_files:
            # Try to detect changed files from git
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=True
            )
            changed_files = [file.strip() for file in result.stdout.split("\n") if file.strip()]

        # Run quality checks
        passed = run_quality_check(changed_files)

        if passed:
            update_task_status(
                task.id,
                TaskStatus.PR_READY,
                "Code quality checks passed. Ready for PR submission."
            )
            return True
        else:
            update_task_status(
                task.id,
                TaskStatus.NEEDS_REVISION,
                "Code quality checks failed. Please fix issues before submitting PR."
            )
            return False

    except Exception as e:
        logger.error(f"Error during code quality check: {e}")
        update_task_status(
            task.id,
            TaskStatus.ERROR,
            f"Error during code quality check: {str(e)}"
        )
        return False


def submit_pr_for_task(task: Task, branch_name: str, pr_title: str = None, pr_body: str = None) -> Optional[str]:
    """
    Submit a PR for a task after ensuring code quality

    Args:
        task: The task object
        branch_name: Branch name to create PR from
        pr_title: Optional PR title (defaults to task title)
        pr_body: Optional PR body

    Returns:
        PR URL if successful, None otherwise
    """
    # First run code quality checks
    if not check_code_quality_before_pr(task):
        return None

    # Set defaults
    if not pr_title:
        pr_title = f"[Task {task.id}] {task.title}"

    if not pr_body:
        pr_body = f"Completing task {task.id}: {task.title}\n\n"
        if task.description:
            pr_body += f"{task.description}\n\n"
        pr_body += "This PR passed automated code quality checks."

    # Submit PR (implementation would depend on your GitHub interface)
    try:
        # Example implementation:
        result = subprocess.run(
            [
                "gh", "pr", "create",
                "--title", pr_title,
                "--body", pr_body,
                "--base", "main",
                "--head", branch_name
            ],
            capture_output=True,
            text=True,
            check=True
        )

        # Extract PR URL from result
        pr_url = result.stdout.strip()

        # Update task with PR URL
        task.artifacts = task.artifacts or []
        task.artifacts.append(pr_url)
        save_task(task)

        update_task_status(
            task.id,
            TaskStatus.PR_SUBMITTED,
            f"PR submitted: {pr_url}"
        )

        return pr_url

    except Exception as e:
        logger.error(f"Error submitting PR: {e}")
        update_task_status(
            task.id,
            TaskStatus.ERROR,
            f"Error submitting PR: {str(e)}"
        )
        return None
