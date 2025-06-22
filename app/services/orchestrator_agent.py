import logging
from typing import Dict, Any, Optional, List, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
import json
import asyncio
from datetime import datetime, date

from app.models.schemas import (
    AgentQuery, AgentResponse, SummaryRequest, SummaryResponse, SummaryType,
    UserType, HealthRecordResponse, FileResponse, Medication
)
from app.services.neo4j_service import neo4j_service
from app.services.agent_service import agent_service
from app.services.file_service import file_service
from app.services.audit_service import audit_service
from app.core.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# STATE MANAGEMENT
# =============================================================================

class AgentState(BaseModel):
    """State for the orchestrator agent"""
    user_query: str
    user_id: str
    user_type: UserType
    health_record_id: Optional[str] = None
    intent: Optional[str] = None
    tools_to_call: List[str] = Field(default_factory=list)
    tool_results: Dict[str, Any] = Field(default_factory=dict)
    final_response: Optional[str] = None
    confidence: float = 0.0
    sources: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

@tool
async def get_medical_history_report(user_id: str, date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
    """Generate a complete medical history report for a patient"""
    try:
        # Get all health records for the patient
        filters = {"patient_id": user_id}
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
            
        health_records = await neo4j_service.list_health_records(filters, skip=0, limit=1000)
        
        # Get all files for each health record
        all_files = []
        for record in health_records["health_records"]:
            files = await neo4j_service.list_files(record["id"], {}, skip=0, limit=1000)
            all_files.extend(files["files"])
        
        # Sort by date
        all_files.sort(key=lambda x: x.get("created_at", datetime.min))
        
        # Generate comprehensive summary
        summary_request = SummaryRequest(
            content=json.dumps({
                "health_records": health_records["health_records"],
                "files": all_files
            }, default=str),
            summary_type=SummaryType.BOTH,
            context=f"Complete medical history for patient {user_id}"
        )
        
        summary = await agent_service.generate_summary(summary_request)
        
        return {
            "success": True,
            "health_records_count": len(health_records["health_records"]),
            "files_count": len(all_files),
            "summary": summary.model_dump(),
            "data": {
                "health_records": health_records["health_records"],
                "files": all_files
            }
        }
    except Exception as e:
        logger.error(f"Error generating medical history report: {e}")
        return {"success": False, "error": str(e)}

@tool
async def query_medical_record(health_record_id: str, user_id: str, query: str) -> Dict[str, Any]:
    """Query a specific medical record for detailed information"""
    try:
        # Get the health record
        health_record = await neo4j_service.get_health_record_by_id(health_record_id)
        if not health_record:
            return {"success": False, "error": "Health record not found"}
        
        # Get all files for this record
        files = await neo4j_service.list_files(health_record_id, {}, skip=0, limit=1000)
        
        # Create a detailed query context
        context = {
            "health_record": health_record,
            "files": files["files"],
            "user_query": query
        }
        
        # Use the agent service to process the query
        agent_query = AgentQuery(
            query=query,
            health_record_id=health_record_id,
            user_id=user_id,
            user_type=UserType.PATIENT  # Default to patient, can be overridden
        )
        
        response = await agent_service.process_query(agent_query)
        
        return {
            "success": True,
            "health_record": health_record,
            "files": files["files"],
            "response": response.model_dump(),
            "context": context
        }
    except Exception as e:
        logger.error(f"Error querying medical record: {e}")
        return {"success": False, "error": str(e)}

@tool
async def get_latest_prescription(user_id: str) -> Dict[str, Any]:
    """Get the latest medical prescription for a patient"""
    try:
        # Get all health records for the patient
        filters = {"patient_id": user_id}
        health_records = await neo4j_service.list_health_records(filters, skip=0, limit=1000)
        
        # Get medications from all health records
        all_medications = []
        for record in health_records["health_records"]:
            medications = await neo4j_service.get_medications(record["id"])
            for med in medications:
                med["health_record_id"] = record["id"]
                med["health_record_title"] = record.get("title", "Unknown")
                all_medications.append(med)
        
        # Sort by creation date and get the latest
        if all_medications:
            latest_medication = max(all_medications, key=lambda x: x.get("created_at", datetime.min))
            
            # Get additional context about the medication
            medicine_info = await agent_service.generate_medicine_summary_via_perplexity(
                latest_medication.get("medicine_name", "Unknown")
            )
            
            return {
                "success": True,
                "latest_prescription": latest_medication,
                "medicine_info": medicine_info,
                "all_medications_count": len(all_medications)
            }
        else:
            return {
                "success": True,
                "latest_prescription": None,
                "message": "No prescriptions found for this patient"
            }
    except Exception as e:
        logger.error(f"Error getting latest prescription: {e}")
        return {"success": False, "error": str(e)}

@tool
async def search_health_records(query: str, user_id: str, user_type: str) -> Dict[str, Any]:
    """Search across all health records and files"""
    try:
        # Search in health records
        health_record_results = await neo4j_service.search_health_records(query, user_id, user_type)
        
        # Search in files
        file_results = await neo4j_service.search_files(query, user_id, user_type)
        
        return {
            "success": True,
            "health_records": health_record_results,
            "files": file_results,
            "total_results": len(health_record_results) + len(file_results)
        }
    except Exception as e:
        logger.error(f"Error searching health records: {e}")
        return {"success": False, "error": str(e)}

@tool
async def generate_health_summary(health_record_id: str, summary_type: str = "BOTH") -> Dict[str, Any]:
    """Generate a comprehensive health summary for a specific health record"""
    try:
        summary_type_enum = SummaryType(summary_type)
        
        # Get health record and all its files
        health_record = await neo4j_service.get_health_record_by_id(health_record_id)
        if not health_record:
            return {"success": False, "error": "Health record not found"}
        
        files = await neo4j_service.list_files(health_record_id, {}, skip=0, limit=1000)
        
        # Generate summary using the existing service
        summary = await agent_service.generate_summary_from_file_id(
            health_record_id, summary_type_enum
        )
        
        return {
            "success": True,
            "health_record": health_record,
            "files_count": len(files["files"]),
            "summary": summary.model_dump()
        }
    except Exception as e:
        logger.error(f"Error generating health summary: {e}")
        return {"success": False, "error": str(e)}

# =============================================================================
# ORCHESTRATOR AGENT
# =============================================================================

class OrchestratorAgent:
    def __init__(self):
        self.tools = {
            "get_medical_history_report": get_medical_history_report,
            "query_medical_record": query_medical_record,
            "get_latest_prescription": get_latest_prescription,
            "search_health_records": search_health_records,
            "generate_health_summary": generate_health_summary
        }
        self.memory = MemorySaver()
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        
        # Define the workflow
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("select_tools", self._select_tools)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("generate_response", self._generate_response)
        
        # Define edges
        workflow.set_entry_point("analyze_intent")
        workflow.add_edge("analyze_intent", "select_tools")
        workflow.add_edge("select_tools", "execute_tools")
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _analyze_intent(self, state: AgentState) -> AgentState:
        """Analyze user intent from the query"""
        try:
            # Simple intent classification based on keywords
            query_lower = state.user_query.lower()
            
            if any(word in query_lower for word in ["history", "report", "complete", "all"]):
                state.intent = "get_medical_history"
            elif any(word in query_lower for word in ["prescription", "medication", "medicine", "latest"]):
                state.intent = "get_latest_prescription"
            elif any(word in query_lower for word in ["search", "find", "look for"]):
                state.intent = "search_records"
            elif any(word in query_lower for word in ["summary", "summarize", "overview"]):
                state.intent = "generate_summary"
            elif any(word in query_lower for word in ["query", "details", "information"]):
                state.intent = "query_record"
            else:
                state.intent = "general_query"
            
            return state
        except Exception as e:
            state.error = f"Intent analysis failed: {str(e)}"
            return state
    
    async def _select_tools(self, state: AgentState) -> AgentState:
        """Select appropriate tools based on intent"""
        try:
            tool_mapping = {
                "get_medical_history": ["get_medical_history_report"],
                "get_latest_prescription": ["get_latest_prescription"],
                "search_records": ["search_health_records"],
                "generate_summary": ["generate_health_summary"],
                "query_record": ["query_medical_record"],
                "general_query": ["search_health_records"]
            }
            
            state.tools_to_call = tool_mapping.get(state.intent, ["search_health_records"])
            return state
        except Exception as e:
            state.error = f"Tool selection failed: {str(e)}"
            return state
    
    async def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute the selected tools"""
        try:
            state.tool_results = {}
            
            for tool_name in state.tools_to_call:
                if tool_name in self.tools:
                    tool_func = self.tools[tool_name]
                    
                    # Execute tool with appropriate parameters
                    if tool_name == "get_medical_history_report":
                        result = await tool_func(user_id=state.user_id)
                    elif tool_name == "get_latest_prescription":
                        result = await tool_func(user_id=state.user_id)
                    elif tool_name == "search_health_records":
                        result = await tool_func(
                            query=state.user_query,
                            user_id=state.user_id,
                            user_type=state.user_type.value
                        )
                    elif tool_name == "generate_health_summary":
                        result = await tool_func(
                            health_record_id=state.health_record_id or "default",
                            summary_type="BOTH"
                        )
                    elif tool_name == "query_medical_record":
                        result = await tool_func(
                            health_record_id=state.health_record_id or "default",
                            user_id=state.user_id,
                            query=state.user_query
                        )
                    else:
                        result = {"success": False, "error": f"Unknown tool: {tool_name}"}
                    
                    state.tool_results[tool_name] = result
                else:
                    state.tool_results[tool_name] = {"success": False, "error": f"Tool not found: {tool_name}"}
            
            return state
        except Exception as e:
            state.error = f"Tool execution failed: {str(e)}"
            return state
    
    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate final response based on tool results"""
        try:
            if state.error:
                state.final_response = f"I encountered an error: {state.error}"
                state.confidence = 0.0
                return state
            
            # Process tool results and generate a comprehensive response
            response_parts = []
            
            for tool_name, result in state.tool_results.items():
                if result.get("success"):
                    if tool_name == "get_medical_history_report":
                        response_parts.append(f"📋 **Medical History Report Generated**\n\n")
                        response_parts.append(f"Found {result['health_records_count']} health records with {result['files_count']} files.\n\n")
                        if result['summary'].get('layman_summary'):
                            response_parts.append(f"**Summary:** {result['summary']['layman_summary']}")
                    
                    elif tool_name == "get_latest_prescription":
                        if result.get('latest_prescription'):
                            med = result['latest_prescription']
                            response_parts.append(f"💊 **Latest Prescription**\n\n")
                            response_parts.append(f"**Medicine:** {med.get('medicine_name', 'Unknown')}\n")
                            response_parts.append(f"**Dosage:** {med.get('dosage', 'Unknown')}\n")
                            response_parts.append(f"**Frequency:** {med.get('frequency', 'Unknown')}\n")
                            response_parts.append(f"**Prescribed:** {med.get('created_at', 'Unknown')}\n\n")
                            if result.get('medicine_info'):
                                response_parts.append(f"**Medicine Information:** {result['medicine_info']}")
                        else:
                            response_parts.append("No prescriptions found for this patient.")
                    
                    elif tool_name == "search_health_records":
                        response_parts.append(f"🔍 **Search Results**\n\n")
                        response_parts.append(f"Found {result['total_results']} results:\n")
                        if result['health_records']:
                            response_parts.append(f"- {len(result['health_records'])} health records\n")
                        if result['files']:
                            response_parts.append(f"- {len(result['files'])} files\n")
                    
                    elif tool_name == "generate_health_summary":
                        response_parts.append(f"📝 **Health Summary**\n\n")
                        if result['summary'].get('layman_summary'):
                            response_parts.append(f"**Summary:** {result['summary']['layman_summary']}")
                    
                    elif tool_name == "query_medical_record":
                        response_parts.append(f"📋 **Medical Record Query**\n\n")
                        if result.get('response', {}).get('response'):
                            response_parts.append(result['response']['response'])
                else:
                    response_parts.append(f"❌ Error with {tool_name}: {result.get('error', 'Unknown error')}")
            
            if not response_parts:
                response_parts.append("I couldn't find any relevant information for your query.")
            
            state.final_response = "\n".join(response_parts)
            state.confidence = 0.8 if not state.error else 0.0
            state.sources = ["health_records", "medical_database"]
            state.suggested_actions = ["view_health_record", "schedule_appointment"]
            
            return state
        except Exception as e:
            state.error = f"Response generation failed: {str(e)}"
            state.final_response = f"I encountered an error while generating the response: {str(e)}"
            return state
    
    async def process_query(self, query: AgentQuery) -> AgentResponse:
        """Process a user query through the orchestrator agent"""
        try:
            # Create initial state
            initial_state = AgentState(
                user_query=query.query,
                user_id=query.user_id,
                user_type=query.user_type,
                health_record_id=query.health_record_id
            )
            
            # Run the workflow
            config = {"configurable": {"thread_id": f"user_{query.user_id}_{datetime.now().timestamp()}"}}
            final_state = await self.graph.ainvoke(initial_state, config)
            
            # Handle the state properly - it might be a dict or an object
            if hasattr(final_state, 'final_response'):
                final_response = final_state.final_response
                confidence = final_state.confidence
                sources = final_state.sources
                suggested_actions = final_state.suggested_actions
            elif isinstance(final_state, dict):
                final_response = final_state.get('final_response')
                confidence = final_state.get('confidence', 0.0)
                sources = final_state.get('sources', [])
                suggested_actions = final_state.get('suggested_actions', [])
            else:
                # Fallback - try to access as dict
                final_response = getattr(final_state, 'final_response', None) or final_state.get('final_response', 'No response generated')
                confidence = getattr(final_state, 'confidence', 0.0) or final_state.get('confidence', 0.0)
                sources = getattr(final_state, 'sources', []) or final_state.get('sources', [])
                suggested_actions = getattr(final_state, 'suggested_actions', []) or final_state.get('suggested_actions', [])
            
            # Convert to AgentResponse
            return AgentResponse(
                response=final_response or "No response generated",
                confidence=confidence,
                sources=sources,
                suggested_actions=suggested_actions,
                cypher_queries_executed=[]
            )
            
        except Exception as e:
            logger.error(f"Orchestrator agent error: {e}")
            return AgentResponse(
                response=f"I encountered an error while processing your request: {str(e)}",
                confidence=0.0,
                sources=[],
                suggested_actions=[],
                cypher_queries_executed=[]
            )

# Global instance
orchestrator_agent = OrchestratorAgent() 