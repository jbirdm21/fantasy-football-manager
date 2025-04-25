"""Simple web dashboard for monitoring the agent system."""
import os
import time
import json
from datetime import datetime
from pathlib import Path
import logging
import sqlite3
import glob
import subprocess

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
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
    title="UPFFM Agent System Dashboard",
    description="Dashboard for monitoring the agent system",
    version="0.1.0",
)

# Create templates directory
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)

# Create static directory
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

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

# Create CSS file if it doesn't exist
css_file = os.path.join(static_dir, "style.css")
if not os.path.exists(css_file):
    with open(css_file, "w") as f:
        f.write("""
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .tabs { display: flex; margin-bottom: 20px; border-bottom: 1px solid #ddd; }
        .tab { padding: 10px 20px; cursor: pointer; }
        .tab.active { border-bottom: 3px solid #0366d6; font-weight: bold; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        tr:hover { background-color: #f1f1f1; }
        .status-pending { color: orange; }
        .status-in-progress { color: blue; }
        .status-completed { color: green; }
        .status-failed { color: red; }
        .refresh-btn { padding: 8px 16px; background: #0366d6; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .log-viewer { background: #272822; color: #f8f8f2; padding: 15px; border-radius: 5px; font-family: monospace; overflow: auto; max-height: 500px; }
        .file-changes { font-family: monospace; }
        pre { background: #f8f8f8; padding: 10px; border-radius: 5px; overflow: auto; }
        .progress-container { height: 20px; background-color: #f5f5f5; border-radius: 10px; margin-bottom: 10px; }
        .progress-bar { height: 100%; border-radius: 10px; background-color: #4CAF50; }
        .search-box { padding: 8px; margin-bottom: 15px; width: 100%; }
        """)

# Database connection helper


def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), "outputs", "agent_system.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Main dashboard route


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Create the base template if it doesn't exist
    base_template = os.path.join(templates_dir, "base.html")
    if True:  # Force overwrite to ensure we have a compatible template
        with open(base_template, "w") as f:
            f.write("""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>UPFFM - Agent Dashboard</title>
                <link rel="stylesheet" href="/static/style.css">
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
                <link rel="preconnect" href="https://fonts.googleapis.com">
                <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
                <meta http-equiv="refresh" content="60">
            </head>
            <body>
                <div class="container">
                    <!-- Sidebar Navigation -->
                    <div class="sidebar">
                        <div class="sidebar-header">
                            <div class="app-title">UPFFM</div>
                            <button class="theme-toggle" id="themeToggle">
                                <i class="bi bi-moon-stars"></i>
                            </button>
                        </div>
                        <div class="sidebar-menu">
                            <a href="#" class="nav-link active" id="overviewLink" onclick="openTab('overview')">
                                <i class="bi bi-grid"></i>
                                <span>Overview</span>
                            </a>
                            <a href="#" class="nav-link" id="agentsLink" onclick="openTab('agents')">
                                <i class="bi bi-person-badge"></i>
                                <span>Agents</span>
                            </a>
                            <a href="#" class="nav-link" id="tasksLink" onclick="openTab('tasks')">
                                <i class="bi bi-list-check"></i>
                                <span>Tasks</span>
                            </a>
                            <a href="#" class="nav-link" id="logsLink" onclick="openTab('logs')">
                                <i class="bi bi-journal-text"></i>
                                <span>Logs</span>
                            </a>
                            <a href="#" class="nav-link" id="changesLink" onclick="openTab('changes')">
                                <i class="bi bi-git"></i>
                                <span>File Changes</span>
                            </a>
                            <a href="#" class="nav-link" id="conversationsLink" onclick="openTab('conversations')">
                                <i class="bi bi-chat-dots"></i>
                                <span>Conversations</span>
                            </a>
                            <a href="#" class="nav-link" id="databaseLink" onclick="openTab('database')">
                                <i class="bi bi-database"></i>
                                <span>Database</span>
                            </a>
                        </div>
                    </div>

                    <!-- Main Content Area -->
                    <div class="main-content">
                        <div class="content-header">
                            <h1 class="page-title">Agent System Dashboard</h1>
                            <div class="flex items-center gap-3">
                                <span>Last refreshed: {{ now }}</span>
                                <button class="btn btn-primary" onclick="window.location.reload()">
                                    <i class="bi bi-arrow-clockwise mr-1"></i> Refresh
                                </button>
                            </div>
                        </div>

                        {% block content %}{% endblock %}
                    </div>
                </div>

                <script>
                function openTab(tabId) {
                    // Hide all tab contents
                    const tabContents = document.querySelectorAll('.tab-content');
                    tabContents.forEach(tab => {
                        tab.style.display = 'none';
                    });

                    // Remove active class from all nav links
                    const navLinks = document.querySelectorAll('.nav-link');
                    navLinks.forEach(link => {
                        link.classList.remove('active');
                    });

                    // Show the selected tab
                    document.getElementById(tabId).style.display = 'block';
                    document.getElementById(tabId + 'Link').classList.add('active');
                }

                // Filter table function
                function filterTable(inputId, tableId) {
                    const input = document.getElementById(inputId);
                    const filter = input.value.toUpperCase();
                    const table = document.getElementById(tableId);
                    const rows = table.getElementsByTagName('tr');

                    for (let i = 1; i < rows.length; i++) {
                        const cells = rows[i].getElementsByTagName('td');
                        let found = false;

                        for (let j = 0; j < cells.length; j++) {
                            const cell = cells[j];
                            if (cell) {
                                const text = cell.textContent || cell.innerText;
                                if (text.toUpperCase().indexOf(filter) > -1) {
                                    found = true;
                                    break;
                                }
                            }
                        }

                        rows[i].style.display = found ? '' : 'none';
                    }
                }

                function filterLogs() {
                    const filter = document.getElementById('logSearch').value.toUpperCase();
                    const logContent = document.getElementById('logContent');
                    const lines = logContent.getElementsByTagName('div');

                    for (let i = 0; i < lines.length; i++) {
                        const text = lines[i].textContent || lines[i].innerText;
                        lines[i].style.display = text.toUpperCase().indexOf(filter) > -1 ? '' : 'none';
                    }
                }

                function fetchLogFile() {
                    const logFile = document.getElementById('logFile').value;
                    fetch('/logs/' + logFile)
                        .then(response => response.json())
                        .then(data => {
                            const logContent = document.getElementById('logContent');
                            logContent.innerHTML = '';
                            data.content.forEach(line => {
                                const div = document.createElement('div');
                                div.className = 'log-line';
                                div.textContent = line;

                                // Add color classes based on log content
                                if (line.includes('ERROR') || line.includes('Error')) {
                                    div.className += ' log-error';
                                } else if (line.includes('WARNING') || line.includes('Warning')) {
                                    div.className += ' log-warning';
                                } else if (line.includes('INFO') || line.includes('Info')) {
                                    div.className += ' log-info';
                                } else if (line.includes('SUCCESS') || line.includes('Success')) {
                                    div.className += ' log-success';
                                }

                                logContent.appendChild(div);
                            });
                        });
                }

                function fetchConversation() {
                    const agentId = document.getElementById('convoAgent').value;
                    const taskId = document.getElementById('convoTask').value;
                    fetch(`/conversations/${agentId}/${taskId}`)
                        .then(response => response.json())
                        .then(data => {
                            const convoContent = document.getElementById('conversationContent');
                            if (data.conversation) {
                                convoContent.innerHTML = `<pre>${data.conversation}</pre>`;
                            } else {
                                convoContent.innerHTML = "<p>No conversation found</p>";
                            }
                        });
                }

                // Show the overview tab by default
                document.addEventListener('DOMContentLoaded', function() {
                    openTab('overview');
                });
                </script>
            </body>
            </html>
            """)

    # Create a modern index template
    index_template = os.path.join(templates_dir, "index.html")
    if True:  # Force overwrite to ensure we have a compatible template
        with open(index_template, "w") as f:
            f.write("""
            {% extends "base.html" %}
            {% block content %}
            <!-- Overview Tab -->
            <div id="overview" class="tab-content">
                <div class="cards-grid">
                    <div class="card">
                        <div class="stat-card">
                            <div class="stat-title">Active Agents</div>
                            <div class="stat-value">{{ active_agents }}/{{ total_agents }}</div>
                            <div class="progress-container">
                                <div class="progress-bar" style="width: {{ (active_agents / total_agents) * 100 if total_agents > 0 else 0 }}%;"></div>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="stat-card">
                            <div class="stat-title">Tasks Completed</div>
                            <div class="stat-value">{{ completed_tasks }}/{{ total_tasks }}</div>
                            <div class="progress-container">
                                <div class="progress-bar" style="width: {{ (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0 }}%;"></div>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="stat-card">
                            <div class="stat-title">Tasks In Progress</div>
                            <div class="stat-value">{{ task_summary.IN_PROGRESS if task_summary.IN_PROGRESS else 0 }}</div>
                            <div class="stat-change positive">
                                <i class="bi bi-arrow-up-right"></i>
                                <span>Currently Being Processed</span>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="stat-card">
                            <div class="stat-title">Pending Tasks</div>
                            <div class="stat-value">{{ task_summary.PENDING if task_summary.PENDING else 0 }}</div>
                            <div class="stat-change">
                                <i class="bi bi-clock"></i>
                                <span>Waiting to be Started</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card mb-4">
                    <div class="card-heading">
                        <h2>Current Agent Activity</h2>
                    </div>
                    <div class="card-body">
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Agent</th>
                                        <th>Current Task</th>
                                        <th>Status</th>
                                        <th>Started</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for agent in agents %}
                                    <tr>
                                        <td><strong>{{ agent.name if agent.name else agent.agent_id }}</strong></td>
                                        <td>{{ agent.current_task_title if agent.current_task_title else "None" }}</td>
                                        <td>
                                            <span class="status status-{{ (agent.status|lower) if agent.status else 'unknown' }}">
                                                {% if agent.status == 'ACTIVE' %}
                                                <i class="bi bi-check-circle-fill"></i>
                                                {% elif agent.status == 'WORKING' %}
                                                <i class="bi bi-lightning-fill"></i>
                                                {% elif agent.status == 'IDLE' %}
                                                <i class="bi bi-pause-circle"></i>
                                                {% else %}
                                                <i class="bi bi-question-circle"></i>
                                                {% endif %}
                                                {{ agent.status if agent.status else "Unknown" }}
                                            </span>
                                        </td>
                                        <td>{{ agent.task_started_at if agent.task_started_at else "N/A" }}</td>
                                        <td>
                                            <button class="btn btn-sm btn-primary">
                                                <i class="bi bi-play-fill"></i> Run
                                            </button>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div class="card mb-4">
                    <div class="card-heading">
                        <h2>Recent Tasks</h2>
                    </div>
                    <div class="card-body">
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Task</th>
                                        <th>Agent</th>
                                        <th>Status</th>
                                        <th>Updated</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for task in recent_tasks %}
                                    <tr>
                                        <td><strong>{{ task.title }}</strong></td>
                                        <td>{{ task.assigned_to }}</td>
                                        <td>
                                            <span class="status status-{{ (task.status|lower) if task.status else 'unknown' }}">
                                                {% if task.status == 'COMPLETED' %}
                                                <i class="bi bi-check-circle-fill"></i>
                                                {% elif task.status == 'IN_PROGRESS' %}
                                                <i class="bi bi-lightning-fill"></i>
                                                {% elif task.status == 'PENDING' %}
                                                <i class="bi bi-clock"></i>
                                                {% elif task.status == 'FAILED' %}
                                                <i class="bi bi-x-circle-fill"></i>
                                                {% else %}
                                                <i class="bi bi-question-circle"></i>
                                                {% endif %}
                                                {{ task.status if task.status else "Unknown" }}
                                            </span>
                                        </td>
                                        <td>{{ task.updated_at }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-heading">
                        <h2>Recent Log Messages</h2>
                    </div>
                    <div class="card-body">
                        <div class="log-viewer">
                            {% for log in recent_logs %}
                            <div class="log-line {% if 'ERROR' in log or 'Error' in log %}log-error{% elif 'WARNING' in log or 'Warning' in log %}log-warning{% elif 'INFO' in log or 'Info' in log %}log-info{% elif 'SUCCESS' in log or 'Success' in log %}log-success{% endif %}">
                                {{ log }}
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Agents Tab -->
            <div id="agents" class="tab-content">
                <div class="card">
                    <div class="card-heading">
                        <h2>Agent Status</h2>
                        <div class="search-box">
                            <i class="bi bi-search"></i>
                            <input type="text" id="agentSearch" onkeyup="filterTable('agentSearch', 'agentTable')" placeholder="Search for agents...">
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="table-container">
                            <table id="agentTable">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Agent ID</th>
                                        <th>Status</th>
                                        <th>Current Task</th>
                                        <th>Last Active</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for agent in agents %}
                                    <tr>
                                        <td><strong>{{ agent.name if agent.name else "Unknown" }}</strong></td>
                                        <td>{{ agent.agent_id }}</td>
                                        <td>
                                            <span class="status status-{{ (agent.status|lower) if agent.status else 'unknown' }}">
                                                {% if agent.status == 'ACTIVE' %}
                                                <i class="bi bi-check-circle-fill"></i>
                                                {% elif agent.status == 'WORKING' %}
                                                <i class="bi bi-lightning-fill"></i>
                                                {% elif agent.status == 'IDLE' %}
                                                <i class="bi bi-pause-circle"></i>
                                                {% else %}
                                                <i class="bi bi-question-circle"></i>
                                                {% endif %}
                                                {{ agent.status if agent.status else "Unknown" }}
                                            </span>
                                        </td>
                                        <td>{{ agent.current_task_title if agent.current_task_title else "None" }}</td>
                                        <td>{{ agent.updated_at if agent.updated_at else "Unknown" }}</td>
                                        <td>
                                            <button class="btn btn-sm btn-primary">
                                                <i class="bi bi-play-fill"></i> Run
                                            </button>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tasks Tab -->
            <div id="tasks" class="tab-content">
                <div class="card">
                    <div class="card-heading">
                        <h2>Task List</h2>
                        <div class="search-box">
                            <i class="bi bi-search"></i>
                            <input type="text" id="taskSearch" onkeyup="filterTable('taskSearch', 'taskTable')" placeholder="Search for tasks...">
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="flex gap-3 mb-3">
                            <button class="btn btn-sm btn-primary" onclick="filterTasksByStatus('all')">All</button>
                            <button class="btn btn-sm btn-secondary" onclick="filterTasksByStatus('pending')">Pending</button>
                            <button class="btn btn-sm btn-info" onclick="filterTasksByStatus('in-progress')">In Progress</button>
                            <button class="btn btn-sm btn-success" onclick="filterTasksByStatus('completed')">Completed</button>
                            <button class="btn btn-sm btn-danger" onclick="filterTasksByStatus('failed')">Failed</button>
                        </div>
                        <div class="table-container">
                            <table id="taskTable">
                                <thead>
                                    <tr>
                                        <th>Task ID</th>
                                        <th>Title</th>
                                        <th>Status</th>
                                        <th>Assigned To</th>
                                        <th>Created At</th>
                                        <th>Updated At</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for task in tasks %}
                                    <tr data-status="{{ (task.status|lower) if task.status else 'unknown' }}">
                                        <td>{{ task.task_id }}</td>
                                        <td><strong>{{ task.title }}</strong></td>
                                        <td>
                                            <span class="status status-{{ (task.status|lower) if task.status else 'unknown' }}">
                                                {% if task.status == 'COMPLETED' %}
                                                <i class="bi bi-check-circle-fill"></i>
                                                {% elif task.status == 'IN_PROGRESS' %}
                                                <i class="bi bi-lightning-fill"></i>
                                                {% elif task.status == 'PENDING' %}
                                                <i class="bi bi-clock"></i>
                                                {% elif task.status == 'FAILED' %}
                                                <i class="bi bi-x-circle-fill"></i>
                                                {% else %}
                                                <i class="bi bi-question-circle"></i>
                                                {% endif %}
                                                {{ task.status if task.status else "Unknown" }}
                                            </span>
                                        </td>
                                        <td>{{ task.assigned_to }}</td>
                                        <td>{{ task.created_at }}</td>
                                        <td>{{ task.updated_at }}</td>
                                        <td>
                                            <button class="btn btn-sm btn-primary">
                                                <i class="bi bi-play-fill"></i> Run
                                            </button>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Logs Tab -->
            <div id="logs" class="tab-content">
                <div class="card">
                    <div class="card-heading">
                        <h2>System Logs</h2>
                    </div>
                    <div class="card-body">
                        <div class="flex gap-3 mb-3">
                            <div class="search-box flex-1">
                                <i class="bi bi-search"></i>
                                <input type="text" id="logSearch" onkeyup="filterLogs()" placeholder="Filter logs...">
                            </div>
                            <select id="logFile" onchange="fetchLogFile()" class="form-control" style="max-width: 200px;">
                                {% for log_file in log_files %}
                                <option value="{{ log_file }}">{{ log_file }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="log-viewer" id="logContent">
                            {% for line in log_content %}
                            <div class="log-line {% if 'ERROR' in line or 'Error' in line %}log-error{% elif 'WARNING' in line or 'Warning' in line %}log-warning{% elif 'INFO' in line or 'Info' in line %}log-info{% elif 'SUCCESS' in line or 'Success' in line %}log-success{% endif %}">
                                {{ line }}
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>

            <!-- File Changes Tab -->
            <div id="changes" class="tab-content">
                <div class="card">
                    <div class="card-heading">
                        <h2>Recent File Changes</h2>
                    </div>
                    <div class="card-body">
                        {% for change in file_changes %}
                        <div class="card mb-3">
                            <div class="card-heading">
                                <h2>{{ change.file }}</h2>
                                <span>Last modified: {{ change.modified_time }}</span>
                            </div>
                            <div class="card-body">
                                <pre>{{ change.preview }}</pre>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- Conversations Tab -->
            <div id="conversations" class="tab-content">
                <div class="card">
                    <div class="card-heading">
                        <h2>Agent Conversations</h2>
                    </div>
                    <div class="card-body">
                        <div class="flex gap-3 mb-3">
                            <div class="form-group flex-1">
                                <label class="form-label">Agent</label>
                                <select id="convoAgent" onchange="fetchConversation()" class="form-control">
                                    {% for agent in agents %}
                                    <option value="{{ agent.agent_id }}">{{ agent.name if agent.name else agent.agent_id }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="form-group flex-1">
                                <label class="form-label">Task</label>
                                <select id="convoTask" onchange="fetchConversation()" class="form-control">
                                    {% for task in tasks %}
                                    <option value="{{ task.task_id }}">{{ task.title }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        <div id="conversationContent" class="log-viewer">
                            {% if conversation %}
                            <pre>{{ conversation }}</pre>
                            {% else %}
                            <p>Select an agent and task to view conversations</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Database Tab -->
            <div id="database" class="tab-content">
                <div class="card">
                    <div class="card-heading">
                        <h2>Database Query</h2>
                    </div>
                    <div class="card-body">
                        <form action="/query" method="post">
                            <div class="form-group">
                                <label class="form-label">SQL Query</label>
                                <textarea name="query" class="form-control" style="height: 100px;">SELECT * FROM tasks LIMIT 10;</textarea>
                            </div>
                            <button type="submit" class="btn btn-primary">
                                <i class="bi bi-play-fill"></i> Run Query
                            </button>
                        </form>

                        {% if query_result %}
                        <div class="mt-4">
                            <h3 class="mb-3">Query Results</h3>
                            <div class="table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            {% for column in query_columns %}
                                            <th>{{ column }}</th>
                                            {% endfor %}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for row in query_result %}
                                        <tr>
                                            {% for cell in row %}
                                            <td>{{ cell }}</td>
                                            {% endfor %}
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
            <script>
            function filterTasksByStatus(status) {
                const rows = document.querySelectorAll('#taskTable tbody tr');
                rows.forEach(row => {
                    if (status === 'all') {
                        row.style.display = '';
                    } else {
                        row.style.display = row.dataset.status === status ? '' : 'none';
                    }
                });
            }
            </script>
            {% endblock %}
            """)

    try:
        # Get agent states
        conn = get_db_connection()
        agents = conn.execute('SELECT * FROM agent_states').fetchall()

        # Get task list
        tasks = conn.execute('SELECT * FROM tasks ORDER BY created_at DESC').fetchall()
        recent_tasks = conn.execute('SELECT * FROM tasks ORDER BY updated_at DESC LIMIT 10').fetchall()

        # Calculate stats safely
        active_agents = sum(1 for agent in agents if getattr(agent, 'status', '') in ('ACTIVE', 'WORKING'))
        total_agents = len(agents)
        completed_tasks = sum(1 for task in tasks if getattr(task, 'status', '') == 'COMPLETED')
        total_tasks = len(tasks)

        # Create task summary safely
        task_summary = {}
        for status in ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'BLOCKED']:
            task_summary[status] = sum(1 for task in tasks if getattr(task, 'status', '') == status)
        task_summary_total = sum(task_summary.values())

        # Create phase progress safely
        phase_progress = {}

        # Get recent log entries
        log_dir = os.path.join(os.path.dirname(__file__), "outputs", "logs")
        log_files = []
        log_content = []
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            log_files.sort(reverse=True)

            if log_files:
                main_log = os.path.join(log_dir, log_files[0])
                try:
                    with open(main_log, 'r') as f:
                        log_content = [line.strip() for line in f.readlines()[-50:]]
                except Exception as e:
                    log_content = [f"Error reading log: {str(e)}"]

        # Get recent file changes
        file_changes = []
        try:
            # Find recently modified files, excluding common directories
            cmd = 'find /Users/Jeff/fantasy-football-manager -type f -mtime -1 -not -path "*/\\.*" -not -path "*/outputs/*" -not -path "*/__pycache__/*" -not -path "*/venv/*" -not -path "*/.venv/*" | sort'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            recent_files = result.stdout.strip().split('\n')

            for file_path in recent_files[:10]:  # Limit to 10 files
                if not file_path:
                    continue

                try:
                    stat = os.stat(file_path)
                    modified_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

                    # Get file preview
                    with open(file_path, 'r', errors='replace') as f:
                        lines = f.readlines()
                        preview = ''.join(lines[:20])  # First 20 lines
                        if len(lines) > 20:
                            preview += "\n... (more lines) ...\n"

                    file_changes.append({
                        'file': file_path,
                        'modified_time': modified_time,
                        'preview': preview
                    })
                except Exception as e:
                    file_changes.append({
                        'file': file_path,
                        'modified_time': 'Error',
                        'preview': f"Error reading file: {str(e)}"
                    })
        except Exception as e:
            file_changes = [{
                'file': 'Error',
                'modified_time': 'Error',
                'preview': f"Error finding files: {str(e)}"
            }]

        # Prepare template context
        context = {
            "request": request,
            "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "agents": agents,
            "tasks": tasks,
            "recent_tasks": recent_tasks,
            "active_agents": active_agents,
            "total_agents": total_agents,
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "recent_logs": log_content,
            "log_files": log_files,
            "file_changes": file_changes,
            "task_summary": task_summary,
            "task_summary_total": task_summary_total,
            "phase_progress": phase_progress
        }

        return templates.TemplateResponse("index.html", context)
    except Exception as e:
        # Fallback context for error cases
        error_context = {
            "request": request,
            "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error_message": str(e),
            "agents": [],
            "tasks": [],
            "recent_tasks": [],
            "active_agents": 0,
            "total_agents": 0,
            "completed_tasks": 0,
            "total_tasks": 0,
            "recent_logs": [f"Error loading dashboard: {str(e)}"],
            "log_files": [],
            "file_changes": [],
            "task_summary": {"PENDING": 0, "IN_PROGRESS": 0, "COMPLETED": 0, "FAILED": 0, "BLOCKED": 0},
            "task_summary_total": 0,
            "phase_progress": {}
        }
        return templates.TemplateResponse("index.html", error_context)

# Log file endpoint


@app.get("/logs/{log_file}")
async def get_log_file(log_file: str):
    log_dir = os.path.join(os.path.dirname(__file__), "outputs", "logs")
    log_path = os.path.join(log_dir, log_file)

    if not os.path.exists(log_path) or not log_file.endswith('.log'):
        raise HTTPException(status_code=404, detail="Log file not found")

    try:
        with open(log_path, 'r') as f:
            content = [line.strip() for line in f.readlines()]
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log file: {str(e)}")

# Conversation endpoint


@app.get("/conversations/{agent_id}/{task_id}")
async def get_conversation(agent_id: str, task_id: str):
    conversations_dir = os.path.join(os.path.dirname(__file__), "outputs", "conversations")

    if not os.path.exists(conversations_dir):
        return {"conversation": None}

    # Look for conversation files for this agent and task
    conversation_files = glob.glob(f"{conversations_dir}/{agent_id}_{task_id}_*.json")
    if not conversation_files:
        return {"conversation": None}

    # Sort by timestamp (assuming filename contains timestamp)
    conversation_files.sort(reverse=True)

    try:
        with open(conversation_files[0], 'r') as f:
            conversation_data = json.load(f)

        # Format the conversation
        formatted = json.dumps(conversation_data, indent=2)
        return {"conversation": formatted}
    except Exception as e:
        return {"conversation": f"Error reading conversation: {str(e)}"}

# Database query endpoint


@app.post("/query")
async def run_query(request: Request, query: str = Form(...)):
    conn = get_db_connection()
    try:
        result = conn.execute(query).fetchall()
        columns = [description[0] for description in conn.execute(query).description]

        # Convert result to list of lists for the template
        rows = []
        for row in result:
            rows.append([row[col] for col in row.keys()])

        # Reload page with query results
        context = {
            "request": request,
            "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "agents": conn.execute('SELECT * FROM agent_states').fetchall(),
            "tasks": conn.execute('SELECT * FROM tasks ORDER BY created_at DESC').fetchall(),
            "recent_tasks": conn.execute('SELECT * FROM tasks ORDER BY updated_at DESC LIMIT 10').fetchall(),
            "query_result": rows,
            "query_columns": columns
        }

        return templates.TemplateResponse("index.html", context)
    except Exception as e:
        # Return error message
        context = {
            "request": request,
            "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "agents": conn.execute('SELECT * FROM agent_states').fetchall(),
            "tasks": conn.execute('SELECT * FROM tasks ORDER BY created_at DESC').fetchall(),
            "recent_tasks": conn.execute('SELECT * FROM tasks ORDER BY updated_at DESC LIMIT 10').fetchall(),
            "query_error": str(e)
        }

        return templates.TemplateResponse("index.html", context)

# Add a debug route to check static files


@app.get("/debug-static")
async def debug_static():
    static_files = []
    for file_path in Path(static_dir).glob("**/*"):
        if file_path.is_file():
            static_files.append({
                "file": str(file_path.relative_to(static_dir)),
                "size": file_path.stat().st_size,
                "url": f"/static/{file_path.relative_to(static_dir)}"
            })
    return {
        "static_dir": str(static_dir),
        "files": static_files
    }


def main():
    """Run the dashboard server."""
    uvicorn.run("agent_system.dashboard:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    main()
