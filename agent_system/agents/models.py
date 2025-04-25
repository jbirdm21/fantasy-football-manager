"""Models for agent definitions and state management."""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


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
    """Status of a task in the system."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    REVIEW = "review"


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


class Task(BaseModel):
    """A task to be performed by an agent."""
    
    task_id: str = Field(..., description="Unique identifier for the task")
    title: str = Field(..., description="Title of the task")
    description: str = Field(..., description="Detailed description of the task")
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description="List of criteria that must be met for the task to be considered complete"
    )
    priority: int = Field(default=5, description="Priority from 1 (highest) to 10 (lowest)")
    assigned_agent_id: Optional[str] = Field(
        default=None, 
        description="ID of the agent assigned to this task"
    )
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status of the task")
    dependencies: List[str] = Field(
        default_factory=list,
        description="IDs of tasks that must be completed before this one"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When the task was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="When the task was last updated"
    )
    estimated_hours: float = Field(
        default=0.0,
        description="Estimated hours to complete this task"
    )
    actual_hours: Optional[float] = Field(
        default=None,
        description="Actual hours spent on this task"
    )
    roadmap_phase: str = Field(
        default="",
        description="Which phase of the roadmap this task belongs to"
    )
    artifacts: List[str] = Field(
        default_factory=list,
        description="Paths to artifacts created or modified by this task"
    ) 