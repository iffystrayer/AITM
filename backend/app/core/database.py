"""
Database configuration and models
"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

from app.core.config import get_settings

settings = get_settings()

# Create async engine for SQLite
if settings.database_url.startswith("sqlite"):
    # Convert to async SQLite URL
    async_database_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    async_database_url = settings.database_url

engine = create_async_engine(async_database_url, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


class Project(Base):
    """Threat modeling project"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="created")  # created, analyzing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    system_inputs = relationship("SystemInput", back_populates="project")
    assets = relationship("Asset", back_populates="project")
    attack_paths = relationship("AttackPath", back_populates="project")
    recommendations = relationship("Recommendation", back_populates="project")
    analysis_state = relationship("AnalysisState", back_populates="project", uselist=False)
    analysis_results = relationship("AnalysisResults", back_populates="project", uselist=False)


class SystemInput(Base):
    """System input data for threat modeling"""
    __tablename__ = "system_inputs"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    input_type = Column(String(50))  # text, json, file
    content = Column(Text)
    filename = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="system_inputs")


class Asset(Base):
    """Identified system assets"""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(255), nullable=False)
    asset_type = Column(String(100))  # server, database, application, etc.
    criticality = Column(String(50))  # high, medium, low
    description = Column(Text)
    technologies = Column(Text)  # JSON string of technologies
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="assets")


class AttackPath(Base):
    """Identified attack paths"""
    __tablename__ = "attack_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(255), nullable=False)
    techniques = Column(Text)  # JSON string of MITRE ATT&CK technique IDs
    priority_score = Column(Float, default=0.5)
    explanation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="attack_paths")


class Recommendation(Base):
    """Security recommendations"""
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(String(50))  # high, medium, low
    attack_technique = Column(String(50))  # MITRE ATT&CK technique ID
    status = Column(String(50), default="proposed")  # proposed, accepted, implemented
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="recommendations")


class AnalysisState(Base):
    """Analysis state tracking for threat modeling projects"""
    __tablename__ = "analysis_states"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), unique=True)
    status = Column(String(50), default="idle")  # idle, running, completed, failed
    current_phase = Column(String(100))  # system_analysis, attack_mapping, control_evaluation, report_generation
    progress_percentage = Column(Float, default=0.0)
    progress_message = Column(String(500))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    configuration = Column(Text)  # JSON string of analysis configuration
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="analysis_state")


class AnalysisResults(Base):
    """Analysis results for threat modeling projects"""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), unique=True)
    overall_risk_score = Column(Float)
    confidence_score = Column(Float)
    executive_summary = Column(Text)  # JSON string
    system_analysis_results = Column(Text)  # JSON string
    identified_techniques = Column(Text)  # JSON string
    attack_paths_data = Column(Text)  # JSON string
    control_evaluation_results = Column(Text)  # JSON string
    recommendations_data = Column(Text)  # JSON string
    full_report = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="analysis_results")


class MitreAttack(Base):
    """MITRE ATT&CK framework data"""
    __tablename__ = "mitre_attack"
    
    id = Column(Integer, primary_key=True, index=True)
    technique_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    tactic = Column(String(100))
    description = Column(Text)
    platforms = Column(Text)  # JSON string
    data_sources = Column(Text)  # JSON string
    mitigations = Column(Text)  # JSON string
    updated_at = Column(DateTime, default=datetime.utcnow)


async def get_db():
    """Get database session"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
