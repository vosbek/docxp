#!/usr/bin/env python3
"""
Test script to check what's available in strands-agents package
"""

import sys
import pkgutil

def test_strands_imports():
    """Test different import patterns for strands-agents"""
    
    print("🔍 Testing strands-agents imports...")
    
    # Test 1: Try to find the package
    try:
        import strands_agents
        print("✅ Found 'strands_agents' package")
        print(f"   Location: {strands_agents.__file__}")
        
        # List submodules
        for importer, modname, ispkg in pkgutil.iter_modules(strands_agents.__path__, strands_agents.__name__ + "."):
            print(f"   Submodule: {modname}")
            
    except ImportError as e:
        print(f"❌ 'strands_agents' not found: {e}")
    
    # Test 2: Try 'strands' directly
    try:
        import strands
        print("✅ Found 'strands' package")
        print(f"   Location: {strands.__file__}")
        
        # Try specific imports
        test_imports = [
            'strands.Agent',
            'strands.MessageFlow', 
            'strands.ConversationMemory',
            'strands.providers.bedrock.BedrockProvider',
            'strands.core.agent.AgentConfig'
        ]
        
        for import_path in test_imports:
            try:
                parts = import_path.split('.')
                module_path = '.'.join(parts[:-1])
                class_name = parts[-1]
                
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                print(f"   ✅ {import_path} - OK")
            except Exception as e:
                print(f"   ❌ {import_path} - {e}")
                
    except ImportError as e:
        print(f"❌ 'strands' not found: {e}")
    
    # Test 3: Check what's actually installed
    try:
        import pkg_resources
        installed_packages = [d.project_name for d in pkg_resources.working_set]
        strands_packages = [p for p in installed_packages if 'strands' in p.lower()]
        print(f"📦 Strands-related packages: {strands_packages}")
        
        # Get details for each
        for pkg_name in strands_packages:
            try:
                dist = pkg_resources.get_distribution(pkg_name)
                print(f"   {pkg_name}: version {dist.version}")
            except Exception as e:
                print(f"   {pkg_name}: error getting version - {e}")
                
    except Exception as e:
        print(f"❌ Error checking packages: {e}")

if __name__ == "__main__":
    test_strands_imports()