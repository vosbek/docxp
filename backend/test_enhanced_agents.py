#!/usr/bin/env python3
"""
Test script for enhanced Strands Agents with business rule context integration
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

async def test_enhanced_agents():
    """Test enhanced Strands Agents integration"""
    try:
        from app.services.strands_agent_service import get_strands_agent_service, AgentType
        
        print("Testing Enhanced Strands Agents Integration")
        print("=" * 60)
        
        # Get service
        strands_service = await get_strands_agent_service()
        
        # Test service health
        health = await strands_service.get_service_health()
        print(f"Service Health: {health['service_available']}")
        print(f"  - Strands installed: {health['strands_installed']}")
        print(f"  - Active conversations: {health['active_conversations']}")
        print(f"  - Project coordinator: {health['dependencies']['project_coordinator_service']}")
        print(f"  - Cross-repo discovery: {health['dependencies']['cross_repo_discovery_service']}")
        print(f"  - Business rule cache: {health['business_rule_cache_entries']}")
        print()
        
        # Test enhanced conversation with business rule context
        print("Starting Enhanced Conversation Test")
        print("-" * 40)
        
        context = {
            "repository_ids": ["1", "2"],
            "project_id": "test_project_001",
            "user_expertise_level": "expert",
            "user_preferences": {
                "technical_depth": "detailed",
                "focus_area": "migration_strategy"
            }
        }
        
        response = await strands_service.start_conversation(
            message="I need help analyzing business rules in our legacy Struts application for migration to Spring Boot",
            agent_type=AgentType.MIGRATION_EXPERT,
            context=context
        )
        
        print("Conversation started successfully")
        print(f"  - Agent: {response.agent_type.value}")
        print(f"  - Confidence: {response.confidence}")
        print(f"  - Session ID: {response.metadata.get('session_id', 'N/A')}")
        print(f"  - Response length: {len(response.content)} characters")
        print(f"  - Suggested actions: {len(response.suggested_actions)}")
        print(f"  - Followup questions: {len(response.followup_questions)}")
        print()
        
        # Test conversation context
        session_id = response.metadata.get('session_id')
        if session_id:
            conv_context = await strands_service.get_conversation_history(session_id)
            if conv_context:
                print("Conversation Context Details:")
                print(f"  - Business rules loaded: {len(conv_context.business_rules_context)}")
                print(f"  - Architectural insights: {len(conv_context.architectural_insights_context)}")
                print(f"  - Conversation focus: {conv_context.conversation_focus}")
                print(f"  - User expertise: {conv_context.user_expertise_level}")
                print(f"  - Tags: {', '.join(conv_context.conversation_tags[:3]) if conv_context.conversation_tags else 'None'}")
                print()
        
        # Test available agents
        agents = await strands_service.get_available_agents()
        print(f"Available Agents: {len(agents)}")
        for agent_id, info in agents.items():
            status = "Available" if info["available"] else "Unavailable"
            print(f"  - {info['name']}: {status}")
        print()
        
        print("Enhanced Strands Agents integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner"""
    success = await test_enhanced_agents()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)