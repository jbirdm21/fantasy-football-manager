#!/usr/bin/env python
"""
Combined workflow script that orchestrates test generation, QA validation,
and integration testing to ensure high-quality agent-generated code.
"""
from agent_system.agents.models import TaskStatus, Task
from agent_system.utils.persistence import get_all_tasks, get_task, save_task
import argparse
import logging
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Set up environment
os.environ["PYTHONPATH"] = str(parent_dir)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("code_quality_workflow")
console = Console()


def run_script(script_name: str, *args) -> int:
    """Run a Python script with arguments.

    Args:
        script_name: Name of the script to run
        *args: Additional arguments to pass to the script

    Returns:
        Exit code of the script
    """
    cmd = [sys.executable, script_name]
    cmd.extend(args)

    console.print(f"[bold blue]Running {script_name} {' '.join(args)}[/bold blue]")

    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            check=False
        )
        return result.returncode
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return 1


def process_single_task(task_id: str, skip_tests: bool = False) -> bool:
    """Process a single task through the full code quality workflow.

    Args:
        task_id: ID of the task to process
        skip_tests: Whether to skip test generation

    Returns:
        True if successful, False otherwise
    """
    task = get_task(task_id)
    if not task:
        console.print(f"[red]Task {task_id} not found[/red]")
        return False

    console.print(Panel(f"Starting code quality workflow for task: {task.title} ({task.task_id})"))

    success = True

    # Step 1: Generate tests (if not skipped)
    if not skip_tests:
        console.print("[bold]Step 1: Generating Tests[/bold]")
        exit_code = run_script("test_generator.py", "--task", task_id)
        if exit_code != 0:
            console.print("[yellow]Warning: Test generation had issues[/yellow]")
            success = False

    # Step 2: Run QA workflow
    console.print("[bold]Step 2: Running QA Validation[/bold]")
    exit_code = run_script("qa_workflow.py", "--task", task_id)
    if exit_code != 0:
        console.print("[yellow]Warning: QA validation had issues[/yellow]")
        success = False

    # Step 3: Update task with quality status
    task = get_task(task_id)  # Reload task as it may have been modified
    if task:
        task.code_quality_checked = True
        task.code_quality_status = "passed" if success else "issues_found"
        save_task(task)

    if success:
        console.print(Panel("[bold green]Code Quality Workflow PASSED[/bold green]"))
    else:
        console.print(Panel("[bold yellow]Code Quality Workflow completed with issues[/bold yellow]"))

    return success


def process_all_completed_tasks(skip_tests: bool = False) -> None:
    """Process all completed tasks through the code quality workflow.

    Args:
        skip_tests: Whether to skip test generation
    """
    all_tasks = get_all_tasks()
    completed_tasks = [
        t for t in all_tasks
        if t.status == TaskStatus.COMPLETED and
        (not hasattr(t, 'code_quality_checked') or not t.code_quality_checked)
    ]

    if not completed_tasks:
        console.print("[yellow]No completed tasks found that need code quality checks[/yellow]")
        return

    console.print(f"[bold]Found {len(completed_tasks)} completed tasks that need code quality checks[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task_progress = progress.add_task(
            "[bold]Running code quality workflow...",
            total=len(completed_tasks)
        )

        success_count = 0
        issue_count = 0

        for task in completed_tasks:
            progress.update(task_progress, description=f"[bold]Processing task: {task.title}")

            if process_single_task(task.task_id, skip_tests):
                success_count += 1
            else:
                issue_count += 1

            progress.update(task_progress, advance=1)

    # Final summary
    console.print(Panel(f"[bold]Code Quality Workflow Summary[/bold]\n\n"
                        f"Total Tasks: {len(completed_tasks)}\n"
                        f"Passed: {success_count}\n"
                        f"Issues Found: {issue_count}"))


def check_collaboration(tasks_limit: int = 10) -> None:
    """Check and report on collaboration between agents.

    Args:
        tasks_limit: Maximum number of tasks to analyze
    """
    all_tasks = get_all_tasks()
    completed_tasks = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]

    # Take most recent tasks first
    completed_tasks.sort(key=lambda t: t.updated_at, reverse=True)
    tasks_to_analyze = completed_tasks[:tasks_limit]

    console.print("[bold]Analyzing Agent Collaboration[/bold]")

    # Agent collaboration matrix
    agents = set()
    for task in all_tasks:
        agents.add(task.assigned_agent_id)

    agents = sorted(list(agents))

    # Create collaboration table
    table = Table(title="Agent Collaboration Analysis")
    table.add_column("Agent", style="cyan")
    for agent in agents:
        table.add_column(agent, style="green")

    # Calculate collaboration scores
    for agent1 in agents:
        row = [agent1]
        for agent2 in agents:
            if agent1 == agent2:
                row.append("-")
                continue

            # Count related tasks between these agents
            related_count = 0
            for task in tasks_to_analyze:
                if task.assigned_agent_id == agent1:
                    related_tasks = find_related_tasks_by_agent(task, agent2)
                    related_count += len(related_tasks)

            row.append(str(related_count))

        table.add_row(*row)

    console.print(table)


def find_related_tasks_by_agent(task: Task, agent_id: str) -> List[Task]:
    """Find tasks related to the given task that are assigned to a specific agent.

    Args:
        task: The task to find related tasks for
        agent_id: ID of the agent to filter by

    Returns:
        List of related tasks assigned to the specified agent
    """
    all_tasks = get_all_tasks()

    # Simple heuristic - same roadmap phase or related keywords
    related_tasks = []

    for t in all_tasks:
        if t.task_id == task.task_id or t.assigned_agent_id != agent_id:
            continue

        # Check roadmap phase
        if t.roadmap_phase == task.roadmap_phase:
            related_tasks.append(t)
            continue

        # Check keywords
        keywords = [word.lower() for word in task.title.split() if len(word) > 4]
        for keyword in keywords:
            if keyword in t.title.lower():
                related_tasks.append(t)
                break

    return related_tasks


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Combined workflow for ensuring high-quality agent-generated code"
    )
    parser.add_argument(
        "--task",
        type=str,
        help="ID of a specific task to process"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all completed tasks"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip test generation (only do QA)"
    )
    parser.add_argument(
        "--collaboration",
        action="store_true",
        help="Check and report on agent collaboration"
    )

    args = parser.parse_args()

    if args.task:
        process_single_task(args.task, args.skip_tests)
    elif args.all:
        process_all_completed_tasks(args.skip_tests)
    elif args.collaboration:
        check_collaboration()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
