"""
Threat modeling API endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, Project, AttackPath, Recommendation
from app.models.schemas import ThreatModelingRequest, ThreatModelingResponse, ThreatModelingStatus
from app.services.orchestrator import ThreatModelingOrchestrator

router = APIRouter()


@router.post("/{project_id}/analyze", response_model=ThreatModelingResponse)
async def start_threat_modeling(
    project_id: int,
    request: ThreatModelingRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Start threat modeling analysis for a project"""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update project status
    project.status = "analyzing"
    
    # Initialize orchestrator
    orchestrator = ThreatModelingOrchestrator()
    
    # Start background analysis
    background_tasks.add_task(
        orchestrator.analyze_project,
        project_id,
        request.dict()
    )
    
    return ThreatModelingResponse(
        project_id=project_id,
        status="started",
        message="Threat modeling analysis started. Check status for progress."
    )


@router.get("/{project_id}/status", response_model=ThreatModelingStatus)
async def get_threat_modeling_status(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the current status of threat modeling analysis"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Count results
    attack_paths_result = await db.execute(
        select(AttackPath).where(AttackPath.project_id == project_id)
    )
    attack_paths_count = len(attack_paths_result.scalars().all())
    
    recommendations_result = await db.execute(
        select(Recommendation).where(Recommendation.project_id == project_id)
    )
    recommendations_count = len(recommendations_result.scalars().all())
    
    return ThreatModelingStatus(
        project_id=project_id,
        status=project.status,
        attack_paths_count=attack_paths_count,
        recommendations_count=recommendations_count,
        last_updated=project.updated_at
    )


@router.get("/{project_id}/results/attack-paths")
async def get_attack_paths(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get identified attack paths for a project"""
    result = await db.execute(
        select(AttackPath).where(AttackPath.project_id == project_id)
        .order_by(AttackPath.priority_score.desc())
    )
    attack_paths = result.scalars().all()
    return attack_paths


@router.get("/{project_id}/results/recommendations")
async def get_recommendations(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get security recommendations for a project"""
    result = await db.execute(
        select(Recommendation).where(Recommendation.project_id == project_id)
        .order_by(Recommendation.priority.desc())
    )
    recommendations = result.scalars().all()
    return recommendations


@router.get("/{project_id}/results/summary")
async def get_threat_modeling_summary(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a summary of threat modeling results"""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get attack paths
    attack_paths_result = await db.execute(
        select(AttackPath).where(AttackPath.project_id == project_id)
        .order_by(AttackPath.priority_score.desc())
    )
    attack_paths = attack_paths_result.scalars().all()
    
    # Get recommendations
    recommendations_result = await db.execute(
        select(Recommendation).where(Recommendation.project_id == project_id)
        .order_by(Recommendation.priority.desc())
    )
    recommendations = recommendations_result.scalars().all()
    
    # Calculate summary statistics
    high_priority_paths = [ap for ap in attack_paths if ap.priority_score > 0.7]
    critical_recommendations = [r for r in recommendations if r.priority == "high"]
    
    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "status": project.status,
            "last_updated": project.updated_at
        },
        "summary": {
            "total_attack_paths": len(attack_paths),
            "high_priority_paths": len(high_priority_paths),
            "total_recommendations": len(recommendations),
            "critical_recommendations": len(critical_recommendations)
        },
        "attack_paths": [
            {
                "id": ap.id,
                "name": ap.name,
                "priority_score": ap.priority_score,
                "techniques": ap.techniques
            } for ap in attack_paths[:5]  # Top 5 attack paths
        ],
        "recommendations": [
            {
                "id": r.id,
                "title": r.title,
                "priority": r.priority,
                "attack_technique": r.attack_technique
            } for r in recommendations[:10]  # Top 10 recommendations
        ]
    }
