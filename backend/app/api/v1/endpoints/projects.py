"""
Projects API endpoints with authentication
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, Project, SystemInput, AnalysisState, AnalysisResults
from app.api.endpoints.auth import get_current_active_user
from app.models.user import User
from app.models.schemas import (
    ProjectCreate, ProjectResponse, ProjectUpdate, SystemInputCreate,
    AnalysisStartRequest, AnalysisStartResponse, AnalysisStatusResponse,
    AnalysisResultsResponse, AnalysisProgress
)

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new threat modeling project"""
    project_data = project.dict()
    project_data["owner_user_id"] = current_user.id
    
    db_project = Project(**project_data)
    db.add(db_project)
    await db.flush()
    await db.refresh(db_project)
    
    # Log activity (import collaboration service)
    from app.services.collaboration_service import get_collaboration_service
    from app.models.collaboration import ActivityType
    collab_service = get_collaboration_service()
    await collab_service._log_activity(
        db,
        user_id=current_user.id,
        project_id=db_project.id,
        activity_type=ActivityType.PROJECT_CREATED,
        description=f"Created project '{project.name}'",
        metadata={"project_name": project.name}
    )
    
    return db_project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all threat modeling projects"""
    result = await db.execute(
        select(Project).offset(skip).limit(limit).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific project by ID"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    await db.flush()
    await db.refresh(project)
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    await db.delete(project)
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/inputs", status_code=status.HTTP_201_CREATED)
async def add_system_input(
    project_id: int,
    system_input: SystemInputCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add system input data to a project"""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db_input = SystemInput(project_id=project_id, **system_input.dict())
    db.add(db_input)
    await db.flush()
    await db.refresh(db_input)
    
    return {"message": "System input added successfully", "input_id": db_input.id}


@router.get("/{project_id}/inputs")
async def get_project_inputs(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all system inputs for a project"""
    result = await db.execute(
        select(SystemInput).where(SystemInput.project_id == project_id)
    )
    inputs = result.scalars().all()
    return {"data": inputs}


# Analysis endpoints
from datetime import datetime
import json
import asyncio


@router.post("/{project_id}/analysis/start", response_model=AnalysisStartResponse)
async def start_analysis(
    project_id: int,
    request: AnalysisStartRequest,
    db: AsyncSession = Depends(get_db)
):
    """Start threat analysis for a project"""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify system inputs exist
    if request.input_ids:
        input_result = await db.execute(
            select(SystemInput).where(
                SystemInput.project_id == project_id,
                SystemInput.id.in_(request.input_ids)
            )
        )
        inputs = input_result.scalars().all()
        if len(inputs) != len(request.input_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some input IDs not found"
            )
    
    # Check if analysis is already running
    state_result = await db.execute(
        select(AnalysisState).where(AnalysisState.project_id == project_id)
    )
    existing_state = state_result.scalar_one_or_none()
    
    if existing_state and existing_state.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis is already running for this project"
        )
    
    # Create or update analysis state
    now = datetime.utcnow()
    if existing_state:
        existing_state.status = "running"
        existing_state.current_phase = "system_analysis"
        existing_state.progress_percentage = 0.0
        existing_state.progress_message = "Initializing threat analysis..."
        existing_state.started_at = now
        existing_state.completed_at = None
        existing_state.error_message = None
        existing_state.configuration = json.dumps(request.config)
        existing_state.updated_at = now
    else:
        existing_state = AnalysisState(
            project_id=project_id,
            status="running",
            current_phase="system_analysis",
            progress_percentage=0.0,
            progress_message="Initializing threat analysis...",
            started_at=now,
            configuration=json.dumps(request.config)
        )
        db.add(existing_state)
    
    # Update project status
    project.status = "analyzing"
    project.updated_at = now
    
    await db.flush()
    
    # Start the analysis in the background
    asyncio.create_task(run_analysis_workflow(project_id, request.input_ids, request.config))
    
    return AnalysisStartResponse(
        project_id=project_id,
        status="running",
        message="Threat analysis started successfully",
        started_at=now
    )


@router.get("/{project_id}/analysis/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get current analysis status for a project"""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get analysis state
    state_result = await db.execute(
        select(AnalysisState).where(AnalysisState.project_id == project_id)
    )
    analysis_state = state_result.scalar_one_or_none()
    
    if not analysis_state:
        return AnalysisStatusResponse(
            project_id=project_id,
            status="idle"
        )
    
    progress = None
    if analysis_state.status == "running":
        progress = AnalysisProgress(
            current_phase=analysis_state.current_phase,
            percentage=analysis_state.progress_percentage or 0.0,
            message=analysis_state.progress_message
        )
    
    return AnalysisStatusResponse(
        project_id=project_id,
        status=analysis_state.status,
        progress=progress,
        started_at=analysis_state.started_at,
        completed_at=analysis_state.completed_at,
        error_message=analysis_state.error_message
    )


@router.get("/{project_id}/analysis/results", response_model=AnalysisResultsResponse)
async def get_analysis_results(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get analysis results for a project"""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get analysis results
    results_query = await db.execute(
        select(AnalysisResults).where(AnalysisResults.project_id == project_id)
    )
    analysis_results = results_query.scalar_one_or_none()
    
    if not analysis_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis results found for this project"
        )
    
    # Parse JSON fields
    def safe_json_loads(json_str, default=None):
        if not json_str:
            return default or []
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return default or []
    
    return AnalysisResultsResponse(
        project_id=project_id,
        overall_risk_score=analysis_results.overall_risk_score or 0.0,
        confidence_score=analysis_results.confidence_score or 0.0,
        executive_summary=safe_json_loads(analysis_results.executive_summary),
        attack_paths=safe_json_loads(analysis_results.attack_paths_data, []),
        identified_techniques=safe_json_loads(analysis_results.identified_techniques, []),
        recommendations=safe_json_loads(analysis_results.recommendations_data, []),
        system_analysis_results=safe_json_loads(analysis_results.system_analysis_results, []),
        control_evaluation_results=safe_json_loads(analysis_results.control_evaluation_results, []),
        full_report=safe_json_loads(analysis_results.full_report),
        created_at=analysis_results.created_at,
        updated_at=analysis_results.updated_at
    )


# Background task for running analysis workflow
async def run_analysis_workflow(project_id: int, input_ids: List[int], config: dict):
    """Run the complete analysis workflow using AI agents"""
    from app.core.database import async_session
    from app.agents.system_analyst_agent import SystemAnalystAgent
    from app.agents.attack_mapper_agent import AttackMapperAgent, ControlEvaluationAgent
    from app.agents.report_generation_agent import ReportGenerationAgent
    from app.models.schemas import AgentTask
    import uuid
    
    async with async_session() as db:
        try:
            # Update status: Starting system analysis
            await update_analysis_progress(
                db, project_id, "system_analysis", 10, "Starting system analysis..."
            )
            
            # Step 1: System Analysis
            system_agent = SystemAnalystAgent()
            system_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_type="system_analyst",
                task_description="Analyze system architecture and identify components",
                input_data={
                    "project_id": project_id,
                    "input_ids": input_ids,
                    "config": config
                }
            )
            
            await update_analysis_progress(
                db, project_id, "system_analysis", 25, "Analyzing system components..."
            )
            
            system_response = await system_agent.process_task(system_task)
            if system_response.status != "success":
                await mark_analysis_failed(db, project_id, "System analysis failed")
                return
            
            # Step 2: Attack Mapping
            await update_analysis_progress(
                db, project_id, "attack_mapping", 40, "Mapping attack techniques..."
            )
            
            attack_agent = AttackMapperAgent()
            attack_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_type="attack_mapper",
                task_description="Map MITRE ATT&CK techniques to system",
                input_data={
                    "project_id": project_id,
                    "system_analysis": system_response.output_data
                }
            )
            
            attack_response = await attack_agent.process_task(attack_task)
            if attack_response.status != "success":
                await mark_analysis_failed(db, project_id, "Attack mapping failed")
                return
            
            # Step 3: Control Evaluation
            await update_analysis_progress(
                db, project_id, "control_evaluation", 65, "Evaluating security controls..."
            )
            
            control_agent = ControlEvaluationAgent()
            control_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_type="control_evaluator",
                task_description="Evaluate existing security controls",
                input_data={
                    "project_id": project_id,
                    "attack_analysis": attack_response.output_data
                }
            )
            
            control_response = await control_agent.process_task(control_task)
            if control_response.status != "success":
                await mark_analysis_failed(db, project_id, "Control evaluation failed")
                return
            
            # Step 4: Report Generation
            await update_analysis_progress(
                db, project_id, "report_generation", 85, "Generating comprehensive report..."
            )
            
            report_agent = ReportGenerationAgent()
            report_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_type="report_generator",
                task_description="Generate comprehensive threat modeling report",
                input_data={
                    "project_id": project_id,
                    "system_analysis": system_response.output_data,
                    "attack_analysis": attack_response.output_data,
                    "control_analysis": control_response.output_data
                }
            )
            
            report_response = await report_agent.process_task(report_task)
            if report_response.status != "success":
                await mark_analysis_failed(db, project_id, "Report generation failed")
                return
            
            # Step 5: Store Results
            await update_analysis_progress(
                db, project_id, "finalizing", 95, "Storing analysis results..."
            )
            
            await store_analysis_results(
                db, project_id, 
                system_response.output_data,
                attack_response.output_data,
                control_response.output_data,
                report_response.output_data
            )
            
            # Mark as completed
            await mark_analysis_completed(db, project_id)
            
        except Exception as e:
            await mark_analysis_failed(db, project_id, f"Analysis workflow failed: {str(e)}")
            import logging
            logging.error(f"Analysis workflow failed for project {project_id}: {str(e)}", exc_info=True)


async def update_analysis_progress(db: AsyncSession, project_id: int, phase: str, percentage: float, message: str):
    """Update analysis progress in database"""
    result = await db.execute(select(AnalysisState).where(AnalysisState.project_id == project_id))
    state = result.scalar_one_or_none()
    
    if state:
        state.current_phase = phase
        state.progress_percentage = percentage
        state.progress_message = message
        state.updated_at = datetime.utcnow()
        await db.commit()


async def mark_analysis_failed(db: AsyncSession, project_id: int, error_message: str):
    """Mark analysis as failed"""
    result = await db.execute(select(AnalysisState).where(AnalysisState.project_id == project_id))
    state = result.scalar_one_or_none()
    
    if state:
        state.status = "failed"
        state.error_message = error_message
        state.completed_at = datetime.utcnow()
        state.updated_at = datetime.utcnow()
        
    # Update project status
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if project:
        project.status = "failed"
        project.updated_at = datetime.utcnow()
    
    await db.commit()


async def mark_analysis_completed(db: AsyncSession, project_id: int):
    """Mark analysis as completed"""
    result = await db.execute(select(AnalysisState).where(AnalysisState.project_id == project_id))
    state = result.scalar_one_or_none()
    
    if state:
        state.status = "completed"
        state.current_phase = "completed"
        state.progress_percentage = 100.0
        state.progress_message = "Analysis completed successfully"
        state.completed_at = datetime.utcnow()
        state.updated_at = datetime.utcnow()
        
    # Update project status
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if project:
        project.status = "completed"
        project.updated_at = datetime.utcnow()
    
    await db.commit()


async def store_analysis_results(db: AsyncSession, project_id: int, system_data: dict, 
                                attack_data: dict, control_data: dict, report_data: dict):
    """Store comprehensive analysis results"""
    # Check if results already exist
    result = await db.execute(select(AnalysisResults).where(AnalysisResults.project_id == project_id))
    analysis_results = result.scalar_one_or_none()
    
    # Calculate overall metrics
    overall_risk_score = report_data.get("metrics", {}).get("residual_risk", 0.5)
    confidence_score = min(
        system_data.get("confidence_score", 0.8),
        attack_data.get("confidence_score", 0.8),
        control_data.get("confidence_score", 0.8),
        report_data.get("confidence_score", 0.8)
    )
    
    now = datetime.utcnow()
    
    if analysis_results:
        # Update existing results
        analysis_results.overall_risk_score = overall_risk_score
        analysis_results.confidence_score = confidence_score
        analysis_results.executive_summary = json.dumps(report_data.get("executive_summary", {}))
        analysis_results.system_analysis_results = json.dumps([system_data])
        analysis_results.identified_techniques = json.dumps(attack_data.get("technique_mappings", []))
        analysis_results.attack_paths_data = json.dumps(attack_data.get("attack_paths", []))
        analysis_results.control_evaluation_results = json.dumps([control_data])
        analysis_results.recommendations_data = json.dumps(report_data.get("recommendations", {}).get("immediate_actions", []))
        analysis_results.full_report = json.dumps(report_data)
        analysis_results.updated_at = now
    else:
        # Create new results
        analysis_results = AnalysisResults(
            project_id=project_id,
            overall_risk_score=overall_risk_score,
            confidence_score=confidence_score,
            executive_summary=json.dumps(report_data.get("executive_summary", {})),
            system_analysis_results=json.dumps([system_data]),
            identified_techniques=json.dumps(attack_data.get("technique_mappings", [])),
            attack_paths_data=json.dumps(attack_data.get("attack_paths", [])),
            control_evaluation_results=json.dumps([control_data]),
            recommendations_data=json.dumps(report_data.get("recommendations", {}).get("immediate_actions", [])),
            full_report=json.dumps(report_data)
        )
        db.add(analysis_results)
    
    await db.commit()
