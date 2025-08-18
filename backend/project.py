#!/usr/bin/env python3
"""
Example: Create and Manage Projects with DocXP
Shows how to use the project coordinator service for enterprise modernization projects
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.project_coordinator_service import get_project_coordinator_service

async def create_modernization_project():
    """Create a sample modernization project"""
    
    print("🏗️ DocXP Project Management Example")
    print("="*50)
    
    try:
        # Get project coordinator service
        coordinator = await get_project_coordinator_service()
        
        print("📋 Creating example modernization project...")
        
        # Create a sample project
        project_id = await coordinator.create_project(
            name="Legacy Banking System Modernization",
            description="Modernize legacy Struts/CORBA banking application to Spring Boot/GraphQL",
            repository_ids=["banking-core", "banking-ui", "banking-services"],
            modernization_goals={
                "target_framework": "Spring Boot 3.x",
                "target_database": "PostgreSQL",
                "target_ui": "React + GraphQL",
                "target_integration": "REST APIs",
                "timeline": "12 months",
                "priority": "high"
            },
            business_sponsor="CTO",
            technical_lead="Senior Architect",
            created_by="DocXP User"
        )
        
        print(f"✅ Created modernization project: {project_id}")
        print()
        
        # Get project status
        print("📊 Fetching project status...")
        status = await coordinator.get_project_status(project_id)
        
        print("🎯 Project Details:")
        print(f"  Name: {status.get('name', 'Unknown')}")
        print(f"  Status: {status.get('status', 'unknown')}")
        print(f"  Progress: {status.get('progress_percentage', 0):.1f}%")
        
        repositories = status.get('repositories', {})
        print(f"  Repositories: {repositories.get('total', 0)} total")
        print(f"    - Analyzed: {repositories.get('analyzed', 0)}")
        print(f"    - In Progress: {repositories.get('in_progress', 0)}")
        print(f"    - Pending: {repositories.get('pending', 0)}")
        
        discoveries = status.get('discoveries', {})
        print(f"  Discoveries:")
        print(f"    - Business Rules: {discoveries.get('business_rules', 0)}")
        print(f"    - Insights: {discoveries.get('insights', 0)}")
        
        timeline = status.get('timeline', {})
        if timeline.get('planned_start'):
            print(f"  Timeline:")
            print(f"    - Planned Start: {timeline.get('planned_start', 'Not set')[:10]}")
            print(f"    - Planned End: {timeline.get('planned_end', 'Not set')[:10]}")
        
        print()
        print("✅ Project created and configured successfully!")
        
        return project_id
        
    except Exception as e:
        print(f"❌ Failed to create project: {str(e)}")
        print()
        print("Common issues:")
        print("  - Database connection issues")
        print("  - Invalid repository IDs")
        print("  - Insufficient permissions")
        return None

async def list_active_projects():
    """List all active projects"""
    
    print("📋 Listing Active Projects")
    print("-" * 30)
    
    try:
        coordinator = await get_project_coordinator_service()
        projects = await coordinator.list_active_projects()
        
        if not projects:
            print("No active projects found.")
            return
        
        for project in projects:
            print(f"📁 {project.get('name', 'Unnamed Project')}")
            print(f"   ID: {project.get('project_id', 'Unknown')}")
            print(f"   Status: {project.get('status', 'unknown')}")
            print(f"   Priority: {project.get('priority', 'medium')}")
            print(f"   Progress: {project.get('progress_percentage', 0):.1f}%")
            print(f"   Sponsor: {project.get('business_sponsor', 'Not assigned')}")
            print(f"   Lead: {project.get('technical_lead', 'Not assigned')}")
            print()
            
    except Exception as e:
        print(f"❌ Failed to list projects: {str(e)}")

async def interactive_project_demo():
    """Interactive project management demo"""
    
    print("🎯 Interactive Project Management Demo")
    print("="*50)
    
    while True:
        print("\nWhat would you like to do?")
        print("1. Create a new project")
        print("2. List active projects") 
        print("3. Get project status")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            print("\n" + "="*30)
            await create_modernization_project()
        elif choice == "2":
            print("\n" + "="*30)
            await list_active_projects()
        elif choice == "3":
            print("\n" + "="*30)
            project_id = input("Enter project ID: ").strip()
            if project_id:
                try:
                    coordinator = await get_project_coordinator_service()
                    status = await coordinator.get_project_status(project_id)
                    if status:
                        print(f"\n📊 Status for project: {project_id}")
                        print(f"Status: {status.get('status', 'unknown')}")
                        print(f"Progress: {status.get('progress_percentage', 0):.1f}%")
                    else:
                        print(f"❌ Project not found: {project_id}")
                except Exception as e:
                    print(f"❌ Error getting status: {str(e)}")
        elif choice == "4":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")

async def main():
    """Main function"""
    try:
        # Quick project creation example
        print("🚀 Quick Project Creation Example")
        print("="*40)
        project_id = await create_modernization_project()
        
        if project_id:
            print("\n" + "="*40)
            await list_active_projects()
            
            print("\n" + "="*40)
            print("🎉 Example completed successfully!")
            print()
            print("Next steps:")
            print("  1. Start project analysis")
            print("  2. Monitor progress")
            print("  3. Review discovered business rules")
            print("  4. Generate modernization insights")
            
            # Offer interactive mode
            print()
            interactive = input("Would you like to try interactive mode? (y/n): ").strip().lower()
            if interactive == 'y':
                await interactive_project_demo()
        
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("Please check your DocXP installation and try again.")

if __name__ == "__main__":
    # Example of how to run this script
    print("📋 DocXP Project Management Examples")
    print("="*40)
    print("This script demonstrates:")
    print("  - Creating modernization projects")
    print("  - Tracking project status") 
    print("  - Managing multiple repositories")
    print("  - Monitoring progress")
    print()
    
    asyncio.run(main())