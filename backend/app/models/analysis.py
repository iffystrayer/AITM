"""
Analysis models
"""

from app.core.database import AnalysisState, AnalysisResults

# Alias for backward compatibility
Analysis = AnalysisResults

__all__ = ["Analysis", "AnalysisState", "AnalysisResults"]
