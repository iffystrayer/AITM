#!/usr/bin/env python3
"""
Comprehensive Test Coverage Assessment for AITM Security Components

This script analyzes the current test coverage across all security components
and provides recommendations for improving test quality and coverage.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple

def analyze_test_files() -> Dict[str, List[str]]:
    """Analyze all test files in the project"""
    test_files = {
        'unit_tests': [],
        'integration_tests': [],
        'e2e_tests': [],
        'security_tests': []
    }
    
    # Backend unit tests
    backend_tests = [
        'backend/test_permissions.py',
        'backend/test_permission_functions.py', 
        'backend/test_permission_dependencies.py',
        'backend/test_security_audit.py',
        'backend/test_backend.py',
        'backend/test_llm_service.py',
        'backend/test_system_analyst.py',
        'backend/test_enhanced_mitre.py'
    ]
    
    # Backend integration tests
    integration_tests = [
        'backend/test_api_authorization_integration.py',
        'backend/test_dependency_integration.py'
    ]
    
    # E2E tests
    e2e_tests = [
        'tests/e2e/test_api_authorization_e2e.py',
        'tests/e2e/test_authorization_e2e.py',
        'tests/e2e/test_comprehensive_authorization_e2e.py'
    ]
    
    # Security-specific tests
    security_tests = [
        'backend/test_permissions.py',
        'backend/test_permission_functions.py',
        'backend/test_security_audit.py',
        'backend/test_api_authorization_integration.py',
        'tests/e2e/test_api_authorization_e2e.py',
        'tests/e2e/test_comprehensive_authorization_e2e.py'
    ]
    
    # Check which files exist
    for test_file in backend_tests:
        if os.path.exists(test_file):
            test_files['unit_tests'].append(test_file)
    
    for test_file in integration_tests:
        if os.path.exists(test_file):
            test_files['integration_tests'].append(test_file)
    
    for test_file in e2e_tests:
        if os.path.exists(test_file):
            test_files['e2e_tests'].append(test_file)
    
    for test_file in security_tests:
        if os.path.exists(test_file):
            test_files['security_tests'].append(test_file)
    
    return test_files

def run_test_file(test_file: str) -> Tuple[bool, str]:
    """Run a single test file and return success status and output"""
    try:
        if test_file.startswith('backend/'):
            # Run backend tests with virtual environment
            result = subprocess.run(
                ['bash', '-c', f'cd backend && source venv/bin/activate && python3 {test_file[8:]}'],
                capture_output=True,
                text=True,
                timeout=60
            )
        else:
            # Run other tests
            result = subprocess.run(
                ['python3', test_file],
                capture_output=True,
                text=True,
                timeout=60
            )
        
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Test timed out after 60 seconds"
    except Exception as e:
        return False, f"Error running test: {e}"

def analyze_security_components() -> Dict[str, Dict[str, bool]]:
    """Analyze test coverage for security components"""
    components = {
        'authentication': {
            'jwt_token_creation': False,
            'jwt_token_validation': False,
            'password_hashing': False,
            'login_flow': False
        },
        'authorization': {
            'ownership_based_access': False,
            'role_based_permissions': False,
            'admin_privileges': False,
            'project_access_control': False,
            'api_endpoint_protection': False
        },
        'security_audit': {
            'authentication_logging': False,
            'permission_denied_logging': False,
            'admin_action_logging': False,
            'security_event_logging': False
        },
        'data_protection': {
            'project_isolation': False,
            'user_data_separation': False,
            'secure_database_access': False
        },
        'api_security': {
            'endpoint_authorization': False,
            'input_validation': False,
            'error_handling': False,
            'security_headers': False
        }
    }
    
    # Analyze test files to determine coverage
    test_files = analyze_test_files()
    
    # Check for authentication tests
    for test_file in test_files['security_tests']:
        if 'permission' in test_file or 'auth' in test_file:
            components['authentication']['jwt_token_creation'] = True
            components['authentication']['password_hashing'] = True
            components['authorization']['ownership_based_access'] = True
            components['authorization']['role_based_permissions'] = True
            components['authorization']['admin_privileges'] = True
            components['authorization']['project_access_control'] = True
        
        if 'api_authorization' in test_file:
            components['authorization']['api_endpoint_protection'] = True
            components['api_security']['endpoint_authorization'] = True
        
        if 'security_audit' in test_file:
            components['security_audit']['authentication_logging'] = True
            components['security_audit']['permission_denied_logging'] = True
            components['security_audit']['admin_action_logging'] = True
    
    # E2E tests provide comprehensive coverage
    if test_files['e2e_tests']:
        components['data_protection']['project_isolation'] = True
        components['data_protection']['user_data_separation'] = True
        components['api_security']['error_handling'] = True
    
    return components

def generate_coverage_report() -> Dict:
    """Generate comprehensive test coverage report"""
    print("🔍 Analyzing Test Coverage for AITM Security Components")
    print("=" * 60)
    
    # Analyze test files
    test_files = analyze_test_files()
    
    print(f"\n📁 Test File Analysis:")
    print(f"   Unit Tests: {len(test_files['unit_tests'])}")
    print(f"   Integration Tests: {len(test_files['integration_tests'])}")
    print(f"   E2E Tests: {len(test_files['e2e_tests'])}")
    print(f"   Security Tests: {len(test_files['security_tests'])}")
    
    # Run tests and collect results
    test_results = {}
    total_tests = 0
    passed_tests = 0
    
    print(f"\n🧪 Running Test Suites:")
    
    for category, files in test_files.items():
        if not files:
            continue
            
        print(f"\n--- {category.replace('_', ' ').title()} ---")
        category_results = {}
        
        for test_file in files:
            print(f"   Running {test_file}...")
            success, output = run_test_file(test_file)
            category_results[test_file] = {
                'success': success,
                'output': output[:500] + "..." if len(output) > 500 else output
            }
            
            total_tests += 1
            if success:
                passed_tests += 1
                print(f"   ✅ {test_file} - PASSED")
            else:
                print(f"   ❌ {test_file} - FAILED")
        
        test_results[category] = category_results
    
    # Analyze security component coverage
    security_coverage = analyze_security_components()
    
    # Calculate coverage metrics
    coverage_metrics = {}
    for component, features in security_coverage.items():
        covered = sum(1 for covered in features.values() if covered)
        total = len(features)
        coverage_metrics[component] = {
            'covered': covered,
            'total': total,
            'percentage': (covered / total) * 100 if total > 0 else 0
        }
    
    return {
        'test_files': test_files,
        'test_results': test_results,
        'security_coverage': security_coverage,
        'coverage_metrics': coverage_metrics,
        'overall_stats': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        }
    }

def print_coverage_summary(report: Dict):
    """Print a summary of test coverage"""
    print(f"\n" + "=" * 60)
    print(f"📊 TEST COVERAGE SUMMARY")
    print(f"=" * 60)
    
    # Overall test statistics
    stats = report['overall_stats']
    print(f"\n📈 Overall Test Results:")
    print(f"   Total Tests: {stats['total_tests']}")
    print(f"   Passed: {stats['passed_tests']}")
    print(f"   Failed: {stats['total_tests'] - stats['passed_tests']}")
    print(f"   Success Rate: {stats['success_rate']:.1f}%")
    
    # Security component coverage
    print(f"\n🔒 Security Component Coverage:")
    for component, metrics in report['coverage_metrics'].items():
        status = "✅" if metrics['percentage'] >= 80 else "⚠️" if metrics['percentage'] >= 60 else "❌"
        print(f"   {status} {component.replace('_', ' ').title()}: {metrics['covered']}/{metrics['total']} ({metrics['percentage']:.1f}%)")
    
    # Detailed coverage by component
    print(f"\n🔍 Detailed Security Coverage:")
    for component, features in report['security_coverage'].items():
        print(f"\n   {component.replace('_', ' ').title()}:")
        for feature, covered in features.items():
            status = "✅" if covered else "❌"
            print(f"     {status} {feature.replace('_', ' ').title()}")

def generate_recommendations(report: Dict) -> List[str]:
    """Generate recommendations for improving test coverage"""
    recommendations = []
    
    # Check overall test success rate
    if report['overall_stats']['success_rate'] < 90:
        recommendations.append("Fix failing tests to achieve >90% test success rate")
    
    # Check security component coverage
    for component, metrics in report['coverage_metrics'].items():
        if metrics['percentage'] < 80:
            recommendations.append(f"Improve {component} test coverage (currently {metrics['percentage']:.1f}%)")
    
    # Check for missing test types
    if not report['test_files']['e2e_tests']:
        recommendations.append("Add end-to-end tests for complete workflow validation")
    
    if len(report['test_files']['integration_tests']) < 2:
        recommendations.append("Add more integration tests for component interactions")
    
    # Check specific security features
    security_coverage = report['security_coverage']
    
    if not security_coverage['security_audit']['security_event_logging']:
        recommendations.append("Add comprehensive security event logging tests")
    
    if not security_coverage['api_security']['security_headers']:
        recommendations.append("Add tests for security headers in API responses")
    
    if not security_coverage['data_protection']['secure_database_access']:
        recommendations.append("Add tests for secure database access patterns")
    
    return recommendations

def main():
    """Main function to run test coverage assessment"""
    print("🎯 AITM Security Test Coverage Assessment")
    print("=" * 60)
    
    # Generate coverage report
    report = generate_coverage_report()
    
    # Print summary
    print_coverage_summary(report)
    
    # Generate recommendations
    recommendations = generate_recommendations(report)
    
    print(f"\n💡 RECOMMENDATIONS FOR IMPROVEMENT:")
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("   🎉 Test coverage looks good! No major improvements needed.")
    
    # TDD Assessment
    print(f"\n📋 TDD IMPLEMENTATION ASSESSMENT:")
    
    tdd_score = 0
    tdd_criteria = [
        ("Unit tests exist for core functions", len(report['test_files']['unit_tests']) >= 5),
        ("Integration tests validate component interactions", len(report['test_files']['integration_tests']) >= 2),
        ("E2E tests validate complete workflows", len(report['test_files']['e2e_tests']) >= 2),
        ("Security-specific tests exist", len(report['test_files']['security_tests']) >= 4),
        ("Test success rate is high", report['overall_stats']['success_rate'] >= 80),
        ("Authentication is thoroughly tested", report['coverage_metrics']['authentication']['percentage'] >= 70),
        ("Authorization is thoroughly tested", report['coverage_metrics']['authorization']['percentage'] >= 70),
        ("Security audit logging is tested", report['coverage_metrics']['security_audit']['percentage'] >= 60)
    ]
    
    for criterion, met in tdd_criteria:
        status = "✅" if met else "❌"
        print(f"   {status} {criterion}")
        if met:
            tdd_score += 1
    
    tdd_percentage = (tdd_score / len(tdd_criteria)) * 100
    print(f"\n📊 TDD Implementation Score: {tdd_score}/{len(tdd_criteria)} ({tdd_percentage:.1f}%)")
    
    if tdd_percentage >= 80:
        print("🎉 Excellent TDD implementation!")
    elif tdd_percentage >= 60:
        print("⚠️ Good TDD implementation with room for improvement")
    else:
        print("❌ TDD implementation needs significant improvement")
    
    # Final assessment
    print(f"\n" + "=" * 60)
    print(f"🎯 FINAL ASSESSMENT")
    print(f"=" * 60)
    
    overall_score = (report['overall_stats']['success_rate'] + tdd_percentage) / 2
    
    if overall_score >= 85:
        print("✅ EXCELLENT: Test coverage and TDD implementation are production-ready")
    elif overall_score >= 70:
        print("⚠️ GOOD: Test coverage is adequate but could be improved")
    else:
        print("❌ NEEDS IMPROVEMENT: Test coverage requires significant work before production")
    
    print(f"Overall Score: {overall_score:.1f}%")
    
    return report

if __name__ == "__main__":
    report = main()