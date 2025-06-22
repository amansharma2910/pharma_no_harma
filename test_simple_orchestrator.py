#!/usr/bin/env python3
"""
Simple test script for the Orchestrator Agent
Tests basic functionality without complex workflows
"""

import asyncio
from app.services.orchestrator_agent import orchestrator_agent
from app.models.schemas import AgentQuery, UserType

async def test_simple_orchestrator():
    """Test basic orchestrator functionality"""
    
    print("🤖 Testing Simple Orchestrator Agent")
    print("=" * 50)
    
    # Test query
    test_query = "Give me my complete medical history report"
    print(f"Query: {test_query}")
    
    # Create agent query
    agent_query = AgentQuery(
        query=test_query,
        user_id="test_user_123",
        user_type=UserType.PATIENT,
        health_record_id=None
    )
    
    try:
        # Test tools info
        print(f"\n🔧 Available tools: {list(orchestrator_agent.tools.keys())}")
        
        # Test intent analysis
        from app.services.orchestrator_agent import AgentState
        
        initial_state = AgentState(
            user_query=test_query,
            user_id="test_user_123",
            user_type=UserType.PATIENT
        )
        
        # Test intent analysis
        state_after_intent = await orchestrator_agent._analyze_intent(initial_state)
        print(f"✅ Intent detected: {state_after_intent.intent}")
        
        # Test tool selection
        state_after_tools = await orchestrator_agent._select_tools(state_after_intent)
        print(f"✅ Tools selected: {state_after_tools.tools_to_call}")
        
        print("\n✅ Basic functionality tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_orchestrator()) 