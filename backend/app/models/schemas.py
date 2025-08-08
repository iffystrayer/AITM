"""
Pydantic schemas for API data validation
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


# Project Schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# System Input Schemas
class SystemInputCreate(BaseModel):
    input_type: str = Field(..., pattern="^(text|json|file)$")
    content: str
    filename: Optional[str] = None


class SystemInputResponse(SystemInputCreate):
    id: int
    project_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Threat Modeling Schemas
class ThreatModelingRequest(BaseModel):
    llm_provider: Optional[str] = Field(None, pattern="^(openai|google|ollama|litellm)$")
    analysis_depth: Optional[str] = Field("standard", pattern="^(quick|standard|deep)$")
    include_mitigations: bool = True
    custom_instructions: Optional[str] = None


class ThreatModelingResponse(BaseModel):
    project_id: int
    status: str
    message: str


class ThreatModelingStatus(BaseModel):
    project_id: int
    status: str
    attack_paths_count: int
    recommendations_count: int
    last_updated: datetime


# Attack Path Schemas
class AttackPathCreate(BaseModel):
    name: str
    techniques: List[str]  # List of MITRE ATT&CK technique IDs
    priority_score: float = Field(..., ge=0.0, le=1.0)
    explanation: str


class AttackPathResponse(AttackPathCreate):
    id: int
    project_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Recommendation Schemas
class RecommendationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str
    priority: str = Field(..., pattern="^(high|medium|low)$")
    attack_technique: Optional[str] = None
    status: str = Field("proposed", pattern="^(proposed|accepted|implemented)$")


class RecommendationResponse(RecommendationCreate):
    id: int
    project_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Asset Schemas
class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    asset_type: str = Field(..., max_length=100)
    criticality: str = Field(..., pattern="^(high|medium|low)$")
    description: Optional[str] = None
    technologies: Optional[List[str]] = None


class AssetResponse(AssetCreate):
    id: int
    project_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# MITRE ATT&CK Schemas
class MitreAttackTechnique(BaseModel):
    technique_id: str
    name: str
    tactic: str
    description: str
    platforms: List[str]
    data_sources: List[str]
    mitigations: List[str]


# Agent Communication Schemas
class AgentTask(BaseModel):
    task_id: str
    agent_type: str
    task_description: str
    input_data: Dict[str, Any]
    priority: int = Field(default=1, ge=1, le=10)


class AgentResponse(BaseModel):
    task_id: str
    agent_type: str
    status: str = Field(..., pattern="^(success|failure|partial)$")
    output_data: Dict[str, Any]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    execution_time: float
    errors: Optional[List[str]] = None


# Shared Context Schema
class SharedContext(BaseModel):
    project_id: int
    system_description: Optional[str] = None
    identified_assets: List[Dict[str, Any]] = []
    identified_technologies: List[str] = []
    potential_entry_points: List[str] = []
    threat_actors_of_interest: List[str] = []
    attack_paths: List[Dict[str, Any]] = []
    control_evaluation_results: List[Dict[str, Any]] = []
    mitigation_recommendations: List[Dict[str, Any]] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)
