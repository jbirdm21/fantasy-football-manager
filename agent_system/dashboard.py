"""Simple web dashboard for monitoring the agent system."""
import os
import time
import json
from datetime import datetime
from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from agent_system.agents.models import TaskStatus
from agent_system.agents.definitions import AGENTS, AGENT_MAP
from agent_system.utils.persistence import (
    get_agent_state, get_task, get_all_tasks, update_task_status
)
from agent_system.config import AGENT_OUTPUTS_DIR


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("dashboard")

# Create FastAPI app
app = FastAPI(
    title="Agent System Dashboard",
    description="Dashboard for monitoring the agent system",
    version="0.1.0",
)

# Create templates directory
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)

# Create static directory
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

# Create base template
base_template = templates_dir / "base.html"
if not base_template.exists():
    base_template.write_text("""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Agent System Dashboard{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .task-pending { background-color: #f8f9fa; }
        .task-in-progress { background-color: #cff4fc; }
        .task-completed { background-color: #d1e7dd; }
        .task-failed { background-color: #f8d7da; }
        .task-blocked { background-color: #fff3cd; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">Agent System Dashboard</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Home</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/agents">Agents</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/tasks">Tasks</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/logs">Logs</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Auto-refresh the page every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
""")

# Create index template
index_template = templates_dir / "index.html"
if not index_template.exists():
    index_template.write_text("""{% extends "base.html" %}

{% block content %}
<h1>Agent System Dashboard</h1>

<div class="row mt-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Agents</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Role</th>
                                <th>Status</th>
                                <th>Current Task</th>
                                <th>Last Activity</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for agent in agents %}
                            <tr>
                                <td>{{ agent.name }}</td>
                                <td>{{ agent.role }}</td>
                                <td>{{ agent.status }}</td>
                                <td>
                                    {% if agent.current_task %}
                                    <a href="/tasks/{{ agent.current_task.task_id }}">{{ agent.current_task.title }}</a>
                                    {% else %}
                                    -
                                    {% endif %}
                                </td>
                                <td>{{ agent.last_activity }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Task Summary</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Status</th>
                                <th>Count</th>
                                <th>Percentage</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for status, count in task_summary.items() %}
                            <tr class="task-{{ status.lower() }}">
                                <td>{{ status }}</td>
                                <td>{{ count }}</td>
                                <td>{{ (count / task_summary_total * 100) | round(1) }}%</td>
                            </tr>
                            {% endfor %}
                            <tr>
                                <td><strong>Total</strong></td>
                                <td><strong>{{ task_summary_total }}</strong></td>
                                <td>100%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="card mt-4">
            <div class="card-header">
                <h5>Phase Progress</h5>
            </div>
            <div class="card-body">
                {% for phase, progress in phase_progress.items() %}
                <h6>{{ phase }}</h6>
                <div class="progress mb-3">
                    <div class="progress-bar" role="progressbar" style="width: {{ progress }}%">
                        {{ progress }}%
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
""")

# Create agents template
agents_template = templates_dir / "agents.html"
if not agents_template.exists():
    agents_template.write_text("""{% extends "base.html" %}

{% block content %}
<h1>Agents</h1>

<div class="row mt-4">
    {% for agent in agents %}
    <div class="col-md-6 mb-4">
        <div class="card">
            <div class="card-header">
                <h5>{{ agent.name }} ({{ agent.role }})</h5>
            </div>
            <div class="card-body">
                <p><strong>Status:</strong> {{ agent.status }}</p>
                <p><strong>Last Activity:</strong> {{ agent.last_activity }}</p>
                
                {% if agent.current_task %}
                <p><strong>Current Task:</strong> <a href="/tasks/{{ agent.current_task.task_id }}">{{ agent.current_task.title }}</a></p>
                {% endif %}
                
                <h6>Completed Tasks</h6>
                {% if agent.completed_tasks %}
                <ul>
                    {% for task in agent.completed_tasks %}
                    <li><a href="/tasks/{{ task.task_id }}">{{ task.title }}</a></li>
                    {% endfor %}
                </ul>
                {% else %}
                <p>No completed tasks yet.</p>
                {% endif %}
                
                <h6>Specializations</h6>
                <ul>
                    {% for spec in agent.specializations %}
                    <li>{{ spec }}</li>
                    {% endfor %}
                </ul>
                
                <div class="mt-3">
                    <a href="/agents/{{ agent.agent_id }}/run" class="btn btn-primary btn-sm">Run Agent</a>
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
""")

# Create tasks template
tasks_template = templates_dir / "tasks.html"
if not tasks_template.exists():
    tasks_template.write_text("""{% extends "base.html" %}

{% block content %}
<h1>Tasks</h1>

<div class="mb-3">
    <div class="btn-group" role="group">
        <a href="/tasks" class="btn btn-outline-primary {% if not filter %}active{% endif %}">All</a>
        <a href="/tasks?filter=pending" class="btn btn-outline-primary {% if filter == 'pending' %}active{% endif %}">Pending</a>
        <a href="/tasks?filter=in_progress" class="btn btn-outline-primary {% if filter == 'in_progress' %}active{% endif %}">In Progress</a>
        <a href="/tasks?filter=completed" class="btn btn-outline-primary {% if filter == 'completed' %}active{% endif %}">Completed</a>
        <a href="/tasks?filter=failed" class="btn btn-outline-primary {% if filter == 'failed' %}active{% endif %}">Failed</a>
        <a href="/tasks?filter=blocked" class="btn btn-outline-primary {% if filter == 'blocked' %}active{% endif %}">Blocked</a>
    </div>
</div>

<div class="table-responsive">
    <table class="table table-striped">
        <thead>
            <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Assigned To</th>
                <th>Priority</th>
                <th>Phase</th>
                <th>Updated</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for task in tasks %}
            <tr class="task-{{ task.status.lower() }}">
                <td><a href="/tasks/{{ task.task_id }}">{{ task.title }}</a></td>
                <td>{{ task.status }}</td>
                <td>{{ task.assigned_to }}</td>
                <td>{{ task.priority }}</td>
                <td>{{ task.roadmap_phase }}</td>
                <td>{{ task.updated_at }}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <a href="/tasks/{{ task.task_id }}/run" class="btn btn-primary">Run</a>
                        <button type="button" class="btn btn-primary dropdown-toggle dropdown-toggle-split" data-bs-toggle="dropdown"></button>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="/tasks/{{ task.task_id }}/status/pending">Mark Pending</a></li>
                            <li><a class="dropdown-item" href="/tasks/{{ task.task_id }}/status/in_progress">Mark In Progress</a></li>
                            <li><a class="dropdown-item" href="/tasks/{{ task.task_id }}/status/completed">Mark Completed</a></li>
                            <li><a class="dropdown-item" href="/tasks/{{ task.task_id }}/status/failed">Mark Failed</a></li>
                            <li><a class="dropdown-item" href="/tasks/{{ task.task_id }}/status/blocked">Mark Blocked</a></li>
                        </ul>
                    </div>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
""")

# Create task detail template
task_detail_template = templates_dir / "task_detail.html"
if not task_detail_template.exists():
    task_detail_template.write_text("""{% extends "base.html" %}

{% block content %}
<h1>Task: {{ task.title }}</h1>

<div class="card mb-4">
    <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
            <h5>Task Details</h5>
            <div class="btn-group btn-group-sm">
                <a href="/tasks/{{ task.task_id }}/run" class="btn btn-primary">Run Task</a>
                <button type="button" class="btn btn-primary dropdown-toggle dropdown-toggle-split" data-bs-toggle="dropdown"></button>
                <ul class="dropdown-menu">
                    <li><a class="dropdown-item" href="/tasks/{{ task.task_id }}/status/pending">Mark Pending</a></li>
                    <li><a class="dropdown-item" href="/tasks/{{ task.task_id }}/status/in_progress">Mark In Progress</a></li>
                    <li><a class="dropdown-item" href="/tasks/{{ task.task_id }}/status/completed">Mark Completed</a></li>
                    <li><a class="dropdown-item" href="/tasks/{{ task.task_id }}/status/failed">Mark Failed</a></li>
                    <li><a class="dropdown-item" href="/tasks/{{ task.task_id }}/status/blocked">Mark Blocked</a></li>
                </ul>
            </div>
        </div>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-6">
                <p><strong>ID:</strong> {{ task.task_id }}</p>
                <p><strong>Status:</strong> <span class="badge bg-{{ task_status_color }}">{{ task.status }}</span></p>
                <p><strong>Assigned To:</strong> {{ task.assigned_to }}</p>
                <p><strong>Priority:</strong> {{ task.priority }}</p>
                <p><strong>Phase:</strong> {{ task.roadmap_phase }}</p>
                <p><strong>Created:</strong> {{ task.created_at }}</p>
                <p><strong>Updated:</strong> {{ task.updated_at }}</p>
                <p><strong>Estimated Hours:</strong> {{ task.estimated_hours if task.estimated_hours else "N/A" }}</p>
                <p><strong>Actual Hours:</strong> {{ task.actual_hours if task.actual_hours else "N/A" }}</p>
            </div>
            <div class="col-md-6">
                <h6>Description</h6>
                <p>{{ task.description }}</p>
                
                <h6>Acceptance Criteria</h6>
                <ul>
                    {% for criterion in task.acceptance_criteria %}
                    <li>{{ criterion }}</li>
                    {% endfor %}
                </ul>
                
                <h6>Dependencies</h6>
                {% if task.dependencies %}
                <ul>
                    {% for dep in task.dependencies %}
                    <li><a href="/tasks/{{ dep.task_id }}">{{ dep.title }}</a></li>
                    {% endfor %}
                </ul>
                {% else %}
                <p>No dependencies</p>
                {% endif %}
            </div>
        </div>
        
        {% if task.artifacts %}
        <h6 class="mt-3">Artifacts</h6>
        <ul>
            {% for artifact in task.artifacts %}
            <li><a href="{{ artifact }}" target="_blank">{{ artifact }}</a></li>
            {% endfor %}
        </ul>
        {% endif %}
    </div>
</div>

{% if agent_logs %}
<div class="card">
    <div class="card-header">
        <h5>Agent Logs</h5>
    </div>
    <div class="card-body">
        <div class="bg-dark text-light p-3 rounded" style="max-height: 400px; overflow-y: auto;">
            <pre>{{ agent_logs }}</pre>
        </div>
    </div>
</div>
{% endif %}
{% endblock %}
""")

# Create logs template
logs_template = templates_dir / "logs.html"
if not logs_template.exists():
    logs_template.write_text("""{% extends "base.html" %}

{% block content %}
<h1>Agent Logs</h1>

<div class="mb-3">
    <div class="btn-group" role="group">
        {% for agent_id, agent_name in agent_options.items() %}
        <a href="/logs?agent={{ agent_id }}" class="btn btn-outline-primary {% if agent_id == selected_agent %}active{% endif %}">{{ agent_name }}</a>
        {% endfor %}
    </div>
</div>

<div class="card">
    <div class="card-header">
        <h5>Logs for {{ agent_name }}</h5>
    </div>
    <div class="card-body">
        <div class="bg-dark text-light p-3 rounded" style="max-height: 600px; overflow-y: auto;">
            <pre>{{ logs }}</pre>
        </div>
    </div>
</div>
{% endblock %}
""")

# Set up Jinja2 templates
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the dashboard index page."""
    # Get agent states
    agents_data = []
    for agent_id, agent_def in AGENT_MAP.items():
        state = get_agent_state(agent_id)
        if state:
            current_task = None
            if state.current_task_id:
                task = get_task(state.current_task_id)
                if task:
                    current_task = {
                        "task_id": task.task_id,
                        "title": task.title
                    }
            
            agents_data.append({
                "name": agent_def.name,
                "role": agent_def.role.value,
                "status": state.status,
                "current_task": current_task,
                "last_activity": state.last_activity.strftime("%Y-%m-%d %H:%M:%S")
            })
    
    # Get task summary
    tasks = get_all_tasks()
    task_summary = {}
    for status in TaskStatus:
        task_summary[status.value] = len([t for t in tasks if t.status == status])
    
    task_summary_total = sum(task_summary.values())
    
    # Calculate phase progress
    phase_progress = {}
    for task in tasks:
        phase = task.roadmap_phase
        if phase not in phase_progress:
            phase_progress[phase] = {
                "total": 0,
                "completed": 0
            }
        
        phase_progress[phase]["total"] += 1
        if task.status == TaskStatus.COMPLETED:
            phase_progress[phase]["completed"] += 1
    
    # Convert to percentages
    for phase, counts in phase_progress.items():
        if counts["total"] > 0:
            phase_progress[phase] = round(counts["completed"] / counts["total"] * 100, 1)
        else:
            phase_progress[phase] = 0.0
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "agents": agents_data,
            "task_summary": task_summary,
            "task_summary_total": task_summary_total,
            "phase_progress": phase_progress
        }
    )


@app.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request):
    """Render the agents page."""
    agents_data = []
    for agent_id, agent_def in AGENT_MAP.items():
        state = get_agent_state(agent_id)
        if state:
            current_task = None
            if state.current_task_id:
                task = get_task(state.current_task_id)
                if task:
                    current_task = {
                        "task_id": task.task_id,
                        "title": task.title
                    }
            
            # Get completed tasks
            completed_tasks = []
            for task_id in state.completed_tasks:
                task = get_task(task_id)
                if task:
                    completed_tasks.append({
                        "task_id": task.task_id,
                        "title": task.title
                    })
            
            agents_data.append({
                "agent_id": agent_id,
                "name": agent_def.name,
                "role": agent_def.role.value,
                "status": state.status,
                "current_task": current_task,
                "completed_tasks": completed_tasks,
                "last_activity": state.last_activity.strftime("%Y-%m-%d %H:%M:%S"),
                "specializations": [spec.value for spec in agent_def.specializations]
            })
    
    return templates.TemplateResponse(
        "agents.html",
        {
            "request": request,
            "agents": agents_data
        }
    )


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request, filter: str = None):
    """Render the tasks page."""
    tasks = get_all_tasks()
    
    # Apply filter if provided
    if filter:
        try:
            status = TaskStatus(filter)
            tasks = [t for t in tasks if t.status == status]
        except ValueError:
            pass
    
    # Format tasks for display
    tasks_data = []
    for task in tasks:
        agent_name = "Unassigned"
        if task.assigned_agent_id:
            agent = AGENT_MAP.get(task.assigned_agent_id)
            if agent:
                agent_name = agent.name
        
        tasks_data.append({
            "task_id": task.task_id,
            "title": task.title,
            "status": task.status.value,
            "assigned_to": agent_name,
            "priority": task.priority,
            "roadmap_phase": task.roadmap_phase,
            "updated_at": task.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # Sort by priority and status
    tasks_data.sort(key=lambda t: (t["priority"], t["status"] != "PENDING"))
    
    return templates.TemplateResponse(
        "tasks.html",
        {
            "request": request,
            "tasks": tasks_data,
            "filter": filter
        }
    )


@app.get("/tasks/{task_id}", response_class=HTMLResponse)
async def task_detail(request: Request, task_id: str):
    """Render the task detail page."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get agent name
    agent_name = "Unassigned"
    if task.assigned_agent_id:
        agent = AGENT_MAP.get(task.assigned_agent_id)
        if agent:
            agent_name = agent.name
    
    # Get dependencies
    dependencies = []
    for dep_id in task.dependencies:
        dep_task = get_task(dep_id)
        if dep_task:
            dependencies.append({
                "task_id": dep_task.task_id,
                "title": dep_task.title
            })
    
    # Get agent logs
    agent_logs = ""
    if task.assigned_agent_id:
        log_file = AGENT_OUTPUTS_DIR / "logs" / f"{task.assigned_agent_id}.log"
        if log_file.exists():
            logs = log_file.read_text().splitlines()
            # Filter logs for this task
            task_logs = [line for line in logs if task_id in line]
            agent_logs = "\n".join(task_logs)
    
    # Determine status color
    status_colors = {
        "PENDING": "secondary",
        "IN_PROGRESS": "info",
        "COMPLETED": "success",
        "FAILED": "danger",
        "BLOCKED": "warning",
        "REVIEW": "primary"
    }
    task_status_color = status_colors.get(task.status.value, "secondary")
    
    return templates.TemplateResponse(
        "task_detail.html",
        {
            "request": request,
            "task": {
                "task_id": task.task_id,
                "title": task.title,
                "description": task.description,
                "status": task.status.value,
                "assigned_to": agent_name,
                "priority": task.priority,
                "roadmap_phase": task.roadmap_phase,
                "created_at": task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": task.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "estimated_hours": task.estimated_hours,
                "actual_hours": task.actual_hours,
                "acceptance_criteria": task.acceptance_criteria,
                "dependencies": dependencies,
                "artifacts": task.artifacts
            },
            "task_status_color": task_status_color,
            "agent_logs": agent_logs
        }
    )


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request, agent: str = None):
    """Render the logs page."""
    # Get available agents
    agent_options = {a.agent_id: a.name for a in AGENTS}
    
    # If no agent specified, use the first one
    if not agent and agent_options:
        agent = next(iter(agent_options.keys()))
    
    # Get agent name
    agent_name = agent_options.get(agent, "Unknown")
    
    # Get logs
    logs = ""
    if agent:
        log_file = AGENT_OUTPUTS_DIR / "logs" / f"{agent}.log"
        if log_file.exists():
            logs = log_file.read_text()
    
    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
            "agent_options": agent_options,
            "selected_agent": agent,
            "agent_name": agent_name,
            "logs": logs
        }
    )


@app.get("/agents/{agent_id}/run")
async def run_agent(agent_id: str):
    """Run an agent manually."""
    # Import here to avoid circular imports
    from agent_system.agent_runner import run_agent as run_agent_function
    
    # Run the agent in a separate process
    import subprocess
    import sys
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent)
    
    cmd = [sys.executable, "-m", "agent_system.agent_runner", "--agent", agent_id]
    subprocess.Popen(cmd, env=env)
    
    return {"status": "Agent started", "agent_id": agent_id}


@app.get("/tasks/{task_id}/run")
async def run_task(task_id: str):
    """Run a specific task manually."""
    # Import here to avoid circular imports
    from agent_system.agent_runner import run_agent as run_agent_function
    
    # Get the task
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if not task.assigned_agent_id:
        raise HTTPException(status_code=400, detail="Task is not assigned to any agent")
    
    # Run the agent in a separate process
    import subprocess
    import sys
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent)
    
    cmd = [sys.executable, "-m", "agent_system.agent_runner", "--agent", task.assigned_agent_id, "--task", task_id]
    subprocess.Popen(cmd, env=env)
    
    return {"status": "Task started", "task_id": task_id, "agent_id": task.assigned_agent_id}


@app.get("/tasks/{task_id}/status/{status}")
async def update_task_status_endpoint(task_id: str, status: str):
    """Update the status of a task."""
    try:
        task_status = TaskStatus(status.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    try:
        update_task_status(task_id, task_status)
        return {"status": "success", "task_id": task_id, "new_status": task_status.value}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def main():
    """Run the dashboard server."""
    uvicorn.run("agent_system.dashboard:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    main() 