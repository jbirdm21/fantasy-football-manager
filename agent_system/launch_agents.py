#!/usr/bin/env python3

from agent_system.agents.models import TaskStatus, Task
from agent_system.agents.tasks import check_code_quality_before_pr, submit_pr_for_task, update_task_status
from agent_system.utils.persistence import get_all_tasks, save_task
import os
import sys
from pathlib import Path
import argparse
import logging
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Import agent system modules

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / "agent_activity.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agent_system")

console = Console()

# Sample fantasy football tasks if none exist
SAMPLE_TASKS = [
    {
        "id": "FFM-001",
        "title": "Set up database models for fantasy football teams",
        "description": "Create database models for Teams, Players, Leagues, and basic stats",
        "status": TaskStatus.READY,
        "priority": 1
    },
    {
        "id": "FFM-002",
        "title": "Implement basic API routes for team management",
        "description": "Create API endpoints for CRUD operations on fantasy teams",
        "status": TaskStatus.READY,
        "priority": 2
    },
    {
        "id": "FFM-003",
        "title": "Connect to external football data APIs",
        "description": "Set up clients for ESPN, Yahoo, and Sleeper APIs to fetch player stats",
        "status": TaskStatus.READY,
        "priority": 3
    },
    {
        "id": "FFM-004",
        "title": "Create draft simulation interface",
        "description": "Develop UI and backend for fantasy draft simulation",
        "status": TaskStatus.READY,
        "priority": 4
    },
    {
        "id": "FFM-005",
        "title": "Implement player comparison tool",
        "description": "Create a tool to compare player statistics and projections",
        "status": TaskStatus.READY,
        "priority": 5
    }
]


def initialize_tasks():
    """Initialize task list if it doesn't exist."""
    tasks = get_all_tasks()

    if not tasks:
        console.print("[yellow]No tasks found. Initializing with sample fantasy football tasks...[/yellow]")
        for task_data in SAMPLE_TASKS:
            task = Task(**task_data)
            save_task(task)
        console.print("[green]Sample tasks created successfully![/green]")

    return get_all_tasks()


def get_next_task():
    """Get the next available task from the task list."""
    tasks = get_all_tasks()

    # Sort by priority
    available_tasks = [t for t in tasks if t.status == TaskStatus.READY]
    if not available_tasks:
        return None

    available_tasks.sort(key=lambda x: x.priority)
    return available_tasks[0]


def assign_task_to_agent(task):
    """Assign a task to an agent and start working on it."""
    # Mark task as in progress
    update_task_status(task.id, TaskStatus.IN_PROGRESS, "Task assigned to agent")

    console.print(Panel(f"[bold]Agent working on task: {task.id} - {task.title}[/bold]"))
    console.print(f"Description: {task.description}")

    # Here, you would call your agent to work on the task
    # For now, we'll simulate the agent process

    # Create a branch for the task
    branch_name = f"task/{task.id.lower()}"
    os.system(f"git checkout -b {branch_name}")

    # Simulate agent work
    with Progress() as progress:
        agent_work = progress.add_task("[cyan]Agent working...", total=100)

        # Simulate progress
        for i in range(100):
            progress.update(agent_work, advance=1)
            import time
            time.sleep(0.1)

    # Run code quality checks
    passed = check_code_quality_before_pr(task)

    if passed:
        # Submit PR
        pr_url = submit_pr_for_task(task, branch_name)
        if pr_url:
            console.print(f"[green]PR submitted successfully: {pr_url}[/green]")
        else:
            console.print("[red]Failed to submit PR[/red]")
    else:
        console.print("[red]Code quality checks failed. Fix issues before submitting PR.[/red]")

    return passed


def main():
    """Main entry point for agent system."""
    parser = argparse.ArgumentParser(description="Launch the agent system")
    parser.add_argument("--task", help="Specific task ID to work on")
    parser.add_argument("--list", action="store_true", help="List all tasks")
    parser.add_argument("--init", action="store_true", help="Initialize task list")

    args = parser.parse_args()

    if args.init:
        initialize_tasks()
        return

    if args.list:
        tasks = get_all_tasks()
        console.print("\n[bold]Fantasy Football Manager Task List:[/bold]\n")

        for task in sorted(tasks, key=lambda x: x.priority):
            status_color = {
                TaskStatus.READY: "blue",
                TaskStatus.IN_PROGRESS: "yellow",
                TaskStatus.COMPLETED: "green",
                TaskStatus.PR_SUBMITTED: "cyan",
                TaskStatus.PR_READY: "magenta",
                TaskStatus.NEEDS_REVISION: "red",
                TaskStatus.ERROR: "red",
            }.get(task.status, "white")

            console.print(f"[{status_color}]{task.id}[/{status_color}] - {task.title} (Priority: {task.priority})")
            console.print(f"  Status: [{status_color}]{task.status}[/{status_color}]")
            if task.description:
                console.print(f"  Description: {task.description}")
            console.print("")
        return

    # Initialize tasks if needed
    tasks = get_all_tasks()
    if not tasks:
        tasks = initialize_tasks()

    console.print(Panel("[bold]Fantasy Football Manager Agent System[/bold]",
                        subtitle="Let's build some fantasy football goodness!"))

    if args.task:
        # Work on specific task
        task = next((t for t in tasks if t.id == args.task), None)
        if not task:
            console.print(f"[red]Task {args.task} not found[/red]")
            return

        assign_task_to_agent(task)
    else:
        # Get next task
        task = get_next_task()
        if not task:
            console.print("[yellow]No available tasks found. All tasks may be complete or in progress.[/yellow]")
            return

        assign_task_to_agent(task)


if __name__ == "__main__":
    main()
