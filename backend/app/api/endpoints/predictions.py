from fastapi import APIRouter, Depends
from app.services.prediction_service import RiskPredictionService
from app.core.dependencies import get_prediction_service

router = APIRouter()

@router.post("/predict-risk")
def predict_risk(historical_data: list[tuple[int, float]], service: RiskPredictionService = Depends(get_prediction_service)):
    """Predict future risk based on historical data."""
    service.train(historical_data)
    predictions = service.predict_future_risk()
    trend = service.analyze_trends(historical_data)
    return {"predictions": predictions, "trend": trend}

