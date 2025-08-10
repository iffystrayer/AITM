from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class RiskPredictionService:
    def __init__(self):
        # Use ensemble of models for better predictions
        self.linear_model = LinearRegression()
        self.rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        
        # Model performance metrics
        self.model_metrics = {
            'linear': {'mse': None, 'r2': None, 'trained': False},
            'rf': {'mse': None, 'r2': None, 'trained': False}
        }
        
        # Feature importance tracking
        self.feature_weights = {
            'temporal': 0.3,
            'attack_complexity': 0.25,
            'system_exposure': 0.25,
            'mitre_coverage': 0.2
        }

    def extract_features(self, threat_data: Dict) -> np.array:
        """Extract meaningful features from threat analysis data."""
        features = []
        
        # Temporal features (time-based patterns)
        features.append(threat_data.get('days_since_last_analysis', 0))
        features.append(threat_data.get('analysis_frequency', 1))
        
        # Attack complexity features
        features.append(threat_data.get('unique_attack_paths', 0))
        features.append(threat_data.get('avg_attack_complexity', 0.5))
        features.append(threat_data.get('critical_vulnerabilities', 0))
        
        # System exposure features
        features.append(threat_data.get('public_endpoints', 0))
        features.append(threat_data.get('trust_boundaries', 1))
        features.append(threat_data.get('data_sensitivity_score', 0.5))
        
        # MITRE ATT&CK coverage
        features.append(threat_data.get('mitre_technique_count', 0))
        features.append(threat_data.get('mitre_tactic_coverage', 0))
        features.append(threat_data.get('high_impact_techniques', 0))
        
        return np.array(features).reshape(1, -1)

    def train(self, historical_data: List[Dict]):
        """Train the risk prediction models with enhanced features."""
        if not historical_data or len(historical_data) < 3:
            logger.warning("Insufficient historical data for training")
            return

        try:
            # Extract features and targets
            X_features = []
            y_scores = []
            
            for data_point in historical_data:
                features = self.extract_features(data_point).flatten()
                X_features.append(features)
                y_scores.append(data_point.get('risk_score', 0.5))
            
            X = np.array(X_features)
            y = np.array(y_scores)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Split into train/test for validation
            split_idx = int(0.8 * len(X))
            X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Train linear model
            self.linear_model.fit(X_train, y_train)
            if len(X_test) > 0:
                linear_pred = self.linear_model.predict(X_test)
                self.model_metrics['linear']['mse'] = mean_squared_error(y_test, linear_pred)
                self.model_metrics['linear']['r2'] = r2_score(y_test, linear_pred)
            self.model_metrics['linear']['trained'] = True
            
            # Train random forest model
            self.rf_model.fit(X_train, y_train)
            if len(X_test) > 0:
                rf_pred = self.rf_model.predict(X_test)
                self.model_metrics['rf']['mse'] = mean_squared_error(y_test, rf_pred)
                self.model_metrics['rf']['r2'] = r2_score(y_test, rf_pred)
            self.model_metrics['rf']['trained'] = True
            
            logger.info(f"Models trained successfully with {len(historical_data)} data points")
            logger.info(f"Linear model R²: {self.model_metrics['linear']['r2']:.3f}")
            logger.info(f"Random Forest R²: {self.model_metrics['rf']['r2']:.3f}")
            
        except Exception as e:
            logger.error(f"Error training prediction models: {e}")
            raise

    def predict_risk_score(self, threat_data: Dict) -> Dict:
        """Predict risk score for given threat data using ensemble approach."""
        try:
            # Extract features
            features = self.extract_features(threat_data)
            
            if not self.model_metrics['linear']['trained'] and not self.model_metrics['rf']['trained']:
                # Use rule-based fallback if no models are trained
                return self._rule_based_prediction(threat_data)
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            predictions = []
            weights = []
            
            # Linear model prediction
            if self.model_metrics['linear']['trained']:
                linear_pred = self.linear_model.predict(features_scaled)[0]
                linear_weight = max(0.1, self.model_metrics['linear'].get('r2', 0.5))
                predictions.append(linear_pred)
                weights.append(linear_weight)
            
            # Random Forest prediction
            if self.model_metrics['rf']['trained']:
                rf_pred = self.rf_model.predict(features_scaled)[0]
                rf_weight = max(0.1, self.model_metrics['rf'].get('r2', 0.5))
                predictions.append(rf_pred)
                weights.append(rf_weight)
            
            # Ensemble prediction (weighted average)
            if predictions:
                ensemble_pred = np.average(predictions, weights=weights)
                confidence = np.mean(weights) if weights else 0.5
            else:
                ensemble_pred = 0.5
                confidence = 0.3
            
            # Ensure prediction is within valid range [0, 1]
            ensemble_pred = max(0.0, min(1.0, ensemble_pred))
            
            return {
                'risk_score': float(ensemble_pred),
                'confidence': float(confidence),
                'model_predictions': {
                    'linear': predictions[0] if len(predictions) > 0 and self.model_metrics['linear']['trained'] else None,
                    'random_forest': predictions[-1] if len(predictions) > 0 and self.model_metrics['rf']['trained'] else None
                },
                'feature_contributions': self._analyze_feature_importance(features.flatten())
            }
            
        except Exception as e:
            logger.error(f"Error in risk prediction: {e}")
            return self._rule_based_prediction(threat_data)

    def _rule_based_prediction(self, threat_data: Dict) -> Dict:
        """Fallback rule-based risk prediction when ML models aren't available."""
        base_score = 0.5
        adjustments = []
        
        # Attack complexity adjustments
        attack_paths = threat_data.get('unique_attack_paths', 0)
        if attack_paths > 10:
            base_score += 0.2
            adjustments.append(f"High attack path count (+0.2)")
        elif attack_paths > 5:
            base_score += 0.1
            adjustments.append(f"Moderate attack path count (+0.1)")
        
        # Critical vulnerabilities
        critical_vulns = threat_data.get('critical_vulnerabilities', 0)
        if critical_vulns > 0:
            base_score += min(0.3, critical_vulns * 0.1)
            adjustments.append(f"Critical vulnerabilities (+{min(0.3, critical_vulns * 0.1):.1f})")
        
        # Public exposure
        public_endpoints = threat_data.get('public_endpoints', 0)
        if public_endpoints > 0:
            base_score += min(0.2, public_endpoints * 0.05)
            adjustments.append(f"Public endpoints (+{min(0.2, public_endpoints * 0.05):.1f})")
        
        # MITRE coverage (high coverage = higher risk)
        mitre_count = threat_data.get('mitre_technique_count', 0)
        if mitre_count > 20:
            base_score += 0.15
            adjustments.append(f"High MITRE technique count (+0.15)")
        elif mitre_count > 10:
            base_score += 0.1
            adjustments.append(f"Moderate MITRE technique count (+0.1)")
        
        # Ensure within bounds
        final_score = max(0.0, min(1.0, base_score))
        
        return {
            'risk_score': float(final_score),
            'confidence': 0.6,  # Lower confidence for rule-based
            'model_predictions': {'rule_based': final_score},
            'rule_adjustments': adjustments
        }

    def _analyze_feature_importance(self, features: np.array) -> Dict:
        """Analyze which features contribute most to the risk score."""
        feature_names = [
            'days_since_last_analysis', 'analysis_frequency', 'unique_attack_paths',
            'avg_attack_complexity', 'critical_vulnerabilities', 'public_endpoints',
            'trust_boundaries', 'data_sensitivity_score', 'mitre_technique_count',
            'mitre_tactic_coverage', 'high_impact_techniques'
        ]
        
        contributions = {}
        
        # Use Random Forest feature importance if available
        if (self.model_metrics['rf']['trained'] and 
            hasattr(self.rf_model, 'feature_importances_') and 
            len(self.rf_model.feature_importances_) == len(features)):
            
            for i, (name, importance) in enumerate(zip(feature_names, self.rf_model.feature_importances_)):
                contributions[name] = {
                    'value': float(features[i]),
                    'importance': float(importance),
                    'contribution': float(features[i] * importance)
                }
        else:
            # Use simple weighted contributions
            weights = [0.1, 0.05, 0.2, 0.15, 0.25, 0.1, 0.05, 0.1, 0.15, 0.1, 0.2]
            for i, (name, weight) in enumerate(zip(feature_names, weights)):
                if i < len(features):
                    contributions[name] = {
                        'value': float(features[i]),
                        'importance': weight,
                        'contribution': float(features[i] * weight)
                    }
        
        return contributions

    def predict_future_risk(self, current_data: Dict, days_ahead: int = 30) -> Dict:
        """Predict future risk progression based on current threat landscape."""
        try:
            current_risk = self.predict_risk_score(current_data)
            base_score = current_risk['risk_score']
            
            # Simulate different scenarios
            scenarios = {
                'optimistic': {'factor': 0.9, 'description': 'Improved security posture'},
                'realistic': {'factor': 1.0, 'description': 'Current trajectory maintained'},
                'pessimistic': {'factor': 1.1, 'description': 'Degrading security conditions'}
            }
            
            predictions = {}
            
            for scenario_name, scenario_data in scenarios.items():
                # Simple time-decay model for demonstration
                time_factor = 1 + (days_ahead / 365) * 0.1  # Risk generally increases over time
                predicted_score = min(1.0, base_score * scenario_data['factor'] * time_factor)
                
                predictions[scenario_name] = {
                    'risk_score': float(predicted_score),
                    'description': scenario_data['description'],
                    'confidence': max(0.3, current_risk['confidence'] * 0.8)  # Lower confidence for future
                }
            
            return {
                'current_risk': current_risk['risk_score'],
                'days_ahead': days_ahead,
                'scenarios': predictions,
                'recommendations': self._generate_risk_recommendations(current_data, predictions)
            }
            
        except Exception as e:
            logger.error(f"Error predicting future risk: {e}")
            return {'error': 'Prediction unavailable', 'current_risk': 0.5}

    def _generate_risk_recommendations(self, current_data: Dict, predictions: Dict) -> List[str]:
        """Generate actionable recommendations based on risk predictions."""
        recommendations = []
        
        pessimistic_score = predictions.get('pessimistic', {}).get('risk_score', 0.5)
        
        if pessimistic_score > 0.8:
            recommendations.append("Critical: Immediate security assessment required")
            recommendations.append("Implement emergency incident response procedures")
        
        if current_data.get('critical_vulnerabilities', 0) > 0:
            recommendations.append("Prioritize patching critical vulnerabilities")
        
        if current_data.get('public_endpoints', 0) > 5:
            recommendations.append("Review and minimize public attack surface")
        
        if current_data.get('mitre_technique_count', 0) > 15:
            recommendations.append("Implement additional security controls for high-risk attack techniques")
        
        if not recommendations:
            recommendations.append("Continue monitoring and regular security assessments")
        
        return recommendations

    def analyze_trends(self, historical_data: List[Dict]) -> Dict:
        """Enhanced trend analysis with multiple metrics."""
        if not historical_data or len(historical_data) < 3:
            return {'trend': 'insufficient_data', 'confidence': 0.0}
        
        # Extract risk scores over time
        risk_scores = [data.get('risk_score', 0.5) for data in historical_data]
        time_points = list(range(len(risk_scores)))
        
        # Calculate trend statistics
        slope = np.polyfit(time_points, risk_scores, 1)[0]
        correlation = np.corrcoef(time_points, risk_scores)[0, 1] if len(risk_scores) > 1 else 0
        
        # Recent vs historical average
        recent_avg = np.mean(risk_scores[-3:]) if len(risk_scores) >= 3 else risk_scores[-1]
        historical_avg = np.mean(risk_scores[:-3]) if len(risk_scores) > 3 else recent_avg
        
        # Volatility (standard deviation)
        volatility = np.std(risk_scores) if len(risk_scores) > 1 else 0
        
        # Determine trend category
        if abs(slope) < 0.01:
            trend = 'stable'
        elif slope > 0.05:
            trend = 'increasing'
        elif slope < -0.05:
            trend = 'decreasing'
        else:
            trend = 'slightly_' + ('increasing' if slope > 0 else 'decreasing')
        
        return {
            'trend': trend,
            'slope': float(slope),
            'correlation': float(correlation),
            'recent_avg': float(recent_avg),
            'historical_avg': float(historical_avg),
            'volatility': float(volatility),
            'confidence': min(1.0, abs(correlation) * (len(historical_data) / 10)),
            'data_points': len(historical_data)
        }

    def get_model_status(self) -> Dict:
        """Get current status and performance of prediction models."""
        return {
            'models': self.model_metrics,
            'feature_weights': self.feature_weights,
            'ready_for_prediction': any(m['trained'] for m in self.model_metrics.values())
        }
