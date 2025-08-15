"""
Demo script showcasing the intelligent code improvement recommendation engine.

This script demonstrates the recommendation engine's capabilities including:
- Duplicate code detection and consolidation suggestions
- Performance optimization recommendations
- Security vulnerability detection
- Code pattern analysis and improvement suggestions
"""

import ast
from app.services.code_analysis.recommendation_engine import RecommendationEngine
from app.services.code_analysis.base_analyzer import AnalysisContext


def demo_duplicate_detection():
    """Demonstrate duplicate code detection."""
    print("=" * 60)
    print("DUPLICATE CODE DETECTION DEMO")
    print("=" * 60)
    
    code_with_duplicates = '''
def calculate_total_price(items, tax_rate):
    subtotal = 0
    for item in items:
        subtotal += item.price * item.quantity
    tax_amount = subtotal * tax_rate
    total = subtotal + tax_amount
    return total

def calculate_order_total(products, tax_percentage):
    subtotal = 0
    for item in products:
        subtotal += item.price * item.quantity
    tax_amount = subtotal * tax_percentage
    total = subtotal + tax_amount
    return total

def process_invoice(line_items, tax_rate):
    subtotal = 0
    for item in line_items:
        subtotal += item.price * item.quantity
    tax_amount = subtotal * tax_rate
    total = subtotal + tax_amount
    return total
'''
    
    engine = RecommendationEngine()
    context = AnalysisContext(
        project_id="demo_project",
        file_path="duplicate_demo.py",
        file_content=code_with_duplicates,
        language="python"
    )
    
    result = engine.analyze(context)
    
    print(f"Analysis completed in {result.execution_time:.3f} seconds")
    print(f"Found {len(result.issues)} recommendations")
    print()
    
    for issue in result.issues:
        if issue.issue_type.value == "duplication":
            print(f"🔄 {issue.description}")
            print(f"   Severity: {issue.severity.value}")
            print(f"   Line: {issue.line_number}")
            if issue.suggested_fix:
                print(f"   Suggested fix: {issue.suggested_fix[:100]}...")
            print()


def demo_security_analysis():
    """Demonstrate security vulnerability detection."""
    print("=" * 60)
    print("SECURITY VULNERABILITY DETECTION DEMO")
    print("=" * 60)
    
    insecure_code = '''
import os
import subprocess

def process_user_input(user_data):
    # Dangerous: using eval with user input
    result = eval(user_data)
    
    # Dangerous: executing system commands with user input
    os.system(f"echo {user_data}")
    
    # Dangerous: hardcoded secrets
    api_key = "sk-1234567890abcdef"
    password = "admin123"
    secret = "my_secret_token"
    
    return result

def unsafe_query(user_id):
    # Missing input validation
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query

def execute_command(cmd):
    # Dangerous: arbitrary command execution
    subprocess.call(cmd, shell=True)
'''
    
    engine = RecommendationEngine()
    context = AnalysisContext(
        project_id="demo_project",
        file_path="security_demo.py",
        file_content=insecure_code,
        language="python"
    )
    
    result = engine.analyze(context)
    
    print(f"Analysis completed in {result.execution_time:.3f} seconds")
    print(f"Found {len(result.issues)} recommendations")
    print()
    
    security_issues = [issue for issue in result.issues if issue.issue_type.value == "security"]
    for issue in security_issues:
        print(f"🔒 {issue.description}")
        print(f"   Severity: {issue.severity.value}")
        print(f"   Line: {issue.line_number}")
        print(f"   Category: {issue.category}")
        print()


def demo_performance_analysis():
    """Demonstrate performance optimization recommendations."""
    print("=" * 60)
    print("PERFORMANCE OPTIMIZATION DEMO")
    print("=" * 60)
    
    inefficient_code = '''
def find_duplicates(data):
    duplicates = []
    # Inefficient: O(n²) nested loops
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            if data[i] == data[j]:
                duplicates.append(data[i])
    return duplicates

def process_large_dataset(dataset):
    results = []
    # Inefficient: repeated function calls in loop
    for i in range(len(dataset)):
        results.append(expensive_computation(dataset[i]))
    return results

def complex_list_comprehension():
    # Complex comprehension that could be simplified
    return [x * y for x in range(100) if x % 2 == 0 
            for y in range(x) if y > 10 and y < 50 
            if (x + y) % 3 == 0]

def expensive_computation(item):
    return item ** 2
'''
    
    engine = RecommendationEngine()
    context = AnalysisContext(
        project_id="demo_project",
        file_path="performance_demo.py",
        file_content=inefficient_code,
        language="python"
    )
    
    result = engine.analyze(context)
    
    print(f"Analysis completed in {result.execution_time:.3f} seconds")
    print(f"Found {len(result.issues)} recommendations")
    print()
    
    performance_issues = [issue for issue in result.issues if issue.issue_type.value == "performance"]
    for issue in performance_issues:
        print(f"⚡ {issue.description}")
        print(f"   Severity: {issue.severity.value}")
        print(f"   Line: {issue.line_number}")
        print(f"   Category: {issue.category}")
        print()


def demo_pattern_analysis():
    """Demonstrate code pattern analysis and refactoring suggestions."""
    print("=" * 60)
    print("CODE PATTERN ANALYSIS DEMO")
    print("=" * 60)
    
    problematic_code = '''
def very_long_function_with_too_many_responsibilities(a, b, c, d, e, f, g, h, i, j):
    # This function is too long and has too many parameters
    result = 0
    
    # Complex condition that should be simplified
    if a > 0 and b < 10 and c == 5 and d != 3 and e >= 7 and f <= 20 and g > h and i != j:
        result += 1
    
    # Lots of repetitive code
    if a > 0:
        result += a
    if b > 0:
        result += b
    if c > 0:
        result += c
    if d > 0:
        result += d
    if e > 0:
        result += e
    if f > 0:
        result += f
    if g > 0:
        result += g
    if h > 0:
        result += h
    if i > 0:
        result += i
    if j > 0:
        result += j
    
    # More complex logic
    for x in range(100):
        if x % 2 == 0:
            for y in range(x):
                if y % 3 == 0:
                    result += x * y
    
    # Even more logic
    temp_list = []
    for item in [a, b, c, d, e, f, g, h, i, j]:
        if item > 0:
            temp_list.append(item * 2)
    
    final_result = sum(temp_list) + result
    return final_result

class GodClass:
    """A class with too many methods and responsibilities."""
    
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
    def method16(self): pass
    def method17(self): pass
    def method18(self): pass
    def method19(self): pass
    def method20(self): pass
    def method21(self): pass
    def method22(self): pass
    def method23(self): pass
    def method24(self): pass
    def method25(self): pass
'''
    
    engine = RecommendationEngine()
    context = AnalysisContext(
        project_id="demo_project",
        file_path="pattern_demo.py",
        file_content=problematic_code,
        language="python"
    )
    
    result = engine.analyze(context)
    
    print(f"Analysis completed in {result.execution_time:.3f} seconds")
    print(f"Found {len(result.issues)} recommendations")
    print()
    
    pattern_issues = [issue for issue in result.issues 
                     if issue.issue_type.value in ["maintainability", "complexity"]]
    for issue in pattern_issues:
        print(f"🔧 {issue.description}")
        print(f"   Severity: {issue.severity.value}")
        print(f"   Line: {issue.line_number}")
        print(f"   Category: {issue.category}")
        print()


def demo_comprehensive_analysis():
    """Demonstrate comprehensive analysis with all recommendation types."""
    print("=" * 60)
    print("COMPREHENSIVE CODE ANALYSIS DEMO")
    print("=" * 60)
    
    complex_code = '''
import os

def calculate_user_score(user_id, items, tax_rate, discount_rate):
    # Security issue: no input validation
    # Performance issue: inefficient calculation
    
    # Hardcoded secret (security issue)
    api_key = "secret_key_123"
    
    # Duplicate calculation logic (appears multiple times)
    subtotal = 0
    for item in items:
        subtotal += item.price * item.quantity
    
    # Dangerous function call (security issue)
    os.system(f"log_calculation {user_id}")
    
    # Complex condition (pattern issue)
    if user_id > 0 and len(items) > 0 and tax_rate >= 0 and discount_rate >= 0 and subtotal > 0:
        tax_amount = subtotal * tax_rate
        discount_amount = subtotal * discount_rate
        total = subtotal + tax_amount - discount_amount
        return total
    
    return 0

def calculate_order_total(order_id, products, tax_percentage, discount_percentage):
    # Duplicate of above function with different names
    api_key = "secret_key_123"  # Same hardcoded secret
    
    subtotal = 0
    for item in products:
        subtotal += item.price * item.quantity
    
    os.system(f"log_calculation {order_id}")  # Same dangerous call
    
    if order_id > 0 and len(products) > 0 and tax_percentage >= 0 and discount_percentage >= 0 and subtotal > 0:
        tax_amount = subtotal * tax_percentage
        discount_amount = subtotal * discount_percentage
        total = subtotal + tax_amount - discount_amount
        return total
    
    return 0
'''
    
    engine = RecommendationEngine()
    context = AnalysisContext(
        project_id="demo_project",
        file_path="comprehensive_demo.py",
        file_content=complex_code,
        language="python"
    )
    
    result = engine.analyze(context)
    
    print(f"Analysis completed in {result.execution_time:.3f} seconds")
    print(f"Found {len(result.issues)} total recommendations")
    print()
    
    # Group recommendations by type
    by_type = {}
    for issue in result.issues:
        issue_type = issue.issue_type.value
        if issue_type not in by_type:
            by_type[issue_type] = []
        by_type[issue_type].append(issue)
    
    for issue_type, issues in by_type.items():
        print(f"{issue_type.upper()} ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"  • {issue.description}")
            print(f"    Severity: {issue.severity.value}, Line: {issue.line_number}")
        print()
    
    # Show metrics
    print("ANALYSIS METRICS:")
    for metric_name, metric_value in result.metrics.items():
        print(f"  {metric_name}: {metric_value}")


def main():
    """Run all recommendation engine demos."""
    print("🚀 INTELLIGENT CODE IMPROVEMENT RECOMMENDATION ENGINE DEMO")
    print("This demo showcases the recommendation engine's capabilities")
    print()
    
    try:
        demo_duplicate_detection()
        demo_security_analysis()
        demo_performance_analysis()
        demo_pattern_analysis()
        demo_comprehensive_analysis()
        
        print("=" * 60)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("The recommendation engine successfully demonstrated:")
        print("✓ Duplicate code detection and consolidation suggestions")
        print("✓ Security vulnerability identification")
        print("✓ Performance optimization recommendations")
        print("✓ Code pattern analysis and refactoring suggestions")
        print("✓ Comprehensive multi-type analysis")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()