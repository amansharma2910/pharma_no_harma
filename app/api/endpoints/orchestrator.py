from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, Optional
from app.services.orchestrator_agent import orchestrator_agent
from app.models.schemas import AgentQuery, AgentResponse, UserType, AuditAction
from app.services.audit_service import audit_service
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/orchestrator/query", response_model=AgentResponse)
async def process_natural_language_query(query: AgentQuery, request: Request):
    """
    Process natural language queries through the orchestrator agent.
    
    The orchestrator will:
    1. Analyze the user's intent
    2. Select appropriate tools/agents
    3. Execute the workflow
    4. Return a comprehensive response
    
    Example queries:
    - "Give me my complete medical history report"
    - "What's my latest prescription?"
    - "Search for diabetes-related records"
    - "Generate a summary of my health record"
    """
    try:
        # Log the query for audit
        await audit_service.log_action(
            user_id=query.user_id,
            user_name=f"User {query.user_id}",
            action=AuditAction.READ,
            resource_type="agent_query",
            resource_id=f"query_{query.user_id}_{query.query[:50]}",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={"query": query.query, "user_type": query.user_type.value}
        )
        
        # Process through orchestrator agent
        response = await orchestrator_agent.process_query(query)
        
        # Log the response for audit
        await audit_service.log_action(
            user_id=query.user_id,
            user_name=f"User {query.user_id}",
            action=AuditAction.CREATE,
            resource_type="agent_response",
            resource_id=f"response_{query.user_id}_{query.query[:50]}",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={
                "confidence": response.confidence,
                "sources": response.sources,
                "suggested_actions": response.suggested_actions
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Orchestrator query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.get("/orchestrator/tools")
async def get_available_tools():
    """Get list of available tools that the orchestrator can use"""
    try:
        tools_info = []
        for tool_name, tool_func in orchestrator_agent.tools.items():
            tools_info.append({
                "name": tool_name,
                "description": tool_func.description if hasattr(tool_func, 'description') else "No description available",
                "parameters": tool_func.args_schema.schema() if hasattr(tool_func, 'args_schema') else {}
            })
        
        return {
            "success": True,
            "tools": tools_info,
            "total_tools": len(tools_info)
        }
    except Exception as e:
        logger.error(f"Error getting tools info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tools info: {str(e)}")

@router.get("/orchestrator/status")
async def get_orchestrator_status():
    """Get the status of the orchestrator agent"""
    try:
        return {
            "status": "healthy",
            "agent_type": "orchestrator",
            "framework": "langgraph",
            "available_tools": len(orchestrator_agent.tools),
            "memory_enabled": True,
            "timestamp": orchestrator_agent.memory is not None
        }
    except Exception as e:
        logger.error(f"Error getting orchestrator status: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/orchestrator/examples")
async def get_query_examples():
    """Get example queries that users can ask"""
    examples = {
        "medical_history": [
            "Give me my complete medical history report",
            "Show me all my health records",
            "Generate a comprehensive medical history",
            "What's my medical background?"
        ],
        "prescriptions": [
            "What's my latest prescription?",
            "Show me my current medications",
            "Get my most recent medicine prescription",
            "What medications am I currently taking?"
        ],
        "search": [
            "Search for diabetes-related records",
            "Find all records about my heart condition",
            "Look for blood test results",
            "Search for appointment records"
        ],
        "summaries": [
            "Generate a summary of my health record",
            "Give me an overview of my medical condition",
            "Summarize my latest health checkup",
            "Create a summary of my treatment plan"
        ],
        "specific_queries": [
            "What were my blood pressure readings?",
            "Show me my vaccination records",
            "What was my last diagnosis?",
            "When was my last appointment?"
        ]
    }
    
    return {
        "success": True,
        "examples": examples,
        "total_categories": len(examples)
    } 