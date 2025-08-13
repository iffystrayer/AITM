"""
Configuration settings for AITM application
"""

import os
from functools import lru_cache
from typing import List, Optional, Union, Annotated

from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "AITM"
    environment: str = "development"
    log_level: str = "INFO"
    
    # Database
    database_url: str = "sqlite:///./aitm.db"
    
    # Ports
    backend_port: int = 38527
    frontend_port: int = 41241
    
    # Security
    jwt_secret_key: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # CORS  
    cors_origins: List[str] = [
        "http://localhost:41241",
        "http://127.0.0.1:41241", 
        "http://0.0.0.0:41241",
        "http://frontend:41241"
    ]
    
    # LLM Providers
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    litellm_base_url: str = "http://localhost:8000"
    litellm_api_key: Optional[str] = None
    default_llm_provider: str = "google"
    
    # Monitoring
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "aitm-development"
    langsmith_tracing: bool = True
    
    # MITRE ATT&CK
    mitre_attack_version: str = "14.1"
    mitre_attack_data_url: str = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 20
    
    # Threat Intelligence
    threat_intelligence_enabled: bool = True
    threat_feed_polling_interval: int = 300  # 5 minutes
    threat_correlation_threshold: float = 0.7
    threat_alert_threshold: float = 0.8
    threat_data_retention_days: int = 90
    max_indicators_per_feed: int = 100000
    
    # Threat Feed API Keys (optional)
    misp_url: Optional[str] = None
    misp_api_key: Optional[str] = None
    otx_api_key: Optional[str] = None
    virustotal_api_key: Optional[str] = None
    
    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        if isinstance(v, list):
            return v
        return []
    
    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, v):
        if not v or v == "your-super-secret-jwt-key-change-this-in-production":
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError("JWT_SECRET_KEY must be set in production")
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_parse_none_str": False,
        "env_parse_enums": False
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
