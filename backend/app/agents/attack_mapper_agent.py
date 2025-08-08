"""
ATT&CK Mapper Agent and Control Evaluation Agent
"""

import json
import time
from typing import Dict, Any, List

from langsmith import traceable

from app.agents.base_agent import BaseAgent
from app.services.enhanced_mitre_service import get_enhanced_mitre_service
from app.models.schemas import AgentTask, AgentResponse


class AttackMapperAgent(BaseAgent):
    """Agent responsible for mapping system characteristics to MITRE ATT&CK techniques and building attack paths"""
    
    def __init__(self):
        super().__init__(
            agent_type="attack_mapper",
            description="Maps system components to MITRE ATT&CK techniques and constructs plausible attack paths"
        )
    
    def get_system_prompt(self) -> str:
        return '''You are a cybersecurity threat modeling expert specializing in MITRE ATT&CK framework. Your role is to:

1. Map identified system assets and technologies to relevant ATT&CK techniques
2. Construct plausible attack paths using sequences of ATT&CK techniques
3. Prioritize attack paths based on likelihood and impact

You have access to the MITRE ATT&CK knowledge base. Always provide responses in JSON format:
{
    "technique_mappings": [
        {
            "technique_id": "T1190",
            "technique_name": "Exploit Public-Facing Application",
            "tactics": ["initial-access"],
            "relevance_reason": "Why this technique applies to the system",
            "applicable_assets": ["asset1", "asset2"],
            "likelihood": "high|medium|low"
        }
    ],
    "attack_paths": [
        {
            "name": "Attack path name",
            "description": "Detailed description of the attack scenario",
            "techniques": ["T1190", "T1059", "T1078"],
            "priority_score": 0.85,
            "explanation": "Why this attack path is significant",
            "affected_assets": ["asset1", "asset2"],
            "prerequisites": ["List of conditions needed for this attack"]
        }
    ]
}

Focus on realistic, system-specific attack scenarios. Consider the actual technologies and architecture identified.'''
    
    @traceable
    async def process_task(self, task: AgentTask) -> AgentResponse:
        """Map assets to ATT&CK techniques and generate attack paths"""
        start_time = time.time()
        
        try:
            # Get context data
            context = self.get_context_data()
            
            # Get system characteristics from context
            assets = context.identified_assets
            technologies = context.identified_technologies
            entry_points = context.potential_entry_points
            
            if not assets and not technologies:
                return self.create_response(
                    task.task_id,
                    "failure",
                    {"error": "No system assets or technologies identified"},
                    errors=["Missing system analysis data"]
                )
            
            # Get suggested techniques from enhanced MITRE service
            mitre_service = get_enhanced_mitre_service()
            
            # Convert assets to components format
            components = [
                {
                    'name': asset.get('name', 'unknown'),
                    'type': asset.get('type', 'unknown'),
                    'technologies': technologies,
                    'criticality': asset.get('criticality', 'medium')
                }
                for asset in assets
            ]
            
            # Get techniques for components
            component_techniques = mitre_service.get_techniques_for_system_components(
                components=components, 
                limit_per_component=15
            )
            
            # Flatten techniques from all components
            suggested_techniques = []
            for comp_name, techniques in component_techniques.items():
                suggested_techniques.extend(techniques)
            
            # Create prompt with system context and suggested techniques
            techniques_info = "\\n".join([
                f"- {t['id']}: {t['name']} (Tactics: {', '.join(t['tactics'])})"
                for t in suggested_techniques[:15]  # Limit to prevent token overflow
            ])
            
            assets_info = "\\n".join([
                f"- {asset['name']} ({asset['type']}) - {asset['criticality']} criticality"
                for asset in assets
            ])
            
            prompt = f'''Based on the following system analysis, map relevant MITRE ATT&CK techniques and create attack paths:

IDENTIFIED ASSETS:
{assets_info}

TECHNOLOGIES USED:
{', '.join(technologies)}

POTENTIAL ENTRY POINTS:
{', '.join(entry_points)}

SUGGESTED ATT&CK TECHNIQUES:
{techniques_info}

Please analyze this system and provide:
1. Technique mappings explaining how each technique applies
2. Realistic attack paths combining multiple techniques
3. Prioritization based on likelihood and impact

Focus on the most relevant and realistic threats for this specific system.'''
            
            llm_response = await self.generate_llm_response(prompt, temperature=0.6)
            
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
            
            # Update shared context with attack paths
            attack_paths = analysis.get('attack_paths', [])
            context_updates = {
                'attack_paths': attack_paths
            }
            self.update_context(context_updates)
            
            execution_time = time.time() - start_time
            
            return self.create_response(
                task.task_id,
                "success",
                {
                    "technique_mappings": analysis.get('technique_mappings', []),
                    "attack_paths": attack_paths,
                    "techniques_count": len(analysis.get('technique_mappings', [])),
                    "attack_paths_count": len(attack_paths)
                },
                confidence_score=0.80,
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


class ControlEvaluationAgent(BaseAgent):
    """Agent responsible for evaluating existing security controls against identified threats"""
    
    def __init__(self):
        super().__init__(
            agent_type="control_evaluator",
            description="Evaluates existing security controls against ATT&CK techniques and identifies gaps"
        )
    
    def get_system_prompt(self) -> str:
        return '''You are a cybersecurity control assessment expert. Your role is to:

1. Evaluate existing security controls against identified ATT&CK techniques
2. Identify control gaps and weaknesses
3. Assess the effectiveness of current security measures

Always provide responses in JSON format:
{
    "control_evaluations": [
        {
            "technique_id": "T1190",
            "technique_name": "Exploit Public-Facing Application",
            "existing_controls": [
                {
                    "control_name": "Web Application Firewall",
                    "effectiveness": "partial|effective|ineffective",
                    "coverage_percentage": 75,
                    "notes": "Blocks common attacks but may miss zero-days"
                }
            ],
            "control_gaps": [
                "Missing input validation",
                "No code review process"
            ],
            "risk_level": "high|medium|low"
        }
    ],
    "overall_assessment": {
        "total_techniques_assessed": 5,
        "adequately_controlled": 2,
        "partially_controlled": 2,
        "uncontrolled": 1,
        "overall_risk_score": 0.65
    },
    "priority_gaps": [
        {
            "gap_description": "No endpoint detection and response (EDR) solution",
            "affected_techniques": ["T1055", "T1059"],
            "priority": "high|medium|low",
            "recommendation": "Brief recommendation"
        }
    ]
}

Be realistic about control effectiveness and focus on actionable insights.'''
    
    @traceable
    async def process_task(self, task: AgentTask) -> AgentResponse:
        """Evaluate security controls against identified techniques"""
        start_time = time.time()
        
        try:
            # Get context data
            context = self.get_context_data()
            attack_paths = context.attack_paths
            
            if not attack_paths:
                return self.create_response(
                    task.task_id,
                    "failure",
                    {"error": "No attack paths identified for control evaluation"},
                    errors=["Missing attack path data"]
                )
            
            # Get control information from task input
            existing_controls = task.input_data.get('existing_controls', [])
            control_documentation = task.input_data.get('control_documentation', '')
            
            # Extract techniques from attack paths
            all_techniques = set()
            for path in attack_paths:
                techniques = path.get('techniques', [])
                if isinstance(techniques, list):
                    all_techniques.update(techniques)
                elif isinstance(techniques, str):
                    # Handle JSON string case
                    try:
                        technique_list = json.loads(techniques)
                        all_techniques.update(technique_list)
                    except json.JSONDecodeError:
                        continue
            
            techniques_list = list(all_techniques)[:10]  # Limit for prompt size
            
            # Get technique details for context using enhanced MITRE service
            mitre_service = get_enhanced_mitre_service()
            technique_details = []
            for tech_id in techniques_list:
                technique_info = mitre_service.get_technique(tech_id)
                if technique_info:
                    technique_details.append(f"- {tech_id}: {technique_info['name']}")
            
            prompt = f'''Evaluate security controls against the following identified ATT&CK techniques:

IDENTIFIED ATTACK TECHNIQUES:
{chr(10).join(technique_details)}

EXISTING SECURITY CONTROLS:
{chr(10).join(existing_controls) if existing_controls else "No specific controls documented"}

CONTROL DOCUMENTATION:
{control_documentation or "No additional control documentation provided"}

ATTACK PATHS CONTEXT:
{len(attack_paths)} attack paths identified involving these techniques

Please assess:
1. How well existing controls address each technique
2. Identify specific control gaps
3. Provide an overall risk assessment
4. Prioritize the most critical gaps

Focus on practical, implementable control improvements.'''
            
            llm_response = await self.generate_llm_response(prompt, temperature=0.5)
            
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
                'control_evaluation_results': [analysis]
            }
            self.update_context(context_updates)
            
            execution_time = time.time() - start_time
            
            return self.create_response(
                task.task_id,
                "success",
                {
                    "control_evaluations": analysis.get('control_evaluations', []),
                    "overall_assessment": analysis.get('overall_assessment', {}),
                    "priority_gaps": analysis.get('priority_gaps', []),
                    "techniques_assessed": len(analysis.get('control_evaluations', [])),
                    "gaps_identified": len(analysis.get('priority_gaps', []))
                },
                confidence_score=0.75,
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
