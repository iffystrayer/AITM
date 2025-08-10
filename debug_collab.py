#!/usr/bin/env python3
"""
Debug collaboration service directly
"""

import asyncio
import sys
import os

# Change to backend directory so relative DB path works
os.chdir('/Users/ifiokmoses/code/AITM/backend')

# Add backend to path
sys.path.append('/Users/ifiokmoses/code/AITM/backend')

from app.core.database import get_db
from app.services.collaboration_service import CollaborationService
from app.models.collaboration import TeamCreate

async def test_create_team():
    """Test team creation directly"""
    
    # Get database session
    db_gen = get_db()
    db = await anext(db_gen)
    
    try:
        # Create service
        collab_service = CollaborationService()
        
        # Test data
        team_data = TeamCreate(
            name="Debug Test Team",
            description="Test team for debugging"
        )
        
        admin_user_id = "admin@aitm.com"  # Assuming admin user exists
        
        print("Creating team...")
        team = await collab_service.create_team(db, team_data, admin_user_id)
        await db.commit()
        
        print(f"Success! Team created: {team}")
        
    except Exception as e:
        print(f"Error creating team: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        await db.rollback()
        
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test_create_team())
