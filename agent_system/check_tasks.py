from rich.table import Table
from rich.console import Console
from pathlib import Path
import json
import sqlite3
import sys
import os
import logging

logger = logging.getLogger(__name__)
#!/usr/bin/env python
"""Script to check task status and PR URLs directly from the database."""

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Set up environment
os.environ["PYTHONPATH"] = str(parent_dir)

# Connect to database
db_path = Path(__file__).parent / "outputs" / "agent_system.db"
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

# Setup console
console = Console()


def get_all_tasks():
    """Get all tasks from the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks ORDER BY task_id")
    return cursor.fetchall()


def get_task(task_id):
    """Get a specific task by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
    return cursor.fetchone()


def check_task_prs(tasks=None, limit=5):
    """Check if tasks have PRs and display the results.

    Args:
        tasks: List of tasks to check, or None to get all tasks
        limit: Maximum number of tasks to display if tasks is None
    """
    if tasks is None:
        tasks = get_all_tasks()
        if limit > 0:
            tasks = tasks[:limit]

    # Create table for display
    table = Table(title="Task Status and PR Check")
    table.add_column("Task ID", style="dim")
    table.add_column("Title", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Has PR?", style="blue")
    table.add_column("PR URL", style="magenta")

    for task in tasks:
        # Parse artifacts JSON to check for PRs
        artifacts = []
        if task['artifacts']:
            try:
                artifacts = json.loads(task['artifacts'])
            except BaseException:
                artifacts = [task['artifacts']]

        # Check if any artifact is a PR URL
        has_pr = "✓" if any("github.com" in str(a) and "/pull/" in str(a) for a in artifacts) else "✗"

        # Get PR URLs
        pr_urls = [a for a in artifacts if "github.com" in str(a) and "/pull/" in str(a)]

        # Format PR URLs for display (truncate if too long)
        pr_display = ""
        if pr_urls:
            pr_display = pr_urls[0]
            if len(pr_urls) > 1:
                pr_display += f" (+{len(pr_urls) - 1} more)"

        # Add row to table
        table.add_row(
            task['task_id'][:8] + "...",
            task['title'],
            task['status'],
            f"[green]{has_pr}[/green]" if has_pr == "✓" else f"[red]{has_pr}[/red]",
            pr_display
        )

    console.print(table)


def main():
    """Main function."""
    # Get tasks with specified IDs
    task_ids = [
        "task-039c1290-a4bb-40cb-98b0-4a5ca2d11ec7",  # Secrets management
        "task-04a530c6-d265-4ad0-a510-1e5df74c62f1",  # Draft analytics dashboard
        "task-086dee3f-1968-4b9f-8e99-be873ea9e957",  # OAuth flow
        "task-123965ce-0c5a-4219-926c-ae8e6e289637",  # FAAB bid suggestions
        "task-184684eb-012f-466f-8b0d-24632110182a",  # Authentication flow
    ]

    tasks = [get_task(task_id) for task_id in task_ids]
    tasks = [t for t in tasks if t is not None]

    console.print(f"[bold]Checking {len(tasks)} specific tasks:[/bold]")
    check_task_prs(tasks)

    console.print("\n[bold]First 5 tasks in database:[/bold]")
    check_task_prs(limit=5)


if __name__ == "__main__":
    main()
