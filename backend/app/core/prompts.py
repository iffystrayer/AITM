"""
Prompt Templates for AITM Agents
Centralized prompt engineering for threat modeling agents
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class AgentType(Enum):
    """Different types of agents in the AITM system"""
    SYSTEM_ANALYST = "system_analyst"
    ATTACK_MAPPER = "attack_mapper"
    CONTROL_EVALUATOR = "control_evaluator"
    THREAT_INTELLIGENCE = "threat_intelligence"
    MITIGATION_RECOMMENDER = "mitigation_recommender"


@dataclass
class PromptTemplate:
    """Template for agent prompts"""
    system_prompt: str
    user_prompt_template: str
    response_format: Dict[str, Any]
    few_shot_examples: Optional[List[Dict[str, str]]] = None


class PromptLibrary:
    """Library of prompt templates for different agent types"""
    
    SYSTEM_ANALYST_PROMPT = PromptTemplate(
        system_prompt="""You are a cybersecurity expert specializing in system architecture analysis and threat modeling. Your role is to analyze system descriptions and identify critical security-relevant components.

You must analyze the provided system description and extract:
1. Critical assets (databases, servers, applications, data stores)
2. System components and their relationships
3. Technology stack and versions
4. Network architecture and boundaries
5. Data flows between components
6. Trust boundaries and security domains
7. Potential entry points and attack surfaces
8. User roles and access patterns

Focus on security-relevant aspects that could be targets or vectors for cyber attacks. Be thorough but concise in your analysis.""",
        
        user_prompt_template="""Analyze the following system description and identify all security-relevant components:

SYSTEM DESCRIPTION:
{system_description}

Please provide a comprehensive analysis following the JSON schema format.""",
        
        response_format={
            "type": "object",
            "properties": {
                "critical_assets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "criticality": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                            "description": {"type": "string"},
                            "data_classification": {"type": "string"}
                        },
                        "required": ["name", "type", "criticality", "description"]
                    }
                },
                "system_components": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "technologies": {"type": "array", "items": {"type": "string"}},
                            "version": {"type": "string"},
                            "purpose": {"type": "string"},
                            "network_zone": {"type": "string"}
                        },
                        "required": ["name", "type", "purpose"]
                    }
                },
                "data_flows": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "from": {"type": "string"},
                            "to": {"type": "string"},
                            "data_type": {"type": "string"},
                            "protocol": {"type": "string"},
                            "encryption": {"type": "boolean"}
                        },
                        "required": ["from", "to", "data_type"]
                    }
                },
                "trust_boundaries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "description": {"type": "string"},
                            "protection_level": {"type": "string"}
                        },
                        "required": ["name", "type", "description"]
                    }
                },
                "entry_points": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "access_level": {"type": "string"},
                            "authentication_required": {"type": "boolean"},
                            "exposure": {"type": "string", "enum": ["internal", "external", "partner"]}
                        },
                        "required": ["name", "type", "exposure"]
                    }
                },
                "user_roles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string"},
                            "privileges": {"type": "string"},
                            "access_pattern": {"type": "string"}
                        },
                        "required": ["role", "privileges"]
                    }
                }
            },
            "required": ["critical_assets", "system_components", "data_flows", "trust_boundaries", "entry_points"]
        }
    )
    
    ATTACK_MAPPER_PROMPT = PromptTemplate(
        system_prompt="""You are a cybersecurity expert specializing in adversary tactics and the MITRE ATT&CK framework. Your role is to map system components and characteristics to relevant MITRE ATT&CK techniques and construct plausible attack paths.

Given a system analysis, you must:
1. Identify MITRE ATT&CK techniques applicable to the system components
2. Consider the technology stack, architecture, and entry points
3. Map techniques to specific system elements
4. Construct realistic attack paths showing technique progression
5. Prioritize techniques based on likelihood and impact
6. Consider both initial access and post-compromise scenarios

Use your knowledge of real-world attack patterns and focus on techniques that are actually feasible given the system's characteristics.""",
        
        user_prompt_template="""Based on the following system analysis, identify relevant MITRE ATT&CK techniques and construct attack paths:

SYSTEM ANALYSIS:
{system_analysis}

AVAILABLE ATT&CK TECHNIQUES:
{attack_techniques}

Map techniques to system components and create realistic attack paths.""",
        
        response_format={
            "type": "object",
            "properties": {
                "technique_mappings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "technique_id": {"type": "string"},
                            "technique_name": {"type": "string"},
                            "tactic": {"type": "string"},
                            "system_component": {"type": "string"},
                            "applicability_score": {"type": "number", "minimum": 0, "maximum": 1},
                            "rationale": {"type": "string"},
                            "prerequisites": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["technique_id", "technique_name", "tactic", "system_component", "applicability_score", "rationale"]
                    }
                },
                "attack_paths": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path_id": {"type": "string"},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "techniques": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "step": {"type": "integer"},
                                        "technique_id": {"type": "string"},
                                        "technique_name": {"type": "string"},
                                        "tactic": {"type": "string"},
                                        "target_component": {"type": "string"},
                                        "description": {"type": "string"}
                                    },
                                    "required": ["step", "technique_id", "technique_name", "tactic", "target_component"]
                                }
                            },
                            "likelihood": {"type": "string", "enum": ["low", "medium", "high"]},
                            "impact": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                            "complexity": {"type": "string", "enum": ["low", "medium", "high"]}
                        },
                        "required": ["path_id", "name", "description", "techniques", "likelihood", "impact"]
                    }
                }
            },
            "required": ["technique_mappings", "attack_paths"]
        }
    )
    
    CONTROL_EVALUATOR_PROMPT = PromptTemplate(
        system_prompt="""You are a cybersecurity controls specialist expert in evaluating security controls against specific attack techniques. Your role is to assess the effectiveness of existing security controls in mitigating identified threats.

Given attack techniques and existing controls, you must:
1. Analyze each control's effectiveness against specific ATT&CK techniques
2. Identify coverage gaps where techniques are not adequately mitigated
3. Assess control implementation strength and maturity
4. Consider control dependencies and failure scenarios
5. Evaluate defense-in-depth coverage
6. Rate overall control effectiveness

Focus on practical control assessment considering real-world implementation challenges and attacker adaptation.""",
        
        user_prompt_template="""Evaluate the effectiveness of existing security controls against the identified attack techniques:

ATTACK TECHNIQUES:
{attack_techniques}

EXISTING CONTROLS:
{existing_controls}

Assess control effectiveness and identify gaps.""",
        
        response_format={
            "type": "object",
            "properties": {
                "control_assessments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "control_id": {"type": "string"},
                            "control_name": {"type": "string"},
                            "effectiveness_score": {"type": "number", "minimum": 0, "maximum": 1},
                            "coverage": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "technique_id": {"type": "string"},
                                        "mitigation_level": {"type": "string", "enum": ["none", "minimal", "partial", "significant", "complete"]},
                                        "confidence": {"type": "string", "enum": ["low", "medium", "high"]}
                                    },
                                    "required": ["technique_id", "mitigation_level"]
                                }
                            },
                            "strengths": {"type": "array", "items": {"type": "string"}},
                            "weaknesses": {"type": "array", "items": {"type": "string"}},
                            "implementation_quality": {"type": "string", "enum": ["poor", "basic", "good", "excellent"]}
                        },
                        "required": ["control_id", "control_name", "effectiveness_score", "coverage"]
                    }
                },
                "coverage_gaps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "technique_id": {"type": "string"},
                            "technique_name": {"type": "string"},
                            "gap_severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                            "current_coverage": {"type": "string"},
                            "risk_description": {"type": "string"}
                        },
                        "required": ["technique_id", "technique_name", "gap_severity", "risk_description"]
                    }
                },
                "overall_assessment": {
                    "type": "object",
                    "properties": {
                        "defense_score": {"type": "number", "minimum": 0, "maximum": 1},
                        "coverage_percentage": {"type": "number", "minimum": 0, "maximum": 100},
                        "critical_gaps": {"type": "integer"},
                        "recommendations_priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]}
                    },
                    "required": ["defense_score", "coverage_percentage", "critical_gaps"]
                }
            },
            "required": ["control_assessments", "coverage_gaps", "overall_assessment"]
        }
    )
    
    @classmethod
    def get_template(cls, agent_type: AgentType) -> PromptTemplate:
        """Get prompt template for specific agent type"""
        templates = {
            AgentType.SYSTEM_ANALYST: cls.SYSTEM_ANALYST_PROMPT,
            AgentType.ATTACK_MAPPER: cls.ATTACK_MAPPER_PROMPT,
            AgentType.CONTROL_EVALUATOR: cls.CONTROL_EVALUATOR_PROMPT,
        }
        
        template = templates.get(agent_type)
        if not template:
            raise ValueError(f"No template found for agent type: {agent_type}")
        
        return template
    
    @classmethod
    def format_prompt(
        cls, 
        agent_type: AgentType, 
        context: Dict[str, Any]
    ) -> tuple[str, str, Dict[str, Any]]:
        """Format prompt template with context data"""
        template = cls.get_template(agent_type)
        
        # Format user prompt with context
        user_prompt = template.user_prompt_template.format(**context)
        
        return template.system_prompt, user_prompt, template.response_format


def get_system_analyst_prompt(system_description: str) -> tuple[str, str, Dict[str, Any]]:
    """Get formatted system analyst prompt"""
    return PromptLibrary.format_prompt(
        AgentType.SYSTEM_ANALYST,
        {"system_description": system_description}
    )


def get_attack_mapper_prompt(system_analysis: Dict[str, Any], attack_techniques: List[Dict[str, Any]]) -> tuple[str, str, Dict[str, Any]]:
    """Get formatted attack mapper prompt"""
    # Convert techniques list to formatted string
    techniques_str = ""
    for tech in attack_techniques:
        techniques_str += f"- {tech.get('technique_id', '')}: {tech.get('name', '')} ({tech.get('tactic', '')})\n"
    
    return PromptLibrary.format_prompt(
        AgentType.ATTACK_MAPPER,
        {
            "system_analysis": system_analysis,
            "attack_techniques": techniques_str
        }
    )


def get_control_evaluator_prompt(attack_techniques: List[Dict[str, Any]], existing_controls: List[Dict[str, Any]]) -> tuple[str, str, Dict[str, Any]]:
    """Get formatted control evaluator prompt"""
    # Format techniques and controls
    techniques_str = ""
    for tech in attack_techniques:
        techniques_str += f"- {tech.get('technique_id', '')}: {tech.get('name', '')}\n"
    
    controls_str = ""
    for control in existing_controls:
        controls_str += f"- {control.get('name', '')}: {control.get('description', '')}\n"
    
    return PromptLibrary.format_prompt(
        AgentType.CONTROL_EVALUATOR,
        {
            "attack_techniques": techniques_str,
            "existing_controls": controls_str
        }
    )
