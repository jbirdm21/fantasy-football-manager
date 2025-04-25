#!/usr/bin/env python
"""Script to test the first 5 tasks and verify agent code changes."""
from agent_system.agents.models import TaskStatus, Task
from agent_system.utils.persistence import get_all_tasks, get_task, save_task
import os
import sys
import logging
import subprocess
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from datetime import datetime

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Set up environment
os.environ["PYTHONPATH"] = str(parent_dir)

# Setup console
console = Console()


def get_first_n_tasks(n=5):
    """Get the first n tasks from the database.

    Args:
        n: Number of tasks to retrieve

    Returns:
        List of the first n tasks
    """
    all_tasks = get_all_tasks()

    # Sort tasks by task_id to get a consistent order
    all_tasks.sort(key=lambda t: t.task_id)

    # Take the first n tasks
    return all_tasks[:n]


def reset_tasks_for_testing(tasks):
    """Reset tasks to PENDING status for testing.

    Args:
        tasks: List of tasks to reset

    Returns:
        Number of tasks reset
    """
    reset_count = 0

    for task in tasks:
        # Only reset completed or failed tasks
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.BLOCKED]:
            task.status = TaskStatus.PENDING
            task.updated_at = datetime.now()

            # Clear any existing artifacts
            if hasattr(task, 'artifacts'):
                # Store previous artifacts in a variable but don't set on task
                previous_artifacts = task.artifacts
                task.artifacts = []
                logger.info(f"Cleared {len(previous_artifacts)} artifacts from task {task.task_id}")

            save_task(task)
            reset_count += 1
            console.print(f"[yellow]Reset task {task.task_id}: {task.title}[/yellow]")

    return reset_count


def run_agents_on_tasks(tasks):
    """Run agents on the specified tasks.

    Args:
        tasks: List of tasks to run agents on
    """
    for task in tasks:
        agent_id = task.assigned_agent_id
        task_id = task.task_id

        console.print(Panel(f"[bold]Running agent {agent_id} on task: {task.title}[/bold]"))

        # Run the agent on this specific task
        try:
            result = subprocess.run(
                [sys.executable, "agent_runner.py", "--agent", agent_id, "--task", task_id],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                console.print(f"[green]Agent completed task successfully[/green]")
            else:
                console.print(f"[red]Agent encountered an error (code {result.returncode})[/red]")
                console.print(f"[dim]{result.stderr}[/dim]")

        except Exception as e:
            console.print(f"[red]Error running agent: {str(e)}[/red]")


def verify_code_changes(tasks):
    """Verify that code changes were made for each task.

    Args:
        tasks: List of tasks to verify

    Returns:
        Table with verification results
    """
    # Reload tasks to get updated status
    updated_tasks = []
    for task in tasks:
        updated_task = get_task(task.task_id)
        if updated_task:
            updated_tasks.append(updated_task)

    # Create results table
    table = Table(title="Task Code Change Verification")
    table.add_column("Task ID", style="dim")
    table.add_column("Title", style="cyan")
    table.add_column("Agent", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Code Changed", style="bold")
    table.add_column("PR Created", style="bold")

    for task in updated_tasks:
        # Check if task has artifacts (PR URLs)
        has_artifacts = hasattr(task, 'artifacts') and task.artifacts
        pr_count = len([url for url in (task.artifacts or []) if "github.com" in url and "/pull/" in url])

        # Determine if code was changed
        code_changed = "✓" if has_artifacts else "✗"
        pr_created = f"✓ ({pr_count} PRs)" if pr_count > 0 else "✗"

        # Set status color
        status_style = {
            TaskStatus.COMPLETED: "green",
            TaskStatus.IN_PROGRESS: "blue",
            TaskStatus.PENDING: "yellow",
            TaskStatus.FAILED: "red",
            TaskStatus.BLOCKED: "orange"
        }.get(task.status, "white")

        # Add row to table
        table.add_row(
            task.task_id[:8] + "...",
            task.title,
            task.assigned_agent_id,
            f"[{status_style}]{task.status.value}[/{status_style}]",
            f"[green]{code_changed}[/green]" if has_artifacts else f"[red]{code_changed}[/red]",
            f"[green]{pr_created}[/green]" if pr_count > 0 else f"[red]{pr_created}[/red]"
        )

    return table


def run_quality_checks(tasks):
    """Run quality checks on the completed tasks.

    Args:
        tasks: List of tasks to check
    """
    # Get IDs of completed tasks
    completed_task_ids = [
        task.task_id for task in tasks
        if task.status == TaskStatus.COMPLETED
    ]

    if not completed_task_ids:
        console.print("[yellow]No completed tasks to run quality checks on[/yellow]")
        return

    console.print(Panel(f"[bold]Running quality checks on {len(completed_task_ids)} completed tasks[/bold]"))

    # Run quality checks on each completed task
    for task_id in completed_task_ids:
        try:
            result = subprocess.run(
                [sys.executable, "code_quality_workflow.py", "--task", task_id],
                cwd=Path(__file__).parent,
                check=False
            )

            if result.returncode == 0:
                console.print(f"[green]Quality checks passed for task {task_id}[/green]")
            else:
                console.print(f"[yellow]Quality checks found issues for task {task_id}[/yellow]")

        except Exception as e:
            console.print(f"[red]Error running quality checks: {str(e)}[/red]")


def main():
    """Main function."""
    console.print(Panel("[bold]Testing First 5 Tasks[/bold]"))

    # Get the first 5 tasks
    tasks = get_first_n_tasks(5)
    console.print(f"Found {len(tasks)} tasks to test")

    # Display tasks
    task_table = Table(title="Tasks to Test")
    task_table.add_column("Task ID", style="dim")
    task_table.add_column("Title", style="cyan")
    task_table.add_column("Agent", style="magenta")
    task_table.add_column("Status", style="green")

    for task in tasks:
        task_table.add_row(
            task.task_id[:8] + "...",
            task.title,
            task.assigned_agent_id,
            task.status.value
        )

    console.print(task_table)

    # Reset tasks for testing
    console.print("[bold]Resetting Tasks for Testing[/bold]")
    reset_count = reset_tasks_for_testing(tasks)
    console.print(f"Reset {reset_count} tasks to PENDING status")

    # Run agents on tasks
    console.print("[bold]Running Agents on Tasks[/bold]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task_progress = progress.add_task("[bold]Processing tasks...", total=len(tasks))

        run_agents_on_tasks(tasks)

        progress.update(task_progress, completed=len(tasks))

    # Wait for agent processes to complete
    console.print("[yellow]Waiting for agent processes to complete (30 seconds)...[/yellow]")
    time.sleep(30)

    # Verify code changes
    console.print("[bold]Verifying Code Changes[/bold]")
    verification_table = verify_code_changes(tasks)
    console.print(verification_table)

    # Run quality checks
    run_quality_checks(tasks)

    console.print(Panel("[bold green]Test Complete![/bold green]"))


if __name__ == "__main__":
    main()
