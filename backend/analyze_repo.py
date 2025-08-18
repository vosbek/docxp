#!/usr/bin/env python3
"""
Example: Analyze a Repository with DocXP
Shows how to use the repository analysis worker to analyze a local repository
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.workers.repository_analysis_worker import analyze_repository

async def analyze_my_repo():
    """Analyze a local repository using DocXP"""
    
    print("🔍 DocXP Repository Analysis Example")
    print("="*50)
    
    # Get repository path from user
    default_path = "/path/to/your/legacy/repository"
    repo_path = input(f"Enter repository path (default: {default_path}): ").strip()
    
    if not repo_path:
        repo_path = default_path
    
    # Check if path exists
    if not os.path.exists(repo_path):
        print(f"❌ Path does not exist: {repo_path}")
        print("Please provide a valid repository path.")
        return
    
    print(f"📁 Analyzing repository: {repo_path}")
    print("⏳ This may take a few minutes for large repositories...")
    print()
    
    try:
        # Run the analysis
        result = await analyze_repository(
            repository_id="example-repo",
            project_id="example-project",
            analysis_type="full",
            local_path=repo_path
        )
        
        # Display results
        print("📊 Analysis Results:")
        print(f"  Status: {result['status']}")
        print(f"  Files Analyzed: {result.get('files_analyzed', 0)}")
        print(f"  Business Rules Discovered: {result.get('business_rules_discovered', 0)}")
        print(f"  Insights Generated: {result.get('insights_generated', 0)}")
        
        if result.get('errors'):
            print(f"  Errors: {len(result['errors'])}")
            for error in result['errors'][:3]:  # Show first 3 errors
                print(f"    - {error}")
        
        if result.get('warnings'):
            print(f"  Warnings: {len(result['warnings'])}")
        
        print()
        
        if result['status'] == 'completed':
            print("✅ Analysis completed successfully!")
            print()
            print("Next steps:")
            print("  1. Review the discovered business rules")
            print("  2. Examine architectural insights")
            print("  3. Use the conversational AI to explore findings")
        else:
            print("⚠️ Analysis completed with issues. Check the errors above.")
            
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        print()
        print("Common issues:")
        print("  - Repository path is invalid")
        print("  - Insufficient permissions")
        print("  - Repository contains unsupported file types")

async def main():
    """Main function"""
    try:
        await analyze_my_repo()
    except KeyboardInterrupt:
        print("\n⚠️ Analysis cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("Please check your DocXP installation and try again.")

if __name__ == "__main__":
    # Example of how to run this script
    print("📋 Example Usage:")
    print("  python analyze_repo.py")
    print()
    print("📝 Example repository paths:")
    print("  - ./test_repository")
    print("  - /home/user/projects/legacy-banking")
    print("  - C:\\\\Projects\\\\LegacyApp")
    print()
    
    asyncio.run(main())