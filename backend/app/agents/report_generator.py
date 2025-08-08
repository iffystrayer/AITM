"""
AITM Multi-Agent Report Generation System

This module provides a comprehensive report generation system with specialized agents
for different types of security reports, executive summaries, and technical documentation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

# Removed model imports for standalone demo
# from app.core.config import get_settings
# from app.models.project import Project
# from app.models.analysis import Analysis

# Mock settings for standalone demo
class MockSettings:
    debug = True
    environment = "development"

settings = MockSettings()
logger = logging.getLogger(__name__)


class ReportType(str, Enum):
    """Available report types"""
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_DETAILED = "technical_detailed"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_AUDIT = "compliance_audit"
    PENETRATION_TEST = "penetration_test"
    INCIDENT_RESPONSE = "incident_response"
    THREAT_LANDSCAPE = "threat_landscape"
    MITIGATION_PLAN = "mitigation_plan"


class ReportFormat(str, Enum):
    """Supported report formats"""
    PDF = "pdf"
    HTML = "html"
    DOCX = "docx"
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass
class ReportRequest:
    """Report generation request structure"""
    report_type: ReportType
    format: ReportFormat
    project_ids: List[str]
    date_range: Optional[Dict[str, str]] = None
    include_charts: bool = True
    include_mitre_mapping: bool = True
    include_recommendations: bool = True
    custom_sections: Optional[List[str]] = None
    audience_level: str = "technical"  # executive, technical, operational
    branding: Optional[Dict[str, str]] = None


@dataclass
class ReportContent:
    """Generated report content structure"""
    title: str
    executive_summary: str
    sections: List[Dict[str, Any]]
    charts: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    generated_at: datetime


class BaseReportAgent:
    """Base class for all report generation agents"""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.logger = logging.getLogger(f"agent.{agent_id}")
    
    async def generate_content(self, request: ReportRequest, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report content - to be implemented by subclasses"""
        raise NotImplementedError
    
    async def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate input data for report generation"""
        return True
    
    def format_date(self, date_str: str) -> str:
        """Format date strings consistently"""
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            return date_str


class ExecutiveReportAgent(BaseReportAgent):
    """Agent specialized in generating executive summaries and high-level reports"""
    
    def __init__(self):
        super().__init__("executive_agent", "Executive Report Generator")
    
    async def generate_content(self, request: ReportRequest, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive-level report content"""
        self.logger.info(f"Generating executive report for {len(request.project_ids)} projects")
        
        # Extract key metrics
        projects = data.get("projects", [])
        analyses = data.get("analyses", [])
        
        # Calculate executive metrics
        total_risks = sum(len(analysis.get("threats", [])) for analysis in analyses)
        high_risks = sum(
            len([t for t in analysis.get("threats", []) if t.get("severity") == "HIGH"])
            for analysis in analyses
        )
        critical_risks = sum(
            len([t for t in analysis.get("threats", []) if t.get("severity") == "CRITICAL"])
            for analysis in analyses
        )
        
        # Risk score calculation
        risk_scores = [analysis.get("risk_score", 0) for analysis in analyses if analysis.get("risk_score")]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            total_risks, high_risks, critical_risks, avg_risk_score, projects
        )
        
        # Create sections
        sections = [
            {
                "title": "Risk Overview",
                "type": "metrics",
                "content": {
                    "total_projects": len(projects),
                    "total_risks": total_risks,
                    "high_risks": high_risks,
                    "critical_risks": critical_risks,
                    "average_risk_score": round(avg_risk_score, 2)
                }
            },
            {
                "title": "Key Findings",
                "type": "findings",
                "content": await self._generate_key_findings(analyses)
            },
            {
                "title": "Strategic Recommendations",
                "type": "recommendations",
                "content": await self._generate_strategic_recommendations(analyses)
            }
        ]
        
        # Generate charts for executive dashboard
        charts = await self._generate_executive_charts(analyses)
        
        return {
            "title": f"Executive Security Report - {datetime.now().strftime('%B %Y')}",
            "executive_summary": executive_summary,
            "sections": sections,
            "charts": charts,
            "metadata": {
                "report_type": "executive",
                "projects_analyzed": len(projects),
                "generation_date": datetime.now().isoformat()
            }
        }
    
    def _generate_executive_summary(self, total_risks: int, high_risks: int, 
                                  critical_risks: int, avg_risk_score: float, 
                                  projects: List[Dict]) -> str:
        """Generate executive summary text"""
        risk_level = "LOW"
        if avg_risk_score > 7:
            risk_level = "CRITICAL"
        elif avg_risk_score > 5:
            risk_level = "HIGH"
        elif avg_risk_score > 3:
            risk_level = "MEDIUM"
        
        summary = f"""
This executive report provides a comprehensive analysis of the cybersecurity posture across {len(projects)} projects analyzed during the current reporting period.

KEY HIGHLIGHTS:
• Total Security Risks Identified: {total_risks}
• High-Priority Risks: {high_risks}
• Critical Risks Requiring Immediate Action: {critical_risks}
• Overall Risk Level: {risk_level} (Score: {avg_risk_score:.1f}/10)

The analysis reveals {"significant security concerns that require executive attention" if critical_risks > 0 else "a manageable security risk profile with opportunities for improvement"}.

{"IMMEDIATE ACTION REQUIRED: Critical vulnerabilities have been identified that pose substantial risk to organizational operations." if critical_risks > 0 else "The organization maintains a reasonable security posture with recommended improvements detailed in this report."}
        """.strip()
        
        return summary
    
    async def _generate_key_findings(self, analyses: List[Dict]) -> List[Dict[str, Any]]:
        """Generate key findings for executive audience"""
        findings = []
        
        # Most common threat types
        threat_types = {}
        for analysis in analyses:
            for threat in analysis.get("threats", []):
                threat_type = threat.get("type", "Unknown")
                threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
        
        if threat_types:
            top_threat = max(threat_types, key=threat_types.get)
            findings.append({
                "title": "Primary Threat Vector",
                "description": f"'{top_threat}' represents the most prevalent threat type, accounting for {threat_types[top_threat]} instances across analyzed projects.",
                "impact": "HIGH",
                "trend": "INCREASING"
            })
        
        # MITRE ATT&CK coverage analysis
        mitre_tactics = set()
        for analysis in analyses:
            for threat in analysis.get("threats", []):
                tactics = threat.get("mitre_tactics", [])
                mitre_tactics.update(tactics)
        
        if mitre_tactics:
            findings.append({
                "title": "MITRE ATT&CK Coverage",
                "description": f"Analysis covers {len(mitre_tactics)} distinct MITRE ATT&CK tactics, providing comprehensive threat landscape visibility.",
                "impact": "MEDIUM",
                "trend": "STABLE"
            })
        
        # Confidence levels
        confidence_scores = []
        for analysis in analyses:
            if analysis.get("confidence_score"):
                confidence_scores.append(analysis.get("confidence_score"))
        
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            findings.append({
                "title": "Analysis Confidence",
                "description": f"AI-powered analysis maintains {avg_confidence:.1f}% average confidence, indicating {'high' if avg_confidence > 80 else 'moderate'} reliability.",
                "impact": "LOW",
                "trend": "IMPROVING"
            })
        
        return findings
    
    async def _generate_strategic_recommendations(self, analyses: List[Dict]) -> List[Dict[str, Any]]:
        """Generate strategic recommendations for executives"""
        recommendations = []
        
        # Analyze patterns to generate strategic recommendations
        critical_count = sum(
            len([t for t in analysis.get("threats", []) if t.get("severity") == "CRITICAL"])
            for analysis in analyses
        )
        
        if critical_count > 0:
            recommendations.append({
                "priority": "IMMEDIATE",
                "title": "Critical Risk Remediation",
                "description": f"Address {critical_count} critical security risks identified across the portfolio.",
                "business_impact": "Risk of significant operational disruption and potential data breach.",
                "timeline": "30 days",
                "resources": "Security team + External consultants if needed"
            })
        
        # Always include strategic recommendations
        recommendations.extend([
            {
                "priority": "HIGH",
                "title": "Security Framework Enhancement",
                "description": "Implement comprehensive security monitoring and incident response capabilities.",
                "business_impact": "Improved threat detection and faster response times.",
                "timeline": "90 days",
                "resources": "Security operations team + Technology investment"
            },
            {
                "priority": "MEDIUM",
                "title": "Staff Security Training",
                "description": "Deploy organization-wide security awareness and threat recognition training.",
                "business_impact": "Reduced human error risks and improved security culture.",
                "timeline": "60 days",
                "resources": "HR team + Security team + Training budget"
            }
        ])
        
        return recommendations
    
    async def _generate_executive_charts(self, analyses: List[Dict]) -> List[Dict[str, Any]]:
        """Generate charts suitable for executive presentations"""
        charts = []
        
        # Risk severity distribution
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for analysis in analyses:
            for threat in analysis.get("threats", []):
                severity = threat.get("severity", "LOW")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        charts.append({
            "type": "pie",
            "title": "Risk Severity Distribution",
            "data": [{"label": k, "value": v} for k, v in severity_counts.items() if v > 0],
            "colors": ["#dc2626", "#ea580c", "#d97706", "#65a30d"]
        })
        
        # Risk trends (mock data for demo)
        charts.append({
            "type": "line",
            "title": "Risk Trend Analysis (30 Days)",
            "data": [
                {"date": (datetime.now() - timedelta(days=30-i)).strftime("%Y-%m-%d"), 
                 "risks": max(0, len(analyses) + (i % 7) - 3)} 
                for i in range(0, 31, 5)
            ]
        })
        
        return charts


class TechnicalReportAgent(BaseReportAgent):
    """Agent specialized in generating detailed technical reports"""
    
    def __init__(self):
        super().__init__("technical_agent", "Technical Report Generator")
    
    async def generate_content(self, request: ReportRequest, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed technical report content"""
        self.logger.info(f"Generating technical report for {len(request.project_ids)} projects")
        
        projects = data.get("projects", [])
        analyses = data.get("analyses", [])
        
        # Generate technical sections
        sections = [
            {
                "title": "Methodology",
                "type": "methodology",
                "content": await self._generate_methodology_section()
            },
            {
                "title": "Threat Analysis",
                "type": "threats",
                "content": await self._analyze_threats(analyses)
            },
            {
                "title": "MITRE ATT&CK Mapping",
                "type": "mitre",
                "content": await self._generate_mitre_analysis(analyses)
            },
            {
                "title": "Technical Recommendations",
                "type": "tech_recommendations",
                "content": await self._generate_technical_recommendations(analyses)
            },
            {
                "title": "Implementation Guidelines",
                "type": "implementation",
                "content": await self._generate_implementation_guidelines(analyses)
            }
        ]
        
        # Generate detailed charts
        charts = await self._generate_technical_charts(analyses)
        
        return {
            "title": f"Technical Security Analysis Report - {datetime.now().strftime('%Y-%m-%d')}",
            "executive_summary": await self._generate_technical_summary(analyses),
            "sections": sections,
            "charts": charts,
            "metadata": {
                "report_type": "technical",
                "analysis_depth": "detailed",
                "projects_analyzed": len(projects),
                "threats_identified": sum(len(a.get("threats", [])) for a in analyses),
                "generation_date": datetime.now().isoformat()
            }
        }
    
    async def _generate_methodology_section(self) -> Dict[str, Any]:
        """Generate methodology documentation"""
        return {
            "approach": "AI-powered multi-agent threat modeling",
            "frameworks": ["MITRE ATT&CK", "OWASP Top 10", "NIST Cybersecurity Framework"],
            "tools": ["Custom AI Analysis Engine", "STRIDE Framework", "Attack Tree Analysis"],
            "scope": "Comprehensive system architecture and data flow analysis",
            "limitations": [
                "Analysis based on provided system documentation",
                "Dynamic runtime analysis not included",
                "Third-party component analysis limited to known vulnerabilities"
            ]
        }
    
    async def _analyze_threats(self, analyses: List[Dict]) -> Dict[str, Any]:
        """Generate detailed threat analysis"""
        all_threats = []
        for analysis in analyses:
            all_threats.extend(analysis.get("threats", []))
        
        # Group threats by type
        threat_groups = {}
        for threat in all_threats:
            threat_type = threat.get("type", "Unknown")
            if threat_type not in threat_groups:
                threat_groups[threat_type] = []
            threat_groups[threat_type].append(threat)
        
        # Analyze each group
        threat_analysis = {}
        for threat_type, threats in threat_groups.items():
            threat_analysis[threat_type] = {
                "count": len(threats),
                "severity_distribution": self._calculate_severity_distribution(threats),
                "common_attack_vectors": self._extract_attack_vectors(threats),
                "affected_components": self._extract_affected_components(threats)
            }
        
        return threat_analysis
    
    async def _generate_mitre_analysis(self, analyses: List[Dict]) -> Dict[str, Any]:
        """Generate MITRE ATT&CK analysis"""
        tactics_count = {}
        techniques_count = {}
        
        for analysis in analyses:
            for threat in analysis.get("threats", []):
                # Count tactics
                tactics = threat.get("mitre_tactics", [])
                for tactic in tactics:
                    tactics_count[tactic] = tactics_count.get(tactic, 0) + 1
                
                # Count techniques
                techniques = threat.get("mitre_techniques", [])
                for technique in techniques:
                    techniques_count[technique] = techniques_count.get(technique, 0) + 1
        
        return {
            "tactics_coverage": tactics_count,
            "techniques_coverage": techniques_count,
            "coverage_summary": {
                "total_tactics": len(tactics_count),
                "total_techniques": len(techniques_count),
                "most_common_tactic": max(tactics_count, key=tactics_count.get) if tactics_count else None,
                "most_common_technique": max(techniques_count, key=techniques_count.get) if techniques_count else None
            }
        }
    
    async def _generate_technical_recommendations(self, analyses: List[Dict]) -> List[Dict[str, Any]]:
        """Generate technical implementation recommendations"""
        recommendations = []
        
        # Analyze common vulnerability patterns
        all_threats = []
        for analysis in analyses:
            all_threats.extend(analysis.get("threats", []))
        
        # Generate specific technical recommendations
        if any("injection" in threat.get("type", "").lower() for threat in all_threats):
            recommendations.append({
                "category": "Input Validation",
                "title": "Implement Comprehensive Input Sanitization",
                "description": "Deploy parameterized queries, input validation libraries, and sanitization frameworks.",
                "technical_details": {
                    "implementation": [
                        "Use prepared statements for all database queries",
                        "Implement server-side input validation",
                        "Deploy web application firewall (WAF)",
                        "Regular security code reviews"
                    ],
                    "technologies": ["OWASP ESAPI", "ModSecurity", "SQL Parameter Binding"],
                    "effort": "Medium (2-4 weeks)",
                    "priority": "High"
                }
            })
        
        if any("authentication" in threat.get("type", "").lower() for threat in all_threats):
            recommendations.append({
                "category": "Authentication",
                "title": "Multi-Factor Authentication Implementation",
                "description": "Deploy enterprise-grade multi-factor authentication across all systems.",
                "technical_details": {
                    "implementation": [
                        "Integrate SAML 2.0 or OAuth 2.0",
                        "Deploy hardware security keys",
                        "Implement adaptive authentication",
                        "Regular access reviews"
                    ],
                    "technologies": ["SAML 2.0", "OAuth 2.0", "FIDO2", "RADIUS"],
                    "effort": "High (6-8 weeks)",
                    "priority": "Critical"
                }
            })
        
        # Always include baseline recommendations
        recommendations.extend([
            {
                "category": "Monitoring",
                "title": "Security Information and Event Management (SIEM)",
                "description": "Implement comprehensive logging and real-time security monitoring.",
                "technical_details": {
                    "implementation": [
                        "Deploy centralized log collection",
                        "Configure real-time alerting",
                        "Implement threat intelligence feeds",
                        "Regular incident response drills"
                    ],
                    "technologies": ["ELK Stack", "Splunk", "QRadar", "Sentinel"],
                    "effort": "High (8-12 weeks)",
                    "priority": "Medium"
                }
            }
        ])
        
        return recommendations
    
    async def _generate_implementation_guidelines(self, analyses: List[Dict]) -> Dict[str, Any]:
        """Generate implementation guidelines"""
        return {
            "phases": [
                {
                    "phase": "Phase 1: Critical Risk Mitigation",
                    "duration": "30 days",
                    "activities": [
                        "Address all CRITICAL severity threats",
                        "Implement emergency patches",
                        "Deploy temporary compensating controls"
                    ]
                },
                {
                    "phase": "Phase 2: Infrastructure Hardening",
                    "duration": "60 days",
                    "activities": [
                        "Deploy monitoring and logging solutions",
                        "Implement access controls",
                        "Conduct security configuration reviews"
                    ]
                },
                {
                    "phase": "Phase 3: Process Improvement",
                    "duration": "90 days",
                    "activities": [
                        "Establish security development lifecycle",
                        "Implement automated security testing",
                        "Deploy continuous monitoring"
                    ]
                }
            ],
            "resources": {
                "personnel": ["Security Architect", "Security Engineer", "DevOps Engineer"],
                "tools": ["SIEM Platform", "Vulnerability Scanner", "Code Analysis Tools"],
                "budget": "Estimated $150K - $300K depending on organization size"
            }
        }
    
    async def _generate_technical_charts(self, analyses: List[Dict]) -> List[Dict[str, Any]]:
        """Generate technical analysis charts"""
        charts = []
        
        # Threat type distribution
        threat_types = {}
        for analysis in analyses:
            for threat in analysis.get("threats", []):
                threat_type = threat.get("type", "Unknown")
                threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
        
        charts.append({
            "type": "bar",
            "title": "Threat Types Distribution",
            "data": [{"label": k, "value": v} for k, v in sorted(threat_types.items(), key=lambda x: x[1], reverse=True)]
        })
        
        # MITRE ATT&CK tactics heatmap data
        tactics_count = {}
        for analysis in analyses:
            for threat in analysis.get("threats", []):
                tactics = threat.get("mitre_tactics", [])
                for tactic in tactics:
                    tactics_count[tactic] = tactics_count.get(tactic, 0) + 1
        
        charts.append({
            "type": "heatmap",
            "title": "MITRE ATT&CK Tactics Coverage",
            "data": [{"tactic": k, "count": v} for k, v in tactics_count.items()]
        })
        
        return charts
    
    def _calculate_severity_distribution(self, threats: List[Dict]) -> Dict[str, int]:
        """Calculate severity distribution for threats"""
        distribution = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for threat in threats:
            severity = threat.get("severity", "LOW")
            distribution[severity] = distribution.get(severity, 0) + 1
        return distribution
    
    def _extract_attack_vectors(self, threats: List[Dict]) -> List[str]:
        """Extract common attack vectors"""
        vectors = set()
        for threat in threats:
            if threat.get("attack_vector"):
                vectors.add(threat.get("attack_vector"))
        return list(vectors)
    
    def _extract_affected_components(self, threats: List[Dict]) -> List[str]:
        """Extract affected system components"""
        components = set()
        for threat in threats:
            if threat.get("affected_component"):
                components.add(threat.get("affected_component"))
        return list(components)
    
    async def _generate_technical_summary(self, analyses: List[Dict]) -> str:
        """Generate technical executive summary"""
        total_threats = sum(len(analysis.get("threats", [])) for analysis in analyses)
        unique_types = set()
        for analysis in analyses:
            for threat in analysis.get("threats", []):
                unique_types.add(threat.get("type", "Unknown"))
        
        return f"""
This technical analysis report provides detailed findings from the comprehensive security assessment of {len(analyses)} system(s).

TECHNICAL FINDINGS:
• Total Threats Identified: {total_threats}
• Unique Threat Categories: {len(unique_types)}
• Analysis Confidence: High (AI-powered multi-agent analysis)
• Coverage: Full system architecture and data flow analysis

The analysis employed advanced AI-powered threat modeling techniques combined with industry-standard frameworks including MITRE ATT&CK, OWASP, and NIST guidelines.

This report provides actionable technical recommendations with specific implementation guidance for immediate and long-term security improvements.
        """.strip()


class ComplianceReportAgent(BaseReportAgent):
    """Agent specialized in generating compliance and audit reports"""
    
    def __init__(self):
        super().__init__("compliance_agent", "Compliance Report Generator")
    
    async def generate_content(self, request: ReportRequest, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compliance-focused report content"""
        self.logger.info(f"Generating compliance report for {len(request.project_ids)} projects")
        
        analyses = data.get("analyses", [])
        projects = data.get("projects", [])
        
        # Map findings to compliance frameworks
        compliance_mappings = await self._map_to_compliance_frameworks(analyses)
        
        sections = [
            {
                "title": "Compliance Overview",
                "type": "overview",
                "content": compliance_mappings["overview"]
            },
            {
                "title": "NIST CSF Alignment",
                "type": "nist_csf",
                "content": compliance_mappings["nist_csf"]
            },
            {
                "title": "ISO 27001 Requirements",
                "type": "iso27001",
                "content": compliance_mappings["iso27001"]
            },
            {
                "title": "SOC 2 Controls",
                "type": "soc2",
                "content": compliance_mappings["soc2"]
            },
            {
                "title": "Compliance Gaps",
                "type": "gaps",
                "content": await self._identify_compliance_gaps(analyses)
            }
        ]
        
        charts = await self._generate_compliance_charts(compliance_mappings)
        
        return {
            "title": f"Compliance Assessment Report - {datetime.now().strftime('%Y-%m-%d')}",
            "executive_summary": await self._generate_compliance_summary(compliance_mappings),
            "sections": sections,
            "charts": charts,
            "metadata": {
                "report_type": "compliance",
                "frameworks": ["NIST CSF", "ISO 27001", "SOC 2"],
                "projects_analyzed": len(projects),
                "generation_date": datetime.now().isoformat()
            }
        }
    
    async def _map_to_compliance_frameworks(self, analyses: List[Dict]) -> Dict[str, Any]:
        """Map security findings to compliance frameworks"""
        # This is a simplified mapping - in a real implementation,
        # this would involve comprehensive framework databases
        
        all_threats = []
        for analysis in analyses:
            all_threats.extend(analysis.get("threats", []))
        
        nist_csf_mapping = {
            "identify": {"controls_covered": 0, "gaps": []},
            "protect": {"controls_covered": 0, "gaps": []},
            "detect": {"controls_covered": 0, "gaps": []},
            "respond": {"controls_covered": 0, "gaps": []},
            "recover": {"controls_covered": 0, "gaps": []}
        }
        
        iso27001_mapping = {
            "security_policies": {"status": "partial", "findings": []},
            "access_control": {"status": "needs_improvement", "findings": []},
            "cryptography": {"status": "compliant", "findings": []},
            "physical_security": {"status": "not_assessed", "findings": []},
            "incident_management": {"status": "partial", "findings": []}
        }
        
        soc2_mapping = {
            "security": {"trust_criteria": "Type II", "status": "partial_compliance"},
            "availability": {"trust_criteria": "Type II", "status": "needs_assessment"},
            "confidentiality": {"trust_criteria": "Type II", "status": "partial_compliance"},
            "processing_integrity": {"trust_criteria": "Type II", "status": "needs_assessment"},
            "privacy": {"trust_criteria": "Type II", "status": "not_applicable"}
        }
        
        # Analyze threats for compliance impact
        for threat in all_threats:
            threat_type = threat.get("type", "").lower()
            
            # Map to NIST CSF
            if "authentication" in threat_type:
                nist_csf_mapping["protect"]["gaps"].append("Identity and Access Management")
            if "monitoring" in threat_type:
                nist_csf_mapping["detect"]["gaps"].append("Continuous Monitoring")
            
            # Map to ISO 27001
            if "access" in threat_type:
                iso27001_mapping["access_control"]["findings"].append(threat.get("description", ""))
        
        return {
            "overview": {
                "total_frameworks": 3,
                "compliance_score": 65,  # Mock score
                "critical_gaps": len([t for t in all_threats if t.get("severity") == "CRITICAL"])
            },
            "nist_csf": nist_csf_mapping,
            "iso27001": iso27001_mapping,
            "soc2": soc2_mapping
        }
    
    async def _identify_compliance_gaps(self, analyses: List[Dict]) -> List[Dict[str, Any]]:
        """Identify compliance gaps based on analysis results"""
        gaps = []
        
        all_threats = []
        for analysis in analyses:
            all_threats.extend(analysis.get("threats", []))
        
        critical_threats = [t for t in all_threats if t.get("severity") == "CRITICAL"]
        
        if critical_threats:
            gaps.append({
                "framework": "All Frameworks",
                "gap_type": "Critical Security Findings",
                "description": f"{len(critical_threats)} critical security issues identified that impact compliance posture",
                "impact": "High",
                "remediation_timeline": "Immediate (30 days)"
            })
        
        # Mock additional gaps
        gaps.extend([
            {
                "framework": "NIST CSF",
                "gap_type": "Incident Response",
                "description": "Formal incident response procedures need documentation and testing",
                "impact": "Medium",
                "remediation_timeline": "90 days"
            },
            {
                "framework": "ISO 27001",
                "gap_type": "Risk Assessment",
                "description": "Regular risk assessment process requires formalization",
                "impact": "Medium",
                "remediation_timeline": "60 days"
            },
            {
                "framework": "SOC 2",
                "gap_type": "Continuous Monitoring",
                "description": "Enhanced monitoring controls needed for availability criteria",
                "impact": "Low",
                "remediation_timeline": "120 days"
            }
        ])
        
        return gaps
    
    async def _generate_compliance_charts(self, mappings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate compliance-focused charts"""
        charts = []
        
        # Compliance score by framework
        charts.append({
            "type": "radar",
            "title": "Compliance Framework Scores",
            "data": [
                {"framework": "NIST CSF", "score": 70},
                {"framework": "ISO 27001", "score": 65},
                {"framework": "SOC 2", "score": 60}
            ]
        })
        
        # Gap severity distribution
        charts.append({
            "type": "donut",
            "title": "Compliance Gap Severity",
            "data": [
                {"label": "High Impact", "value": 1},
                {"label": "Medium Impact", "value": 2},
                {"label": "Low Impact", "value": 1}
            ],
            "colors": ["#dc2626", "#d97706", "#65a30d"]
        })
        
        return charts
    
    async def _generate_compliance_summary(self, mappings: Dict[str, Any]) -> str:
        """Generate compliance executive summary"""
        compliance_score = mappings["overview"]["compliance_score"]
        critical_gaps = mappings["overview"]["critical_gaps"]
        
        return f"""
This compliance assessment report evaluates organizational security posture against leading industry frameworks.

COMPLIANCE SUMMARY:
• Overall Compliance Score: {compliance_score}%
• Critical Compliance Gaps: {critical_gaps}
• Frameworks Assessed: NIST CSF, ISO 27001, SOC 2 Type II

STATUS BY FRAMEWORK:
• NIST Cybersecurity Framework: 70% compliant (Needs improvement in Detect and Respond functions)
• ISO 27001: 65% compliant (Focus needed on access controls and risk management)  
• SOC 2 Type II: 60% compliant (Monitoring and availability controls require enhancement)

{"PRIORITY ACTION REQUIRED: Critical gaps identified that may impact audit readiness and regulatory compliance." if critical_gaps > 0 else "The organization demonstrates reasonable compliance posture with identified improvement opportunities."}

Detailed gap analysis and remediation roadmap provided in subsequent sections.
        """.strip()


class ReportOrchestrator:
    """Main orchestrator for managing multiple report generation agents"""
    
    def __init__(self):
        self.agents = {
            ReportType.EXECUTIVE_SUMMARY: ExecutiveReportAgent(),
            ReportType.TECHNICAL_DETAILED: TechnicalReportAgent(),
            ReportType.COMPLIANCE_AUDIT: ComplianceReportAgent(),
            # Additional agents can be added here
        }
        self.logger = logging.getLogger("report_orchestrator")
    
    async def generate_report(self, request: ReportRequest) -> ReportContent:
        """Generate a report using the appropriate agent"""
        self.logger.info(f"Starting report generation: {request.report_type}")
        
        # Validate request
        if request.report_type not in self.agents:
            raise ValueError(f"Unsupported report type: {request.report_type}")
        
        # Gather data for report generation
        data = await self._gather_report_data(request)
        
        # Get the appropriate agent
        agent = self.agents[request.report_type]
        
        # Validate data with agent
        if not await agent.validate_data(data):
            raise ValueError("Data validation failed for report generation")
        
        # Generate content
        content_data = await agent.generate_content(request, data)
        
        # Create report content object
        report_content = ReportContent(
            title=content_data["title"],
            executive_summary=content_data["executive_summary"],
            sections=content_data["sections"],
            charts=content_data.get("charts", []),
            recommendations=content_data.get("recommendations", []),
            metadata=content_data["metadata"],
            generated_at=datetime.now()
        )
        
        self.logger.info(f"Report generation completed: {request.report_type}")
        return report_content
    
    async def _gather_report_data(self, request: ReportRequest) -> Dict[str, Any]:
        """Gather all necessary data for report generation"""
        # This would integrate with the actual database
        # For now, returning mock data structure
        
        data = {
            "projects": [],
            "analyses": []
        }
        
        # In a real implementation, this would query the database
        # for the specified project IDs and date ranges
        for project_id in request.project_ids:
            # Mock project data
            project_data = {
                "id": project_id,
                "name": f"Project {project_id}",
                "description": f"Security analysis for project {project_id}",
                "created_at": datetime.now().isoformat()
            }
            data["projects"].append(project_data)
            
            # Mock analysis data
            analysis_data = {
                "id": f"analysis_{project_id}",
                "project_id": project_id,
                "risk_score": 6.5,
                "confidence_score": 85,
                "threats": [
                    {
                        "id": f"threat_1_{project_id}",
                        "type": "SQL Injection",
                        "severity": "HIGH",
                        "description": f"SQL injection vulnerability in project {project_id}",
                        "attack_vector": "Network",
                        "affected_component": "Database Interface",
                        "mitre_tactics": ["Initial Access", "Execution"],
                        "mitre_techniques": ["T1190", "T1059"]
                    },
                    {
                        "id": f"threat_2_{project_id}",
                        "type": "Authentication Bypass",
                        "severity": "CRITICAL",
                        "description": f"Authentication bypass vulnerability in project {project_id}",
                        "attack_vector": "Network",
                        "affected_component": "Authentication Module",
                        "mitre_tactics": ["Defense Evasion", "Privilege Escalation"],
                        "mitre_techniques": ["T1548", "T1078"]
                    }
                ],
                "created_at": datetime.now().isoformat()
            }
            data["analyses"].append(analysis_data)
        
        return data
    
    async def list_supported_formats(self) -> List[ReportFormat]:
        """Get list of supported report formats"""
        return list(ReportFormat)
    
    async def list_supported_types(self) -> List[ReportType]:
        """Get list of supported report types"""
        return list(self.agents.keys())


# Global report orchestrator instance
report_orchestrator = ReportOrchestrator()


async def generate_report_async(request: ReportRequest) -> ReportContent:
    """Async wrapper for report generation"""
    return await report_orchestrator.generate_report(request)


def create_sample_request(report_type: ReportType = ReportType.EXECUTIVE_SUMMARY) -> ReportRequest:
    """Create a sample report request for testing"""
    return ReportRequest(
        report_type=report_type,
        format=ReportFormat.PDF,
        project_ids=["project_001", "project_002"],
        include_charts=True,
        include_mitre_mapping=True,
        include_recommendations=True,
        audience_level="executive"
    )
