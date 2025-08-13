#!/usr/bin/env python3
"""
Production Security Configuration Validation Script

This script validates all security configurations required for production deployment
of the AITM system, including JWT settings, HTTPS/TLS configuration, security headers,
and audit logging setup.
"""

import os
import sys
import json
import secrets
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityConfigValidator:
    """Comprehensive security configuration validator for production deployment"""
    
    def __init__(self, env_file: str = ".env.prod"):
        self.env_file = env_file
        self.config = {}
        self.validation_results = []
        self.critical_issues = []
        self.warnings = []
        
    def load_environment_config(self) -> bool:
        """Load environment configuration from file"""
        try:
            if not os.path.exists(self.env_file):
                self.critical_issues.append(f"Environment file {self.env_file} not found")
                return False
            
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Clean value by removing inline comments
                        value = value.split('#')[0].strip()
                        self.config[key.strip()] = value
            
            logger.info(f"Loaded {len(self.config)} configuration variables from {self.env_file}")
            return True
            
        except Exception as e:
            self.critical_issues.append(f"Failed to load environment config: {str(e)}")
            return False
    
    def validate_jwt_security(self) -> Dict[str, str]:
        """Validate JWT token security configuration"""
        results = {}
        
        # Check JWT secret key
        jwt_secret = self.config.get('JWT_SECRET_KEY') or self.config.get('SECRET_KEY')
        if not jwt_secret:
            self.critical_issues.append("JWT_SECRET_KEY is not configured")
            results['jwt_secret'] = "CRITICAL: Missing"
        elif len(jwt_secret) < 32:
            self.critical_issues.append(f"JWT_SECRET_KEY is too short ({len(jwt_secret)} chars, minimum 32)")
            results['jwt_secret'] = f"CRITICAL: Too short ({len(jwt_secret)} chars)"
        elif jwt_secret in [
            'your-super-secret-jwt-key-change-this-in-production',
            'your-super-secure-jwt-secret-key-min-32-chars',
            'secret', 'password', '123456', 'changeme'
        ]:
            self.critical_issues.append("JWT_SECRET_KEY appears to be a default/weak value")
            results['jwt_secret'] = "CRITICAL: Default/weak value"
        else:
            results['jwt_secret'] = f"✅ Secure ({len(jwt_secret)} chars)"
        
        # Check JWT algorithm
        jwt_algorithm = self.config.get('JWT_ALGORITHM', 'HS256')
        if jwt_algorithm != 'HS256':
            self.warnings.append(f"JWT algorithm is {jwt_algorithm}, recommended: HS256")
            results['jwt_algorithm'] = f"⚠️ {jwt_algorithm} (recommend HS256)"
        else:
            results['jwt_algorithm'] = "✅ HS256"
        
        # Check token expiration settings
        access_expire = int(self.config.get('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
        if access_expire > 60:
            self.warnings.append(f"Access token expiry is {access_expire} minutes (recommend ≤60)")
            results['access_token_expiry'] = f"⚠️ {access_expire} minutes (long)"
        else:
            results['access_token_expiry'] = f"✅ {access_expire} minutes"
        
        refresh_expire = int(self.config.get('REFRESH_TOKEN_EXPIRE_DAYS', '7'))
        if refresh_expire > 30:
            self.warnings.append(f"Refresh token expiry is {refresh_expire} days (recommend ≤30)")
            results['refresh_token_expiry'] = f"⚠️ {refresh_expire} days (long)"
        else:
            results['refresh_token_expiry'] = f"✅ {refresh_expire} days"
        
        return results
    
    def validate_https_tls_config(self) -> Dict[str, str]:
        """Validate HTTPS/TLS configuration"""
        results = {}
        
        # Check SSL certificate paths
        ssl_cert_path = self.config.get('SSL_CERT_PATH')
        ssl_key_path = self.config.get('SSL_KEY_PATH')
        
        if not ssl_cert_path:
            self.warnings.append("SSL_CERT_PATH not configured")
            results['ssl_cert_path'] = "⚠️ Not configured"
        else:
            results['ssl_cert_path'] = f"✅ {ssl_cert_path}"
        
        if not ssl_key_path:
            self.warnings.append("SSL_KEY_PATH not configured")
            results['ssl_key_path'] = "⚠️ Not configured"
        else:
            results['ssl_key_path'] = f"✅ {ssl_key_path}"
        
        # Check ACME configuration for Let's Encrypt
        acme_email = self.config.get('ACME_EMAIL')
        if not acme_email:
            self.warnings.append("ACME_EMAIL not configured for Let's Encrypt")
            results['acme_email'] = "⚠️ Not configured"
        else:
            results['acme_email'] = f"✅ {acme_email}"
        
        # Check HSTS configuration
        enable_hsts = self.config.get('ENABLE_HSTS', 'true').lower()
        hsts_max_age = int(self.config.get('HSTS_MAX_AGE', '31536000'))
        
        if enable_hsts == 'true':
            if hsts_max_age < 31536000:  # 1 year
                self.warnings.append(f"HSTS max age is {hsts_max_age} seconds (recommend ≥31536000)")
                results['hsts'] = f"⚠️ Enabled, {hsts_max_age}s (short)"
            else:
                results['hsts'] = f"✅ Enabled, {hsts_max_age}s"
        else:
            self.warnings.append("HSTS is disabled")
            results['hsts'] = "⚠️ Disabled"
        
        return results
    
    def validate_security_headers(self) -> Dict[str, str]:
        """Validate security headers configuration"""
        results = {}
        
        # Check Content Security Policy
        enable_csp = self.config.get('ENABLE_CSP', 'true').lower()
        if enable_csp == 'true':
            csp_default_src = self.config.get('CSP_DEFAULT_SRC', "'self'")
            results['csp'] = f"✅ Enabled, default-src: {csp_default_src}"
        else:
            self.warnings.append("Content Security Policy is disabled")
            results['csp'] = "⚠️ Disabled"
        
        # Check session security
        session_secure = self.config.get('SESSION_SECURE', 'true').lower()
        session_httponly = self.config.get('SESSION_HTTPONLY', 'true').lower()
        session_samesite = self.config.get('SESSION_SAMESITE', 'strict').lower()
        
        if session_secure == 'true':
            results['session_secure'] = "✅ Enabled"
        else:
            self.warnings.append("Secure session cookies disabled")
            results['session_secure'] = "⚠️ Disabled"
        
        if session_httponly == 'true':
            results['session_httponly'] = "✅ Enabled"
        else:
            self.warnings.append("HttpOnly session cookies disabled")
            results['session_httponly'] = "⚠️ Disabled"
        
        if session_samesite in ['strict', 'lax']:
            results['session_samesite'] = f"✅ {session_samesite.title()}"
        else:
            self.warnings.append(f"Session SameSite is {session_samesite} (recommend strict/lax)")
            results['session_samesite'] = f"⚠️ {session_samesite}"
        
        return results
    
    def validate_cors_configuration(self) -> Dict[str, str]:
        """Validate CORS configuration for production"""
        results = {}
        
        cors_origins = self.config.get('CORS_ORIGINS', '')
        if not cors_origins:
            self.critical_issues.append("CORS_ORIGINS not configured")
            results['cors_origins'] = "CRITICAL: Not configured"
        elif cors_origins == '*':
            self.critical_issues.append("CORS allows all origins (*) - security risk")
            results['cors_origins'] = "CRITICAL: Allows all origins"
        elif 'localhost' in cors_origins or '127.0.0.1' in cors_origins:
            self.warnings.append("CORS includes localhost/127.0.0.1 - remove for production")
            results['cors_origins'] = f"⚠️ Includes localhost: {cors_origins}"
        else:
            origins = cors_origins.split(',')
            results['cors_origins'] = f"✅ {len(origins)} origins configured"
        
        return results
    
    def validate_database_security(self) -> Dict[str, str]:
        """Validate database security configuration"""
        results = {}
        
        # Check database password
        db_password = self.config.get('DB_PASSWORD')
        if not db_password:
            self.critical_issues.append("DB_PASSWORD not configured")
            results['db_password'] = "CRITICAL: Not configured"
        elif len(db_password) < 16:
            self.critical_issues.append(f"DB_PASSWORD is too short ({len(db_password)} chars, minimum 16)")
            results['db_password'] = f"CRITICAL: Too short ({len(db_password)} chars)"
        elif db_password in ['password', '123456', 'changeme', 'admin']:
            self.critical_issues.append("DB_PASSWORD appears to be a weak/default value")
            results['db_password'] = "CRITICAL: Weak/default value"
        else:
            results['db_password'] = f"✅ Secure ({len(db_password)} chars)"
        
        # Check database URL
        database_url = self.config.get('DATABASE_URL', '')
        if 'sqlite' in database_url.lower():
            self.warnings.append("Using SQLite database - consider PostgreSQL for production")
            results['database_type'] = "⚠️ SQLite (consider PostgreSQL)"
        elif 'postgresql' in database_url.lower():
            results['database_type'] = "✅ PostgreSQL"
        else:
            results['database_type'] = f"? Unknown: {database_url[:50]}..."
        
        # Check connection pool settings
        pool_size = int(self.config.get('DATABASE_POOL_SIZE', '5'))
        if pool_size < 10:
            self.warnings.append(f"Database pool size is {pool_size} (recommend ≥10 for production)")
            results['db_pool_size'] = f"⚠️ {pool_size} (small)"
        else:
            results['db_pool_size'] = f"✅ {pool_size}"
        
        return results
    
    def validate_audit_logging(self) -> Dict[str, str]:
        """Validate security audit logging configuration"""
        results = {}
        
        # Check audit logging enabled
        audit_enabled = self.config.get('AUDIT_LOG_ENABLED', 'true').lower()
        if audit_enabled == 'true':
            results['audit_enabled'] = "✅ Enabled"
        else:
            self.critical_issues.append("Security audit logging is disabled")
            results['audit_enabled'] = "CRITICAL: Disabled"
        
        # Check audit log retention
        audit_retention = int(self.config.get('AUDIT_LOG_RETENTION_DAYS', '365'))
        if audit_retention < 365:
            self.warnings.append(f"Audit log retention is {audit_retention} days (recommend ≥365)")
            results['audit_retention'] = f"⚠️ {audit_retention} days (short)"
        else:
            results['audit_retention'] = f"✅ {audit_retention} days"
        
        # Check log format
        log_format = self.config.get('LOG_FORMAT', 'text')
        if log_format.lower() == 'json':
            results['log_format'] = "✅ JSON (structured)"
        else:
            self.warnings.append("Log format is not JSON - structured logging recommended")
            results['log_format'] = f"⚠️ {log_format} (recommend JSON)"
        
        return results
    
    def validate_rate_limiting(self) -> Dict[str, str]:
        """Validate rate limiting configuration"""
        results = {}
        
        rate_limit_requests = int(self.config.get('RATE_LIMIT_REQUESTS', '100'))
        rate_limit_window = int(self.config.get('RATE_LIMIT_WINDOW', '300'))
        
        if rate_limit_requests > 1000:
            self.warnings.append(f"Rate limit is high ({rate_limit_requests} requests)")
            results['rate_limit'] = f"⚠️ {rate_limit_requests} req/{rate_limit_window}s (high)"
        else:
            results['rate_limit'] = f"✅ {rate_limit_requests} req/{rate_limit_window}s"
        
        return results
    
    def validate_monitoring_security(self) -> Dict[str, str]:
        """Validate monitoring and alerting security"""
        results = {}
        
        # Check Grafana password
        grafana_password = self.config.get('GRAFANA_PASSWORD')
        if not grafana_password:
            self.critical_issues.append("GRAFANA_PASSWORD not configured")
            results['grafana_password'] = "CRITICAL: Not configured"
        elif len(grafana_password) < 12:
            self.warnings.append(f"Grafana password is short ({len(grafana_password)} chars)")
            results['grafana_password'] = f"⚠️ Short ({len(grafana_password)} chars)"
        else:
            results['grafana_password'] = f"✅ Secure ({len(grafana_password)} chars)"
        
        # Check Sentry DSN (if configured)
        sentry_dsn = self.config.get('SENTRY_DSN')
        if sentry_dsn:
            results['sentry_dsn'] = "✅ Configured"
        else:
            results['sentry_dsn'] = "⚠️ Not configured"
        
        return results
    
    def generate_security_recommendations(self) -> List[str]:
        """Generate security recommendations based on validation results"""
        recommendations = []
        
        if self.critical_issues:
            recommendations.append("🚨 CRITICAL ISSUES MUST BE RESOLVED BEFORE DEPLOYMENT:")
            for issue in self.critical_issues:
                recommendations.append(f"   • {issue}")
            recommendations.append("")
        
        if self.warnings:
            recommendations.append("⚠️ WARNINGS - RECOMMENDED IMPROVEMENTS:")
            for warning in self.warnings:
                recommendations.append(f"   • {warning}")
            recommendations.append("")
        
        # Additional security recommendations
        recommendations.extend([
            "🔒 ADDITIONAL SECURITY RECOMMENDATIONS:",
            "   • Implement Web Application Firewall (WAF)",
            "   • Set up intrusion detection system (IDS)",
            "   • Configure automated security scanning",
            "   • Implement API rate limiting per user",
            "   • Set up security incident response procedures",
            "   • Configure automated backup encryption",
            "   • Implement database query monitoring",
            "   • Set up SSL certificate monitoring and auto-renewal",
            ""
        ])
        
        return recommendations
    
    def run_validation(self) -> Dict:
        """Run complete security configuration validation"""
        logger.info("Starting production security configuration validation...")
        
        if not self.load_environment_config():
            return {
                'status': 'FAILED',
                'critical_issues': self.critical_issues,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        # Run all validation checks
        validation_results = {
            'jwt_security': self.validate_jwt_security(),
            'https_tls': self.validate_https_tls_config(),
            'security_headers': self.validate_security_headers(),
            'cors_config': self.validate_cors_configuration(),
            'database_security': self.validate_database_security(),
            'audit_logging': self.validate_audit_logging(),
            'rate_limiting': self.validate_rate_limiting(),
            'monitoring_security': self.validate_monitoring_security()
        }
        
        # Generate recommendations
        recommendations = self.generate_security_recommendations()
        
        # Determine overall status
        if self.critical_issues:
            status = 'CRITICAL_ISSUES'
        elif self.warnings:
            status = 'WARNINGS'
        else:
            status = 'PASSED'
        
        return {
            'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'validation_results': validation_results,
            'critical_issues': self.critical_issues,
            'warnings': self.warnings,
            'recommendations': recommendations,
            'summary': {
                'total_checks': sum(len(category) for category in validation_results.values()),
                'critical_issues_count': len(self.critical_issues),
                'warnings_count': len(self.warnings)
            }
        }
    
    def print_validation_report(self, results: Dict):
        """Print formatted validation report"""
        print("\n" + "="*80)
        print("🔒 PRODUCTION SECURITY CONFIGURATION VALIDATION REPORT")
        print("="*80)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Status: {results['status']}")
        print(f"Environment File: {self.env_file}")
        print()
        
        # Print validation results by category
        for category, checks in results['validation_results'].items():
            print(f"📋 {category.replace('_', ' ').title()}:")
            for check, result in checks.items():
                print(f"   {check.replace('_', ' ').title()}: {result}")
            print()
        
        # Print summary
        summary = results['summary']
        print(f"📊 SUMMARY:")
        print(f"   Total Checks: {summary['total_checks']}")
        print(f"   Critical Issues: {summary['critical_issues_count']}")
        print(f"   Warnings: {summary['warnings_count']}")
        print()
        
        # Print recommendations
        if results['recommendations']:
            for recommendation in results['recommendations']:
                print(recommendation)
        
        print("="*80)

def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate production security configuration')
    parser.add_argument('--env-file', default='.env.prod', help='Environment file to validate')
    parser.add_argument('--output', help='Output file for JSON results')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    validator = SecurityConfigValidator(args.env_file)
    results = validator.run_validation()
    
    if not args.quiet:
        validator.print_validation_report(results)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    
    # Exit with appropriate code
    if results['status'] == 'CRITICAL_ISSUES':
        sys.exit(1)
    elif results['status'] == 'WARNINGS':
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()