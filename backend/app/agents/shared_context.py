"""
Shared Context Management for AITM Multi-Agent System
Manages shared data and communication between agents
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class ContextEventType(Enum):
    """Types of events that can occur in the shared context"""
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    DATA_ADDED = "data_added"
    DATA_UPDATED = "data_updated"
    MILESTONE_REACHED = "milestone_reached"


@dataclass
class ContextEvent:
    """Event that occurred in the shared context"""
    event_type: ContextEventType
    agent_id: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['event_type'] = self.event_type.value
        return result


@dataclass
class AgentState:
    """State of an individual agent"""
    agent_id: str
    agent_type: str
    status: str  # "idle", "running", "completed", "failed"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0
    current_task: Optional[str] = None
    error_message: Optional[str] = None
    outputs: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        if self.start_time:
            result['start_time'] = self.start_time.isoformat()
        if self.end_time:
            result['end_time'] = self.end_time.isoformat()
        return result


class SharedContext:
    """
    Shared context for multi-agent threat modeling system
    Acts as a blackboard pattern implementation for agent coordination
    """
    
    def __init__(self, project_id: int):
        self.project_id = project_id
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
        # Core data storage
        self._data: Dict[str, Any] = {
            "project_id": project_id,
            "system_description": None,
            "system_inputs": [],
            "system_analysis": {},
            "attack_techniques": [],
            "attack_paths": [],
            "control_evaluation": {},
            "coverage_gaps": [],
            "recommendations": [],
            "metadata": {
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat()
            }
        }
        
        # Agent management
        self._agents: Dict[str, AgentState] = {}
        self._events: List[ContextEvent] = []
        self._lock = asyncio.Lock()
        
        # Progress tracking
        self._milestones: List[str] = [
            "system_analysis_complete",
            "attack_mapping_complete", 
            "control_evaluation_complete",
            "recommendations_complete"
        ]
        self._completed_milestones: set = set()
    
    async def initialize(self, system_description: str, system_inputs: List[Dict[str, Any]] = None):
        """Initialize the context with system data"""
        async with self._lock:
            self._data["system_description"] = system_description
            if system_inputs:
                self._data["system_inputs"] = system_inputs
            
            self._update_timestamp()
            
            await self._add_event(
                ContextEventType.DATA_ADDED,
                "system", 
                {"action": "initialized", "description_length": len(system_description)}
            )
    
    async def register_agent(self, agent_id: str, agent_type: str) -> None:
        """Register a new agent with the context"""
        async with self._lock:
            self._agents[agent_id] = AgentState(
                agent_id=agent_id,
                agent_type=agent_type,
                status="idle"
            )
            
            await self._add_event(
                ContextEventType.AGENT_STARTED,
                agent_id,
                {"agent_type": agent_type}
            )
            
            logger.info(f"Registered agent: {agent_id} ({agent_type})")
    
    async def update_agent_status(
        self, 
        agent_id: str, 
        status: str, 
        progress: Optional[float] = None,
        current_task: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Update agent status and progress"""
        async with self._lock:
            if agent_id not in self._agents:
                raise ValueError(f"Agent {agent_id} not registered")
            
            agent = self._agents[agent_id]
            agent.status = status
            
            if progress is not None:
                agent.progress = max(0.0, min(1.0, progress))
            
            if current_task is not None:
                agent.current_task = current_task
                
            if error_message is not None:
                agent.error_message = error_message
            
            # Set timestamps
            if status == "running" and agent.start_time is None:
                agent.start_time = datetime.now(timezone.utc)
            elif status in ["completed", "failed"]:
                agent.end_time = datetime.now(timezone.utc)
            
            self._update_timestamp()
            
            # Add event
            event_type = (
                ContextEventType.AGENT_COMPLETED if status == "completed"
                else ContextEventType.AGENT_FAILED if status == "failed"
                else ContextEventType.DATA_UPDATED
            )
            
            await self._add_event(
                event_type,
                agent_id,
                {
                    "status": status,
                    "progress": agent.progress,
                    "current_task": current_task,
                    "error": error_message
                }
            )
    
    async def set_data(self, key: str, value: Any, agent_id: Optional[str] = None) -> None:
        """Set data in the shared context"""
        async with self._lock:
            self._data[key] = value
            self._update_timestamp()
            
            await self._add_event(
                ContextEventType.DATA_ADDED,
                agent_id or "system",
                {"key": key, "data_type": type(value).__name__}
            )
            
            # Check for milestone completion
            await self._check_milestones()
    
    async def get_data(self, key: str) -> Any:
        """Get data from the shared context"""
        async with self._lock:
            return self._data.get(key)
    
    async def update_data(self, key: str, updates: Dict[str, Any], agent_id: Optional[str] = None) -> None:
        """Update existing data in the context"""
        async with self._lock:
            if key not in self._data:
                self._data[key] = {}
            
            if isinstance(self._data[key], dict):
                self._data[key].update(updates)
            else:
                self._data[key] = updates
            
            self._update_timestamp()
            
            await self._add_event(
                ContextEventType.DATA_UPDATED,
                agent_id or "system",
                {"key": key, "updates": list(updates.keys()) if isinstance(updates, dict) else "full_update"}
            )
            
            # Check for milestone completion
            await self._check_milestones()
    
    async def append_data(self, key: str, value: Any, agent_id: Optional[str] = None) -> None:
        """Append value to a list in the context"""
        async with self._lock:
            if key not in self._data:
                self._data[key] = []
            
            if not isinstance(self._data[key], list):
                raise ValueError(f"Cannot append to non-list data at key: {key}")
            
            self._data[key].append(value)
            self._update_timestamp()
            
            await self._add_event(
                ContextEventType.DATA_ADDED,
                agent_id or "system",
                {"key": key, "appended_type": type(value).__name__}
            )
    
    async def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get state of a specific agent"""
        async with self._lock:
            return self._agents.get(agent_id)
    
    async def get_all_agent_states(self) -> Dict[str, AgentState]:
        """Get states of all agents"""
        async with self._lock:
            return self._agents.copy()
    
    async def get_context_snapshot(self) -> Dict[str, Any]:
        """Get complete context snapshot"""
        async with self._lock:
            return {
                "project_id": self.project_id,
                "data": self._data.copy(),
                "agents": {agent_id: agent.to_dict() for agent_id, agent in self._agents.items()},
                "events": [event.to_dict() for event in self._events[-50:]],  # Last 50 events
                "completed_milestones": list(self._completed_milestones),
                "overall_progress": self._calculate_overall_progress()
            }
    
    async def get_events(self, limit: int = 50) -> List[ContextEvent]:
        """Get recent events from the context"""
        async with self._lock:
            return self._events[-limit:] if self._events else []
    
    def _update_timestamp(self) -> None:
        """Update the last modified timestamp"""
        self.updated_at = datetime.now(timezone.utc)
        self._data["metadata"]["updated_at"] = self.updated_at.isoformat()
    
    async def _add_event(self, event_type: ContextEventType, agent_id: str, data: Dict[str, Any], message: Optional[str] = None) -> None:
        """Add event to the context history"""
        event = ContextEvent(
            event_type=event_type,
            agent_id=agent_id,
            timestamp=datetime.now(timezone.utc),
            data=data,
            message=message
        )
        
        self._events.append(event)
        
        # Keep only last 1000 events to prevent memory bloat
        if len(self._events) > 1000:
            self._events = self._events[-500:]  # Keep last 500
        
        logger.debug(f"Added event: {event_type.value} from {agent_id}")
    
    async def _check_milestones(self) -> None:
        """Check if any milestones have been completed"""
        new_milestones = []
        
        # Check system analysis milestone
        if ("system_analysis_complete" not in self._completed_milestones and 
            self._data.get("system_analysis") and 
            isinstance(self._data["system_analysis"], dict) and
            len(self._data["system_analysis"]) > 0):
            new_milestones.append("system_analysis_complete")
        
        # Check attack mapping milestone
        if ("attack_mapping_complete" not in self._completed_milestones and
            self._data.get("attack_paths") and 
            len(self._data["attack_paths"]) > 0):
            new_milestones.append("attack_mapping_complete")
        
        # Check control evaluation milestone
        if ("control_evaluation_complete" not in self._completed_milestones and
            self._data.get("control_evaluation") and
            isinstance(self._data["control_evaluation"], dict) and
            len(self._data["control_evaluation"]) > 0):
            new_milestones.append("control_evaluation_complete")
        
        # Check recommendations milestone  
        if ("recommendations_complete" not in self._completed_milestones and
            self._data.get("recommendations") and
            len(self._data["recommendations"]) > 0):
            new_milestones.append("recommendations_complete")
        
        # Add new milestones
        for milestone in new_milestones:
            self._completed_milestones.add(milestone)
            await self._add_event(
                ContextEventType.MILESTONE_REACHED,
                "system",
                {"milestone": milestone},
                f"Milestone reached: {milestone}"
            )
            logger.info(f"Milestone reached: {milestone}")
    
    def _calculate_overall_progress(self) -> float:
        """Calculate overall progress based on completed milestones and agent progress"""
        if not self._agents:
            return 0.0
        
        # Weight milestones at 60% and agent progress at 40%
        milestone_progress = len(self._completed_milestones) / len(self._milestones)
        
        agent_progress = 0.0
        if self._agents:
            agent_progress = sum(agent.progress for agent in self._agents.values()) / len(self._agents)
        
        return (milestone_progress * 0.6) + (agent_progress * 0.4)
    
    @asynccontextmanager
    async def agent_session(self, agent_id: str, agent_type: str):
        """Context manager for agent sessions"""
        await self.register_agent(agent_id, agent_type)
        
        try:
            await self.update_agent_status(agent_id, "running", 0.0)
            yield self
        except Exception as e:
            await self.update_agent_status(agent_id, "failed", error_message=str(e))
            raise
        finally:
            # If not already marked as failed, mark as completed
            agent_state = await self.get_agent_state(agent_id)
            if agent_state and agent_state.status not in ["completed", "failed"]:
                await self.update_agent_status(agent_id, "completed", 1.0)
