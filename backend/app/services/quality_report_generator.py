"""
Quality Reporting and Analytics System

This module implements comprehensive quality report generation with multiple formats,
executive-level quality summaries, trend analysis, and comparative analysis across
projects and teams for the AITM platform.
"""

import asyncio
import sqlite3
import json
import csv
import io
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from statistics import mean, median, stdev
from enum import Enum
import base64

from app.models.quality import (
    QualityMetrics, QualityIssue, QualityTrend, AutoFixResult,
    IssueType, Severity, IssueStatus, TestQualityMetrics
)
from app.services.quality_metrics_collector import QualityMetricsCollector


class ReportFormat(str, Enum):
    """Supported report formats."""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    EXCEL = "excel"


class ReportType(str, Enum):
    """Types of quality reports."""
    COMPREHENSIVE = "comprehensive"
    EXECUTIVE_SUMMARY = "executive_summary"
    TREND_ANALYSIS = "trend_analysis"
    COMPARATIVE = "comparative"
    ISSUE_SUMMARY = "issue_summary"
    TEAM_PERFORMANCE = "team_performance"
    PROJECT_HEALTH = "project_health"
    TECHNICAL_DEBT = "technical_debt"


@dataclass
class ReportConfiguration:
    """Configuration for report generation."""
    report_type: ReportType
    format: ReportFormat
    project_ids: List[str]
    team_ids: Optional[List[str]] = None
    date_range: Optional[Tuple[datetime, datetime]] = None
    include_trends: bool = True
    include_comparisons: bool = True
    include_recommendations: bool = True
    executive_level: bool = False
    custom_metrics: Optional[List[str]] = None


@dataclass
class QualityReportData:
    """Container for quality report data."""
    project_id: str
    project_name: str
    report_date: datetime
    metrics: QualityMetrics
    issues: List[QualityIssue]
    trends: List[QualityTrend]
    auto_fixes: List[AutoFixResult]
    test_metrics: Optional[TestQualityMetrics] = None


@dataclass
class ExecutiveSummary:
    """Executive-level quality summary."""
    overall_health_score: float
    quality_grade: str  # A, B, C, D, F
    key_metrics: Dict[str, float]
    critical_issues: int
    improvement_trend: str  # "improving", "stable", "declining"
    recommendations: List[str]
    risk_assessment: str  # "low", "medium", "high", "critical"
    investment_priority: str  # "low", "medium", "high"


@dataclass
class ComparativeAnalysis:
    """Comparative analysis between projects/teams."""
    baseline_project: str
    comparison_projects: List[str]
    metric_comparisons: Dict[str, Dict[str, float]]
    performance_rankings: Dict[str, List[str]]
    best_practices: List[str]
    improvement_opportunities: List[str]


@dataclass
class TrendAnalysis:
    """Trend analysis for quality metrics."""
    metric_name: str
    trend_direction: str
    change_rate: float
    prediction: Optional[float]
    confidence_level: float
    seasonal_patterns: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]


class QualityReportGenerator:
    """
    Comprehensive quality reporting and analytics system.
    
    Handles:
    - Multi-format report generation
    - Executive-level summaries
    - Trend analysis and predictions
    - Comparative analysis across projects and teams
    - Custom report configurations
    """
    
    def __init__(self, db_path: str = "aitm.db"):
        self.db_path = db_path
        self.metrics_collector = QualityMetricsCollector(db_path)
        self._ensure_database_schema()
    
    def _ensure_database_schema(self):
        """Ensure required database tables exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Ensure quality_reports table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_reports (
                    id TEXT PRIMARY KEY,
                    report_type TEXT NOT NULL,
                    format TEXT NOT NULL,
                    project_ids TEXT NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    generated_by TEXT,
                    report_data TEXT NOT NULL,
                    file_path TEXT,
                    file_size INTEGER,
                    expires_at TIMESTAMP
                )
            """)
            
            # Ensure report_templates table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS report_templates (
                    id TEXT PRIMARY KEY,
                    template_name TEXT NOT NULL,
                    template_type TEXT NOT NULL,
                    template_content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    async def generate_comprehensive_report(self, config: ReportConfiguration) -> Dict[str, Any]:
        """
        Generate a comprehensive quality report.
        
        Args:
            config: Report configuration specifying type, format, and options
            
        Returns:
            Dictionary containing report data and metadata
        """
        try:
            # Collect data for all specified projects
            report_data = []
            for project_id in config.project_ids:
                data = await self._collect_project_data(project_id, config.date_range)
                if data:
                    report_data.append(data)
            
            if not report_data:
                raise ValueError("No data available for specified projects")
            
            # Generate report based on type
            if config.report_type == ReportType.EXECUTIVE_SUMMARY:
                report_content = await self._generate_executive_summary(report_data, config)
            elif config.report_type == ReportType.TREND_ANALYSIS:
                report_content = await self._generate_trend_analysis(report_data, config)
            elif config.report_type == ReportType.COMPARATIVE:
                report_content = await self._generate_comparative_analysis(report_data, config)
            elif config.report_type == ReportType.ISSUE_SUMMARY:
                report_content = await self._generate_issue_summary(report_data, config)
            elif config.report_type == ReportType.TEAM_PERFORMANCE:
                report_content = await self._generate_team_performance(report_data, config)
            elif config.report_type == ReportType.PROJECT_HEALTH:
                report_content = await self._generate_project_health(report_data, config)
            elif config.report_type == ReportType.TECHNICAL_DEBT:
                report_content = await self._generate_technical_debt_report(report_data, config)
            else:  # COMPREHENSIVE
                report_content = await self._generate_comprehensive_content(report_data, config)
            
            # Format the report
            formatted_report = await self._format_report(report_content, config.format)
            
            # Store report in database
            report_id = await self._store_report(config, formatted_report)
            
            return {
                'report_id': report_id,
                'report_type': config.report_type.value,
                'format': config.format.value,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'project_count': len(config.project_ids),
                'content': formatted_report,
                'metadata': {
                    'projects': config.project_ids,
                    'date_range': config.date_range,
                    'includes_trends': config.include_trends,
                    'includes_comparisons': config.include_comparisons,
                    'executive_level': config.executive_level
                }
            }
            
        except Exception as e:
            print(f"Error generating comprehensive report: {e}")
            raise
    
    async def _collect_project_data(self, project_id: str, 
                                  date_range: Optional[Tuple[datetime, datetime]]) -> Optional[QualityReportData]:
        """Collect all relevant data for a project."""
        try:
            # Get latest metrics
            metrics = await self._get_latest_metrics(project_id)
            if not metrics:
                return None
            
            # Get issues
            issues = await self._get_project_issues(project_id, date_range)
            
            # Get trends
            trends = await self._get_project_trends(project_id, date_range)
            
            # Get auto-fix results
            auto_fixes = await self._get_auto_fix_results(project_id, date_range)
            
            # Get test metrics
            test_metrics = await self._get_test_metrics(project_id)
            
            return QualityReportData(
                project_id=project_id,
                project_name=await self._get_project_name(project_id),
                report_date=datetime.now(timezone.utc),
                metrics=metrics,
                issues=issues,
                trends=trends,
                auto_fixes=auto_fixes,
                test_metrics=test_metrics
            )
            
        except Exception as e:
            print(f"Error collecting data for project {project_id}: {e}")
            return None
    
    async def _generate_executive_summary(self, report_data: List[QualityReportData], 
                                        config: ReportConfiguration) -> Dict[str, Any]:
        """Generate executive-level quality summary."""
        if not report_data:
            return {}
        
        # Calculate overall health score
        health_scores = []
        critical_issues_total = 0
        all_metrics = []
        
        for data in report_data:
            # Calculate project health score
            project_health = self._calculate_project_health_score(data.metrics)
            health_scores.append(project_health)
            
            # Count critical issues
            critical_issues_total += len([
                issue for issue in data.issues 
                if issue.severity == Severity.CRITICAL and issue.status == IssueStatus.OPEN
            ])
            
            all_metrics.append(data.metrics)
        
        overall_health = mean(health_scores) if health_scores else 0
        quality_grade = self._calculate_quality_grade(overall_health)
        
        # Calculate key metrics averages
        key_metrics = self._calculate_key_metrics_summary(all_metrics)
        
        # Determine improvement trend
        improvement_trend = await self._calculate_improvement_trend(report_data)
        
        # Generate recommendations
        recommendations = await self._generate_executive_recommendations(report_data)
        
        # Assess risk
        risk_assessment = self._assess_quality_risk(overall_health, critical_issues_total)
        
        # Determine investment priority
        investment_priority = self._determine_investment_priority(
            overall_health, critical_issues_total, improvement_trend
        )
        
        summary = ExecutiveSummary(
            overall_health_score=overall_health,
            quality_grade=quality_grade,
            key_metrics=key_metrics,
            critical_issues=critical_issues_total,
            improvement_trend=improvement_trend,
            recommendations=recommendations,
            risk_assessment=risk_assessment,
            investment_priority=investment_priority
        )
        
        return {
            'executive_summary': asdict(summary),
            'project_count': len(report_data),
            'report_period': self._get_report_period(config.date_range),
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'detailed_projects': [
                {
                    'project_id': data.project_id,
                    'project_name': data.project_name,
                    'health_score': self._calculate_project_health_score(data.metrics),
                    'critical_issues': len([
                        issue for issue in data.issues 
                        if issue.severity == Severity.CRITICAL
                    ]),
                    'last_updated': data.metrics.timestamp.isoformat()
                }
                for data in report_data
            ]
        }
    
    async def _generate_trend_analysis(self, report_data: List[QualityReportData], 
                                     config: ReportConfiguration) -> Dict[str, Any]:
        """Generate trend analysis report."""
        trend_analyses = {}
        
        # Analyze trends for each metric
        metric_names = [
            'code_coverage', 'cyclomatic_complexity', 'maintainability_index',
            'technical_debt_ratio', 'test_quality_score', 'security_score',
            'performance_score'
        ]
        
        for metric_name in metric_names:
            trend_data = []
            for data in report_data:
                project_trends = [
                    trend for trend in data.trends 
                    if trend.metric_name == metric_name
                ]
                trend_data.extend(project_trends)
            
            if trend_data:
                analysis = await self._analyze_metric_trend(metric_name, trend_data)
                trend_analyses[metric_name] = asdict(analysis)
        
        # Calculate overall trend direction
        overall_trend = self._calculate_overall_trend_direction(trend_analyses)
        
        return {
            'trend_analysis': trend_analyses,
            'overall_trend': overall_trend,
            'analysis_period': self._get_report_period(config.date_range),
            'project_count': len(report_data),
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'insights': await self._generate_trend_insights(trend_analyses),
            'predictions': await self._generate_trend_predictions(trend_analyses)
        }
    
    async def _generate_comparative_analysis(self, report_data: List[QualityReportData], 
                                           config: ReportConfiguration) -> Dict[str, Any]:
        """Generate comparative analysis between projects."""
        if len(report_data) < 2:
            return {'error': 'Comparative analysis requires at least 2 projects'}
        
        # Use first project as baseline
        baseline = report_data[0]
        comparisons = report_data[1:]
        
        # Compare metrics
        metric_comparisons = {}
        performance_rankings = {}
        
        metric_names = [
            'code_coverage', 'cyclomatic_complexity', 'maintainability_index',
            'technical_debt_ratio', 'test_quality_score', 'security_score',
            'performance_score'
        ]
        
        for metric_name in metric_names:
            baseline_value = getattr(baseline.metrics, metric_name, 0) or 0
            comparison_values = {}
            
            for comp_data in comparisons:
                comp_value = getattr(comp_data.metrics, metric_name, 0) or 0
                comparison_values[comp_data.project_id] = {
                    'value': comp_value,
                    'difference': comp_value - baseline_value,
                    'percentage_change': ((comp_value - baseline_value) / baseline_value * 100) 
                                       if baseline_value != 0 else 0
                }
            
            metric_comparisons[metric_name] = {
                'baseline': {'project_id': baseline.project_id, 'value': baseline_value},
                'comparisons': comparison_values
            }
            
            # Rank projects by this metric
            all_values = [(baseline.project_id, baseline_value)]
            all_values.extend([
                (comp_data.project_id, getattr(comp_data.metrics, metric_name, 0) or 0)
                for comp_data in comparisons
            ])
            
            # Sort by value (higher is better for most metrics, except complexity and debt)
            reverse_sort = metric_name not in ['cyclomatic_complexity', 'technical_debt_ratio']
            ranked = sorted(all_values, key=lambda x: x[1], reverse=reverse_sort)
            performance_rankings[metric_name] = [project_id for project_id, _ in ranked]
        
        # Identify best practices and improvement opportunities
        best_practices = self._identify_best_practices(report_data, performance_rankings)
        improvement_opportunities = self._identify_improvement_opportunities(
            report_data, performance_rankings
        )
        
        analysis = ComparativeAnalysis(
            baseline_project=baseline.project_id,
            comparison_projects=[data.project_id for data in comparisons],
            metric_comparisons=metric_comparisons,
            performance_rankings=performance_rankings,
            best_practices=best_practices,
            improvement_opportunities=improvement_opportunities
        )
        
        return {
            'comparative_analysis': asdict(analysis),
            'project_count': len(report_data),
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'top_performer': self._identify_top_performer(report_data),
                'most_improved': await self._identify_most_improved(report_data),
                'needs_attention': self._identify_projects_needing_attention(report_data)
            }
        }
    
    async def _generate_issue_summary(self, report_data: List[QualityReportData], 
                                    config: ReportConfiguration) -> Dict[str, Any]:
        """Generate issue summary report."""
        all_issues = []
        for data in report_data:
            all_issues.extend(data.issues)
        
        # Categorize issues
        issue_summary = {
            'total_issues': len(all_issues),
            'by_severity': {},
            'by_type': {},
            'by_status': {},
            'by_project': {},
            'resolution_stats': {},
            'auto_fixable': 0
        }
        
        # Count by severity
        for severity in Severity:
            count = len([issue for issue in all_issues if issue.severity == severity])
            issue_summary['by_severity'][severity.value] = count
        
        # Count by type
        for issue_type in IssueType:
            count = len([issue for issue in all_issues if issue.issue_type == issue_type])
            issue_summary['by_type'][issue_type.value] = count
        
        # Count by status
        for status in IssueStatus:
            count = len([issue for issue in all_issues if issue.status == status])
            issue_summary['by_status'][status.value] = count
        
        # Count by project
        for data in report_data:
            issue_summary['by_project'][data.project_id] = len(data.issues)
        
        # Auto-fixable issues
        issue_summary['auto_fixable'] = len([
            issue for issue in all_issues if issue.auto_fixable
        ])
        
        # Resolution statistics
        resolved_issues = [issue for issue in all_issues if issue.status == IssueStatus.RESOLVED]
        if resolved_issues:
            resolution_times = []
            for issue in resolved_issues:
                if issue.resolved_at and issue.created_at:
                    resolution_time = (issue.resolved_at - issue.created_at).total_seconds() / 3600  # hours
                    resolution_times.append(resolution_time)
            
            if resolution_times:
                issue_summary['resolution_stats'] = {
                    'average_resolution_time_hours': mean(resolution_times),
                    'median_resolution_time_hours': median(resolution_times),
                    'fastest_resolution_hours': min(resolution_times),
                    'slowest_resolution_hours': max(resolution_times)
                }
        
        # Top issues by frequency
        issue_descriptions = [issue.description for issue in all_issues]
        issue_frequency = {}
        for desc in issue_descriptions:
            issue_frequency[desc] = issue_frequency.get(desc, 0) + 1
        
        top_issues = sorted(issue_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'issue_summary': issue_summary,
            'top_issues': [{'description': desc, 'count': count} for desc, count in top_issues],
            'recommendations': self._generate_issue_recommendations(all_issues),
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'project_count': len(report_data)
        }
    
    async def _generate_team_performance(self, report_data: List[QualityReportData], 
                                       config: ReportConfiguration) -> Dict[str, Any]:
        """Generate team performance report."""
        # This would require team mapping data, which we'll simulate
        team_performance = {}
        
        for data in report_data:
            # Simulate team assignment (in real implementation, this would come from project metadata)
            team_id = f"team_{hash(data.project_id) % 5 + 1}"  # Assign to one of 5 teams
            
            if team_id not in team_performance:
                team_performance[team_id] = {
                    'projects': [],
                    'total_issues': 0,
                    'critical_issues': 0,
                    'avg_health_score': 0,
                    'metrics': []
                }
            
            team_performance[team_id]['projects'].append(data.project_id)
            team_performance[team_id]['total_issues'] += len(data.issues)
            team_performance[team_id]['critical_issues'] += len([
                issue for issue in data.issues if issue.severity == Severity.CRITICAL
            ])
            team_performance[team_id]['metrics'].append(data.metrics)
        
        # Calculate team averages
        for team_id, team_data in team_performance.items():
            if team_data['metrics']:
                health_scores = [
                    self._calculate_project_health_score(metrics) 
                    for metrics in team_data['metrics']
                ]
                team_data['avg_health_score'] = mean(health_scores)
                
                # Calculate average metrics
                team_data['avg_metrics'] = self._calculate_key_metrics_summary(team_data['metrics'])
            
            # Remove raw metrics to clean up response
            del team_data['metrics']
        
        # Rank teams
        team_rankings = sorted(
            team_performance.items(),
            key=lambda x: x[1]['avg_health_score'],
            reverse=True
        )
        
        return {
            'team_performance': team_performance,
            'team_rankings': [{'team_id': team_id, 'score': data['avg_health_score']} 
                            for team_id, data in team_rankings],
            'insights': self._generate_team_insights(team_performance),
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    
    async def _generate_project_health(self, report_data: List[QualityReportData], 
                                     config: ReportConfiguration) -> Dict[str, Any]:
        """Generate project health report."""
        project_health = {}
        
        for data in report_data:
            health_score = self._calculate_project_health_score(data.metrics)
            
            # Categorize health status
            if health_score >= 90:
                health_status = "excellent"
            elif health_score >= 75:
                health_status = "good"
            elif health_score >= 60:
                health_status = "fair"
            elif health_score >= 40:
                health_status = "poor"
            else:
                health_status = "critical"
            
            # Calculate risk factors
            risk_factors = []
            if data.metrics.technical_debt_ratio and data.metrics.technical_debt_ratio > 0.3:
                risk_factors.append("High technical debt")
            if data.metrics.code_coverage and data.metrics.code_coverage < 70:
                risk_factors.append("Low test coverage")
            if data.metrics.security_score and data.metrics.security_score < 80:
                risk_factors.append("Security vulnerabilities")
            
            critical_issues = len([
                issue for issue in data.issues 
                if issue.severity == Severity.CRITICAL and issue.status == IssueStatus.OPEN
            ])
            
            if critical_issues > 0:
                risk_factors.append(f"{critical_issues} critical issues")
            
            project_health[data.project_id] = {
                'project_name': data.project_name,
                'health_score': health_score,
                'health_status': health_status,
                'risk_factors': risk_factors,
                'metrics_summary': {
                    'code_coverage': data.metrics.code_coverage,
                    'maintainability_index': data.metrics.maintainability_index,
                    'technical_debt_ratio': data.metrics.technical_debt_ratio,
                    'security_score': data.metrics.security_score
                },
                'issue_count': len(data.issues),
                'critical_issues': critical_issues,
                'last_updated': data.metrics.timestamp.isoformat()
            }
        
        # Overall portfolio health
        all_scores = [data['health_score'] for data in project_health.values()]
        portfolio_health = mean(all_scores) if all_scores else 0
        
        return {
            'project_health': project_health,
            'portfolio_health': {
                'overall_score': portfolio_health,
                'project_count': len(project_health),
                'healthy_projects': len([
                    data for data in project_health.values() 
                    if data['health_score'] >= 75
                ]),
                'at_risk_projects': len([
                    data for data in project_health.values() 
                    if data['health_score'] < 60
                ])
            },
            'recommendations': self._generate_health_recommendations(project_health),
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    
    async def _generate_technical_debt_report(self, report_data: List[QualityReportData], 
                                            config: ReportConfiguration) -> Dict[str, Any]:
        """Generate technical debt analysis report."""
        debt_analysis = {}
        total_debt_score = 0
        
        for data in report_data:
            debt_ratio = data.metrics.technical_debt_ratio or 0
            
            # Estimate debt in hours (simplified calculation)
            lines_of_code = data.metrics.lines_of_code or 0
            estimated_debt_hours = debt_ratio * lines_of_code * 0.1  # 0.1 hours per line of debt
            
            # Categorize debt level
            if debt_ratio < 0.1:
                debt_level = "low"
            elif debt_ratio < 0.2:
                debt_level = "moderate"
            elif debt_ratio < 0.4:
                debt_level = "high"
            else:
                debt_level = "critical"
            
            # Identify debt sources
            debt_sources = []
            if data.metrics.cyclomatic_complexity and data.metrics.cyclomatic_complexity > 10:
                debt_sources.append("High complexity")
            if data.metrics.code_coverage and data.metrics.code_coverage < 70:
                debt_sources.append("Insufficient testing")
            if data.metrics.duplicate_code_ratio and data.metrics.duplicate_code_ratio > 0.1:
                debt_sources.append("Code duplication")
            if data.metrics.comment_ratio and data.metrics.comment_ratio < 0.1:
                debt_sources.append("Poor documentation")
            
            debt_analysis[data.project_id] = {
                'project_name': data.project_name,
                'debt_ratio': debt_ratio,
                'debt_level': debt_level,
                'estimated_debt_hours': estimated_debt_hours,
                'debt_sources': debt_sources,
                'lines_of_code': lines_of_code,
                'priority_score': debt_ratio * (lines_of_code / 1000)  # Weighted by size
            }
            
            total_debt_score += debt_ratio
        
        # Calculate portfolio debt metrics
        avg_debt_ratio = total_debt_score / len(report_data) if report_data else 0
        total_estimated_hours = sum(
            data['estimated_debt_hours'] for data in debt_analysis.values()
        )
        
        # Prioritize projects for debt reduction
        debt_priority = sorted(
            debt_analysis.items(),
            key=lambda x: x[1]['priority_score'],
            reverse=True
        )
        
        return {
            'technical_debt_analysis': debt_analysis,
            'portfolio_summary': {
                'average_debt_ratio': avg_debt_ratio,
                'total_estimated_hours': total_estimated_hours,
                'projects_with_high_debt': len([
                    data for data in debt_analysis.values() 
                    if data['debt_ratio'] > 0.2
                ]),
                'estimated_cost': total_estimated_hours * 100  # $100/hour estimate
            },
            'debt_reduction_priority': [
                {'project_id': project_id, 'priority_score': data['priority_score']}
                for project_id, data in debt_priority[:10]  # Top 10
            ],
            'recommendations': self._generate_debt_recommendations(debt_analysis),
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    
    async def _generate_comprehensive_content(self, report_data: List[QualityReportData], 
                                            config: ReportConfiguration) -> Dict[str, Any]:
        """Generate comprehensive report content."""
        # Combine all report types
        executive_summary = await self._generate_executive_summary(report_data, config)
        trend_analysis = await self._generate_trend_analysis(report_data, config)
        comparative_analysis = await self._generate_comparative_analysis(report_data, config)
        issue_summary = await self._generate_issue_summary(report_data, config)
        project_health = await self._generate_project_health(report_data, config)
        technical_debt = await self._generate_technical_debt_report(report_data, config)
        
        return {
            'comprehensive_report': {
                'executive_summary': executive_summary,
                'trend_analysis': trend_analysis,
                'comparative_analysis': comparative_analysis,
                'issue_summary': issue_summary,
                'project_health': project_health,
                'technical_debt': technical_debt
            },
            'report_metadata': {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'project_count': len(report_data),
                'report_period': self._get_report_period(config.date_range),
                'configuration': asdict(config)
            }
        }    
   
 # Helper methods for report generation
    
    def _calculate_project_health_score(self, metrics: QualityMetrics) -> float:
        """Calculate overall project health score (0-100)."""
        scores = []
        
        if metrics.code_coverage is not None:
            scores.append(metrics.code_coverage)
        
        if metrics.maintainability_index is not None:
            scores.append(metrics.maintainability_index)
        
        if metrics.test_quality_score is not None:
            scores.append(metrics.test_quality_score)
        
        if metrics.security_score is not None:
            scores.append(metrics.security_score)
        
        if metrics.performance_score is not None:
            scores.append(metrics.performance_score)
        
        # Invert technical debt ratio (lower is better)
        if metrics.technical_debt_ratio is not None:
            debt_score = max(0, 100 - (metrics.technical_debt_ratio * 100))
            scores.append(debt_score)
        
        # Invert complexity (lower is better)
        if metrics.cyclomatic_complexity is not None:
            complexity_score = max(0, 100 - (metrics.cyclomatic_complexity * 5))
            scores.append(complexity_score)
        
        return mean(scores) if scores else 0
    
    def _calculate_quality_grade(self, health_score: float) -> str:
        """Convert health score to letter grade."""
        if health_score >= 90:
            return "A"
        elif health_score >= 80:
            return "B"
        elif health_score >= 70:
            return "C"
        elif health_score >= 60:
            return "D"
        else:
            return "F"
    
    def _calculate_key_metrics_summary(self, metrics_list: List[QualityMetrics]) -> Dict[str, float]:
        """Calculate summary of key metrics across projects."""
        if not metrics_list:
            return {}
        
        summary = {}
        metric_names = [
            'code_coverage', 'cyclomatic_complexity', 'maintainability_index',
            'technical_debt_ratio', 'test_quality_score', 'security_score',
            'performance_score'
        ]
        
        for metric_name in metric_names:
            values = [
                getattr(metrics, metric_name) 
                for metrics in metrics_list 
                if getattr(metrics, metric_name) is not None
            ]
            
            if values:
                summary[metric_name] = {
                    'average': mean(values),
                    'median': median(values),
                    'min': min(values),
                    'max': max(values),
                    'std_dev': stdev(values) if len(values) > 1 else 0
                }
        
        return summary
    
    async def _calculate_improvement_trend(self, report_data: List[QualityReportData]) -> str:
        """Calculate overall improvement trend."""
        improving_count = 0
        declining_count = 0
        stable_count = 0
        
        for data in report_data:
            for trend in data.trends:
                if trend.trend_direction == 'up':
                    # For metrics where higher is better
                    if trend.metric_name in ['code_coverage', 'maintainability_index', 
                                           'test_quality_score', 'security_score', 'performance_score']:
                        improving_count += 1
                    else:
                        declining_count += 1
                elif trend.trend_direction == 'down':
                    # For metrics where lower is better
                    if trend.metric_name in ['cyclomatic_complexity', 'technical_debt_ratio']:
                        improving_count += 1
                    else:
                        declining_count += 1
                else:
                    stable_count += 1
        
        total_trends = improving_count + declining_count + stable_count
        if total_trends == 0:
            return "stable"
        
        improving_ratio = improving_count / total_trends
        declining_ratio = declining_count / total_trends
        
        if improving_ratio > 0.6:
            return "improving"
        elif declining_ratio > 0.6:
            return "declining"
        else:
            return "stable"
    
    async def _generate_executive_recommendations(self, report_data: List[QualityReportData]) -> List[str]:
        """Generate executive-level recommendations."""
        recommendations = []
        
        # Analyze common issues across projects
        all_issues = []
        for data in report_data:
            all_issues.extend(data.issues)
        
        # Count critical issues
        critical_issues = len([issue for issue in all_issues if issue.severity == Severity.CRITICAL])
        if critical_issues > 0:
            recommendations.append(f"Address {critical_issues} critical quality issues immediately")
        
        # Check test coverage
        low_coverage_projects = [
            data for data in report_data 
            if data.metrics.code_coverage and data.metrics.code_coverage < 70
        ]
        if len(low_coverage_projects) > len(report_data) * 0.5:
            recommendations.append("Invest in improving test coverage across projects")
        
        # Check technical debt
        high_debt_projects = [
            data for data in report_data 
            if data.metrics.technical_debt_ratio and data.metrics.technical_debt_ratio > 0.3
        ]
        if len(high_debt_projects) > len(report_data) * 0.3:
            recommendations.append("Prioritize technical debt reduction initiatives")
        
        # Check security
        low_security_projects = [
            data for data in report_data 
            if data.metrics.security_score and data.metrics.security_score < 80
        ]
        if len(low_security_projects) > 0:
            recommendations.append("Enhance security practices and vulnerability management")
        
        # Auto-fix opportunities
        auto_fixable_issues = len([issue for issue in all_issues if issue.auto_fixable])
        if auto_fixable_issues > 10:
            recommendations.append(f"Enable automated fixes for {auto_fixable_issues} fixable issues")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _assess_quality_risk(self, health_score: float, critical_issues: int) -> str:
        """Assess overall quality risk level."""
        if health_score < 40 or critical_issues > 10:
            return "critical"
        elif health_score < 60 or critical_issues > 5:
            return "high"
        elif health_score < 75 or critical_issues > 0:
            return "medium"
        else:
            return "low"
    
    def _determine_investment_priority(self, health_score: float, 
                                     critical_issues: int, 
                                     improvement_trend: str) -> str:
        """Determine investment priority level."""
        if health_score < 50 or critical_issues > 5:
            return "high"
        elif health_score < 70 or improvement_trend == "declining":
            return "medium"
        else:
            return "low"
    
    def _get_report_period(self, date_range: Optional[Tuple[datetime, datetime]]) -> str:
        """Get human-readable report period."""
        if not date_range:
            return "All time"
        
        start_date, end_date = date_range
        return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    
    async def _analyze_metric_trend(self, metric_name: str, trend_data: List[QualityTrend]) -> TrendAnalysis:
        """Analyze trend for a specific metric."""
        if not trend_data:
            return TrendAnalysis(
                metric_name=metric_name,
                trend_direction="stable",
                change_rate=0.0,
                prediction=None,
                confidence_level=0.0,
                seasonal_patterns=[],
                anomalies=[]
            )
        
        # Sort by timestamp
        sorted_trends = sorted(trend_data, key=lambda x: x.timestamp)
        
        # Calculate overall trend direction
        values = [trend.metric_value for trend in sorted_trends]
        if len(values) < 2:
            trend_direction = "stable"
            change_rate = 0.0
        else:
            # Simple linear trend calculation
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            
            first_avg = mean(first_half)
            second_avg = mean(second_half)
            
            change_rate = ((second_avg - first_avg) / first_avg * 100) if first_avg != 0 else 0
            
            if abs(change_rate) < 5:
                trend_direction = "stable"
            elif change_rate > 0:
                trend_direction = "up"
            else:
                trend_direction = "down"
        
        # Simple prediction (linear extrapolation)
        prediction = None
        confidence_level = 0.5  # Default confidence
        
        if len(values) >= 3:
            # Calculate simple moving average for prediction
            recent_values = values[-3:]
            prediction = mean(recent_values)
            
            # Higher confidence with more data points
            confidence_level = min(0.9, 0.3 + (len(values) * 0.1))
        
        # Detect anomalies (values significantly different from mean)
        anomalies = []
        if len(values) > 5:
            mean_value = mean(values)
            std_value = stdev(values)
            
            for i, trend in enumerate(sorted_trends):
                if abs(trend.metric_value - mean_value) > 2 * std_value:
                    anomalies.append({
                        'timestamp': trend.timestamp.isoformat(),
                        'value': trend.metric_value,
                        'deviation': abs(trend.metric_value - mean_value)
                    })
        
        return TrendAnalysis(
            metric_name=metric_name,
            trend_direction=trend_direction,
            change_rate=change_rate,
            prediction=prediction,
            confidence_level=confidence_level,
            seasonal_patterns=[],  # Would require more sophisticated analysis
            anomalies=anomalies
        )
    
    def _calculate_overall_trend_direction(self, trend_analyses: Dict[str, Any]) -> str:
        """Calculate overall trend direction across all metrics."""
        up_count = 0
        down_count = 0
        stable_count = 0
        
        for analysis in trend_analyses.values():
            direction = analysis.get('trend_direction', 'stable')
            if direction == 'up':
                up_count += 1
            elif direction == 'down':
                down_count += 1
            else:
                stable_count += 1
        
        total = up_count + down_count + stable_count
        if total == 0:
            return "stable"
        
        if up_count / total > 0.5:
            return "improving"
        elif down_count / total > 0.5:
            return "declining"
        else:
            return "stable"
    
    async def _generate_trend_insights(self, trend_analyses: Dict[str, Any]) -> List[str]:
        """Generate insights from trend analysis."""
        insights = []
        
        for metric_name, analysis in trend_analyses.items():
            direction = analysis.get('trend_direction', 'stable')
            change_rate = analysis.get('change_rate', 0)
            
            if direction == 'up' and abs(change_rate) > 10:
                if metric_name in ['code_coverage', 'maintainability_index', 'security_score']:
                    insights.append(f"{metric_name.replace('_', ' ').title()} is improving significantly (+{change_rate:.1f}%)")
                else:
                    insights.append(f"{metric_name.replace('_', ' ').title()} is increasing (+{change_rate:.1f}%) - needs attention")
            elif direction == 'down' and abs(change_rate) > 10:
                if metric_name in ['cyclomatic_complexity', 'technical_debt_ratio']:
                    insights.append(f"{metric_name.replace('_', ' ').title()} is decreasing ({change_rate:.1f}%) - good progress")
                else:
                    insights.append(f"{metric_name.replace('_', ' ').title()} is declining ({change_rate:.1f}%) - requires intervention")
        
        return insights[:5]  # Limit to top 5 insights
    
    async def _generate_trend_predictions(self, trend_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictions based on trend analysis."""
        predictions = {}
        
        for metric_name, analysis in trend_analyses.items():
            prediction = analysis.get('prediction')
            confidence = analysis.get('confidence_level', 0)
            
            if prediction is not None and confidence > 0.6:
                predictions[metric_name] = {
                    'predicted_value': prediction,
                    'confidence_level': confidence,
                    'timeframe': '30 days'  # Simple prediction timeframe
                }
        
        return predictions
    
    def _identify_best_practices(self, report_data: List[QualityReportData], 
                               performance_rankings: Dict[str, List[str]]) -> List[str]:
        """Identify best practices from top-performing projects."""
        best_practices = []
        
        # Find consistently top-performing projects
        top_performers = {}
        for metric_name, rankings in performance_rankings.items():
            if rankings:
                top_project = rankings[0]
                top_performers[top_project] = top_performers.get(top_project, 0) + 1
        
        # Get the most consistent top performer
        if top_performers:
            best_project_id = max(top_performers.items(), key=lambda x: x[1])[0]
            best_project_data = next(
                (data for data in report_data if data.project_id == best_project_id), 
                None
            )
            
            if best_project_data:
                metrics = best_project_data.metrics
                
                if metrics.code_coverage and metrics.code_coverage > 90:
                    best_practices.append("Maintain high test coverage (>90%)")
                
                if metrics.technical_debt_ratio and metrics.technical_debt_ratio < 0.1:
                    best_practices.append("Keep technical debt ratio low (<10%)")
                
                if metrics.security_score and metrics.security_score > 95:
                    best_practices.append("Implement comprehensive security practices")
                
                if len(best_project_data.issues) < 5:
                    best_practices.append("Proactive issue prevention and resolution")
        
        return best_practices
    
    def _identify_improvement_opportunities(self, report_data: List[QualityReportData], 
                                          performance_rankings: Dict[str, List[str]]) -> List[str]:
        """Identify improvement opportunities from analysis."""
        opportunities = []
        
        # Analyze common weaknesses
        low_coverage_count = len([
            data for data in report_data 
            if data.metrics.code_coverage and data.metrics.code_coverage < 70
        ])
        
        if low_coverage_count > 0:
            opportunities.append(f"Improve test coverage in {low_coverage_count} projects")
        
        high_complexity_count = len([
            data for data in report_data 
            if data.metrics.cyclomatic_complexity and data.metrics.cyclomatic_complexity > 15
        ])
        
        if high_complexity_count > 0:
            opportunities.append(f"Reduce code complexity in {high_complexity_count} projects")
        
        # Check for auto-fixable issues
        total_auto_fixable = sum(
            len([issue for issue in data.issues if issue.auto_fixable])
            for data in report_data
        )
        
        if total_auto_fixable > 0:
            opportunities.append(f"Apply automated fixes for {total_auto_fixable} issues")
        
        return opportunities
    
    def _identify_top_performer(self, report_data: List[QualityReportData]) -> Dict[str, Any]:
        """Identify the top-performing project."""
        if not report_data:
            return {}
        
        best_project = max(
            report_data, 
            key=lambda data: self._calculate_project_health_score(data.metrics)
        )
        
        return {
            'project_id': best_project.project_id,
            'project_name': best_project.project_name,
            'health_score': self._calculate_project_health_score(best_project.metrics)
        }
    
    async def _identify_most_improved(self, report_data: List[QualityReportData]) -> Dict[str, Any]:
        """Identify the most improved project based on trends."""
        best_improvement = None
        best_improvement_score = 0
        
        for data in report_data:
            improvement_score = 0
            trend_count = 0
            
            for trend in data.trends:
                if trend.change_percentage is not None:
                    # Positive change for good metrics, negative change for bad metrics
                    if trend.metric_name in ['code_coverage', 'maintainability_index', 
                                           'test_quality_score', 'security_score', 'performance_score']:
                        improvement_score += trend.change_percentage
                    else:  # For complexity and debt ratio, negative change is good
                        improvement_score -= trend.change_percentage
                    trend_count += 1
            
            if trend_count > 0:
                avg_improvement = improvement_score / trend_count
                if avg_improvement > best_improvement_score:
                    best_improvement_score = avg_improvement
                    best_improvement = {
                        'project_id': data.project_id,
                        'project_name': data.project_name,
                        'improvement_score': avg_improvement
                    }
        
        return best_improvement or {}
    
    def _identify_projects_needing_attention(self, report_data: List[QualityReportData]) -> List[Dict[str, Any]]:
        """Identify projects that need immediate attention."""
        needs_attention = []
        
        for data in report_data:
            health_score = self._calculate_project_health_score(data.metrics)
            critical_issues = len([
                issue for issue in data.issues 
                if issue.severity == Severity.CRITICAL and issue.status == IssueStatus.OPEN
            ])
            
            if health_score < 60 or critical_issues > 0:
                needs_attention.append({
                    'project_id': data.project_id,
                    'project_name': data.project_name,
                    'health_score': health_score,
                    'critical_issues': critical_issues,
                    'reasons': self._get_attention_reasons(data)
                })
        
        return sorted(needs_attention, key=lambda x: x['health_score'])
    
    def _get_attention_reasons(self, data: QualityReportData) -> List[str]:
        """Get reasons why a project needs attention."""
        reasons = []
        
        if data.metrics.code_coverage and data.metrics.code_coverage < 50:
            reasons.append("Very low test coverage")
        
        if data.metrics.technical_debt_ratio and data.metrics.technical_debt_ratio > 0.4:
            reasons.append("High technical debt")
        
        if data.metrics.security_score and data.metrics.security_score < 70:
            reasons.append("Security vulnerabilities")
        
        critical_issues = len([
            issue for issue in data.issues 
            if issue.severity == Severity.CRITICAL and issue.status == IssueStatus.OPEN
        ])
        
        if critical_issues > 0:
            reasons.append(f"{critical_issues} critical issues")
        
        return reasons
    
    def _generate_issue_recommendations(self, all_issues: List[QualityIssue]) -> List[str]:
        """Generate recommendations based on issue analysis."""
        recommendations = []
        
        # Count issues by type
        type_counts = {}
        for issue in all_issues:
            type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1
        
        # Recommend based on most common issue types
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        
        for issue_type, count in sorted_types[:3]:  # Top 3 issue types
            if issue_type == IssueType.STYLE:
                recommendations.append(f"Implement automated code formatting to address {count} style issues")
            elif issue_type == IssueType.COMPLEXITY:
                recommendations.append(f"Refactor complex code to address {count} complexity issues")
            elif issue_type == IssueType.SECURITY:
                recommendations.append(f"Conduct security review to address {count} security issues")
            elif issue_type == IssueType.TESTING:
                recommendations.append(f"Improve test coverage to address {count} testing issues")
        
        # Check for auto-fixable issues
        auto_fixable = len([issue for issue in all_issues if issue.auto_fixable])
        if auto_fixable > 0:
            recommendations.append(f"Enable automated fixes for {auto_fixable} fixable issues")
        
        return recommendations
    
    def _generate_team_insights(self, team_performance: Dict[str, Any]) -> List[str]:
        """Generate insights about team performance."""
        insights = []
        
        # Find best and worst performing teams
        team_scores = [(team_id, data['avg_health_score']) 
                      for team_id, data in team_performance.items()]
        team_scores.sort(key=lambda x: x[1], reverse=True)
        
        if len(team_scores) >= 2:
            best_team = team_scores[0]
            worst_team = team_scores[-1]
            
            insights.append(f"Team {best_team[0]} leads with {best_team[1]:.1f} average health score")
            insights.append(f"Team {worst_team[0]} needs support with {worst_team[1]:.1f} average health score")
            
            score_gap = best_team[1] - worst_team[1]
            if score_gap > 20:
                insights.append("Significant performance gap between teams suggests need for knowledge sharing")
        
        # Analyze issue distribution
        total_issues = sum(data['total_issues'] for data in team_performance.values())
        if total_issues > 0:
            high_issue_teams = [
                team_id for team_id, data in team_performance.items()
                if data['total_issues'] > total_issues / len(team_performance) * 1.5
            ]
            
            if high_issue_teams:
                insights.append(f"Teams {', '.join(high_issue_teams)} have above-average issue counts")
        
        return insights
    
    def _generate_health_recommendations(self, project_health: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on project health analysis."""
        recommendations = []
        
        # Count projects by health status
        status_counts = {}
        for data in project_health.values():
            status = data['health_status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        critical_count = status_counts.get('critical', 0)
        poor_count = status_counts.get('poor', 0)
        
        if critical_count > 0:
            recommendations.append(f"Immediate intervention required for {critical_count} critical projects")
        
        if poor_count > 0:
            recommendations.append(f"Develop improvement plans for {poor_count} poor-performing projects")
        
        # Analyze common risk factors
        risk_factor_counts = {}
        for data in project_health.values():
            for risk_factor in data['risk_factors']:
                risk_factor_counts[risk_factor] = risk_factor_counts.get(risk_factor, 0) + 1
        
        common_risks = sorted(risk_factor_counts.items(), key=lambda x: x[1], reverse=True)
        for risk_factor, count in common_risks[:2]:  # Top 2 common risks
            if 'technical debt' in risk_factor.lower():
                recommendations.append("Prioritize technical debt reduction across portfolio")
            elif 'test coverage' in risk_factor.lower():
                recommendations.append("Implement organization-wide testing standards")
            elif 'security' in risk_factor.lower():
                recommendations.append("Enhance security practices and training")
        
        return recommendations
    
    def _generate_debt_recommendations(self, debt_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for technical debt reduction."""
        recommendations = []
        
        # Count projects by debt level
        debt_levels = {}
        for data in debt_analysis.values():
            level = data['debt_level']
            debt_levels[level] = debt_levels.get(level, 0) + 1
        
        critical_debt = debt_levels.get('critical', 0)
        high_debt = debt_levels.get('high', 0)
        
        if critical_debt > 0:
            recommendations.append(f"Emergency debt reduction needed for {critical_debt} projects")
        
        if high_debt > 0:
            recommendations.append(f"Schedule debt reduction sprints for {high_debt} high-debt projects")
        
        # Analyze common debt sources
        source_counts = {}
        for data in debt_analysis.values():
            for source in data['debt_sources']:
                source_counts[source] = source_counts.get(source, 0) + 1
        
        common_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
        for source, count in common_sources[:3]:  # Top 3 sources
            if 'complexity' in source.lower():
                recommendations.append("Implement code complexity monitoring and refactoring guidelines")
            elif 'testing' in source.lower():
                recommendations.append("Establish minimum test coverage requirements")
            elif 'duplication' in source.lower():
                recommendations.append("Use automated tools to detect and eliminate code duplication")
            elif 'documentation' in source.lower():
                recommendations.append("Enforce documentation standards and reviews")
        
        return recommendations
    
    async def _format_report(self, content: Dict[str, Any], format: ReportFormat) -> Union[str, bytes]:
        """Format report content according to specified format."""
        if format == ReportFormat.JSON:
            return json.dumps(content, indent=2, default=str)
        
        elif format == ReportFormat.CSV:
            return await self._format_as_csv(content)
        
        elif format == ReportFormat.HTML:
            return await self._format_as_html(content)
        
        elif format == ReportFormat.MARKDOWN:
            return await self._format_as_markdown(content)
        
        elif format == ReportFormat.PDF:
            # Would require additional PDF generation library
            html_content = await self._format_as_html(content)
            return f"PDF generation not implemented. HTML content: {html_content}"
        
        elif format == ReportFormat.EXCEL:
            # Would require additional Excel generation library
            csv_content = await self._format_as_csv(content)
            return f"Excel generation not implemented. CSV content: {csv_content}"
        
        else:
            return json.dumps(content, indent=2, default=str)
    
    async def _format_as_csv(self, content: Dict[str, Any]) -> str:
        """Format report content as CSV."""
        output = io.StringIO()
        
        # Extract tabular data from content
        if 'executive_summary' in content:
            writer = csv.writer(output)
            writer.writerow(['Metric', 'Value'])
            
            summary = content['executive_summary']
            writer.writerow(['Overall Health Score', summary.get('overall_health_score', 0)])
            writer.writerow(['Quality Grade', summary.get('quality_grade', 'N/A')])
            writer.writerow(['Critical Issues', summary.get('critical_issues', 0)])
            writer.writerow(['Improvement Trend', summary.get('improvement_trend', 'N/A')])
            writer.writerow(['Risk Assessment', summary.get('risk_assessment', 'N/A')])
        
        return output.getvalue()
    
    async def _format_as_html(self, content: Dict[str, Any]) -> str:
        """Format report content as HTML."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Quality Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .section { margin: 20px 0; }
                .metric { display: inline-block; margin: 10px; padding: 10px; 
                         background-color: #e9e9e9; border-radius: 3px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .critical { color: red; font-weight: bold; }
                .good { color: green; font-weight: bold; }
            </style>
        </head>
        <body>
        """
        
        html += f"<div class='header'><h1>Quality Report</h1>"
        html += f"<p>Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p></div>"
        
        # Add executive summary if present
        if 'executive_summary' in content:
            summary = content['executive_summary']
            html += "<div class='section'><h2>Executive Summary</h2>"
            html += f"<div class='metric'>Health Score: {summary.get('overall_health_score', 0):.1f}</div>"
            html += f"<div class='metric'>Grade: {summary.get('quality_grade', 'N/A')}</div>"
            html += f"<div class='metric'>Critical Issues: {summary.get('critical_issues', 0)}</div>"
            html += "</div>"
        
        # Add project health if present
        if 'project_health' in content:
            health_data = content['project_health']
            html += "<div class='section'><h2>Project Health</h2><table>"
            html += "<tr><th>Project</th><th>Health Score</th><th>Status</th><th>Critical Issues</th></tr>"
            
            for project_id, data in health_data.items():
                status_class = 'critical' if data['health_status'] in ['critical', 'poor'] else 'good'
                html += f"<tr><td>{data['project_name']}</td>"
                html += f"<td>{data['health_score']:.1f}</td>"
                html += f"<td class='{status_class}'>{data['health_status']}</td>"
                html += f"<td>{data['critical_issues']}</td></tr>"
            
            html += "</table></div>"
        
        html += "</body></html>"
        return html
    
    async def _format_as_markdown(self, content: Dict[str, Any]) -> str:
        """Format report content as Markdown."""
        md = f"# Quality Report\n\n"
        md += f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        
        # Add executive summary
        if 'executive_summary' in content:
            summary = content['executive_summary']
            md += "## Executive Summary\n\n"
            md += f"- **Overall Health Score:** {summary.get('overall_health_score', 0):.1f}\n"
            md += f"- **Quality Grade:** {summary.get('quality_grade', 'N/A')}\n"
            md += f"- **Critical Issues:** {summary.get('critical_issues', 0)}\n"
            md += f"- **Improvement Trend:** {summary.get('improvement_trend', 'N/A')}\n"
            md += f"- **Risk Assessment:** {summary.get('risk_assessment', 'N/A')}\n\n"
            
            recommendations = summary.get('recommendations', [])
            if recommendations:
                md += "### Recommendations\n\n"
                for rec in recommendations:
                    md += f"- {rec}\n"
                md += "\n"
        
        # Add project health
        if 'project_health' in content:
            health_data = content['project_health']
            md += "## Project Health\n\n"
            md += "| Project | Health Score | Status | Critical Issues |\n"
            md += "|---------|-------------|--------|----------------|\n"
            
            for project_id, data in health_data.items():
                md += f"| {data['project_name']} | {data['health_score']:.1f} | "
                md += f"{data['health_status']} | {data['critical_issues']} |\n"
            md += "\n"
        
        return md
    
    async def _store_report(self, config: ReportConfiguration, formatted_report: Union[str, bytes]) -> str:
        """Store generated report in database."""
        import uuid
        
        report_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO quality_reports 
                (id, report_type, format, project_ids, generated_at, report_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                config.report_type.value,
                config.format.value,
                json.dumps(config.project_ids),
                datetime.now(timezone.utc).isoformat(),
                formatted_report if isinstance(formatted_report, str) else formatted_report.decode('utf-8')
            ))
            
            conn.commit()
            return report_id
            
        finally:
            conn.close()
    
    # Database helper methods
    
    async def _get_latest_metrics(self, project_id: str) -> Optional[QualityMetrics]:
        """Get latest quality metrics for a project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM quality_metrics 
                WHERE project_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (project_id,))
            
            row = cursor.fetchone()
            if row:
                return QualityMetrics.from_dict({
                    'id': row[0],
                    'project_id': row[1],
                    'timestamp': row[2],
                    'code_coverage': row[3],
                    'cyclomatic_complexity': row[4],
                    'maintainability_index': row[5],
                    'technical_debt_ratio': row[6],
                    'test_quality_score': row[7],
                    'security_score': row[8],
                    'performance_score': row[9],
                    'lines_of_code': row[10],
                    'duplicate_code_ratio': row[11],
                    'comment_ratio': row[12]
                })
            
            return None
            
        finally:
            conn.close()
    
    async def _get_project_issues(self, project_id: str, 
                                date_range: Optional[Tuple[datetime, datetime]]) -> List[QualityIssue]:
        """Get quality issues for a project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if date_range:
                start_date, end_date = date_range
                cursor.execute("""
                    SELECT * FROM quality_issues 
                    WHERE project_id = ? AND created_at BETWEEN ? AND ?
                    ORDER BY created_at DESC
                """, (project_id, start_date.isoformat(), end_date.isoformat()))
            else:
                cursor.execute("""
                    SELECT * FROM quality_issues 
                    WHERE project_id = ? 
                    ORDER BY created_at DESC
                """, (project_id,))
            
            issues = []
            for row in cursor.fetchall():
                issues.append(QualityIssue.from_dict({
                    'id': row[0],
                    'project_id': row[1],
                    'file_path': row[2],
                    'line_number': row[3],
                    'column_number': row[4],
                    'issue_type': row[5],
                    'severity': row[6],
                    'category': row[7],
                    'description': row[8],
                    'suggested_fix': row[9],
                    'auto_fixable': row[10],
                    'status': row[11],
                    'created_at': row[12],
                    'resolved_at': row[13],
                    'resolved_by': row[14],
                    'resolution_method': row[15]
                }))
            
            return issues
            
        finally:
            conn.close()
    
    async def _get_project_trends(self, project_id: str, 
                                date_range: Optional[Tuple[datetime, datetime]]) -> List[QualityTrend]:
        """Get quality trends for a project."""
        return await self.metrics_collector.get_quality_trends(
            project_id, 
            days=30 if not date_range else (date_range[1] - date_range[0]).days
        )
    
    async def _get_auto_fix_results(self, project_id: str, 
                                  date_range: Optional[Tuple[datetime, datetime]]) -> List[AutoFixResult]:
        """Get auto-fix results for a project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if date_range:
                start_date, end_date = date_range
                cursor.execute("""
                    SELECT * FROM auto_fix_results 
                    WHERE project_id = ? AND applied_at BETWEEN ? AND ?
                    ORDER BY applied_at DESC
                """, (project_id, start_date.isoformat(), end_date.isoformat()))
            else:
                cursor.execute("""
                    SELECT * FROM auto_fix_results 
                    WHERE project_id = ? 
                    ORDER BY applied_at DESC
                """, (project_id,))
            
            results = []
            for row in cursor.fetchall():
                results.append(AutoFixResult.from_dict({
                    'id': row[0],
                    'issue_id': row[1],
                    'project_id': row[2],
                    'file_path': row[3],
                    'fix_type': row[4],
                    'original_content': row[5],
                    'fixed_content': row[6],
                    'success': row[7],
                    'error_message': row[8],
                    'applied_at': row[9],
                    'applied_by': row[10],
                    'rollback_id': row[11],
                    'is_rolled_back': row[12]
                }))
            
            return results
            
        finally:
            conn.close()
    
    async def _get_test_metrics(self, project_id: str) -> Optional[TestQualityMetrics]:
        """Get test quality metrics for a project."""
        # This would be implemented based on test metrics storage
        # For now, return None as placeholder
        return None
    
    async def _get_project_name(self, project_id: str) -> str:
        """Get project name from project ID."""
        # This would typically come from a projects table
        # For now, return a formatted version of the project ID
        return project_id.replace('_', ' ').replace('-', ' ').title() 
   
    # Additional methods for API support
    
    async def list_reports(self, project_id: Optional[str] = None,
                          report_type: Optional[ReportType] = None,
                          limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List previously generated reports."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = "SELECT id, report_type, format, project_ids, generated_at, generated_by, file_size FROM quality_reports"
            params = []
            conditions = []
            
            if project_id:
                conditions.append("project_ids LIKE ?")
                params.append(f'%"{project_id}"%')
            
            if report_type:
                conditions.append("report_type = ?")
                params.append(report_type.value)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY generated_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            
            reports = []
            for row in cursor.fetchall():
                project_ids = json.loads(row[3]) if row[3] else []
                reports.append({
                    'report_id': row[0],
                    'report_type': row[1],
                    'format': row[2],
                    'project_ids': project_ids,
                    'generated_at': row[4],
                    'generated_by': row[5],
                    'file_size': row[6]
                })
            
            return reports
            
        finally:
            conn.close()
    
    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific report by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM quality_reports WHERE id = ?
            """, (report_id,))
            
            row = cursor.fetchone()
            if row:
                project_ids = json.loads(row[3]) if row[3] else []
                return {
                    'report_id': row[0],
                    'report_type': row[1],
                    'format': row[2],
                    'project_ids': project_ids,
                    'generated_at': row[4],
                    'generated_by': row[5],
                    'content': json.loads(row[6]) if row[6] else {},
                    'file_path': row[7],
                    'file_size': row[8],
                    'expires_at': row[9]
                }
            
            return None
            
        finally:
            conn.close()
    
    async def delete_report(self, report_id: str) -> bool:
        """Delete a report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM quality_reports WHERE id = ?", (report_id,))
            conn.commit()
            return cursor.rowcount > 0
            
        finally:
            conn.close()
    
    async def export_report(self, report_id: str, format: ReportFormat) -> Optional[Union[str, bytes]]:
        """Export a report in specified format."""
        report = await self.get_report(report_id)
        if not report:
            return None
        
        content = report.get('content', {})
        return await self._format_report(content, format)
    
    async def schedule_report(self, request: 'ReportRequest', schedule_cron: str, user: str) -> Dict[str, Any]:
        """Schedule automatic report generation."""
        import uuid
        from datetime import datetime, timezone
        
        schedule_id = str(uuid.uuid4())
        
        # This would integrate with a job scheduler like Celery or APScheduler
        # For now, just return a placeholder response
        
        return {
            'schedule_id': schedule_id,
            'next_run': datetime.now(timezone.utc).isoformat(),
            'cron_expression': schedule_cron,
            'report_config': {
                'report_type': request.report_type.value,
                'format': request.format.value,
                'project_ids': request.project_ids
            }
        }