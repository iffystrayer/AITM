"""
Advanced Analytics Service for AITM

Provides comprehensive analytics, reporting, and insights for threat modeling data.
Includes trend analysis, risk correlations, and predictive analytics.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_, or_
import pandas as pd
import numpy as np
from collections import defaultdict
import logging

from app.core.database import (
    Project, SystemInput, AttackPath, Recommendation, 
    AnalysisResults, AnalysisState, MitreAttack
)
from app.services.prediction_service import RiskPredictionService

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Comprehensive analytics service for threat modeling data"""
    
    def __init__(self, prediction_service: RiskPredictionService):
        self.prediction_service = prediction_service
    
    async def get_dashboard_metrics(self, db: AsyncSession, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics for executive summary"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Basic project metrics
            project_metrics = await self._get_project_metrics(db, cutoff_date)
            
            # Risk analysis metrics  
            risk_metrics = await self._get_risk_metrics(db, cutoff_date)
            
            # Threat landscape metrics
            threat_metrics = await self._get_threat_landscape_metrics(db, cutoff_date)
            
            # Performance metrics
            performance_metrics = await self._get_performance_metrics(db, cutoff_date)
            
            # Trend analysis
            trend_metrics = await self._get_trend_analysis(db, days)
            
            return {
                'period': f'Last {days} days',
                'generated_at': datetime.utcnow().isoformat(),
                'project_metrics': project_metrics,
                'risk_metrics': risk_metrics,
                'threat_metrics': threat_metrics,
                'performance_metrics': performance_metrics,
                'trends': trend_metrics,
                'summary': await self._generate_executive_summary(
                    project_metrics, risk_metrics, threat_metrics
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating dashboard metrics: {e}")
            return self._get_default_metrics()
    
    async def _get_project_metrics(self, db: AsyncSession, cutoff_date: datetime) -> Dict[str, Any]:
        """Get project-related metrics"""
        # Total projects
        total_projects = await db.scalar(select(func.count(Project.id)))
        
        # Recent projects
        recent_projects = await db.scalar(
            select(func.count(Project.id)).where(Project.created_at >= cutoff_date)
        )
        
        # Projects by status
        status_query = await db.execute(
            select(Project.status, func.count(Project.id))
            .group_by(Project.status)
        )
        status_distribution = {status: count for status, count in status_query}
        
        # Active projects (analyzed in last 30 days)
        active_projects = await db.scalar(
            select(func.count(Project.id.distinct()))
            .select_from(Project)
            .join(AnalysisState, Project.id == AnalysisState.project_id)
            .where(AnalysisState.updated_at >= cutoff_date)
        )
        
        return {
            'total_projects': total_projects or 0,
            'recent_projects': recent_projects or 0,
            'active_projects': active_projects or 0,
            'status_distribution': status_distribution,
            'completion_rate': (
                status_distribution.get('completed', 0) / max(total_projects, 1) * 100
                if total_projects else 0
            )
        }
    
    async def _get_risk_metrics(self, db: AsyncSession, cutoff_date: datetime) -> Dict[str, Any]:
        """Get risk assessment metrics"""
        # Average risk scores
        avg_risk_score = await db.scalar(
            select(func.avg(AnalysisResults.overall_risk_score))
            .where(AnalysisResults.created_at >= cutoff_date)
        )
        
        # Risk distribution
        risk_ranges = {
            'low': (0.0, 0.3),
            'medium': (0.3, 0.7),
            'high': (0.7, 1.0)
        }
        
        risk_distribution = {}
        for level, (min_val, max_val) in risk_ranges.items():
            count = await db.scalar(
                select(func.count(AnalysisResults.id))
                .where(
                    and_(
                        AnalysisResults.overall_risk_score >= min_val,
                        AnalysisResults.overall_risk_score < max_val,
                        AnalysisResults.created_at >= cutoff_date
                    )
                )
            )
            risk_distribution[level] = count or 0
        
        # High risk projects (>0.7)
        high_risk_projects = await db.scalar(
            select(func.count(AnalysisResults.id))
            .where(
                and_(
                    AnalysisResults.overall_risk_score >= 0.7,
                    AnalysisResults.created_at >= cutoff_date
                )
            )
        )
        
        # Confidence metrics
        avg_confidence = await db.scalar(
            select(func.avg(AnalysisResults.confidence_score))
            .where(AnalysisResults.created_at >= cutoff_date)
        )
        
        return {
            'average_risk_score': round(avg_risk_score or 0.5, 3),
            'average_confidence': round(avg_confidence or 0.8, 3),
            'risk_distribution': risk_distribution,
            'high_risk_projects': high_risk_projects or 0,
            'risk_trend': await self._calculate_risk_trend(db, cutoff_date)
        }
    
    async def _get_threat_landscape_metrics(self, db: AsyncSession, cutoff_date: datetime) -> Dict[str, Any]:
        """Get threat landscape and MITRE ATT&CK metrics"""
        # Total attack paths identified
        total_attack_paths = await db.scalar(
            select(func.count(AttackPath.id))
            .where(AttackPath.created_at >= cutoff_date)
        )
        
        # High priority attack paths
        high_priority_paths = await db.scalar(
            select(func.count(AttackPath.id))
            .where(
                and_(
                    AttackPath.priority_score >= 0.7,
                    AttackPath.created_at >= cutoff_date
                )
            )
        )
        
        # Most common attack techniques
        technique_query = await db.execute(
            select(AttackPath.techniques, func.count(AttackPath.id))
            .where(AttackPath.created_at >= cutoff_date)
            .group_by(AttackPath.techniques)
            .order_by(func.count(AttackPath.id).desc())
            .limit(10)
        )
        
        common_techniques = [
            {'technique': tech, 'count': count} 
            for tech, count in technique_query
        ]
        
        # Recommendations generated
        total_recommendations = await db.scalar(
            select(func.count(Recommendation.id))
            .where(Recommendation.created_at >= cutoff_date)
        )
        
        # Critical recommendations
        critical_recommendations = await db.scalar(
            select(func.count(Recommendation.id))
            .where(
                and_(
                    Recommendation.priority == 'high',
                    Recommendation.created_at >= cutoff_date
                )
            )
        )
        
        return {
            'total_attack_paths': total_attack_paths or 0,
            'high_priority_paths': high_priority_paths or 0,
            'total_recommendations': total_recommendations or 0,
            'critical_recommendations': critical_recommendations or 0,
            'common_techniques': common_techniques,
            'threat_coverage': await self._calculate_threat_coverage(db)
        }
    
    async def _get_performance_metrics(self, db: AsyncSession, cutoff_date: datetime) -> Dict[str, Any]:
        """Get system performance and efficiency metrics"""
        # Analysis completion times
        completion_times = await db.execute(
            select(
                AnalysisState.started_at,
                AnalysisState.completed_at
            )
            .where(
                and_(
                    AnalysisState.status == 'completed',
                    AnalysisState.completed_at >= cutoff_date,
                    AnalysisState.started_at.is_not(None),
                    AnalysisState.completed_at.is_not(None)
                )
            )
        )
        
        durations = []
        for start_time, end_time in completion_times:
            if start_time and end_time:
                duration = (end_time - start_time).total_seconds() / 60  # minutes
                durations.append(duration)
        
        avg_analysis_time = np.mean(durations) if durations else 0
        
        # Success rate
        total_analyses = await db.scalar(
            select(func.count(AnalysisState.id))
            .where(AnalysisState.started_at >= cutoff_date)
        )
        
        successful_analyses = await db.scalar(
            select(func.count(AnalysisState.id))
            .where(
                and_(
                    AnalysisState.status == 'completed',
                    AnalysisState.started_at >= cutoff_date
                )
            )
        )
        
        success_rate = (
            successful_analyses / max(total_analyses, 1) * 100
            if total_analyses else 0
        )
        
        return {
            'average_analysis_time_minutes': round(avg_analysis_time, 2),
            'success_rate': round(success_rate, 1),
            'total_analyses': total_analyses or 0,
            'successful_analyses': successful_analyses or 0,
            'system_efficiency': await self._calculate_efficiency_score(
                success_rate, avg_analysis_time
            )
        }
    
    async def _get_trend_analysis(self, db: AsyncSession, days: int) -> Dict[str, Any]:
        """Get trend analysis for the specified period"""
        # Daily project creation trend
        daily_projects = await db.execute(
            select(
                func.date(Project.created_at).label('date'),
                func.count(Project.id).label('count')
            )
            .where(Project.created_at >= datetime.utcnow() - timedelta(days=days))
            .group_by(func.date(Project.created_at))
            .order_by(func.date(Project.created_at))
        )
        
        project_trend = [
            {'date': str(date), 'count': count}
            for date, count in daily_projects
        ]
        
        # Risk score trend
        risk_trend = await db.execute(
            select(
                func.date(AnalysisResults.created_at).label('date'),
                func.avg(AnalysisResults.overall_risk_score).label('avg_risk')
            )
            .where(AnalysisResults.created_at >= datetime.utcnow() - timedelta(days=days))
            .group_by(func.date(AnalysisResults.created_at))
            .order_by(func.date(AnalysisResults.created_at))
        )
        
        risk_score_trend = [
            {'date': str(date), 'avg_risk': round(float(avg_risk), 3)}
            for date, avg_risk in risk_trend if avg_risk
        ]
        
        return {
            'project_creation_trend': project_trend,
            'risk_score_trend': risk_score_trend,
            'trend_analysis': await self._analyze_trends(project_trend, risk_score_trend)
        }
    
    async def get_detailed_project_analytics(
        self, 
        db: AsyncSession, 
        project_id: int
    ) -> Dict[str, Any]:
        """Get detailed analytics for a specific project"""
        try:
            # Get project details
            project = await db.scalar(select(Project).where(Project.id == project_id))
            if not project:
                raise ValueError("Project not found")
            
            # Get analysis results
            analysis_results = await db.scalar(
                select(AnalysisResults).where(AnalysisResults.project_id == project_id)
            )
            
            # Get attack paths
            attack_paths = await db.scalars(
                select(AttackPath).where(AttackPath.project_id == project_id)
                .order_by(AttackPath.priority_score.desc())
            )
            
            # Get recommendations
            recommendations = await db.scalars(
                select(Recommendation).where(Recommendation.project_id == project_id)
                .order_by(Recommendation.priority.desc())
            )
            
            # Generate comprehensive project analytics
            return {
                'project_info': {
                    'id': project.id,
                    'name': project.name,
                    'status': project.status,
                    'created_at': project.created_at.isoformat(),
                    'updated_at': project.updated_at.isoformat()
                },
                'risk_assessment': {
                    'overall_risk_score': analysis_results.overall_risk_score if analysis_results else None,
                    'confidence_score': analysis_results.confidence_score if analysis_results else None,
                    'risk_level': self._categorize_risk_level(
                        analysis_results.overall_risk_score if analysis_results else 0.5
                    )
                },
                'attack_paths': [
                    {
                        'id': ap.id,
                        'name': ap.name,
                        'priority_score': ap.priority_score,
                        'explanation': ap.explanation
                    } for ap in attack_paths.all()
                ],
                'recommendations': [
                    {
                        'id': rec.id,
                        'title': rec.title,
                        'priority': rec.priority,
                        'status': rec.status,
                        'description': rec.description
                    } for rec in recommendations.all()
                ],
                'threat_intelligence': await self._get_project_threat_intelligence(
                    db, project_id, analysis_results
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating project analytics for {project_id}: {e}")
            raise
    
    async def generate_executive_report(
        self, 
        db: AsyncSession, 
        report_type: str = "monthly"
    ) -> Dict[str, Any]:
        """Generate comprehensive executive report"""
        
        days_map = {
            'weekly': 7,
            'monthly': 30,
            'quarterly': 90,
            'yearly': 365
        }
        
        days = days_map.get(report_type, 30)
        
        # Get comprehensive metrics
        dashboard_metrics = await self.get_dashboard_metrics(db, days)
        
        # Get industry benchmarking
        industry_comparison = await self._get_industry_benchmarks(dashboard_metrics)
        
        # Get strategic recommendations
        strategic_recommendations = await self._generate_strategic_recommendations(
            db, dashboard_metrics
        )
        
        return {
            'report_type': report_type,
            'reporting_period': f'Last {days} days',
            'generated_at': datetime.utcnow().isoformat(),
            'executive_summary': dashboard_metrics['summary'],
            'key_metrics': dashboard_metrics,
            'strategic_insights': strategic_recommendations,
            'industry_comparison': industry_comparison,
            'action_items': await self._generate_action_items(db, dashboard_metrics),
            'risk_outlook': await self._generate_risk_outlook(db, dashboard_metrics)
        }
    
    # Helper methods
    async def _calculate_risk_trend(self, db: AsyncSession, cutoff_date: datetime) -> str:
        """Calculate risk trend direction"""
        recent_avg = await db.scalar(
            select(func.avg(AnalysisResults.overall_risk_score))
            .where(AnalysisResults.created_at >= cutoff_date)
        )
        
        older_avg = await db.scalar(
            select(func.avg(AnalysisResults.overall_risk_score))
            .where(AnalysisResults.created_at < cutoff_date)
        )
        
        if not recent_avg or not older_avg:
            return "stable"
        
        if recent_avg > older_avg + 0.05:
            return "increasing"
        elif recent_avg < older_avg - 0.05:
            return "decreasing"
        else:
            return "stable"
    
    async def _calculate_threat_coverage(self, db: AsyncSession) -> float:
        """Calculate threat coverage percentage based on MITRE ATT&CK"""
        total_mitre_techniques = await db.scalar(select(func.count(MitreAttack.id)))
        
        # Count unique techniques identified in attack paths
        unique_techniques = await db.execute(
            select(func.count(func.distinct(AttackPath.techniques)))
        )
        
        identified_count = unique_techniques.scalar() or 0
        total_count = total_mitre_techniques or 1
        
        return round(identified_count / total_count * 100, 1)
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize risk score into level"""
        if risk_score < 0.3:
            return "Low"
        elif risk_score < 0.7:
            return "Medium"
        else:
            return "High"
    
    async def _calculate_efficiency_score(self, success_rate: float, avg_time: float) -> float:
        """Calculate system efficiency score"""
        # Normalize success rate (0-100) and average time (penalize longer times)
        success_factor = success_rate / 100
        time_factor = max(0.1, 1 - (avg_time / 60))  # Penalize if over 1 hour
        
        return round((success_factor * 0.7 + time_factor * 0.3) * 100, 1)
    
    async def _generate_executive_summary(
        self, 
        project_metrics: Dict, 
        risk_metrics: Dict, 
        threat_metrics: Dict
    ) -> Dict[str, str]:
        """Generate executive summary insights"""
        
        # Determine overall health
        health_score = (
            min(project_metrics['completion_rate'] / 100, 1.0) * 0.3 +
            (1 - risk_metrics['average_risk_score']) * 0.4 +
            min(threat_metrics['total_recommendations'] / 10, 1.0) * 0.3
        )
        
        if health_score > 0.8:
            overall_status = "Excellent"
            status_color = "green"
        elif health_score > 0.6:
            overall_status = "Good"
            status_color = "blue"
        elif health_score > 0.4:
            overall_status = "Moderate"
            status_color = "yellow"
        else:
            overall_status = "Needs Attention"
            status_color = "red"
        
        return {
            'overall_status': overall_status,
            'status_color': status_color,
            'health_score': round(health_score * 100, 1),
            'key_insight': self._generate_key_insight(project_metrics, risk_metrics, threat_metrics),
            'priority_action': self._generate_priority_action(risk_metrics, threat_metrics)
        }
    
    def _generate_key_insight(self, project_metrics: Dict, risk_metrics: Dict, threat_metrics: Dict) -> str:
        """Generate key insight based on metrics"""
        if risk_metrics['high_risk_projects'] > 5:
            return f"High attention needed: {risk_metrics['high_risk_projects']} projects have high risk scores"
        elif project_metrics['completion_rate'] < 50:
            return "Focus on completing pending threat analysis projects to improve security posture"
        elif threat_metrics['critical_recommendations'] > 10:
            return f"Priority implementation needed: {threat_metrics['critical_recommendations']} critical recommendations pending"
        else:
            return "Security posture is stable with continuous improvement opportunities identified"
    
    def _generate_priority_action(self, risk_metrics: Dict, threat_metrics: Dict) -> str:
        """Generate priority action item"""
        if risk_metrics['high_risk_projects'] > 0:
            return "Immediately review and remediate high-risk projects"
        elif threat_metrics['critical_recommendations'] > 5:
            return "Prioritize implementation of critical security recommendations"
        else:
            return "Continue regular threat modeling activities and maintain current security standards"
    
    def _get_default_metrics(self) -> Dict[str, Any]:
        """Return default metrics when errors occur"""
        return {
            'period': 'Last 30 days',
            'generated_at': datetime.utcnow().isoformat(),
            'project_metrics': {
                'total_projects': 0,
                'recent_projects': 0,
                'active_projects': 0,
                'status_distribution': {},
                'completion_rate': 0
            },
            'risk_metrics': {
                'average_risk_score': 0.5,
                'average_confidence': 0.8,
                'risk_distribution': {'low': 0, 'medium': 0, 'high': 0},
                'high_risk_projects': 0,
                'risk_trend': 'stable'
            },
            'threat_metrics': {
                'total_attack_paths': 0,
                'high_priority_paths': 0,
                'total_recommendations': 0,
                'critical_recommendations': 0,
                'common_techniques': [],
                'threat_coverage': 0
            },
            'performance_metrics': {
                'average_analysis_time_minutes': 0,
                'success_rate': 0,
                'total_analyses': 0,
                'successful_analyses': 0,
                'system_efficiency': 0
            },
            'trends': {
                'project_creation_trend': [],
                'risk_score_trend': [],
                'trend_analysis': {}
            },
            'summary': {
                'overall_status': 'Unknown',
                'status_color': 'gray',
                'health_score': 0,
                'key_insight': 'Insufficient data for analysis',
                'priority_action': 'Perform threat modeling analyses to generate insights'
            }
        }
    
    async def _get_project_threat_intelligence(
        self, 
        db: AsyncSession, 
        project_id: int, 
        analysis_results
    ) -> Dict[str, Any]:
        """Get threat intelligence data for a project"""
        try:
            # Get MITRE techniques associated with this project
            mitre_techniques = await db.execute(
                select(MitreAttack)
                .join(AttackPath, AttackPath.techniques.contains(MitreAttack.technique_id))
                .where(AttackPath.project_id == project_id)
                .limit(10)
            )
            
            techniques = [{
                'technique_id': tech.technique_id,
                'name': tech.name,
                'tactic': tech.tactic,
                'description': tech.description[:200] + '...' if tech.description else ''
            } for tech in mitre_techniques.scalars().all()]
            
            # Calculate threat landscape score
            threat_score = analysis_results.overall_risk_score if analysis_results else 0.5
            
            return {
                'mitre_techniques': techniques,
                'threat_landscape_score': threat_score,
                'threat_categories': await self._categorize_threats(techniques),
                'intelligence_sources': ['MITRE ATT&CK', 'Internal Analysis']
            }
            
        except Exception as e:
            logger.error(f"Error getting threat intelligence for project {project_id}: {e}")
            return {
                'mitre_techniques': [],
                'threat_landscape_score': 0.5,
                'threat_categories': {},
                'intelligence_sources': []
            }
    
    async def _categorize_threats(self, techniques: List[Dict]) -> Dict[str, int]:
        """Categorize threats by tactic"""
        categories = {}
        for technique in techniques:
            tactic = technique.get('tactic', 'unknown')
            categories[tactic] = categories.get(tactic, 0) + 1
        return categories
    
    # Additional advanced analytics methods would go here...
    async def _get_industry_benchmarks(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate industry benchmarking data"""
        # This would typically connect to external benchmarking data
        return {
            'industry_average_risk': 0.45,
            'industry_completion_rate': 65,
            'peer_comparison': 'Above Average',
            'benchmark_date': datetime.utcnow().isoformat()
        }
    
    async def _generate_strategic_recommendations(self, db: AsyncSession, metrics: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate strategic recommendations based on analytics"""
        recommendations = []
        
        risk_score = metrics['risk_metrics']['average_risk_score']
        completion_rate = metrics['project_metrics']['completion_rate']
        
        if risk_score > 0.7:
            recommendations.append({
                'priority': 'High',
                'category': 'Risk Management',
                'recommendation': 'Implement immediate risk reduction measures across high-risk projects',
                'impact': 'Critical security posture improvement'
            })
        
        if completion_rate < 50:
            recommendations.append({
                'priority': 'Medium',
                'category': 'Process Improvement',
                'recommendation': 'Streamline threat modeling workflow to improve completion rates',
                'impact': 'Enhanced operational efficiency'
            })
        
        return recommendations
    
    async def _generate_action_items(self, db: AsyncSession, metrics: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable items for leadership"""
        items = []
        
        high_risk_count = metrics['risk_metrics']['high_risk_projects']
        if high_risk_count > 0:
            items.append({
                'action': f'Review {high_risk_count} high-risk projects',
                'owner': 'Security Team',
                'timeline': 'Within 7 days',
                'priority': 'High'
            })
        
        return items
    
    async def _generate_risk_outlook(self, db: AsyncSession, metrics: Dict[str, Any]) -> Dict[str, str]:
        """Generate risk outlook and predictions"""
        trend = metrics['risk_metrics']['risk_trend']
        
        if trend == 'increasing':
            outlook = 'Risk levels are trending upward, requiring immediate attention'
        elif trend == 'decreasing':
            outlook = 'Risk levels are improving, continue current security measures'
        else:
            outlook = 'Risk levels are stable, maintain vigilant monitoring'
        
        return {
            'short_term': outlook,
            'long_term': 'Continued threat modeling will improve overall security posture',
            'confidence': 'High'
        }
    
    async def _analyze_trends(self, project_trend: List, risk_trend: List) -> Dict[str, str]:
        """Analyze trends and provide insights"""
        return {
            'project_activity': 'Stable' if len(project_trend) > 0 else 'Low',
            'risk_direction': 'Monitored' if len(risk_trend) > 0 else 'Insufficient Data',
            'recommendation': 'Continue regular monitoring and analysis'
        }
