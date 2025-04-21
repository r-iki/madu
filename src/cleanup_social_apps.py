"""
Cleanup script for removing duplicate social applications
Usage: python manage.py runscript cleanup_social_apps
"""

import os
import django
from django.db import transaction

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Import after Django setup
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


def run():
    # List all social apps to see duplicates
    print("Current social applications:")
    apps = SocialApp.objects.all()
    for app in apps:
        sites = ", ".join([site.domain for site in app.sites.all()])
        print(f"- ID: {app.id}, Provider: {app.provider}, Name: {app.name}, Sites: {sites}")
    
    # Find duplicates by provider
    providers = {}
    duplicates = []
    
    for app in apps:
        if app.provider not in providers:
            providers[app.provider] = app
        else:
            # Mark as duplicate
            duplicates.append(app)
    
    if duplicates:
        print("\nFound duplicate applications:")
        for app in duplicates:
            print(f"- ID: {app.id}, Provider: {app.provider}, Name: {app.name}")
        
        # Ask for confirmation
        confirm = input("\nDo you want to remove these duplicate applications? (yes/no): ")
        if confirm.lower() == "yes":
            with transaction.atomic():
                for app in duplicates:
                    print(f"Deleting app ID: {app.id}, Provider: {app.provider}")
                    app.delete()
                print("Duplicate applications removed successfully.")
        else:
            print("No changes were made.")
    else:
        print("\nNo duplicate applications found.")
    
    # Make sure there's a Site with ID=1
    try:
        site = Site.objects.get(id=1)
        print(f"\nSite ID=1 exists: {site.domain}")
    except Site.DoesNotExist:
        print("\nSite ID=1 does not exist. Creating...")
        Site.objects.create(id=1, domain='localhost:8000', name='localhost')
        print("Created Site ID=1 (localhost:8000)")


if __name__ == "__main__":
    run()