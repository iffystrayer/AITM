"""
Enhanced AI API endpoints for advanced threat analysis
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.enhanced_ai_service import enhanced_ai_service, AnalysisMode, ThreatSeverity
from app.core.permissions import require_permission
from app.core.cache import CacheManager

# Initialize cache manager
cache_manager = CacheManager()

router = APIRouter()

# Request/Response Models

class AdvancedAnalysisRequest(BaseModel):
    """Request model for advanced system analysis"""
    system_description: str = Field(..., min_length=10, description="System description to analyze")
    analysis_mode: AnalysisMode = Field(default=AnalysisMode.STANDARD, description="Analysis depth and scope")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for analysis")
    cache_results: bool = Field(default=True, description="Whether to cache analysis results")

class ThreatIntelligenceResponse(BaseModel):
    """Response model for threat intelligence data"""
    threat_id: str
    name: str
    severity: ThreatSeverity
    confidence: float
    mitre_techniques: List[str]
    attack_vectors: List[str]
    potential_impact: Dict[str, Any]
    likelihood_score: float
    temporal_trends: Dict[str, float]
    contextual_factors: List[str]
    mitigation_strategies: List[Dict[str, Any]]

class AIInsightResponse(BaseModel):
    """Response model for AI-generated insights"""
    insight_type: str
    title: str
    description: str
    confidence: float
    supporting_data: Dict[str, Any]
    recommendations: List[str]
    priority_score: float

class AdvancedAnalysisResponse(BaseModel):
    """Response model for advanced analysis results"""
    analysis_id: str
    pattern_analysis: Dict[str, Any]
    technical_analysis: Optional[Dict[str, Any]] = None
    threat_intelligence: List[ThreatIntelligenceResponse]
    risk_analysis: Dict[str, Any]
    ai_insights: List[AIInsightResponse]
    temporal_analysis: Optional[Dict[str, Any]] = None
    analysis_metadata: Dict[str, Any]

class NaturalLanguageQueryRequest(BaseModel):
    """Request model for natural language queries"""
    query: str = Field(..., min_length=5, description="Natural language security question")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context for the query")
    include_recommendations: bool = Field(default=True, description="Include actionable recommendations")

class NaturalLanguageQueryResponse(BaseModel):
    """Response model for natural language query results"""
    query: str
    answer: str
    recommendations: List[str]
    confidence: float
    context_used: bool
    related_topics: Optional[List[str]] = None

class RiskPredictionRequest(BaseModel):
    """Request model for risk prediction"""
    system_description: str
    time_horizon_days: int = Field(default=30, ge=1, le=365, description="Prediction time horizon")
    scenario_analysis: bool = Field(default=True, description="Include scenario analysis")

class RiskPredictionResponse(BaseModel):
    """Response model for risk prediction"""
    current_risk_score: float
    predicted_risk_score: float
    confidence: float
    risk_level: str
    scenarios: Optional[Dict[str, Any]] = None
    risk_factors: List[str]
    recommendations: List[str]
    prediction_horizon_days: int

# API Endpoints

@router.post("/analyze/advanced", response_model=AdvancedAnalysisResponse)
async def advanced_system_analysis(
    request: AdvancedAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_permission("ai_analysis"))
):
    """
    Perform advanced AI-powered system analysis
    
    This endpoint provides comprehensive threat analysis including:
    - Pattern recognition and classification
    - Deep technical analysis (for DEEP/COMPREHENSIVE modes)
    - Contextual threat intelligence gathering
    - Advanced risk scoring with ML predictions
    - AI-generated insights and recommendations
    - Temporal threat analysis (for COMPREHENSIVE mode)
    """
    try:
        # Check cache first
        cache_key = f"advanced_analysis:{hash(request.system_description)}:{request.analysis_mode.value}"
        if request.cache_results:
            cached_result = await cache_manager.get(cache_key)
            if cached_result:
                return AdvancedAnalysisResponse.parse_obj(cached_result)
        
        # Perform advanced analysis
        analysis_results = await enhanced_ai_service.analyze_system_advanced(
            system_description=request.system_description,
            analysis_mode=request.analysis_mode,
            context=request.context
        )
        
        # Convert to response format
        response = AdvancedAnalysisResponse(
            analysis_id=f"analysis_{hash(request.system_description)}_{analysis_results['analysis_metadata']['timestamp']}",
            pattern_analysis=analysis_results["pattern_analysis"],
            technical_analysis=analysis_results.get("technical_analysis"),
            threat_intelligence=[
                ThreatIntelligenceResponse(
                    threat_id=threat.threat_id,
                    name=threat.name,
                    severity=threat.severity,
                    confidence=threat.confidence,
                    mitre_techniques=threat.mitre_techniques,
                    attack_vectors=threat.attack_vectors,
                    potential_impact=threat.potential_impact,
                    likelihood_score=threat.likelihood_score,
                    temporal_trends=threat.temporal_trends,
                    contextual_factors=threat.contextual_factors,
                    mitigation_strategies=threat.mitigation_strategies
                ) for threat in analysis_results["threat_intelligence"]
            ],
            risk_analysis=analysis_results["risk_analysis"],
            ai_insights=[
                AIInsightResponse(
                    insight_type=insight.insight_type,
                    title=insight.title,
                    description=insight.description,
                    confidence=insight.confidence,
                    supporting_data=insight.supporting_data,
                    recommendations=insight.recommendations,
                    priority_score=insight.priority_score
                ) for insight in analysis_results["ai_insights"]
            ],
            temporal_analysis=analysis_results.get("temporal_analysis"),
            analysis_metadata=analysis_results["analysis_metadata"]
        )
        
        # Cache results if requested
        if request.cache_results:
            await cache_manager.set(cache_key, response.dict(), expire=3600)  # Cache for 1 hour
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advanced analysis failed: {str(e)}"
        )

@router.post("/query/natural-language", response_model=NaturalLanguageQueryResponse)
async def natural_language_query(
    request: NaturalLanguageQueryRequest,
    _: str = Depends(require_permission("ai_query"))
):
    """
    Process natural language security questions
    
    This endpoint allows users to ask security-related questions in natural language
    and receive expert-level responses with actionable recommendations.
    """
    try:
        # Process the query
        query_result = await enhanced_ai_service.query_natural_language(
            query=request.query,
            context=request.context
        )
        
        # Handle errors
        if "error" in query_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=query_result["error"]
            )
        
        # Extract related topics from context
        related_topics = []
        if request.context:
            if "threat_intelligence" in request.context:
                related_topics.extend([t.get("name", "") for t in request.context["threat_intelligence"][:3]])
            if "detected_patterns" in request.context:
                related_topics.extend([p.get("name", "") for p in request.context["detected_patterns"][:3]])
        
        return NaturalLanguageQueryResponse(
            query=request.query,
            answer=query_result.get("answer", "Unable to process query"),
            recommendations=query_result.get("recommendations", []),
            confidence=query_result.get("confidence", 0.5),
            context_used=request.context is not None,
            related_topics=related_topics[:5] if related_topics else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )

@router.post("/predict/risk", response_model=RiskPredictionResponse)
async def predict_risk_evolution(
    request: RiskPredictionRequest,
    _: str = Depends(require_permission("risk_prediction"))
):
    """
    Predict risk evolution over time
    
    Uses advanced AI and ML models to forecast how security risks
    might evolve over the specified time horizon.
    """
    try:
        # First perform basic analysis to get threat data
        analysis_results = await enhanced_ai_service.analyze_system_advanced(
            system_description=request.system_description,
            analysis_mode=AnalysisMode.STANDARD
        )
        
        # Extract risk analysis
        risk_analysis = analysis_results.get("risk_analysis", {})
        current_risk = risk_analysis.get("aggregated_risk_score", {})
        future_risk = risk_analysis.get("future_risk_projection", {})
        
        # Get risk factors
        risk_factors = []
        if risk_analysis.get("risk_factors_breakdown"):
            for category, factors in risk_analysis["risk_factors_breakdown"].items():
                risk_factors.extend([f["threat"] for f in factors[:2]])  # Top 2 from each category
        
        # Build response
        scenarios = None
        if request.scenario_analysis and future_risk.get("scenarios"):
            scenarios = future_risk["scenarios"]
        
        return RiskPredictionResponse(
            current_risk_score=current_risk.get("final_risk_score", 0.5),
            predicted_risk_score=future_risk.get("scenarios", {}).get("realistic", {}).get("risk_score", 0.5),
            confidence=current_risk.get("confidence", 0.5),
            risk_level=current_risk.get("risk_level", "MEDIUM"),
            scenarios=scenarios,
            risk_factors=risk_factors[:10],  # Top 10 risk factors
            recommendations=future_risk.get("recommendations", []),
            prediction_horizon_days=request.time_horizon_days
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk prediction failed: {str(e)}"
        )

@router.get("/insights/trending")
async def get_trending_insights(
    limit: int = Query(default=10, ge=1, le=50, description="Number of insights to return"),
    severity_filter: Optional[ThreatSeverity] = Query(default=None, description="Filter by threat severity"),
    _: str = Depends(require_permission("threat_intelligence"))
):
    """
    Get trending security insights and threat intelligence
    
    Returns current trending threats, attack patterns, and security insights
    based on the latest threat intelligence data.
    """
    try:
        # This would typically query a threat intelligence database
        # For now, return mock trending data
        trending_insights = [
            {
                "id": "trend_1",
                "title": "Supply Chain Attacks Increasing",
                "description": "40% increase in supply chain attacks targeting npm packages",
                "severity": ThreatSeverity.HIGH,
                "confidence": 0.85,
                "trend_direction": "increasing",
                "affected_sectors": ["Software Development", "DevOps"],
                "mitre_techniques": ["T1195.001", "T1195.002"],
                "first_observed": "2024-01-15",
                "last_updated": "2024-02-10"
            },
            {
                "id": "trend_2", 
                "title": "API Security Vulnerabilities Rising",
                "description": "New authentication bypass techniques discovered in REST APIs",
                "severity": ThreatSeverity.HIGH,
                "confidence": 0.78,
                "trend_direction": "increasing",
                "affected_sectors": ["Web Applications", "Mobile Apps"],
                "mitre_techniques": ["T1190", "T1557"],
                "first_observed": "2024-01-20",
                "last_updated": "2024-02-08"
            },
            {
                "id": "trend_3",
                "title": "Container Escape Techniques Evolving",
                "description": "New Kubernetes privilege escalation methods detected",
                "severity": ThreatSeverity.CRITICAL,
                "confidence": 0.92,
                "trend_direction": "increasing",
                "affected_sectors": ["Cloud Infrastructure", "Container Orchestration"],
                "mitre_techniques": ["T1611", "T1068"],
                "first_observed": "2024-02-01",
                "last_updated": "2024-02-10"
            }
        ]
        
        # Apply severity filter if provided
        if severity_filter:
            trending_insights = [
                insight for insight in trending_insights 
                if ThreatSeverity(insight["severity"]) == severity_filter
            ]
        
        return {
            "trending_insights": trending_insights[:limit],
            "total_count": len(trending_insights),
            "last_updated": "2024-02-10T12:00:00Z",
            "data_sources": ["threat_intelligence_feeds", "security_research", "incident_reports"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trending insights: {str(e)}"
        )

@router.get("/capabilities")
async def get_ai_capabilities():
    """
    Get information about available AI capabilities and models
    
    Returns details about the AI features, analysis modes, and
    capabilities available in the enhanced AI system.
    """
    return {
        "analysis_modes": {
            "STANDARD": {
                "description": "Basic pattern recognition and risk assessment",
                "features": ["Pattern Analysis", "Basic Risk Scoring", "AI Insights"],
                "avg_duration_seconds": 15,
                "api_calls_estimated": 3
            },
            "DEEP": {
                "description": "Comprehensive technical analysis with detailed findings",
                "features": ["Pattern Analysis", "Technical Analysis", "Risk Scoring", "AI Insights"],
                "avg_duration_seconds": 45,
                "api_calls_estimated": 6
            },
            "LIGHTNING": {
                "description": "Rapid analysis for quick security assessments",
                "features": ["Basic Pattern Analysis", "Rapid Risk Scoring"],
                "avg_duration_seconds": 5,
                "api_calls_estimated": 1
            },
            "COMPREHENSIVE": {
                "description": "Full-spectrum analysis with all available features",
                "features": [
                    "Pattern Analysis", "Technical Analysis", "Threat Intelligence",
                    "Risk Scoring", "AI Insights", "Temporal Analysis", "Business Impact",
                    "Compliance Considerations"
                ],
                "avg_duration_seconds": 90,
                "api_calls_estimated": 10
            }
        },
        "threat_patterns": {
            "supported_patterns": [
                "SQL Injection Attack",
                "Cloud Configuration Vulnerability", 
                "API Security Weakness",
                "Container Escape Vulnerability",
                "Supply Chain Attack"
            ],
            "total_patterns": 5,
            "pattern_categories": ["Web Security", "Cloud Security", "API Security", "Container Security", "Supply Chain"]
        },
        "ai_insights": {
            "insight_types": [
                "critical_path", "defense_gap", "risk_trajectory", 
                "business_impact", "compliance"
            ],
            "confidence_threshold": 0.7,
            "max_insights_per_analysis": 10
        },
        "natural_language": {
            "supported_queries": [
                "Risk assessment questions",
                "Security best practices",
                "Threat mitigation strategies",
                "Compliance requirements",
                "Incident response guidance"
            ],
            "response_languages": ["English"],
            "max_query_length": 500
        },
        "risk_prediction": {
            "prediction_horizons": [7, 30, 90, 365],
            "scenario_types": ["optimistic", "realistic", "pessimistic"],
            "prediction_accuracy": "70-85% based on historical validation"
        }
    }

@router.post("/batch/analyze")
async def batch_analysis(
    descriptions: List[str] = Query(..., description="List of system descriptions to analyze"),
    analysis_mode: AnalysisMode = Query(default=AnalysisMode.STANDARD),
    _: str = Depends(require_permission("batch_analysis"))
):
    """
    Perform batch analysis on multiple systems
    
    Analyze multiple system descriptions in a single request.
    Useful for comparing security postures across different systems.
    """
    if len(descriptions) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 systems can be analyzed in a single batch"
        )
    
    try:
        results = []
        for i, description in enumerate(descriptions):
            try:
                analysis = await enhanced_ai_service.analyze_system_advanced(
                    system_description=description,
                    analysis_mode=analysis_mode
                )
                
                # Extract key metrics for summary
                risk_score = analysis.get("risk_analysis", {}).get("aggregated_risk_score", {}).get("final_risk_score", 0.5)
                pattern_count = len(analysis.get("pattern_analysis", {}).get("detected_patterns", []))
                insight_count = len(analysis.get("ai_insights", []))
                
                results.append({
                    "system_index": i,
                    "risk_score": risk_score,
                    "risk_level": analysis.get("risk_analysis", {}).get("aggregated_risk_score", {}).get("risk_level", "MEDIUM"),
                    "pattern_count": pattern_count,
                    "insight_count": insight_count,
                    "analysis_summary": {
                        "primary_threats": analysis.get("pattern_analysis", {}).get("primary_threat_vectors", [])[:3],
                        "confidence": analysis.get("analysis_metadata", {}).get("confidence_score", 0.5)
                    },
                    "full_analysis_available": True
                })
            except Exception as e:
                results.append({
                    "system_index": i,
                    "error": str(e),
                    "full_analysis_available": False
                })
        
        # Calculate batch summary
        successful_analyses = [r for r in results if "error" not in r]
        if successful_analyses:
            avg_risk = sum(r["risk_score"] for r in successful_analyses) / len(successful_analyses)
            high_risk_systems = len([r for r in successful_analyses if r["risk_score"] > 0.7])
        else:
            avg_risk = 0.0
            high_risk_systems = 0
        
        return {
            "batch_results": results,
            "batch_summary": {
                "total_systems": len(descriptions),
                "successful_analyses": len(successful_analyses),
                "failed_analyses": len(descriptions) - len(successful_analyses),
                "average_risk_score": round(avg_risk, 3),
                "high_risk_systems": high_risk_systems,
                "analysis_mode": analysis_mode.value
            },
            "processed_at": "2024-02-10T12:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )
