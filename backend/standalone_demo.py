"""
Standalone AITM Report Generation Demo Server

This is a simplified demo server that showcases the report generation system
without requiring complex database setup.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from io import BytesIO

from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Mock the report generation system
from app.agents.report_generator import (
    ReportType, ReportFormat, ReportRequest, ReportContent,
    ExecutiveReportAgent, TechnicalReportAgent, ComplianceReportAgent
)
from app.services.report_formatter import HTMLTemplateEngine

# Create FastAPI app
app = FastAPI(
    title="AITM Reports Demo",
    description="Standalone demo server for AITM report generation system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class ReportGenerationRequest(BaseModel):
    report_type: ReportType
    format: ReportFormat
    project_ids: List[str]
    date_range: Optional[Dict[str, str]] = None
    include_charts: bool = True
    include_mitre_mapping: bool = True
    include_recommendations: bool = True
    custom_sections: Optional[List[str]] = None
    audience_level: str = Field(default="technical")
    branding: Optional[Dict[str, str]] = None

class ReportResponse(BaseModel):
    report_id: str
    title: str
    report_type: ReportType
    format: ReportFormat
    status: str
    generated_at: datetime
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    preview_url: Optional[str] = None
    metadata: Dict[str, Any]

# In-memory storage for demo
generated_reports: Dict[str, Dict[str, Any]] = {}

# Initialize report agents
executive_agent = ExecutiveReportAgent()
technical_agent = TechnicalReportAgent()
compliance_agent = ComplianceReportAgent()
html_engine = HTMLTemplateEngine()

# Mock user for demo
class MockUser:
    def __init__(self):
        self.id = "demo_user_001"
        self.email = "demo@aitm.com"
        self.full_name = "AITM Demo User"
        self.is_active = True
        self.is_superuser = False

demo_user = MockUser()

@app.get("/")
async def root():
    return {
        "message": "AITM Reports Demo Server", 
        "docs": "/docs",
        "reports": "/api/v1/reports",
        "sample_report": "/api/v1/reports/sample"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "reports-demo"}

@app.get("/api/v1/reports/types")
async def get_report_types():
    """Get list of available report types"""
    return [
        "executive_summary",
        "technical_detailed", 
        "compliance_audit"
    ]

@app.get("/api/v1/reports/formats")
async def get_report_formats():
    """Get list of supported report formats"""
    return ["html", "json", "markdown"]

@app.post("/api/v1/reports/sample")
async def generate_sample_report(
    report_type: ReportType = ReportType.EXECUTIVE_SUMMARY,
    format: ReportFormat = ReportFormat.HTML
):
    """Generate a sample report for testing/demonstration"""
    try:
        # Create sample request
        sample_request = ReportRequest(
            report_type=report_type,
            format=format,
            project_ids=["demo_project_001", "demo_project_002"],
            include_charts=True,
            include_mitre_mapping=True,
            include_recommendations=True,
            audience_level="executive"
        )
        
        # Generate mock data
        mock_data = {
            "projects": [
                {
                    "id": "demo_project_001",
                    "name": "E-commerce Platform",
                    "description": "Online shopping application with payment processing",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "demo_project_002", 
                    "name": "Mobile Banking App",
                    "description": "Secure mobile banking application",
                    "created_at": datetime.now().isoformat()
                }
            ],
            "analyses": [
                {
                    "id": "analysis_001",
                    "project_id": "demo_project_001",
                    "risk_score": 7.2,
                    "confidence_score": 89,
                    "threats": [
                        {
                            "id": "threat_001",
                            "type": "SQL Injection",
                            "severity": "HIGH",
                            "description": "Potential SQL injection vulnerability in payment processing module",
                            "attack_vector": "Network",
                            "affected_component": "Payment Gateway",
                            "mitre_tactics": ["Initial Access", "Execution"],
                            "mitre_techniques": ["T1190", "T1059"]
                        },
                        {
                            "id": "threat_002", 
                            "type": "Authentication Bypass",
                            "severity": "CRITICAL",
                            "description": "Weak authentication implementation allows bypass",
                            "attack_vector": "Network",
                            "affected_component": "User Authentication",
                            "mitre_tactics": ["Defense Evasion", "Privilege Escalation"],
                            "mitre_techniques": ["T1548", "T1078"]
                        }
                    ],
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "analysis_002",
                    "project_id": "demo_project_002", 
                    "risk_score": 5.8,
                    "confidence_score": 92,
                    "threats": [
                        {
                            "id": "threat_003",
                            "type": "Data Exposure",
                            "severity": "MEDIUM",
                            "description": "Sensitive financial data may be exposed through API endpoints",
                            "attack_vector": "Network",
                            "affected_component": "API Gateway",
                            "mitre_tactics": ["Collection", "Exfiltration"],
                            "mitre_techniques": ["T1119", "T1041"]
                        }
                    ],
                    "created_at": datetime.now().isoformat()
                }
            ]
        }
        
        # Select appropriate agent
        if report_type == ReportType.EXECUTIVE_SUMMARY:
            agent = executive_agent
        elif report_type == ReportType.TECHNICAL_DETAILED:
            agent = technical_agent
        elif report_type == ReportType.COMPLIANCE_AUDIT:
            agent = compliance_agent
        else:
            agent = executive_agent
        
        # Generate content
        content_data = await agent.generate_content(sample_request, mock_data)
        
        # Create report content
        report_content = ReportContent(
            title=content_data["title"],
            executive_summary=content_data["executive_summary"],
            sections=content_data["sections"],
            charts=content_data.get("charts", []),
            recommendations=content_data.get("recommendations", []),
            metadata=content_data["metadata"],
            generated_at=datetime.now()
        )
        
        # Format content based on requested format
        if format == ReportFormat.HTML:
            formatted_content = await html_engine.render_report(report_content)
            return Response(content=formatted_content, media_type="text/html")
        elif format == ReportFormat.JSON:
            formatted_content = json.dumps({
                "title": report_content.title,
                "executive_summary": report_content.executive_summary,
                "sections": report_content.sections,
                "charts": report_content.charts,
                "recommendations": report_content.recommendations,
                "metadata": report_content.metadata,
                "generated_at": report_content.generated_at.isoformat()
            }, indent=2, default=str)
            return Response(content=formatted_content, media_type="application/json")
        elif format == ReportFormat.MARKDOWN:
            # Generate basic markdown
            md_parts = [
                f"# {report_content.title}\n",
                f"*Generated on {report_content.generated_at.strftime('%B %d, %Y at %I:%M %p')}*\n",
                "## Executive Summary\n",
                f"{report_content.executive_summary}\n"
            ]
            
            for section in report_content.sections:
                title = section.get("title", "Section")
                md_parts.append(f"## {title}\n")
                content_data = section.get("content", {})
                if isinstance(content_data, dict):
                    for key, value in content_data.items():
                        md_parts.append(f"**{key.replace('_', ' ').title()}:** {value}\n")
                md_parts.append("\n")
            
            formatted_content = "\n".join(md_parts)
            return Response(content=formatted_content, media_type="text/markdown")
        
        return {"error": "Unsupported format"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate sample report: {str(e)}")

@app.post("/api/v1/reports/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Generate a report asynchronously"""
    try:
        # Create unique report ID
        report_id = str(uuid.uuid4())
        
        # Store initial report status
        report_info = {
            "report_id": report_id,
            "status": "generating",
            "created_at": datetime.now(),
            "user_id": demo_user.id,
            "request": request,
            "content": None,
            "formatted_content": None,
            "file_size": None
        }
        generated_reports[report_id] = report_info
        
        # Schedule background generation (simulate instant completion for demo)
        background_tasks.add_task(
            _generate_report_background,
            report_id,
            request
        )
        
        return ReportResponse(
            report_id=report_id,
            title=f"{request.report_type.value.replace('_', ' ').title()} Report",
            report_type=request.report_type,
            format=request.format,
            status="generating",
            generated_at=datetime.now(),
            download_url=f"/api/v1/reports/{report_id}/download",
            preview_url=f"/api/v1/reports/{report_id}/preview",
            metadata={
                "projects_count": len(request.project_ids),
                "audience_level": request.audience_level
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@app.get("/api/v1/reports/{report_id}/status")
async def get_report_status(report_id: str):
    """Get the status of a report generation"""
    if report_id not in generated_reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report_info = generated_reports[report_id]
    
    return {
        "report_id": report_id,
        "status": report_info["status"],
        "created_at": report_info["created_at"],
        "completed_at": report_info.get("completed_at"),
        "error": report_info.get("error")
    }

@app.get("/api/v1/reports/{report_id}/preview")
async def preview_report(report_id: str):
    """Preview a generated report (HTML only)"""
    if report_id not in generated_reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report_info = generated_reports[report_id]
    
    if report_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Report not ready for preview")
    
    content = report_info.get("content")
    if not content:
        raise HTTPException(status_code=500, detail="Report content not available")
    
    # Generate HTML preview
    try:
        html_content = await html_engine.render_report(content)
        return Response(content=html_content, media_type="text/html")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate preview")

@app.get("/api/v1/reports")
async def list_reports():
    """List generated reports"""
    user_reports = []
    for report_id, report_info in generated_reports.items():
        user_reports.append(ReportResponse(
            report_id=report_id,
            title=report_info.get("content", {}).get("title", f"Report {report_id}") if report_info.get("content") else f"Report {report_id}",
            report_type=report_info["request"].report_type,
            format=report_info["request"].format,
            status=report_info["status"],
            generated_at=report_info["created_at"],
            file_size=report_info.get("file_size"),
            download_url=f"/api/v1/reports/{report_id}/download" if report_info["status"] == "completed" else None,
            preview_url=f"/api/v1/reports/{report_id}/preview" if report_info["status"] == "completed" else None,
            metadata={
                "projects_count": len(report_info["request"].project_ids),
                "audience_level": report_info["request"].audience_level
            }
        ))
    
    # Sort by creation date (newest first)
    user_reports.sort(key=lambda x: x.generated_at, reverse=True)
    
    return {
        "reports": user_reports,
        "total": len(user_reports),
        "page": 1,
        "page_size": len(user_reports)
    }

@app.get("/api/v1/reports/analytics")
async def get_report_analytics():
    """Get analytics about report generation"""
    user_reports = list(generated_reports.values())
    
    total_reports = len(user_reports)
    completed_reports = len([r for r in user_reports if r["status"] == "completed"])
    failed_reports = len([r for r in user_reports if r["status"] == "failed"])
    generating_reports = len([r for r in user_reports if r["status"] == "generating"])
    
    # Report type distribution
    type_distribution = {}
    for report in user_reports:
        report_type = report["request"].report_type.value
        type_distribution[report_type] = type_distribution.get(report_type, 0) + 1
    
    # Format distribution
    format_distribution = {}
    for report in user_reports:
        format_type = report["request"].format.value
        format_distribution[format_type] = format_distribution.get(format_type, 0) + 1
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_reports = [
        r for r in user_reports
        if r["created_at"] >= thirty_days_ago
    ]
    
    return {
        "summary": {
            "total_reports": total_reports,
            "completed_reports": completed_reports,
            "failed_reports": failed_reports,
            "generating_reports": generating_reports,
            "success_rate": (completed_reports / total_reports * 100) if total_reports > 0 else 0
        },
        "distributions": {
            "by_type": type_distribution,
            "by_format": format_distribution
        },
        "recent_activity": {
            "reports_last_30_days": len(recent_reports),
            "scheduled_reports": 0
        }
    }

# Background task function
async def _generate_report_background(report_id: str, request: ReportGenerationRequest):
    """Background task to generate report"""
    try:
        # Update status
        generated_reports[report_id]["status"] = "processing"
        
        # Mock data for demonstration
        mock_data = {
            "projects": [
                {
                    "id": pid,
                    "name": f"Project {pid}",
                    "description": f"Security analysis for project {pid}",
                    "created_at": datetime.now().isoformat()
                } for pid in request.project_ids
            ],
            "analyses": [
                {
                    "id": f"analysis_{pid}",
                    "project_id": pid,
                    "risk_score": 6.5,
                    "confidence_score": 85,
                    "threats": [
                        {
                            "id": f"threat_1_{pid}",
                            "type": "SQL Injection",
                            "severity": "HIGH",
                            "description": f"SQL injection vulnerability in project {pid}",
                            "attack_vector": "Network",
                            "affected_component": "Database Interface",
                            "mitre_tactics": ["Initial Access", "Execution"],
                            "mitre_techniques": ["T1190", "T1059"]
                        }
                    ],
                    "created_at": datetime.now().isoformat()
                } for pid in request.project_ids
            ]
        }
        
        # Select appropriate agent
        if request.report_type == ReportType.EXECUTIVE_SUMMARY:
            agent = executive_agent
        elif request.report_type == ReportType.TECHNICAL_DETAILED:
            agent = technical_agent
        elif request.report_type == ReportType.COMPLIANCE_AUDIT:
            agent = compliance_agent
        else:
            agent = executive_agent
        
        # Create internal request format
        internal_request = ReportRequest(
            report_type=request.report_type,
            format=request.format,
            project_ids=request.project_ids,
            date_range=request.date_range,
            include_charts=request.include_charts,
            include_mitre_mapping=request.include_mitre_mapping,
            include_recommendations=request.include_recommendations,
            custom_sections=request.custom_sections,
            audience_level=request.audience_level,
            branding=request.branding
        )
        
        # Generate content
        content_data = await agent.generate_content(internal_request, mock_data)
        
        # Create report content
        content = ReportContent(
            title=content_data["title"],
            executive_summary=content_data["executive_summary"],
            sections=content_data["sections"],
            charts=content_data.get("charts", []),
            recommendations=content_data.get("recommendations", []),
            metadata=content_data["metadata"],
            generated_at=datetime.now()
        )
        
        # Store content and update status
        generated_reports[report_id]["content"] = content
        generated_reports[report_id]["status"] = "completed"
        generated_reports[report_id]["completed_at"] = datetime.now()
        generated_reports[report_id]["file_size"] = 5000  # Mock size
        
    except Exception as e:
        generated_reports[report_id]["status"] = "failed"
        generated_reports[report_id]["error"] = str(e)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AITM Reports Demo Server...")
    print("📊 Available at: http://localhost:38527")
    print("📖 API Documentation: http://localhost:38527/docs")
    print("🔬 Sample Report: http://localhost:38527/api/v1/reports/sample")
    
    uvicorn.run(
        "standalone_demo:app", 
        host="0.0.0.0", 
        port=38527, 
        reload=True,
        log_level="info"
    )
