# Fantasy Football Manager

A comprehensive fantasy football management system with data integration from popular platforms.

## Features

- **Team Management**: Create and manage fantasy football teams
- **Player Database**: Comprehensive player stats and information
- **League Management**: Create and join leagues with customizable settings
- **Draft Tools**: Mock drafts and draft assistance
- **API Integration**: Connect with ESPN, Yahoo, and Sleeper fantasy platforms

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fantasy-football-manager.git
cd fantasy-football-manager
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
# Development mode (with auto-reload)
./scripts/start.sh

# Alternatively
python scripts/run_server.py --frontend-url "http://localhost:3000"
```

5. Open your browser and navigate to:
   - API: [http://localhost:8000](http://localhost:8000)
   - API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Frontend: [http://localhost:3000](http://localhost:3000) (requires separate frontend setup)

## Continuous Running Options

### 1. Docker Compose (Recommended for Development)

```bash
# Start all services
docker-compose -f scripts/docker-compose.yml up -d

# View logs
docker-compose -f scripts/docker-compose.yml logs -f

# Stop all services
docker-compose -f scripts/docker-compose.yml down
```

### 2. Systemd Service (Linux Production Environments)

```bash
# Install as a systemd service (requires root/sudo)
sudo ./scripts/install_systemd_service.sh

# Check service status
sudo systemctl status fantasy-football-manager

# View logs
sudo journalctl -u fantasy-football-manager -f
```

## Database Models

The application includes the following key models:

- **Player**: Football player information and stats
- **Team**: Fantasy team data
- **League**: League settings and configuration
- **User**: User accounts and authentication
- **Draft**: Draft history and configuration

## API Routes

The API provides the following endpoints:

- `/api/players`: Player information and stats
- `/api/teams`: Team management
- `/api/leagues`: League settings and data
- `/api/drafts`: Draft tools and history
- `/api/token`: Authentication

## Agent System

The project includes an agent system for automated tasks:

```bash
# Initialize task list
python agent_system/launch_agents.py --init

# List all tasks
python agent_system/launch_agents.py --list

# Run the next task in the queue
python agent_system/launch_agents.py

# Run a specific task
python agent_system/launch_agents.py --task FFM-001
```

## Code Quality

Code quality is enforced using automated checks:

```bash
# Run code quality validation
python agent_system/validate_code_quality.py --all --detailed

# Automatically fix common issues
python agent_system/code_quality_autofix.py
```

## Connecting with Frontend

The backend API is configured to accept connections from the frontend running at `http://localhost:3000` by default. You can specify a different frontend URL when starting the server:

```bash
python scripts/run_server.py --frontend-url "https://your-frontend-url.com"
```

## License

MIT 