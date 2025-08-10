from fastapi import APIRouter, Depends, HTTPException, status
from app.services.prediction_service import RiskPredictionService
from app.core.dependencies import get_prediction_service
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response Models
class ThreatDataInput(BaseModel):
    """Input data for threat analysis predictions"""
    days_since_last_analysis: int = Field(0, ge=0, description="Days since last analysis")
    analysis_frequency: int = Field(1, ge=1, description="How often analyses are performed")
    unique_attack_paths: int = Field(0, ge=0, description="Number of unique attack paths identified")
    avg_attack_complexity: float = Field(0.5, ge=0.0, le=1.0, description="Average complexity of attacks (0-1)")
    critical_vulnerabilities: int = Field(0, ge=0, description="Number of critical vulnerabilities")
    public_endpoints: int = Field(0, ge=0, description="Number of public-facing endpoints")
    trust_boundaries: int = Field(1, ge=1, description="Number of trust boundaries")
    data_sensitivity_score: float = Field(0.5, ge=0.0, le=1.0, description="Data sensitivity score (0-1)")
    mitre_technique_count: int = Field(0, ge=0, description="Number of MITRE ATT&CK techniques identified")
    mitre_tactic_coverage: int = Field(0, ge=0, description="Number of MITRE tactics covered")
    high_impact_techniques: int = Field(0, ge=0, description="Number of high-impact techniques")

class HistoricalDataPoint(BaseModel):
    """Historical data point for model training"""
    timestamp: str = Field(description="ISO timestamp of the data point")
    risk_score: float = Field(ge=0.0, le=1.0, description="Risk score (0-1)")
    threat_data: ThreatDataInput

class RiskPredictionResponse(BaseModel):
    """Response model for risk predictions"""
    risk_score: float = Field(description="Predicted risk score (0-1)")
    confidence: float = Field(description="Prediction confidence (0-1)")
    model_predictions: Dict = Field(description="Individual model predictions")
    feature_contributions: Dict = Field(description="Feature contribution analysis")

class FutureRiskResponse(BaseModel):
    """Response model for future risk predictions"""
    current_risk: float
    days_ahead: int
    scenarios: Dict
    recommendations: List[str]

class TrendAnalysisResponse(BaseModel):
    """Response model for trend analysis"""
    trend: str
    slope: float
    correlation: float
    recent_avg: float
    historical_avg: float
    volatility: float
    confidence: float
    data_points: int

# API Endpoints
@router.post("/predict-current-risk", response_model=RiskPredictionResponse)
def predict_current_risk(
    threat_data: ThreatDataInput,
    service: RiskPredictionService = Depends(get_prediction_service)
):
    """Predict current risk score based on threat landscape data."""
    try:
        result = service.predict_risk_score(threat_data.dict())
        return RiskPredictionResponse(**result)
    except Exception as e:
        logger.error(f"Error predicting current risk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Risk prediction failed"
        )

@router.post("/predict-future-risk", response_model=FutureRiskResponse)
def predict_future_risk(
    threat_data: ThreatDataInput,
    days_ahead: int = Field(30, ge=1, le=365, description="Days ahead to predict"),
    service: RiskPredictionService = Depends(get_prediction_service)
):
    """Predict future risk progression with scenario analysis."""
    try:
        result = service.predict_future_risk(threat_data.dict(), days_ahead)
        return FutureRiskResponse(**result)
    except Exception as e:
        logger.error(f"Error predicting future risk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Future risk prediction failed"
        )

@router.post("/train-models")
def train_prediction_models(
    historical_data: List[HistoricalDataPoint],
    service: RiskPredictionService = Depends(get_prediction_service)
):
    """Train prediction models with historical data."""
    if len(historical_data) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 3 historical data points required for training"
        )
    
    try:
        # Convert to format expected by service
        training_data = []
        for point in historical_data:
            data_dict = point.threat_data.dict()
            data_dict['risk_score'] = point.risk_score
            data_dict['timestamp'] = point.timestamp
            training_data.append(data_dict)
        
        service.train(training_data)
        model_status = service.get_model_status()
        
        return {
            "message": f"Models trained successfully with {len(historical_data)} data points",
            "model_status": model_status
        }
    except Exception as e:
        logger.error(f"Error training models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model training failed"
        )

@router.post("/analyze-trends", response_model=TrendAnalysisResponse)
def analyze_risk_trends(
    historical_data: List[HistoricalDataPoint],
    service: RiskPredictionService = Depends(get_prediction_service)
):
    """Analyze trends in historical risk data."""
    if len(historical_data) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 3 historical data points required for trend analysis"
        )
    
    try:
        # Convert to format expected by service
        trend_data = []
        for point in historical_data:
            data_dict = point.threat_data.dict()
            data_dict['risk_score'] = point.risk_score
            data_dict['timestamp'] = point.timestamp
            trend_data.append(data_dict)
        
        result = service.analyze_trends(trend_data)
        return TrendAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"Error analyzing trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Trend analysis failed"
        )

@router.get("/model-status")
def get_model_status(
    service: RiskPredictionService = Depends(get_prediction_service)
):
    """Get current status and performance metrics of prediction models."""
    try:
        status = service.get_model_status()
        return status
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model status"
        )

# Legacy endpoint for backward compatibility
@router.post("/predict-risk")
def predict_risk_legacy(
    historical_data: list,
    service: RiskPredictionService = Depends(get_prediction_service)
):
    """Legacy endpoint: Predict future risk based on historical data."""
    try:
        # Convert legacy format to new format
        if not historical_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Historical data required"
            )
        
        # Assume legacy format is list of tuples (index, risk_score)
        converted_data = []
        for i, item in enumerate(historical_data):
            if isinstance(item, (tuple, list)) and len(item) >= 2:
                converted_data.append({
                    'risk_score': float(item[1]),
                    'unique_attack_paths': i,  # Use index as proxy
                    'timestamp': f"2025-01-{min(31, i+1):02d}T12:00:00Z"
                })
        
        if converted_data:
            service.train(converted_data)
            
            # Get current prediction based on last data point
            last_data = converted_data[-1]
            current_prediction = service.predict_risk_score(last_data)
            trend = service.analyze_trends(converted_data)
            
            # Generate simple future predictions
            future_predictions = []
            for i in range(30):  # 30 days
                base_score = current_prediction['risk_score']
                noise = np.random.normal(0, 0.1)  # Add some randomness
                pred = max(0.0, min(1.0, base_score + noise))
                future_predictions.append(pred)
            
            return {
                "predictions": future_predictions,
                "trend": trend,
                "current_risk": current_prediction
            }
        
        return {"predictions": [0.5] * 30, "trend": {"trend": "stable", "confidence": 0.0}}
        
    except Exception as e:
        logger.error(f"Error in legacy risk prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Risk prediction failed"
        )

