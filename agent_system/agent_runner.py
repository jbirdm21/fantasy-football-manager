"""Main runner for the agent system."""
from agent_system.agents.models import Agent, AgentState, Task, TaskStatus
from agent_system.config import (
    OPENAI_API_KEY, AGENT_LOG_LEVEL, MAX_CONCURRENT_TASKS, TASK_TIMEOUT_HOURS,
    AGENT_OUTPUTS_DIR, PROJECT_ROOT, is_path_allowed
)
from agent_system.utils.github_integration import commit_agent_changes
from agent_system.utils.persistence import (
    save_agent_state, get_agent_state, save_task, get_task,
    get_all_tasks, get_available_tasks, update_task_status, log_agent_activity
)
from agent_system.tasks.roadmap_parser import generate_tasks_from_roadmap, assign_tasks_to_agents
from agent_system.agents.definitions import AGENTS, AGENT_MAP
import os
import time
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import argparse
import json
from pathlib import Path
import sqlite3

import openai
from rich.console import Console
from rich.logging import RichHandler

# Define database connection function


def get_db_connection():
    """Get a connection to the SQLite database.

    Returns:
        SQLite connection object
    """
    db_path = Path(__file__).parent / "outputs" / "agent_system.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


# Setup logging
logging.basicConfig(
    level=getattr(logging, AGENT_LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("agent_runner")
console = Console()


def initialize_agents() -> None:
    """Initialize agent states in the database."""
    for agent in AGENTS:
        # Check if agent state already exists
        state = get_agent_state(agent.agent_id)
        if not state:
            # Create new agent state
            state = AgentState(agent_id=agent.agent_id)
            save_agent_state(state)
            logger.info(f"Initialized agent {agent.name} ({agent.agent_id})")


def initialize_tasks() -> None:
    """Initialize tasks in the database from the roadmap."""
    existing_tasks = get_all_tasks()
    if not existing_tasks:
        # Generate tasks from roadmap
        logger.info("Generating tasks from roadmap...")
        tasks = generate_tasks_from_roadmap()

        # Create specialization map for task assignment
        specialization_map = {}
        for agent in AGENTS:
            specialization_map[agent.agent_id] = [spec.value for spec in agent.specializations]

        # Assign tasks to agents
        assigned_tasks = assign_tasks_to_agents(tasks, specialization_map)

        # Save tasks to database
        for task in assigned_tasks:
            save_task(task)
            logger.info(f"Created task: {task.title} (assigned to {task.assigned_agent_id})")
    else:
        logger.info(f"Found {len(existing_tasks)} existing tasks in the database")


def run_agent(agent_id: str, task_id: Optional[str] = None) -> None:
    """Run an agent on a task.

    Args:
        agent_id: ID of the agent to run.
        task_id: Optional ID of the task to run. If not provided, the agent's current task
                 or the next available task will be used.
    """
    # Get agent and state
    agent = AGENT_MAP.get(agent_id)
    if not agent:
        logger.error(f"Agent {agent_id} not found")
        return

    state = get_agent_state(agent_id)
    if not state:
        logger.error(f"State for agent {agent_id} not found")
        return

    # Determine which task to work on
    if task_id:
        task = get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
    elif state.current_task_id:
        task = get_task(state.current_task_id)
        if not task:
            logger.error(f"Current task {state.current_task_id} for agent {agent_id} not found")
            return
    else:
        # Get next available task
        available_tasks = get_available_tasks(agent_id)
        if not available_tasks:
            logger.info(f"No available tasks for agent {agent_id}")
            return
        task = available_tasks[0]

    # Update agent state
    state.current_task_id = task.task_id
    state.status = "working"
    state.last_activity = datetime.now()
    save_agent_state(state)

    # Update task status
    if task.status == TaskStatus.PENDING:
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.now()
        save_task(task)

    # Log start of task
    logger.info(f"Agent {agent.name} starting task: {task.title}")
    log_agent_activity(agent_id, f"Starting task {task.task_id}: {task.title}")

    try:
        # Execute task
        result = execute_task(agent, task, state)

        # Update task status
        if result.get("status") == "completed":
            task.status = TaskStatus.COMPLETED
            task.actual_hours = result.get("hours", 0.0)
            state.completed_tasks.append(task.task_id)

            # Store artifacts
            if "artifacts" in result:
                task.artifacts = result["artifacts"]
                for artifact in result["artifacts"]:
                    if artifact.startswith("http"):
                        logger.info(f"Task '{task.title}' created PR: {artifact}")

            logger.info(f"Agent {agent.name} completed task: {task.title}")
            log_agent_activity(agent_id, f"Completed task {task.task_id}: {task.title}")
        elif result.get("status") == "failed":
            task.status = TaskStatus.FAILED
            logger.error(f"Agent {agent.name} failed task: {task.title}")
            log_agent_activity(agent_id, f"Failed task {task.task_id}: {task.title}", "ERROR")
        elif result.get("status") == "blocked":
            task.status = TaskStatus.BLOCKED
            logger.warning(f"Agent {agent.name} blocked on task: {task.title}")
            log_agent_activity(agent_id, f"Blocked on task {task.task_id}: {task.title}", "WARNING")

        task.updated_at = datetime.now()
        save_task(task)
    except Exception as e:
        logger.exception(f"Error executing task {task.task_id}: {e}")
        log_agent_activity(agent_id, f"Error executing task {task.task_id}: {e}", "ERROR")

        # Update task and agent state
        task.status = TaskStatus.FAILED
        task.updated_at = datetime.now()
        save_task(task)
    finally:
        # Update agent state
        state.status = "idle"
        state.current_task_id = None if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] else task.task_id
        state.last_activity = datetime.now()
        save_agent_state(state)


def execute_task(agent: Agent, task: Task, state: AgentState) -> Dict[str, Any]:
    """Execute a task using the agent.

    Args:
        agent: The agent to use for execution.
        task: The task to execute.
        state: The agent's current state.

    Returns:
        A dictionary with the execution result.
    """
    # Set up OpenAI client
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # Prepare system prompt
    system_prompt = agent.system_prompt

    # Prepare user message with task details
    user_message = f"""
# Task: {task.title}

## Description
{task.description}

## Acceptance Criteria
{chr(10).join(['- ' + criterion for criterion in task.acceptance_criteria])}

## Context
- Task ID: {task.task_id}
- Priority: {task.priority}
- Roadmap Phase: {task.roadmap_phase}
- Dependencies: {', '.join(task.dependencies) if task.dependencies else 'None'}

Remember to follow the reasoning steps in your process:
1. Clarify Intent – restate the acceptance criteria
2. Context Scan – list all code/files/docs that might be touched
3. Plan – ordered checklist; estimate effort
4. Execute – implement the solution
5. Self-Test – validate your changes work
6. Reflect – note edge-cases missed & open follow-ups
7. Commit & PR – prepare changes for review

## CRITICAL REQUIREMENTS
1. YOU MUST INCLUDE file_changes in your response with at least one file change
2. File changes MUST INCLUDE both path and content
3. Failure to provide file changes will result in task failure
4. Every task requires code or documentation changes - NO EXCEPTIONS
5. Your changes will be automatically committed to GitHub

Please provide your response in the following structured format:
```yaml
message:
  summary: One-line status
  progress: "% complete vs. phase"
  blockers: |
    - item 1 (or null)
  next_actions: |
    - action 1
file_changes:
  - path: path/to/file
    content: |
      // File content
reasoning: |
  Detailed reasoning about your approach and decisions
```

IMPORTANT: For every task, you MUST include at least one file change in the file_changes section.
This will automatically create a Pull Request. Even for small tasks or documentation, create or modify
an appropriate file to implement your solution.

When you're done, clearly state "TASK COMPLETED" or indicate what's blocking you from completing the task.
"""

    # Agent memory to provide context
    if state.memory.get("context"):
        user_message += f"\n\n## Previous context\n{state.memory['context']}"

    # Send the request to the model
    logger.info(f"Sending request to {agent.model} for task {task.task_id}")
    try:
        response = client.chat.completions.create(
            model=agent.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=agent.temperature,
            max_tokens=agent.max_tokens
        )

        # Extract response content
        response_content = response.choices[0].message.content

        # Process response
        return process_agent_response(agent, task, response_content, state)
    except Exception as e:
        logger.exception(f"Error calling LLM API: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


def process_agent_response(
    agent: Agent,
    task: Task,
    response: str,
    state: AgentState
) -> Dict[str, Any]:
    """Process the response from the agent.

    Args:
        agent: The agent that generated the response.
        task: The task being executed.
        response: The response from the agent.
        state: The agent's state.

    Returns:
        A dictionary with the processing result.
    """
    # Check if task was completed
    if "TASK COMPLETED" in response:
        status = "completed"
    elif "BLOCKED" in response or "BLOCKER" in response:
        status = "blocked"
    else:
        status = "in_progress"

    # Try to parse YAML structure
    try:
        # Extract YAML section from response
        yaml_section = response
        if "```yaml" in response:
            yaml_parts = response.split("```yaml", 1)
            if len(yaml_parts) > 1:
                yaml_section = yaml_parts[1].split("```", 1)[0]

        # Parse YAML content
        import yaml
        parsed = yaml.safe_load(yaml_section)

        if not parsed:
            logger.warning(f"Could not parse YAML from response for task {task.task_id}")
            return {
                "status": "failed",
                "hours": 0.5,
                "error": "Failed to parse agent response format",
                "raw_response": response
            }

        # ENFORCE FILE CHANGES - Ensure every task has file changes
        if not parsed.get("file_changes") or not isinstance(
                parsed["file_changes"], list) or len(parsed["file_changes"]) == 0:
            logger.warning(f"No file changes provided for task {task.task_id} - forcing agent to retry")
            return {
                "status": "failed",
                "hours": 0.1,
                "error": "No file changes provided - each task must include code changes",
                "raw_response": response
            }

        # Process file changes if present
        file_changes = {}

        # First pass - validate paths and prepare changes
        for change in parsed["file_changes"]:
            file_path = change.get("path")
            content = change.get("content")

            if file_path and content:
                # Normalize path
                path_obj = Path(file_path)

                # If it's a relative path, make it absolute from project root
                if not path_obj.is_absolute():
                    path_obj = PROJECT_ROOT / path_obj

                # Validate path is within allowed project directories
                if not is_path_allowed(str(path_obj)):
                    logger.warning(f"Path {file_path} is not allowed, skipping")
                    continue

                # Make directories if they don't exist
                try:
                    path_obj.parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Ensuring directory exists: {path_obj.parent}")
                except (PermissionError, OSError) as e:
                    logger.error(f"Error creating directory for {file_path}: {e}")
                    continue

                # Store the file changes
                file_changes[str(path_obj)] = content

        if file_changes:
            # Commit changes to GitHub
            pr_desc = parsed.get("reasoning", "Changes made by agent")
            commit_msg = parsed.get("message", {}).get("summary", f"Update for task {task.title}")

            try:
                pr_url = commit_agent_changes(
                    agent.agent_id,
                    file_changes,
                    commit_msg,
                    pr_desc
                )
                logger.info(f"Created PR: {pr_url}")

                # Store PR URL as artifact regardless of task status
                return {
                    "status": status,
                    "hours": 1.0,
                    "artifacts": [pr_url],
                    "message": parsed.get("message", {})
                }
            except Exception as e:
                logger.error(f"Error committing changes: {e}")

                # If GitHub commit fails, write files locally
                try:
                    for file_path, content in file_changes.items():
                        with open(file_path, 'w') as f:
                            f.write(content)
                        logger.info(f"Created local file: {file_path}")
                except Exception as local_e:
                    logger.error(f"Error writing local files: {local_e}")

        # Update agent memory with context if provided
        if "reasoning" in parsed:
            state.memory["context"] = parsed["reasoning"]
            save_agent_state(state)

        # Return processed result
        return {
            "status": status,
            "hours": 0.5,
            "message": parsed.get("message", {}),
            "raw_response": response
        }
    except Exception as e:
        logger.exception(f"Error processing agent response: {e}")
        return {
            "status": status,
            "hours": 0.5,
            "error": str(e),
            "raw_response": response
        }


def run_all_agents() -> None:
    """Run all agents on available tasks."""
    # Check for stalled tasks first
    check_stalled_tasks()

    # Get all agents
    for agent_id, agent in AGENT_MAP.items():
        state = get_agent_state(agent_id)
        if not state:
            logger.warning(f"State for agent {agent_id} not found, initializing...")
            state = AgentState(agent_id=agent_id)
            save_agent_state(state)

        # Skip agents that are already working
        if state.status == "working":
            logger.info(f"Agent {agent.name} is already working on a task, skipping")
            continue

        # Check if this agent has an active task
        if state.current_task_id:
            task = get_task(state.current_task_id)
            if task and task.status == TaskStatus.IN_PROGRESS:
                # Check if task has timed out
                timeout = timedelta(hours=TASK_TIMEOUT_HOURS)
                if datetime.now() - task.updated_at > timeout:
                    logger.warning(f"Task {task.task_id} has timed out for agent {agent_id}, marking as failed")
                    task.status = TaskStatus.FAILED
                    task.updated_at = datetime.now()
                    save_task(task)

                    state.current_task_id = None
                    state.status = "idle"
                    state.last_activity = datetime.now()
                    save_agent_state(state)
                else:
                    # Continue working on current task
                    run_agent(agent_id, task.task_id)
                    continue

        # Get next available task
        available_tasks = get_available_tasks(agent_id)
        if not available_tasks:
            # Check for failed tasks to retry
            failed_tasks = get_failed_tasks(agent_id)
            if failed_tasks:
                logger.info(f"Found {len(failed_tasks)} failed tasks for agent {agent.name}, retrying...")
                # Reset the first failed task to PENDING and assign it
                task = failed_tasks[0]
                task.status = TaskStatus.PENDING
                task.updated_at = datetime.now()
                task.retry_count = getattr(task, 'retry_count', 0) + 1

                # Only retry up to 3 times
                if task.retry_count <= 3:
                    save_task(task)
                    logger.info(f"Retrying task {task.title} (attempt {task.retry_count}/3)")
                    run_agent(agent_id, task.task_id)
                else:
                    logger.warning(f"Task {task.title} has failed {task.retry_count} times, giving up")
                    continue
            else:
                logger.info(f"No available tasks for agent {agent.name}")
                continue
        else:
            # Run agent on next task
            run_agent(agent_id, available_tasks[0].task_id)


def check_stalled_tasks() -> None:
    """Check for tasks that might be stalled and reset them."""
    # Get all in-progress tasks
    tasks = get_all_tasks()
    in_progress_tasks = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]

    for task in in_progress_tasks:
        # Check if the task has been updated in the last 2 hours
        timeout = timedelta(hours=2)
        if datetime.now() - task.updated_at > timeout:
            logger.warning(f"Task {task.task_id} ({task.title}) appears to be stalled, resetting to PENDING")

            # Get the agent state to update it
            agent_id = task.assigned_agent_id
            state = get_agent_state(agent_id)

            if state and state.current_task_id == task.task_id:
                # Reset agent state
                state.current_task_id = None
                state.status = "idle"
                state.last_activity = datetime.now()
                save_agent_state(state)

            # Reset the task
            task.status = TaskStatus.PENDING
            task.updated_at = datetime.now()
            task.retry_count = getattr(task, 'retry_count', 0) + 1
            save_task(task)


def get_failed_tasks(agent_id: str) -> List[Task]:
    """Get failed tasks for an agent.

    Args:
        agent_id: The ID of the agent to get failed tasks for.

    Returns:
        A list of failed tasks for the agent.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all failed tasks for this agent
    cursor.execute(
        "SELECT * FROM tasks WHERE assigned_agent_id = ? AND status = ? ORDER BY priority DESC",
        (agent_id, TaskStatus.FAILED.value)
    )

    tasks = []
    for row in cursor.fetchall():
        tasks.append(Task.from_dict(dict(row)))

    conn.close()
    return tasks


def main():
    """Main entry point for the agent runner."""
    parser = argparse.ArgumentParser(description="Run the agent system")
    parser.add_argument(
        "--initialize",
        action="store_true",
        help="Initialize agents and tasks"
    )
    parser.add_argument(
        "--agent",
        type=str,
        help="Run a specific agent by ID"
    )
    parser.add_argument(
        "--task",
        type=str,
        help="Run a specific task by ID"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run in daemon mode (continuous operation)"
    )

    args = parser.parse_args()

    # Check if OpenAI API key is set
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return

    # Initialize if requested
    if args.initialize:
        logger.info("Initializing agent system...")
        initialize_agents()
        initialize_tasks()
        logger.info("Initialization complete")

    # Run specific agent and task if provided
    if args.agent and args.task:
        logger.info(f"Running agent {args.agent} on task {args.task}")
        run_agent(args.agent, args.task)
    elif args.agent:
        logger.info(f"Running agent {args.agent} on next available task")
        run_agent(args.agent)
    elif args.daemon:
        logger.info("Starting daemon mode")
        try:
            while True:
                run_all_agents()
                time.sleep(60)  # Check for new tasks every minute
        except KeyboardInterrupt:
            logger.info("Daemon stopped by user")
    else:
        logger.info("Running all agents once")
        run_all_agents()


if __name__ == "__main__":
    main()
