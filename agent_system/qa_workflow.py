#!/usr/bin/env python
"""QA workflow to validate agent-generated code and ensure quality standards."""
from agent_system.utils.github_integration import commit_agent_changes
from agent_system.agents.models import TaskStatus, Task
from agent_system.utils.persistence import get_all_tasks, get_task, save_task
import argparse
import logging
import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

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
logger = logging.getLogger("qa_workflow")
console = Console()


def find_related_tasks(task: Task) -> List[Task]:
    """Find tasks that are related to the given task.

    Args:
        task: The task to find related tasks for.

    Returns:
        A list of related tasks.
    """
    all_tasks = get_all_tasks()

    # Find tasks that might be related based on:
    # 1. Dependencies
    # 2. Similar keywords in title
    # 3. Same roadmap phase

    related_tasks = []

    # Check dependencies
    if hasattr(task, 'dependencies') and task.dependencies:
        for dep_id in task.dependencies:
            for t in all_tasks:
                if t.task_id == dep_id:
                    related_tasks.append(t)

    # Check similar keywords in title
    keywords = [word.lower() for word in task.title.split() if len(word) > 4]
    for t in all_tasks:
        if t.task_id != task.task_id:  # Skip self
            for keyword in keywords:
                if keyword in t.title.lower() and t not in related_tasks:
                    related_tasks.append(t)
                    break

    # Check same roadmap phase
    for t in all_tasks:
        if (t.task_id != task.task_id and
            t.roadmap_phase == task.roadmap_phase and
                t not in related_tasks):
            related_tasks.append(t)

    return related_tasks


def run_tests_for_task(task: Task) -> Tuple[bool, List[str]]:
    """Run tests related to the task's changes.

    Args:
        task: The task to run tests for.

    Returns:
        A tuple of (success, test_output).
    """
    console.print(f"[bold blue]Running tests for task: {task.title}[/bold blue]")

    # Get artifacts (PR URLs) from task
    pr_urls = task.artifacts if hasattr(task, 'artifacts') and task.artifacts else []

    # If no PRs found, we can't determine what to test
    if not pr_urls:
        console.print("[yellow]No PRs found for this task, skipping tests[/yellow]")
        return False, ["No PRs found for this task"]

    # Get the changed files from the PR descriptions
    # For now, we'll use a heuristic based on the task title and related words
    potential_test_dirs = []

    # Backend task detection
    backend_keywords = ["api", "database", "server", "endpoint", "service", "model"]
    if any(keyword in task.title.lower() for keyword in backend_keywords):
        potential_test_dirs.append("tests/backend")
        potential_test_dirs.append("backend/tests")

    # Frontend task detection
    frontend_keywords = ["ui", "interface", "component", "page", "form", "react", "vue"]
    if any(keyword in task.title.lower() for keyword in frontend_keywords):
        potential_test_dirs.append("tests/frontend")
        potential_test_dirs.append("frontend/tests")

    # Data task detection
    data_keywords = ["data", "etl", "analytics", "metrics", "statistics", "import"]
    if any(keyword in task.title.lower() for keyword in data_keywords):
        potential_test_dirs.append("tests/data")
        potential_test_dirs.append("data/tests")

    # Add generic test directories as fallback
    potential_test_dirs.append("tests")

    # Run tests in the identified directories
    test_results = []
    success = True

    for test_dir in potential_test_dirs:
        test_dir_path = parent_dir / test_dir
        if not test_dir_path.exists():
            continue

        console.print(f"[blue]Testing directory: {test_dir}[/blue]")

        # Check if pytest is available
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", str(test_dir_path), "-v"],
                capture_output=True,
                text=True,
                check=False
            )

            output = result.stdout if result.stdout else result.stderr
            test_results.append(f"Tests in {test_dir}:\n{output}")

            if result.returncode != 0:
                success = False
                console.print(f"[red]Tests failed in {test_dir}[/red]")
            else:
                console.print(f"[green]Tests passed in {test_dir}[/green]")

        except Exception as e:
            test_results.append(f"Error running tests in {test_dir}: {str(e)}")
            success = False

    return success, test_results


def lint_code(task: Task) -> Tuple[bool, List[str]]:
    """Run linting on code changes related to the task.

    Args:
        task: The task to lint code for.

    Returns:
        A tuple of (success, lint_output).
    """
    console.print(f"[bold blue]Linting code for task: {task.title}[/bold blue]")

    # Similar approach to the test function, but with linting tools
    lint_results = []
    success = True

    # Try to detect what type of code was changed
    is_python = False
    is_javascript = False
    is_typescript = False

    # Simple heuristic based on task title/description
    python_keywords = ["python", "django", "flask", "api", "backend", "fastapi"]
    js_keywords = ["javascript", "js", "react", "vue", "frontend", "web"]
    ts_keywords = ["typescript", "ts", "angular", "frontend", "next.js"]

    task_text = f"{task.title} {task.description}".lower()

    if any(keyword in task_text for keyword in python_keywords):
        is_python = True
    if any(keyword in task_text for keyword in js_keywords):
        is_javascript = True
    if any(keyword in task_text for keyword in ts_keywords):
        is_typescript = True

    # Run appropriate linters
    if is_python:
        try:
            # Run flake8
            result = subprocess.run(
                ["flake8", "backend", "--max-line-length=100"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.stdout:
                lint_results.append(f"Python linting issues:\n{result.stdout}")
                success = False
                console.print("[yellow]Python linting found issues[/yellow]")
            else:
                console.print("[green]Python linting passed[/green]")

        except Exception as e:
            lint_results.append(f"Error running Python linter: {str(e)}")

    if is_javascript or is_typescript:
        try:
            # Run eslint
            result = subprocess.run(
                ["npx", "eslint", "frontend", "--ext", ".js,.jsx,.ts,.tsx"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.stdout:
                lint_results.append(f"JS/TS linting issues:\n{result.stdout}")
                success = False
                console.print("[yellow]JS/TS linting found issues[/yellow]")
            else:
                console.print("[green]JS/TS linting passed[/green]")

        except Exception as e:
            lint_results.append(f"Error running JS/TS linter: {str(e)}")

    return success, lint_results


def run_integration_checks(task: Task, related_tasks: List[Task]) -> Tuple[bool, List[str]]:
    """Run integration checks between this task and related tasks.

    Args:
        task: The main task
        related_tasks: List of related tasks

    Returns:
        A tuple of (success, integration_output).
    """
    console.print(f"[bold blue]Running integration checks for task: {task.title}[/bold blue]")

    integration_results = []
    success = True

    if not related_tasks:
        integration_results.append("No related tasks found for integration checks")
        return True, integration_results

    # Display related tasks
    related_table = Table(title="Related Tasks for Integration")
    related_table.add_column("Task ID", style="dim")
    related_table.add_column("Title", style="cyan")
    related_table.add_column("Status", style="green")

    for related_task in related_tasks:
        related_table.add_row(
            related_task.task_id[:8] + "...",
            related_task.title,
            related_task.status.value
        )

    console.print(related_table)

    # Run integration tests if they exist
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/integration", "-v"],
            capture_output=True,
            text=True,
            check=False
        )

        output = result.stdout if result.stdout else result.stderr
        integration_results.append(f"Integration tests:\n{output}")

        if result.returncode != 0:
            success = False
            console.print(f"[red]Integration tests failed[/red]")
        else:
            console.print(f"[green]Integration tests passed[/green]")

    except Exception as e:
        integration_results.append(f"Error running integration tests: {str(e)}")
        success = False

    return success, integration_results


def create_qa_report(task: Task, test_results: List[str], lint_results: List[str],
                     integration_results: List[str], success: bool) -> str:
    """Create a QA report for the task.

    Args:
        task: The task that was QA'd
        test_results: List of test results
        lint_results: List of linting results
        integration_results: List of integration test results
        success: Overall success status

    Returns:
        Report content as a string
    """
    report = f"# QA Report for Task: {task.title}\n\n"
    report += f"- Task ID: {task.task_id}\n"
    report += f"- Status: {task.status.value}\n"
    report += f"- Assigned to: {task.assigned_agent_id}\n\n"

    report += "## Test Results\n\n"
    for result in test_results:
        report += f"```\n{result}\n```\n\n"

    report += "## Linting Results\n\n"
    for result in lint_results:
        report += f"```\n{result}\n```\n\n"

    report += "## Integration Results\n\n"
    for result in integration_results:
        report += f"```\n{result}\n```\n\n"

    report += f"## Overall Status\n\n"
    report += f"**{'PASSED' if success else 'FAILED'}**\n\n"

    if not success:
        report += "## Recommendations\n\n"
        report += "- Review test failures and fix issues\n"
        report += "- Address code style issues identified by linting\n"
        report += "- Check integration with related components\n"

    return report


def submit_qa_report(task: Task, report: str) -> str:
    """Submit a QA report as a comment on the task's PR.

    Args:
        task: The task to submit a report for
        report: The QA report content

    Returns:
        URL of the created PR or file
    """
    # Create a report file in the docs/qa_reports directory
    report_dir = parent_dir / "docs" / "qa_reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = f"qa_report_{task.task_id}_{int(time.time())}.md"
    report_path = report_dir / report_file

    # Create file changes dictionary for GitHub commit
    file_changes = {
        str(report_path): report
    }

    try:
        # Commit the QA report
        pr_url = commit_agent_changes(
            agent_id="qa-eng-1",
            file_changes=file_changes,
            commit_message=f"QA Report for task: {task.title}",
            pr_description=f"This PR contains the QA report for task {task.task_id}: {task.title}"
        )

        console.print(f"[green]Created QA report PR: {pr_url}[/green]")
        return pr_url
    except Exception as e:
        logger.error(f"Error creating QA report PR: {e}")

        # Fallback to local file if GitHub fails
        with open(report_path, 'w') as f:
            f.write(report)

        console.print(f"[yellow]Created local QA report: {report_path}[/yellow]")
        return str(report_path)


def process_completed_task(task_id: str) -> None:
    """Run the QA workflow for a completed task.

    Args:
        task_id: ID of the task to process
    """
    task = get_task(task_id)
    if not task:
        console.print(f"[red]Task {task_id} not found[/red]")
        return

    console.print(Panel(f"Starting QA workflow for task: {task.title} ({task.task_id})"))

    # Find related tasks
    related_tasks = find_related_tasks(task)
    console.print(f"Found {len(related_tasks)} related tasks for integration checks")

    # Run tests
    test_success, test_results = run_tests_for_task(task)

    # Run linting
    lint_success, lint_results = lint_code(task)

    # Run integration checks
    integration_success, integration_results = run_integration_checks(task, related_tasks)

    # Overall success
    success = test_success and lint_success and integration_success

    # Create and submit report
    report = create_qa_report(task, test_results, lint_results, integration_results, success)
    report_url = submit_qa_report(task, report)

    # Update task with QA results
    if hasattr(task, 'artifacts') and task.artifacts:
        task.artifacts.append(report_url)
    else:
        task.artifacts = [report_url]

    # Add QA status to task
    task.qa_status = "passed" if success else "failed"
    task.qa_report_url = report_url

    # Save task
    save_task(task)

    # Print final status
    if success:
        console.print(Panel("[bold green]QA PASSED: Code meets quality standards[/bold green]"))
    else:
        console.print(Panel("[bold red]QA FAILED: Issues detected that need to be fixed[/bold red]"))


def process_all_completed_tasks() -> None:
    """Process all completed tasks that haven't been QA'd yet."""
    all_tasks = get_all_tasks()
    completed_tasks = [
        t for t in all_tasks
        if t.status == TaskStatus.COMPLETED and
        (not hasattr(t, 'qa_status') or not t.qa_status)
    ]

    if not completed_tasks:
        console.print("[yellow]No completed tasks found that need QA[/yellow]")
        return

    console.print(f"[bold]Found {len(completed_tasks)} completed tasks that need QA[/bold]")

    for task in completed_tasks:
        process_completed_task(task.task_id)


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="QA workflow for agent-generated code")
    parser.add_argument(
        "--task",
        type=str,
        help="ID of a specific task to QA"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all completed tasks that haven't been QA'd"
    )

    args = parser.parse_args()

    if args.task:
        process_completed_task(args.task)
    elif args.all:
        process_all_completed_tasks()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
