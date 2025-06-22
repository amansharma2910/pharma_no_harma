import logging
import json
from typing import Dict, Any, Optional, List
from prompts import graph_schema_summary, graph_schema_prompt, layman_summary_prompt
from app.services.bedrock_service import bedrock_service
from app.services.neo4j_service import neo4j_service
from app.models.schemas import AgentQuery, AgentResponse, SummaryRequest, SummaryResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

class BedrockNeo4jService:
    def __init__(self):
        self.bedrock_service = bedrock_service
        self.neo4j_service = neo4j_service
    
    async def process_query_with_neo4j_context(self, query: AgentQuery) -> AgentResponse:
        """Process query using Bedrock with Neo4j knowledge graph context"""
        try:
            # Step 1: Analyze query intent and extract entities
            intent_analysis = await self._analyze_query_intent(query.query, query.user_id, query.user_type, query.health_record_id)
            # Step 2: Generate Cypher queries based on intent
            cypher_queries = await self._generate_cypher_queries(intent_analysis, query)
            
            # Step 3: Execute queries and gather context
            context_data = await self._gather_neo4j_context(cypher_queries)
            
            # Step 4: Generate response with context
            response = await self._generate_contextual_response(query, context_data, intent_analysis)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query with Neo4j context: {e}")
            # Fallback to basic Bedrock response
            return await self.bedrock_service.process_query_with_bedrock(query)
    
    async def _analyze_query_intent(self, query: str, user_id: str = None, user_type: str = None, health_record_id: str = None) -> Dict[str, Any]:
        """Analyze query to understand intent and extract entities"""
        try:
            analysis_prompt = f"""
            The following is the query to be analyzed: {query}.

            Based on the query, find the following information. Do not make up any information. Do not make assumptions. All the information is strictly from the query.

            Your task is to analyze this medical query and extract:
            1. Intent (what the user wants to know)
            2. User ID
            3. User type; can be PATIENT or DOCTOR
            4. HealthRecord ID
            3. Query type (patient_info, HealthRecord summary, File summary, medication, appointment, etc.)
            
            The final output should be a JSON object with the following fields:
            {{
                "intent": "str",
                "user_id": {user_id},
                "user_type": {user_type},
                "health_record_id: "str",
                "query_type": "str"
            }}

            Strictly follow the JSON format. Do not add any other text or comments.
            """
            
            response = await self.bedrock_service.invoke_model(
                analysis_prompt, 
                inference_profile_arn=settings.BEDROCK_INFERENCE_PROFILE_ARN
            )
            
            # Parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Fallback parsing
                logger.info(query)
                logger.info(response)
                
        except Exception as e:
            logger.error(f"Error analyzing query intent: {e}")
            return {
                "intent": "general_query",
                "entities": [],
                "user_id": {user_id},
                "user_type": {user_type},
                "health_record_id": {health_record_id},
                "query_type": "general"
            }
    
    async def _generate_cypher_queries(self, intent_analysis: Dict[str, Any], query: AgentQuery) -> List[str]:
        """Generate Cypher queries based on intent analysis"""
        try:
            cypher_prompt = f"""
            Generate Cypher queries for Neo4j based on this intent analysis:
            
            Intent: {intent_analysis['intent']}
            id: {intent_analysis['user_id']}
            user_type: {intent_analysis['user_type']}
            Health Record ID: {intent_analysis['health_record_id']}
            Query Type: {intent_analysis['query_type']}
            
            Available node types: User, HealthRecord, Medication, File, Appointment
            Available relationships: 
            - (User)-[:OWNS]->(HealthRecord) --> Here, user has user_type: PATIENT
            - (User)-[:MANAGES]->(HealthRecord) --> Here, user has user_type: DOCTOR
            - (User)-[:PRESCRIBED]->(Medication) --> Here, user has user_type: DOCTOR
            - (User)-[:TREATS]->(User) --> Here, first user has user_type: DOCTOR and second user has user_type: PATIENT
            - (User)-[:UPLOADED]->(File) --> Here, user can be both PATIENT and DOCTOR
            - (HealthRecord)-[:HAS_FILE]->(File) --> Record-file associations
            - (HealthRecord)-[:HAS_MEDICATION]->(Medication) --> Record-medication links

            ## Essential Properties:
            - User: id, name, email, user_type, specialization (doctors)
            - HealthRecord: id, title, ailment, status, layman_summary, medical_summary
            - Medication: id, medication_name, dosage, frequency, instructions
            - File: id, filename, parsed_content, layman_summary, doctor_summary
            
            Generate a detailed Cypher query that would retrieve the relevant information. Ensure the generated cypher query strictly has a RETURN clause, return the relevant nodes and relationships.
            
            Return only the Cypher query. Do not add any other text or comments.
            """
            
            response = await self.bedrock_service.invoke_model(
                cypher_prompt,
                inference_profile_arn=settings.BEDROCK_INFERENCE_PROFILE_ARN
            )
            
            # Extract Cypher queries from response
            queries = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if line.startswith('MATCH') or line.startswith('//'):
                    queries.append(line)
            
            # Add fallback queries if none generated
            if not queries:
                queries = [
                    "MATCH (u:User) RETURN u LIMIT 10",
                    "MATCH (hr:HealthRecord) RETURN hr LIMIT 10"
                ]
            
            return queries
            
        except Exception as e:
            logger.error(f"Error generating Cypher queries: {e}")
            return ["MATCH (n) RETURN n LIMIT 5"]
    
    async def _gather_neo4j_context(self, cypher_queries: List[str]) -> Dict[str, Any]:
        """Execute Cypher queries and gather context data"""
        context_data = {
            "patient_info": [],
            "health_records": [],
            "medications": [],
            "appointments": [],
            "files": [],
            "relationships": []
        }
        
        try:
            for query in cypher_queries:
                logger.info(f"Executing Cypher query: {query}")
                
                # Execute query using existing neo4j_service
                result = await self.neo4j_service.execute_query(query)
                
                if result:
                    # Categorize results based on query content
                    if "User" in query and "PATIENT" in query:
                        context_data["patient_info"].extend(result)
                    elif "HealthRecord" in query:
                        context_data["health_records"].extend(result)
                    elif "Medication" in query:
                        context_data["medications"].extend(result)
                    elif "Appointment" in query:
                        context_data["appointments"].extend(result)
                    elif "File" in query:
                        context_data["files"].extend(result)
                    else:
                        context_data["relationships"].extend(result)
                        
        except Exception as e:
            logger.error(f"Error gathering Neo4j context: {e}")
        
        return context_data
    
    async def _generate_contextual_response(self, query: AgentQuery, context_data: Dict[str, Any], intent_analysis: Dict[str, Any]) -> AgentResponse:
        """Generate response using Bedrock with Neo4j context"""
        try:
            # Format context data for the model
            context_summary = self._format_context_for_model(context_data, query.user_type.value)
            
            response_prompt = f"""
            You are a medical AI assistant with access to a patient's health records stored in a Neo4j knowledge graph.
            
            User Query: {query.query}
            User Type: {query.user_type.value}
            Query Intent: {intent_analysis['intent']}
            
            Available Context from Knowledge Graph:
            {context_summary}
            
            Please provide a helpful, accurate response based on the available data.
            If the user is a PATIENT, use simple, non-technical language.
            If the user is a DOCTOR, include medical terminology and clinical details.
            
            If no relevant data is found, acknowledge this and provide general information.
            Always maintain patient privacy and confidentiality.
            """
            
            response_text = await self.bedrock_service.invoke_model(
                response_prompt,
                inference_profile_arn=settings.BEDROCK_INFERENCE_PROFILE_ARN
            )
            
            return AgentResponse(
                response=response_text,
                confidence=0.9 if context_data else 0.7,
                sources=["neo4j_knowledge_graph", "bedrock_model"],
                suggested_actions=self._generate_suggested_actions(intent_analysis, context_data),
                cypher_queries_executed=[q for q in context_data.get("relationships", [])]
            )
            
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            return AgentResponse(
                response="I'm sorry, I couldn't process your query with the available data.",
                confidence=0.0
            )
    
    def _format_context_for_model(self, context_data: Dict[str, Any], user_type: str) -> str:
        """Format Neo4j context data for the language model"""
        formatted_context = []
        
        # Format patient information
        if context_data.get("patient_info"):
            formatted_context.append("Patient Information:")
            for patient in context_data["patient_info"][:3]:  # Limit to 3 patients
                formatted_context.append(f"- {patient.get('name', 'Unknown')}: {patient.get('user_type', 'Unknown')}")
        
        # Format health records
        if context_data.get("health_records"):
            formatted_context.append("\nHealth Records:")
            for record in context_data["health_records"][:5]:  # Limit to 5 records
                formatted_context.append(f"- {record.get('title', 'Unknown')}: {record.get('content', '')[:100]}...")
        
        # Format medications
        if context_data.get("medications"):
            formatted_context.append("\nMedications:")
            for med in context_data["medications"][:5]:
                formatted_context.append(f"- {med.get('name', 'Unknown')}: {med.get('dosage', 'Unknown')}")
        
        # Format appointments
        if context_data.get("appointments"):
            formatted_context.append("\nAppointments:")
            for apt in context_data["appointments"][:3]:
                formatted_context.append(f"- {apt.get('title', 'Unknown')}: {apt.get('date', 'Unknown')}")
        
        # Format files
        if context_data.get("files"):
            formatted_context.append("\nMedical Files:")
            for file in context_data["files"][:3]:
                formatted_context.append(f"- {file.get('filename', 'Unknown')}: {file.get('category', 'Unknown')}")
        
        return "\n".join(formatted_context) if formatted_context else "No relevant data found in knowledge graph."
    
    def _generate_suggested_actions(self, intent_analysis: Dict[str, Any], context_data: Dict[str, Any]) -> List[str]:
        """Generate suggested actions based on intent and available data"""
        actions = []
        
        query_type = intent_analysis.get("query_type", "")
        
        if "medication" in query_type.lower():
            actions.extend(["view_medication_list", "check_drug_interactions", "schedule_medication_review"])
        
        if "appointment" in query_type.lower():
            actions.extend(["schedule_appointment", "view_upcoming_appointments", "reschedule_appointment"])
        
        if "health_record" in query_type.lower():
            actions.extend(["view_health_records", "add_health_record", "export_health_records"])
        
        if "patient" in query_type.lower():
            actions.extend(["view_patient_profile", "update_patient_info", "view_patient_history"])
        
        # Default actions
        if not actions:
            actions = ["view_health_records", "schedule_appointment", "contact_doctor"]
        
        return actions
    
    async def generate_cypher_from_natural_language(self, natural_language: str, context: Dict[str, Any] = None) -> str:
        """Generate Cypher query from natural language using Bedrock"""
        try:
            prompt = f"""
            Convert this natural language query to a Cypher query for Neo4j:
            
            Natural Language: {natural_language}
            
            Available node types: User, HealthRecord, Medication, File, Appointment
            Available relationships: HAS_RECORD, PRESCRIBED, UPLOADED, SCHEDULED, ASSIGNED_TO
            
            Context: {context or 'No additional context'}
            
            Return only the Cypher query, no explanation.
            """
            
            response = await self.bedrock_service.invoke_model(
                prompt,
                inference_profile_arn=settings.BEDROCK_INFERENCE_PROFILE_ARN
            )
            
            # Clean up response to extract just the Cypher query
            lines = response.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('MATCH') or line.startswith('//'):
                    return line
            
            return "MATCH (n) RETURN n LIMIT 10"  # Fallback
            
        except Exception as e:
            logger.error(f"Error generating Cypher from natural language: {e}")
            return "MATCH (n) RETURN n LIMIT 10"
    
    async def get_patient_context(self, patient_id: str) -> Dict[str, Any]:
        """Get comprehensive patient context from Neo4j"""
        try:
            # Get patient information
            patient_query = f"MATCH (p:User {{id: '{patient_id}'}}) RETURN p"
            patient_result = await self.neo4j_service.execute_query(patient_query)
            
            # Get health records
            records_query = f"MATCH (p:User {{id: '{patient_id}'}})-[:HAS_RECORD]->(hr:HealthRecord) RETURN hr ORDER BY hr.date DESC LIMIT 10"
            records_result = await self.neo4j_service.execute_query(records_query)
            
            # Get medications
            meds_query = f"MATCH (p:User {{id: '{patient_id}'}})-[:HAS_RECORD]->(hr:HealthRecord)-[:PRESCRIBED]->(m:Medication) RETURN m"
            meds_result = await self.neo4j_service.execute_query(meds_query)
            
            # Get appointments
            apts_query = f"MATCH (p:User {{id: '{patient_id}'}})-[:HAS_RECORD]->(hr:HealthRecord)-[:SCHEDULED]->(a:Appointment) RETURN a ORDER BY a.date DESC LIMIT 5"
            apts_result = await self.neo4j_service.execute_query(apts_query)
            
            return {
                "patient": patient_result[0] if patient_result else None,
                "health_records": records_result,
                "medications": meds_result,
                "appointments": apts_result
            }
            
        except Exception as e:
            logger.error(f"Error getting patient context: {e}")
            return {}
    
    async def search_health_records(self, search_term: str, patient_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search health records using Neo4j and enhance with Bedrock"""
        try:
            # Build Cypher query
            if patient_id:
                query = f"""
                MATCH (p:User {{id: '{patient_id}'}})-[:HAS_RECORD]->(hr:HealthRecord)
                WHERE hr.title CONTAINS '{search_term}' OR hr.content CONTAINS '{search_term}'
                RETURN hr ORDER BY hr.date DESC
                """
            else:
                query = f"""
                MATCH (hr:HealthRecord)
                WHERE hr.title CONTAINS '{search_term}' OR hr.content CONTAINS '{search_term}'
                RETURN hr ORDER BY hr.date DESC LIMIT 20
                """
            
            results = await self.neo4j_service.execute_query(query)
            
            # Enhance results with Bedrock-generated summaries using improved prompt
            enhanced_results = []
            for record in results:
                if record.get('content'):
                    summary_prompt = f"{layman_summary_prompt}\n\nContent to summarize:\n{record['content'][:500]}...\n\nContext: Health record search result"
                    summary = await self.bedrock_service.invoke_model(
                        summary_prompt,
                        inference_profile_arn=settings.BEDROCK_INFERENCE_PROFILE_ARN
                    )
                    record['ai_summary'] = summary
                
                enhanced_results.append(record)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error searching health records: {e}")
            return []

# Global instance
bedrock_neo4j_service = BedrockNeo4jService() 