#!/usr/bin/env python3
"""
Database migration script for collaboration features.

This script updates the existing database to include collaboration tables
and adds owner_user_id to existing projects.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import async_session, init_db
from app.core.database import Project
from sqlalchemy import text


async def migrate_database():
    """Migrate database for collaboration features"""
    print("🔄 Migrating database for collaboration features...")
    print("=" * 50)
    
    try:
        async with async_session() as db:
            # First, check if owner_user_id column exists
            print("🔍 Checking existing database schema...")
            result = await db.execute(text("PRAGMA table_info(projects)"))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            
            has_owner_column = 'owner_user_id' in column_names
            print(f"   Projects table has owner_user_id column: {has_owner_column}")
            
            # Get admin user for default ownership
            admin_user = None
            result = await db.execute(text("SELECT id FROM users WHERE is_superuser = 1 LIMIT 1"))
            admin_user_row = result.scalar_one_or_none()
            if admin_user_row:
                admin_user = admin_user_row
                print(f"   Found admin user: {admin_user}")
            
            # Add owner_user_id column if it doesn't exist
            if not has_owner_column:
                print("➕ Adding owner_user_id column to projects table...")
                if admin_user:
                    # Add column with default value as admin user
                    await db.execute(text(f"ALTER TABLE projects ADD COLUMN owner_user_id TEXT DEFAULT '{admin_user}'"))
                else:
                    # Add column without default (will be NULL)
                    await db.execute(text("ALTER TABLE projects ADD COLUMN owner_user_id TEXT"))
                await db.commit()
                print("✅ Added owner_user_id column to projects table")
            else:
                print("   owner_user_id column already exists")
            
        # Now initialize database with new tables
        print("\n📦 Creating new collaboration tables...")
        await init_db()
        print("✅ Database tables created/updated successfully")
        
        # Update existing projects that don't have owner_user_id set
        if admin_user:
            print("\n👤 Updating projects without owner...")
            async with async_session() as db:
                result = await db.execute(text("""
                    UPDATE projects 
                    SET owner_user_id = :admin_id 
                    WHERE owner_user_id IS NULL OR owner_user_id = ''
                """), {"admin_id": admin_user})
                
                updated_count = result.rowcount
                await db.commit()
                
                if updated_count > 0:
                    print(f"✅ Updated {updated_count} projects with default owner")
                else:
                    print("   All projects already have owners assigned")
        else:
            print("\n⚠️  No admin user found. Please create one first using setup_auth_db.py")
            print("   Existing projects will need owner assignment later")
        
        print("\n🎉 Collaboration features migration completed!")
        print("\n🚀 Available Features:")
        print("   • Team management")
        print("   • Project sharing with users/teams") 
        print("   • Role-based access control")
        print("   • Comments and discussions")
        print("   • Activity tracking and feeds")
        print("   • Real-time collaboration")
        
        print("\n📖 API Endpoints:")
        print("   • POST /api/v1/collaboration/teams - Create team")
        print("   • GET /api/v1/collaboration/teams - List user teams")
        print("   • POST /api/v1/collaboration/projects/{id}/share - Share project")
        print("   • POST /api/v1/collaboration/projects/{id}/comments - Add comment")
        print("   • GET /api/v1/collaboration/activity - Get activity feed")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(migrate_database())
