#!/usr/bin/env python3
"""
Test script to verify the object-level permission functions work correctly
"""

import sys
sys.path.append('.')

from app.core.permissions import can_access_project, can_modify_project, can_delete_project, Permission, Role

# Create test user and project objects
class MockProject:
    def __init__(self, owner_user_id):
        self.owner_user_id = owner_user_id

class MockUser:
    def __init__(self, user_id, role, is_active=True):
        self.id = user_id
        self.role = role
        self.is_active = is_active

# Test scenarios
owner_user = MockUser('user1', Role.ANALYST.value)
other_user = MockUser('user2', Role.ANALYST.value)
admin_user = MockUser('admin1', Role.ADMIN.value)
viewer_user = MockUser('viewer1', Role.VIEWER.value)

project = MockProject('user1')

print('Testing can_access_project:')
print(f'Owner access: {can_access_project(owner_user, project)}')
print(f'Other user access: {can_access_project(other_user, project)}')
print(f'Admin access: {can_access_project(admin_user, project)}')
print(f'Viewer access: {can_access_project(viewer_user, project)}')

print('\nTesting can_modify_project:')
print(f'Owner modify: {can_modify_project(owner_user, project)}')
print(f'Other user modify: {can_modify_project(other_user, project)}')
print(f'Admin modify: {can_modify_project(admin_user, project)}')
print(f'Viewer modify: {can_modify_project(viewer_user, project)}')

print('\nTesting can_delete_project:')
print(f'Owner delete: {can_delete_project(owner_user, project)}')
print(f'Other user delete: {can_delete_project(other_user, project)}')
print(f'Admin delete: {can_delete_project(admin_user, project)}')
print(f'Viewer delete: {can_delete_project(viewer_user, project)}')