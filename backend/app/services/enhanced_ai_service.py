"""
Enhanced AI Service for Advanced Threat Analysis
Provides multi-model intelligence, predictive modeling, and sophisticated analysis
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from enum import Enum

from app.services.llm_service import llm_service
from app.services.prediction_service import RiskPredictionService
from app.services.llm_providers.base import LLMMessage
from app.models.schemas import AgentTask

logger = logging.getLogger(__name__)


class ThreatSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalysisMode(Enum):
    STANDARD = "standard"
    DEEP = "deep"
    LIGHTNING = "lightning"
    COMPREHENSIVE = "comprehensive"


@dataclass
class ThreatIntelligence:
    """Advanced threat intelligence data structure"""
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


@dataclass
class AIInsight:
    """AI-generated insight with supporting data"""
    insight_type: str
    title: str
    description: str
    confidence: float
    supporting_data: Dict[str, Any]
    recommendations: List[str]
    priority_score: float


class EnhancedAIService:
    """
    Enhanced AI service providing advanced threat analysis capabilities
    """
    
    def __init__(self):
        self.risk_predictor = RiskPredictionService()
        self.analysis_cache = {}
        self.threat_patterns_db = self._initialize_threat_patterns()
        
    def _initialize_threat_patterns(self) -> Dict[str, Dict]:
        """Initialize threat pattern database with common attack patterns"""
        return {
            "web_app_sqli": {
                "name": "SQL Injection Attack",
                "mitre_techniques": ["T1190", "T1059.007"],
                "indicators": ["sql", "injection", "database", "query", "parameter"],
                "severity_base": 0.8,
                "common_vectors": ["web forms", "api endpoints", "search parameters"]
            },
            "cloud_misconfiguration": {
                "name": "Cloud Configuration Vulnerability",
                "mitre_techniques": ["T1190", "T1078.004"],
                "indicators": ["aws", "azure", "gcp", "s3", "storage", "permissions"],
                "severity_base": 0.7,
                "common_vectors": ["public buckets", "overprivileged roles", "weak access controls"]
            },
            "api_security": {
                "name": "API Security Weakness",
                "mitre_techniques": ["T1190", "T1557"],
                "indicators": ["api", "rest", "graphql", "authentication", "authorization"],
                "severity_base": 0.75,
                "common_vectors": ["broken authentication", "excessive data exposure", "rate limiting"]
            },
            "container_escape": {
                "name": "Container Escape Vulnerability",
                "mitre_techniques": ["T1611", "T1068"],
                "indicators": ["docker", "kubernetes", "container", "runtime", "escape"],
                "severity_base": 0.85,
                "common_vectors": ["privileged containers", "host mount vulnerabilities", "kernel exploits"]
            },
            "supply_chain": {
                "name": "Supply Chain Attack",
                "mitre_techniques": ["T1195.001", "T1195.002"],
                "indicators": ["dependency", "package", "library", "third-party", "npm", "pip"],
                "severity_base": 0.9,
                "common_vectors": ["malicious packages", "compromised updates", "dependency confusion"]
            }
        }

    async def analyze_system_advanced(
        self, 
        system_description: str,
        analysis_mode: AnalysisMode = AnalysisMode.STANDARD,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Perform advanced system analysis with multi-model intelligence
        """
        logger.info(f"Starting advanced system analysis in {analysis_mode.value} mode")
        
        try:
            # Multi-stage analysis pipeline
            results = {}
            
            # Stage 1: Pattern Recognition and Classification
            pattern_analysis = await self._analyze_threat_patterns(system_description)
            results["pattern_analysis"] = pattern_analysis
            
            # Stage 2: Deep Technical Analysis (if requested)
            if analysis_mode in [AnalysisMode.DEEP, AnalysisMode.COMPREHENSIVE]:
                technical_analysis = await self._deep_technical_analysis(system_description, context)
                results["technical_analysis"] = technical_analysis
            
            # Stage 3: Contextual Threat Intelligence
            threat_intelligence = await self._gather_threat_intelligence(
                system_description, pattern_analysis
            )
            results["threat_intelligence"] = threat_intelligence
            
            # Stage 4: Risk Scoring and Prediction
            risk_analysis = await self._advanced_risk_analysis(
                system_description, pattern_analysis, threat_intelligence
            )
            results["risk_analysis"] = risk_analysis
            
            # Stage 5: AI-Generated Insights
            ai_insights = await self._generate_ai_insights(
                system_description, results, analysis_mode
            )
            results["ai_insights"] = ai_insights
            
            # Stage 6: Temporal Analysis (for comprehensive mode)
            if analysis_mode == AnalysisMode.COMPREHENSIVE:
                temporal_analysis = await self._temporal_threat_analysis(results)
                results["temporal_analysis"] = temporal_analysis
            
            results["analysis_metadata"] = {
                "analysis_mode": analysis_mode.value,
                "timestamp": datetime.utcnow().isoformat(),
                "confidence_score": self._calculate_overall_confidence(results),
                "analysis_duration": "estimated_duration"
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in advanced system analysis: {e}")
            raise

    async def _analyze_threat_patterns(self, system_description: str) -> Dict[str, Any]:
        """Analyze system description for known threat patterns"""
        
        detected_patterns = []
        description_lower = system_description.lower()
        
        for pattern_id, pattern_data in self.threat_patterns_db.items():
            indicators = pattern_data["indicators"]
            matches = sum(1 for indicator in indicators if indicator in description_lower)
            
            if matches > 0:
                confidence = min(0.95, (matches / len(indicators)) * 1.2)
                detected_patterns.append({
                    "pattern_id": pattern_id,
                    "name": pattern_data["name"],
                    "confidence": confidence,
                    "matched_indicators": [ind for ind in indicators if ind in description_lower],
                    "mitre_techniques": pattern_data["mitre_techniques"],
                    "severity_base": pattern_data["severity_base"]
                })
        
        # Sort by confidence
        detected_patterns.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Use AI to validate and enhance pattern detection
        ai_validation = await self._ai_validate_patterns(system_description, detected_patterns)
        
        return {
            "detected_patterns": detected_patterns,
            "pattern_confidence": len(detected_patterns) / len(self.threat_patterns_db),
            "ai_validation": ai_validation,
            "primary_threat_vectors": [p["name"] for p in detected_patterns[:3]]
        }

    async def _ai_validate_patterns(self, system_description: str, patterns: List[Dict]) -> Dict:
        """Use AI to validate detected patterns and suggest additional threats"""
        
        patterns_summary = "\n".join([
            f"- {p['name']}: {p['confidence']:.2f} confidence"
            for p in patterns[:5]
        ])
        
        prompt = f"""Analyze this system description and validate the detected threat patterns:

SYSTEM DESCRIPTION:
{system_description}

DETECTED PATTERNS:
{patterns_summary}

Please provide:
1. Validation of detected patterns (accurate/inaccurate/partially accurate)
2. Any critical threats that might have been missed
3. Context-specific risks based on the system architecture
4. Prioritization of the most critical threats

Respond in JSON format with validation results and additional insights."""

        try:
            messages = [
                LLMMessage(role="system", content="You are a cybersecurity expert specializing in threat analysis and pattern recognition."),
                LLMMessage(role="user", content=prompt)
            ]
            
            response = await llm_service.generate_response(
                messages=messages,
                max_tokens=1000,
                temperature=0.3
            )
            
            # Try to parse JSON response
            try:
                validation_result = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback to structured text parsing
                validation_result = {
                    "validation_summary": response.content,
                    "additional_threats": [],
                    "pattern_accuracy": "unknown"
                }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error in AI pattern validation: {e}")
            return {"error": "AI validation failed", "fallback_used": True}

    async def _deep_technical_analysis(self, system_description: str, context: Optional[Dict]) -> Dict:
        """Perform deep technical analysis using advanced AI reasoning"""
        
        prompt = f"""Perform a deep technical security analysis of this system:

SYSTEM DESCRIPTION:
{system_description}

ADDITIONAL CONTEXT:
{json.dumps(context, indent=2) if context else "No additional context provided"}

Provide a comprehensive technical analysis including:

1. **Architecture Analysis**:
   - System components and their interactions
   - Data flow analysis
   - Trust boundaries identification
   - Critical attack surfaces

2. **Vulnerability Assessment**:
   - Technical vulnerabilities by component
   - Configuration weaknesses
   - Design flaws and security gaps

3. **Attack Vector Analysis**:
   - Detailed attack paths with technical steps
   - Privilege escalation opportunities
   - Data exfiltration scenarios
   - Lateral movement possibilities

4. **Security Control Evaluation**:
   - Existing security measures
   - Control gaps and weaknesses
   - Defense-in-depth assessment

5. **Risk Prioritization**:
   - Critical vulnerabilities requiring immediate attention
   - Medium-risk issues with recommended timelines
   - Long-term security improvements

Respond with detailed technical findings in JSON format."""

        try:
            messages = [
                LLMMessage(
                    role="system", 
                    content="You are a senior security architect and penetration tester with expertise in system design analysis, vulnerability assessment, and threat modeling."
                ),
                LLMMessage(role="user", content=prompt)
            ]
            
            response = await llm_service.generate_response(
                messages=messages,
                max_tokens=2000,
                temperature=0.2
            )
            
            # Parse technical analysis
            try:
                analysis_result = json.loads(response.content)
            except json.JSONDecodeError:
                # Structure the text response
                analysis_result = {
                    "raw_analysis": response.content,
                    "structured": False,
                    "technical_findings": self._extract_technical_findings(response.content)
                }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in deep technical analysis: {e}")
            return {"error": "Deep technical analysis failed"}

    def _extract_technical_findings(self, analysis_text: str) -> Dict:
        """Extract structured findings from unstructured analysis text"""
        # Simple keyword-based extraction for fallback
        findings = {
            "vulnerabilities": [],
            "attack_vectors": [],
            "recommendations": []
        }
        
        lines = analysis_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect sections
            if "vulnerabilit" in line.lower():
                current_section = "vulnerabilities"
            elif "attack" in line.lower() or "vector" in line.lower():
                current_section = "attack_vectors"
            elif "recommend" in line.lower() or "mitigation" in line.lower():
                current_section = "recommendations"
            elif line.startswith('-') or line.startswith('•'):
                if current_section:
                    findings[current_section].append(line[1:].strip())
        
        return findings

    async def _gather_threat_intelligence(
        self, 
        system_description: str, 
        pattern_analysis: Dict
    ) -> List[ThreatIntelligence]:
        """Gather and synthesize threat intelligence"""
        
        detected_patterns = pattern_analysis.get("detected_patterns", [])
        threat_intel = []
        
        for pattern in detected_patterns[:3]:  # Focus on top 3 patterns
            # Generate detailed threat intelligence for each pattern
            intel_prompt = f"""Generate detailed threat intelligence for this security threat:

THREAT: {pattern['name']}
MITRE TECHNIQUES: {', '.join(pattern['mitre_techniques'])}
CONFIDENCE: {pattern['confidence']:.2f}
SYSTEM CONTEXT: {system_description[:500]}...

Provide comprehensive threat intelligence including:
1. Current threat landscape and trends
2. Recent attack campaigns using this technique
3. Potential impact assessment (confidentiality, integrity, availability)
4. Likelihood assessment based on current threat actors
5. Specific mitigation strategies and controls
6. Detection and monitoring recommendations

Format as detailed threat intelligence report."""

            try:
                messages = [
                    LLMMessage(
                        role="system",
                        content="You are a threat intelligence analyst with access to current cybersecurity threat data and attack trends."
                    ),
                    LLMMessage(role="user", content=intel_prompt)
                ]
                
                response = await llm_service.generate_response(
                    messages=messages,
                    max_tokens=1200,
                    temperature=0.4
                )
                
                # Create ThreatIntelligence object
                intel_obj = ThreatIntelligence(
                    threat_id=f"threat_{pattern['pattern_id']}_{datetime.now().timestamp()}",
                    name=pattern['name'],
                    severity=self._map_severity(pattern['severity_base']),
                    confidence=pattern['confidence'],
                    mitre_techniques=pattern['mitre_techniques'],
                    attack_vectors=self.threat_patterns_db[pattern['pattern_id']]['common_vectors'],
                    potential_impact=self._assess_potential_impact(response.content),
                    likelihood_score=self._calculate_likelihood_score(pattern, response.content),
                    temporal_trends={"current_activity": 0.7, "trend_direction": 1.1},
                    contextual_factors=self._extract_contextual_factors(response.content),
                    mitigation_strategies=self._extract_mitigation_strategies(response.content)
                )
                
                threat_intel.append(intel_obj)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error gathering threat intelligence for {pattern['name']}: {e}")
                continue
        
        return threat_intel

    def _map_severity(self, severity_base: float) -> ThreatSeverity:
        """Map numeric severity to enum"""
        if severity_base >= 0.8:
            return ThreatSeverity.CRITICAL
        elif severity_base >= 0.6:
            return ThreatSeverity.HIGH
        elif severity_base >= 0.4:
            return ThreatSeverity.MEDIUM
        else:
            return ThreatSeverity.LOW

    def _assess_potential_impact(self, threat_intel_text: str) -> Dict[str, Any]:
        """Extract potential impact from threat intelligence text"""
        impact = {
            "confidentiality": 0.5,
            "integrity": 0.5,
            "availability": 0.5,
            "financial": 0.5,
            "reputation": 0.5
        }
        
        text_lower = threat_intel_text.lower()
        
        # Simple keyword-based impact assessment
        if any(word in text_lower for word in ["data breach", "exposure", "leak", "steal"]):
            impact["confidentiality"] = 0.8
            impact["financial"] = 0.7
            impact["reputation"] = 0.8
        
        if any(word in text_lower for word in ["modify", "alter", "corrupt", "tamper"]):
            impact["integrity"] = 0.8
        
        if any(word in text_lower for word in ["downtime", "denial", "outage", "crash"]):
            impact["availability"] = 0.8
            impact["financial"] = 0.6
        
        return impact

    def _calculate_likelihood_score(self, pattern: Dict, intel_text: str) -> float:
        """Calculate likelihood score based on various factors"""
        base_likelihood = pattern['confidence']
        
        # Adjust based on threat intelligence content
        text_lower = intel_text.lower()
        
        if "increasing" in text_lower or "trending" in text_lower:
            base_likelihood *= 1.2
        elif "decreasing" in text_lower or "rare" in text_lower:
            base_likelihood *= 0.8
        
        if "actively" in text_lower or "current" in text_lower:
            base_likelihood *= 1.1
        
        return min(0.95, base_likelihood)

    def _extract_contextual_factors(self, intel_text: str) -> List[str]:
        """Extract contextual factors from threat intelligence"""
        factors = []
        
        lines = intel_text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['factor', 'context', 'environment', 'condition']):
                factors.append(line.strip())
        
        # Add default factors if none found
        if not factors:
            factors = ["General applicability", "Industry-standard risk factors"]
        
        return factors[:5]  # Limit to top 5

    def _extract_mitigation_strategies(self, intel_text: str) -> List[Dict[str, Any]]:
        """Extract mitigation strategies from threat intelligence"""
        strategies = []
        
        lines = intel_text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['mitigation', 'control', 'prevention', 'protection']):
                strategies.append({
                    "description": line.strip(),
                    "effort": "medium",
                    "effectiveness": 0.7
                })
        
        return strategies[:10]  # Limit to top 10

    async def _advanced_risk_analysis(
        self, 
        system_description: str,
        pattern_analysis: Dict,
        threat_intelligence: List[ThreatIntelligence]
    ) -> Dict[str, Any]:
        """Perform advanced risk analysis with predictive modeling"""
        
        # Extract threat data for ML prediction
        threat_data = {
            'unique_attack_paths': len(pattern_analysis.get('detected_patterns', [])),
            'avg_attack_complexity': np.mean([p['confidence'] for p in pattern_analysis.get('detected_patterns', [])]) if pattern_analysis.get('detected_patterns') else 0.5,
            'critical_vulnerabilities': len([t for t in threat_intelligence if t.severity == ThreatSeverity.CRITICAL]),
            'high_impact_techniques': len([t for t in threat_intelligence if len(t.mitre_techniques) > 1]),
            'mitre_technique_count': sum(len(t.mitre_techniques) for t in threat_intelligence),
            'public_endpoints': self._estimate_public_endpoints(system_description),
            'trust_boundaries': self._estimate_trust_boundaries(system_description),
            'data_sensitivity_score': self._estimate_data_sensitivity(system_description),
            'days_since_last_analysis': 0,  # Current analysis
            'analysis_frequency': 1,
            'mitre_tactic_coverage': 0.5  # Default value
        }
        
        # Get ML-based risk prediction
        risk_prediction = self.risk_predictor.predict_risk_score(threat_data)
        
        # Get future risk projection
        future_risk = self.risk_predictor.predict_future_risk(threat_data, days_ahead=30)
        
        # Combine with threat intelligence insights
        aggregated_risk = self._aggregate_risk_scores(risk_prediction, threat_intelligence)
        
        return {
            "current_risk_assessment": risk_prediction,
            "future_risk_projection": future_risk,
            "aggregated_risk_score": aggregated_risk,
            "threat_data_used": threat_data,
            "risk_factors_breakdown": self._breakdown_risk_factors(threat_intelligence),
            "temporal_risk_trends": self._analyze_temporal_trends(threat_intelligence)
        }

    def _estimate_public_endpoints(self, system_description: str) -> int:
        """Estimate number of public endpoints from system description"""
        text_lower = system_description.lower()
        endpoint_indicators = ['api', 'endpoint', 'service', 'web', 'public', 'external']
        return min(10, sum(text_lower.count(indicator) for indicator in endpoint_indicators))

    def _estimate_trust_boundaries(self, system_description: str) -> int:
        """Estimate number of trust boundaries"""
        text_lower = system_description.lower()
        boundary_indicators = ['network', 'vpc', 'subnet', 'firewall', 'zone', 'environment']
        return max(1, min(5, sum(text_lower.count(indicator) for indicator in boundary_indicators)))

    def _estimate_data_sensitivity(self, system_description: str) -> float:
        """Estimate data sensitivity score"""
        text_lower = system_description.lower()
        sensitive_keywords = ['personal', 'financial', 'healthcare', 'sensitive', 'confidential', 'private']
        sensitivity = sum(text_lower.count(keyword) for keyword in sensitive_keywords)
        return min(1.0, sensitivity * 0.2)

    def _aggregate_risk_scores(self, ml_prediction: Dict, threat_intelligence: List[ThreatIntelligence]) -> Dict:
        """Aggregate ML prediction with threat intelligence"""
        ml_score = ml_prediction['risk_score']
        ml_confidence = ml_prediction['confidence']
        
        # Calculate threat intelligence score
        if threat_intelligence:
            intel_scores = []
            for threat in threat_intelligence:
                severity_weight = {
                    ThreatSeverity.LOW: 0.25,
                    ThreatSeverity.MEDIUM: 0.5,
                    ThreatSeverity.HIGH: 0.75,
                    ThreatSeverity.CRITICAL: 1.0
                }[threat.severity]
                
                intel_score = severity_weight * threat.likelihood_score * threat.confidence
                intel_scores.append(intel_score)
            
            avg_intel_score = np.mean(intel_scores)
            intel_confidence = np.mean([t.confidence for t in threat_intelligence])
        else:
            avg_intel_score = 0.5
            intel_confidence = 0.3
        
        # Weighted ensemble of ML and intelligence
        ml_weight = ml_confidence
        intel_weight = intel_confidence
        total_weight = ml_weight + intel_weight
        
        if total_weight > 0:
            final_score = (ml_score * ml_weight + avg_intel_score * intel_weight) / total_weight
            final_confidence = (ml_confidence + intel_confidence) / 2
        else:
            final_score = ml_score
            final_confidence = ml_confidence
        
        return {
            "final_risk_score": round(final_score, 3),
            "confidence": round(final_confidence, 3),
            "ml_component": {"score": ml_score, "weight": ml_weight},
            "intelligence_component": {"score": avg_intel_score, "weight": intel_weight},
            "risk_level": self._categorize_risk_level(final_score)
        }

    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize risk score into levels"""
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"

    def _breakdown_risk_factors(self, threat_intelligence: List[ThreatIntelligence]) -> Dict:
        """Breakdown risk factors by category"""
        breakdown = {
            "technical_vulnerabilities": [],
            "process_weaknesses": [],
            "environmental_factors": [],
            "human_factors": []
        }
        
        for threat in threat_intelligence:
            # Categorize based on MITRE techniques
            for technique in threat.mitre_techniques:
                if technique.startswith('T11'):  # Initial Access
                    breakdown["technical_vulnerabilities"].append({
                        "threat": threat.name,
                        "technique": technique,
                        "severity": threat.severity.value
                    })
                elif technique.startswith('T15'):  # Defense Evasion
                    breakdown["process_weaknesses"].append({
                        "threat": threat.name,
                        "technique": technique,
                        "severity": threat.severity.value
                    })
        
        return breakdown

    def _analyze_temporal_trends(self, threat_intelligence: List[ThreatIntelligence]) -> Dict:
        """Analyze temporal trends in threat landscape"""
        trends = {
            "increasing_threats": [],
            "emerging_vectors": [],
            "seasonal_patterns": {},
            "forecast": {}
        }
        
        for threat in threat_intelligence:
            if threat.temporal_trends.get("trend_direction", 1.0) > 1.0:
                trends["increasing_threats"].append({
                    "name": threat.name,
                    "trend": threat.temporal_trends.get("trend_direction", 1.0),
                    "activity_level": threat.temporal_trends.get("current_activity", 0.5)
                })
        
        return trends

    async def _generate_ai_insights(
        self, 
        system_description: str, 
        analysis_results: Dict,
        analysis_mode: AnalysisMode
    ) -> List[AIInsight]:
        """Generate AI-powered insights from analysis results"""
        
        insights = []
        
        # Insight 1: Critical Path Analysis
        critical_insight = await self._generate_critical_path_insight(analysis_results)
        if critical_insight:
            insights.append(critical_insight)
        
        # Insight 2: Defense Gap Analysis
        defense_insight = await self._generate_defense_gap_insight(analysis_results)
        if defense_insight:
            insights.append(defense_insight)
        
        # Insight 3: Risk Trajectory Analysis
        risk_insight = await self._generate_risk_trajectory_insight(analysis_results)
        if risk_insight:
            insights.append(risk_insight)
        
        # Additional insights for comprehensive mode
        if analysis_mode == AnalysisMode.COMPREHENSIVE:
            business_insight = await self._generate_business_impact_insight(analysis_results)
            if business_insight:
                insights.append(business_insight)
            
            compliance_insight = await self._generate_compliance_insight(analysis_results)
            if compliance_insight:
                insights.append(compliance_insight)
        
        return sorted(insights, key=lambda x: x.priority_score, reverse=True)

    async def _generate_critical_path_insight(self, analysis_results: Dict) -> Optional[AIInsight]:
        """Generate insight about critical attack paths"""
        try:
            patterns = analysis_results.get("pattern_analysis", {}).get("detected_patterns", [])
            if not patterns:
                return None
            
            # Find the most critical pattern
            critical_pattern = max(patterns, key=lambda x: x["confidence"] * x["severity_base"])
            
            return AIInsight(
                insight_type="critical_path",
                title="Critical Attack Path Identified",
                description=f"The system is vulnerable to {critical_pattern['name']} attacks with {critical_pattern['confidence']:.1%} confidence. This represents the highest-risk attack vector requiring immediate attention.",
                confidence=critical_pattern["confidence"],
                supporting_data={
                    "pattern": critical_pattern,
                    "mitre_techniques": critical_pattern["mitre_techniques"],
                    "matched_indicators": critical_pattern["matched_indicators"]
                },
                recommendations=[
                    f"Implement specific controls for {critical_pattern['name']}",
                    "Prioritize security testing for this attack vector",
                    "Monitor for indicators of this attack pattern"
                ],
                priority_score=critical_pattern["confidence"] * critical_pattern["severity_base"]
            )
        except Exception as e:
            logger.error(f"Error generating critical path insight: {e}")
            return None

    async def _generate_defense_gap_insight(self, analysis_results: Dict) -> Optional[AIInsight]:
        """Generate insight about defense gaps"""
        try:
            risk_analysis = analysis_results.get("risk_analysis", {})
            aggregated_risk = risk_analysis.get("aggregated_risk_score", {})
            
            if not aggregated_risk:
                return None
            
            risk_score = aggregated_risk.get("final_risk_score", 0.5)
            
            return AIInsight(
                insight_type="defense_gap",
                title="Security Control Gap Analysis",
                description=f"Current security posture shows a {risk_score:.1%} risk level. Analysis indicates potential gaps in layered defense mechanisms.",
                confidence=aggregated_risk.get("confidence", 0.7),
                supporting_data={
                    "risk_breakdown": risk_analysis.get("risk_factors_breakdown", {}),
                    "current_controls": "analysis_pending"
                },
                recommendations=[
                    "Implement defense-in-depth strategy",
                    "Strengthen monitoring and detection capabilities",
                    "Review and update security policies"
                ],
                priority_score=risk_score * 0.8
            )
        except Exception as e:
            logger.error(f"Error generating defense gap insight: {e}")
            return None

    async def _generate_risk_trajectory_insight(self, analysis_results: Dict) -> Optional[AIInsight]:
        """Generate insight about risk trajectory"""
        try:
            risk_analysis = analysis_results.get("risk_analysis", {})
            future_risk = risk_analysis.get("future_risk_projection", {})
            
            if not future_risk:
                return None
            
            scenarios = future_risk.get("scenarios", {})
            pessimistic = scenarios.get("pessimistic", {})
            
            return AIInsight(
                insight_type="risk_trajectory",
                title="Risk Trajectory Forecast",
                description=f"Risk modeling predicts potential escalation to {pessimistic.get('risk_score', 0.5):.1%} risk level within 30 days without intervention.",
                confidence=pessimistic.get("confidence", 0.6),
                supporting_data={
                    "scenarios": scenarios,
                    "current_risk": future_risk.get("current_risk", 0.5),
                    "projection_days": future_risk.get("days_ahead", 30)
                },
                recommendations=future_risk.get("recommendations", []),
                priority_score=pessimistic.get("risk_score", 0.5) * 0.9
            )
        except Exception as e:
            logger.error(f"Error generating risk trajectory insight: {e}")
            return None

    async def _generate_business_impact_insight(self, analysis_results: Dict) -> Optional[AIInsight]:
        """Generate business impact insight"""
        try:
            threat_intelligence = analysis_results.get("threat_intelligence", [])
            if not threat_intelligence:
                return None
            
            # Calculate business impact based on threat intelligence
            financial_impact = sum(t.potential_impact.get("financial", 0) for t in threat_intelligence) / len(threat_intelligence)
            reputation_impact = sum(t.potential_impact.get("reputation", 0) for t in threat_intelligence) / len(threat_intelligence)
            
            return AIInsight(
                insight_type="business_impact",
                title="Business Impact Assessment",
                description=f"Identified threats pose significant business risks with estimated {financial_impact:.1%} financial impact and {reputation_impact:.1%} reputational risk.",
                confidence=0.7,
                supporting_data={
                    "financial_impact": financial_impact,
                    "reputation_impact": reputation_impact,
                    "threat_count": len(threat_intelligence)
                },
                recommendations=[
                    "Develop incident response plan",
                    "Consider cyber insurance coverage",
                    "Implement business continuity measures"
                ],
                priority_score=(financial_impact + reputation_impact) / 2
            )
        except Exception as e:
            logger.error(f"Error generating business impact insight: {e}")
            return None

    async def _generate_compliance_insight(self, analysis_results: Dict) -> Optional[AIInsight]:
        """Generate compliance-related insight"""
        try:
            # Basic compliance insight based on detected patterns
            patterns = analysis_results.get("pattern_analysis", {}).get("detected_patterns", [])
            
            compliance_relevant = [p for p in patterns if any(
                keyword in p["name"].lower() 
                for keyword in ["data", "privacy", "access", "authentication"]
            )]
            
            if compliance_relevant:
                return AIInsight(
                    insight_type="compliance",
                    title="Regulatory Compliance Considerations",
                    description=f"Detected security patterns have implications for regulatory compliance. {len(compliance_relevant)} issues require compliance review.",
                    confidence=0.6,
                    supporting_data={
                        "compliance_patterns": compliance_relevant,
                        "frameworks": ["SOC 2", "ISO 27001", "GDPR"]
                    },
                    recommendations=[
                        "Review compliance requirements",
                        "Document security controls",
                        "Conduct compliance audit"
                    ],
                    priority_score=0.6
                )
        except Exception as e:
            logger.error(f"Error generating compliance insight: {e}")
        
        return None

    async def _temporal_threat_analysis(self, analysis_results: Dict) -> Dict[str, Any]:
        """Perform temporal analysis of threats"""
        return {
            "threat_evolution": {
                "emerging_patterns": [],
                "declining_threats": [],
                "seasonal_variations": {}
            },
            "prediction_horizon": {
                "30_day": "moderate_increase",
                "90_day": "significant_change_possible",
                "1_year": "major_landscape_evolution"
            },
            "monitoring_recommendations": [
                "Implement continuous threat monitoring",
                "Set up automated alerting for pattern changes",
                "Regular threat landscape reviews"
            ]
        }

    def _calculate_overall_confidence(self, results: Dict) -> float:
        """Calculate overall confidence score for the analysis"""
        confidence_scores = []
        
        # Pattern analysis confidence
        pattern_conf = results.get("pattern_analysis", {}).get("pattern_confidence", 0.5)
        confidence_scores.append(pattern_conf)
        
        # Risk analysis confidence
        risk_conf = results.get("risk_analysis", {}).get("aggregated_risk_score", {}).get("confidence", 0.5)
        confidence_scores.append(risk_conf)
        
        # AI insights confidence
        insights = results.get("ai_insights", [])
        if insights:
            insights_conf = np.mean([insight.confidence for insight in insights])
            confidence_scores.append(insights_conf)
        
        return np.mean(confidence_scores) if confidence_scores else 0.5

    async def query_natural_language(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process natural language queries about security analysis"""
        
        prompt = f"""You are an AI security analyst. Answer this security-related question based on the provided context:

QUERY: {query}

CONTEXT: {json.dumps(context, indent=2) if context else "No specific context provided"}

Provide a comprehensive answer including:
1. Direct response to the question
2. Relevant security considerations
3. Actionable recommendations
4. Additional context or warnings if applicable

Format your response as JSON with sections for answer, recommendations, and confidence level."""

        try:
            messages = [
                LLMMessage(role="system", content="You are an expert cybersecurity analyst with deep knowledge of threat modeling, risk assessment, and security best practices."),
                LLMMessage(role="user", content=prompt)
            ]
            
            response = await llm_service.generate_response(
                messages=messages,
                max_tokens=1000,
                temperature=0.4
            )
            
            try:
                result = json.loads(response.content)
            except json.JSONDecodeError:
                result = {
                    "answer": response.content,
                    "recommendations": [],
                    "confidence": 0.7,
                    "structured": False
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing natural language query: {e}")
            return {
                "error": "Failed to process query",
                "query": query,
                "fallback": True
            }

# Global instance
enhanced_ai_service = EnhancedAIService()
