"""
System Analyst Agent
Analyzes system descriptions to identify critical security components
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..services.enhanced_llm_service import get_enhanced_llm_service
from ..services.llm_providers import LLMError, LLMModel
from ..core.prompts import get_system_analyst_prompt, AgentType
from .shared_context import SharedContext

logger = logging.getLogger(__name__)


@dataclass
class SystemAnalysisResult:
    """Results of system analysis"""
    critical_assets: List[Dict[str, Any]]
    system_components: List[Dict[str, Any]]
    data_flows: List[Dict[str, Any]]
    trust_boundaries: List[Dict[str, Any]]
    entry_points: List[Dict[str, Any]]
    user_roles: List[Dict[str, Any]]
    confidence_score: float
    analysis_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "critical_assets": self.critical_assets,
            "system_components": self.system_components,
            "data_flows": self.data_flows,
            "trust_boundaries": self.trust_boundaries,
            "entry_points": self.entry_points,
            "user_roles": self.user_roles,
            "confidence_score": self.confidence_score,
            "analysis_metadata": self.analysis_metadata
        }


class SystemAnalystAgent:
    """
    System Analyst Agent for AITM
    
    Responsible for:
    1. Parsing system descriptions
    2. Identifying critical assets and components
    3. Determining system architecture and data flows
    4. Identifying trust boundaries and entry points
    5. Mapping user roles and access patterns
    """
    
    def __init__(self, agent_id: str = "system_analyst"):
        self.agent_id = agent_id
        self.agent_type = "system_analyst"
        self.llm_service = get_enhanced_llm_service()
        
        # Preferred models (in order of preference)
        self.preferred_models = [
            LLMModel.GPT_4O,           # Best for complex analysis
            LLMModel.CLAUDE_3_5_SONNET,  # Excellent for structured thinking
            LLMModel.GPT_4O_MINI,      # Good balance of speed and quality
            LLMModel.CLAUDE_3_HAIKU,   # Fast and cost-effective
        ]
    
    async def analyze_system(
        self, 
        context: SharedContext,
        system_description: str,
        additional_inputs: Optional[List[Dict[str, Any]]] = None,
        preferred_model: Optional[LLMModel] = None
    ) -> SystemAnalysisResult:
        """
        Analyze a system description and extract security-relevant components
        
        Args:
            context: Shared context for multi-agent coordination
            system_description: Text description of the system to analyze
            additional_inputs: Optional additional system information
            preferred_model: Preferred LLM model to use
            
        Returns:
            SystemAnalysisResult with extracted components
        """
        async with context.agent_session(self.agent_id, self.agent_type) as ctx:
            try:
                await ctx.update_agent_status(
                    self.agent_id, 
                    "running", 
                    0.1, 
                    "Preparing system analysis"
                )
                
                # Prepare input data
                full_description = self._prepare_input_data(system_description, additional_inputs)
                
                await ctx.update_agent_status(
                    self.agent_id, 
                    "running", 
                    0.2, 
                    "Generating analysis prompts"
                )
                
                # Get formatted prompts
                system_prompt, user_prompt, response_schema = get_system_analyst_prompt(full_description)
                
                await ctx.update_agent_status(
                    self.agent_id, 
                    "running", 
                    0.3, 
                    "Calling LLM for analysis"
                )
                
                # Perform analysis with retries
                analysis_response = await self._perform_analysis_with_retry(
                    system_prompt, user_prompt, response_schema, preferred_model
                )
                
                await ctx.update_agent_status(
                    self.agent_id, 
                    "running", 
                    0.7, 
                    "Processing and validating analysis results"
                )
                
                # Parse and validate results
                analysis_data = self._parse_and_validate_response(analysis_response, full_description)
                
                # Create structured result
                result = SystemAnalysisResult(
                    critical_assets=analysis_data.get("critical_assets", []),
                    system_components=analysis_data.get("system_components", []),
                    data_flows=analysis_data.get("data_flows", []),
                    trust_boundaries=analysis_data.get("trust_boundaries", []),
                    entry_points=analysis_data.get("entry_points", []),
                    user_roles=analysis_data.get("user_roles", []),
                    confidence_score=self._calculate_confidence_score(analysis_data),
                    analysis_metadata={
                        "model_used": analysis_response.model,
                        "provider_used": analysis_response.provider,
                        "response_time": analysis_response.response_time,
                        "token_usage": analysis_response.token_usage.to_dict() if analysis_response.token_usage else None,
                        "estimated_cost": analysis_response.token_usage.estimated_cost if analysis_response.token_usage else 0.0,
                        "input_length": len(full_description),
                        "output_length": len(analysis_response.content)
                    }
                )
                
                await ctx.update_agent_status(
                    self.agent_id, 
                    "running", 
                    0.9, 
                    "Storing analysis results in shared context"
                )
                
                # Store results in shared context
                await ctx.set_data("system_analysis", result.to_dict(), self.agent_id)
                
                # Store individual components for other agents to use
                await ctx.set_data("critical_assets", result.critical_assets, self.agent_id)
                await ctx.set_data("system_components", result.system_components, self.agent_id)
                await ctx.set_data("data_flows", result.data_flows, self.agent_id)
                await ctx.set_data("trust_boundaries", result.trust_boundaries, self.agent_id)
                await ctx.set_data("entry_points", result.entry_points, self.agent_id)
                await ctx.set_data("user_roles", result.user_roles, self.agent_id)
                
                await ctx.update_agent_status(
                    self.agent_id, 
                    "completed", 
                    1.0, 
                    f"Analysis complete: {len(result.critical_assets)} assets, {len(result.system_components)} components identified"
                )
                
                logger.info(f"System analysis completed successfully. "
                          f"Identified {len(result.critical_assets)} critical assets, "
                          f"{len(result.system_components)} components, "
                          f"{len(result.entry_points)} entry points")
                
                return result
                
            except Exception as e:
                error_msg = f"System analysis failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                await ctx.update_agent_status(
                    self.agent_id, 
                    "failed", 
                    error_message=error_msg
                )
                raise
    
    def _prepare_input_data(
        self, 
        system_description: str, 
        additional_inputs: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Prepare and enhance the input data for analysis"""
        full_description = system_description.strip()
        
        if additional_inputs:
            full_description += "\n\nAdditional System Information:\n"
            for i, input_data in enumerate(additional_inputs, 1):
                if input_data.get('content'):
                    full_description += f"\n{i}. {input_data.get('type', 'Additional Info')}: {input_data['content']}\n"
        
        return full_description
    
    async def _perform_analysis_with_retry(
        self,
        system_prompt: str,
        user_prompt: str, 
        response_schema: Dict[str, Any],
        preferred_model: Optional[LLMModel] = None
    ):
        """Perform analysis with model fallback on failure"""
        models_to_try = [preferred_model] if preferred_model else []
        models_to_try.extend([m for m in self.preferred_models if m != preferred_model])
        
        last_error = None
        
        for model in models_to_try:
            try:
                logger.info(f"Attempting system analysis with model: {model.value if model else 'auto'}")
                
                response = await self.llm_service.generate_structured_completion(
                    prompt=user_prompt,
                    response_schema=response_schema,
                    system_prompt=system_prompt,
                    model=model,
                    temperature=0.1,
                    max_tokens=4000
                )
                
                logger.info(f"System analysis successful with model: {response.model}")
                return response
                
            except LLMError as e:
                last_error = e
                logger.warning(f"Analysis failed with model {model.value if model else 'auto'}: {e}")
                continue
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error with model {model.value if model else 'auto'}: {e}")
                continue
        
        # If all models failed
        raise LLMError(f"System analysis failed with all available models. Last error: {last_error}")
    
    def _parse_and_validate_response(self, response, original_input: str) -> Dict[str, Any]:
        """Parse and validate the LLM response"""
        try:
            # Parse JSON response
            analysis_data = json.loads(response.content)
            
            # Basic validation
            required_keys = ["critical_assets", "system_components", "data_flows", "trust_boundaries", "entry_points"]
            missing_keys = [key for key in required_keys if key not in analysis_data]
            
            if missing_keys:
                logger.warning(f"Analysis response missing required keys: {missing_keys}")
                # Add empty lists for missing keys
                for key in missing_keys:
                    analysis_data[key] = []
            
            # Validate data types
            for key in required_keys:
                if not isinstance(analysis_data[key], list):
                    logger.warning(f"Converting {key} to list format")
                    analysis_data[key] = []
            
            # Validate critical assets have required fields
            for i, asset in enumerate(analysis_data.get("critical_assets", [])):
                if not isinstance(asset, dict) or not asset.get("name"):
                    logger.warning(f"Invalid critical asset at index {i}: {asset}")
                    continue
                
                # Ensure required fields exist
                if "criticality" not in asset:
                    asset["criticality"] = "medium"  # Default
                if "type" not in asset:
                    asset["type"] = "unknown"
                if "description" not in asset:
                    asset["description"] = asset.get("name", "No description available")
            
            # Add validation metadata
            analysis_data["validation"] = {
                "input_length": len(original_input),
                "total_assets": len(analysis_data.get("critical_assets", [])),
                "total_components": len(analysis_data.get("system_components", [])),
                "total_flows": len(analysis_data.get("data_flows", [])),
                "total_boundaries": len(analysis_data.get("trust_boundaries", [])),
                "total_entry_points": len(analysis_data.get("entry_points", [])),
                "has_user_roles": bool(analysis_data.get("user_roles"))
            }
            
            return analysis_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response content: {response.content[:500]}...")
            
            # Return minimal valid structure
            return {
                "critical_assets": [],
                "system_components": [],
                "data_flows": [],
                "trust_boundaries": [],
                "entry_points": [],
                "user_roles": [],
                "validation": {
                    "error": "JSON parse error",
                    "raw_response_preview": response.content[:200]
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error validating response: {e}")
            raise
    
    def _calculate_confidence_score(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on analysis completeness"""
        score = 0.0
        max_score = 100.0
        
        # Check for presence of key components (40 points)
        critical_assets = analysis_data.get("critical_assets", [])
        system_components = analysis_data.get("system_components", [])
        
        if critical_assets:
            score += 15
        if system_components:
            score += 15
        if len(critical_assets) >= 3:  # Multiple assets indicate thorough analysis
            score += 10
        
        # Check for architecture details (30 points)
        data_flows = analysis_data.get("data_flows", [])
        trust_boundaries = analysis_data.get("trust_boundaries", [])
        entry_points = analysis_data.get("entry_points", [])
        
        if data_flows:
            score += 10
        if trust_boundaries:
            score += 10
        if entry_points:
            score += 10
        
        # Check for detailed information (20 points)
        user_roles = analysis_data.get("user_roles", [])
        if user_roles:
            score += 10
        
        # Check quality of descriptions (10 points)
        detailed_assets = sum(1 for asset in critical_assets 
                             if isinstance(asset, dict) and 
                             len(asset.get("description", "")) > 20)
        if detailed_assets > 0:
            score += 5
        if detailed_assets >= len(critical_assets) * 0.7:  # 70% have good descriptions
            score += 5
        
        return min(score / max_score, 1.0)
    
    async def process_task(self, task) -> Any:
        """Process an agent task - compatibility method for workflow integration"""
        from ..models.schemas import AgentResponse
        from ..agents.shared_context import SharedContext
        
        try:
            # Extract task data
            task_data = task.input_data
            project_id = task_data.get("project_id")
            input_ids = task_data.get("input_ids", [])
            config = task_data.get("config", {})
            
            # Get system inputs from database
            from ..core.database import async_session, SystemInput
            from sqlalchemy import select
            
            async with async_session() as db:
                if input_ids:
                    result = await db.execute(
                        select(SystemInput).where(SystemInput.id.in_(input_ids))
                    )
                    inputs = result.scalars().all()
                    system_description = "\n\n".join([inp.content for inp in inputs])
                else:
                    system_description = "No system description provided"
            
            # Create shared context for the project
            context = SharedContext(project_id=project_id)
            
            # Perform system analysis
            result = await self.analyze_system(
                context=context,
                system_description=system_description,
                additional_inputs=None
            )
            
            return AgentResponse(
                task_id=task.task_id,
                agent_type=self.agent_type,
                status="success",
                output_data=result.to_dict(),
                confidence_score=result.confidence_score,
                execution_time=0.0,  # Would need to track this
                errors=None
            )
            
        except Exception as e:
            logger.error(f"Task processing failed: {str(e)}", exc_info=True)
            return AgentResponse(
                task_id=task.task_id,
                agent_type=self.agent_type,
                status="failure",
                output_data={},
                confidence_score=0.0,
                execution_time=0.0,
                errors=[str(e)]
            )
    
    async def get_analysis_summary(self, context: SharedContext) -> Optional[Dict[str, Any]]:
        """Get a summary of the current system analysis"""
        analysis_data = await context.get_data("system_analysis")
        if not analysis_data:
            return None
        
        return {
            "agent_id": self.agent_id,
            "status": "completed",
            "summary": {
                "critical_assets": len(analysis_data.get("critical_assets", [])),
                "system_components": len(analysis_data.get("system_components", [])),
                "data_flows": len(analysis_data.get("data_flows", [])),
                "trust_boundaries": len(analysis_data.get("trust_boundaries", [])),
                "entry_points": len(analysis_data.get("entry_points", [])),
                "user_roles": len(analysis_data.get("user_roles", [])),
                "confidence_score": analysis_data.get("confidence_score", 0.0)
            },
            "metadata": analysis_data.get("analysis_metadata", {})
        }
