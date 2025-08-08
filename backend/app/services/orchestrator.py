"""
Threat Modeling Orchestrator using Langgraph for multi-agent workflow
"""

import json
import logging
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import async_session, Project, AttackPath, Recommendation
from app.agents.base_agent import SharedContextManager, SystemAnalystAgent
from app.agents.attack_mapper_agent import AttackMapperAgent, ControlEvaluationAgent
from app.agents.report_generation_agent import ReportGenerationAgent
from app.models.schemas import AgentTask
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ThreatModelingOrchestrator:
    """
    Master orchestrator for the threat modeling workflow
    Coordinates multiple agents to complete the analysis
    """
    
    def __init__(self):
        # Initialize agents
        self.system_analyst = SystemAnalystAgent()
        self.attack_mapper = AttackMapperAgent()
        self.control_evaluator = ControlEvaluationAgent()
        self.report_generator = ReportGenerationAgent()
        
        # Agent registry
        self.agents = {
            "system_analyst": self.system_analyst,
            "attack_mapper": self.attack_mapper,
            "control_evaluator": self.control_evaluator,
            "report_generator": self.report_generator
        }
    
    async def analyze_project(self, project_id: int, analysis_config: Dict[str, Any]):
        """
        Main orchestration method - coordinates the entire threat modeling process
        """
        logger.info(f"Starting threat modeling analysis for project {project_id}")
        
        try:
            # Initialize shared context
            context_manager = SharedContextManager(project_id)
            
            # Set context for all agents
            for agent in self.agents.values():
                agent.set_context_manager(context_manager)
            
            # Update project status
            await self._update_project_status(project_id, "analyzing")
            
            # Get system input data
            system_inputs = await self._get_system_inputs(project_id)
            if not system_inputs:
                await self._update_project_status(project_id, "failed")
                logger.error(f"No system inputs found for project {project_id}")
                return
            
            # Combine all system inputs
            combined_description = "\\n\\n".join([
                input_data.content for input_data in system_inputs
            ])
            
            # Step 1: System Analysis
            logger.info(f"Step 1: System Analysis for project {project_id}")
            analysis_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_type="system_analyst",
                task_description="Analyze system description and identify assets, technologies, and entry points",
                input_data={"system_description": combined_description}
            )
            
            analysis_result = await self.system_analyst.process_task(analysis_task)
            
            if analysis_result.status != "success":
                logger.error(f"System analysis failed for project {project_id}: {analysis_result.errors}")
                await self._update_project_status(project_id, "failed")
                return
            
            # Step 2: Attack Path Mapping
            logger.info(f"Step 2: Attack Path Mapping for project {project_id}")
            mapping_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_type="attack_mapper",
                task_description="Map system components to ATT&CK techniques and generate attack paths",
                input_data={"analysis_depth": analysis_config.get("analysis_depth", "standard")}
            )
            
            mapping_result = await self.attack_mapper.process_task(mapping_task)
            
            if mapping_result.status != "success":
                logger.error(f"Attack mapping failed for project {project_id}: {mapping_result.errors}")
                await self._update_project_status(project_id, "failed")
                return
            
            # Step 3: Control Evaluation (if requested)
            if analysis_config.get("include_mitigations", True):
                logger.info(f"Step 3: Control Evaluation for project {project_id}")
                control_task = AgentTask(
                    task_id=str(uuid.uuid4()),
                    agent_type="control_evaluator",
                    task_description="Evaluate existing controls against identified techniques",
                    input_data={
                        "existing_controls": analysis_config.get("existing_controls", []),
                        "control_documentation": analysis_config.get("control_documentation", "")
                    }
                )
                
                control_result = await self.control_evaluator.process_task(control_task)
                
                if control_result.status != "success":
                    logger.warning(f"Control evaluation failed for project {project_id}, continuing without it")
            
            # Step 4: Generate Recommendations
            logger.info(f"Step 4: Generate Recommendations for project {project_id}")
            await self._generate_recommendations(project_id, context_manager)
            
            # Step 5: Generate Comprehensive Report
            logger.info(f"Step 5: Generate Comprehensive Report for project {project_id}")
            report_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_type="report_generator",
                task_description="Generate comprehensive threat modeling report",
                input_data={
                    "include_executive_summary": analysis_config.get("include_executive_summary", True),
                    "include_technical_details": analysis_config.get("include_technical_details", True),
                    "report_format": analysis_config.get("report_format", "comprehensive")
                }
            )
            
            report_result = await self.report_generator.process_task(report_task)
            
            if report_result.status != "success":
                logger.warning(f"Report generation failed for project {project_id}, continuing without it")
            
            # Step 6: Store Results in Database
            logger.info(f"Step 6: Storing results for project {project_id}")
            await self._store_results(project_id, context_manager)
            
            # Mark as completed
            await self._update_project_status(project_id, "completed")
            logger.info(f"Threat modeling analysis completed for project {project_id}")
            
        except Exception as e:
            logger.error(f"Threat modeling analysis failed for project {project_id}: {str(e)}", exc_info=True)
            await self._update_project_status(project_id, "failed")
    
    async def _get_system_inputs(self, project_id: int):
        """Get system inputs for the project"""
        async with async_session() as db:
            from app.core.database import SystemInput
            result = await db.execute(
                select(SystemInput).where(SystemInput.project_id == project_id)
            )
            return result.scalars().all()
    
    async def _update_project_status(self, project_id: int, status: str):
        """Update project status in database"""
        async with async_session() as db:
            await db.execute(
                update(Project)
                .where(Project.id == project_id)
                .values(status=status, updated_at=datetime.utcnow())
            )
            await db.commit()
    
    async def _generate_recommendations(self, project_id: int, context_manager: SharedContextManager):
        """Generate security recommendations based on analysis results"""
        context = context_manager.read_context()
        
        # Create prompt for recommendations
        attack_paths_summary = "\\n".join([
            f"- {path.get('name', 'Unnamed')}: {path.get('explanation', 'No explanation')}"
            for path in context.attack_paths[:5]  # Top 5 paths
        ])
        
        control_gaps = []
        if context.control_evaluation_results:
            for evaluation in context.control_evaluation_results:
                priority_gaps = evaluation.get('priority_gaps', [])
                control_gaps.extend([gap.get('gap_description', '') for gap in priority_gaps])
        
        prompt = f'''Based on the threat modeling analysis, generate specific security recommendations:

TOP ATTACK PATHS IDENTIFIED:
{attack_paths_summary}

IDENTIFIED CONTROL GAPS:
{chr(10).join(control_gaps[:10]) if control_gaps else "No specific control gaps documented"}

Please provide actionable security recommendations in JSON format:
{{
    "recommendations": [
        {{
            "title": "Recommendation title",
            "description": "Detailed description of the recommended action",
            "priority": "high|medium|low",
            "attack_technique": "T1234",
            "implementation_effort": "high|medium|low",
            "estimated_cost": "high|medium|low",
            "timeline": "immediate|short-term|long-term"
        }}
    ]
}}

Focus on practical, prioritized recommendations that address the most significant risks.'''
        
        try:
            llm_response = await llm_service.generate_response(
                prompt=prompt,
                system_prompt="You are a cybersecurity consultant providing actionable security recommendations.",
                temperature=0.6
            )
            
            if llm_response['success']:
                recommendations_data = json.loads(llm_response['response'])
                recommendations = recommendations_data.get('recommendations', [])
                
                # Update context
                context_manager.update_context({
                    'mitigation_recommendations': recommendations
                })
                
                logger.info(f"Generated {len(recommendations)} recommendations for project {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations for project {project_id}: {e}")
    
    async def _store_results(self, project_id: int, context_manager: SharedContextManager):
        """Store analysis results in database"""
        context = context_manager.read_context()
        
        async with async_session() as db:
            try:
                # Store attack paths
                for path_data in context.attack_paths:
                    attack_path = AttackPath(
                        project_id=project_id,
                        name=path_data.get('name', 'Unnamed Attack Path'),
                        techniques=json.dumps(path_data.get('techniques', [])),
                        priority_score=float(path_data.get('priority_score', 0.5)),
                        explanation=path_data.get('explanation', '')
                    )
                    db.add(attack_path)
                
                # Store recommendations
                for rec_data in context.mitigation_recommendations:
                    recommendation = Recommendation(
                        project_id=project_id,
                        title=rec_data.get('title', 'Unnamed Recommendation'),
                        description=rec_data.get('description', ''),
                        priority=rec_data.get('priority', 'medium'),
                        attack_technique=rec_data.get('attack_technique', ''),
                        status='proposed'
                    )
                    db.add(recommendation)
                
                await db.commit()
                logger.info(f"Stored {len(context.attack_paths)} attack paths and {len(context.mitigation_recommendations)} recommendations for project {project_id}")
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to store results for project {project_id}: {e}")
                raise
