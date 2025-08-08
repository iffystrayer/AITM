"""
Pydantic Schemas for Agent Data Structures
Data models for multi-agent threat modeling system
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class CriticalityLevel(str, Enum):
    """Asset criticality levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExposureLevel(str, Enum):
    """Entry point exposure levels"""
    INTERNAL = "internal"
    EXTERNAL = "external"
    PARTNER = "partner"


class ImplementationQuality(str, Enum):
    """Control implementation quality levels"""
    POOR = "poor"
    BASIC = "basic"
    GOOD = "good"
    EXCELLENT = "excellent"


class MitigationLevel(str, Enum):
    """Control mitigation effectiveness levels"""
    NONE = "none"
    MINIMAL = "minimal"
    PARTIAL = "partial"
    SIGNIFICANT = "significant"
    COMPLETE = "complete"


class Priority(str, Enum):
    """Priority levels for recommendations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# System Analysis Schemas
class CriticalAsset(BaseModel):
    """Critical asset identified by System Analyst Agent"""
    name: str = Field(..., description="Asset name")
    type: str = Field(..., description="Asset type (database, server, application, etc.)")
    criticality: CriticalityLevel = Field(..., description="Asset criticality level")
    description: str = Field(..., description="Detailed asset description")
    data_classification: Optional[str] = Field(None, description="Data classification level")
    dependencies: Optional[List[str]] = Field(default_factory=list, description="Asset dependencies")


class SystemComponent(BaseModel):
    """System component identified by analysis"""
    name: str = Field(..., description="Component name")
    type: str = Field(..., description="Component type")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    version: Optional[str] = Field(None, description="Component version")
    purpose: str = Field(..., description="Component purpose")
    network_zone: Optional[str] = Field(None, description="Network zone location")


class DataFlow(BaseModel):
    """Data flow between components"""
    from_component: str = Field(..., alias="from", description="Source component")
    to_component: str = Field(..., alias="to", description="Destination component")
    data_type: str = Field(..., description="Type of data being transferred")
    protocol: Optional[str] = Field(None, description="Communication protocol")
    encryption: Optional[bool] = Field(None, description="Whether data is encrypted in transit")
    
    class Config:
        allow_population_by_field_name = True


class TrustBoundary(BaseModel):
    """Trust boundary in the system"""
    name: str = Field(..., description="Boundary name")
    type: str = Field(..., description="Boundary type (network, process, etc.)")
    description: str = Field(..., description="Boundary description")
    protection_level: Optional[str] = Field(None, description="Level of protection")


class EntryPoint(BaseModel):
    """System entry point"""
    name: str = Field(..., description="Entry point name")
    type: str = Field(..., description="Entry point type (web, API, etc.)")
    access_level: Optional[str] = Field(None, description="Required access level")
    authentication_required: Optional[bool] = Field(None, description="Whether authentication is required")
    exposure: ExposureLevel = Field(..., description="Exposure level")


class UserRole(BaseModel):
    """User role in the system"""
    role: str = Field(..., description="Role name")
    privileges: str = Field(..., description="Role privileges")
    access_pattern: Optional[str] = Field(None, description="Typical access patterns")


class SystemAnalysisSchema(BaseModel):
    """Complete system analysis results"""
    critical_assets: List[CriticalAsset] = Field(default_factory=list)
    system_components: List[SystemComponent] = Field(default_factory=list)
    data_flows: List[DataFlow] = Field(default_factory=list)
    trust_boundaries: List[TrustBoundary] = Field(default_factory=list)
    entry_points: List[EntryPoint] = Field(default_factory=list)
    user_roles: List[UserRole] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence score")
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)


# Attack Mapping Schemas
class TechniqueMapping(BaseModel):
    """MITRE ATT&CK technique mapping"""
    technique_id: str = Field(..., description="ATT&CK technique ID (e.g., T1059)")
    technique_name: str = Field(..., description="Technique name")
    tactic: str = Field(..., description="ATT&CK tactic")
    system_component: str = Field(..., description="Affected system component")
    applicability_score: float = Field(..., ge=0.0, le=1.0, description="Technique applicability score")
    rationale: str = Field(..., description="Why this technique applies")
    prerequisites: List[str] = Field(default_factory=list, description="Attack prerequisites")


class AttackStep(BaseModel):
    """Individual step in an attack path"""
    step: int = Field(..., description="Step number in the attack sequence")
    technique_id: str = Field(..., description="ATT&CK technique ID")
    technique_name: str = Field(..., description="Technique name")
    tactic: str = Field(..., description="ATT&CK tactic")
    target_component: str = Field(..., description="Target component")
    description: Optional[str] = Field(None, description="Step description")


class AttackPath(BaseModel):
    """Complete attack path"""
    path_id: str = Field(..., description="Unique path identifier")
    name: str = Field(..., description="Attack path name")
    description: str = Field(..., description="Attack path description")
    techniques: List[AttackStep] = Field(..., description="Attack steps")
    likelihood: str = Field(..., description="Attack likelihood")
    impact: str = Field(..., description="Potential impact")
    complexity: Optional[str] = Field(None, description="Attack complexity")


# Control Evaluation Schemas
class ControlCoverage(BaseModel):
    """Control coverage against specific technique"""
    technique_id: str = Field(..., description="ATT&CK technique ID")
    mitigation_level: MitigationLevel = Field(..., description="Mitigation effectiveness")
    confidence: str = Field(..., description="Confidence in assessment")


class ControlAssessment(BaseModel):
    """Assessment of a security control"""
    control_id: str = Field(..., description="Control identifier")
    control_name: str = Field(..., description="Control name")
    effectiveness_score: float = Field(..., ge=0.0, le=1.0, description="Overall effectiveness")
    coverage: List[ControlCoverage] = Field(..., description="Technique coverage")
    strengths: List[str] = Field(default_factory=list, description="Control strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Control weaknesses")
    implementation_quality: ImplementationQuality = Field(..., description="Implementation quality")


class CoverageGap(BaseModel):
    """Identified security control gap"""
    technique_id: str = Field(..., description="Uncovered technique ID")
    technique_name: str = Field(..., description="Technique name")
    gap_severity: Priority = Field(..., description="Gap severity level")
    current_coverage: Optional[str] = Field(None, description="Current coverage description")
    risk_description: str = Field(..., description="Risk description")


class OverallAssessment(BaseModel):
    """Overall control effectiveness assessment"""
    defense_score: float = Field(..., ge=0.0, le=1.0, description="Overall defense effectiveness")
    coverage_percentage: float = Field(..., ge=0.0, le=100.0, description="Technique coverage percentage")
    critical_gaps: int = Field(..., ge=0, description="Number of critical gaps")
    recommendations_priority: Optional[Priority] = Field(None, description="Recommendations priority")


# Recommendation Schemas
class MitigationRecommendation(BaseModel):
    """Security mitigation recommendation"""
    recommendation_id: str = Field(..., description="Unique recommendation ID")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed recommendation")
    priority: Priority = Field(..., description="Implementation priority")
    attack_technique: Optional[str] = Field(None, description="Related ATT&CK technique")
    affected_assets: List[str] = Field(default_factory=list, description="Affected assets")
    implementation_effort: Optional[str] = Field(None, description="Implementation effort estimate")
    cost_estimate: Optional[str] = Field(None, description="Cost estimate")
    timeline: Optional[str] = Field(None, description="Implementation timeline")


# Agent State Schemas
class TokenUsageSchema(BaseModel):
    """Token usage statistics"""
    prompt_tokens: int = Field(default=0, description="Prompt tokens used")
    completion_tokens: int = Field(default=0, description="Completion tokens used")
    total_tokens: int = Field(default=0, description="Total tokens used")
    estimated_cost: float = Field(default=0.0, description="Estimated cost")


class AgentMetadata(BaseModel):
    """Agent execution metadata"""
    model_used: Optional[str] = Field(None, description="LLM model used")
    provider_used: Optional[str] = Field(None, description="LLM provider used")
    response_time: Optional[float] = Field(None, description="Response time in seconds")
    token_usage: Optional[TokenUsageSchema] = Field(None, description="Token usage statistics")
    estimated_cost: Optional[float] = Field(None, description="Estimated execution cost")


class AgentStateSchema(BaseModel):
    """Agent state information"""
    agent_id: str = Field(..., description="Agent identifier")
    agent_type: str = Field(..., description="Agent type")
    status: AgentStatus = Field(..., description="Current status")
    start_time: Optional[datetime] = Field(None, description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Progress percentage")
    current_task: Optional[str] = Field(None, description="Current task description")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="Agent outputs")


# Request/Response Schemas
class SystemAnalysisRequest(BaseModel):
    """Request for system analysis"""
    system_description: str = Field(..., description="System description to analyze")
    additional_inputs: Optional[List[Dict[str, Any]]] = Field(None, description="Additional system inputs")
    preferred_model: Optional[str] = Field(None, description="Preferred LLM model")
    
    @validator('system_description')
    def validate_description_length(cls, v):
        if len(v.strip()) < 50:
            raise ValueError('System description must be at least 50 characters long')
        return v.strip()


class ThreatModelingRequest(BaseModel):
    """Request to start threat modeling analysis"""
    include_system_analysis: bool = Field(default=True, description="Include system analysis step")
    include_attack_mapping: bool = Field(default=True, description="Include attack mapping step")
    include_control_evaluation: bool = Field(default=True, description="Include control evaluation step")
    preferred_model: Optional[str] = Field(None, description="Preferred LLM model")
    analysis_depth: str = Field(default="standard", description="Analysis depth level")
    
    @validator('analysis_depth')
    def validate_analysis_depth(cls, v):
        allowed_depths = ["basic", "standard", "comprehensive"]
        if v not in allowed_depths:
            raise ValueError(f'Analysis depth must be one of: {allowed_depths}')
        return v


class ThreatModelingResponse(BaseModel):
    """Response from threat modeling analysis"""
    project_id: int = Field(..., description="Project ID")
    status: str = Field(..., description="Analysis status")
    message: str = Field(..., description="Status message")
    started_at: Optional[datetime] = Field(None, description="Analysis start time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


class ThreatModelingStatus(BaseModel):
    """Current status of threat modeling analysis"""
    project_id: int = Field(..., description="Project ID")
    status: str = Field(..., description="Current status")
    overall_progress: float = Field(..., ge=0.0, le=1.0, description="Overall progress")
    agents: Dict[str, AgentStateSchema] = Field(default_factory=dict, description="Agent states")
    completed_milestones: List[str] = Field(default_factory=list, description="Completed milestones")
    attack_paths_count: int = Field(default=0, description="Number of attack paths identified")
    recommendations_count: int = Field(default=0, description="Number of recommendations generated")
    last_updated: Optional[datetime] = Field(None, description="Last update time")
