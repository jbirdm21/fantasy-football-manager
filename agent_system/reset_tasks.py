#!/usr/bin/env python
"""Script to reset tasks from completed/failed status back to pending."""
import sqlite3
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("task_reset")

# Database path
DB_PATH = Path(__file__).parent / "outputs" / "agent_system.db"


def connect_db() -> sqlite3.Connection:
    """Connect to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_tasks(conn: sqlite3.Connection, status: Optional[str] = None) -> List[dict]:
    """Get tasks from the database, optionally filtered by status.

    Args:
        conn: Database connection
        status: Optional status filter (e.g., 'COMPLETED')

    Returns:
        List of tasks as dictionaries
    """
    query = "SELECT * FROM tasks"
    if status:
        query += f" WHERE status = '{status}'"

    cursor = conn.cursor()
    cursor.execute(query)
    return [dict(row) for row in cursor.fetchall()]


def update_task_status(conn: sqlite3.Connection, task_id: str, new_status: str) -> None:
    """Update the status of a task.

    Args:
        conn: Database connection
        task_id: ID of the task to update
        new_status: New status for the task
    """
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET status = ?, updated_at = ? WHERE task_id = ?",
        (new_status, datetime.now().isoformat(), task_id)
    )
    conn.commit()


def clear_agent_completed_tasks(conn: sqlite3.Connection) -> None:
    """Clear the completed_tasks list for all agents.

    Args:
        conn: Database connection
    """
    cursor = conn.cursor()

    # First get all agent states
    cursor.execute("SELECT * FROM agent_states")
    agent_states = [dict(row) for row in cursor.fetchall()]

    # Update each agent state to clear completed tasks
    for state in agent_states:
        agent_id = state['agent_id']

        # Reset current_task_id if it exists
        if state.get('current_task_id'):
            cursor.execute(
                "UPDATE agent_states SET current_task_id = NULL WHERE agent_id = ?",
                (agent_id,)
            )

        # Reset completed_tasks to empty list
        cursor.execute(
            "UPDATE agent_states SET completed_tasks = '[]' WHERE agent_id = ?",
            (agent_id,)
        )

    conn.commit()


def main():
    """Main function to reset tasks."""
    parser = argparse.ArgumentParser(description="Reset tasks status")
    parser.add_argument(
        "--status",
        default="COMPLETED",
        help="Status to reset (default: COMPLETED)"
    )
    parser.add_argument(
        "--new-status",
        default="PENDING",
        help="New status to set (default: PENDING)"
    )
    parser.add_argument(
        "--task-id",
        help="Reset a specific task ID (optional)"
    )
    parser.add_argument(
        "--clear-agent-tasks",
        action="store_true",
        help="Clear completed tasks from agent states"
    )

    args = parser.parse_args()

    # Connect to database
    conn = connect_db()

    try:
        if args.task_id:
            # Reset a specific task
            update_task_status(conn, args.task_id, args.new_status)
            logger.info(f"Reset task {args.task_id} to {args.new_status}")
        else:
            # Get all tasks with the specified status
            tasks = get_tasks(conn, args.status)
            logger.info(f"Found {len(tasks)} tasks with status {args.status}")

            # Reset each task
            for task in tasks:
                update_task_status(conn, task['task_id'], args.new_status)
                logger.info(f"Reset task {task['task_id']} ({task['title']}) to {args.new_status}")

        # Clear agent completed tasks if requested
        if args.clear_agent_tasks:
            clear_agent_completed_tasks(conn)
            logger.info("Cleared completed tasks from all agent states")

        logger.info("Task reset complete")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
