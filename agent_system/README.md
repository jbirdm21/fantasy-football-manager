# Agent System for Fantasy Football Manager

This directory contains the autonomous agent system for developing the Ultimate Personal Fantasy Football Manager (UPFFM).

## Overview

The agent system uses GPT-4.1 models to autonomously work on development tasks for the fantasy football manager project. It includes:

- Multiple specialized agents with different roles (backend, frontend, data science, etc.)
- Task parsing from the project roadmap
- Persistence of agent states and task progress
- GitHub integration for committing changes
- A web dashboard for monitoring progress

## Getting Started

### Prerequisites

- Python 3.11 or higher
- An OpenAI API key
- A GitHub personal access token (if using GitHub integration)
- Redis (optional, for more robust state persistence)

### Installation

1. Clone the repository and navigate to the project directory
2. Install the required dependencies:

```bash
pip install -r agent_system/requirements.txt
```

3. Set up the environment:

```bash
python -m agent_system.run --setup
```

4. Edit the `.env` file in the `agent_system` directory to add your API keys

### Running the Agent System

#### Local Execution

To initialize the agent system and run all agents once:

```bash
python -m agent_system.run --initialize
```

To run a specific agent:

```bash
python -m agent_system.run --agent backend-dev-1
```

To run in daemon mode (continuous operation):

```bash
python -m agent_system.run --daemon
```

#### Docker Execution

To run the entire system using Docker:

```bash
cd agent_system
docker-compose up -d
```

This will start:
- The agent orchestrator
- A web dashboard on port 8080
- A Redis instance for state persistence

## Architecture

The agent system consists of the following components:

- **Agent Models**: Definitions of agent roles, tasks, and states
- **Agent Runner**: Core orchestration logic for executing agents and tasks
- **Persistence**: Storage of agent states and task progress
- **GitHub Integration**: Committing changes to the repository
- **Dashboard**: Web interface for monitoring progress

## Agent Roles

The system includes the following specialized agents:

- **Backend Developer**: Implements FastAPI services and database models
- **Frontend Developer**: Creates Next.js UI components
- **Data Scientist**: Develops player projection models
- **DevOps Engineer**: Manages deployment and infrastructure
- **Technical Lead**: Coordinates development efforts
- **QA Engineer**: Ensures comprehensive testing

## Task Management

Tasks are automatically generated from the project roadmap in `docs/ROADMAP.md`. Each task:

1. Has a set of acceptance criteria
2. Is assigned to a specific agent based on specialization
3. May have dependencies on other tasks
4. Has a priority based on its position in the roadmap

## Dashboard

The dashboard provides a web interface for monitoring the agent system:

- **Home**: Overview of agent status and task progress
- **Agents**: Details of each agent and their current tasks
- **Tasks**: List of all tasks and their status
- **Logs**: Agent activity logs

Access the dashboard at `http://localhost:8080` when running the system.

## Contributing

To extend or modify the agent system:

1. Add new agent roles or specializations in `agents/models.py`
2. Define new agents in `agents/definitions.py`
3. Modify the task parsing logic in `tasks/roadmap_parser.py`
4. Enhance the agent execution logic in `agent_runner.py`

## License

This code is released under the MIT License. 