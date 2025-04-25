"""Persistence utilities for storing agent and task states."""
import json
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import sqlite3
from pathlib import Path
import logging

from agent_system.agents.models import Agent, AgentState, Task, TaskStatus
from agent_system.config import AGENT_OUTPUTS_DIR, PROJECT_ROOT


# Database setup
DB_PATH = AGENT_OUTPUTS_DIR / "agent_system.db"

# Set up logger
logger = logging.getLogger(__name__)

# Get the storage directory
STORAGE_DIR = Path(__file__).parent.parent / "storage"
TASKS_FILE = STORAGE_DIR / "tasks.json"

# Ensure storage directory exists
os.makedirs(STORAGE_DIR, exist_ok=True)


def init_database():
    """Initialize the SQLite database for agent system."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Create agent_states table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agent_states (
        agent_id TEXT PRIMARY KEY,
        status TEXT,
        current_task_id TEXT,
        last_activity TEXT,
        completed_tasks TEXT,
        memory TEXT
    )
    ''')

    # Create tasks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        title TEXT,
        description TEXT,
        acceptance_criteria TEXT,
        priority INTEGER,
        assigned_agent_id TEXT,
        status TEXT,
        dependencies TEXT,
        created_at TEXT,
        updated_at TEXT,
        estimated_hours REAL,
        actual_hours REAL,
        roadmap_phase TEXT,
        artifacts TEXT
    )
    ''')

    conn.commit()
    conn.close()


def _serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format string."""
    return dt.isoformat()


def _deserialize_datetime(dt_str: str) -> datetime:
    """Deserialize ISO format string to datetime."""
    return datetime.fromisoformat(dt_str)


def save_agent_state(agent_state: AgentState) -> None:
    """Save agent state to the database.

    Args:
        agent_state: The agent state to save.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Convert datetime to string and lists/dicts to JSON
    completed_tasks_json = json.dumps(agent_state.completed_tasks)
    memory_json = json.dumps(agent_state.memory)
    last_activity_str = _serialize_datetime(agent_state.last_activity)

    cursor.execute(
        '''
        INSERT OR REPLACE INTO agent_states
        (agent_id, status, current_task_id, last_activity, completed_tasks, memory)
        VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (
            agent_state.agent_id,
            agent_state.status,
            agent_state.current_task_id,
            last_activity_str,
            completed_tasks_json,
            memory_json
        )
    )

    conn.commit()
    conn.close()


def get_agent_state(agent_id: str) -> Optional[AgentState]:
    """Get agent state from the database.

    Args:
        agent_id: ID of the agent to get state for.

    Returns:
        The agent state if found, None otherwise.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute(
        'SELECT agent_id, status, current_task_id, last_activity, completed_tasks, memory FROM agent_states WHERE agent_id = ?',
        (agent_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    # Deserialize JSON and datetime
    agent_id, status, current_task_id, last_activity_str, completed_tasks_json, memory_json = row
    completed_tasks = json.loads(completed_tasks_json)
    memory = json.loads(memory_json)
    last_activity = _deserialize_datetime(last_activity_str)

    return AgentState(
        agent_id=agent_id,
        status=status,
        current_task_id=current_task_id,
        last_activity=last_activity,
        completed_tasks=completed_tasks,
        memory=memory
    )


def save_task(task) -> bool:
    """Save a task to persistent storage.

    Args:
        task: The task object to save

    Returns:
        True if successful, False otherwise
    """
    try:
        # Load existing tasks
        tasks = load_tasks()

        # Convert task to dictionary for storage
        task_dict = task.to_dict()

        # Update or add task
        tasks[task.id] = task_dict

        # Save tasks
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)

        logger.info(f"Task {task.id} saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving task: {e}")
        return False


def load_tasks() -> Dict[str, Any]:
    """Load all tasks from storage.

    Returns:
        Dictionary of task data by task ID
    """
    try:
        if not TASKS_FILE.exists():
            return {}

        with open(TASKS_FILE, 'r') as f:
            tasks = json.load(f)

        return tasks

    except Exception as e:
        logger.error(f"Error loading tasks: {e}")
        return {}


def get_task(task_id: str) -> Optional[Any]:
    """Get a specific task by ID.

    Args:
        task_id: The ID of the task to get

    Returns:
        Task object if found, None otherwise
    """
    try:
        tasks = load_tasks()

        if task_id not in tasks:
            return None

        # Import here to avoid circular imports
        from agent_system.agents.models import Task

        # Create task object from dictionary
        return Task.from_dict(tasks[task_id])

    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        return None


def get_all_tasks() -> List[Any]:
    """Get all tasks.

    Returns:
        List of task objects
    """
    try:
        tasks = load_tasks()

        # Import here to avoid circular imports
        from agent_system.agents.models import Task

        # Create task objects from dictionaries
        return [Task.from_dict(task_data) for task_data in tasks.values()]

    except Exception as e:
        logger.error(f"Error getting all tasks: {e}")
        return []


def delete_task(task_id: str) -> bool:
    """Delete a task.

    Args:
        task_id: The ID of the task to delete

    Returns:
        True if successful, False otherwise
    """
    try:
        tasks = load_tasks()

        if task_id not in tasks:
            return False

        # Remove task
        del tasks[task_id]

        # Save tasks
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)

        logger.info(f"Task {task_id} deleted successfully")
        return True

    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        return False


def get_available_tasks(agent_id: str) -> List[Task]:
    """Get tasks that are available for an agent to work on.

    Args:
        agent_id: ID of the agent to get tasks for.

    Returns:
        List of tasks that the agent can work on.
    """
    all_tasks = get_all_tasks()

    # Filter to pending tasks assigned to this agent
    agent_tasks = [t for t in all_tasks if t.assigned_agent_id == agent_id and t.status == TaskStatus.PENDING]

    # Check dependencies
    available_tasks = []
    for task in agent_tasks:
        dependencies_met = True
        for dep_id in task.dependencies:
            dep_task = next((t for t in all_tasks if t.task_id == dep_id), None)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                dependencies_met = False
                break

        if dependencies_met:
            available_tasks.append(task)

    # Sort by priority (lower number = higher priority)
    return sorted(available_tasks, key=lambda t: t.priority)


def update_task_status(task_id: str, status: TaskStatus) -> None:
    """Update the status of a task.

    Args:
        task_id: ID of the task to update.
        status: New status for the task.
    """
    task = get_task(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")

    task.status = status
    task.updated_at = datetime.now()
    save_task(task)


def log_agent_activity(agent_id: str, message: str, level: str = "INFO") -> None:
    """Log agent activity to a file.

    Args:
        agent_id: ID of the agent.
        message: Log message.
        level: Log level (INFO, WARNING, ERROR, etc.).
    """
    log_dir = AGENT_OUTPUTS_DIR / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"{agent_id}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] [{level}] {message}\n")


# Initialize the database
init_database()
