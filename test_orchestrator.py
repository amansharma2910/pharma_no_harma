#!/usr/bin/env python3
"""
Test script for the Orchestrator Agent
Demonstrates the agentic architecture with example queries
"""

import asyncio
import json
from datetime import datetime
from app.services.orchestrator_agent import orchestrator_agent
from app.models.schemas import AgentQuery, UserType

async def test_orchestrator_agent():
    """Test the orchestrator agent with various queries"""
    
    print("🤖 Testing Orchestrator Agent")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        {
            "query": "Give me my complete medical history report",
            "description": "Complete Medical History Report"
        },
        {
            "query": "What's my latest prescription?",
            "description": "Latest Prescription"
        },
        {
            "query": "Search for diabetes-related records",
            "description": "Search Records"
        },
        {
            "query": "Generate a summary of my health record",
            "description": "Health Summary"
        },
        {
            "query": "What medications am I currently taking?",
            "description": "Current Medications"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n📋 Test {i}: {test_case['description']}")
        print("-" * 30)
        print(f"Query: {test_case['query']}")
        
        # Create agent query
        agent_query = AgentQuery(
            query=test_case['query'],
            user_id="test_user_123",
            user_type=UserType.PATIENT,
            health_record_id=None
        )
        
        try:
            # Process query
            start_time = datetime.now()
            response = await orchestrator_agent.process_query(agent_query)
            end_time = datetime.now()
            
            # Display results
            print(f"⏱️  Processing time: {(end_time - start_time).total_seconds():.2f}s")
            print(f"🎯 Confidence: {response.confidence}")
            print(f"📊 Sources: {', '.join(response.sources)}")
            print(f"🔧 Suggested Actions: {', '.join(response.suggested_actions)}")
            print(f"💬 Response:\n{response.response}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("\n" + "=" * 50)

async def test_tools_info():
    """Test getting tools information"""
    print("\n🔧 Available Tools Information")
    print("=" * 50)
    
    try:
        tools_info = []
        for tool in orchestrator_agent.tools:
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.args_schema.schema() if hasattr(tool, 'args_schema') else {}
            })
        
        print(f"Total tools available: {len(tools_info)}")
        for tool in tools_info:
            print(f"\n📌 {tool['name']}")
            print(f"   Description: {tool['description']}")
            if tool['parameters']:
                print(f"   Parameters: {json.dumps(tool['parameters'], indent=2)}")
                
    except Exception as e:
        print(f"❌ Error getting tools info: {str(e)}")

async def test_workflow_steps():
    """Test individual workflow steps"""
    print("\n🔄 Testing Workflow Steps")
    print("=" * 50)
    
    # Test intent analysis
    test_query = "Give me my complete medical history report"
    print(f"Testing intent analysis for: '{test_query}'")
    
    try:
        # Create initial state
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
        
    except Exception as e:
        print(f"❌ Error testing workflow steps: {str(e)}")

async def main():
    """Main test function"""
    print("🚀 Starting Orchestrator Agent Tests")
    print("=" * 60)
    
    # Test tools information
    await test_tools_info()
    
    # Test workflow steps
    await test_workflow_steps()
    
    # Test full orchestrator agent
    await test_orchestrator_agent()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(main()) 