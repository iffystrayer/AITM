"""
Base agent class and shared context for AITM multi-agent system
"""

import json
import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain.agents import AgentExecutor
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langsmith import traceable

from app.services.llm_service import llm_service
from app.services.mitre_service import mitre_service
from app.models.schemas import AgentTask, AgentResponse, SharedContext


class SharedContextManager:
    """Manages shared context between agents using blackboard pattern"""
    
    def __init__(self, project_id: int):
        self.project_id = project_id
        self.context = SharedContext(project_id=project_id)
        self._lock = False  # Simple lock for context updates
    
    def read_context(self) -> SharedContext:
        """Read the current shared context"""
        return self.context
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update the shared context with new data"""
        if self._lock:
            time.sleep(0.1)  # Wait briefly if locked
        
        self._lock = True
        try:
            for key, value in updates.items():
                if hasattr(self.context, key):
                    if isinstance(value, list) and key.endswith('s'):
                        # For list fields, extend rather than replace
                        current_list = getattr(self.context, key)
                        if isinstance(current_list, list):
                            current_list.extend(value)
                        else:
                            setattr(self.context, key, value)
                    else:
                        setattr(self.context, key, value)
            
            self.context.last_updated = datetime.utcnow()
            
        finally:
            self._lock = False
    
    def get_context_summary(self) -> str:
        """Get a text summary of the current context"""
        summary = f"Project {self.project_id} Context Summary:\\n"
        summary += f"- System Description: {bool(self.context.system_description)}\\n"
        summary += f"- Identified Assets: {len(self.context.identified_assets)}\\n"
        summary += f"- Technologies: {len(self.context.identified_technologies)}\\n"
        summary += f"- Entry Points: {len(self.context.potential_entry_points)}\\n"
        summary += f"- Attack Paths: {len(self.context.attack_paths)}\\n"
        summary += f"- Recommendations: {len(self.context.mitigation_recommendations)}\\n"
        return summary


class BaseAgent(ABC):
    """Base class for all AITM agents"""
    
    def __init__(self, agent_type: str, description: str):
        self.agent_type = agent_type
        self.description = description
        self.context_manager: Optional[SharedContextManager] = None
    
    def set_context_manager(self, context_manager: SharedContextManager):
        """Set the shared context manager"""
        self.context_manager = context_manager
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the agent's system prompt"""
        pass
    
    @abstractmethod
    async def process_task(self, task: AgentTask) -> AgentResponse:
        """Process a specific task"""
        pass
    
    def get_context_data(self) -> SharedContext:
        """Get current shared context data"""
        if not self.context_manager:
            raise ValueError("Context manager not set")
        return self.context_manager.read_context()
    
    def update_context(self, updates: Dict[str, Any]):
        """Update shared context"""
        if not self.context_manager:
            raise ValueError("Context manager not set")
        self.context_manager.update_context(updates)
    
    @traceable
    async def generate_llm_response(
        self, 
        prompt: str, 
        preferred_provider: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate LLM response using the agent's system prompt"""
        system_prompt = self.get_system_prompt()
        
        # Add context information to the prompt
        context_summary = self.context_manager.get_context_summary() if self.context_manager else ""
        if context_summary:
            prompt = f"Current Context:\\n{context_summary}\\n\\nTask:\\n{prompt}"
        
        return await llm_service.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            preferred_provider=preferred_provider
        )
    
    def parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling potential formatting issues"""
        try:
            # Try to parse as is
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\\{.*\\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # If all else fails, return a structured error
            return {
                "error": "Failed to parse JSON response",
                "raw_response": response_text
            }
    
    def create_response(
        self, 
        task_id: str, 
        status: str, 
        output_data: Dict[str, Any],
        confidence_score: float = 0.8,
        execution_time: float = 0.0,
        errors: Optional[List[str]] = None
    ) -> AgentResponse:
        """Create a standardized agent response"""
        return AgentResponse(
            task_id=task_id,
            agent_type=self.agent_type,
            status=status,
            output_data=output_data,
            confidence_score=confidence_score,
            execution_time=execution_time,
            errors=errors or []
        )


class SystemAnalystAgent(BaseAgent):
    """Agent responsible for analyzing system architecture and identifying assets"""
    
    def __init__(self):
        super().__init__(
            agent_type="system_analyst",
            description="Analyzes system architecture, identifies critical assets, technologies, and potential entry points"
        )
    
    def get_system_prompt(self) -> str:
        return '''You are a cybersecurity system analyst expert. Your role is to analyze system descriptions and identify:

1. Critical assets (servers, databases, applications, data repositories)
2. Technologies used (operating systems, frameworks, cloud services, databases)
3. Potential entry points (public-facing services, user interfaces, APIs)
4. System architecture components and their relationships

Always provide responses in JSON format with the following structure:
{
    "assets": [
        {
            "name": "asset name",
            "type": "server|database|application|data|network",
            "criticality": "high|medium|low",
            "description": "detailed description",
            "technologies": ["tech1", "tech2"]
        }
    ],
    "technologies": ["tech1", "tech2", "tech3"],
    "entry_points": ["entry1", "entry2"],
    "architecture_notes": "Additional observations about the system architecture"
}

Be thorough but practical. Focus on security-relevant assets and technologies.'''
    
    @traceable
    async def process_task(self, task: AgentTask) -> AgentResponse:
        """Analyze system input and identify assets and technologies"""
        start_time = time.time()
        
        try:
            # Get system input from task data
            system_description = task.input_data.get('system_description', '')
            
            prompt = f'''Analyze the following system description and identify critical assets, technologies, and potential entry points:

System Description:
{system_description}

Please provide a comprehensive analysis in the required JSON format.'''
            
            llm_response = await self.generate_llm_response(prompt)
            
            if not llm_response['success']:
                return self.create_response(
                    task.task_id, 
                    "failure", 
                    {"error": "LLM request failed"},
                    errors=["LLM service unavailable"]
                )
            
            # Parse the JSON response
            analysis = self.parse_json_response(llm_response['response'])
            
            if 'error' in analysis:
                return self.create_response(
                    task.task_id,
                    "failure",
                    analysis,
                    errors=["Failed to parse LLM response"]
                )
            
            # Update shared context
            context_updates = {
                'identified_assets': analysis.get('assets', []),
                'identified_technologies': analysis.get('technologies', []),
                'potential_entry_points': analysis.get('entry_points', []),
                'system_description': system_description
            }
            self.update_context(context_updates)
            
            execution_time = time.time() - start_time
            
            return self.create_response(
                task.task_id,
                "success",
                {
                    "analysis": analysis,
                    "assets_count": len(analysis.get('assets', [])),
                    "technologies_count": len(analysis.get('technologies', [])),
                    "entry_points_count": len(analysis.get('entry_points', []))
                },
                confidence_score=0.85,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return self.create_response(
                task.task_id,
                "failure",
                {"error": str(e)},
                execution_time=execution_time,
                errors=[str(e)]
            )
