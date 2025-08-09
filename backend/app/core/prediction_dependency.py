from app.services.prediction_service import RiskPredictionService

def get_prediction_service() -> RiskPredictionService:
    return RiskPredictionService()
