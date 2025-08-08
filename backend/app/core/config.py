"""
Configuration settings for AITM application
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, validator


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
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:41241",
        "http://127.0.0.1:41241"
    ]
    
    # LLM Providers
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    litellm_api_key: Optional[str] = None
    default_llm_provider: str = "google"
    
    # Monitoring
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "aitm-development"
    langsmith_tracing: bool = True
    
    # MITRE ATT&CK
    mitre_attack_version: str = "14.1"
    mitre_attack_data_url: str = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("jwt_secret_key")
    def validate_jwt_secret_key(cls, v):
        if not v or v == "your-super-secret-jwt-key-change-this-in-production":
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError("JWT_SECRET_KEY must be set in production")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
