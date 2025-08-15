"""
Configuration management for code quality standards and rules.
"""

import json
import sqlite3
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from app.models.quality import QualityStandard, SafetyLevel, FixType
import uuid


@dataclass
class QualityRuleConfig:
    """Configuration for a specific quality rule."""
    rule_id: str
    rule_name: str
    enabled: bool
    severity: str
    parameters: Dict[str, Any]
    description: str


@dataclass
class AutoFixConfig:
    """Configuration for automatic fixes."""
    enabled_fix_types: List[FixType]
    safety_level: SafetyLevel
    backup_enabled: bool
    rollback_timeout: int  # seconds
    excluded_patterns: List[str]
    max_fixes_per_run: int
    require_approval: bool


@dataclass
class QualityThresholds:
    """Quality metric thresholds."""
    min_coverage: float
    max_complexity: int
    min_maintainability: float
    max_technical_debt_ratio: float
    min_test_quality: float
    min_security_score: float
    max_duplicate_ratio: float


class QualityConfigManager:
    """Manages quality standards and configuration."""
    
    def __init__(self, db_path: str = "aitm.db"):
        self.db_path = db_path
        self._default_configs = self._load_default_configs()
    
    def _load_default_configs(self) -> Dict[str, Any]:
        """Load default quality configurations."""
        return {
            'python_style': {
                'max_line_length': 88,
                'max_complexity': 10,
                'naming_conventions': {
                    'function': 'snake_case',
                    'variable': 'snake_case',
                    'class': 'PascalCase',
                    'constant': 'UPPER_CASE'
                },
                'import_order': ['standard', 'third_party', 'local'],
                'docstring_style': 'google',
                'enforce_type_hints': True
            },
            'javascript_style': {
                'max_line_length': 100,
                'max_complexity': 10,
                'indent_size': 2,
                'quote_style': 'single',
                'semicolons': True,
                'trailing_commas': True
            },
            'quality_thresholds': {
                'min_coverage': 80.0,
                'max_complexity': 10,
                'min_maintainability': 70.0,
                'max_technical_debt_ratio': 0.05,
                'min_test_quality': 75.0,
                'min_security_score': 85.0,
                'max_duplicate_ratio': 0.03
            },
            'autofix_config': {
                'enabled_fix_types': ['formatting', 'imports', 'style'],
                'safety_level': 'conservative',
                'backup_enabled': True,
                'rollback_timeout': 3600,
                'excluded_patterns': ['*.min.js', '*.generated.*', 'migrations/*'],
                'max_fixes_per_run': 50,
                'require_approval': False
            },
            'security_rules': {
                'check_sql_injection': True,
                'check_xss_vulnerabilities': True,
                'check_hardcoded_secrets': True,
                'check_insecure_random': True,
                'check_weak_crypto': True
            },
            'performance_rules': {
                'check_n_plus_one_queries': True,
                'check_inefficient_loops': True,
                'check_memory_leaks': True,
                'check_blocking_operations': True
            }
        }
    
    def get_quality_standard(self, project_id: Optional[str] = None, 
                           standard_type: str = 'quality') -> Dict[str, Any]:
        """Get quality standard configuration for a project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # First try to get project-specific standard
            if project_id:
                cursor.execute("""
                    SELECT configuration FROM quality_standards 
                    WHERE project_id = ? AND standard_type = ? AND is_active = 1
                    ORDER BY updated_at DESC LIMIT 1
                """, (project_id, standard_type))
                result = cursor.fetchone()
                if result:
                    return json.loads(result[0])
            
            # Fall back to global standard
            cursor.execute("""
                SELECT configuration FROM quality_standards 
                WHERE project_id IS NULL AND standard_type = ? AND is_active = 1
                ORDER BY updated_at DESC LIMIT 1
            """, (standard_type,))
            result = cursor.fetchone()
            
            if result:
                return json.loads(result[0])
            
            # Fall back to default configuration
            return self._get_default_config(standard_type)
            
        finally:
            conn.close()
    
    def _get_default_config(self, standard_type: str) -> Dict[str, Any]:
        """Get default configuration for a standard type."""
        type_mapping = {
            'quality': 'quality_thresholds',
            'style': 'python_style',
            'autofix': 'autofix_config',
            'security': 'security_rules',
            'performance': 'performance_rules'
        }
        
        config_key = type_mapping.get(standard_type, 'quality_thresholds')
        return self._default_configs.get(config_key, {})
    
    def save_quality_standard(self, standard: QualityStandard) -> str:
        """Save a quality standard configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if not standard.id:
                standard.id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT OR REPLACE INTO quality_standards 
                (id, project_id, standard_name, standard_type, configuration, is_active, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                standard.id,
                standard.project_id,
                standard.standard_name,
                standard.standard_type,
                json.dumps(standard.configuration),
                standard.is_active
            ))
            
            conn.commit()
            return standard.id
            
        finally:
            conn.close()
    
    def get_autofix_config(self, project_id: Optional[str] = None) -> AutoFixConfig:
        """Get auto-fix configuration for a project."""
        config = self.get_quality_standard(project_id, 'autofix')
        
        return AutoFixConfig(
            enabled_fix_types=[FixType(ft) for ft in config.get('enabled_fix_types', ['formatting'])],
            safety_level=SafetyLevel(config.get('safety_level', 'conservative')),
            backup_enabled=config.get('backup_enabled', True),
            rollback_timeout=config.get('rollback_timeout', 3600),
            excluded_patterns=config.get('excluded_patterns', []),
            max_fixes_per_run=config.get('max_fixes_per_run', 50),
            require_approval=config.get('require_approval', False)
        )
    
    def get_quality_thresholds(self, project_id: Optional[str] = None) -> QualityThresholds:
        """Get quality thresholds for a project."""
        config = self.get_quality_standard(project_id, 'quality')
        
        return QualityThresholds(
            min_coverage=config.get('min_coverage', 80.0),
            max_complexity=config.get('max_complexity', 10),
            min_maintainability=config.get('min_maintainability', 70.0),
            max_technical_debt_ratio=config.get('max_technical_debt_ratio', 0.05),
            min_test_quality=config.get('min_test_quality', 75.0),
            min_security_score=config.get('min_security_score', 85.0),
            max_duplicate_ratio=config.get('max_duplicate_ratio', 0.03)
        )
    
    def get_style_config(self, project_id: Optional[str] = None, 
                        language: str = 'python') -> Dict[str, Any]:
        """Get style configuration for a specific language."""
        standard_type = f'{language}_style'
        return self.get_quality_standard(project_id, standard_type)
    
    def get_security_rules(self, project_id: Optional[str] = None) -> Dict[str, bool]:
        """Get security rules configuration."""
        return self.get_quality_standard(project_id, 'security')
    
    def get_performance_rules(self, project_id: Optional[str] = None) -> Dict[str, bool]:
        """Get performance rules configuration."""
        return self.get_quality_standard(project_id, 'performance')
    
    def list_quality_standards(self, project_id: Optional[str] = None) -> List[QualityStandard]:
        """List all quality standards for a project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if project_id:
                cursor.execute("""
                    SELECT id, project_id, standard_name, standard_type, configuration, is_active
                    FROM quality_standards 
                    WHERE project_id = ? OR project_id IS NULL
                    ORDER BY project_id, standard_type, updated_at DESC
                """, (project_id,))
            else:
                cursor.execute("""
                    SELECT id, project_id, standard_name, standard_type, configuration, is_active
                    FROM quality_standards 
                    WHERE project_id IS NULL
                    ORDER BY standard_type, updated_at DESC
                """)
            
            standards = []
            for row in cursor.fetchall():
                standards.append(QualityStandard(
                    id=row[0],
                    project_id=row[1],
                    standard_name=row[2],
                    standard_type=row[3],
                    configuration=json.loads(row[4]),
                    is_active=bool(row[5])
                ))
            
            return standards
            
        finally:
            conn.close()
    
    def update_quality_standard(self, standard_id: str, 
                              updates: Dict[str, Any]) -> bool:
        """Update a quality standard configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get current standard
            cursor.execute("""
                SELECT configuration FROM quality_standards WHERE id = ?
            """, (standard_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            current_config = json.loads(result[0])
            current_config.update(updates)
            
            cursor.execute("""
                UPDATE quality_standards 
                SET configuration = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (json.dumps(current_config), standard_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        finally:
            conn.close()
    
    def delete_quality_standard(self, standard_id: str) -> bool:
        """Delete a quality standard."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM quality_standards WHERE id = ?
            """, (standard_id,))
            
            conn.commit()
            return cursor.rowcount > 0
            
        finally:
            conn.close()
    
    def validate_configuration(self, config: Dict[str, Any], 
                             config_type: str) -> List[str]:
        """Validate a configuration against expected schema."""
        errors = []
        
        if config_type == 'quality':
            required_fields = ['min_coverage', 'max_complexity', 'min_maintainability']
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field: {field}")
                elif not isinstance(config[field], (int, float)):
                    errors.append(f"Field {field} must be a number")
        
        elif config_type == 'autofix':
            if 'enabled_fix_types' in config:
                valid_types = [ft.value for ft in FixType]
                for fix_type in config['enabled_fix_types']:
                    if fix_type not in valid_types:
                        errors.append(f"Invalid fix type: {fix_type}")
        
        return errors