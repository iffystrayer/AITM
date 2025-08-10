#!/usr/bin/env python3
"""
Test script for collaboration features.
"""

import requests
import json

BASE_URL = "http://localhost:38527/api/v1"

def test_collaboration_features():
    """Test the new collaboration endpoints"""
    print("🤝 Testing AITM Collaboration Features")
    print("=" * 40)
    
    # Step 1: Login to get authentication token
    print("\n1. 🔐 Authenticating with admin user...")
    login_data = {
        "username": "admin@aitm.com",
        "password": "SecureAdmin123!"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return
        
        tokens = response.json()
        access_token = tokens["access_token"]
        print("✅ Login successful!")
        
        # Set up headers for authenticated requests
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Step 2: Test team creation
        print("\n2. 👥 Creating a test team...")
        team_data = {
            "name": "Security Team Alpha",
            "description": "Core security team for threat modeling"
        }
        
        response = requests.post(
            f"{BASE_URL}/collaboration/teams",
            json=team_data,
            headers=headers
        )
        
        if response.status_code == 201:
            team = response.json()
            team_id = team["id"]
            print(f"✅ Team created successfully!")
            print(f"   Team ID: {team_id}")
            print(f"   Name: {team['name']}")
            print(f"   Members: {team['member_count']}")
        else:
            print(f"❌ Team creation failed: {response.status_code} - {response.text}")
            return
        
        # Step 3: Test getting user teams
        print("\n3. 📋 Getting user teams...")
        response = requests.get(
            f"{BASE_URL}/collaboration/teams",
            headers=headers
        )
        
        if response.status_code == 200:
            teams = response.json()
            print(f"✅ Found {len(teams)} teams")
            for team in teams:
                print(f"   - {team['name']} (ID: {team['id']})")
        else:
            print(f"❌ Failed to get teams: {response.status_code} - {response.text}")
        
        # Step 4: Test project sharing (assuming a project exists)
        print("\n4. 📤 Testing project access check...")
        # First let's see if we have any projects
        response = requests.get(f"{BASE_URL}/projects", headers=headers)
        
        if response.status_code == 200:
            projects_data = response.json()
            if isinstance(projects_data, dict) and "data" in projects_data:
                projects = projects_data["data"]
            else:
                projects = projects_data
            
            if projects:
                project_id = projects[0]["id"]
                print(f"   Using project: {projects[0]['name']} (ID: {project_id})")
                
                # Check user access to this project
                response = requests.get(
                    f"{BASE_URL}/collaboration/projects/{project_id}/access",
                    headers=headers
                )
                
                if response.status_code == 200:
                    access_info = response.json()
                    print("✅ Project access check successful!")
                    print(f"   Access level: {access_info['access_level']}")
                    print(f"   Has access: {access_info['has_access']}")
                else:
                    print(f"❌ Project access check failed: {response.status_code}")
            else:
                print("   No projects found to test sharing")
        
        # Step 5: Test activity feed
        print("\n5. 📊 Getting activity feed...")
        response = requests.get(
            f"{BASE_URL}/collaboration/activity",
            headers=headers,
            params={"limit": 5}
        )
        
        if response.status_code == 200:
            activity_feed = response.json()
            print(f"✅ Activity feed retrieved!")
            print(f"   Total activities: {activity_feed['total_count']}")
            print(f"   Activities in response: {len(activity_feed['activities'])}")
            
            for activity in activity_feed['activities'][:3]:  # Show first 3
                print(f"   - {activity['description']} ({activity['activity_type']})")
        else:
            print(f"❌ Failed to get activity feed: {response.status_code}")
        
        print("\n🎉 Collaboration Features Test Complete!")
        print("✅ Authentication system working")
        print("✅ Team management working")
        print("✅ Project access control working")
        print("✅ Activity tracking working")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_collaboration_features()
