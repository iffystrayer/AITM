"""
Report Generation Agent
Generates comprehensive threat modeling reports with executive summaries and technical details
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from langsmith import traceable

from app.agents.base_agent import BaseAgent
from app.services.enhanced_mitre_service import get_enhanced_mitre_service
from app.models.schemas import AgentTask, AgentResponse

logger = logging.getLogger(__name__)


class ReportGenerationAgent(BaseAgent):
    """Agent responsible for generating comprehensive threat modeling reports"""
    
    def __init__(self):
        super().__init__(
            agent_type="report_generator",
            description="Generates comprehensive threat modeling reports with executive summaries and technical details"
        )
    
    def get_system_prompt(self) -> str:
        return '''You are a cybersecurity report writer specializing in threat modeling documentation. Your role is to:

1. Create comprehensive threat modeling reports
2. Write executive summaries for business stakeholders
3. Provide technical details for security teams
4. Generate actionable recommendations
5. Present findings in a clear, professional format

Always provide responses in JSON format:
{
    "executive_summary": {
        "overview": "High-level overview of security posture",
        "key_findings": ["Critical finding 1", "Critical finding 2"],
        "risk_level": "critical|high|medium|low",
        "priority_actions": ["Action 1", "Action 2"],
        "business_impact": "Impact on business operations"
    },
    "technical_analysis": {
        "system_overview": "Technical description of analyzed system",
        "attack_surface": {
            "entry_points": 5,
            "critical_assets": 3,
            "identified_threats": 12
        },
        "threat_landscape": [
            {
                "threat_category": "Category name",
                "techniques_count": 4,
                "risk_level": "high",
                "description": "Threat description"
            }
        ],
        "attack_paths": [
            {
                "path_name": "Attack path name",
                "likelihood": "high|medium|low",
                "impact": "critical|high|medium|low",
                "techniques": ["T1190", "T1059"],
                "description": "Attack path description"
            }
        ]
    },
    "control_assessment": {
        "current_controls": "Assessment of existing controls",
        "effectiveness_score": 0.65,
        "control_gaps": [
            {
                "gap": "Control gap description",
                "severity": "high|medium|low",
                "affected_techniques": ["T1190"],
                "recommendation": "Specific recommendation"
            }
        ]
    },
    "recommendations": {
        "immediate_actions": [
            {
                "priority": 1,
                "action": "Specific action to take",
                "justification": "Why this is important",
                "timeline": "Implementation timeline",
                "effort": "low|medium|high"
            }
        ],
        "strategic_improvements": [
            {
                "improvement": "Strategic improvement",
                "benefits": "Expected benefits",
                "timeline": "Implementation timeline",
                "investment": "Required investment level"
            }
        ]
    },
    "metrics": {
        "threat_coverage": 0.85,
        "control_maturity": 0.70,
        "residual_risk": 0.45,
        "techniques_analyzed": 15,
        "paths_identified": 8
    }
}

Focus on actionable insights and clear communication for both technical and business audiences.'''

    @traceable
    async def process_task(self, task: AgentTask) -> AgentResponse:
        """Generate comprehensive threat modeling report"""
        start_time = time.time()
        
        try:
            # Get all context data
            context = self.get_context_data()
            
            # Extract analysis results
            system_analysis = getattr(context, 'system_analysis_results', [])
            attack_paths = getattr(context, 'attack_paths', [])
            control_evaluations = getattr(context, 'control_evaluation_results', [])
            identified_assets = getattr(context, 'identified_assets', [])
            technologies = getattr(context, 'identified_technologies', [])
            entry_points = getattr(context, 'potential_entry_points', [])
            
            if not any([system_analysis, attack_paths, control_evaluations]):
                return self.create_response(
                    task.task_id,
                    "failure",
                    {"error": "Insufficient analysis data for report generation"},
                    errors=["Missing analysis results"]
                )
            
            # Get additional context from enhanced MITRE service
            mitre_service = get_enhanced_mitre_service()
            
            # Prepare comprehensive context for report
            report_context = {
                "system_overview": {
                    "assets_count": len(identified_assets),
                    "technologies": technologies,
                    "entry_points": entry_points,
                    "analysis_date": datetime.now().isoformat()
                },
                "threat_analysis": {
                    "attack_paths": attack_paths,
                    "total_techniques": self._count_unique_techniques(attack_paths),
                    "mitre_coverage": await self._calculate_mitre_coverage(attack_paths, mitre_service)
                },
                "control_assessment": control_evaluations,
                "risk_metrics": await self._calculate_risk_metrics(
                    attack_paths, control_evaluations, identified_assets
                )
            }
            
            # Generate report content
            prompt = self._create_report_prompt(report_context)
            
            llm_response = await self.generate_llm_response(prompt, temperature=0.4)
            
            if not llm_response['success']:
                return self.create_response(
                    task.task_id,
                    "failure",
                    {"error": "LLM request failed"},
                    errors=["LLM service unavailable"]
                )
            
            # Parse the JSON response
            report = self.parse_json_response(llm_response['response'])
            
            if 'error' in report:
                return self.create_response(
                    task.task_id,
                    "failure",
                    report,
                    errors=["Failed to parse LLM response"]
                )
            
            # Enhance report with additional technical details
            enhanced_report = await self._enhance_report(report, report_context, mitre_service)
            
            # Store report in context
            context_updates = {
                'threat_model_report': enhanced_report,
                'report_generated_at': datetime.now().isoformat()
            }
            self.update_context(context_updates)
            
            execution_time = time.time() - start_time
            
            return self.create_response(
                task.task_id,
                "success",
                {
                    "report": enhanced_report,
                    "report_summary": {
                        "risk_level": enhanced_report.get('executive_summary', {}).get('risk_level', 'medium'),
                        "techniques_analyzed": enhanced_report.get('metrics', {}).get('techniques_analyzed', 0),
                        "recommendations_count": len(enhanced_report.get('recommendations', {}).get('immediate_actions', [])),
                        "control_gaps": len(enhanced_report.get('control_assessment', {}).get('control_gaps', []))
                    }
                },
                confidence_score=0.88,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error generating report: {e}")
            return self.create_response(
                task.task_id,
                "failure",
                {"error": str(e)},
                execution_time=execution_time,
                errors=[str(e)]
            )
    
    def _create_report_prompt(self, context: Dict[str, Any]) -> str:
        """Create comprehensive report generation prompt"""
        system_info = context.get('system_overview', {})
        threat_info = context.get('threat_analysis', {})
        control_info = context.get('control_assessment', [])
        risk_metrics = context.get('risk_metrics', {})
        
        # Format attack paths for prompt
        attack_paths_summary = []
        for path in threat_info.get('attack_paths', [])[:10]:  # Limit for prompt size
            path_summary = f"- {path.get('name', 'Unknown Path')}: {len(path.get('techniques', []))} techniques, Impact: {path.get('impact', 'unknown')}, Likelihood: {path.get('likelihood', 'unknown')}"
            attack_paths_summary.append(path_summary)
        
        # Format control evaluations
        control_summary = []
        for evaluation in control_info[:5]:  # Limit for prompt size
            eval_data = evaluation if isinstance(evaluation, dict) else {}
            control_evals = eval_data.get('control_evaluations', [])
            control_summary.append(f"- Assessed {len(control_evals)} techniques")
            
            overall_assessment = eval_data.get('overall_assessment', {})
            if overall_assessment:
                control_summary.append(f"- Overall risk score: {overall_assessment.get('overall_risk_score', 'unknown')}")
        
        prompt = f'''Generate a comprehensive threat modeling report based on the following analysis:

SYSTEM OVERVIEW:
- Assets analyzed: {system_info.get('assets_count', 0)}
- Technologies: {', '.join(system_info.get('technologies', [])[:10])}
- Entry points: {', '.join(system_info.get('entry_points', [])[:10])}
- Analysis date: {system_info.get('analysis_date', 'unknown')}

THREAT ANALYSIS:
- Attack paths identified: {len(threat_info.get('attack_paths', []))}
- Unique techniques identified: {threat_info.get('total_techniques', 0)}
- MITRE ATT&CK coverage: {threat_info.get('mitre_coverage', {}).get('percentage', 0):.1f}%

ATTACK PATHS SUMMARY:
{chr(10).join(attack_paths_summary) if attack_paths_summary else "No attack paths identified"}

CONTROL ASSESSMENT:
{chr(10).join(control_summary) if control_summary else "No control assessments available"}

RISK METRICS:
- Overall risk score: {risk_metrics.get('overall_risk_score', 'unknown')}
- Critical findings: {risk_metrics.get('critical_findings_count', 0)}
- High-risk techniques: {risk_metrics.get('high_risk_techniques', 0)}

Generate a professional threat modeling report that:
1. Provides clear executive summary for business stakeholders
2. Includes detailed technical analysis for security teams
3. Assesses current security controls and identifies gaps
4. Offers prioritized, actionable recommendations
5. Presents metrics and measurements

Focus on practical insights that help improve security posture.'''
        
        return prompt
    
    def _count_unique_techniques(self, attack_paths: List[Dict[str, Any]]) -> int:
        """Count unique ATT&CK techniques across all attack paths"""
        unique_techniques = set()
        
        for path in attack_paths:
            techniques = path.get('techniques', [])
            if isinstance(techniques, list):
                unique_techniques.update(techniques)
            elif isinstance(techniques, str):
                try:
                    technique_list = json.loads(techniques)
                    unique_techniques.update(technique_list)
                except json.JSONDecodeError:
                    continue
        
        return len(unique_techniques)
    
    async def _calculate_mitre_coverage(
        self, 
        attack_paths: List[Dict[str, Any]], 
        mitre_service
    ) -> Dict[str, Any]:
        """Calculate coverage of MITRE ATT&CK framework"""
        # Get all techniques from attack paths
        path_techniques = set()
        for path in attack_paths:
            techniques = path.get('techniques', [])
            if isinstance(techniques, list):
                path_techniques.update(techniques)
        
        # Get total techniques in MITRE ATT&CK
        total_techniques = mitre_service.get_technique_count()
        
        # Calculate coverage
        coverage_percentage = (len(path_techniques) / total_techniques * 100) if total_techniques > 0 else 0
        
        # Analyze tactic coverage
        tactic_coverage = {}
        all_tactics = mitre_service.get_all_tactics()
        
        for tactic in all_tactics:
            tactic_techniques = mitre_service.get_techniques_by_tactic(tactic)
            tactic_technique_ids = {t['id'] for t in tactic_techniques}
            
            covered_in_tactic = path_techniques.intersection(tactic_technique_ids)
            tactic_coverage[tactic] = {
                'total': len(tactic_technique_ids),
                'covered': len(covered_in_tactic),
                'percentage': (len(covered_in_tactic) / len(tactic_technique_ids) * 100) if len(tactic_technique_ids) > 0 else 0
            }
        
        return {
            'percentage': coverage_percentage,
            'techniques_covered': len(path_techniques),
            'total_techniques': total_techniques,
            'tactic_coverage': tactic_coverage
        }
    
    async def _calculate_risk_metrics(
        self,
        attack_paths: List[Dict[str, Any]],
        control_evaluations: List[Dict[str, Any]],
        assets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics"""
        
        # Count risk levels in attack paths
        risk_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for path in attack_paths:
            impact = path.get('impact', 'medium').lower()
            likelihood = path.get('likelihood', 'medium').lower()
            
            # Simple risk calculation based on impact and likelihood
            if impact in ['critical'] and likelihood in ['high']:
                risk_counts['critical'] += 1
            elif impact in ['critical', 'high'] and likelihood in ['medium', 'high']:
                risk_counts['high'] += 1
            elif impact in ['medium', 'high'] or likelihood in ['medium', 'high']:
                risk_counts['medium'] += 1
            else:
                risk_counts['low'] += 1
        
        # Count critical assets
        critical_assets = len([a for a in assets if a.get('criticality', '').lower() == 'critical'])
        
        # Calculate overall risk score
        total_paths = len(attack_paths)
        if total_paths > 0:
            overall_risk_score = (
                risk_counts['critical'] * 4 + 
                risk_counts['high'] * 3 + 
                risk_counts['medium'] * 2 + 
                risk_counts['low'] * 1
            ) / (total_paths * 4)  # Normalize to 0-1 scale
        else:
            overall_risk_score = 0
        
        # Extract control metrics
        control_effectiveness = 0
        if control_evaluations:
            total_score = 0
            eval_count = 0
            for evaluation in control_evaluations:
                if isinstance(evaluation, dict):
                    overall_assessment = evaluation.get('overall_assessment', {})
                    score = overall_assessment.get('overall_risk_score', 0)
                    if score:
                        total_score += (1 - score)  # Convert risk score to effectiveness
                        eval_count += 1
            
            if eval_count > 0:
                control_effectiveness = total_score / eval_count
        
        return {
            'overall_risk_score': overall_risk_score,
            'critical_findings_count': risk_counts['critical'],
            'high_risk_techniques': risk_counts['high'],
            'risk_distribution': risk_counts,
            'critical_assets_count': critical_assets,
            'control_effectiveness': control_effectiveness,
            'total_attack_paths': total_paths
        }
    
    async def _enhance_report(
        self,
        report: Dict[str, Any],
        context: Dict[str, Any],
        mitre_service
    ) -> Dict[str, Any]:
        """Enhance report with additional technical details"""
        enhanced_report = report.copy()
        
        # Add detailed technique information to attack paths
        if 'technical_analysis' in enhanced_report and 'attack_paths' in enhanced_report['technical_analysis']:
            for path in enhanced_report['technical_analysis']['attack_paths']:
                technique_ids = path.get('techniques', [])
                detailed_techniques = []
                
                for tech_id in technique_ids:
                    technique_info = mitre_service.get_technique(tech_id)
                    if technique_info:
                        detailed_techniques.append({
                            'id': tech_id,
                            'name': technique_info['name'],
                            'tactics': technique_info.get('tactics', []),
                            'description': technique_info.get('description', '')[:200] + '...'
                        })
                
                path['technique_details'] = detailed_techniques
        
        # Add MITRE coverage details
        mitre_coverage = context.get('threat_analysis', {}).get('mitre_coverage', {})
        enhanced_report['mitre_analysis'] = {
            'framework_version': 'Enterprise ATT&CK v14.1',
            'coverage_analysis': mitre_coverage,
            'top_tactics_covered': self._get_top_covered_tactics(mitre_coverage.get('tactic_coverage', {}))
        }
        
        # Add timestamp and metadata
        enhanced_report['report_metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'analysis_scope': 'Full System Threat Model',
            'framework': 'MITRE ATT&CK',
            'version': '1.0'
        }
        
        return enhanced_report
    
    def _get_top_covered_tactics(self, tactic_coverage: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Get top covered tactics sorted by coverage percentage"""
        tactic_list = []
        
        for tactic, coverage_data in tactic_coverage.items():
            tactic_list.append({
                'tactic': tactic,
                'coverage_percentage': coverage_data.get('percentage', 0),
                'techniques_covered': coverage_data.get('covered', 0),
                'total_techniques': coverage_data.get('total', 0)
            })
        
        # Sort by coverage percentage
        tactic_list.sort(key=lambda x: x['coverage_percentage'], reverse=True)
        
        return tactic_list[:10]  # Return top 10
