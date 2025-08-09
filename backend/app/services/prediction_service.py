from sklearn.linear_model import LinearRegression
import numpy as np

class RiskPredictionService:
    def __init__(self):
        self.model = LinearRegression()

    def train(self, historical_data):
        """Train the risk prediction model."""
        if not historical_data or len(historical_data) < 2:
            return

        X = np.array([i for i, _ in enumerate(historical_data)]).reshape(-1, 1)
        y = np.array([score for _, score in historical_data])
        
        self.model.fit(X, y)

    def predict_future_risk(self, days_ahead=30):
        """Predict future risk scores."""
        last_day = self.model.coef_.size if hasattr(self.model, 'coef_') else 0
        future_days = np.array([i for i in range(last_day, last_day + days_ahead)]).reshape(-1, 1)
        
        if not hasattr(self.model, 'coef_'):
            return [0.5] * days_ahead # Default prediction

        return self.model.predict(future_days).tolist()

    def analyze_trends(self, historical_data):
        """Analyze trends in the historical data."""
        if not hasattr(self.model, 'coef_') or not self.model.coef_:
            return {'trend': 'neutral', 'slope': 0}

        slope = self.model.coef_[0]
        
        if slope > 0.05:
            trend = 'increasing'
        elif slope < -0.05:
            trend = 'decreasing'
        else:
            trend = 'stable'

        return {'trend': trend, 'slope': slope}
