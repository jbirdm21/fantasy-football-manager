from agent_system.config import PROJECT_ROOT
from agent_system.agents.models import Task, TaskStatus
from typing import List, Dict, Any, Tuple
from pathlib import Path
import uuid
import re
import logging

logger = logging.getLogger(__name__)
"""Module for parsing the project roadmap and generating tasks."""


def read_roadmap_file() -> str:
    """Read the roadmap markdown file from the docs directory.

    Returns:
        The content of the roadmap file as a string.
    """
    roadmap_path = PROJECT_ROOT / "docs" / "ROADMAP.md"
    if not roadmap_path.exists():
        raise FileNotFoundError(f"Roadmap file not found at {roadmap_path}")

    return roadmap_path.read_text()


def parse_phases(roadmap_content: str) -> List[Dict[str, Any]]:
    """Parse the roadmap content to extract phases.

    Args:
        roadmap_content: The content of the roadmap file as a string.

    Returns:
        A list of dictionaries, each representing a phase with its tasks.
    """
    # Find all phase sections in the roadmap
    phase_pattern = r"## Phase (\d+): ([^(]+) \(Target: ([^)]+)\)([\s\S]*?)(?=## Phase \d+:|$)"
    phase_matches = re.finditer(phase_pattern, roadmap_content)

    phases = []
    for match in phase_matches:
        phase_num = match.group(1)
        phase_name = match.group(2).strip()
        target_date = match.group(3).strip()
        phase_content = match.group(4).strip()

        # Parse tasks within this phase
        tasks = parse_tasks(phase_content, f"P{phase_num}. {phase_name}")

        phases.append({
            "phase_id": f"phase-{phase_num}",
            "phase_number": int(phase_num),
            "name": phase_name,
            "target_date": target_date,
            "tasks": tasks
        })

    return phases


def parse_tasks(phase_content: str, phase_name: str) -> List[Dict[str, Any]]:
    """Parse tasks from the phase content.

    Args:
        phase_content: The content of the phase section.
        phase_name: The name of the phase.

    Returns:
        A list of dictionaries, each representing a task.
    """
    tasks = []

    # Find all top-level task items
    task_pattern = r"- \[ \] ([^-\n]+)(?:[\s\S]*?(?=- \[ \]|$))"
    task_matches = re.finditer(task_pattern, phase_content)

    for i, match in enumerate(task_matches):
        task_name = match.group(1).strip()
        full_task_text = match.group(0).strip()

        # Find subtasks if they exist
        subtask_pattern = r"  - \[ \] ([^\n]+)"
        subtasks = re.findall(subtask_pattern, full_task_text)

        # Create acceptance criteria from subtasks or task itself
        acceptance_criteria = []
        if subtasks:
            acceptance_criteria = subtasks
        else:
            acceptance_criteria = [f"Implement {task_name} successfully"]

        # Generate a description from task name and subtasks
        description = f"Implement {task_name} for the fantasy football manager project."
        if subtasks:
            description += "\n\nThis task includes the following subtasks:\n"
            for subtask in subtasks:
                description += f"- {subtask}\n"

        tasks.append({
            "task_id": f"task-{uuid.uuid4()}",
            "title": task_name,
            "description": description,
            "acceptance_criteria": acceptance_criteria,
            "priority": i + 1,  # Priority based on order in roadmap
            "roadmap_phase": phase_name,
            "status": TaskStatus.PENDING
        })

    return tasks


def generate_tasks_from_roadmap() -> List[Task]:
    """Generate Task objects from the project roadmap.

    Returns:
        A list of Task objects derived from the roadmap.
    """
    roadmap_content = read_roadmap_file()
    phases = parse_phases(roadmap_content)

    # Flatten phase tasks into a single list
    all_tasks = []
    for phase in phases:
        for task_dict in phase.get("tasks", []):
            # Create Task instance from dictionary
            task = Task(**task_dict)
            all_tasks.append(task)

    # Add dependencies between tasks (each task depends on all tasks in previous phases)
    phase_tasks: Dict[int, List[Task]] = {}
    for phase in phases:
        phase_num = phase["phase_number"]
        phase_tasks[phase_num] = []
        for task_dict in phase.get("tasks", []):
            task_id = task_dict["task_id"]
            task = next((t for t in all_tasks if t.task_id == task_id), None)
            if task:
                phase_tasks[phase_num].append(task)

    # Add dependencies
    for phase_num in sorted(phase_tasks.keys()):
        if phase_num == 0:  # Skip dependencies for bootstrap phase
            continue

        current_phase_tasks = phase_tasks[phase_num]
        previous_phase_tasks = phase_tasks.get(phase_num - 1, [])

        for task in current_phase_tasks:
            task.dependencies.extend([prev_task.task_id for prev_task in previous_phase_tasks])

    return all_tasks


def assign_tasks_to_agents(tasks: List[Task], agent_specialization_map: Dict[str, List[str]]) -> List[Task]:
    """Assign tasks to agents based on task content and agent specializations.

    Args:
        tasks: List of tasks to assign.
        agent_specialization_map: Map of agent_id to list of specializations.

    Returns:
        The same list of tasks, but with assigned_agent_id populated.
    """
    # Simple keyword-based assignment for now
    keyword_to_agent: Dict[str, str] = {}

    # Build a reverse index from keywords to agents
    for agent_id, specializations in agent_specialization_map.items():
        for spec in specializations:
            keyword_to_agent[spec.lower()] = agent_id

    # Add role-based keywords
    keyword_to_agent.update({
        "backend": "backend-dev-1",
        "frontend": "frontend-dev-1",
        "api": "backend-dev-1",
        "database": "backend-dev-1",
        "ui": "frontend-dev-1",
        "data": "data-scientist-1",
        "model": "data-scientist-1",
        "prediction": "data-scientist-1",
        "devops": "devops-eng-1",
        "deployment": "devops-eng-1",
        "test": "qa-eng-1",
        "quality": "qa-eng-1",
        "architecture": "tech-lead-1",
        "design": "tech-lead-1",
    })

    for task in tasks:
        # Combine title and description for matching
        text = f"{task.title} {task.description}".lower()

        # Count matches for each agent
        agent_matches = {}
        for keyword, agent_id in keyword_to_agent.items():
            matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
            agent_matches[agent_id] = agent_matches.get(agent_id, 0) + matches

        # Find agent with most matches
        if agent_matches:
            best_agent = max(agent_matches.items(), key=lambda x: x[1])
            if best_agent[1] > 0:  # Only assign if there's at least one match
                task.assigned_agent_id = best_agent[0]

        # If no assignment was made, delegate to the tech lead
        if not task.assigned_agent_id:
            task.assigned_agent_id = "tech-lead-1"

    return tasks


if __name__ == "__main__":
    # Test the roadmap parser
    tasks = generate_tasks_from_roadmap()
    logger.info(f"Generated {len(tasks)} tasks from roadmap")
    for task in tasks:
        logger.info(f"- {task.title} (Phase: {task.roadmap_phase})")

    # Example agent specialization map
    agent_spec_map = {
        "backend-dev-1": ["python", "fastapi", "sql", "api"],
        "frontend-dev-1": ["react", "nextjs", "ui"],
        "data-scientist-1": ["machine learning", "data", "python"],
        "devops-eng-1": ["docker", "deployment", "ci/cd"],
        "tech-lead-1": ["architecture", "design", "review"],
        "qa-eng-1": ["testing", "quality", "validation"]
    }

    assigned_tasks = assign_tasks_to_agents(tasks, agent_spec_map)
    logger.info("\nTask assignments:")
    for task in assigned_tasks:
        logger.info(f"- {task.title} -> {task.assigned_agent_id}")
