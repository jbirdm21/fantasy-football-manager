#!/usr/bin/env python
"""Continuous monitoring script to ensure agents are making progress and creating PRs."""
import os
import sys
import time
import argparse
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
from rich.console import Console
from rich.logging import RichHandler

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
logger = logging.getLogger("continuous_monitoring")

# Setup console
console = Console()


def run_command(cmd, capture_output=True):
    """Run a command and return the result.

    Args:
        cmd: Command to run as a list of strings
        capture_output: Whether to capture output

    Returns:
        A tuple of (success, output)
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=capture_output,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout if capture_output else ""
    except Exception as e:
        logger.error(f"Error running command {' '.join(cmd)}: {e}")
        return False, str(e)


def check_stalled_tasks():
    """Check for stalled tasks and reset them."""
    logger.info("Checking for stalled tasks")
    success, _ = run_command([sys.executable, "reset_tasks.py", "--status", "IN_PROGRESS", "--new-status", "PENDING"])
    if success:
        logger.info("Successfully reset stalled tasks")
    else:
        logger.error("Failed to reset stalled tasks")


def process_pending_tasks():
    """Run agents on pending tasks."""
    logger.info("Running agents on pending tasks")
    success, _ = run_command([sys.executable, "run_parallel_agents.py", "--max-parallel", "3"])
    if success:
        logger.info("Successfully ran agents on pending tasks")
    else:
        logger.error("Failed to run agents on pending tasks")


def verify_completed_tasks():
    """Verify completed tasks have PRs, generating them if necessary."""
    logger.info("Verifying completed tasks have PRs")
    success, _ = run_command([sys.executable, "ensure_task_completion.py", "--max-tasks", "10"])
    if success:
        logger.info("Successfully verified completed tasks")
    else:
        logger.error("Failed to verify completed tasks")


def run_code_quality_checks():
    """Run code quality checks on recently completed tasks."""
    logger.info("Running code quality checks")
    success, _ = run_command([sys.executable, "code_quality_workflow.py", "--all"])
    if success:
        logger.info("Successfully ran code quality checks")
    else:
        logger.error("Failed to run code quality checks")


def generate_status_report():
    """Generate a status report of the agent system."""
    logger.info("Generating status report")
    success, output = run_command([sys.executable, "check_tasks.py", "--limit", "20"])
    if success:
        report_file = Path(__file__).parent / "outputs" / \
            f"status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(f"Agent System Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(output)
        logger.info(f"Status report saved to {report_file}")
    else:
        logger.error("Failed to generate status report")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Continuous monitoring for agent system")
    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="Check interval in minutes (default: 15)"
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Don't reset stalled tasks"
    )
    parser.add_argument(
        "--no-quality",
        action="store_true",
        help="Skip code quality checks"
    )

    args = parser.parse_args()
    interval_seconds = args.interval * 60

    console.print(f"[bold green]Starting continuous monitoring (interval: {args.interval} minutes)[/bold green]")

    try:
        while True:
            start_time = time.time()

            # Main monitoring cycle
            if not args.no_reset:
                check_stalled_tasks()

            process_pending_tasks()
            verify_completed_tasks()

            if not args.no_quality:
                run_code_quality_checks()

            generate_status_report()

            # Wait for next cycle
            elapsed = time.time() - start_time
            wait_time = max(0, interval_seconds - elapsed)

            console.print(f"[bold]Cycle completed in {elapsed:.1f}s. Next check in {wait_time/60:.1f} minutes.[/bold]")

            if wait_time > 0:
                time.sleep(wait_time)

    except KeyboardInterrupt:
        console.print("[bold red]Monitoring stopped by user[/bold red]")
    except Exception as e:
        logger.exception(f"Error in monitoring loop: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
