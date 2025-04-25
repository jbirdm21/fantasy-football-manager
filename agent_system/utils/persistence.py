"""Persistence utilities for storing agent and task states."""
import json
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import sqlite3
from pathlib import Path

from agent_system.agents.models import Agent, AgentState, Task, TaskStatus
from agent_system.config import AGENT_OUTPUTS_DIR, PROJECT_ROOT


# Database setup
DB_PATH = AGENT_OUTPUTS_DIR / "agent_system.db"


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


def save_task(task: Task) -> None:
    """Save task to the database.
    
    Args:
        task: The task to save.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Convert lists and datetimes to strings
    acceptance_criteria_json = json.dumps(task.acceptance_criteria)
    dependencies_json = json.dumps(task.dependencies)
    artifacts_json = json.dumps(task.artifacts)
    created_at_str = _serialize_datetime(task.created_at)
    updated_at_str = _serialize_datetime(task.updated_at)
    
    cursor.execute(
        '''
        INSERT OR REPLACE INTO tasks
        (task_id, title, description, acceptance_criteria, priority, assigned_agent_id,
         status, dependencies, created_at, updated_at, estimated_hours, actual_hours,
         roadmap_phase, artifacts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            task.task_id,
            task.title,
            task.description,
            acceptance_criteria_json,
            task.priority,
            task.assigned_agent_id,
            task.status,
            dependencies_json,
            created_at_str,
            updated_at_str,
            task.estimated_hours,
            task.actual_hours,
            task.roadmap_phase,
            artifacts_json
        )
    )
    
    conn.commit()
    conn.close()


def get_task(task_id: str) -> Optional[Task]:
    """Get task from the database.
    
    Args:
        task_id: ID of the task to get.
        
    Returns:
        The task if found, None otherwise.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute(
        '''
        SELECT task_id, title, description, acceptance_criteria, priority, assigned_agent_id,
               status, dependencies, created_at, updated_at, estimated_hours, actual_hours, 
               roadmap_phase, artifacts
        FROM tasks WHERE task_id = ?
        ''',
        (task_id,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    # Deserialize JSON and datetime
    (
        task_id, title, description, acceptance_criteria_json, priority, assigned_agent_id,
        status, dependencies_json, created_at_str, updated_at_str, estimated_hours, actual_hours,
        roadmap_phase, artifacts_json
    ) = row
    
    acceptance_criteria = json.loads(acceptance_criteria_json)
    dependencies = json.loads(dependencies_json)
    artifacts = json.loads(artifacts_json)
    created_at = _deserialize_datetime(created_at_str)
    updated_at = _deserialize_datetime(updated_at_str)
    
    return Task(
        task_id=task_id,
        title=title,
        description=description,
        acceptance_criteria=acceptance_criteria,
        priority=priority,
        assigned_agent_id=assigned_agent_id,
        status=TaskStatus(status),
        dependencies=dependencies,
        created_at=created_at,
        updated_at=updated_at,
        estimated_hours=estimated_hours,
        actual_hours=actual_hours,
        roadmap_phase=roadmap_phase,
        artifacts=artifacts
    )


def get_all_tasks() -> List[Task]:
    """Get all tasks from the database.
    
    Returns:
        List of all tasks.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute(
        '''
        SELECT task_id, title, description, acceptance_criteria, priority, assigned_agent_id,
               status, dependencies, created_at, updated_at, estimated_hours, actual_hours, 
               roadmap_phase, artifacts
        FROM tasks
        '''
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    tasks = []
    for row in rows:
        (
            task_id, title, description, acceptance_criteria_json, priority, assigned_agent_id,
            status, dependencies_json, created_at_str, updated_at_str, estimated_hours, actual_hours,
            roadmap_phase, artifacts_json
        ) = row
        
        acceptance_criteria = json.loads(acceptance_criteria_json)
        dependencies = json.loads(dependencies_json)
        artifacts = json.loads(artifacts_json)
        created_at = _deserialize_datetime(created_at_str)
        updated_at = _deserialize_datetime(updated_at_str)
        
        task = Task(
            task_id=task_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            priority=priority,
            assigned_agent_id=assigned_agent_id,
            status=TaskStatus(status),
            dependencies=dependencies,
            created_at=created_at,
            updated_at=updated_at,
            estimated_hours=estimated_hours,
            actual_hours=actual_hours,
            roadmap_phase=roadmap_phase,
            artifacts=artifacts
        )
        tasks.append(task)
    
    return tasks


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