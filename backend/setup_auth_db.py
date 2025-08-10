#!/usr/bin/env python3
"""
Database setup script for AITM authentication system.

This script creates the necessary database tables for authentication
and creates a default admin user for initial system access.
"""

import asyncio
import sys
import os
import getpass
import argparse
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session, init_db
from app.services.user_service import UserService
from app.core.auth import AuthService
from app.models.user import UserCreate

async def create_admin_user(email=None, full_name=None, password=None, non_interactive=False):
    """Create the initial admin user for the system."""
    print("🔐 Setting up AITM Authentication System")
    print("=" * 50)
    
    # Initialize database
    print("📦 Initializing database...")
    await init_db()
    print("✅ Database initialized successfully")
    
    # Setup services
    auth_service = AuthService()
    user_service = UserService(auth_service)
    
    print("\n👤 Creating Initial Admin User")
    print("-" * 30)
    
    # Use provided values or get from user
    if not email:
        while True:
            email = input("Admin Email: ").strip()
            if email and "@" in email:
                break
            print("❌ Please enter a valid email address")
    
    if not full_name:
        full_name = input("Admin Full Name: ").strip() or "System Administrator"
    
    if not password:
        # Get secure password interactively
        while True:
            password = getpass.getpass("Admin Password: ")
            confirm_password = getpass.getpass("Confirm Password: ")
            
            if password != confirm_password:
                print("❌ Passwords do not match. Please try again.")
                continue
                
            if len(password) < 8:
                print("❌ Password must be at least 8 characters long")
                continue
                
            # Check password strength
            from app.core.auth import validate_password_strength
            if not validate_password_strength(password):
                print("❌ Password must contain:")
                print("   - At least one uppercase letter")
                print("   - At least one lowercase letter")
                print("   - At least one number")
                print("   - At least one special character")
                continue
                
            break
    
    # Validate provided password if given
    if password and len(password) >= 8:
        from app.core.auth import validate_password_strength
        if not validate_password_strength(password):
            print("❌ Provided password does not meet strength requirements")
            return
    
    # Create admin user
    async with async_session() as db:
        try:
            admin_user = UserCreate(
                email=email,
                password=password,
                full_name=full_name,
                is_active=True,
                is_superuser=True
            )
            
            # Check if admin already exists
            existing_admin = await user_service.get_user_by_email(db, email)
            if existing_admin:
                print(f"⚠️  Admin user with email {email} already exists!")
                if non_interactive:
                    # In non-interactive mode, always update
                    overwrite = 'y'
                    print("Running in non-interactive mode, updating existing user...")
                else:
                    overwrite = input("Do you want to update this user? (y/N): ").lower().strip()
                
                if overwrite == 'y':
                    # Update existing user to be admin
                    from app.models.user import UserUpdate
                    updated_admin = UserUpdate(
                        password=password,
                        full_name=full_name,
                        is_active=True,
                        is_superuser=True
                    )
                    user = await user_service.update_user(db, existing_admin.id, updated_admin)
                    await db.commit()
                    print(f"✅ Updated existing user {email} with admin privileges")
                else:
                    print("❌ Setup cancelled")
                    return
            else:
                user = await user_service.create_user(db, admin_user)
                await db.commit()
                print(f"✅ Created admin user: {email}")
            
            print("\n🎉 Authentication system setup complete!")
            print("\n🔐 Admin User Details:")
            print(f"   Email: {user.email}")
            print(f"   Name: {user.full_name}")
            print(f"   ID: {user.id}")
            print(f"   Admin: {'Yes' if user.is_superuser else 'No'}")
            print(f"   Active: {'Yes' if user.is_active else 'No'}")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error creating admin user: {e}")
            return

async def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description='Setup AITM authentication system')
    parser.add_argument('--email', help='Admin user email')
    parser.add_argument('--name', help='Admin user full name', default='System Administrator')
    parser.add_argument('--password', help='Admin user password')
    parser.add_argument('--non-interactive', action='store_true', help='Run in non-interactive mode')
    
    args = parser.parse_args()
    
    try:
        if args.non_interactive and not (args.email and args.password):
            print("❌ In non-interactive mode, --email and --password are required")
            sys.exit(1)
            
        await create_admin_user(
            email=args.email,
            full_name=args.name,
            password=args.password,
            non_interactive=args.non_interactive
        )
        
        print("\n🚀 Next Steps:")
        print("1. Start the backend server: python start_server.py")
        print("2. Test authentication at: http://localhost:38527/docs")
        print("3. Use the admin credentials to log in")
        print("4. Create additional users through the API or admin interface")
        
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
