"""
Test Suite for AI Agents
Tests for ATT&CK Mapper, Control Evaluation, and Report Generation agents
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json
from datetime import datetime

from app.agents.attack_mapper_agent import AttackMapperAgent, ControlEvaluationAgent
from app.agents.report_generation_agent import ReportGenerationAgent
from app.models.schemas import AgentTask


class TestAttackMapperAgent:
    """Test ATT&CK Mapper Agent"""
    
    @pytest.fixture
    def attack_mapper_agent(self):
        """Create attack mapper agent instance"""
        return AttackMapperAgent()
    
    @pytest.fixture
    def sample_context(self):
        """Sample context data for testing"""
        return {
            'identified_assets': [
                {
                    'name': 'web-server',
                    'type': 'web application',
                    'criticality': 'high'
                },
                {
                    'name': 'database',
                    'type': 'database server',
                    'criticality': 'critical'
                }
            ],
            'identified_technologies': ['nginx', 'postgresql', 'docker'],
            'potential_entry_points': ['public-api', 'admin-panel']
        }
    
    def test_agent_initialization(self, attack_mapper_agent):
        """Test agent initialization"""
        assert attack_mapper_agent.agent_type == "attack_mapper"
        assert "MITRE ATT&CK" in attack_mapper_agent.get_system_prompt()
    
    @pytest.mark.asyncio
    async def test_process_task_success(self, attack_mapper_agent, sample_context):
        """Test successful attack mapping task processing"""
        # Mock context and LLM response
        with patch.object(attack_mapper_agent, 'get_context_data') as mock_context:
            mock_context.return_value = MagicMock(**sample_context)
            
            # Mock enhanced MITRE service
            with patch('app.agents.attack_mapper_agent.get_enhanced_mitre_service') as mock_mitre:
                mock_mitre_service = MagicMock()
                mock_mitre_service.get_techniques_for_system_components.return_value = {
                    'web-server': [
                        {
                            'id': 'T1190',
                            'name': 'Exploit Public-Facing Application',
                            'tactics': ['initial-access']
                        }
                    ],
                    'database': [
                        {
                            'id': 'T1078',
                            'name': 'Valid Accounts',
                            'tactics': ['initial-access', 'persistence']
                        }
                    ]
                }
                mock_mitre.return_value = mock_mitre_service
                
                # Mock LLM response
                with patch.object(attack_mapper_agent, 'generate_llm_response') as mock_llm:
                    mock_llm.return_value = {
                        'success': True,
                        'response': json.dumps({
                            'technique_mappings': [
                                {
                                    'technique_id': 'T1190',
                                    'technique_name': 'Exploit Public-Facing Application',
                                    'tactics': ['initial-access'],
                                    'relevance_reason': 'Web server is publicly accessible',
                                    'applicable_assets': ['web-server'],
                                    'likelihood': 'high'
                                }
                            ],
                            'attack_paths': [
                                {
                                    'name': 'Web Application Attack',
                                    'description': 'Attack via public web interface',
                                    'techniques': ['T1190', 'T1059'],
                                    'priority_score': 0.85,
                                    'explanation': 'High-impact attack path',
                                    'affected_assets': ['web-server'],
                                    'prerequisites': ['Internet access', 'Web vulnerability']
                                }
                            ]
                        })
                    }
                    
                    with patch.object(attack_mapper_agent, 'update_context'):
                        # Create task
                        task = AgentTask(
                            task_id="test-task",
                            agent_type="attack_mapper",
                            task_description="Test attack mapping",
                            input_data={}
                        )
                        
                        # Process task
                        response = await attack_mapper_agent.process_task(task)
                        
                        # Assertions
                        assert response.status == "success"
                        assert response.result['techniques_count'] == 1
                        assert response.result['attack_paths_count'] == 1
                        assert response.confidence_score == 0.80
    
    @pytest.mark.asyncio
    async def test_process_task_no_data(self, attack_mapper_agent):
        """Test handling of missing system data"""
        # Mock empty context
        with patch.object(attack_mapper_agent, 'get_context_data') as mock_context:
            mock_context.return_value = MagicMock(
                identified_assets=[],
                identified_technologies=[],
                potential_entry_points=[]
            )
            
            task = AgentTask(
                task_id="test-task",
                agent_type="attack_mapper",
                task_description="Test attack mapping with no data",
                input_data={}
            )
            
            response = await attack_mapper_agent.process_task(task)
            
            assert response.status == "failure"
            assert "No system assets or technologies identified" in response.result['error']
    
    @pytest.mark.asyncio
    async def test_process_task_llm_failure(self, attack_mapper_agent, sample_context):
        """Test handling of LLM service failure"""
        with patch.object(attack_mapper_agent, 'get_context_data') as mock_context:
            mock_context.return_value = MagicMock(**sample_context)
            
            with patch('app.agents.attack_mapper_agent.get_enhanced_mitre_service'):
                with patch.object(attack_mapper_agent, 'generate_llm_response') as mock_llm:
                    mock_llm.return_value = {'success': False}
                    
                    task = AgentTask(
                        task_id="test-task",
                        agent_type="attack_mapper",
                        task_description="Test LLM failure",
                        input_data={}
                    )
                    
                    response = await attack_mapper_agent.process_task(task)
                    
                    assert response.status == "failure"
                    assert "LLM request failed" in response.result['error']


class TestControlEvaluationAgent:
    """Test Control Evaluation Agent"""
    
    @pytest.fixture
    def control_agent(self):
        """Create control evaluation agent instance"""
        return ControlEvaluationAgent()
    
    @pytest.fixture
    def sample_attack_paths(self):
        """Sample attack paths for testing"""
        return [
            {
                'name': 'Web Attack Path',
                'techniques': ['T1190', 'T1059', 'T1078'],
                'impact': 'high',
                'likelihood': 'medium'
            }
        ]
    
    def test_agent_initialization(self, control_agent):
        """Test control evaluation agent initialization"""
        assert control_agent.agent_type == "control_evaluator"
        assert "control assessment" in control_agent.get_system_prompt()
    
    @pytest.mark.asyncio
    async def test_process_task_success(self, control_agent, sample_attack_paths):
        """Test successful control evaluation"""
        # Mock context with attack paths
        with patch.object(control_agent, 'get_context_data') as mock_context:
            mock_context.return_value = MagicMock(attack_paths=sample_attack_paths)
            
            # Mock enhanced MITRE service
            with patch('app.agents.attack_mapper_agent.get_enhanced_mitre_service') as mock_mitre:
                mock_mitre_service = MagicMock()
                mock_mitre_service.get_technique.return_value = {
                    'id': 'T1190',
                    'name': 'Exploit Public-Facing Application'
                }
                mock_mitre.return_value = mock_mitre_service
                
                # Mock LLM response
                with patch.object(control_agent, 'generate_llm_response') as mock_llm:
                    mock_llm.return_value = {
                        'success': True,
                        'response': json.dumps({
                            'control_evaluations': [
                                {
                                    'technique_id': 'T1190',
                                    'technique_name': 'Exploit Public-Facing Application',
                                    'existing_controls': [
                                        {
                                            'control_name': 'Web Application Firewall',
                                            'effectiveness': 'partial',
                                            'coverage_percentage': 70,
                                            'notes': 'Blocks common attacks'
                                        }
                                    ],
                                    'control_gaps': ['Missing input validation'],
                                    'risk_level': 'medium'
                                }
                            ],
                            'overall_assessment': {
                                'total_techniques_assessed': 3,
                                'adequately_controlled': 1,
                                'partially_controlled': 1,
                                'uncontrolled': 1,
                                'overall_risk_score': 0.65
                            },
                            'priority_gaps': [
                                {
                                    'gap_description': 'No endpoint detection and response',
                                    'affected_techniques': ['T1055', 'T1059'],
                                    'priority': 'high',
                                    'recommendation': 'Deploy EDR solution'
                                }
                            ]
                        })
                    }
                    
                    with patch.object(control_agent, 'update_context'):
                        # Create task with control information
                        task = AgentTask(
                            task_id="test-task",
                            agent_type="control_evaluator",
                            task_description="Test control evaluation",
                            input_data={
                                'existing_controls': ['WAF', 'Firewall'],
                                'control_documentation': 'Basic security controls in place'
                            }
                        )
                        
                        response = await control_agent.process_task(task)
                        
                        assert response.status == "success"
                        assert response.result['techniques_assessed'] == 1
                        assert response.result['gaps_identified'] == 1
                        assert response.confidence_score == 0.75
    
    @pytest.mark.asyncio
    async def test_process_task_no_attack_paths(self, control_agent):
        """Test handling of missing attack paths"""
        with patch.object(control_agent, 'get_context_data') as mock_context:
            mock_context.return_value = MagicMock(attack_paths=[])
            
            task = AgentTask(
                task_id="test-task",
                agent_type="control_evaluator",
                task_description="Test no attack paths",
                input_data={}
            )
            
            response = await control_agent.process_task(task)
            
            assert response.status == "failure"
            assert "No attack paths identified" in response.result['error']


class TestReportGenerationAgent:
    """Test Report Generation Agent"""
    
    @pytest.fixture
    def report_agent(self):
        """Create report generation agent instance"""
        return ReportGenerationAgent()
    
    @pytest.fixture
    def sample_full_context(self):
        """Sample full context data for report generation"""
        return {
            'system_analysis_results': [{'analysis': 'completed'}],
            'attack_paths': [
                {
                    'name': 'Web Attack Path',
                    'techniques': ['T1190', 'T1059'],
                    'impact': 'high',
                    'likelihood': 'medium'
                }
            ],
            'control_evaluation_results': [
                {
                    'control_evaluations': [
                        {
                            'technique_id': 'T1190',
                            'risk_level': 'medium'
                        }
                    ],
                    'overall_assessment': {
                        'overall_risk_score': 0.65
                    }
                }
            ],
            'identified_assets': [
                {
                    'name': 'web-server',
                    'type': 'web application',
                    'criticality': 'high'
                }
            ],
            'identified_technologies': ['nginx', 'postgresql'],
            'potential_entry_points': ['public-api']
        }
    
    def test_agent_initialization(self, report_agent):
        """Test report generation agent initialization"""
        assert report_agent.agent_type == "report_generator"
        assert "report writer" in report_agent.get_system_prompt()
    
    @pytest.mark.asyncio
    async def test_process_task_success(self, report_agent, sample_full_context):
        """Test successful report generation"""
        with patch.object(report_agent, 'get_context_data') as mock_context:
            # Create mock context object with attributes
            mock_context_obj = MagicMock()
            for key, value in sample_full_context.items():
                setattr(mock_context_obj, key, value)
            mock_context.return_value = mock_context_obj
            
            # Mock enhanced MITRE service
            with patch('app.agents.report_generation_agent.get_enhanced_mitre_service') as mock_mitre:
                mock_mitre_service = MagicMock()
                mock_mitre_service.get_technique_count.return_value = 823
                mock_mitre_service.get_all_tactics.return_value = ['initial-access', 'execution']
                mock_mitre_service.get_techniques_by_tactic.return_value = [
                    {'id': 'T1190', 'name': 'Exploit Public-Facing Application'}
                ]
                mock_mitre_service.get_technique.return_value = {
                    'id': 'T1190',
                    'name': 'Exploit Public-Facing Application',
                    'tactics': ['initial-access'],
                    'description': 'Attack technique description'
                }
                mock_mitre.return_value = mock_mitre_service
                
                # Mock LLM response
                with patch.object(report_agent, 'generate_llm_response') as mock_llm:
                    mock_llm.return_value = {
                        'success': True,
                        'response': json.dumps({
                            'executive_summary': {
                                'overview': 'System has moderate security risks',
                                'key_findings': ['Public-facing vulnerabilities', 'Control gaps'],
                                'risk_level': 'medium',
                                'priority_actions': ['Patch web server', 'Implement monitoring'],
                                'business_impact': 'Potential data breach'
                            },
                            'technical_analysis': {
                                'system_overview': 'Web application with database backend',
                                'attack_surface': {
                                    'entry_points': 1,
                                    'critical_assets': 1,
                                    'identified_threats': 2
                                },
                                'threat_landscape': [
                                    {
                                        'threat_category': 'Web Application Attacks',
                                        'techniques_count': 2,
                                        'risk_level': 'high',
                                        'description': 'Attacks targeting web interface'
                                    }
                                ],
                                'attack_paths': [
                                    {
                                        'path_name': 'Web Attack Path',
                                        'likelihood': 'medium',
                                        'impact': 'high',
                                        'techniques': ['T1190', 'T1059'],
                                        'description': 'Attack via web vulnerability'
                                    }
                                ]
                            },
                            'control_assessment': {
                                'current_controls': 'Basic controls in place',
                                'effectiveness_score': 0.65,
                                'control_gaps': [
                                    {
                                        'gap': 'No input validation',
                                        'severity': 'high',
                                        'affected_techniques': ['T1190'],
                                        'recommendation': 'Implement input validation'
                                    }
                                ]
                            },
                            'recommendations': {
                                'immediate_actions': [
                                    {
                                        'priority': 1,
                                        'action': 'Patch web server vulnerabilities',
                                        'justification': 'Prevents initial access',
                                        'timeline': '1 week',
                                        'effort': 'medium'
                                    }
                                ],
                                'strategic_improvements': [
                                    {
                                        'improvement': 'Implement security monitoring',
                                        'benefits': 'Early threat detection',
                                        'timeline': '3 months',
                                        'investment': 'medium'
                                    }
                                ]
                            },
                            'metrics': {
                                'threat_coverage': 0.85,
                                'control_maturity': 0.70,
                                'residual_risk': 0.45,
                                'techniques_analyzed': 2,
                                'paths_identified': 1
                            }
                        })
                    }
                    
                    with patch.object(report_agent, 'update_context'):
                        task = AgentTask(
                            task_id="test-task",
                            agent_type="report_generator",
                            task_description="Test report generation success",
                            input_data={}
                        )
                        
                        response = await report_agent.process_task(task)
                        
                        assert response.status == "success"
                        assert 'report' in response.result
                        assert response.result['report_summary']['risk_level'] == 'medium'
                        assert response.result['report_summary']['techniques_analyzed'] == 2
                        assert response.confidence_score == 0.88
    
    @pytest.mark.asyncio
    async def test_process_task_insufficient_data(self, report_agent):
        """Test handling of insufficient analysis data"""
        with patch.object(report_agent, 'get_context_data') as mock_context:
            # Create mock context with no analysis data
            mock_context_obj = MagicMock()
            mock_context_obj.system_analysis_results = []
            mock_context_obj.attack_paths = []
            mock_context_obj.control_evaluation_results = []
            mock_context.return_value = mock_context_obj
            
            task = AgentTask(
                task_id="test-task",
                agent_type="report_generator",
                task_description="Test insufficient data",
                input_data={}
            )
            
            response = await report_agent.process_task(task)
            
            assert response.status == "failure"
            assert "Insufficient analysis data" in response.result['error']
    
    def test_count_unique_techniques(self, report_agent):
        """Test unique technique counting"""
        attack_paths = [
            {'techniques': ['T1190', 'T1059']},
            {'techniques': ['T1190', 'T1078']},  # T1190 repeated
            {'techniques': ['T1055']}
        ]
        
        count = report_agent._count_unique_techniques(attack_paths)
        assert count == 4  # T1190, T1059, T1078, T1055
    
    @pytest.mark.asyncio
    async def test_calculate_mitre_coverage(self, report_agent):
        """Test MITRE coverage calculation"""
        attack_paths = [{'techniques': ['T1190', 'T1059']}]
        
        # Mock MITRE service
        mock_mitre_service = MagicMock()
        mock_mitre_service.get_technique_count.return_value = 100
        mock_mitre_service.get_all_tactics.return_value = ['initial-access']
        mock_mitre_service.get_techniques_by_tactic.return_value = [
            {'id': 'T1190'},
            {'id': 'T1059'},
            {'id': 'T1078'}
        ]
        
        coverage = await report_agent._calculate_mitre_coverage(attack_paths, mock_mitre_service)
        
        assert coverage['techniques_covered'] == 2
        assert coverage['total_techniques'] == 100
        assert coverage['percentage'] == 2.0
        assert 'tactic_coverage' in coverage
    
    @pytest.mark.asyncio 
    async def test_calculate_risk_metrics(self, report_agent):
        """Test risk metrics calculation"""
        attack_paths = [
            {'impact': 'critical', 'likelihood': 'high'},
            {'impact': 'high', 'likelihood': 'medium'},
            {'impact': 'medium', 'likelihood': 'low'}
        ]
        
        control_evaluations = [
            {
                'overall_assessment': {
                    'overall_risk_score': 0.7
                }
            }
        ]
        
        assets = [
            {'criticality': 'critical'},
            {'criticality': 'high'}
        ]
        
        metrics = await report_agent._calculate_risk_metrics(
            attack_paths, control_evaluations, assets
        )
        
        assert metrics['total_attack_paths'] == 3
        assert metrics['critical_findings_count'] == 1
        assert metrics['critical_assets_count'] == 1
        assert metrics['overall_risk_score'] > 0
        assert metrics['control_effectiveness'] > 0


if __name__ == "__main__":
    pytest.main([__file__])
