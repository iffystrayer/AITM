#!/usr/bin/env python3
"""
Database migration script to create threat intelligence tables
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_db, engine
from app.models.threat_intelligence import (
    ThreatFeed, ThreatIndicator, ThreatRelationship, ThreatCorrelation,
    ThreatAlert, ThreatIntelligenceCache, ThreatIntelligenceMetrics
)


async def create_threat_intelligence_tables():
    """Create threat intelligence database tables"""
    try:
        print("Creating threat intelligence database tables...")
        
        # Initialize database with all models
        await init_db()
        
        print("✅ Threat intelligence tables created successfully!")
        
        # Verify tables were created
        from sqlalchemy import text
        async with engine.begin() as conn:
            # Check if tables exist by trying to query them
            tables_to_check = [
                "threat_feeds",
                "threat_indicators", 
                "threat_relationships",
                "threat_correlations",
                "threat_alerts",
                "threat_intelligence_cache",
                "threat_intelligence_metrics"
            ]
            
            for table_name in tables_to_check:
                try:
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    print(f"✅ Table '{table_name}' created successfully (current rows: {count})")
                except Exception as e:
                    print(f"❌ Error checking table '{table_name}': {e}")
        
        print("\n🎉 Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error creating threat intelligence tables: {e}")
        raise


async def seed_default_threat_feeds():
    """Seed database with default threat feed configurations"""
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.threat_intelligence import ThreatFeed
    from app.core.config import get_settings
    
    settings = get_settings()
    
    # Create async session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    default_feeds = [
        {
            "name": "MISP Default",
            "url": settings.misp_url or "https://misp.example.com",
            "format": "stix",
            "polling_interval": 3600,  # 1 hour
            "rate_limit": 100,
            "is_active": bool(settings.misp_api_key),
            "configuration": {
                "api_key_required": True,
                "supported_types": ["ioc", "malware", "campaign"],
                "description": "MISP Threat Intelligence Platform"
            }
        },
        {
            "name": "AlienVault OTX",
            "url": "https://otx.alienvault.com/api/v1",
            "format": "json",
            "polling_interval": 1800,  # 30 minutes
            "rate_limit": 1000,
            "is_active": bool(settings.otx_api_key),
            "configuration": {
                "api_key_required": True,
                "supported_types": ["ioc", "malware", "campaign", "threat_actor"],
                "description": "AlienVault Open Threat Exchange"
            }
        },
        {
            "name": "VirusTotal Intelligence",
            "url": "https://www.virustotal.com/vtapi/v2",
            "format": "json",
            "polling_interval": 3600,  # 1 hour
            "rate_limit": 4,  # Very limited for free tier
            "is_active": bool(settings.virustotal_api_key),
            "configuration": {
                "api_key_required": True,
                "supported_types": ["ioc", "malware"],
                "description": "VirusTotal Threat Intelligence"
            }
        }
    ]
    
    try:
        async with async_session() as session:
            # Check if feeds already exist
            from sqlalchemy import text
            existing_feeds = await session.execute(text("SELECT name FROM threat_feeds"))
            existing_names = {row[0] for row in existing_feeds.fetchall()}
            
            feeds_added = 0
            for feed_data in default_feeds:
                if feed_data["name"] not in existing_names:
                    feed = ThreatFeed(**feed_data)
                    session.add(feed)
                    feeds_added += 1
                    print(f"✅ Added default feed: {feed_data['name']}")
                else:
                    print(f"⏭️  Feed already exists: {feed_data['name']}")
            
            if feeds_added > 0:
                await session.commit()
                print(f"\n🎉 Added {feeds_added} default threat feeds!")
            else:
                print("\n✅ All default threat feeds already exist.")
                
    except Exception as e:
        print(f"❌ Error seeding default threat feeds: {e}")
        raise


async def main():
    """Main migration function"""
    print("🚀 Starting threat intelligence database migration...")
    
    try:
        # Create tables
        await create_threat_intelligence_tables()
        
        # Seed default feeds
        print("\n📡 Seeding default threat feeds...")
        await seed_default_threat_feeds()
        
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Configure threat feed API keys in your .env file:")
        print("   - MISP_API_KEY=your_misp_key")
        print("   - OTX_API_KEY=your_otx_key") 
        print("   - VIRUSTOTAL_API_KEY=your_vt_key")
        print("2. Start Redis server: redis-server")
        print("3. Start the threat intelligence ingestion service")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())