#!/usr/bin/env python
import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QR_Attendance_System.settings')
django.setup()

from django.contrib.auth.models import User
from AdminPanel.models import UserProfile

def create_admin_user(username, email, password):
    """Create an admin user"""
    try:
        # Check if user exists
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            print(f"User {username} already exists. Updating to admin role.")
            # Update password in case it needs to be reset
            user.set_password(password)
            user.save()
        else:
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True  # Give admin users staff privileges
            )
            print(f"Created new user: {username}")
        
        # Create or get the profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.role = 'ADMIN'
        profile.save()
        
        print(f"User {username} has been set as an ADMIN")
        print(f"Login with username: {username} and the password you provided")
        return user
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python create_admin_user.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    create_admin_user(username, email, password) 