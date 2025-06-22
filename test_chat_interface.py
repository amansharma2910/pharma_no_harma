#!/usr/bin/env python3
"""
Test script for the Chat Interface
Tests the integration between Streamlit chat interface and orchestrator agent
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_orchestrator_api():
    """Test the orchestrator API endpoints"""
    
    print("🧪 Testing Orchestrator API Integration")
    print("=" * 50)
    
    # Test 1: Check orchestrator status
    print("\n1. Testing Orchestrator Status...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/orchestrator/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Status: {status.get('status', 'unknown')}")
            print(f"✅ Available Tools: {status.get('available_tools', 0)}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status check error: {str(e)}")
    
    # Test 2: Get available tools
    print("\n2. Testing Available Tools...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/orchestrator/tools")
        if response.status_code == 200:
            tools = response.json()
            print(f"✅ Total Tools: {tools.get('total_tools', 0)}")
            for tool in tools.get('tools', []):
                print(f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
        else:
            print(f"❌ Tools check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Tools check error: {str(e)}")
    
    # Test 3: Get example queries
    print("\n3. Testing Example Queries...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/v1/orchestrator/examples")
        if response.status_code == 200:
            examples = response.json()
            print(f"✅ Total Categories: {examples.get('total_categories', 0)}")
            for category, queries in examples.get('examples', {}).items():
                print(f"   - {category}: {len(queries)} examples")
        else:
            print(f"❌ Examples check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Examples check error: {str(e)}")

def test_orchestrator_queries():
    """Test various orchestrator queries"""
    
    print("\n🧪 Testing Orchestrator Queries")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        {
            "query": "Give me my complete medical history report",
            "description": "Medical History Report"
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
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: {test_case['description']}")
        print(f"   Query: {test_case['query']}")
        
        try:
            payload = {
                "query": test_case["query"],
                "user_id": "test_user_123",
                "user_type": "PATIENT",
                "health_record_id": None
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/v1/orchestrator/query",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Response received")
                print(f"   ✅ Confidence: {result.get('confidence', 'N/A')}")
                print(f"   ✅ Response length: {len(result.get('response', ''))} characters")
                print(f"   ✅ Suggested actions: {len(result.get('suggested_actions', []))}")
            else:
                print(f"   ❌ Query failed: {response.status_code}")
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Query error: {str(e)}")

def test_chat_interface_simulation():
    """Simulate chat interface interactions"""
    
    print("\n🧪 Simulating Chat Interface")
    print("=" * 50)
    
    # Simulate a conversation
    conversation = [
        "Give me my complete medical history report",
        "What's my latest prescription?",
        "Search for diabetes-related records"
    ]
    
    print("Simulating a conversation with the AI assistant...")
    
    for i, query in enumerate(conversation, 1):
        print(f"\n--- Turn {i} ---")
        print(f"👤 User: {query}")
        
        try:
            payload = {
                "query": query,
                "user_id": "test_user_123",
                "user_type": "PATIENT"
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/v1/orchestrator/query",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', 'No response')
                
                # Truncate long responses for display
                if len(ai_response) > 200:
                    ai_response = ai_response[:200] + "..."
                
                print(f"🤖 AI: {ai_response}")
                print(f"   Confidence: {result.get('confidence', 'N/A')}")
            else:
                print(f"🤖 AI: ❌ Error - {response.status_code}")
                
        except Exception as e:
            print(f"🤖 AI: ❌ Error - {str(e)}")

def main():
    """Main test function"""
    print("🚀 Starting Chat Interface Tests")
    print("=" * 60)
    
    # Test API endpoints
    test_orchestrator_api()
    
    # Test queries
    test_orchestrator_queries()
    
    # Test chat simulation
    test_chat_interface_simulation()
    
    print("\n✅ All tests completed!")
    print("\n📝 To run the chat interface:")
    print("1. Ensure backend server is running: python run.py")
    print("2. Start chat interface: streamlit run streamlit_chat_interface.py")
    print("3. Open browser: http://localhost:8501")

if __name__ == "__main__":
    main()