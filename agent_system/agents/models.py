"""Models for agent definitions and state management."""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from dataclasses import dataclass, field


class AgentRole(str, Enum):
    """Roles that agents can assume in the system."""

    BACKEND_DEVELOPER = "backend_developer"
    FRONTEND_DEVELOPER = "frontend_developer"
    DATA_SCIENTIST = "data_scientist"
    DEVOPS_ENGINEER = "devops_engineer"
    TECHNICAL_LEAD = "technical_lead"
    QA_ENGINEER = "qa_engineer"


class AgentSpecialization(str, Enum):
    """Areas of specialization for agents."""

    PYTHON = "python"
    FASTAPI = "fastapi"
    SQL = "sql"
    REACT = "react"
    NEXTJS = "nextjs"
    MACHINE_LEARNING = "machine_learning"
    DOCKER = "docker"
    DATA_ENGINEERING = "data_engineering"
    TESTING = "testing"
    API_INTEGRATION = "api_integration"


class TaskStatus(str, Enum):
    """Status of a task in the agent system."""
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PR_READY = "PR_READY"
    PR_SUBMITTED = "PR_SUBMITTED"
    NEEDS_REVISION = "NEEDS_REVISION"
    ERROR = "ERROR"


class Agent(BaseModel):
    """Definition of an AI agent in the system."""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable name for the agent")
    role: AgentRole = Field(..., description="Primary role of the agent")
    specializations: List[AgentSpecialization] = Field(
        default_factory=list,
        description="Areas of specialization for this agent"
    )
    goal: str = Field(..., description="The high-level goal of this agent")
    backstory: str = Field(
        default="",
        description="Background story to provide context to the agent"
    )
    model: str = Field(
        default="gpt-4-1106-preview",
        description="LLM model used by this agent"
    )
    temperature: float = Field(
        default=0.1,
        description="Temperature for LLM generation (higher = more creative)"
    )
    max_tokens: int = Field(
        default=4000,
        description="Maximum number of tokens in LLM responses"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Custom system prompt for this agent"
    )


class AgentState(BaseModel):
    """The current state of an agent in the system."""

    agent_id: str = Field(..., description="ID of the agent this state belongs to")
    status: str = Field(default="idle", description="Current status of the agent")
    current_task_id: Optional[str] = Field(
        default=None,
        description="ID of the task currently being worked on"
    )
    last_activity: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of the last activity"
    )
    completed_tasks: List[str] = Field(
        default_factory=list,
        description="IDs of tasks completed by this agent"
    )
    memory: Dict[str, Any] = Field(
        default_factory=dict,
        description="Persistent memory for the agent across tasks"
    )


@dataclass
class Task:
    """Task for agents to work on."""
    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.READY
    priority: int = 999
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "artifacts": self.artifacts,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary representation."""
        # Convert string dates back to datetime
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        # Convert status string to enum
        if "status" in data and isinstance(data["status"], str):
            data["status"] = TaskStatus(data["status"])

        return cls(**data)
