#!/usr/bin/env python3
"""
Test script to verify the permission dependency factories are working correctly.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_permission_dependencies():
    """Test that the permission dependency factories can be imported and used"""
    try:
        # Test imports
        from app.core.permissions import (
            require_project_access,
            require_project_modification, 
            require_project_deletion,
            can_access_project,
            can_modify_project,
            can_delete_project
        )
        
        print("✅ Successfully imported all permission dependency factories")
        
        # Test that the factories can be called
        access_dep = require_project_access(1)
        modify_dep = require_project_modification(1)
        delete_dep = require_project_deletion(1)
        
        print("✅ Successfully created dependency factory instances")
        
        # Test that the functions exist and are callable
        assert callable(can_access_project), "can_access_project should be callable"
        assert callable(can_modify_project), "can_modify_project should be callable"
        assert callable(can_delete_project), "can_delete_project should be callable"
        
        print("✅ All object-level permission functions are callable")
        
        # Test that the dependency factories return functions
        assert callable(access_dep), "require_project_access should return a callable dependency"
        assert callable(modify_dep), "require_project_modification should return a callable dependency"
        assert callable(delete_dep), "require_project_deletion should return a callable dependency"
        
        print("✅ All dependency factories return callable dependencies")
        
        print("\n🎉 All permission dependency tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_permission_dependencies())
    sys.exit(0 if success else 1)