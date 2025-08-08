#!/usr/bin/env python3
"""
Add mock analysis results to test the frontend
"""

import asyncio
import json
from datetime import datetime
from app.core.database import async_session, AnalysisResults, Project, AnalysisState
from sqlalchemy import select, update

async def add_mock_results():
    async with async_session() as db:
        # Update project status to completed
        await db.execute(
            update(Project)
            .where(Project.id == 2)
            .values(status="completed")
        )
        
        # Add analysis state
        analysis_state = AnalysisState(
            project_id=2,
            status="completed",
            current_phase="completed",
            progress_percentage=100.0,
            progress_message="Analysis completed successfully",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            configuration=json.dumps({
                "analysis_depth": "standard",
                "include_threat_modeling": True,
                "include_mitigations": True,
                "priority_level": "high"
            })
        )
        db.add(analysis_state)
        
        # Mock executive summary
        executive_summary = {
            "overview": "The web application presents a moderate security risk profile with several critical vulnerabilities identified in user authentication and file upload mechanisms.",
            "key_findings": [
                "Insufficient input validation on file uploads could lead to malicious file execution",
                "Session management lacks proper timeout and renewal mechanisms",
                "Database queries vulnerable to SQL injection attacks",
                "API endpoints missing proper authentication checks"
            ],
            "priority_actions": [
                "Implement file type validation and scanning",
                "Upgrade authentication system with MFA",
                "Apply parameterized queries throughout the application",
                "Implement comprehensive API security measures"
            ],
            "risk_level": "medium-high",
            "business_impact": "Medium - potential data breach and system compromise"
        }
        
        # Mock attack paths
        attack_paths = [
            {
                "name": "File Upload Attack Chain",
                "description": "Attacker uploads malicious file, gains code execution, and escalates privileges",
                "impact": "high",
                "likelihood": "medium",
                "techniques": [
                    {
                        "step": 1,
                        "technique_id": "T1566.001",
                        "technique_name": "Phishing: Spearphishing Attachment",
                        "tactic": "Initial Access",
                        "target_component": "File Upload Service",
                        "description": "Attacker crafts malicious file to exploit upload validation"
                    },
                    {
                        "step": 2,
                        "technique_id": "T1059.007",
                        "technique_name": "Command and Scripting Interpreter: JavaScript",
                        "tactic": "Execution",
                        "target_component": "Web Server",
                        "description": "Execute malicious code through uploaded file"
                    }
                ]
            },
            {
                "name": "SQL Injection to Data Exfiltration",
                "description": "Exploit SQL injection vulnerability to access and extract sensitive database information",
                "impact": "critical",
                "likelihood": "high",
                "techniques": [
                    {
                        "step": 1,
                        "technique_id": "T1190",
                        "technique_name": "Exploit Public-Facing Application",
                        "tactic": "Initial Access",
                        "target_component": "Database API",
                        "description": "SQL injection through user input fields"
                    },
                    {
                        "step": 2,
                        "technique_id": "T1005",
                        "technique_name": "Data from Local System",
                        "tactic": "Collection",
                        "target_component": "Database Server",
                        "description": "Extract sensitive customer and user data"
                    }
                ]
            }
        ]
        
        # Mock identified techniques
        identified_techniques = [
            {
                "technique_id": "T1190",
                "technique_name": "Exploit Public-Facing Application",
                "tactic": "Initial Access",
                "applicability_score": 0.9,
                "system_component": "Web Application",
                "rationale": "Application has multiple public-facing endpoints with insufficient validation",
                "prerequisites": ["Network access to application", "Knowledge of endpoints"]
            },
            {
                "technique_id": "T1059.007", 
                "technique_name": "Command and Scripting Interpreter: JavaScript",
                "tactic": "Execution",
                "applicability_score": 0.8,
                "system_component": "Frontend/Backend",
                "rationale": "JavaScript execution possible through uploaded files and XSS",
                "prerequisites": ["File upload or XSS vulnerability"]
            },
            {
                "technique_id": "T1005",
                "technique_name": "Data from Local System",
                "tactic": "Collection", 
                "applicability_score": 0.7,
                "system_component": "Database",
                "rationale": "Database access possible through SQL injection",
                "prerequisites": ["Database access", "SQL injection vulnerability"]
            }
        ]
        
        # Mock recommendations
        recommendations = [
            {
                "title": "Implement Comprehensive File Upload Security",
                "description": "Deploy multi-layered file upload security including type validation, content scanning, and sandboxed execution environment",
                "priority": "high",
                "attack_technique": "T1566.001",
                "affected_assets": ["File Upload Service", "Web Server"],
                "implementation_effort": "medium",
                "cost_estimate": "$15,000-25,000",
                "timeline": "2-3 weeks"
            },
            {
                "title": "Database Security Hardening",
                "description": "Implement parameterized queries, input validation, and database access controls",
                "priority": "urgent",
                "attack_technique": "T1190",
                "affected_assets": ["Database Server", "API Layer"],
                "implementation_effort": "high",
                "cost_estimate": "$25,000-35,000", 
                "timeline": "3-4 weeks"
            },
            {
                "title": "Authentication System Upgrade",
                "description": "Deploy multi-factor authentication and improve session management",
                "priority": "high",
                "affected_assets": ["Authentication Service", "User Management"],
                "implementation_effort": "medium",
                "cost_estimate": "$10,000-20,000",
                "timeline": "2-3 weeks"
            }
        ]
        
        # Mock system analysis results
        system_analysis_results = [
            {
                "critical_assets": [
                    {"name": "User Database", "type": "data_store", "criticality": "high"},
                    {"name": "Authentication Service", "type": "service", "criticality": "high"},
                    {"name": "File Upload Service", "type": "service", "criticality": "medium"}
                ],
                "system_components": [
                    {"name": "React Frontend", "type": "frontend", "trust_level": "low"},
                    {"name": "Node.js Backend", "type": "backend", "trust_level": "medium"},
                    {"name": "MySQL Database", "type": "database", "trust_level": "high"}
                ],
                "entry_points": [
                    {"name": "Web Interface", "type": "web", "exposure": "public"},
                    {"name": "REST API", "type": "api", "exposure": "public"},
                    {"name": "File Upload Endpoint", "type": "upload", "exposure": "authenticated"}
                ]
            }
        ]
        
        # Mock control evaluation results  
        control_evaluation_results = [
            {
                "control_category": "Authentication",
                "effectiveness": "medium",
                "gaps": ["No MFA", "Weak password policy"],
                "recommendations": ["Implement MFA", "Strengthen password requirements"]
            },
            {
                "control_category": "Input Validation",
                "effectiveness": "low", 
                "gaps": ["No file content scanning", "SQL injection vulnerabilities"],
                "recommendations": ["Implement comprehensive input validation", "Use parameterized queries"]
            }
        ]
        
        # Mock full report
        full_report = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "project_id": 2
            },
            "executive_summary": executive_summary,
            "threat_landscape": {
                "total_techniques_identified": len(identified_techniques),
                "high_risk_paths": len([p for p in attack_paths if p["impact"] == "high"]),
                "critical_vulnerabilities": 3
            },
            "recommendations": {
                "immediate_actions": recommendations[:2],
                "medium_term": recommendations[2:],
                "long_term": []
            },
            "metrics": {
                "overall_risk": 0.7,
                "residual_risk": 0.4,
                "coverage_score": 0.8
            }
        }
        
        # Create analysis results record
        analysis_results = AnalysisResults(
            project_id=2,
            overall_risk_score=0.7,
            confidence_score=0.85,
            executive_summary=json.dumps(executive_summary),
            attack_paths_data=json.dumps(attack_paths),
            identified_techniques=json.dumps(identified_techniques),
            recommendations_data=json.dumps(recommendations),
            system_analysis_results=json.dumps(system_analysis_results),
            control_evaluation_results=json.dumps(control_evaluation_results),
            full_report=json.dumps(full_report)
        )
        db.add(analysis_results)
        
        await db.commit()
        print("Mock analysis results added successfully for project 2!")

if __name__ == "__main__":
    asyncio.run(add_mock_results())
