#!/usr/bin/env python
"""Script to run multiple agents in parallel to process tasks more efficiently."""
import argparse
import logging
import os
import sys
import time
import multiprocessing
from pathlib import Path
import subprocess
from typing import List, Optional
from rich.console import Console
from rich.logging import RichHandler
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
logger = logging.getLogger("parallel_agents")
console = Console()

DEFAULT_AGENTS = [
    "tech-lead-1",
    "frontend-dev-1",
    "backend-dev-1",
    "data-scientist-1",
    "devops-eng-1",
    "qa-eng-1"
]


def run_agent(agent_id: str, task_id: Optional[str] = None, monitor: bool = False) -> None:
    """Run an agent in a separate process.

    Args:
        agent_id: ID of the agent to run
        task_id: Optional ID of a specific task to run
        monitor: Whether to run task monitor after agent completes
    """
    cmd = [sys.executable, "agent_runner.py", "--agent", agent_id]
    if task_id:
        cmd.extend(["--task", task_id])

    agent_log_file = Path("outputs/logs") / f"{agent_id}_{int(time.time())}.log"
    agent_log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting agent {agent_id} (logging to {agent_log_file})")

    with open(agent_log_file, "w") as log_file:
        process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).parent,
        )

        try:
            process.wait()
            logger.info(f"Agent {agent_id} completed with return code {process.returncode}")

            if monitor:
                # Run task monitor to update on progress
                monitor_cmd = [sys.executable, "task_monitor.py"]
                subprocess.run(monitor_cmd, cwd=Path(__file__).parent)

        except KeyboardInterrupt:
            logger.warning(f"Terminating agent {agent_id}")
            process.terminate()
            process.wait()


def run_agents_in_parallel(agents: List[str], max_parallel: int = 3) -> None:
    """Run multiple agents in parallel.

    Args:
        agents: List of agent IDs to run
        max_parallel: Maximum number of agents to run in parallel
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[bold]Running agents in parallel...", total=None)

        # Create a pool of worker processes
        pool = multiprocessing.Pool(processes=max_parallel)

        try:
            # Start agents in parallel
            results = []
            for agent_id in agents:
                result = pool.apply_async(run_agent, (agent_id, None, False))
                results.append((agent_id, result))

            # Wait for all processes to complete
            while results:
                for i, (agent_id, result) in enumerate(results[:]):
                    if result.ready():
                        logger.info(f"Agent {agent_id} has completed")
                        results.pop(i)

                if results:
                    time.sleep(5)  # Wait before checking again

            # Run task monitor at the end to show final status
            logger.info("All agents have completed")
            subprocess.run([sys.executable, "task_monitor.py", "--detailed"],
                           cwd=Path(__file__).parent)

        except KeyboardInterrupt:
            logger.warning("Keyboard interrupt detected, shutting down...")
            pool.terminate()
        finally:
            pool.close()
            pool.join()


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Run multiple agents in parallel")
    parser.add_argument(
        "--agents",
        nargs="+",
        help="List of agent IDs to run (default: all agents)"
    )
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=3,
        help="Maximum number of agents to run in parallel (default: 3)"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous mode (restart agents when they complete)"
    )
    parser.add_argument(
        "--quality-checks",
        action="store_true",
        help="Run code quality checks on completed tasks"
    )

    args = parser.parse_args()

    agents = args.agents if args.agents else DEFAULT_AGENTS

    console.print(f"[bold green]Starting {len(agents)} agents with max {args.max_parallel} in parallel[/bold green]")
    console.print(f"Agents: {', '.join(agents)}")

    if args.continuous:
        console.print("[bold yellow]Running in continuous mode - press Ctrl+C to stop[/bold yellow]")
        try:
            while True:
                run_agents_in_parallel(agents, args.max_parallel)

                # Run code quality checks if requested
                if args.quality_checks:
                    console.print("\n[bold blue]Running code quality checks on completed tasks...[/bold blue]")
                    subprocess.run(
                        [sys.executable, "code_quality_workflow.py", "--all"],
                        cwd=Path(__file__).parent
                    )

                console.print("\n[bold blue]All agents completed, restarting...[/bold blue]\n")
                time.sleep(10)  # Wait before restarting
        except KeyboardInterrupt:
            console.print("\n[bold red]Shutting down[/bold red]")
    else:
        run_agents_in_parallel(agents, args.max_parallel)

        # Run code quality checks if requested
        if args.quality_checks:
            console.print("\n[bold blue]Running code quality checks on completed tasks...[/bold blue]")
            subprocess.run(
                [sys.executable, "code_quality_workflow.py", "--all"],
                cwd=Path(__file__).parent
            )

        console.print("\n[bold green]All agents have completed![/bold green]")


if __name__ == "__main__":
    main()
