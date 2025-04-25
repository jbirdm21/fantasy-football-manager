#!/usr/bin/env python
"""Script to monitor task progress and generate reports."""
from agent_system.agents.models import TaskStatus, Task
from agent_system.utils.persistence import get_all_tasks
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List, Any, Optional
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("task_monitor")
console = Console()


def monitor_tasks() -> Dict[str, Any]:
    """Monitor task progress and return statistics.

    Returns:
        Dictionary with task statistics
    """
    tasks = get_all_tasks()

    # Calculate statistics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
    in_progress_tasks = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
    pending_tasks = len([t for t in tasks if t.status == TaskStatus.PENDING])
    failed_tasks = len([t for t in tasks if t.status == TaskStatus.FAILED])
    blocked_tasks = len([t for t in tasks if t.status == TaskStatus.BLOCKED])

    # Calculate completion percentage
    completion_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

    # Calculate stalled tasks (in progress but not updated in last 2 hours)
    stalled_threshold = datetime.now() - timedelta(hours=2)
    stalled_tasks = [
        t for t in tasks
        if t.status == TaskStatus.IN_PROGRESS and t.updated_at < stalled_threshold
    ]

    # Check for tasks without file changes (no PR)
    tasks_without_pr = [
        t for t in tasks
        if t.status == TaskStatus.COMPLETED and (not hasattr(t, 'artifacts') or not t.artifacts)
    ]

    # Return statistics
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "pending_tasks": pending_tasks,
        "failed_tasks": failed_tasks,
        "blocked_tasks": blocked_tasks,
        "completion_percentage": completion_percentage,
        "stalled_tasks": len(stalled_tasks),
        "tasks_without_pr": len(tasks_without_pr),
        "stalled_task_list": stalled_tasks,
        "failed_task_list": [t for t in tasks if t.status == TaskStatus.FAILED],
        "blocked_task_list": [t for t in tasks if t.status == TaskStatus.BLOCKED],
        "timestamp": datetime.now().isoformat()
    }


def display_tasks(task_list: List[Task], title: str = "Tasks") -> None:
    """Display a list of tasks in a formatted table.

    Args:
        task_list: List of tasks to display
        title: Title for the table
    """
    if not task_list:
        console.print(f"No {title.lower()} found.", style="yellow")
        return

    table = Table(title=title)
    table.add_column("ID", style="dim")
    table.add_column("Title", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Agent", style="magenta")
    table.add_column("Updated", style="blue")

    for task in task_list:
        task_id = task.task_id[:8] + "..."  # Truncate ID for display

        # Format update time as a relative time
        updated_at = task.updated_at
        now = datetime.now()
        time_diff = now - updated_at

        if time_diff.days > 0:
            updated_str = f"{time_diff.days}d ago"
        elif time_diff.seconds > 3600:
            updated_str = f"{time_diff.seconds // 3600}h ago"
        else:
            updated_str = f"{time_diff.seconds // 60}m ago"

        # Set status color
        status_style = {
            TaskStatus.COMPLETED: "green",
            TaskStatus.IN_PROGRESS: "blue",
            TaskStatus.PENDING: "yellow",
            TaskStatus.FAILED: "red",
            TaskStatus.BLOCKED: "orange"
        }.get(task.status, "white")

        table.add_row(
            task_id,
            task.title,
            f"[{status_style}]{task.status.value}[/{status_style}]",
            task.assigned_agent_id,
            updated_str
        )

    console.print(table)


def generate_report(stats: Dict[str, Any], detailed: bool = False) -> None:
    """Generate a report of task statistics.

    Args:
        stats: Task statistics dictionary
        detailed: Whether to include detailed task lists
    """
    console.print(f"\n[bold blue]Task Monitor Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold blue]\n")

    # Create summary table
    summary_table = Table(title="Task Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Total Tasks", str(stats["total_tasks"]))
    summary_table.add_row("Completed", f"{stats['completed_tasks']} ({stats['completion_percentage']:.1f}%)")
    summary_table.add_row("In Progress", str(stats["in_progress_tasks"]))
    summary_table.add_row("Pending", str(stats["pending_tasks"]))
    summary_table.add_row("Failed", str(stats["failed_tasks"]))
    summary_table.add_row("Blocked", str(stats["blocked_tasks"]))
    summary_table.add_row("Stalled", str(stats["stalled_tasks"]))
    summary_table.add_row("Without PRs", str(stats["tasks_without_pr"]))

    console.print(summary_table)

    # Show detailed lists if requested
    if detailed:
        if stats["stalled_tasks"] > 0:
            console.print("\n[bold red]Stalled Tasks[/bold red]")
            display_tasks(stats["stalled_task_list"], "Stalled Tasks")

        if stats["failed_tasks"] > 0:
            console.print("\n[bold red]Failed Tasks[/bold red]")
            display_tasks(stats["failed_task_list"], "Failed Tasks")

        if stats["blocked_tasks"] > 0:
            console.print("\n[bold orange]Blocked Tasks[/bold orange]")
            display_tasks(stats["blocked_task_list"], "Blocked Tasks")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Monitor task progress")
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed task lists"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for report"
    )

    args = parser.parse_args()

    try:
        # Get task statistics
        stats = monitor_tasks()

        # Output according to format
        if args.json:
            # Convert Task objects to dictionaries for JSON output
            for key in ["stalled_task_list", "failed_task_list", "blocked_task_list"]:
                if key in stats:
                    stats[key] = [t.__dict__ for t in stats[key]]

            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(stats, f, indent=2, default=str)
                console.print(f"Report saved to {args.output}")
            else:
                logger.info(json.dumps(stats, indent=2, default=str))
        else:
            generate_report(stats, args.detailed)

            if args.output:
                # Redirect output to file
                with open(args.output, 'w') as f:
                    # This is a simplified text report
                    f.write(f"Task Monitor Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"Total Tasks: {stats['total_tasks']}\n")
                    f.write(f"Completed: {stats['completed_tasks']} ({stats['completion_percentage']:.1f}%)\n")
                    f.write(f"In Progress: {stats['in_progress_tasks']}\n")
                    f.write(f"Pending: {stats['pending_tasks']}\n")
                    f.write(f"Failed: {stats['failed_tasks']}\n")
                    f.write(f"Blocked: {stats['blocked_tasks']}\n")
                    f.write(f"Stalled: {stats['stalled_tasks']}\n")
                    f.write(f"Without PRs: {stats['tasks_without_pr']}\n")

                console.print(f"Report saved to {args.output}")

    except Exception as e:
        logger.exception(f"Error generating report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
