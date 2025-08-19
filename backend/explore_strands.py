#!/usr/bin/env python3
"""
Explore the actual strands package structure and find all available components
"""

import strands
import inspect
import pkgutil
import sys
from pathlib import Path

def explore_strands():
    print("Package: Exploring strands package structure...")
    print(f"Package location: {strands.__file__}")
    print(f"Package path: {strands.__path__}")
    
    # List all attributes in the strands module
    print("\nAvailable attributes in strands:")
    for name in dir(strands):
        if not name.startswith('_'):
            attr = getattr(strands, name)
            attr_type = type(attr).__name__
            print(f"  {name}: {attr_type}")
            
            # If it's a class, show its methods
            if inspect.isclass(attr):
                methods = [m for m in dir(attr) if not m.startswith('_')]
                print(f"    Methods: {methods}")
    
    # Explore submodules
    print("\nExploring submodules...")
    try:
        for importer, modname, ispkg in pkgutil.walk_packages(strands.__path__, strands.__name__ + "."):
            print(f"  Module: {modname} (package: {ispkg})")
            
            # Try to import each submodule
            try:
                submodule = __import__(modname, fromlist=[''])
                submodule_attrs = [name for name in dir(submodule) if not name.startswith('_')]
                if submodule_attrs:
                    print(f"    Attributes: {submodule_attrs}")
            except Exception as e:
                print(f"    Error: Could not import {modname}: {e}")
    except Exception as e:
        print(f"Error exploring submodules: {e}")
    
    # Try to import specific classes that exist
    try:
        agent = strands.Agent
        print(f"\nAgent class: {agent}")
        print(f"   Agent methods: {[m for m in dir(agent) if not m.startswith('_')]}")
        
        # Try to create an instance to see what's needed
        try:
            # Check constructor signature
            sig = inspect.signature(agent.__init__)
            print(f"   Agent constructor: {sig}")
        except Exception as e:
            print(f"   Could not get constructor signature: {e}")
            
    except Exception as e:
        print(f"Error exploring Agent: {e}")

    # Check if there are alternative ways to access the needed classes
    print("\nLooking for alternative import paths...")
    
    # Common class names we're looking for
    target_classes = [
        'MessageFlow', 'ConversationMemory', 'BedrockProvider', 
        'AnthropicProvider', 'AgentConfig', 'Message', 'MessageType', 
        'Tool', 'ToolResult'
    ]
    
    for class_name in target_classes:
        found = False
        # Check if available directly in strands
        if hasattr(strands, class_name):
            print(f"  Found: {class_name} found in strands")
            found = True
        
        # Check submodules
        if not found:
            try:
                for importer, modname, ispkg in pkgutil.walk_packages(strands.__path__, strands.__name__ + "."):
                    try:
                        submodule = __import__(modname, fromlist=[''])
                        if hasattr(submodule, class_name):
                            print(f"  Found: {class_name} found in {modname}")
                            found = True
                            break
                    except:
                        continue
            except:
                pass
        
        if not found:
            print(f"  Missing: {class_name} not found anywhere")

if __name__ == "__main__":
    explore_strands()