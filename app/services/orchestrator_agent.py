import logging
from typing import Dict, Any, Optional, List, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
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
from app.services.sarvam_translation_service import sarvam_translation_service
from app.core.config import settings
from app.utils.helpers import convert_neo4j_dates

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
    preferred_language: str = "en-IN"

# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

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
        
        # Convert Neo4j date/time objects to Python native types
        health_records = convert_neo4j_dates(health_records)
        
        # Get all files for each health record
        all_files = []
        for record in health_records["records"]:
            files = await neo4j_service.list_files(record["hr"]["id"], {}, skip=0, limit=1000)
            files = convert_neo4j_dates(files)
            all_files.extend(files["files"])
        
        # Sort by date
        all_files.sort(key=lambda x: x.get("created_at", datetime.min))
        
        # Generate comprehensive summary
        summary_request = SummaryRequest(
            content=json.dumps({
                "health_records": health_records["records"],
                "files": all_files
            }, default=str),
            summary_type=SummaryType.BOTH,
            context=f"Complete medical history for patient {user_id}"
        )
        
        summary = await agent_service.generate_summary(summary_request)
        
        return {
            "success": True,
            "health_records_count": len(health_records["records"]),
            "files_count": len(all_files),
            "summary": summary.model_dump(),
            "data": {
                "health_records": health_records["records"],
                "files": all_files
            }
        }
    except Exception as e:
        logger.error(f"Error generating medical history report: {e}")
        return {"success": False, "error": str(e)}

async def query_medical_record(health_record_id: str, user_id: str, query: str) -> Dict[str, Any]:
    """Query a specific medical record for detailed information"""
    try:
        # Get the health record
        health_record = await neo4j_service.get_health_record_by_id(health_record_id)
        if not health_record:
            return {"success": False, "error": "Health record not found"}
        
        # Convert Neo4j date/time objects to Python native types
        health_record = convert_neo4j_dates(health_record)
        
        # Get all files for this record
        files = await neo4j_service.list_files(health_record_id, {}, skip=0, limit=1000)
        files = convert_neo4j_dates(files)
        
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

async def get_latest_prescription(user_id: str) -> Dict[str, Any]:
    """Get the latest medical prescription for a patient"""
    try:
        # Get all health records for the patient
        filters = {"patient_id": user_id}
        health_records = await neo4j_service.list_health_records(filters, skip=0, limit=1000)
        
        # Convert Neo4j date/time objects to Python native types
        health_records = convert_neo4j_dates(health_records)
        
        # Get medications from all health records
        all_medications = []
        for record in health_records["records"]:
            medications = await neo4j_service.get_medications(record["hr"]["id"])
            medications = convert_neo4j_dates(medications)
            for med in medications:
                med["health_record_id"] = record["hr"]["id"]
                med["health_record_title"] = record["hr"].get("title", "Unknown")
                all_medications.append(med)
        
        # Sort by creation date and get the latest
        if all_medications:
            latest_medication = max(all_medications, key=lambda x: x.get("created_at", datetime.min))
            
            # Only get additional info if we have a real medicine name (not Unknown/empty)
            medicine_info = None
            medicine_name = latest_medication.get("medicine_name", "").strip()
            if medicine_name and medicine_name.lower() != "unknown":
                try:
                    medicine_info = await agent_service.generate_medicine_summary_via_perplexity(medicine_name)
                except Exception as e:
                    logger.warning(f"Could not get medicine info for {medicine_name}: {e}")
                    medicine_info = None
            
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

async def search_health_records(query: str, user_id: str, user_type: str) -> Dict[str, Any]:
    """Search across all health records and files"""
    try:
        # Search in health records
        health_record_results = await neo4j_service.search_health_records(query, user_id, user_type)
        health_record_results = convert_neo4j_dates(health_record_results)
        
        # Search in files
        file_results = await neo4j_service.search_files(query, user_id, user_type)
        file_results = convert_neo4j_dates(file_results)
        
        return {
            "success": True,
            "health_records": health_record_results,
            "files": file_results,
            "total_results": len(health_record_results) + len(file_results)
        }
    except Exception as e:
        logger.error(f"Error searching health records: {e}")
        return {"success": False, "error": str(e)}

async def generate_health_summary(health_record_id: str, summary_type: str = "BOTH") -> Dict[str, Any]:
    """Generate a comprehensive health summary for a specific health record"""
    try:
        summary_type_enum = SummaryType(summary_type)
        
        # Get health record and all its files
        health_record = await neo4j_service.get_health_record_by_id(health_record_id)
        if not health_record:
            return {"success": False, "error": "Health record not found"}
        
        # Convert Neo4j date/time objects to Python native types
        health_record = convert_neo4j_dates(health_record)
        
        files = await neo4j_service.list_files(health_record_id, {}, skip=0, limit=1000)
        files = convert_neo4j_dates(files)
        
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

async def search_drug_information(medicine_name: str) -> Dict[str, Any]:
    """Search for detailed information about a specific drug/medicine"""
    try:
        if not medicine_name or not medicine_name.strip():
            return {"success": False, "error": "Medicine name is required"}
        
        medicine_name = medicine_name.strip()
        
        # Get both summary and detailed information
        try:
            summary = await agent_service.generate_medicine_summary_via_perplexity(medicine_name)
        except Exception as e:
            logger.warning(f"Could not get medicine summary for {medicine_name}: {e}")
            summary = None
        
        try:
            from app.services.perplexity_service import perplexity_service
            detailed_info = await perplexity_service.search_medicine_info(medicine_name)
        except Exception as e:
            logger.warning(f"Could not get detailed medicine info for {medicine_name}: {e}")
            detailed_info = None
        
        if not summary and not detailed_info:
            return {
                "success": False, 
                "error": f"No information found for medicine: {medicine_name}"
            }
        
        return {
            "success": True,
            "medicine_name": medicine_name,
            "summary": summary,
            "detailed_info": detailed_info,
            "source": "perplexity_search"
        }
    except Exception as e:
        logger.error(f"Error searching drug information: {e}")
        return {"success": False, "error": str(e)}

# =============================================================================
# TRANSLATION HELPER FUNCTIONS
# =============================================================================

async def translate_summary_if_needed(summary: str, target_language: str = "en-IN", summary_type: str = "LAYMAN") -> str:
    """Translate summary to target language if not English"""
    if not summary or target_language == "en-IN":
        return summary
    
    try:
        logger.info(f"Translating summary of length {len(summary)} to {target_language}")
        
        # If summary is too long, break it into chunks
        if len(summary) > 800:  # Leave buffer for API overhead
            logger.info(f"Summary too long ({len(summary)} chars), chunking...")
            chunks = _split_text_into_chunks(summary, max_length=800)
            logger.info(f"Split into {len(chunks)} chunks")
            translated_chunks = []
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    logger.info(f"Translating chunk {i+1}: {chunk[:100]}...")
                    result = sarvam_translation_service.translate_medical_summary(
                        summary=chunk,
                        target_language=target_language,
                        summary_type=summary_type
                    )
                    
                    if result.get("success"):
                        translated_text = result.get("translated_text", chunk)
                        logger.info(f"Chunk {i+1} translated successfully: {translated_text[:100]}...")
                        translated_chunks.append(translated_text)
                    else:
                        logger.warning(f"Chunk {i+1} translation failed: {result.get('error')}")
                        translated_chunks.append(chunk)  # Keep original if translation fails
            
            final_result = " ".join(translated_chunks)
            logger.info(f"Final translated result length: {len(final_result)}")
            return final_result
        else:
            # Use Sarvam translation service for short content
            logger.info(f"Translating short summary...")
            result = sarvam_translation_service.translate_medical_summary(
                summary=summary,
                target_language=target_language,
                summary_type=summary_type
            )
            
            if result.get("success"):
                translated_text = result.get("translated_text", summary)
                logger.info(f"Short summary translated successfully")
                return translated_text
            else:
                logger.warning(f"Translation failed: {result.get('error')}")
                return summary
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return summary

def _split_text_into_chunks(text: str, max_length: int = 800) -> list:
    """Split text into chunks that respect sentence and paragraph boundaries"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        if len(current_chunk + paragraph) <= max_length:
            current_chunk += paragraph + '\n\n'
        else:
            # If current chunk has content, save it
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # If paragraph itself is too long, split by sentences
            if len(paragraph) > max_length:
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    if len(current_chunk + sentence) <= max_length:
                        current_chunk += sentence + '. '
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + '. '
            else:
                current_chunk = paragraph + '\n\n'
    
    # Add remaining chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

async def translate_text_if_needed(text: str, target_language: str = "en-IN") -> str:
    """Translate any text to target language if not English"""
    if not text or target_language == "en-IN":
        return text
    
    try:
        # Use Sarvam translation service for general text
        result = sarvam_translation_service.translate_text(
            text=text,
            target_language=target_language,
            source_language="en-IN"
        )
        
        if result.get("success"):
            return result.get("translated_text", text)
        else:
            logger.warning(f"Text translation failed: {result.get('error')}")
            return text
    except Exception as e:
        logger.error(f"Text translation error: {e}")
        return text

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
            "generate_health_summary": generate_health_summary,
            "search_drug_information": search_drug_information
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
    
    def _extract_medicine_name(self, query: str) -> str:
        """Extract medicine name from user query"""
        import re
        
        # Common patterns to extract medicine names
        patterns = [
            r"about\s+([a-zA-Z\s]+?)(?:\s|$|\?|\.)",
            r"information\s+(?:on|about)\s+([a-zA-Z\s]+?)(?:\s|$|\?|\.)",
            r"tell me about\s+([a-zA-Z\s]+?)(?:\s|$|\?|\.)",
            r"what is\s+([a-zA-Z\s]+?)(?:\s|$|\?|\.)",
            r"details\s+(?:on|about)\s+([a-zA-Z\s]+?)(?:\s|$|\?|\.)",
            r"side effects\s+(?:of\s+)?([a-zA-Z\s]+?)(?:\s|$|\?|\.)",
            r"dosage\s+(?:of\s+)?([a-zA-Z\s]+?)(?:\s|$|\?|\.)"
        ]
        
        query_lower = query.lower().strip()
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                medicine_name = match.group(1).strip()
                # Clean up common words
                medicine_name = re.sub(r'\b(drug|medicine|medication|tablet|pill|capsule)\b', '', medicine_name).strip()
                if medicine_name:
                    return medicine_name
        
        # Fallback: look for capitalized words that might be medicine names
        words = query.split()
        for word in words:
            if word[0].isupper() and len(word) > 3 and word.isalpha():
                return word
        
        # If all else fails, return the last meaningful word
        meaningful_words = [w for w in words if len(w) > 3 and w.isalpha()]
        if meaningful_words:
            return meaningful_words[-1]
        
        return "unknown"
    
    async def _analyze_intent(self, state: AgentState) -> AgentState:
        """Analyze user intent from the query"""
        try:
            # Simple intent classification based on keywords
            query_lower = state.user_query.lower()
            
            if any(word in query_lower for word in ["history", "report", "complete", "all"]):
                state.intent = "get_medical_history"
            elif any(word in query_lower for word in ["prescription", "medication", "medicine", "latest"]) and not any(word in query_lower for word in ["about", "information", "tell me", "what is", "details"]):
                state.intent = "get_latest_prescription"
            elif any(word in query_lower for word in ["drug", "medicine", "medication"]) and any(word in query_lower for word in ["about", "information", "tell me", "what is", "details", "side effects", "dosage"]):
                state.intent = "search_drug_info"
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
                "search_drug_info": ["search_drug_information"],
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
                    elif tool_name == "search_drug_information":
                        # Extract medicine name from query
                        medicine_name = self._extract_medicine_name(state.user_query)
                        result = await tool_func(medicine_name=medicine_name)
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
                        # Translate headers and messages
                        header = await translate_text_if_needed("📋 **Medical History Report Generated**", state.preferred_language)
                        summary_text = await translate_text_if_needed(
                            f"Found {result['health_records_count']} health records with {result['files_count']} files.", 
                            state.preferred_language
                        )
                        response_parts.append(f"{header}\n\n")
                        response_parts.append(f"{summary_text}\n\n")
                        
                        # Include both layman and doctor summaries if available
                        summary = result.get('summary', {})
                        if summary.get('layman_summary'):
                            # Translate layman summary if needed
                            translated_layman = await translate_summary_if_needed(
                                summary['layman_summary'], 
                                state.preferred_language, 
                                "LAYMAN"
                            )
                            # Translate the label
                            patient_label = await translate_text_if_needed("**Patient Summary:**", state.preferred_language)
                            response_parts.append(f"{patient_label}\n{translated_layman}\n\n")
                        if summary.get('doctor_summary'):
                            # Check if this is actually patient-friendly content that should be translated
                            doctor_content = summary['doctor_summary']
                            medical_label = await translate_text_if_needed("**Medical Summary:**", state.preferred_language)
                            
                            # If the content looks patient-friendly (contains phrases like "Your Information", "Test Results", etc.), translate it
                            if any(phrase in doctor_content for phrase in ["Your Information", "Patient Summary", "Your blood sugar", "Next Steps", "Keep an eye", "Test Results"]):
                                # This is patient-friendly content, translate it
                                translated_content = await translate_summary_if_needed(doctor_content, state.preferred_language, "LAYMAN")
                                response_parts.append(f"{medical_label}\n{translated_content}\n\n")
                            else:
                                # This is actual medical summary, keep in English for medical accuracy
                                response_parts.append(f"{medical_label}\n{doctor_content}\n\n")
                        
                        # If no structured summaries, try to display any summary content
                        if not summary.get('layman_summary') and not summary.get('doctor_summary'):
                            # Check if there's any summary content in other formats
                            if isinstance(summary, dict):
                                for key, value in summary.items():
                                    if value and isinstance(value, str):
                                        # Translate the key label and content
                                        translated_key = await translate_text_if_needed(f"**{key.replace('_', ' ').title()}:**", state.preferred_language)
                                        translated_value = await translate_summary_if_needed(value, state.preferred_language, "LAYMAN")
                                        response_parts.append(f"{translated_key}\n{translated_value}\n\n")
                    
                    elif tool_name == "get_latest_prescription":
                        if result.get('latest_prescription'):
                            med = result['latest_prescription']
                            # Translate header
                            header = await translate_text_if_needed("💊 **Latest Prescription**", state.preferred_language)
                            response_parts.append(f"{header}\n\n")
                            
                            # Only show actual data, don't show "Unknown" fields
                            if med.get('medicine_name') and med.get('medicine_name').lower() != 'unknown':
                                medicine_label = await translate_text_if_needed("**Medicine:**", state.preferred_language)
                                response_parts.append(f"{medicine_label} {med['medicine_name']}\n")
                            else:
                                medicine_label = await translate_text_if_needed("**Medicine:**", state.preferred_language)
                                not_specified = await translate_text_if_needed("Not specified in records", state.preferred_language)
                                response_parts.append(f"{medicine_label} {not_specified}\n")
                                
                            if med.get('dosage'):
                                dosage_label = await translate_text_if_needed("**Dosage:**", state.preferred_language)
                                response_parts.append(f"{dosage_label} {med['dosage']}\n")
                            if med.get('frequency'):
                                frequency_label = await translate_text_if_needed("**Frequency:**", state.preferred_language)
                                response_parts.append(f"{frequency_label} {med['frequency']}\n")
                            if med.get('duration_days'):
                                duration_label = await translate_text_if_needed("**Duration:**", state.preferred_language)
                                days_text = await translate_text_if_needed("days", state.preferred_language)
                                response_parts.append(f"{duration_label} {med['duration_days']} {days_text}\n")
                            if med.get('instructions'):
                                instructions_label = await translate_text_if_needed("**Instructions:**", state.preferred_language)
                                translated_instructions = await translate_text_if_needed(med['instructions'], state.preferred_language)
                                response_parts.append(f"{instructions_label} {translated_instructions}\n")
                            if med.get('created_at'):
                                # Handle both string and date objects
                                created_at = med['created_at']
                                if hasattr(created_at, 'strftime'):
                                    # It's a date/datetime object
                                    formatted_date = created_at.strftime('%Y-%m-%d')
                                elif isinstance(created_at, str):
                                    # It's already a string, extract date part
                                    formatted_date = created_at[:10]
                                else:
                                    formatted_date = str(created_at)
                                prescribed_label = await translate_text_if_needed("**Prescribed:**", state.preferred_language)
                                response_parts.append(f"{prescribed_label} {formatted_date}\n")
                            if med.get('prescribed_by'):
                                prescribed_by_label = await translate_text_if_needed("**Prescribed by:**", state.preferred_language)
                                doctor_id_text = await translate_text_if_needed("Doctor ID", state.preferred_language)
                                response_parts.append(f"{prescribed_by_label} {doctor_id_text} {med['prescribed_by']}\n")
                            
                            response_parts.append(f"\n")
                            
                            # Only show medicine info if we have real information
                            if result.get('medicine_info') and result['medicine_info'].strip():
                                info_label = await translate_text_if_needed("**Medicine Information:**", state.preferred_language)
                                translated_info = await translate_text_if_needed(result['medicine_info'], state.preferred_language)
                                response_parts.append(f"{info_label}\n{translated_info}\n")
                            
                            if result.get('all_medications_count', 0) > 1:
                                note_text = await translate_text_if_needed(
                                    f"*Note: You have {result['all_medications_count']} total medications in your records.*", 
                                    state.preferred_language
                                )
                                response_parts.append(note_text)
                        else:
                            header = await translate_text_if_needed("💊 **No prescriptions found**", state.preferred_language)
                            message = await translate_text_if_needed("No medication prescriptions were found in your medical records.", state.preferred_language)
                            response_parts.append(f"{header}\n\n{message}")
                    
                    elif tool_name == "search_health_records":
                        header = await translate_text_if_needed("🔍 **Search Results**", state.preferred_language)
                        found_text = await translate_text_if_needed(f"Found {result['total_results']} results:", state.preferred_language)
                        response_parts.append(f"{header}\n\n")
                        response_parts.append(f"{found_text}\n")
                        if result['health_records']:
                            health_records_text = await translate_text_if_needed(f"- {len(result['health_records'])} health records", state.preferred_language)
                            response_parts.append(f"{health_records_text}\n")
                        if result['files']:
                            files_text = await translate_text_if_needed(f"- {len(result['files'])} files", state.preferred_language)
                            response_parts.append(f"{files_text}\n")
                    
                    elif tool_name == "generate_health_summary":
                        header = await translate_text_if_needed("📝 **Health Summary**", state.preferred_language)
                        response_parts.append(f"{header}\n\n")
                        if result['summary'].get('layman_summary'):
                            # Translate health summary if needed
                            translated_summary = await translate_summary_if_needed(
                                result['summary']['layman_summary'],
                                state.preferred_language,
                                "LAYMAN"
                            )
                            summary_label = await translate_text_if_needed("**Summary:**", state.preferred_language)
                            response_parts.append(f"{summary_label} {translated_summary}")
                    
                    elif tool_name == "query_medical_record":
                        header = await translate_text_if_needed("📋 **Medical Record Query**", state.preferred_language)
                        response_parts.append(f"{header}\n\n")
                        if result.get('response', {}).get('response'):
                            # Translate the response content
                            translated_response = await translate_text_if_needed(result['response']['response'], state.preferred_language)
                            response_parts.append(translated_response)
                    
                    elif tool_name == "search_drug_information":
                        if result.get('medicine_name'):
                            drug_info_text = await translate_text_if_needed("Drug Information", state.preferred_language)
                            response_parts.append(f"💊 **{drug_info_text}: {result['medicine_name'].title()}**\n\n")
                            
                            if result.get('summary'):
                                # Translate drug summary if needed
                                translated_summary = await translate_summary_if_needed(
                                    result['summary'],
                                    state.preferred_language,
                                    "LAYMAN"
                                )
                                summary_label = await translate_text_if_needed("**Summary:**", state.preferred_language)
                                response_parts.append(f"{summary_label}\n{translated_summary}\n\n")
                            
                            if result.get('detailed_info'):
                                detailed_label = await translate_text_if_needed("**Detailed Information:**", state.preferred_language)
                                translated_detailed = await translate_text_if_needed(str(result['detailed_info']), state.preferred_language)
                                response_parts.append(f"{detailed_label}\n{translated_detailed}\n\n")
                            
                            source_text = await translate_text_if_needed(f"*Source: {result.get('source', 'Medical database')}*", state.preferred_language)
                            response_parts.append(source_text)
                        else:
                            error_message = await translate_text_if_needed("❌ Could not find information for the requested medicine.", state.preferred_language)
                            response_parts.append(error_message)
                
                else:
                    error_text = await translate_text_if_needed(f"❌ Error with {tool_name}: {result.get('error', 'Unknown error')}", state.preferred_language)
                    response_parts.append(error_text)
            
            if not response_parts:
                no_info_message = await translate_text_if_needed("I couldn't find any relevant information for your query.", state.preferred_language)
                response_parts.append(no_info_message)
            
            state.final_response = "\n".join(response_parts)
            state.confidence = 0.8 if not state.error else 0.0
            state.sources = ["health_records", "medical_database"]
            state.suggested_actions = ["view_health_record", "schedule_appointment"]
            
            return state
        except Exception as e:
            state.error = f"Response generation failed: {str(e)}"
            # Try to translate error message, fallback to English if translation fails
            try:
                error_message = await translate_text_if_needed(
                    f"I encountered an error while generating the response: {str(e)}", 
                    state.preferred_language
                )
            except:
                error_message = f"I encountered an error while generating the response: {str(e)}"
            state.final_response = error_message
            return state
    
    async def process_query(self, query: AgentQuery) -> AgentResponse:
        """Process a user query through the orchestrator agent"""
        try:
            # Create initial state
            initial_state = AgentState(
                user_query=query.query,
                user_id=query.user_id,
                user_type=query.user_type,
                health_record_id=query.health_record_id,
                preferred_language=query.preferred_language or "en-IN"
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
            # Try to translate error message, fallback to English if translation fails
            try:
                error_message = await translate_text_if_needed(
                    f"I encountered an error while processing your request: {str(e)}", 
                    query.preferred_language or "en-IN"
                )
            except:
                error_message = f"I encountered an error while processing your request: {str(e)}"
            
            return AgentResponse(
                response=error_message,
                confidence=0.0,
                sources=[],
                suggested_actions=[],
                cypher_queries_executed=[]
            )

# Global instance
orchestrator_agent = OrchestratorAgent() 